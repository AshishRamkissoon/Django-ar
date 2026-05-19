# Project Requirements: AR-Enhanced Learning Platform

## 1. Project Overview

An AI-powered, augmented reality learning platform delivered entirely through the web browser
(no app install required). Users point their device camera at real-world objects, tap "Scan",
and receive an AI-generated explanation overlaid in AR. The platform is a small SaaS product
targeting up to ~1,000 users.

---

## 2. Core User Flow

1. User signs in via Google or GitHub (OAuth).
2. User opens the AR camera view in their browser.
3. User points camera at any real-world object and taps **Scan**.
4. A camera frame is captured and sent to the backend.
5. Backend forwards the frame to **GPT-4o Vision** for object identification.
6. GPT returns an object label + educational explanation.
7. Backend optionally uses **embeddings + semantic search** to fetch related learning content
   from the database.
8. The explanation text (and related content) is returned to the frontend.
9. The frontend overlays the text on the live camera feed via WebAR.
10. The AI response is cached in Redis to avoid duplicate API calls for the same object.
11. The session and response are persisted to PostgreSQL.

---

## 3. Technology Stack

### Backend
| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | Django 4.2+ |
| REST / partial API | Django REST Framework (DRF) |
| Async task / cache | Redis (django-redis) |
| Database | PostgreSQL 15+ |
| AI | OpenAI Python SDK (`openai>=1.0`) |
| Auth | django-allauth (Google + GitHub OAuth) |
| Rate limiting | django-ratelimit |
| Content moderation | OpenAI Moderation API |
| Secret management | python-dotenv + `.env` file |

### Frontend
| Layer | Technology |
|---|---|
| Templating | Django Templates |
| Interactivity | HTMX (no full page reloads) |
| AR layer | AR.js + A-Frame (WebAR, marker-free mode) |
| Camera capture | Browser `getUserMedia` + Canvas API |
| Styling | Tailwind CSS (CDN) |

### DevOps / Security
| Concern | Tool / Approach |
|---|---|
| Secrets | `.env` file, never committed; `.gitignore` enforced |
| GitHub | `.env.example` committed (keys redacted) |
| CORS | `django-cors-headers` |
| CSRF | Django built-in middleware |
| Per-user API keys | Each user stores their own OpenAI key (encrypted at rest) |
| Rate limiting | Per-user, per-endpoint limits on AI scan endpoint |
| Deployment | Local for now; PaaS-ready (Railway / Render) |

---

## 4. OpenAI Integration Details

### 4.1 GPT-4o Vision — Object Recognition & Explanation
- **Endpoint**: `POST /api/scan/`
- **Input**: Base64-encoded camera frame (JPEG), user prompt, `user_id`
- **OpenAI call**: `openai.chat.completions.create` with `model="gpt-4o"` and
  an image content block (`type: image_url`, `url: data:image/jpeg;base64,...`)
- **System prompt**: Instructs the model to (1) identify the object, (2) give a
  clear educational explanation suitable for a learner, (3) suggest 2–3 related topics.
- **User API key**: Retrieved from the user's encrypted profile field; passed as
  `openai.OpenAI(api_key=user.openai_api_key_decrypted)` — the platform's own key is
  never used for inference.

### 4.2 Embeddings — Semantic Search for Related Content
- **Endpoint**: Called internally after Vision response.
- **Model**: `text-embedding-3-small`
- **Flow**: Embed the GPT-identified object label → cosine-similarity search against
  pre-embedded `LearningContent` records in PostgreSQL (using `pgvector` extension) →
  return top-3 related articles/videos.

### 4.3 Content Moderation
- Before returning any AI-generated text to the frontend, pass it through
  `openai.moderations.create()`.
- If flagged, return a safe fallback message and log the event.

### 4.4 Redis Caching
- Cache key: `sha256(base64_frame)` (hash of the image bytes).
- TTL: 1 hour.
- On cache hit, skip OpenAI call entirely and return cached explanation.

---

## 5. Django Application Structure

```
openai_ar/                   ← project root
├── .env                     ← secrets (gitignored)
├── .env.example             ← template committed to git
├── .gitignore
├── manage.py
├── requirements.txt
├── config/                  ← Django project settings package
│   ├── settings/
│   │   ├── base.py          ← shared settings
│   │   ├── development.py   ← DEBUG=True, SQLite optional
│   │   └── production.py    ← DEBUG=False, PostgreSQL, Redis
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/            ← allauth, user profile, API key storage
│   ├── scanner/             ← AR scan endpoint, OpenAI Vision call
│   ├── learning/            ← LearningContent model, embeddings, semantic search
│   └── core/                ← shared utilities, base templates
└── templates/
    ├── base.html
    ├── accounts/
    └── scanner/
        └── ar_view.html     ← HTMX + A-Frame AR camera view
```

---

## 6. Data Models

### `accounts.UserProfile`
| Field | Type | Notes |
|---|---|---|
| `user` | OneToOne → User | Django auth user |
| `openai_api_key_encrypted` | TextField | Fernet-encrypted at rest |
| `scan_count` | IntegerField | Total scans performed |
| `created_at` | DateTimeField | |

### `scanner.ScanSession`
| Field | Type | Notes |
|---|---|---|
| `user` | FK → User | |
| `image_hash` | CharField | SHA-256 of frame (cache key) |
| `object_label` | CharField | GPT-identified label |
| `explanation` | TextField | GPT-generated explanation |
| `moderation_flagged` | BooleanField | Was content flagged? |
| `tokens_used` | IntegerField | For usage tracking |
| `created_at` | DateTimeField | |

