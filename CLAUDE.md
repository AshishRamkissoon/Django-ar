# CLAUDE.md — AR Learning Platform

Full spec: [`requirements.md`](requirements.md) | Development plan: [`plan.md`](plan.md) | Progress: [`progress.md`](progress.md) | Git log: [`git.md`](git.md)

---

## Project

Django + HTMX + AR.js web app. Users scan real-world objects via browser camera; GPT-4o Vision identifies and explains them in an AR overlay. Small SaaS, ~1 000 users.

**Stack:** Python 3.11 · Django 4.2 · DRF · PostgreSQL 15 + pgvector · Redis · django-allauth (Google/GitHub) · HTMX · AR.js + A-Frame · Tailwind CSS · OpenAI SDK

---

## Project Structure

```
config/settings/   base.py · development.py · production.py
apps/accounts/     UserProfile, Fernet-encrypted API key, signals
apps/scanner/      scan endpoint, GPT-4o Vision service, ScanSession model
apps/learning/     LearningContent model, pgvector embeddings, semantic search
apps/core/         landing view, shared utilities
templates/         base.html, scanner/ar_view.html, partials/
```

---

## Security Rules — Never Break These

1. **No secrets in code.** All secrets live in `.env` only. Load via `python-dotenv`. `.env` is gitignored — `.env.example` (redacted) is committed.
2. **Per-user OpenAI keys are Fernet-encrypted at rest.** Decrypt in memory at request time only. Never log, return, or serialize the raw key.
3. **The platform's own `OPENAI_API_KEY` is for embeddings and moderation only** — never used for user-facing inference.
4. **Every GPT response is passed through `openai.moderations.create()` before being sent to the frontend.** Flagged responses return a safe fallback and set `ScanSession.moderation_flagged = True`.
5. **CSRF middleware is always enabled.** HTMX must send `X-CSRFToken` on all POST requests.
6. **Rate limit `POST /api/scan/`** — 10 requests / minute per authenticated user via `django-ratelimit`. Unauthenticated requests are blocked entirely.
7. **Never log:** raw image data, API keys, session tokens, or full request bodies from the scan endpoint.
8. **Input validation on scan endpoint:** reject Base64 payloads > 5 MB and non-JPEG data (HTTP 400).
9. **Production settings (`production.py`) require:** `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `X_FRAME_OPTIONS = "DENY"`.
10. **Pre-commit hook:** `detect-secrets` must pass before any commit. Run `detect-secrets scan > .secrets.baseline` once and commit the baseline.

---

## Development Conventions

- Settings: always import secrets with `os.environ["KEY"]` (not `.get()`) so missing vars fail loudly at startup.
- New apps go in `apps/` and must be registered in `config/settings/base.py`.
- All state-changing views require `@login_required`. AR scan view also requires `@ratelimit`.
- HTMX endpoints return rendered partials (`templates/.../partials/`), not JSON.
- OpenAI calls live in `apps/scanner/services.py` — views call the service, not the SDK directly.
- Migrations: `makemigrations` + `migrate` after every model change. Never edit existing migrations.
- Mock `openai.OpenAI` in all tests — never hit the real API in CI.

---

## Branch & Push Rules

```
main       ← production-ready only, tagged at each phase release
develop    ← integration; push after each phase passes its checklist
feature/*  ← one branch per feature, PR into develop
```

Push to GitHub after every phase. See `plan.md` for per-phase commit messages and checklists. Every push is recorded in `git.md`.

---

## Current Phase

Check [`progress.md`](progress.md) for the active phase and its checklist before starting any work.
When a phase is approved by the user: update `progress.md` (status → ✅, log in Change Log), push to GitHub, then record the push in `git.md`.

---

## Key Commands

```bash
# Setup
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Redis cache smoke test
python manage.py shell -c "from django.core.cache import cache; cache.set('k','v'); print(cache.get('k'))"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Embed learning content
python manage.py embed_learning_content

# Production check
python manage.py check --deploy

# Tests
pytest -q
```
