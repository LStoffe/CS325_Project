import pandas as pd
from core.formatter.job_formatter import JobFormatter

def test_formatter_extracts_company_and_location():
    df = pd.DataFrame([
        {
            "title": "Software Engineer",
            "company": {"display_name": "Omni Federal"},
            "location": {"display_name": "St. Louis, MO"},
            "description": "Job desc",
            "redirect_url": "http://example.com"
        }
    ])
    fmt = JobFormatter()
    out = fmt.format(df)
    assert out.iloc[0]["company"] == "Omni Federal"
    assert out.iloc[0]["location"] == "St. Louis, MO"
