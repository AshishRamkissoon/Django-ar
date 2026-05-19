from django.core.management.base import BaseCommand
from django.conf import settings
from openai import OpenAI
from apps.learning.models import LearningContent


class Command(BaseCommand):
    help = "Generate embeddings for all LearningContent records that are missing one."

    def handle(self, *args, **kwargs):
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        items = LearningContent.objects.filter(embedding=None)
        total = items.count()

        if total == 0:
            self.stdout.write("All items already have embeddings.")
            return

        self.stdout.write(f"Embedding {total} items...")
        for item in items:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=item.title,
            )
            item.embedding = response.data[0].embedding
            item.save(update_fields=["embedding"])
            self.stdout.write(f"  OK: {item.title}")

        self.stdout.write(self.style.SUCCESS(f"Done — {total} items embedded."))
