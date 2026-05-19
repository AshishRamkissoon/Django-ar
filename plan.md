# Development Plan: AR-Enhanced Learning Platform

> Source of truth: `requirements.md`
> Branch strategy: `main` (stable) → `develop` → `feature/*`
> GitHub push occurs at the end of every phase after tests pass.

---

## Phase Overview

| Phase | Name | Key Deliverable | Est. Effort |
|---|---|---|---|
| 1 | Project Foundation | Runnable Django skeleton + GitHub repo | 1–2 days |
| 2 | Auth & User Profiles | OAuth login + encrypted API key storage | 1–2 days |
| 3 | OpenAI Backend | GPT-4o Vision scan + moderation + Redis cache + embeddings | 2–3 days |
| 4 | WebAR Frontend | Live camera + AR overlay + HTMX scan flow | 2–3 days |
| 5 | Security Hardening | Rate limiting, CORS, HTTPS, secret scanning | 1 day |
| 6 | Testing & Production Readiness | Test suite, prod settings, deploy prep | 1–2 days |

---

## Phase 1 — Project Foundation & Repository Setup

### Goals
- Reproducible local dev environment
- Secrets never in git from day one
- PostgreSQL + Redis connected and migrated
- Codebase pushed to GitHub with proper `.gitignore`

### Steps

#### 1.1 — Create project structure
```
mkdir openai_ar && cd openai_ar
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install django djangorestframework python-dotenv psycopg2-binary django-redis
django-admin startproject config .
mkdir apps templates
python manage.py startapp accounts apps/accounts
python manage.py startapp scanner apps/scanner
python manage.py startapp learning apps/learning
python manage.py startapp core apps/core
```

#### 1.2 — Settings split (base / development / production)
```
config/
└── settings/
    ├── __init__.py       ← empty
    ├── base.py           ← shared: INSTALLED_APPS, MIDDLEWARE, TEMPLATES, AUTH
    ├── development.py    ← DEBUG=True, SQLite fallback, verbose logging
    └── production.py     ← DEBUG=False, PostgreSQL, Redis, HTTPS headers
```

- `base.py` loads all secrets via `python-dotenv` from `.env`.
- Set `DJANGO_SETTINGS_MODULE=config.settings.development` in `.env`.
- Register all four apps in `INSTALLED_APPS`.

#### 1.3 — Create `.env` and `.env.example`
```env
# .env (gitignored — fill in real values)
SECRET_KEY=...
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.development
DATABASE_URL=postgres://user:password@localhost:5432/ar_learning_db
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
ENCRYPTION_KEY=...         # generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

#### 1.4 — `.gitignore`
```
.env
.venv/
venv/
__pycache__/
*.pyc
*.pyo
db.sqlite3
media/
staticfiles/
*.log
.DS_Store
```

#### 1.5 — Install `dj-database-url` and wire PostgreSQL
```python
# base.py
import dj_database_url
DATABASES = {"default": dj_database_url.config(env="DATABASE_URL", conn_max_age=600)}
```

#### 1.6 — Wire Redis cache
```python
# base.py
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ["REDIS_URL"],
    }
}
```

#### 1.7 — Add `requirements.txt`
Pin all dependencies from `requirements.md § 11` plus:
```
dj-database-url>=2.1
```

#### 1.8 — Run initial migration and sanity check
```bash
python manage.py migrate
python manage.py runserver   # should respond on http://127.0.0.1:8000
```

### Phase 1 Tests / Checklist
- [ ] `python manage.py check` passes with no errors
- [ ] `python manage.py migrate` runs clean against PostgreSQL
- [ ] Home page (`/`) returns HTTP 200 (even if it's just the Django default page)
- [ ] `.env` does NOT appear in `git status`
- [ ] `python manage.py shell -c "from django.core.cache import cache; cache.set('k','v'); print(cache.get('k'))"` prints `v`

### GitHub Push — Phase 1
```bash
git init
git remote add origin https://github.com/<your-org>/<repo>.git
git checkout -b develop
git add .
git commit -m "phase 1: project scaffold, settings split, env config"
git push -u origin develop
```

---

## Phase 2 — Authentication & User Profiles

### Goals
- Google + GitHub OAuth login via django-allauth
- `UserProfile` model linked to `User`
- Encrypted OpenAI API key field (Fernet)
- Profile page where user enters / updates their OpenAI API key
- Login / logout working end-to-end in browser

### Steps

#### 2.1 — Install allauth
```bash
pip install django-allauth cryptography
```

Add to `INSTALLED_APPS` in `base.py`:
```python
"django.contrib.sites",
"allauth",
"allauth.account",
"allauth.socialaccount",
"allauth.socialaccount.providers.google",
"allauth.socialaccount.providers.github",
```

#### 2.2 — allauth settings (`base.py`)
```python
SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_REDIRECT_URL = "/ar/"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {"SCOPE": ["profile", "email"], "AUTH_PARAMS": {"access_type": "online"}},
    "github": {"SCOPE": ["user:email"]},
}
```

Add to `config/urls.py`:
```python
path("accounts/", include("allauth.urls")),
```

Run `python manage.py migrate` (allauth adds its own tables).
In Django admin, create the `Site` object matching `localhost:8000`.
Add Google + GitHub OAuth apps in admin under Social Applications.

#### 2.3 — `UserProfile` model (`apps/accounts/models.py`)
```python
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
```

Wire `ENCRYPTION_KEY = os.environ["ENCRYPTION_KEY"]` in `base.py`.

#### 2.4 — Auto-create `UserProfile` on social login (`apps/accounts/signals.py`)
```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import UserProfile

