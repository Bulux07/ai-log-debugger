# prompts.py

LOG_ANALYSIS_PROMPT = """
You are an expert software engineer.
Analyze the following log file and summarize:

1. The most critical errors and warnings
2. Probable root causes
3. Recommended debugging steps
4. Any recurring issues

Logs:
{log_excerpt}
"""
