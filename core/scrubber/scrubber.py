import pandas as pd

class Scrubber:
    def scrub(self, df):
        if df is None or df.empty:
            return df

        df = df.copy()

        # Convert descriptions to string safely
        df["description"] = df["description"].astype(str)

        # Remove empty / whitespace / "None" / missing descriptions
        df = df[df["description"].notnull()]
        df = df[df["description"].str.strip() != ""]
        df = df[df["description"].str.lower() != "none"]

        return df.reset_index(drop=True)
