import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from gui.theme import apply_dark_theme
from gui.results_popup import ResultsPopup
from core.utils.file_loader import load_text_from_file
from core.fetcher.adzuna_fetcher import AdzunaFetcher
from core.cleaner.resume_cleaner import ResumeCleaner
from core.embedder.openai_embedder import OpenAIEmbedder
from core.scrubber.scrubber import Scrubber
from core.formatter.job_formatter import JobFormatter
from core.pipeline.pipeline import Pipeline


# ==========================
# Helper: Trim displayed path
# ==========================
def trim_path(path):
    p = path.replace("\\", "/").split("/")
    if len(path) < 40:
        return path
    return p[0] + "/.../" + p[-1]


# ============================================
# COMBINED CREDENTIAL POPUP (App ID + App Key)
# ============================================
class AdzunaDialog(simpledialog.Dialog):
    def body(self, master):
        ttk.Label(master, text="Adzuna App ID:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.app_id_entry = ttk.Entry(master, width=40)
        self.app_id_entry.grid(row=0, column=1)

        ttk.Label(master, text="Adzuna App Key:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.app_key_entry = ttk.Entry(master, width=40)
        self.app_key_entry.grid(row=1, column=1)

        return self.app_id_entry

    def apply(self):
        self.result = (
            self.app_id_entry.get().strip(),
            self.app_key_entry.get().strip()
        )


# ==================
# MAIN APPLICATION
# ==================
class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Adzuna SOLID Pipeline v3")
        apply_dark_theme(self.root)

        # Main frame layout
        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(main)
        right = ttk.Frame(main)

        left.pack(side="left", fill="y")
        right.pack(side="right", fill="both", expand=True)

        self.resume_path = None

        # Upload button
        ttk.Button(left, text="Upload Resume", command=self.load_resume).pack(pady=10)
        self.resume_label = ttk.Label(left, text="No resume loaded")
        self.resume_label.pack(pady=10)

        # ==========
        # WHAT Field
        # ==========
        ttk.Label(left, text="Job Keywords (what):").pack(pady=5)
        self.entry_what = ttk.Entry(left, width=25)
        self.entry_what.insert(0, "software engineer")
        self.entry_what.pack(pady=5)

        # ===========
        # WHERE Field
        # ===========
        ttk.Label(left, text="Location (where):").pack(pady=5)
        self.entry_where = ttk.Entry(left, width=25)
        self.entry_where.insert(0, "St. Louis, MO")
        self.entry_where.pack(pady=5)

        # Run button
        ttk.Button(left, text="Run Pipeline", command=self.run_pipeline).pack(pady=10)

        # Log window
        self.logbox = tk.Text(right, height=25, bg="#1e1e1e", fg="white")
        self.logbox.pack(fill="both", expand=True)

    # ----------
    # LOGGING
    # ----------
    def log(self, msg):
        self.logbox.insert("end", msg + "\n")
        self.logbox.see("end")
        self.root.update()

    # -----------------
    # LOAD RESUME FILE
    # -----------------
    def load_resume(self):
        path = filedialog.askopenfilename(filetypes=[("Docs", "*.pdf *.txt")])
        if path:
            self.resume_path = path
            self.resume_label.config(text="Resume Loaded:\n" + trim_path(path))
            self.log(f"[Resume] Loaded {path}")

    # --------------
    # RUN PIPELINE
    # --------------
    def run_pipeline(self):
        if not self.resume_path:
            messagebox.showerror("Error", "Upload a resume first.")
            return

        # Combined credentials popup
        dialog = AdzunaDialog(self.root)
        if dialog.result is None:
            self.log("[Error] Adzuna credentials not entered.")
            return

        app_id, app_key = dialog.result
        if not app_id or not app_key:
            messagebox.showerror("Error", "Both Adzuna App ID and App Key are required.")
            return

        # Read Job Search Inputs
        query = self.entry_what.get().strip()
        location = self.entry_where.get().strip()

        if not query:
            messagebox.showerror("Error", "Job keywords (what) cannot be empty.")
            return

        if not location:
            messagebox.showerror("Error", "Location (where) cannot be empty.")
            return

        self.log("[0] Loading resume text...")
        resume_text = load_text_from_file(self.resume_path)

        # Initialize modules
        fetcher = AdzunaFetcher(app_id, app_key, self.log)
        cleaner = ResumeCleaner()

        # FIX APPLIED HERE — remove invalid logger argument
        embedder = OpenAIEmbedder()     # ← FIXED

        scrubber = Scrubber()
        formatter = JobFormatter()
        pipeline = Pipeline(fetcher, cleaner, embedder, scrubber, formatter, self.log)

        # Run pipeline
        df = pipeline.run(resume_text, query, location, 25)

        self.log("[9] Showing results popup...")
        ResultsPopup(self.root, df)

    # ------
    # START
    # ------
    def run(self):
        self.root.mainloop()
