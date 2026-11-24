import hmac
import os

from fastapi import Depends, FastAPI, File, HTTPException, Security, UploadFile
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from analyzer import MODEL, analyze_text

# Cap input so one request can't trigger dozens of Gemini calls
MAX_LOG_CHARS = int(os.getenv("MAX_LOG_CHARS", "100000"))

app = FastAPI(title="AI Log Debugger", version="0.1.0")

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
    model: str
    input_chars: int
    summary: str


def run_analysis(text: str) -> AnalyzeResponse:
    if not text.strip():
        raise HTTPException(status_code=400, detail="Log is empty")
    if len(text) > MAX_LOG_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Log too large: {len(text)} chars (max {MAX_LOG_CHARS})",
        )
    try:
        summary = analyze_text(text)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return AnalyzeResponse(model=MODEL, input_chars=len(text), summary=summary)


@app.get("/health")
def health():
    return {"status": "ok"}


# Plain `def` (not async): the Gemini call blocks, so FastAPI runs it in a thread
@app.post("/analyze", response_model=AnalyzeResponse, dependencies=[Depends(require_api_key)])
def analyze_json(body: AnalyzeRequest):
    return run_analysis(body.log_text)


@app.post("/analyze/file", response_model=AnalyzeResponse, dependencies=[Depends(require_api_key)])
def analyze_file(file: UploadFile = File(...)):
    # Read only slightly past the cap (UTF-8 is up to 4 bytes per char)
    data = file.file.read(MAX_LOG_CHARS * 4 + 1)
    text = data.decode("utf-8", errors="replace")
    return run_analysis(text)