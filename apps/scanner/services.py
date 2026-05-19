import hashlib
import json
import logging
import numpy as np
from django.core.cache import cache
from django.conf import settings
from openai import OpenAI

from apps.learning.models import LearningContent
from .models import ScanSession

logger = logging.getLogger("apps.scanner")

SYSTEM_PROMPT = """You are an educational AI assistant. Given an image:
1. Identify the main object or subject.
2. Provide a clear, engaging educational explanation (3-5 sentences) suitable for a curious learner.
3. Suggest exactly 2 related topics the learner could explore next.
Respond ONLY with valid JSON in this exact format:
{"label": "...", "explanation": "...", "related_topics": ["...", "..."]}"""

SAFE_FALLBACK = "This content could not be displayed. Please try scanning a different object."


def _get_client(user):
    api_key = user.profile.get_api_key()
    if not api_key:
        raise ValueError("No OpenAI API key configured. Please add your key in Profile.")
    return OpenAI(api_key=api_key)


def _platform_client():
    return OpenAI(api_key=settings.OPENAI_API_KEY)


def _moderate(client, text: str) -> bool:
    """Returns True if content is flagged."""
    try:
        result = client.moderations.create(input=text)
        flagged = result.results[0].flagged
        if flagged:
            logger.warning("Moderation flagged content for scan.")
        return flagged
    except Exception as e:
        logger.error("Moderation API error: %s", e)
        return False


def _cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denom) if denom else 0.0


def embed_and_search(label: str) -> list[dict]:
    """Embed label and return top-3 related LearningContent items."""
    items = LearningContent.objects.exclude(embedding=None)
    if not items.exists():
        return []
    try:
        client = _platform_client()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=label,
        )
        query_vec = response.data[0].embedding
        scored = [
            (item, _cosine_similarity(query_vec, item.embedding))
            for item in items
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [
            {"title": item.title, "source_url": item.source_url}
            for item, _ in scored[:3]
        ]
    except Exception as e:
        logger.error("Embedding/search error: %s", e)
        return []


def scan_object(user, base64_image: str) -> dict:
    """
    Core scan pipeline:
    1. Cache check  2. Vision call  3. Moderation  4. Semantic search
    5. Cache store  6. Persist session
    """
    cache_key = "scan:" + hashlib.sha256(base64_image.encode()).hexdigest()
    cached = cache.get(cache_key)
    if cached:
        logger.info("Cache HIT for scan (user=%s)", user.email)
        return cached

    logger.info("Cache MISS — calling GPT-4o Vision (user=%s)", user.email)
    client = _get_client(user)

    # Vision call
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "low",
                            },
                        },
                        {"type": "text", "text": "What is in this image?"},
                    ],
                },
            ],
            max_tokens=512,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        logger.error("GPT-4o Vision error: %s", e)
        raise RuntimeError(f"AI scan failed: {e}")

    tokens_used = response.usage.total_tokens
    raw = response.choices[0].message.content

    try:
        data = json.loads(raw)
        label = data.get("label", "Unknown object")
        explanation = data.get("explanation", "")
        related_topics = data.get("related_topics", [])
    except (json.JSONDecodeError, AttributeError):
        label = "Unknown object"
        explanation = raw
        related_topics = []

    # Moderation gate
    flagged = _moderate(client, explanation)
    if flagged:
        explanation = SAFE_FALLBACK

    # Semantic search for related content
    related_content = embed_and_search(label)

    result = {
        "label": label,
        "explanation": explanation,
        "related_topics": related_topics,
        "related_content": related_content,
        "tokens_used": tokens_used,
        "flagged": flagged,
    }

    # Cache for 1 hour
    cache.set(cache_key, result, timeout=3600)

    # Persist session
    image_hash = hashlib.sha256(base64_image.encode()).hexdigest()
    ScanSession.objects.create(
        user=user,
        image_hash=image_hash,
        object_label=label,
        explanation=explanation,
        related_content=related_content,
        moderation_flagged=flagged,
        tokens_used=tokens_used,
    )

    # Increment scan count
    profile = user.profile
    profile.scan_count += 1
    profile.save(update_fields=["scan_count"])

    return result