@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
```

Register signal in `apps/accounts/apps.py` `ready()`.

#### 2.5 — Profile view + form (`apps/accounts/views.py`)
- `GET /accounts/profile/` — show current API key status (masked) + form.
- `POST /accounts/profile/` — validate key format (`sk-...`), call `profile.set_api_key()`, save.
- Redirect with success message.
- Template: `templates/accounts/profile.html` — Tailwind-styled form.

#### 2.6 — Migrations
```bash
python manage.py makemigrations accounts
python manage.py migrate
```

#### 2.7 — Add profile URL to `config/urls.py`
```python
path("accounts/profile/", include("apps.accounts.urls")),
```

### Phase 2 Tests / Checklist
- [ ] Click "Login with Google" → OAuth dance → redirected to `/ar/`
- [ ] Click "Login with GitHub" → same flow
- [ ] `UserProfile` row is auto-created in DB after first login
- [ ] Visit `/accounts/profile/`, enter an OpenAI key, submit
- [ ] Verify encrypted value in DB differs from raw key
- [ ] Verify `profile.get_api_key()` returns the original key in Django shell
- [ ] Logout clears session

### GitHub Push — Phase 2
```bash
git add apps/accounts config/settings templates/accounts
git commit -m "phase 2: OAuth login, UserProfile, encrypted API key storage"
git push origin develop
```

---

## Phase 3 — OpenAI Backend: Scan, Moderation, Cache, Embeddings

### Goals
- `POST /api/scan/` receives Base64 frame, calls GPT-4o Vision, moderates, caches
- `ScanSession` persisted to PostgreSQL
- `LearningContent` model with pgvector embeddings
- Semantic search returns top-3 related articles after each scan
- All OpenAI calls use the per-user API key

### Steps

#### 3.1 — Install dependencies
```bash
pip install openai pgvector
```

Enable `pgvector` in PostgreSQL:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

#### 3.2 — `ScanSession` model (`apps/scanner/models.py`)
```python
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ScanSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scans")
    image_hash = models.CharField(max_length=64, db_index=True)
    object_label = models.CharField(max_length=255)
    explanation = models.TextField()
    related_content = models.JSONField(default=list)
    moderation_flagged = models.BooleanField(default=False)
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 3.3 — `LearningContent` model (`apps/learning/models.py`)
```python
from django.db import models
from pgvector.django import VectorField

class LearningContent(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()
    embedding = VectorField(dimensions=1536, null=True)
    tags = models.JSONField(default=list)
    source_url = models.URLField(blank=True)
```

Run migrations:
```bash
python manage.py makemigrations scanner learning
python manage.py migrate
```

