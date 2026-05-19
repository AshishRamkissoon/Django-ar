from django.db import models


class LearningContent(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    embedding = models.JSONField(null=True, blank=True)  # list of floats (dim=1536)
    tags = models.JSONField(default=list)
    source_url = models.URLField(blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
