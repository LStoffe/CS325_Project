import pandas as pd
import numpy as np

class JobFormatter:
    """
    Formats job results:
      - Extracts company/location names
      - Computes cosine similarity using OpenAI vectors
      - Sorts by similarity score
    """

    def format(self, df: pd.DataFrame, resume_vec=None, job_vecs=None) -> pd.DataFrame:
        df = df.copy()

        if df.empty:
            return df

        # ---- Extract nested "display_name" fields ----
        if "company" in df.columns:
            df["company"] = df["company"].apply(
                lambda c: c.get("display_name") if isinstance(c, dict) else c
            )

        if "location" in df.columns:
            df["location"] = df["location"].apply(
                lambda loc: loc.get("display_name") if isinstance(loc, dict) else loc
            )

        # ---- REAL cosine similarity ----
        if resume_vec is not None and job_vecs is not None:
            resume_vec = np.array(resume_vec)
            scores = []

            for vec in job_vecs:
                vec = np.array(vec)

                num = np.dot(resume_vec, vec)
                den = np.linalg.norm(resume_vec) * np.linalg.norm(vec)
                sim = num / den if den != 0 else 0.0

                scores.append(float(sim))

            df["score"] = scores
        else:
            df["score"] = 1.0  # fallback

        # Sort highest score → lowest
        df = df.sort_values(by="score", ascending=False).reset_index(drop=True)
        return df