#### 3.4 — OpenAI service layer (`apps/scanner/services.py`)

**`scan_object(user, base64_image) → dict`**

```
1. Compute sha256(base64_image) → cache_key
2. Check Redis cache → if hit, return cached result
3. Get user's decrypted API key → if empty, raise error
4. Call openai.chat.completions.create(model="gpt-4o", messages=[system, user+image])
5. Extract object_label + explanation from response
6. Call openai.moderations.create(input=explanation)
   → if flagged: set explanation = safe fallback, log flag
7. Call _semantic_search(object_label) → top-3 LearningContent titles/URLs
8. Build result dict {label, explanation, related, tokens_used, flagged}
9. Store in Redis with TTL=3600
10. Create ScanSession record
11. Increment user.profile.scan_count
12. Return result dict
```

**`embed_and_search(label) → list[dict]`**

```
1. Call openai.embeddings.create(model="text-embedding-3-small", input=label)
2. Run pgvector cosine similarity query against LearningContent
3. Return top-3 {title, source_url}
```

System prompt for Vision call:
```
You are an educational AI assistant. Given an image:
1. Identify the main object or subject.
2. Provide a clear, engaging educational explanation (3–5 sentences) suitable for a curious learner.
3. Suggest exactly 2 related topics the learner could explore next.
Respond in JSON: {"label": "...", "explanation": "...", "related_topics": ["...", "..."]}
```

#### 3.5 — Scan API view (`apps/scanner/views.py`)
```python
@login_required
@ratelimit(key="user", rate="10/m", method="POST", block=True)
def scan_view(request):
    # Parse base64 image from POST body
    # Call services.scan_object(request.user, base64_image)
    # Return HTMX partial: templates/scanner/partials/result.html
```

`result.html` partial contains: object label, explanation paragraphs, related links.
On rate limit (`RatelimitMixed` exception) → return `partials/rate_limited.html` with HTTP 429.

#### 3.6 — Wire URL
```python
# config/urls.py
path("api/scan/", scanner_views.scan_view, name="scan"),
path("api/history/", scanner_views.history_view, name="history"),
```

#### 3.7 — Management command: embed existing content
```bash
python manage.py embed_learning_content
```

Iterates all `LearningContent` with `embedding=None`, calls OpenAI, saves vector.

### Phase 3 Tests / Checklist
- [ ] POST `/api/scan/` with a valid Base64 JPEG → returns object label + explanation
- [ ] Second identical POST → served from Redis (no OpenAI call — verify with mock or log)
- [ ] User with no API key → returns clear error message (HTTP 400)
- [ ] Flagged content → safe fallback returned, `moderation_flagged=True` in DB
- [ ] `ScanSession` row created in PostgreSQL after each scan
- [ ] `scan_count` on `UserProfile` incremented
- [ ] Semantic search returns ≤ 3 `LearningContent` items

### GitHub Push — Phase 3
```bash
git add apps/scanner apps/learning config/
git commit -m "phase 3: GPT-4o Vision scan, moderation, Redis cache, embeddings search"
git push origin develop
```

---

## Phase 4 — WebAR Frontend

### Goals
- Live camera feed rendered via AR.js + A-Frame in the browser
- User taps **Scan** → frame captured → HTMX POST → explanation overlaid in AR
- Graceful fallback for desktop / non-AR browsers
- Polished Tailwind UI for login, profile, history, and AR view pages

### Steps

#### 4.1 — Base template (`templates/base.html`)
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}AR Learn{% endblock %}</title>
  <!-- Tailwind CSS -->
  <script src="https://cdn.tailwindcss.com"></script>
  <!-- HTMX -->
  <script src="https://unpkg.com/htmx.org@1.9.10"></script>
  <!-- CSRF for HTMX -->
  <script>
    document.addEventListener("htmx:configRequest", (e) => {
      e.detail.headers["X-CSRFToken"] = "{{ csrf_token }}";
    });
  </script>
</head>
<body class="bg-gray-950 text-white min-h-screen">
  {% block content %}{% endblock %}
