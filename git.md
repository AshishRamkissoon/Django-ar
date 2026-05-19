# Git Push Log

> Every push to GitHub is recorded here. Reference: [`plan.md`](plan.md)
> Format: date · branch · tag · commit message · status

---

## Repository

| Key | Value |
|---|---|
| Remote | `origin` (GitHub) |
| Main branch | `main` |
| Integration branch | `develop` |
| Feature branches | `feature/<name>` |
| Strategy | Push to `develop` after each phase; merge to `main` + tag at Phase 6 |

---

## Push History

| # | Date | Branch | Tag | Commit Message | Status |
|---|---|---|---|---|---|
| 1 | 2026-05-19 | `develop` | — | `phase 1: project scaffold, settings split, env config` | ✅ Pushed |
| 2 | 2026-05-19 | `develop` | — | `phase 2: OAuth login, UserProfile, encrypted API key storage` | ✅ Pushed |
| 3 | 2026-05-19 | `develop` | — | `phase 3: GPT-4o Vision scan, moderation, cache, embeddings search` | ✅ Pushed |
| 4 | 2026-05-19 | `develop` | — | `phase 4: AR.js + A-Frame frontend, HTMX scan flow, Tailwind UI` | ✅ Pushed |
| 5 | 2026-05-19 | `develop` | — | `phase 5: rate limiting, CORS, HTTPS headers, input validation, secret scanning` | ✅ Pushed |

---

## Phase Push Targets

These are the planned pushes defined in `plan.md`. Check each off when done.

### Phase 1 — Project Foundation ✅
- [x] **Branch:** `develop`
- [x] **Commit:** `phase 1: project scaffold, settings split, env config`
- [x] **Includes:** `config/`, `apps/`, `templates/`, `.gitignore`, `requirements.txt`, `.env.example`, `CLAUDE.md`, `requirements.md`, `plan.md`, `progress.md`, `git.md`
- [x] **Pushed:** 2026-05-19 — commit `ee474f9`

---

### Phase 2 — Authentication & User Profiles ✅
- [x] **Branch:** `develop`
- [x] **Commit:** `phase 2: OAuth login, UserProfile, encrypted API key storage`
- [x] **Includes:** `apps/accounts/`, `config/settings/`, `templates/accounts/`
- [x] **Pushed:** 2026-05-19 — commit `2012fe3`

---

### Phase 3 — OpenAI Backend
- [ ] **Branch:** `develop`
- [ ] **Commit:** `phase 3: GPT-4o Vision scan, moderation, Redis cache, embeddings search`
- [ ] **Includes:** `apps/scanner/`, `apps/learning/`, `config/urls.py`
- [ ] **Pushed:** —

---

### Phase 4 — WebAR Frontend ✅
- [x] **Branch:** `develop`
- [x] **Commit:** `phase 4: AR.js + A-Frame frontend, HTMX scan flow, Tailwind UI`
- [x] **Includes:** `templates/` (all remaining), `apps/core/`, `config/settings/development.py`
- [x] **Pushed:** 2026-05-19

---

### Phase 5 — Security Hardening ✅
- [x] **Branch:** `develop`
- [x] **Commit:** `phase 5: rate limiting, CORS, HTTPS headers, input validation, secret scanning`
- [x] **Includes:** `apps/scanner/views.py`, `templates/scanner/partials/ratelimit.html`, `.secrets.baseline`, `.pre-commit-config.yaml`, `requirements.txt`
- [x] **Pushed:** 2026-05-19

---

### Phase 6 — Testing & Production Readiness
- [ ] **Branch:** `develop` → merge to `main`
- [ ] **Tag:** `v1.0.0`
- [ ] **Commit (develop):** `phase 6: test suite, WhiteNoise static files, Procfile, README`
- [ ] **Commit (main merge):** `merge develop → main: v1.0.0 release`
- [ ] **Includes:** `tests/`, `Procfile`, `README.md`
- [ ] **Pushed:** —

---

## Git Quick Reference

```bash
# Initial setup (Phase 1 only)
git init
git remote add origin https://github.com/<your-org>/<repo>.git
git checkout -b develop

# Standard phase push
git add <files>
git commit -m "<phase commit message>"
git push origin develop

# Phase 6 — merge and tag
git checkout main
git merge develop --no-ff -m "merge develop → main: v1.0.0 release"
git tag v1.0.0
git push origin main --tags

# Safety checks before any push
git status                   # confirm no .env in staging
git log --oneline -5         # verify commit message
detect-secrets scan          # confirm no new secrets
```

---

## Change Log

| Date | Event |
|---|---|
| 2026-05-19 | `git.md` created; all phase push targets initialised as pending |
| 2026-05-19 | Phase 1 pushed to `develop` — commit `ee474f9` |
