from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ScanSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans")
    image_hash = models.CharField(max_length=64, db_index=True)
    object_label = models.CharField(max_length=255, blank=True)
    explanation = models.TextField(blank=True)
    related_content = models.JSONField(default=list)
    moderation_flagged = models.BooleanField(default=False)
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} — {self.object_label} ({self.created_at:%Y-%m-%d})"
