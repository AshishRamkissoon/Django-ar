from django.db import models
from django.contrib.auth import get_user_model
from cryptography.fernet import Fernet
from django.conf import settings

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    openai_api_key_encrypted = models.TextField(blank=True)
    scan_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_api_key(self, raw_key: str):
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        self.openai_api_key_encrypted = f.encrypt(raw_key.encode()).decode()

    def get_api_key(self) -> str:
        if not self.openai_api_key_encrypted:
            return ""
        f = Fernet(settings.ENCRYPTION_KEY.encode())
        return f.decrypt(self.openai_api_key_encrypted.encode()).decode()

    def has_api_key(self) -> bool:
        return bool(self.openai_api_key_encrypted)

    def __str__(self):
        return f"Profile({self.user.email})"