</body>
</html>
```

#### 4.2 — AR view template (`templates/scanner/ar_view.html`)

**Structure:**
```
┌─────────────────────────────────┐
│   <a-scene> (fullscreen)        │  ← AR.js camera feed
│                                 │
│   [AR text overlay on object]   │  ← injected by HTMX
│                                 │
│   [ SCAN ]  button (bottom)     │  ← triggers capture + POST
└─────────────────────────────────┘
```

**Key JS (inline in template):**
```javascript
function captureAndScan() {
  const video = document.querySelector("video");   // AR.js camera feed
  const canvas = document.createElement("canvas");
  canvas.width = 640; canvas.height = 480;
  canvas.getContext("2d").drawImage(video, 0, 0);
  const base64 = canvas.toDataURL("image/jpeg", 0.8).split(",")[1];

  // Inject into hidden input, then trigger HTMX form submit
  document.getElementById("frame-input").value = base64;
  htmx.trigger("#scan-form", "submit");
}
```

**HTMX scan form (hidden):**
```html
<form id="scan-form"
      hx-post="/api/scan/"
      hx-target="#result-overlay"
      hx-swap="innerHTML"
      hx-indicator="#spinner">
  {% csrf_token %}
  <input type="hidden" id="frame-input" name="image">
</form>
```

**Result overlay (positioned over AR feed):**
```html
<div id="result-overlay"
     class="absolute bottom-24 left-4 right-4 bg-black/70 rounded-xl p-4 text-white">
  <!-- HTMX swaps explanation partial here -->
</div>
```

**AR.js + A-Frame CDN (added inside `<head>`):**
```html
<script src="https://aframe.io/releases/1.5.0/aframe.min.js"></script>
<script src="https://raw.githack.com/AR-js-org/AR.js/master/aframe/build/aframe-ar.js"></script>
```

**`<a-scene>` (markerless, camera-only for AR overlay):**
```html
<a-scene embedded
         arjs="sourceType: webcam; debugUIEnabled: false;"
         vr-mode-ui="enabled: false"
         renderer="logarithmicDepthBuffer: true;">
  <a-camera></a-camera>
</a-scene>
```

#### 4.3 — Desktop fallback
Detect AR support on page load:
```javascript
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
  document.getElementById("ar-scene").style.display = "none";
  document.getElementById("fallback-video").style.display = "block";
}
```
Fallback: plain `<video autoplay>` + explanation appears below it.

#### 4.4 — Result partial (`templates/scanner/partials/result.html`)
```html
<div class="space-y-2">
  <p class="text-yellow-400 font-bold text-lg">{{ label }}</p>
  <p class="text-sm leading-relaxed">{{ explanation }}</p>
  {% if related %}
  <div class="mt-2 border-t border-white/20 pt-2">
    <p class="text-xs text-gray-400 uppercase tracking-wide">Explore next</p>
    {% for item in related %}
    <a href="{{ item.source_url }}" class="block text-blue-400 text-sm hover:underline">
      {{ item.title }}
    </a>
    {% endfor %}
  </div>
  {% endif %}
</div>
```

#### 4.5 — Loading spinner
```html
<div id="spinner" class="htmx-indicator fixed inset-0 flex items-center justify-center
                          bg-black/60 z-50">
  <div class="w-12 h-12 border-4 border-white border-t-transparent rounded-full animate-spin">
  </div>
</div>
```

#### 4.6 — Remaining pages
- `templates/core/landing.html` — Hero section, feature list, "Sign in" CTA
- `templates/accounts/profile.html` — API key form, scan history count
- `templates/scanner/history.html` — Paginated list of past scans (HTMX infinite scroll)
- `templates/accounts/login.html` — Google + GitHub OAuth buttons

#### 4.7 — Core view (`apps/core/views.py`)
```python
def landing(request):
    if request.user.is_authenticated:
        return redirect("ar_view")
    return render(request, "core/landing.html")
