# AR Learn

Point your browser camera at any real-world object and get an AI-powered educational explanation overlaid in augmented reality — no app install required.

**Stack:** Django 6 · HTMX · AR.js + A-Frame · GPT-4o Vision · PostgreSQL · Redis · Tailwind CSS

---

## Features

- **WebAR scanning** — camera feed runs in the browser via AR.js; no native app needed
- **GPT-4o Vision** — identifies objects and returns a structured educational explanation
- **Per-user API keys** — bring your own OpenAI key; stored Fernet-encrypted at rest
- **Semantic search** — related learning content retrieved via cosine similarity on embeddings
- **Content moderation** — every AI response is screened by OpenAI Moderation before display
- **Rate limiting** — 10 scans / minute per authenticated user
- **Google + GitHub OAuth** — via django-allauth

---

## Quick Start (Development)

```bash
# 1. Clone and create a virtual environment
git clone https://github.com/AshishRamkissoon/Django-ar.git
cd Django-ar
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment template and fill in your values
cp .env.example .env
# Edit .env: set SECRET_KEY, DB_*, OPENAI_API_KEY, ENCRYPTION_KEY

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 4. Run migrations
python manage.py migrate

# 5. Create a superuser (or use the local-login dev shortcut)
python manage.py createsuperuser

# 6. (Optional) Seed learning content embeddings
python manage.py embed_learning_content

# 7. Start the dev server
python manage.py runserver
```

Visit `http://localhost:8000`. Log in at `/accounts/local-login/` with your superuser credentials, add your OpenAI API key at `/accounts/profile/`, then open `/ar/` to scan.

---

## Environment Variables

| Variable | Description |
|---|---|
| `SECRET_KEY` | Django secret key |
| `DJANGO_SETTINGS_MODULE` | `config.settings.development` or `config.settings.production` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` | PostgreSQL connection (development) |
| `DATABASE_URL` | PostgreSQL URL (production) |
| `REDIS_URL` | Redis URL (production cache) |
| `OPENAI_API_KEY` | Platform key used for embeddings + moderation only |
| `ENCRYPTION_KEY` | Fernet key for encrypting per-user OpenAI keys |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth app credentials |
| `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` | GitHub OAuth app credentials |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed origins (production) |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames |

---

## Running Tests

```bash
pytest -q
```

All tests mock `openai.OpenAI` — no real API calls are made in CI.

---

## Production Deployment

```bash
# Set DJANGO_SETTINGS_MODULE=config.settings.production in your environment
python manage.py collectstatic --noinput
python manage.py migrate
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

The `Procfile` is compatible with Heroku, Railway, and Render.

---

## Project Structure

```
config/settings/   base · development · production
apps/accounts/     UserProfile, Fernet-encrypted API key, signals
apps/scanner/      GPT-4o Vision scan, rate-limited endpoint, ScanSession
apps/learning/     LearningContent, semantic search via cosine similarity
apps/core/         Landing page, AR view
templates/         base.html, scanner/ar_view.html, partials/
tests/             pytest suite (accounts, scanner, learning)
```

---

## Security

- API keys encrypted with Fernet (AES-128) before storage
- Content moderation on every AI response via OpenAI Moderation API
- CSRF required on all state-changing requests; HTMX sends `X-CSRFToken` automatically
- Rate limiting: 10 POST `/api/scan/` requests per minute per user
- Production: HTTPS-only, HSTS, secure cookies, `X-Frame-Options: DENY`
- `detect-secrets` pre-commit hook prevents accidental secret commits

---

## License

MIT
