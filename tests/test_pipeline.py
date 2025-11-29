import pandas as pd
from core.pipeline.pipeline import Pipeline

class MockFetcher:
    def fetch(self, query, location, pages):
        return pd.DataFrame([
            {"title": "Test Job", "description": "Great job", "company": {"display_name": "TestCo"},
             "location": {"display_name": "City"}, "redirect_url": "http://example.com"}
        ])

class MockCleaner:
    def clean(self, text):
        return text.strip()

class MockEmbedder:
    def embed_batch(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

class MockScrubber:
    def scrub(self, df):
        return df

class MockFormatter:
    def format(self, df):
        return df

def logger(x):
    pass

def test_pipeline_runs_end_to_end():
    pipeline = Pipeline(
        fetcher=MockFetcher(),
        cleaner=MockCleaner(),
        embedder=MockEmbedder(),
        scrubber=MockScrubber(),
        formatter=MockFormatter(),
        logger=logger
    )
    resume_text = "My resume"
    df = pipeline.run(resume_text, "engineer", "St. Louis", 1)
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["title"] == "Test Job"