```

### Phase 4 Tests / Checklist
- [ ] Landing page renders with correct CTA buttons
- [ ] Login flow redirects to `/ar/` with live camera feed visible
- [ ] Tapping **Scan** shows loading spinner
- [ ] Explanation partial appears over camera within ~3 s
- [ ] Related content links are clickable
- [ ] Desktop browser (no camera): fallback `<video>` shown, explanation below
- [ ] Profile page shows masked API key and allows update
- [ ] History page lists past scans in reverse order

### GitHub Push — Phase 4
```bash
git add templates apps/core
git commit -m "phase 4: AR.js + A-Frame frontend, HTMX scan flow, Tailwind UI"
git push origin develop
```

---

## Phase 5 — Security Hardening

### Goals
- Rate limiting enforced and tested
- CORS locked down
- HTTPS production headers configured
- Pre-commit secret scanning in place
- All OWASP basics verified

### Steps

#### 5.1 — Rate limiting (`django-ratelimit`)
```bash
pip install django-ratelimit
```

Already applied to `scan_view` in Phase 3. Verify:
- `RATELIMIT_ENABLE = True` in `base.py`
- In development, set `RATELIMIT_ENABLE = False` so tests aren't blocked

Test manually: hammer `/api/scan/` 11 times in 1 min → 11th returns HTTP 429 HTMX fragment.

#### 5.2 — CORS (`django-cors-headers`)
```bash
pip install django-cors-headers
```

```python
# base.py
INSTALLED_APPS += ["corsheaders"]
MIDDLEWARE.insert(0, "corsheaders.middleware.CorsMiddleware")

# production.py
CORS_ALLOWED_ORIGINS = ["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS = True

# development.py
CORS_ALLOW_ALL_ORIGINS = True   # safe locally
```

#### 5.3 — CSRF verification
- Confirm `django.middleware.csrf.CsrfViewMiddleware` is in `MIDDLEWARE`.
- Confirm HTMX sends `X-CSRFToken` (added in Phase 4 base template).
- Test: remove the HTMX CSRF config, confirm POST returns 403, restore it.

#### 5.4 — Production security headers (`production.py`)
```python
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
```

#### 5.5 — Input validation on scan endpoint
- Reject payloads where `len(base64_image) > 5_000_000` (~ 3.75 MB image limit).
- Validate Base64 decodes to a valid JPEG (`imghdr` or Pillow check).
- Return HTTP 400 with HTMX error partial if invalid.

#### 5.6 — Pre-commit secret scanning
```bash
pip install detect-secrets
detect-secrets scan > .secrets.baseline
```

Add to `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ["--baseline", ".secrets.baseline"]
```

Install hook: `pre-commit install`

#### 5.7 — Logging configuration (`base.py`)
```python
LOGGING = {
    "version": 1,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "apps.scanner": {"handlers": ["console"], "level": "INFO"},
    },
}
```

Log: scan requested, cache hit/miss, moderation flag, OpenAI errors.
Never log: user API keys, raw image data, full JWT tokens.

### Phase 5 Tests / Checklist
- [ ] 11th scan request within 1 min → HTTP 429 with friendly message
- [ ] Unauthenticated POST to `/api/scan/` → HTTP 302 to login (not 403 or 500)
- [ ] POST without CSRF token → HTTP 403
- [ ] Oversized image (> 5 MB Base64) → HTTP 400
- [ ] Non-JPEG Base64 data → HTTP 400
- [ ] `python manage.py check --deploy` passes with no critical warnings
- [ ] `detect-secrets scan` finds zero new secrets

### GitHub Push — Phase 5
```bash
git add config/settings apps/ .secrets.baseline .pre-commit-config.yaml
git commit -m "phase 5: rate limiting, CORS, HTTPS headers, input validation, secret scanning"
git push origin develop
```

---

## Phase 6 — Testing, Polish & Production Readiness

### Goals
- Automated test suite covering critical paths
- Production settings validated
- Static files served via WhiteNoise
- README and deployment guide written
- `develop` merged to `main` and tagged as `v1.0.0`

### Steps

#### 6.1 — Test suite structure
```
tests/
├── test_accounts.py     ← profile model, key encryption/decryption
├── test_scanner.py      ← scan_view: auth required, rate limit, cache hit, moderation flag
├── test_learning.py     ← embed search returns top-3
└── conftest.py          ← fixtures: test user, mock OpenAI responses
```

**Key test cases:**

`test_scanner.py`:
```python
def test_scan_requires_login(client):
    r = client.post("/api/scan/", {"image": "..."})
    assert r.status_code == 302   # redirect to login

