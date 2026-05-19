import pytest
from unittest.mock import MagicMock, patch
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def mock_openai():
    """Patch OpenAI so no test ever hits the real API."""
    with patch("apps.scanner.services.OpenAI") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture(autouse=True)
def clear_cache():
    yield
    from django.core.cache import cache
    cache.clear()


@pytest.fixture
def user(db):
    u = User.objects.create_user(
        username="tester",
        email="tester@example.com",
        password="testpass123",  # pragma: allowlist secret
    )
    return u


@pytest.fixture
def api_key_user(user):
    user.profile.set_api_key("sk-test-fakekey1234567890abcdef")  # pragma: allowlist secret
    user.profile.save()
    return user
