# PangeaWorld deployment: Render + Neon + Gemini

The canonical production layout is a Render Static Site for `frontend`, a
single-instance Render Web Service for `backend`, Neon PostgreSQL, a Render
Cron Job that checks `/healthz`, and Gemini calls proxied only by FastAPI.

## 1. Create the external services

1. Create a Neon project and database. Copy its pooled connection string and
   require TLS. For SQLAlchemy with the installed Psycopg driver, use the form
   `postgresql+psycopg://USER:PASSWORD@HOST/DATABASE?sslmode=require`.
2. Create a Gemini API key and select explicit advisor and newsroom model IDs.
3. In Render, create a Blueprint from this repository's `render.yaml`.

The repository pins Python 3.13 and Node.js 22 through `.python-version` and
`.node-version` so Render uses runtimes compatible with the local verification
baseline and Vite 8.

Do not commit any real credential or paste a Gemini key into a `VITE_*`
variable. Vite variables are compiled into the public browser bundle.

## 2. Configure Render secrets

Set these values when the Blueprint prompts for unsynchronized variables:

| Service | Variable | Value |
| --- | --- | --- |
| `pangeaworld-api` | `PANGEAWORLD_DATABASE_URL` | Neon pooled URL with `sslmode=require` |
| `pangeaworld-api` | `PANGEAWORLD_CORS_ORIGINS` | Final static-site HTTPS origin, with no trailing slash |
| `pangeaworld-api` | `GEMINI_API_KEY` | Gemini secret key |
| `pangeaworld-api` | `GEMINI_ADVISOR_MODEL` | Approved Gemini model ID |
| `pangeaworld-api` | `GEMINI_NEWS_MODEL` | Approved Gemini model ID |
| `pangeaworld` | `VITE_API_URL` | Final API HTTPS origin, with no trailing slash |
| `pangeaworld-keepalive` | `PANGEAWORLD_HEALTH_URL` | Final API URL plus `/healthz` |

The Blueprint sets `PANGEAWORLD_ENV=production` and
`PANGEAWORLD_COOKIE_SECURE=1`. Startup deliberately fails if Neon, HTTPS CORS,
secure cookies, or Gemini variables are missing.

## 3. Deploy in dependency order

1. Deploy `pangeaworld-api`. Its pre-deploy command applies Alembic migrations
   before Uvicorn starts.
2. Verify `https://<api-host>/healthz` returns
   `{"status":"ok","database":"connected"}`.
3. Deploy/redeploy the static site after `VITE_API_URL` is final.
4. Verify registration, lobby creation, a WebSocket connection, one reviewed
   President decision, one reviewed Executive decision, advisor history, and
   instructor analytics.
5. Run the keep-alive cron and confirm a successful health-check log entry.

## 4. Operating constraints

- Keep one API instance until WebSocket broadcasts use shared pub/sub. Database
  row locks protect authoritative phase changes, but in-memory socket lists do
  not cross Render instances.
- SQLite is never production storage. Render filesystem data is disposable.
- The cron endpoint is read-only. It must not create sessions, advance phases,
  or trigger Gemini usage.
- An always-on Render web-service plan is preferred during live classes. A cron
  ping reduces cold starts on plans that suspend but is not an uptime guarantee.
- Review Render, Neon, and Gemini usage/cost dashboards during the pilot. Set
  budget alerts and provider quotas before inviting a full class.

## 5. Local migration check

From the repository root, with backend dependencies installed:

```powershell
$env:PANGEAWORLD_DATABASE_URL = "sqlite:///backend/pangeaworld-migration-check.db"
backend/.venv/Scripts/python.exe -m alembic -c backend/alembic.ini upgrade head
```

Use a disposable database path for this check. Production migrations must run
through the Render pre-deploy command against the configured Neon database.
