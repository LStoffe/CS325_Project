# core/formatter/job_formatter.py

class JobFormatter:
    def format(self, df):
        df = df.copy()

        # Extract clean company names
        def clean_company(c):
            if isinstance(c, dict):
                return c.get("display_name", "")
            return str(c)

        # Extract clean location names
        def clean_location(loc):
            if isinstance(loc, dict):
                # Prefer display_name if available
                if "display_name" in loc:
                    return loc["display_name"]
                # Otherwise join the 'area' array
                if "area" in loc and isinstance(loc["area"], list):
                    return ", ".join(loc["area"])
            return str(loc)

        df["company"] = df["company"].apply(clean_company)
        df["location"] = df["location"].apply(clean_location)

        keep = ["title", "company", "location", "description", "redirect_url"]
        return df[keep]
