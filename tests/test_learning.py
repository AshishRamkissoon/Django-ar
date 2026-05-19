import pytest
from unittest.mock import MagicMock
from apps.learning.models import LearningContent
from apps.scanner.services import embed_and_search, _cosine_similarity


# ── Cosine similarity (pure math, no DB) ─────────────────────────────────────

def test_cosine_similarity_identical_vectors():
    a = [1.0, 0.0, 0.0]
    assert _cosine_similarity(a, a) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_zero_vector():
    assert _cosine_similarity([0.0, 0.0], [1.0, 0.0]) == pytest.approx(0.0)


# ── embed_and_search ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_embed_and_search_empty_db_returns_empty(mock_openai):
    result = embed_and_search("anything")
    assert result == []
    mock_openai.embeddings.create.assert_not_called()


@pytest.mark.django_db
def test_embed_and_search_returns_top3(mock_openai):
    # 5 items with embeddings of decreasing similarity to query [1, 0, ...]
    scores = [1.0, 0.9, 0.8, 0.1, 0.05]
    for i, score in enumerate(scores):
        vec = [score] + [0.0] * 1535
        LearningContent.objects.create(
            title=f"Content {i}",
            body="body",
            embedding=vec,
            source_url=f"https://example.com/{i}",
        )

    query_vec = [1.0] + [0.0] * 1535
    mock_embedding = MagicMock()
    mock_embedding.data[0].embedding = query_vec
    mock_openai.embeddings.create.return_value = mock_embedding

    results = embed_and_search("test label")

    assert len(results) == 3
    assert results[0]["title"] == "Content 0"
    assert results[1]["title"] == "Content 1"
    assert results[2]["title"] == "Content 2"


@pytest.mark.django_db
def test_embed_and_search_skips_items_without_embedding(mock_openai):
    LearningContent.objects.create(title="No embed", body="x", embedding=None)
    result = embed_and_search("test")
    assert result == []
    mock_openai.embeddings.create.assert_not_called()
