
class Scrubber:
    def scrub(self, df):
        df = df.copy()
        df.dropna(subset=["description","title"], inplace=True)
        df["description"] = df["description"].astype(str)
        return df