### `learning.LearningContent`
| Field | Type | Notes |
|---|---|---|
| `title` | CharField | |
| `body` | TextField | |
| `embedding` | VectorField | pgvector, dim=1536 |
| `tags` | ArrayField | |
| `source_url` | URLField | Optional |

---

## 7. API Endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/` | No | Landing page |
| `GET` | `/ar/` | Yes | AR camera view (HTMX page) |
| `POST` | `/api/scan/` | Yes + rate limit | Submit camera frame, get AI explanation |
| `GET` | `/api/history/` | Yes | User's past scan sessions |
| `POST` | `/accounts/login/` | No | django-allauth OAuth redirect |
| `GET` | `/accounts/logout/` | Yes | Log out |
| `GET/POST` | `/accounts/profile/` | Yes | Update OpenAI API key |

---

## 8. Security Requirements

### 8.1 Secret Management
- All secrets in `.env`: `SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`,
  `ENCRYPTION_KEY` (Fernet key for user API keys), `OPENAI_API_KEY` (admin/fallback only).
- `.env` listed in `.gitignore` before first commit.
- `.env.example` committed with placeholder values.
- Settings loaded via `python-dotenv`; no hardcoded secrets anywhere in code.

### 8.2 CSRF
- Django's `CsrfViewMiddleware` enabled on all state-changing endpoints.
- HTMX configured to send `X-CSRFToken` header on POST requests.

### 8.3 CORS
- `django-cors-headers` installed.
- `CORS_ALLOWED_ORIGINS` set explicitly (no wildcard `*` in production).

### 8.4 Rate Limiting
- `django-ratelimit` applied to `POST /api/scan/`:
  - **Unauthenticated**: blocked entirely.
  - **Authenticated**: 10 requests / minute per user.
- Return `HTTP 429` with a user-friendly HTMX fragment on limit hit.

### 8.5 Per-User API Keys
- Users enter their own OpenAI API key in their profile.
- Key is encrypted with Fernet (`cryptography` library) before storage.
- Key is decrypted in memory only at request time; never logged or returned to frontend.
- The platform's own `OPENAI_API_KEY` env var is used only for admin/embedding tasks.

### 8.6 Content Moderation
- Every GPT response passes through the OpenAI Moderation API before display.
- Flagged responses are replaced with a safe fallback; the event is logged to `ScanSession`.

### 8.7 HTTPS
- Enforced via `SECURE_SSL_REDIRECT = True` in production settings.
- `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `HSTS` headers all set.

---

## 9. WebAR Implementation

- **Library**: AR.js + A-Frame (open source, no API key, no app install).
- **Mode**: Location-based or markerless (surface detection via `ARJS_Location` or
  `MindAR` for image tracking — to be decided during development).
- **Scan flow**:
  1. `<a-scene>` with live camera feed rendered via A-Frame.
  2. User taps **Scan** button → JS captures current video frame to `<canvas>` →
     converts to Base64 JPEG.
  3. HTMX `hx-post="/api/scan/"` sends frame + CSRF token.
  4. Server responds with an HTMX partial containing the explanation text.
  5. Partial is injected into a `<a-text>` or HTML overlay positioned over the camera.
- **Fallback**: If WebAR is not supported (desktop browser), show camera feed as plain
  `<video>` with explanation displayed below.

---

## 10. GitHub / Version Control

- Repository initialized with a `.gitignore` that excludes:
  - `.env`
  - `__pycache__/`, `*.pyc`
  - `db.sqlite3`
  - `media/`
  - `.venv/`, `venv/`
- Branch strategy: `main` (production-ready), `develop` (integration), feature branches.
- Pre-commit check recommended: `detect-secrets` or `truffleHog` to prevent accidental
  secret commits.

---

## 11. Python Dependencies (`requirements.txt`)

```
django>=4.2,<5.0
djangorestframework>=3.14
django-allauth>=0.57
django-cors-headers>=4.3
django-ratelimit>=4.1
django-redis>=5.4
psycopg2-binary>=2.9
pgvector>=0.2
openai>=1.30
python-dotenv>=1.0
cryptography>=42.0
Pillow>=10.0
gunicorn>=21.0
whitenoise>=6.6
```

---

## 12. Environment Variables (`.env.example`)

```env
# Django
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:password@localhost:5432/ar_learning_db

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI (platform-level key for embeddings / moderation only)
OPENAI_API_KEY=sk-...

# Encryption key for user API keys (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-fernet-key-here

# Social Auth (django-allauth)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

---

## 13. Out of Scope (Current Phase)

- Payment / subscription system (deferred).
- Mobile native app (WebAR covers mobile via browser).
- On-device ML model (GPT-4o Vision handles recognition server-side).
- Multi-language support.
- Admin analytics dashboard.

---

## 14. Open Decisions (Resolve During Planning)

| Decision | Options | Recommendation |
|---|---|---|
| AR marker strategy | Markerless surface / image tracking / location | Start with image tracking (MindAR) — easiest for objects |
| pgvector vs. external vector DB | pgvector in Postgres / Pinecone / Weaviate | pgvector — keeps stack simple at this scale |
| Deployment platform | Railway / Render / Heroku | Railway — free PostgreSQL + Redis add-ons |
| WebSocket for streaming GPT | Yes (Django Channels) / No (HTMX polling) | Start with HTMX polling; add streaming later |

---

*Document generated: 2026-05-19. Use this file as the single source of truth when creating the development plan.*
