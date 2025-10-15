# =============================================================
#  Adzuna Toolbox: Job/Resume GUI Pipeline
#  Version: Full Pagination (like original fetcher) + Credential Check
# =============================================================

import os, re, time, threading, webbrowser, math
import numpy as np
import pandas as pd
from datetime import date
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext, simpledialog

try:
    import requests
    _REQUESTS_OK = True
except Exception:
    _REQUESTS_OK = False

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

# ------------------------------ (0) Fetch Adzuna API → CSV ------------------------------
def prompt_adzuna_params(parent):
    app_id = simpledialog.askstring("Adzuna App ID", "Enter your Adzuna App ID:", parent=parent)
    if not app_id: return None
    app_key = simpledialog.askstring("Adzuna App Key", "Enter your Adzuna App Key:", parent=parent, show="*")
    if not app_key: return None

    default_query = "computer science"
    what = simpledialog.askstring("Keyword(s)", "Keywords to search:", initialvalue=default_query, parent=parent)
    if not what: what = default_query

    default_where = "St. Louis, MO"
    where = simpledialog.askstring("Location", "Location:", initialvalue=default_where, parent=parent)
    if not where: where = default_where

    max_results = simpledialog.askinteger("Max Results", "How many jobs? (Default 100)",
                                          initialvalue=100, minvalue=1, maxvalue=1000, parent=parent)
    if not max_results: max_results = 100

    save_path = filedialog.asksaveasfilename(parent=parent, title="Save Adzuna Jobs CSV As",
                                             defaultextension=".csv", initialfile="adzuna_cs_jobs.csv",
                                             filetypes=[("CSV files","*.csv")])
    if not save_path: return None

    return {
        "app_id": app_id,
        "app_key": app_key,
        "what": what,
        "where": where,
        "max_results": max_results,
        "save_path": save_path,
    }

def extract_requirements(description):
    if not description:
        return None
    text = description.replace("\r", "")
    pattern = re.compile(r"(Requirements|Qualifications|Skills)[:\-]\s*(.*)", re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)
    if match:
        return text[match.start():].strip()
    bullet_pattern = re.compile(r"(^[\-\•\*]\s+.+|^\d+\.\s+.+)", re.MULTILINE)
    matches = bullet_pattern.findall(text)
    if matches:
        return "\n".join(matches).strip()
    return None

def action_fetch_adzuna_worker(parent, logbox, params):
    if not _REQUESTS_OK:
        popup_error("The 'requests' library is not installed. Run: pip install requests", parent)
        return

    app_id = params["app_id"]
    app_key = params["app_key"]
    query = params["what"]
    location = params["where"]
    max_results = int(params["max_results"])
    save_path = params["save_path"]

    base_url = "https://api.adzuna.com/v1/api/jobs/us/search/{}"
    session = requests.Session()

    # --- Credential Test ---
    try:
        test = session.get(base_url.format(1), params={
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": 1
        }, timeout=10)
        if test.status_code == 403:
            popup_error("❌ Invalid Adzuna App ID or Key. Check your credentials.", parent)
            return
        elif test.status_code != 200:
            gui_log(logbox, f"⚠️ Credential check returned {test.status_code}, proceeding anyway...")
        else:
            gui_log(logbox, "✅ Credentials verified successfully.")
    except Exception as e:
        popup_error(f"Could not verify credentials:\n{e}", parent)
        return

    all_jobs = []
    page = 1
    results_per_page = 20

    gui_log(logbox, f"📡 Fetching jobs for '{query}' in '{location}'...")

    while len(all_jobs) < max_results:
        url = base_url.format(page)
        params_req = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": results_per_page,
            "where": location,
            "what": query,
            "content-type": "application/json"
        }
        try:
            resp = session.get(url, params=params_req, timeout=30)
        except Exception as e:
            gui_log(logbox, f"❌ Network error on page {page}: {e}")
            break

        if resp.status_code != 200:
            gui_log(logbox, f"❌ Error {resp.status_code}: {resp.text}")
            break

        data = resp.json()
        results = data.get("results", [])

        if not results:
            gui_log(logbox, f"⚠️ No jobs found on page {page}. Stopping.")
            break

        for job in results:
            desc = job.get("description", "")
            reqs = extract_requirements(desc)
            all_jobs.append({
                "Title": job.get("title"),
                "Company": job.get("company", {}).get("display_name"),
                "Location": job.get("location", {}).get("display_name"),
                "Category": job.get("category", {}).get("label"),
                "Salary": job.get("salary_is_predicted"),
                "RedirectURL": job.get("redirect_url"),
                "FullDescription": desc,
                "Requirements": reqs
            })

        gui_log(logbox, f"✅ Page {page} fetched. Total jobs so far: {len(all_jobs)}")

        if len(all_jobs) >= max_results:
            break

        page += 1
        time.sleep(2)

    if not all_jobs:
        gui_log(logbox, "⚠️ No jobs found. Try different keywords or a broader location.")
        return

    df = pd.DataFrame(all_jobs[:max_results])
    try:
        df.to_csv(save_path, index=False)
        gui_log(logbox, f"💾 Saved {len(df)} jobs to {save_path}")
    except Exception as e:
        popup_error(f"Error saving CSV:\n{e}", parent)

# ------------------------------ GUI Setup ------------------------------
class ToolboxApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Adzuna Job Fetcher (Full Pagination)")
        self.geometry("900x560")

        left = tk.Frame(self)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.btn_fetch  = tk.Button(left, text="Fetch Adzuna Jobs", width=30, command=self.run_fetch)
        self.btn_exit   = tk.Button(left, text="Exit", width=30, command=self.destroy)
        self.btn_fetch.pack(pady=4, anchor="n")
        self.btn_exit.pack(pady=20, anchor="n")

        right = tk.Frame(self)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        tk.Label(right, text="Status / Log").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(right, height=25, state="disabled")
        self.log.pack(fill=tk.BOTH, expand=True)

    def lock(self, locked=True):
        state = "disabled" if locked else "normal"
        for b in (self.btn_fetch, self.btn_exit):
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

if __name__ == "__main__":
    app = ToolboxApp()
    app.mainloop()