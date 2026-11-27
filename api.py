import hmac
import os
import time

from fastapi import Depends, FastAPI, File, HTTPException, Security, UploadFile
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from sqlalchemy.orm import Session

from analyzer import MODEL, analyze_text
from db import get_db
from error_events import extract_error_events
from models import Analysis, ErrorEvent

# Cap input so one request can't trigger dozens of Gemini calls
MAX_LOG_CHARS = int(os.getenv("MAX_LOG_CHARS", "100000"))

app = FastAPI(title="AI Log Debugger", version="0.2.0")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(provided: str | None = Security(api_key_header)) -> None:
    """Reusable dependency: reject the request unless X-API-Key matches API_KEY."""
    expected = os.getenv("API_KEY")
    if not expected:
        # Fail closed: never run unprotected if the server is misconfigured
        raise HTTPException(status_code=500, detail="Server API key not configured")
    if not provided or not hmac.compare_digest(provided.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class AnalyzeRequest(BaseModel):
    log_text: str


class AnalyzeResponse(BaseModel):
    id: int
    model: str
    input_chars: int
    summary: str


def run_analysis(text: str, filename: str | None, db: Session) -> AnalyzeResponse:
    # Rejected requests (400/413) are not analyses, so nothing is saved for them.
    if not text.strip():
        raise HTTPException(status_code=400, detail="Log is empty")
    if len(text) > MAX_LOG_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Log too large: {len(text)} chars (max {MAX_LOG_CHARS})",
        )

    started = time.perf_counter()

    # Extraction comes straight from the log, so it works even if Gemini fails.
    events = extract_error_events(text)

    summary = None
    gemini_error = None
    try:
        summary = analyze_text(text)
    except RuntimeError as e:
        gemini_error = str(e)

    latency_ms = int((time.perf_counter() - started) * 1000)

    analysis = Analysis(
        filename=filename,
        model=MODEL,
        input_chars=len(text),
        status="failed" if gemini_error else "success",
        latency_ms=latency_ms,
        summary=summary,  # None (NULL) when Gemini failed
        # Attaching events through the relationship: SQLAlchemy saves the analysis
        # first, then fills in each event's analysis_id.
        error_events=[
            ErrorEvent(
                severity=e.severity,
                category=e.category,
                message=e.message,
                repeat_count=e.repeat_count,
            )
            for e in events
        ],
    )
    db.add(analysis)
    db.commit()  # one transaction: the analysis and all its events, or nothing

    if gemini_error:
        # The attempt is recorded, but the caller still gets the error.
        raise HTTPException(status_code=502, detail=gemini_error)

    return AnalyzeResponse(
        id=analysis.id, model=MODEL, input_chars=len(text), summary=summary
    )


@app.get("/health")
def health():
    return {"status": "ok"}


# Plain `def` (not async): the Gemini call blocks, so FastAPI runs it in a thread
@app.post("/analyze", response_model=AnalyzeResponse, dependencies=[Depends(require_api_key)])
def analyze_json(body: AnalyzeRequest, db: Session = Depends(get_db)):
    return run_analysis(body.log_text, None, db)


@app.post("/analyze/file", response_model=AnalyzeResponse, dependencies=[Depends(require_api_key)])
def analyze_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Read only slightly past the cap (UTF-8 is up to 4 bytes per char)
    data = file.file.read(MAX_LOG_CHARS * 4 + 1)
    text = data.decode("utf-8", errors="replace")
    filename = file.filename[:255] if file.filename else None
    return run_analysis(text, filename, db)