"""
Always-file-picker: PDF/TXT resume -> single-row CSV (local only)

Outputs columns:
  name, email, phone, linkedin, github, portfolio,
  skills (semicolon-separated),
  education_compact (entries joined by ' || '),
  experience_compact (entries joined by ' || '),
  resume_text_clean (normalized blob for matching).
"""

import os, re
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

# ----------------------- Regex & Dictionaries -----------------------
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
URL_RE = re.compile(r"(https?://[^\s)]+)", re.I)
GITHUB_RE = re.compile(r"github\.com/[\w\-]+", re.I)
LINKEDIN_RE = re.compile(r"linkedin\.com/in/[^\s/]+", re.I)

DEGREE_WORDS = [
    "bachelor","b.s.","bs","bsc",
    "master","m.s.","ms","msc",
    "ph.d","phd","doctor","associate","btech","mtech"
]

DEFAULT_SKILLS = [
    "python","java","c","c++","c#","javascript","typescript","sql","php","ruby","go","rust","matlab","r","mips",
    "react","node","express","django","flask","spring",".net","asp.net","fastapi","laravel",
    "pandas","numpy","scikit-learn","tensorflow","pytorch","keras","matplotlib","seaborn","spark","hadoop",
    "aws","azure","gcp","docker","kubernetes","terraform","ansible","git","github","gitlab","jenkins","ci/cd",
    "mysql","postgres","sqlite","mongodb","dynamodb","redis","elasticsearch","oracle","mariadb",
    "linux","windows","macos","vim","vscode","visual studio","jira","confluence","agile","scrum","mamp","w3.css",
    "rest","graphql","grpc","microservices","jwt","oauth","ssl","tls"
]

BASIC_STOPWORDS = {
    "a","an","and","are","as","at","be","by","for","from","has","have","in","is","it","its","of","on",
    "or","that","the","to","was","were","with","this","those","these","your","you","i","we","our","us"
}

# ----------------------- IO: Read text -----------------------
def read_text_any(path: str) -> str:
    ext = os.path.splitext(path.lower())[1]
    if ext == ".txt":
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif ext == ".pdf":
        return read_pdf_text(path)
    else:
        raise ValueError("Unsupported file type. Provide a .pdf or .txt")

def read_pdf_text(path: str) -> str:
    try:
        import pdfplumber
    except ImportError as e:
        raise RuntimeError("pdfplumber is required to read PDFs. Install with conda-forge.") from e

    text = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text.append(page.extract_text() or "")
    return "\n".join(text)

# ----------------------- Helpers / Cleaning -----------------------
def normalize_ws(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s).strip()

def compact_newlines(s: str) -> str:
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()

def clean_text_for_scoring(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [t for t in text.split() if t not in BASIC_STOPWORDS]
    return " ".join(tokens)

# ----------------------- Extraction -----------------------
def guess_name(text: str) -> str:
    lines = [normalize_ws(l) for l in text.splitlines()]
    lines = [l for l in lines if l]
    for l in lines[:12]:
        low = l.lower()
        if EMAIL_RE.search(l) or PHONE_RE.search(l) or "linkedin" in low or "github" in low:
            continue
        if any(h in low for h in ["education","experience","summary","skills","projects",
                                  "certifications","objective","profile","work history"]):
            continue
        tokens = [t for t in re.split(r"[^A-Za-z\-]", l) if t]
        if len(tokens) >= 2 and sum(1 for t in tokens if t[:1].isupper()) >= 2:
            return l
    return ""

def find_contact(text: str) -> dict:
    email = EMAIL_RE.search(text)
    phone = PHONE_RE.search(text)
    urls = URL_RE.findall(text)
    linkedin = LINKEDIN_RE.search(text)
    github = GITHUB_RE.search(text)

    portfolio = ""
    for u in urls or []:
        if "linkedin" not in u.lower() and "github" not in u.lower():
            portfolio = u
            break

    return {
        "Email": email.group(0) if email else "",
        "Phone": phone.group(0) if phone else "",
        "LinkedIn": linkedin.group(0) if linkedin else "",
        "GitHub": github.group(0) if github else "",
        "Portfolio": portfolio,
    }

def section_blocks(text: str) -> dict:
    headers = [
        "summary","profile","objective",
        "skills","technical skills","technologies",
        "experience","work experience","professional experience","employment","work history",
        "projects",
        "education","academics",
        "certifications","licenses","awards","honors",
    ]
    lines = text.splitlines()
    idxs = []
    for i, line in enumerate(lines):
        low = line.strip().lower()
        if any(re.match(rf"^{h}\b", low) for h in headers):
            idxs.append((i, low))
    idxs.sort()

    sections = {}
    for j, (start, header) in enumerate(idxs):
        end = idxs[j+1][0] if j+1 < len(idxs) else len(lines)
        sections[header.split()[0]] = "\n".join(lines[start+1:end]).strip()
    return sections

def extract_skills(text: str, skills_list=None) -> list:
    skills_list = skills_list or DEFAULT_SKILLS
    text_lower = " " + re.sub(r"[^a-z0-9+.#/]", " ", text.lower()) + " "
    found = set()
    for skill in skills_list:
        s = skill.lower()
        pattern = r"(?<![a-z0-9])" + re.escape(s) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower, re.I):
            found.add(skill)
    return sorted(found)

