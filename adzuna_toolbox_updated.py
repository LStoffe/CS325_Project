# =============================================================
#  Adzuna Toolbox (Full GUI Pipeline with Assets Directory)
# -------------------------------------------------------------
#  Description:
#     End-to-end job/resume analyzer using Adzuna API and OpenAI
#     embeddings. All output files are now saved automatically
#     into an "assets/" subfolder beside this script.
# =============================================================

import os, re, time, threading, webbrowser
import numpy as np
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, simpledialog
from datetime import date

# ------------------------------ Global Assets Directory ------------------------------
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# ------------------------------ Optional Dependencies ------------------------------
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    nltk.download('stopwords', quiet=True); nltk.download('wordnet', quiet=True)
    _NLTK_OK = True
except Exception:
    _NLTK_OK = False

try:
    from openai import OpenAI
    _OPENAI_OK = True
except Exception:
    _OPENAI_OK = False

try:
    import requests
    _REQUESTS_OK = True
except Exception:
    _REQUESTS_OK = False

# ------------------------------ Constants ------------------------------
APP_TITLE = "Adzuna Toolbox"
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
BATCH_SIZE = 64
SLEEP_BETWEEN_BATCHES = 0.5

# ------------------------------ GUI Helpers ------------------------------
def gui_log(txtbox: scrolledtext.ScrolledText, msg: str):
    def _append():
        try:
            txtbox.configure(state="normal")
            txtbox.insert(tk.END, msg + "\n")
            txtbox.see(tk.END)
            txtbox.configure(state="disabled")
        except tk.TclError:
            print(msg)
    try:
        txtbox.after(0, _append)
    except Exception:
        print(msg)

def popup_error(msg, parent=None, title="Error"):
    messagebox.showerror(title, msg, parent=parent)

# ------------------------------ Common Utilities ------------------------------
_URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.I)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}")

def strip_urls(s: str) -> str:
    if pd.isna(s): return ""
    return _URL_RE.sub("", str(s))

