import numpy as np
import pytest
from core.utils.similarity import cosine_similarity

def test_cosine_similarity_identical():
    a = np.array([1, 2, 3])
    b = np.array([1, 2, 3])
    assert cosine_similarity(a, b) == pytest.approx(1.0)

def test_cosine_similarity_orthogonal():
    a = np.array([1, 0])
    b = np.array([0, 1])
    assert cosine_similarity(a, b) == pytest.approx(0.0)
