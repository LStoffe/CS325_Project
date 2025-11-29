import pytest
from core.cleaner.resume_cleaner import ResumeCleaner

def test_resume_cleaner_basic():
    cleaner = ResumeCleaner()
    text = "Hello\n\n\nWorld!\t\tThis is   a  test."
    result = cleaner.clean(text)
    assert "  " not in result
    assert "\t" not in result
    assert "\n\n" not in result
    assert "Hello" in result
    assert "World!" in result
