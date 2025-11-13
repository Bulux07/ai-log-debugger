import os
from dotenv import load_dotenv
import openai
from prompts import LOG_ANALYSIS_PROMPT

load_dotenv()
openai.api_key=os.getenv("OPENAI_API_KEY")

#Model name
MODEL = "gpt-4o-mini"

def split_text(text: str, max_chars: int = 3500):
    """Split the text into charcter size chunks (keeps each chunk safe for the model)"""
    return [text[i:i + max_chars] for i in range(0, len(text),max_chars)]

def analyze_log(log_text: str) ->str:
    #split log text into chunks
    chunks = split_text(log_text)
    summaries = []
    #process each chunk
    for chunk in chunks:
        prompt = LOG_ANALYSIS_PROMPT.format(log_excerpt=chunk)
        #holds output generated from chatpgt
        response = openai.chat.completions.create(
            model=MODEL,
            #change depending on what needs to be debugged
            messages=[
                {"role": "system", "content": "You are an expert software engineer."},
                {"role": "user", "content": prompt}
            ]
        )
        #get chatgpt response and store it 
        summaries.append(response.choices[0].message.content)
    #combines all of chatgpt response into one string
    return "\n\n".join(summaries)

