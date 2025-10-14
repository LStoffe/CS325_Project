import pandas as pd
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import nltk
from datetime import date

# Download NLTK resources (safe to call multiple times)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# ---------- Helpers ----------
URL_PATTERN = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)

def strip_urls(text: str) -> str:
    if pd.isna(text):
        return ""
    return URL_PATTERN.sub("", text)

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def clean_text(text: str) -> str:
    if pd.isna(text):
        return ""
    text = strip_urls(text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [lemmatizer.lemmatize(w) for w in text.split() if w not in stop_words]
    return " ".join(tokens)

def main():
    # Open file picker
    root = tk.Tk()
    root.withdraw()
    input_file = filedialog.askopenfilename(
        title="Select Adzuna jobs CSV",
        filetypes=[("CSV files", "*.csv")]
    )
    if not input_file:
        messagebox.showinfo("Job Cleaner", "No file selected. Exiting.")
        return

    # Load CSV
    df = pd.read_csv(input_file)

    # Detect URL + company columns
    url_col = next((c for c in df.columns if c.lower() in ("redirecturl", "redirect_url", "url")), None)
    company_col = next((c for c in df.columns if c.lower() in ("company", "companydisplayname", "company.display_name", "company_name")), None)

    # Clean descriptions & requirements
    full_desc = df.get("FullDescription", "").fillna("").astype(str).apply(strip_urls)
    requirements = df.get("Requirements", "").fillna("").astype(str).apply(strip_urls)
    df["job_text"] = (full_desc + " " + requirements).str.strip()

    # Cleaned fields
    df["job_text_clean"] = df["job_text"].apply(clean_text)
    df["Title_clean"] = df.get("Title", "").fillna("").astype(str).apply(clean_text)
    df["Requirements_clean"] = df.get("Requirements", "").fillna("").astype(str).apply(clean_text)

    # Extract URL column for mapping before dropping
    if url_col:
        url_series = df[url_col].astype(str)
        df = df.drop(columns=[url_col], errors="ignore")
    else:
        url_series = pd.Series([""] * len(df))

    # Build company → URL mapping
    if company_col:
        company_url_df = pd.DataFrame({"Company": df[company_col].astype(str), "URL": url_series})
    else:
        company_url_df = pd.DataFrame({"Company": df.get("Title", "").astype(str), "URL": url_series})

    company_url_df = company_url_df[company_url_df["URL"].str.strip() != ""]
    company_url_df = company_url_df.drop_duplicates().reset_index(drop=True)

    # Generate output filenames with today’s date
    today = date.today().isoformat()  # YYYY-MM-DD
    out_dir = input_file.rsplit("/", 1)[0] if "/" in input_file else input_file.rsplit("\\", 1)[0]
    cleaned_out = f"{out_dir}/adzuna_cs_jobs_cleaned_{today}.csv"
    company_urls_out = f"{out_dir}/adzuna_company_urls_{today}.csv"

    # Save outputs
    df.to_csv(cleaned_out, index=False)
    company_url_df.to_csv(company_urls_out, index=False)

    messagebox.showinfo("Job Cleaner",
        f"✅ Cleaned CSV:\n{cleaned_out}\n\n✅ Company→URL CSV:\n{company_urls_out}"
    )

if __name__ == "__main__":
    main()