def extract_education(edu_text: str) -> list:
    results = []
    if not edu_text:
        return results
    chunks = [c.strip() for c in re.split(r"\n\s*\n|•|- |\u2022", edu_text) if c.strip()]
    for c in chunks:
        line = " ".join(c.split())
        if any(dw in line.lower() for dw in DEGREE_WORDS) or "university" in line.lower() or "college" in line.lower():
            results.append(line)
    return results

def extract_experience(exp_text: str) -> list:
    results = []
    if not exp_text:
        return results
    blocks = [b.strip() for b in re.split(r"\n\s*\n", exp_text) if b.strip()]
    for block in blocks:
        bullets = re.findall(r"(?m)^(?:•|-|\*)\s+(.*)$", block)
        if bullets:
            results.extend(bullets)
        else:
            if block:
                results.append(block)
    return results

# ----------------------- End-to-end -----------------------
def process_resume(path: str) -> pd.DataFrame:
    raw = compact_newlines(read_text_any(path))

    # >>> NEW: remove any PDF glyph artifacts like (cid:###) entirely <<<
    raw = re.sub(r"\(cid:\d+\)", "", raw)

    if not raw or len(raw) < 50:
        raise RuntimeError("Could not extract enough text. If PDF is scanned, OCR first or use TXT.")

    name = guess_name(raw)
    contacts = find_contact(raw)
    sections = section_blocks(raw)
    skills_list = extract_skills(raw)
    edu_list = extract_education(sections.get("education", ""))
    exp_list = extract_experience(sections.get("experience", ""))

    skills_compact = "; ".join(skills_list) if skills_list else ""
    education_compact = " || ".join(edu_list) if edu_list else ""
    experience_compact = " || ".join(exp_list) if exp_list else ""

    resume_text_clean = clean_text_for_scoring(
        "\n".join([
            name or "",
            contacts.get("Email",""),
            contacts.get("Phone",""),
            contacts.get("LinkedIn",""),
            contacts.get("GitHub",""),
            contacts.get("Portfolio",""),
            skills_compact,
            education_compact,
            experience_compact,
            raw
        ])
    )

    row = {
        "name": name,
        "email": contacts.get("Email",""),
        "phone": contacts.get("Phone",""),
        "linkedin": contacts.get("LinkedIn",""),
        "github": contacts.get("GitHub",""),
        "portfolio": contacts.get("Portfolio",""),
        "skills": skills_compact,
        "education_compact": education_compact,
        "experience_compact": experience_compact,
        "resume_text_clean": resume_text_clean
    }
    return pd.DataFrame([row])

def main():
    # Always open file picker first
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        title="Select your resume (PDF or TXT)",
        filetypes=[("PDF and Text", "*.pdf *.txt"), ("PDF files", "*.pdf"), ("Text files", "*.txt")]
    )
    if not path:
        messagebox.showinfo("Resume Extractor", "No file selected. Exiting.")
        return

    try:
        df = process_resume(path)
    except Exception as e:
        messagebox.showerror("Resume Extractor", f"Error processing file:\n{e}")
        return

    out_dir = os.path.dirname(path) or "."
    out_path = os.path.join(out_dir, "resume_single.csv")
    try:
        df.to_csv(out_path, index=False)
    except Exception as e:
        messagebox.showerror("Resume Extractor", f"Failed to write CSV:\n{e}")
        return

    messagebox.showinfo("Resume Extractor", f"✅ Wrote: {out_path}")

if __name__ == "__main__":
    main()
