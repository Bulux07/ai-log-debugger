# AI Log Debugger

A Python command-line tool that analyzes log files with Google Gemini. It
filters a log down to the lines that matter, then summarizes critical errors,
probable root causes, and recommended debugging steps.

---

## Features
- Collapses repeated log lines and keeps error-like lines with surrounding context
- Splits large logs into chunks on line boundaries, so entries stay whole
- Combines per-chunk analyses into one overall root-cause summary
- Retries with increasing waits on rate limits and temporary API errors
- Colored terminal output for readability
- Runs locally or in a container (Podman or Docker)

---

## Installation

1. Clone the repository and enter the folder:
```bash
git clone https://github.com/Bulux07/ai-log-debugger.git
cd ai-log-debugger
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/Scripts/activate   # Windows (Git Bash)
# or
source venv/bin/activate       # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a file named `.env` in the project folder with your Gemini API key
(get one from https://aistudio.google.com):
```
GEMINI_API_KEY=your_api_key_here
```

---

## Usage

```bash
python main.py sample_logs/test.log
```

---

## Run with Podman or Docker

```bash
podman build -t ai-log-debugger .
podman run --rm --env-file .env ai-log-debugger sample_logs/test.log
```
Replace `podman` with `docker` if you use Docker. The API key is passed in at
run time and is not stored in the image.

---
