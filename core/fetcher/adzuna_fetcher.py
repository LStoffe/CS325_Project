
import requests

class AdzunaFetcher:
    BASE = "https://api.adzuna.com/v1/api/jobs/us/search/{page}"

    def __init__(self, app_id, app_key, logger):
        self.app_id=app_id
        self.app_key=app_key
        self.log=logger

    def fetch(self, query, location, radius, pages=2):
        results=[]
        for page in range(1,pages+1):
            url=self.BASE.format(page=page)
            params={
                "app_id": self.app_id,
                "app_key": self.app_key,
                "results_per_page":50,
                "what":query,
                "where":location,
                "distance":radius
            }
            self.log(f"[Fetch] Page {page}")
            try:
                r=requests.get(url, params=params, timeout=10)
                r.raise_for_status()
                data=r.json()
                results.extend(data.get("results",[]))
            except Exception as e:
                self.log(f"[Error] {e}")
        return results
