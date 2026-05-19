import pytest
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile

User = get_user_model()


@pytest.mark.django_db
def test_encryption_round_trip(user):
    raw = "sk-test-supersecretkey123"  # pragma: allowlist secret
    user.profile.set_api_key(raw)
    user.profile.save()
    assert user.profile.get_api_key() == raw


@pytest.mark.django_db
def test_encrypted_value_differs_from_raw(user):
    raw = "sk-test-abc123"  # pragma: allowlist secret
    user.profile.set_api_key(raw)
    assert user.profile.openai_api_key_encrypted != raw
    assert len(user.profile.openai_api_key_encrypted) > len(raw)


@pytest.mark.django_db
def test_has_api_key_false_when_empty(user):
    assert user.profile.get_api_key() == ""
    assert user.profile.has_api_key() is False


@pytest.mark.django_db
def test_has_api_key_true_after_set(user):
    user.profile.set_api_key("sk-test-key")  # pragma: allowlist secret
    assert user.profile.has_api_key() is True


@pytest.mark.django_db
def test_profile_auto_created_on_user_save(db):
    u = User.objects.create_user(
        username="newuser",
        email="new@example.com",
        password="pass",  # pragma: allowlist secret
    )
    assert UserProfile.objects.filter(user=u).exists()