def clean_text_basic(text: str, lemmatizer, stop_words):
    if pd.isna(text): return ""
    text = strip_urls(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [lemmatizer.lemmatize(w) for w in text.split() if w not in stop_words]
    return " ".join(tokens)

def cosine_scores(job_vecs: np.ndarray, resume_vec: np.ndarray) -> np.ndarray:
    job_norms = np.linalg.norm(job_vecs, axis=1, keepdims=True) + 1e-12
    res_norm  = np.linalg.norm(resume_vec) + 1e-12
    return (job_vecs / job_norms) @ (resume_vec / res_norm)

# =============================================================
#  Stage 0: Fetch Adzuna API → CSV (Full Pagination + Cred Check)
# =============================================================
def prompt_adzuna_params(parent):
    app_id = simpledialog.askstring("Adzuna App ID", "Enter your Adzuna App ID:", parent=parent)
    if not app_id: return None
    app_key = simpledialog.askstring("Adzuna App Key", "Enter your Adzuna App Key:", parent=parent, show="*")
    if not app_key: return None

    default_query = "computer science"
    what = simpledialog.askstring("Keyword(s)", "Keywords to search:", initialvalue=default_query, parent=parent) or default_query
    default_where = "St. Louis, MO"
    where = simpledialog.askstring("Location", "Location:", initialvalue=default_where, parent=parent) or default_where
    max_results = simpledialog.askinteger("Max Results", "How many jobs? (Default 100)", initialvalue=100, minvalue=1, maxvalue=2000, parent=parent) or 100

    out_default = f"adzuna_jobs_{date.today().isoformat()}.csv"
    save_path = os.path.join(ASSETS_DIR, out_default)
    return {"app_id": app_id, "app_key": app_key, "what": what, "where": where, "max_results": max_results, "save_path": save_path}

def extract_requirements(description: str):
    if not description: return None
    text = description.replace("\r", "")
    m = re.search(r"(Requirements|Qualifications|Skills)[:\-]\s*(.*)", text, re.IGNORECASE | re.DOTALL)
    if m: return text[m.start():].strip()
    bullets = re.findall(r"(^[\-\•\*]\s+.+|^\d+\.\s+.+)", text, re.MULTILINE)
    return "\n".join(bullets).strip() if bullets else None

def action_fetch_adzuna_worker(parent, logbox, params):
    if not _REQUESTS_OK:
        popup_error("The 'requests' library is not installed. Run: pip install requests", parent); return

    app_id, app_key, query, location, max_results, save_path = (
        params["app_id"], params["app_key"], params["what"], params["where"], int(params["max_results"]), params["save_path"]
    )
    session = requests.Session(); base_url = "https://api.adzuna.com/v1/api/jobs/us/search/{}"

    try:
        test = session.get(base_url.format(1), params={"app_id": app_id, "app_key": app_key, "results_per_page": 1}, timeout=10)
        if test.status_code == 403:
            popup_error("❌ Invalid Adzuna App ID or Key. Check your credentials.", parent); return
    except Exception as e:
        popup_error(f"Could not verify credentials:\n{e}", parent); return

    gui_log(logbox, f"📡 Fetching jobs for '{query}' in '{location}'...")
    all_jobs, page, rpp = [], 1, 20
    while len(all_jobs) < max_results:
        url = base_url.format(page)
        p = {"app_id": app_id, "app_key": app_key, "results_per_page": rpp, "where": location, "what": query}
        try:
            resp = session.get(url, params=p, timeout=30); data = resp.json()
        except Exception as e:
            gui_log(logbox, f"❌ Error fetching page {page}: {e}"); break
        results = data.get("results", [])
        if not results:
            gui_log(logbox, f"⚠️ No results on page {page}. Stopping."); break

        for job in results:
            desc = job.get("description", "") or ""
            all_jobs.append({
                "Title": job.get("title"),
                "Company": (job.get("company") or {}).get("display_name"),
                "Location": (job.get("location") or {}).get("display_name"),
                "Category": (job.get("category") or {}).get("label"),
                "ContractTime": job.get("contract_time"),
                "Created": job.get("created"),
                "SalaryMin": job.get("salary_min"),
                "SalaryMax": job.get("salary_max"),
                "RedirectURL": job.get("redirect_url"),
                "FullDescription": desc,
                "Requirements": extract_requirements(desc)
            })
        gui_log(logbox, f"✅ Page {page} fetched ({len(results)} jobs). Total: {len(all_jobs)}")
        if len(all_jobs) >= max_results: break
        page += 1; time.sleep(1.5)

    if not all_jobs:
        gui_log(logbox, "⚠️ No jobs found."); return
    pd.DataFrame(all_jobs[:max_results]).to_csv(save_path, index=False)
    gui_log(logbox, f"💾 Saved {len(all_jobs[:max_results])} jobs to {save_path}")

# =============================================================
#  Stage 1: Clean Adzuna CSV
# =============================================================
def action_clean_adzuna_worker(parent, logbox, _params):
    if not _NLTK_OK:
        popup_error("nltk is required. Run: pip install nltk", parent); return
    in_csv = filedialog.askopenfilename(parent=parent, title="Select Adzuna jobs CSV", filetypes=[("CSV files","*.csv")])
    if not in_csv: return
    try:
        df = pd.read_csv(in_csv)
    except Exception as e:
        popup_error(f"Could not read CSV:\n{e}", parent); return

    lemmatizer = WordNetLemmatizer(); stop_words = set(stopwords.words('english'))
    desc_col = "FullDescription" if "FullDescription" in df.columns else (df.columns[df.columns.str.contains("desc", case=False)][0] if any(df.columns.str.contains("desc", case=False)) else None)
    if not desc_col:
        popup_error("Could not find a description column.", parent); return
    df["job_text_clean"] = df[desc_col].fillna("").astype(str).apply(lambda t: clean_text_basic(t, lemmatizer, stop_words))

    cleaned_out = os.path.join(ASSETS_DIR, os.path.basename(os.path.splitext(in_csv)[0]) + "_cleaned.csv")
    df.to_csv(cleaned_out, index=False)
    gui_log(logbox, f"✅ Cleaned CSV saved: {cleaned_out}")

# =============================================================
#  Stage 2: Resume → CSV
# =============================================================
def read_text_any(path: str) -> str:
    ext = os.path.splitext(path.lower())[1]
    if ext == ".txt":
        return open(path, "r", encoding="utf-8", errors="ignore").read()
    elif ext == ".pdf":
        import pdfplumber
        text = []
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                text.append(p.extract_text() or "")
        return "\n".join(text)
    else:
        raise ValueError("Unsupported file type (use .pdf or .txt)")

def action_resume_to_csv_worker(parent, logbox, _params):
    path = filedialog.askopenfilename(parent=parent, title="Select resume (PDF or TXT)", filetypes=[("PDF/TXT","*.pdf *.txt")])
    if not path: return
    try:
        text = read_text_any(path)
    except Exception as e:
        popup_error(str(e), parent); return

    email = EMAIL_RE.search(text); phone = PHONE_RE.search(text)
    row = {"Email": email.group(0) if email else "", "Phone": phone.group(0) if phone else "", "resume_text_clean": text}
    out_path = os.path.join(ASSETS_DIR, "resume_single.csv")
    pd.DataFrame([row]).to_csv(out_path, index=False)
    gui_log(logbox, f"✅ Resume CSV saved: {out_path}")

# =============================================================
#  Stage 3: Embed Jobs + Resume
# =============================================================
def ensure_openai_key(parent):
    if not _OPENAI_OK: popup_error("openai library required. Run: pip install openai", parent); return None
    key = os.getenv("OPENAI_API_KEY")
    if not key: popup_error("OPENAI_API_KEY is not set. Set it and retry.", parent); return None
    return key

def embed_texts(client, texts, model):
    vecs = []
    for i in range(0, len(texts), BATCH_SIZE):
        chunk = texts[i:i+BATCH_SIZE]
        resp = client.embeddings.create(model=model, input=chunk)
        vecs.extend([d.embedding for d in resp.data])
        time.sleep(SLEEP_BETWEEN_BATCHES)
    return np.array(vecs, dtype=np.float32)

def action_embed_jobs_and_resume_worker(parent, logbox, _params):
    if not ensure_openai_key(parent): return
    jobs_csv = filedialog.askopenfilename(parent=parent, title="Select CLEANED Jobs CSV", filetypes=[("CSV files","*.csv")])
    resume_csv = os.path.join(ASSETS_DIR, "resume_single.csv")
    if not jobs_csv or not os.path.exists(resume_csv):
        popup_error("Missing resume CSV or jobs file.", parent); return

    try:
        jobs = pd.read_csv(jobs_csv); resume = pd.read_csv(resume_csv)
    except Exception as e:
        popup_error(f"Failed to read CSVs:\n{e}", parent); return
    if "job_text_clean" not in jobs.columns or "resume_text_clean" not in resume.columns:
        popup_error("Missing required text columns.", parent); return

    client = OpenAI()
    job_vecs = embed_texts(client, jobs["job_text_clean"].fillna("").astype(str).tolist(), EMBEDDING_MODEL)
    res_vec  = embed_texts(client, [str(resume.iloc[0]["resume_text_clean"])], EMBEDDING_MODEL)[0]

    np.save(os.path.join(ASSETS_DIR, "jobs_embeddings.npy"), job_vecs)
    np.save(os.path.join(ASSETS_DIR, "resume_embedding.npy"), np.array(res_vec, dtype=np.float32))

    meta_cols = ["job_text_clean"]
    for c in ("Title","Company","Location","Category","RedirectURL"):
        if c in jobs.columns: meta_cols.append(c)
    jobs[meta_cols].to_csv(os.path.join(ASSETS_DIR, "jobs_meta.csv"), index=False)

    gui_log(logbox, "✅ Embeddings created and stored in assets folder.")

# =============================================================
#  Stage 4: Rank Jobs vs Resume
# =============================================================
def show_top10_gui(df_top10: pd.DataFrame):
    win = tk.Toplevel(); win.title("Top 10 Job Matches"); win.geometry("1000x560")
    columns = ["Rank","Score","Title","Company","Location","RedirectURL"]
    cols_present = [c for c in columns if c in df_top10.columns]
    tree = ttk.Treeview(win, columns=cols_present, show="headings")
    for col in cols_present:
        width = 80 if col in ("Rank","Score") else 260 if col=="Title" else 200
        tree.heading(col, text=col); tree.column(col, width=width, stretch=True)
    tree.pack(fill=tk.BOTH, expand=True)

    for _, r in df_top10.iterrows():
        vals = [f"{r[c]:.4f}" if c=="Score" else r[c] for c in cols_present]
        tree.insert("", tk.END, values=vals)

    def on_open():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Open Link", "Select a row first.", parent=win)
            return
        values = tree.item(sel[0], "values")
        try:
            url = values[cols_present.index("RedirectURL")]
        except Exception:
            url = ""
        if url:
            webbrowser.open_new_tab(url)
        else:
            messagebox.showinfo("Open Link", "No URL available.", parent=win)

    tk.Button(win, text="Open Link", command=on_open).pack(side=tk.BOTTOM, pady=8)

def action_rank_jobs_openai_worker(parent, logbox, _params):
    if not ensure_openai_key(parent): return
    try:
        job_vecs = np.load(os.path.join(ASSETS_DIR, "jobs_embeddings.npy"))
        resume_vec = np.load(os.path.join(ASSETS_DIR, "resume_embedding.npy"))
        meta = pd.read_csv(os.path.join(ASSETS_DIR, "jobs_meta.csv"))
    except Exception as e:
        popup_error(f"Missing embeddings/meta files in assets. Run Stage 3 first.\n{e}", parent)
        return

    scores = cosine_scores(job_vecs, resume_vec)
    df = meta.copy(); df["_score"] = scores

    rename_map = {"_score": "Score"}
    for alt in ("Title", "title"):
        if alt in df.columns:
            rename_map[alt] = "Title"
            break
    for alt in ("Company", "CompanyDisplayName", "company.display_name"):
        if alt in df.columns:
            rename_map[alt] = "Company"
            break
    for alt in ("Location", "location", "LocationRaw", "location.display_name"):
        if alt in df.columns:
            rename_map[alt] = "Location"
            break
    for alt in ("RedirectURL", "redirect_url", "URL"):
        if alt in df.columns:
            rename_map[alt] = "RedirectURL"
            break

    top10 = df.sort_values("_score", ascending=False).head(10).rename(columns=rename_map).copy()
    top10["Rank"] = np.arange(1, len(top10) + 1)
    cols_final = [c for c in ["Rank", "Score", "Title", "Company", "Location", "RedirectURL"] if c in top10.columns]
    top10 = top10[cols_final]

    out_path = os.path.join(ASSETS_DIR, "top10_ranked_jobs.csv")
    top10.to_csv(out_path, index=False)
    gui_log(logbox, f"✅ Top 10 saved: {out_path}")
    try:
        parent.after(0, lambda: show_top10_gui(top10))
    except Exception:
        show_top10_gui(top10)

# =============================================================
#  GUI Application
# =============================================================
class ToolboxApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE); self.geometry("1040x640")

        left = tk.Frame(self); left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.btn_fetch  = tk.Button(left, text="0) Fetch Adzuna Jobs", width=30, command=self.run_fetch)
        self.btn_clean  = tk.Button(left, text="1) Clean Adzuna CSV",  width=30, command=self.run_clean)
        self.btn_resume = tk.Button(left, text="2) Extract Resume → CSV", width=30, command=self.run_resume)
        self.btn_embed  = tk.Button(left, text="3) Embed Jobs + Resume", width=30, command=self.run_embed)
        self.btn_rank   = tk.Button(left, text="4) Rank Jobs vs Resume", width=30, command=self.run_rank)
        self.btn_exit   = tk.Button(left, text="Exit", width=30, command=self.destroy)
        for b in (self.btn_fetch, self.btn_clean, self.btn_resume, self.btn_embed, self.btn_rank, self.btn_exit):
            b.pack(pady=4, anchor="n")

        right = tk.Frame(self); right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(right, text="Status / Log").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(right, height=30, state="disabled")
        self.log.pack(fill=tk.BOTH, expand=True)

    def lock(self, locked=True):
        state = "disabled" if locked else "normal"
        for b in (self.btn_fetch, self.btn_clean, self.btn_resume, self.btn_embed, self.btn_rank, self.btn_exit):
            b.configure(state=state)
        self.update_idletasks()

    def run_threaded(self, target):
        def wrapper():
            try:
                target()
            finally:
                self.lock(False)
        self.lock(True)
        threading.Thread(target=wrapper, daemon=True).start()

    def run_fetch(self):
        params = prompt_adzuna_params(self)
        if not params:
            gui_log(self.log, "Adzuna fetch: canceled.")
            return
        self.run_threaded(lambda: action_fetch_adzuna_worker(self, self.log, params))

    def run_clean(self):
        self.run_threaded(lambda: action_clean_adzuna_worker(self, self.log, {}))

    def run_resume(self):
        self.run_threaded(lambda: action_resume_to_csv_worker(self, self.log, {}))

    def run_embed(self):
        self.run_threaded(lambda: action_embed_jobs_and_resume_worker(self, self.log, {}))

    def run_rank(self):
        self.run_threaded(lambda: action_rank_jobs_openai_worker(self, self.log, {}))


if __name__ == "__main__":
    app = ToolboxApp()
    app.mainloop()
