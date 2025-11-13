#reads the log file
#will trim for GPT doesnt get overloaded and can handle majority of the log

def parse_log(path):
    with open(path, "r", errors="ignore") as f:
        data = f.read()
    return data[:8000]