def test_scan_returns_explanation(auth_client, mock_openai):
    r = auth_client.post("/api/scan/", {"image": SAMPLE_B64})
    assert r.status_code == 200
    assert "explanation" in r.content.decode()

def test_scan_cache_hit(auth_client, mock_openai, cache):
    auth_client.post("/api/scan/", {"image": SAMPLE_B64})
    auth_client.post("/api/scan/", {"image": SAMPLE_B64})
    assert mock_openai.call_count == 1   # second call served from cache

def test_moderation_flagged_returns_safe_message(auth_client, mock_openai_flagged):
    r = auth_client.post("/api/scan/", {"image": SAMPLE_B64})
    assert "safe" in r.content.decode().lower()
```

`test_accounts.py`:
```python
def test_api_key_encrypted_at_rest(db, user):
    profile = user.profile
    profile.set_api_key("sk-testkey123")
    profile.save()
    assert profile.openai_api_key_encrypted != "sk-testkey123"
    assert profile.get_api_key() == "sk-testkey123"
```

Run with: `pytest --reuse-db -q`

#### 6.2 — Mock OpenAI in tests
Use `unittest.mock.patch` on `openai.OpenAI` — never hit real OpenAI in CI.

```python
# conftest.py
@pytest.fixture
def mock_openai(monkeypatch):
    monkeypatch.setattr("apps.scanner.services.openai.OpenAI", MockOpenAI)
```

#### 6.3 — Static files (WhiteNoise)
```bash
pip install whitenoise
```
```python
# production.py
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```
```bash
python manage.py collectstatic --noinput
```

#### 6.4 — `Procfile` (Railway / Render / Heroku)
```
web: gunicorn config.wsgi --workers 3 --timeout 120
```

#### 6.5 — `README.md`
Cover:
- Project overview (1 paragraph)
- Local setup (clone → `.env` → `pip install` → `migrate` → `runserver`)
- How to generate `ENCRYPTION_KEY`
- How to configure Google + GitHub OAuth apps
- How to seed `LearningContent` (management command)
- Branch + push workflow

#### 6.6 — Final integration walkthrough
End-to-end test on a real mobile device (Chrome on Android or Safari on iOS):
1. Login via Google
2. Set OpenAI API key in profile
3. Open `/ar/` — camera permission prompt appears
4. Point at an object, tap Scan
5. Explanation overlays on camera feed

#### 6.7 — Merge to main and tag
```bash
git checkout main
git merge develop --no-ff -m "merge develop → main: v1.0.0 release"
git tag v1.0.0
git push origin main --tags
```

### Phase 6 Tests / Checklist
- [ ] `pytest` — all tests green
- [ ] `python manage.py check --deploy` — zero issues
- [ ] `collectstatic` runs without errors
- [ ] Static files load correctly (Tailwind, HTMX, A-Frame scripts)
- [ ] End-to-end scan works on a real mobile browser
- [ ] `README.md` reviewed — another developer could set up from scratch with it
- [ ] No `.env` or secrets in `git log --all`
- [ ] `v1.0.0` tag visible on GitHub

### GitHub Push — Phase 6
```bash
git add tests/ Procfile README.md staticfiles/
git commit -m "phase 6: test suite, WhiteNoise static files, Procfile, README"
git push origin develop
# then merge + tag as above
```

---

## Summary: What Gets Pushed After Each Phase

| Phase | Branch | Tag | What's in git |
|---|---|---|---|
| 1 | `develop` | — | Django scaffold, settings, .gitignore, requirements.txt |
| 2 | `develop` | — | + OAuth, UserProfile, Fernet-encrypted API key |
| 3 | `develop` | — | + Scan service, moderation, Redis cache, embeddings |
| 4 | `develop` | — | + AR.js frontend, HTMX flow, Tailwind templates |
| 5 | `develop` | — | + Rate limiting, CORS, HTTPS headers, secret scanning |
| 6 | `main` | `v1.0.0` | + Tests, WhiteNoise, Procfile, README — production-ready |

---

*Plan generated: 2026-05-19. See `requirements.md` for full specification details.*
