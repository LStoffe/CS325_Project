"""
Rank jobs vs resume using OpenAI embeddings + cosine similarity.
- Prompts for: cleaned jobs CSV, resume CSV, and Company→URL CSV.
- Expects:
    Jobs CSV:   'job_text_clean' column; ideally 'Title' and a company column.
    Resume CSV: 'resume_text_clean' single row.
    URL CSV:    'Company','URL' two columns (your company→URL map).

Features:
    - Duplicate removal (Title+Company if available, else Title, else job_text_clean)
    - Prints Top-10 with cosine scores to console
    - Dedupes URL map before joining
    - Shows ranked list GUI with “Open Link”
    - Final info popup REMOVED (prints summary to console)
"""

import os
import time
import webbrowser
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from openai import OpenAI

# ---------- Config ----------
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
BATCH_SIZE = 64
SLEEP_BETWEEN_BATCHES = 0.5  # seconds

# ---------- Small helpers ----------
def popup_error(title, msg):
    """Show a messagebox error without keeping a persistent root."""
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, msg, parent=root)
        root.destroy()
    except Exception:
        print(f"[ERROR] {title}: {msg}")

def ensure_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    return key

def pick_csv_dialog(title="Select CSV"):
    root = tk.Tk(); root.withdraw()
    p = filedialog.askopenfilename(title=title, filetypes=[("CSV files", "*.csv")], parent=root)
    root.destroy()
    return p

def lower_first_existing(df, candidates):
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_lower:
            return cols_lower[cand.lower()]
    return None

def embed_texts(client: OpenAI, texts: list[str], model: str) -> np.ndarray:
    vectors = []
    for i in range(0, len(texts), BATCH_SIZE):
        chunk = texts[i:i+BATCH_SIZE]
        resp = client.embeddings.create(model=model, input=chunk)
        vectors.extend([d.embedding for d in resp.data])
        time.sleep(SLEEP_BETWEEN_BATCHES)
    return np.array(vectors, dtype=np.float32)

def cosine_scores(job_vecs: np.ndarray, resume_vec: np.ndarray) -> np.ndarray:
    job_norms = np.linalg.norm(job_vecs, axis=1, keepdims=True) + 1e-12
    res_norm = np.linalg.norm(resume_vec) + 1e-12
    return (job_vecs / job_norms) @ (resume_vec / res_norm)

def show_top10_gui(df_top10):
    """Create the ranked list window as the Tk root and start mainloop()."""
    win = tk.Tk()
    win.title("Top 10 Job Matches")
    win.geometry("980x520")

    columns = ["Rank", "Score", "Title", "Company", "Location", "URL"]
    cols_present = [c for c in columns if c in df_top10.columns]

    tree = ttk.Treeview(win, columns=cols_present, show="headings")
    for col in cols_present:
        width = 70 if col in ("Rank","Score") else (460 if col=="Title" else 220 if col=="Company" else 200)
        tree.heading(col, text=col)
        tree.column(col, width=width, stretch=True)
    tree.pack(fill=tk.BOTH, expand=True)

    for _, row in df_top10.iterrows():
        values = [row[c] if c != "Score" else f'{row[c]:.4f}' for c in cols_present]
        tree.insert("", tk.END, values=values)

    btn_frame = tk.Frame(win); btn_frame.pack(fill=tk.X)
    tk.Label(btn_frame, text="Select a row and click 'Open Link' to visit the job post").pack(side=tk.LEFT, padx=8, pady=8)

    def on_open():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Open Link", "Select a row first.", parent=win); return
        values = tree.item(sel[0], "values")
        try:
            url = values[cols_present.index("URL")]
        except Exception:
            url = ""
        if url:
            webbrowser.open_new_tab(url)
        else:
            messagebox.showinfo("Open Link", "No URL available for this job.", parent=win)

    tk.Button(btn_frame, text="Open Link", command=on_open).pack(side=tk.RIGHT, padx=8, pady=8)

    # Keep the window open
    win.mainloop()

def dedupe_jobs(df, title_col, company_col):
    before = len(df)
    if title_col and company_col and title_col in df.columns and company_col in df.columns:
        df_dedup = df.drop_duplicates(subset=[title_col, company_col], keep="first").copy()
        basis = f"{title_col} + {company_col}"
    elif title_col and title_col in df.columns:
        df_dedup = df.drop_duplicates(subset=[title_col], keep="first").copy()
        basis = title_col
    else:
        df_dedup = df.drop_duplicates(subset=["job_text_clean"], keep="first").copy()
        basis = "job_text_clean"
    removed = before - len(df_dedup)
    return df_dedup, removed, basis

