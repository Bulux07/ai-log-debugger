# AI Log Debugger

A simple Python CLI tool that uses OpenAI GPT to analyze log files and summarize errors

---

## Features
- Parse logs from multiple languages (Python, Java, C++, etc.)
- Clean and summarize log content
- Generate AI-driven analysis of errors and probable causes
- Also has colorized terminal output for readability

---

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ai-log-debugger.git
python -m venv venv
source venv/Scripts/activate   # Windows
# or
source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
OPENAI_API_KEY=your_api_key_here

To run program do the following: python main.py sample_logs/example.log

