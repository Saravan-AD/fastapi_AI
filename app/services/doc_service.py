import os

DOCS_PATH = "documents"

def load_all_documents():
    content = ""
    for filename in os.listdir(DOCS_PATH):
        with open(os.path.join(DOCS_PATH, filename), "r", encoding="utf-8") as f:
            content += f.read() + "\n"
    return content
