import base64
import hashlib
import pytest
from unittest.mock import MagicMock
from django.core.cache import cache
from apps.scanner.models import ScanSession
from apps.scanner import services

# Minimal valid JPEG (magic bytes \xff\xd8 followed by padding)
JPEG_B64 = base64.b64encode(b"\xff\xd8\xff\xe0" + b"\x00" * 100).decode()


# ── Auth / input validation ─────────────────────────────────────────────────

@pytest.mark.django_db
def test_scan_requires_auth(client):
    r = client.post("/api/scan/", {"image": JPEG_B64})
    assert r.status_code == 302
    assert "/accounts/login/" in r["Location"]


@pytest.mark.django_db
def test_scan_empty_image_returns_400(client, api_key_user):
    client.force_login(api_key_user)
    r = client.post("/api/scan/", {"image": ""})
    assert r.status_code == 400


@pytest.mark.django_db
def test_scan_non_jpeg_returns_400(client, api_key_user):
    client.force_login(api_key_user)
    png_b64 = base64.b64encode(b"\x89PNG\r\n" + b"\x00" * 50).decode()
    r = client.post("/api/scan/", {"image": png_b64})
    assert r.status_code == 400


@pytest.mark.django_db
def test_scan_no_api_key_returns_400(client, user, mock_openai):
    client.force_login(user)
    r = client.post("/api/scan/", {"image": JPEG_B64})
    assert r.status_code == 400


# ── Cache hit ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_scan_cache_hit_skips_openai(client, api_key_user, mock_openai):
    cache_key = "scan:" + hashlib.sha256(JPEG_B64.encode()).hexdigest()
    cached = {
        "label": "Cached Object",
        "explanation": "From cache.",
        "related_topics": ["A", "B"],
        "related_content": [],
        "tokens_used": 0,
        "flagged": False,
    }
    cache.set(cache_key, cached, 3600)

    client.force_login(api_key_user)
    r = client.post("/api/scan/", {"image": JPEG_B64})

    assert r.status_code == 200
    mock_openai.chat.completions.create.assert_not_called()


# ── Moderation flag ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_scan_moderation_flagged(client, api_key_user, mock_openai):
    # Vision response
    completion = MagicMock()
    completion.choices[0].message.content = (
        '{"label": "Knife", "explanation": "Sharp weapon.", "related_topics": ["violence"]}'
    )
    completion.usage.total_tokens = 42
    mock_openai.chat.completions.create.return_value = completion

    # Moderation: flagged
    moderation = MagicMock()
    moderation.results[0].flagged = True
    mock_openai.moderations.create.return_value = moderation

    # Embeddings
    embedding = MagicMock()
    embedding.data[0].embedding = [0.1] * 1536
    mock_openai.embeddings.create.return_value = embedding

    client.force_login(api_key_user)
    r = client.post("/api/scan/", {"image": JPEG_B64})

    assert r.status_code == 200
    session = ScanSession.objects.filter(user=api_key_user).last()
    assert session.moderation_flagged is True
    assert session.explanation == services.SAFE_FALLBACK


# ── Successful scan ──────────────────────────────────────────────────────────

@pytest.mark.django_db
def test_scan_success_saves_session(client, api_key_user, mock_openai):
    completion = MagicMock()
    completion.choices[0].message.content = (
        '{"label": "Apple", "explanation": "A fruit.", "related_topics": ["Nutrition", "Farming"]}'
    )
    completion.usage.total_tokens = 30
    mock_openai.chat.completions.create.return_value = completion

    moderation = MagicMock()
    moderation.results[0].flagged = False
    mock_openai.moderations.create.return_value = moderation

    embedding = MagicMock()
    embedding.data[0].embedding = [0.5] * 1536
    mock_openai.embeddings.create.return_value = embedding

    client.force_login(api_key_user)
    r = client.post("/api/scan/", {"image": JPEG_B64})

    assert r.status_code == 200
    session = ScanSession.objects.filter(user=api_key_user).last()
    assert session.object_label == "Apple"
    assert session.moderation_flagged is False

    api_key_user.profile.refresh_from_db()
    assert api_key_user.profile.scan_count == 1
