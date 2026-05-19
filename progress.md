# Progress Tracker

> Updated manually after each phase milestone. Reference: [`plan.md`](plan.md)
> Status key: `⬜ Not Started` · `🔄 In Progress` · `✅ Completed` · `❌ Blocked`

---

## Phase Summary

| Phase | Name | Status | Started | Completed |
|---|---|---|---|---|
| 1 | Project Foundation & Repository Setup | ✅ Completed | 2026-05-19 | 2026-05-19 |
| 2 | Authentication & User Profiles | 🔄 In Progress | 2026-05-19 | — |
| 3 | OpenAI Backend | ⬜ Not Started | — | — |
| 4 | WebAR Frontend | ⬜ Not Started | — | — |
| 5 | Security Hardening | ⬜ Not Started | — | — |
| 6 | Testing & Production Readiness | ⬜ Not Started | — | — |

---

## Phase 1 — Project Foundation & Repository Setup

**Status:** ✅ Completed — 2026-05-19

### Checklist
- [x] Django project scaffold created (`config/`, `apps/`, `templates/`)
- [x] Settings split into `base.py`, `development.py`, `production.py`
- [x] `.env` created and gitignored; `.env.example` committed
- [x] `.gitignore` in place
- [x] PostgreSQL connected and `migrate` runs clean
- [x] In-memory cache configured for dev (Redis for production)
- [x] `requirements.txt` written with all pinned deps
- [x] `python manage.py check` passes with 0 issues
- [x] Cache smoke test passes (`Cache OK: v`)
- [x] `.env` does NOT appear in `git status`

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 2 — Authentication & User Profiles

**Status:** 🔄 In Progress — 2026-05-19  
**Depends on:** Phase 1 ✅

### Checklist
- [ ] `django-allauth` installed and configured
- [ ] Google OAuth app created and wired
- [ ] GitHub OAuth app created and wired
- [ ] Login with Google → redirects to `/ar/`
- [ ] Login with GitHub → redirects to `/ar/`
- [ ] `UserProfile` model created and migrated
- [ ] `UserProfile` auto-created on first login (signal)
- [ ] `ENCRYPTION_KEY` wired to `base.py`
- [ ] `set_api_key()` encrypts with Fernet
- [ ] `get_api_key()` decrypts correctly (verified in shell)
- [ ] Profile page (`/accounts/profile/`) renders and saves key
- [ ] Encrypted value in DB differs from raw key
- [ ] Logout clears session

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 3 — OpenAI Backend

**Status:** ⬜ Not Started  
**Depends on:** Phase 2 ✅

### Checklist
- [ ] `openai` and `pgvector` installed
- [ ] `pgvector` extension enabled in PostgreSQL
- [ ] `ScanSession` model created and migrated
- [ ] `LearningContent` model with `VectorField` created and migrated
- [ ] `apps/scanner/services.py` — `scan_object()` implemented
- [ ] Redis cache hit/miss logic working (verified by log)
- [ ] GPT-4o Vision call returns `label` + `explanation` JSON
- [ ] OpenAI Moderation API gates every response
- [ ] Flagged content returns safe fallback; `moderation_flagged=True` saved to DB
- [ ] `embed_and_search()` returns top-3 related content via cosine similarity
- [ ] `ScanSession` row saved after each scan
- [ ] `scan_count` on `UserProfile` incremented
- [ ] User with no API key → HTTP 400 with clear error
- [ ] Management command `embed_learning_content` works
- [ ] `POST /api/scan/` and `GET /api/history/` URLs wired

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 4 — WebAR Frontend

**Status:** ⬜ Not Started  
**Depends on:** Phase 3 ✅

### Checklist
- [ ] `templates/base.html` with Tailwind, HTMX, CSRF config
- [ ] `templates/core/landing.html` — hero + "Sign in" CTA
- [ ] `templates/accounts/login.html` — Google + GitHub buttons
- [ ] `templates/accounts/profile.html` — masked API key + update form
- [ ] `templates/scanner/ar_view.html` — A-Frame scene + Scan button
- [ ] `captureAndScan()` JS captures video frame to Base64
- [ ] HTMX form posts frame to `/api/scan/` with CSRF token
- [ ] Loading spinner shown while waiting for response
- [ ] `templates/scanner/partials/result.html` — label + explanation + related links
- [ ] Explanation partial injected over camera feed on success
- [ ] `templates/scanner/history.html` — paginated scan history
- [ ] Desktop fallback: plain `<video>` + explanation below when no camera
- [ ] Landing page redirects authenticated users to `/ar/`
- [ ] All pages mobile-responsive

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 5 — Security Hardening

**Status:** ⬜ Not Started  
**Depends on:** Phase 4 ✅

### Checklist
- [ ] `django-ratelimit` applied to `POST /api/scan/` (10 req/min per user)
- [ ] 11th request within 1 min → HTTP 429 HTMX fragment
- [ ] Unauthenticated POST → HTTP 302 to login
- [ ] `django-cors-headers` installed; `CORS_ALLOWED_ORIGINS` explicit in production
- [ ] `CsrfViewMiddleware` confirmed in `MIDDLEWARE`
- [ ] POST without CSRF token → HTTP 403
- [ ] Production HTTPS headers set in `production.py`
- [ ] Input validation: oversized image (> 5 MB) → HTTP 400
- [ ] Input validation: non-JPEG Base64 → HTTP 400
- [ ] `detect-secrets` installed; `.secrets.baseline` committed
- [ ] Pre-commit hook installed (`pre-commit install`)
- [ ] `detect-secrets scan` finds zero new secrets
- [ ] Logging configured — keys and image data never logged
- [ ] `python manage.py check --deploy` passes with no critical warnings

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 6 — Testing & Production Readiness

**Status:** ⬜ Not Started  
**Depends on:** Phase 5 ✅

### Checklist
- [ ] `tests/conftest.py` — fixtures: test user, mock OpenAI
- [ ] `tests/test_accounts.py` — encryption round-trip test passes
- [ ] `tests/test_scanner.py` — auth required, cache hit, moderation flag tests pass
- [ ] `tests/test_learning.py` — semantic search returns top-3
- [ ] `pytest -q` — all tests green
- [ ] `whitenoise` installed; `collectstatic` runs without errors
- [ ] `Procfile` created
- [ ] `README.md` written and reviewed
- [ ] `python manage.py check --deploy` — zero issues
- [ ] End-to-end scan tested on real mobile browser (Chrome Android or Safari iOS)
- [ ] No `.env` or secrets in `git log --all`
- [ ] `develop` merged to `main` with `--no-ff`
- [ ] `v1.0.0` tag created and pushed

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Change Log

| Date | Phase | Event |
|---|---|---|
| 2026-05-19 | — | `progress.md` created; all phases initialised as Not Started |
| 2026-05-19 | Phase 1 | Started and completed — scaffold, settings, DB, migrations, push to GitHub |
