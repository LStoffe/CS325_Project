
import pandas as pd
from core.utils.similarity import cosine_similarity

class Pipeline:
    def __init__(self, fetcher, cleaner, embedder, scrubber, formatter, logger):
        self.fetcher=fetcher
        self.cleaner=cleaner
        self.embedder=embedder
        self.scrubber=scrubber
        self.formatter=formatter
        self.log=logger

    def run(self, resume_text, query, location, radius):
        self.log("[1] Cleaning resume...")
        clean_resume=self.cleaner.clean(resume_text)

        self.log("[2] Embedding resume...")
        resume_vec=self.embedder.embed_batch([clean_resume])[0]

        self.log("[3] Fetching jobs...")
        jobs=self.fetcher.fetch(query, location, radius, pages=2)
        df=pd.DataFrame(jobs)
        self.log(f"[Fetch] Got {len(df)} jobs")

        self.log("[4] Scrubbing jobs...")
        df=self.scrubber.scrub(df)

        self.log("[5] Formatting jobs...")
        df=self.formatter.format(df)

        self.log("[6] Embedding job descriptions...")
        job_embeddings=self.embedder.embed_batch(df["description"].tolist())
        df["embedding"]=job_embeddings

        self.log("[7] Calculating similarity scores...")
        df["score"]=df["embedding"].apply(lambda v: cosine_similarity(resume_vec, v))

        self.log("[8] Ranking...")
        df=df.sort_values("score", ascending=False).head(10)

        return df
