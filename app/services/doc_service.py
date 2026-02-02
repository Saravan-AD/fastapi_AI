import os
from pypdf import PdfReader

DOCS_PATH = "documents"

def load_all_documents():
    content = ""

    for filename in os.listdir(DOCS_PATH):
        file_path = os.path.join(DOCS_PATH, filename)

        # 📄 Handle TXT files
        if filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                content += f.read() + "\n"

        # 📕 Handle PDF files
        elif filename.endswith(".pdf"):
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    content += text + "\n"

    return content
