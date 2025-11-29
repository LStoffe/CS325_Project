import pandas as pd
from core.pipeline.pipeline import Pipeline

# ================
# MOCK COMPONENTS
# ================

class MockFetcher:
    def fetch(self, query, location, radius, pages=1):
        # Simple mock returning two fake jobs
        return [
            {"title": "Job A", "description": "A great job"},
            {"title": "Job B", "description": "Another job"},
        ]

class MockCleaner:
    def clean(self, text):
        return text.strip()

class MockEmbedder:
    # embed_batch returns vectors as simple lists of numbers
    def embed_batch(self, texts):
        return [[1, 0, 0] for _ in texts]

class MockScrubber:
    def scrub(self, df):
        return df  # pass-through

class MockFormatter:
    # IMPORTANT: signature must match real formatter
    def format(self, df, resume_vec=None, job_vecs=None):
        return df  # pass-through


# ================
# TESTS
# ================
def test_pipeline_runs_end_to_end():
    pipeline = Pipeline(
        fetcher=MockFetcher(),
        cleaner=MockCleaner(),
        embedder=MockEmbedder(),
        scrubber=MockScrubber(),
        formatter=MockFormatter(),
        logger=lambda x: None,
    )

    df = pipeline.run("My resume", "engineer", "St. Louis", 1)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2  # matches MockFetcher
