
import pdfplumber

def load_text_from_file(path):
    path_lower = path.lower()

    # TXT support
    if path_lower.endswith(".txt"):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            return f"ERROR: Unable to read TXT file: {e}"

    # PDF support using pdfplumber
    if path_lower.endswith(".pdf"):
        try:
            text = ""
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            return text.strip()
        except Exception as e:
            return f"ERROR: Unable to read PDF file: {e}"

    # DOCX unsupported
    if path_lower.endswith(".docx"):
        return (
            "ERROR: DOCX files are not supported in this environment.\n"
            "Please upload a PDF or TXT version of your resume."
        )

    return "ERROR: Unsupported file type. Supported: PDF, TXT."
