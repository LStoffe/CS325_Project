import requests
from cachecontrol import CacheControl
import pandas as pd
import time
import re

def extract_requirements(description):
    """
    Extract requirements section from a job description.
    Looks for keywords or bullet-point style lists.
    """
    if not description:
        return None
    
    # Normalize line breaks
    text = description.replace("\r", "")
    
    # 1. Look for keywords like "Requirements:", "Qualifications:", or "Skills:"
    pattern = re.compile(r"(Requirements|Qualifications|Skills)[:\-]\s*(.*)", re.IGNORECASE | re.DOTALL)
    match = pattern.search(text)
    if match:
        return text[match.start():].strip()
    
    # 2. Look for bullet points or numbered lists (common in requirements sections)
    bullet_pattern = re.compile(r"(^[\-\•\*]\s+.+|^\d+\.\s+.+)", re.MULTILINE)
    matches = bullet_pattern.findall(text)
    if matches:
        return "\n".join(matches).strip()
    
    return None


def fetch_jobs(app_id, app_key, location="St. Louis, MO", query="computer science", max_results=100, use_cache=True):
    session = CacheControl(requests.Session()) if use_cache else requests.Session()
    
    all_jobs = []
    page = 1
    results_per_page = 20
    
    while len(all_jobs) < max_results:
        url = f"https://api.adzuna.com/v1/api/jobs/us/search/{page}"
        params = {
            "app_id": app_id,
            "app_key": app_key,
            "results_per_page": results_per_page,
            "where": location,
            "what": query,
            "content-type": "application/json"
        }

        response = session.get(url, params=params)
        
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code} - {response.text}")
            break

        data = response.json()

        if "results" not in data or not data["results"]:
            print("⚠️ No jobs found on this page.")
            print("Request URL:", response.url)
            print("Raw Response:", data)
            break

        for job in data["results"]:
            description = job.get("description") or ""
            requirements = extract_requirements(description)
            
            job_data = {
                "Title": job.get("title"),
                "Company": job.get("company", {}).get("display_name"),
                "Location": job.get("location", {}).get("display_name"),
                "Category": job.get("category", {}).get("label"),
                "Salary": job.get("salary_is_predicted"),
                "RedirectURL": job.get("redirect_url"),
                "FullDescription": description,
                "Requirements": requirements
            }
            all_jobs.append(job_data)

        print(f"✅ Page {page} fetched. Total jobs collected: {len(all_jobs)}")

        if not data["results"]:
            break

        page += 1
        time.sleep(2)

    return all_jobs[:max_results]


if __name__ == "__main__":
    print("🔑 Enter your Adzuna API credentials")
    app_id = input("App ID: ").strip()
    app_key = input("App Key: ").strip()

    print("\n📡 Fetching computer science jobs from Adzuna (St. Louis, MO)...")
    jobs = fetch_jobs(app_id, app_key)

    if jobs:
        df = pd.DataFrame(jobs)
        df.to_csv("adzuna_cs_jobs.csv", index=False)
        print(f"\n💾 Saved {len(jobs)} jobs to adzuna_cs_jobs.csv")
    else:
        print("\n⚠️ No jobs found. Try broadening your search.")