# ---------- Main ----------
def main():
    try:
        ensure_api_key()
    except Exception as e:
        popup_error("Setup", str(e)); return

    jobs_csv = pick_csv_dialog("Select CLEANED Jobs CSV (with job_text_clean)")
    if not jobs_csv: return
    resume_csv = pick_csv_dialog("Select Resume CSV (with resume_text_clean)")
    if not resume_csv: return
    url_csv = pick_csv_dialog("Select Company→URL CSV (Company, URL)")
    if not url_csv: return

    try:
        jobs = pd.read_csv(jobs_csv)
        resume = pd.read_csv(resume_csv)
        urlmap = pd.read_csv(url_csv)
    except Exception as e:
        popup_error("Load Error", f"Failed to read CSVs:\n{e}"); return

    if "job_text_clean" not in jobs.columns:
        popup_error("Data Error", "Jobs CSV missing 'job_text_clean'."); return
    if "resume_text_clean" not in resume.columns:
        popup_error("Data Error", "Resume CSV missing 'resume_text_clean'."); return
    if not {"Company","URL"}.issubset(set(urlmap.columns)):
        popup_error("Data Error", "URL CSV must have columns: Company, URL"); return

    company_col = lower_first_existing(jobs, ["Company","CompanyDisplayName","company.display_name","company_name"])
    title_col   = lower_first_existing(jobs, ["Title","title"])
    loc_col     = lower_first_existing(jobs, ["Location","location","LocationRaw","location.display_name"])

    jobs_dedup, removed, basis = dedupe_jobs(jobs, title_col, company_col)
    print(f"\nDe-duplication: removed {removed} duplicate row(s) based on [{basis}].")
    print(f"Remaining jobs to rank: {len(jobs_dedup)}\n")

    job_texts = jobs_dedup["job_text_clean"].fillna("").astype(str).tolist()
    resume_text = str(resume.iloc[0]["resume_text_clean"])

    client = OpenAI()
    try:
        job_vecs = embed_texts(client, job_texts, EMBEDDING_MODEL)
        res_vec = embed_texts(client, [resume_text], EMBEDDING_MODEL)[0]
    except Exception as e:
        popup_error("OpenAI Error", f"Embedding failed:\n{e}"); return

    scores = cosine_scores(job_vecs, res_vec)
    jobs_rank = jobs_dedup.copy()
    jobs_rank["_score"] = scores
    jobs_sorted = jobs_rank.sort_values("_score", ascending=False).reset_index(drop=True)

    print("Top 10 job matches based on cosine similarity:\n")
    for i in range(min(10, len(jobs_sorted))):
        title_print = jobs_sorted[title_col].iloc[i] if title_col else "(no title)"
        company_print = jobs_sorted[company_col].iloc[i] if company_col else "(no company)"
        score_print = jobs_sorted["_score"].iloc[i]
        print(f"{i+1:>2}. {title_print} at {company_print} — Similarity: {score_print:.4f}")
    print()

    top10 = jobs_sorted.head(10).copy()
    top10["Rank"] = np.arange(1, len(top10) + 1)

    urlmap2 = urlmap.copy()
    urlmap2["Company_key"] = urlmap2["Company"].astype(str).str.strip().str.lower()
    urlmap2 = urlmap2.drop_duplicates(subset=["Company_key"], keep="first")

    if company_col:
        top10["Company_key"] = top10[company_col].astype(str).str.strip().str.lower()
        top10 = pd.merge(top10, urlmap2[["Company_key","URL"]], on="Company_key", how="left")
        top10 = top10.drop(columns=["Company_key"])
    else:
        top10["URL"] = ""

    top10_out = top10.rename(columns={title_col:"Title", company_col:"Company", loc_col:"Location", "_score":"Score"})
    out_cols_final = [c for c in ["Rank","Score","Title","Company","Location","URL"] if c in top10_out.columns]
    top10_out = top10_out[out_cols_final]

    out_dir = os.path.dirname(jobs_csv) or "."
    out_path = os.path.join(out_dir, "top10_ranked_jobs.csv")
    try:
        top10_out.to_csv(out_path, index=False)
    except Exception as e:
        popup_error("Save Error", f"Could not write {out_path}:\n{e}"); return

    # Keep GUI only (no final popup)
    print(f"✅ Removed duplicates: {removed} (basis: {basis})")
    print(f"✅ Wrote Top 10 CSV: {out_path}")
    print(f"✅ Model used: {EMBEDDING_MODEL}\n")

    # Launch the ranked list window and start the event loop
    show_top10_gui(top10_out)

if __name__ == "__main__":
    main()
