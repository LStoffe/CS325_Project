import pandas as pd

class Pipeline:
    def __init__(self, fetcher, cleaner, embedder, scrubber, formatter, logger):
        self.fetcher = fetcher
        self.cleaner = cleaner
        self.embedder = embedder
        self.scrubber = scrubber
        self.formatter = formatter
        self.logger = logger

    def log(self, msg):
        if self.logger:
            self.logger(msg)

    def run(self, resume_text, query, location, radius):
        self.log("[1] Cleaning resume...")
        clean_resume = self.cleaner.clean(resume_text)

        self.log("[2] Embedding resume...")
        resume_vec = self.embedder.embed_batch([clean_resume])[0]

        self.log("[3] Fetching jobs...")
        jobs = self.fetcher.fetch(query, location, radius, pages=2)
        df = pd.DataFrame(jobs)
        self.log(f"[3] Retrieved {len(df)} jobs.")

        self.log("[4] Scrubbing job data...")
        df = self.scrubber.scrub(df)

        # ---- IMPORTANT: embed job descriptions ----
        self.log("[5] Embedding job descriptions...")
        job_texts = df["description"].astype(str).tolist()
        job_vecs = self.embedder.embed_batch(job_texts)

        self.log("[6] Formatting + scoring jobs...")
        df = self.formatter.format(df, resume_vec, job_vecs)

        self.log("[7] Pipeline complete.")
        return df
