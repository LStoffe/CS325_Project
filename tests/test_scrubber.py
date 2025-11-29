import pandas as pd
from core.scrubber.scrubber import Scrubber

def test_scrubber_removes_empty_descriptions():
    df = pd.DataFrame([
        {"title": "A", "description": "Good job"},
        {"title": "B", "description": ""},
        {"title": "C", "description": None}
    ])
    scrubber = Scrubber()
    out = scrubber.scrub(df)
    assert len(out) == 1
    assert out.iloc[0]["title"] == "A"
