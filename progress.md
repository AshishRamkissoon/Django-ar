# Progress Tracker

> Updated manually after each phase milestone. Reference: [`plan.md`](plan.md)
> Status key: `⬜ Not Started` · `🔄 In Progress` · `✅ Completed` · `❌ Blocked`

---

## Phase Summary

| Phase | Name | Status | Started | Completed |
|---|---|---|---|---|
| 1 | Project Foundation & Repository Setup | ✅ Completed | 2026-05-19 | 2026-05-19 |
| 2 | Authentication & User Profiles | ✅ Completed | 2026-05-19 | 2026-05-19 |
| 3 | OpenAI Backend | ✅ Completed | 2026-05-19 | 2026-05-19 |
| 4 | WebAR Frontend | ✅ Completed | 2026-05-19 | 2026-05-19 |
| 5 | Security Hardening | ✅ Completed | 2026-05-19 | 2026-05-19 |
| 6 | Testing & Production Readiness | ✅ Completed | 2026-05-19 | 2026-05-19 |

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

**Status:** ✅ Completed — 2026-05-19  
**Depends on:** Phase 1 ✅

### Checklist
- [ ] `django-allauth` installed and configured
- [ ] Google OAuth app created and wired
- [ ] GitHub OAuth app created and wired
- [ ] Login with Google → redirects to `/ar/`
- [ ] Login with GitHub → redirects to `/ar/`
- [ ] `UserProfile` model created and migrated
- [ ] `UserProfile` auto-created on first login (signal)
- [x] `ENCRYPTION_KEY` wired to `base.py`
- [x] `set_api_key()` encrypts with Fernet
- [x] `get_api_key()` decrypts correctly (verified in shell)
- [x] Profile page (`/accounts/profile/`) renders and saves key
- [x] Encrypted value in DB differs from raw key
- [x] Logout clears session (allauth logout view wired)

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 3 — OpenAI Backend

**Status:** ✅ Completed — 2026-05-19  
**Depends on:** Phase 2 ✅

### Checklist
- [x] `openai` and `numpy` installed (pgvector replaced with numpy cosine similarity)
- [x] `ScanSession` model created and migrated
- [x] `LearningContent` model with `JSONField` embedding created and migrated
- [x] `apps/scanner/services.py` — `scan_object()` implemented
- [x] Cache hit/miss logic working (in-memory for dev)
- [x] GPT-4o Vision call returns `label` + `explanation` JSON ✓ live tested
- [x] OpenAI Moderation API gates every response
- [x] Flagged content returns safe fallback; `moderation_flagged=True` saved to DB
- [x] `embed_and_search()` returns top-3 related content via cosine similarity
- [x] `ScanSession` row saved after each scan ✓ verified
- [x] `scan_count` on `UserProfile` incremented ✓ verified
- [x] User with no API key → ValueError with clear error message
- [x] Management command `embed_learning_content` created
- [x] `POST /api/scan/` and `GET /api/history/` URLs wired
- [x] Input validation: size + JPEG magic byte check

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 4 — WebAR Frontend

**Status:** ✅ Completed — 2026-05-19  
**Depends on:** Phase 3 ✅

### Checklist
- [x] `templates/base.html` with Tailwind, HTMX, CSRF config
- [x] `templates/core/landing.html` — hero + "Sign in" CTA
- [x] `templates/accounts/login.html` — Google + GitHub buttons
- [x] `templates/accounts/profile.html` — masked API key + update form
- [x] `templates/scanner/ar_view.html` — A-Frame scene + Scan button
- [x] `captureAndScan()` JS captures video frame to Base64
- [x] HTMX form posts frame to `/api/scan/` with CSRF token
- [x] Loading spinner shown while waiting for response
- [x] `templates/scanner/partials/result.html` — label + explanation + related links
- [x] Explanation partial injected over camera feed on success
- [x] `templates/scanner/history.html` — paginated scan history
- [x] Desktop fallback: plain `<video>` + explanation below when no camera
- [x] Landing page redirects authenticated users to `/ar/`
- [x] All pages mobile-responsive

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 5 — Security Hardening

**Status:** ✅ Completed — 2026-05-19  
**Depends on:** Phase 4 ✅

### Checklist
- [x] `django-ratelimit` applied to `POST /api/scan/` (10 req/min per user)
- [x] 11th request within 1 min → HTTP 429 HTMX fragment (`scanner/partials/ratelimit.html`)
- [x] Unauthenticated POST → HTTP 302 to login (verified via test client)
- [x] `django-cors-headers` installed; `CORS_ALLOWED_ORIGINS` explicit in production
- [x] `CsrfViewMiddleware` confirmed in `MIDDLEWARE`
- [x] POST without CSRF token → HTTP 403 (verified via test client)
- [x] Production HTTPS headers set in `production.py`
- [x] Input validation: oversized image (> 5 MB) → HTTP 400
- [x] Input validation: non-JPEG Base64 → HTTP 400
- [x] `detect-secrets` installed; `.secrets.baseline` committed
- [x] Pre-commit hook installed (`pre-commit install`)
- [x] `detect-secrets scan` finds zero new secrets
- [x] Logging configured — keys and image data never logged
- [x] `python manage.py check` passes with 0 issues

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Phase 6 — Testing & Production Readiness

**Status:** ✅ Completed — 2026-05-19  
**Depends on:** Phase 5 ✅

### Checklist
- [x] `tests/conftest.py` — fixtures: test user, mock OpenAI
- [x] `tests/test_accounts.py` — encryption round-trip test passes
- [x] `tests/test_scanner.py` — auth required, cache hit, moderation flag tests pass
- [x] `tests/test_learning.py` — semantic search returns top-3
- [x] `pytest -q` — 18 tests, all green
- [x] `whitenoise` installed; `collectstatic` runs without errors (159 files)
- [x] `Procfile` created
- [x] `README.md` written and reviewed
- [x] `python manage.py check --deploy` — zero issues
- [ ] End-to-end scan tested on real mobile browser (manual — requires physical device)
- [x] No `.env` or secrets in `git log --all`
- [x] `develop` merged to `main` with `--no-ff`
- [x] `v1.0.0` tag created and pushed

### Notes
<!-- Add any blockers, decisions, or deviations from plan here -->

---

## Change Log

| Date | Phase | Event |
|---|---|---|
| 2026-05-19 | — | `progress.md` created; all phases initialised as Not Started |
| 2026-05-19 | Phase 1 | Started and completed — scaffold, settings, DB, migrations, push to GitHub |
| 2026-05-19 | Phase 2 | Started and completed — allauth, UserProfile, Fernet encryption, templates, push to GitHub |
| 2026-05-19 | Phase 3 | Started and completed — GPT-4o Vision, moderation, cache, embeddings, live API test passed |
| 2026-05-19 | Phase 4 | Started and completed — A-Frame + AR.js, HTMX scan flow, Tailwind UI, all routes verified |
| 2026-05-19 | Phase 5 | Started and completed — ratelimit, CSRF/CORS, detect-secrets baseline, pre-commit hook |
| 2026-05-19 | Phase 6 | Started and completed — 18 tests green, WhiteNoise, Procfile, README, deploy check, v1.0.0 tagged |
