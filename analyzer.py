import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types, errors
from prompts import LOG_ANALYSIS_PROMPT

load_dotenv()
gemini_client = genai.Client()

#Model name
MODEL = "gemini-3.5-flash-lite"

def split_text(text: str, max_chars: int = 20000):
    """Split text into chunks on line boundaries so log entries stay whole."""
    chunks, current, size = [], [], 0
    for line in text.splitlines(keepends=True):
        if size + len(line) > max_chars and current:
            chunks.append("".join(current))
            current, size = [], 0
        current.append(line)
        size += len(line)
    if current:
        chunks.append("".join(current))
        return chunks

#if it hits a rate limit or a temporary server error then it pauses then tries again
def ask_gemini(prompt: str, retries: int = 3) -> str:
    """Send one prompt to Gemini, retrying on rate limits and temporary errors."""
    for attempt in range(retries):
        try:
            response = gemini_client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are an expert software engineer.",
                    temperature=0.2,
                ),
            )
            return response.text or ""
        except errors.APIError as e:
            if e.code in (429, 503) and attempt < retries - 1:
                time.sleep(2 ** attempt * 5)    # wait 5s, then 10s, then give up
                continue
            raise RuntimeError(f"Gemini API error {e.code}: {e.message}") from e

#splits log into chunks, run each chunk thorugh gemini
def analyze_log(log_text: str) -> str:
    chunks = split_text(log_text)
    summaries = [
        ask_gemini(LOG_ANALYSIS_PROMPT.format(log_excerpt=chunk)) for chunk in chunks
    ]
    if len(summaries) == 1:
        return summaries[0]
    # Combine the per-chunk summaries into one overall root-cause summary
    combined = "\n\n".join(summaries)
    return ask_gemini(
        "Combine these partial log analyses into one summary of the most likely "
        "root causes, ordered by importance:\n\n" + combined
    )

