# FITCHECK

FITCHECK is a local-first personal wardrobe and outfit planner. The frontend is React/Vite with Tailwind CSS, Framer Motion, Lucide icons, and React Router. The API is FastAPI with SQLAlchemy 2.x and Alembic.

## Run on Windows

Keep the existing Python environment. The current Python 3.14.6 environment has compatible FastAPI, SQLAlchemy, Pillow, and PostgreSQL driver packages installed.

### Test on your phone over Wi-Fi

Install the app from a home-screen shortcut after publishing FITCHECK on an HTTPS host. Android Chrome offers **Install app** or **Add to Home screen**; on iPhone, open the HTTPS site in Safari and select **Share → Add to Home Screen**.

For temporary same-Wi-Fi testing, FITCHECK uses the same hostname for the API and frontend automatically. In PowerShell, use your computer's actual Wi-Fi IPv4 address in the backend CORS list:

```powershell
Set-Location C:\Users\saharsh\Documents\FITCHECK\backend
$env:FITCHECK_CORS_ORIGINS='http://localhost:5173,http://127.0.0.1:5173,http://192.168.0.112:5173'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

In a second terminal, start Vite:

```powershell
Set-Location C:\Users\saharsh\Documents\FITCHECK\frontend
npm run dev -- --host 0.0.0.0
```

Open `http://192.168.0.112:5173` on the phone and keep both terminals and the computer running. A shortcut to this local development address only works while the computer is online and the phone is on the same network. Publish the PWA and its API to HTTPS hosting to use it anywhere.

The production frontend includes home-screen icons, an installable PWA manifest, and an offline-cached app shell. Offline wardrobe, image upload, and recommendations still require the API and database to be reachable.

### Free internet hosting

The root `Dockerfile` and `render.yaml` prepare a free Render web service. The service may go to sleep after inactivity, so the first opening may take a little while. For persistent wardrobe and image data without a paid server disk, pair it with a free PostgreSQL database from Neon: on the hosted service, uploaded photos are resized and stored in PostgreSQL.

1. Create a **private** GitHub repository and add this project. Never upload `.env`/`.env.local` files, personal access tokens, or database passwords.
2. Create a free Neon PostgreSQL project and copy its **direct (not pooled)** connection string from the Neon dashboard. Keep it private.
3. In Render, create a new Blueprint from your private repository and accept the included `render.yaml`.
4. When prompted, set `DATABASE_URL` to your Neon connection string. Create a strong private `FITCHECK_APP_PASSWORD` of at least 16 characters. Render generates the session-signing secret.
5. Wait for the Render deployment and `/health` check to finish. Open the HTTPS Render address on Android in Chrome and choose **Install app** from the menu (or use Chrome's install prompt).

The hosted API protects private wardrobe data and photos with a signed, HTTP-only, secure session cookie and rate-limited sign-in. Production startup fails if the private app password or signing secret is missing. Keep the GitHub repository private and never publish API/database passwords. Neon PostgreSQL connection strings are adapted for the installed psycopg 3 driver; migrations run automatically on container startup.

The API health endpoint is `http://127.0.0.1:8001/health`; interactive API documentation is at `http://127.0.0.1:8001/docs`.

Port 8000 was already occupied by a separate `python -m http.server` process in the inspected environment. FITCHECK therefore uses port 8001 rather than terminating or reusing that unrelated process. The correct ASGI import target is `app.main:app`, launched with `backend` as the working directory.

## Data and configuration

- Without `DATABASE_URL`, the API creates a persistent SQLite database at `backend/fitcheck.db`, which is suitable for local development.
- To use PostgreSQL, set `DATABASE_URL` to a private `postgresql+psycopg://...` connection string in the backend process environment.
- Run `alembic upgrade head` from `backend` to apply schema migrations; the development server also creates missing tables on startup.
- Uploaded JPEG, PNG, and WebP images (up to 8 MB each) are stored in `backend/uploads`. Set `FITCHECK_UPLOAD_DIR` to choose another local directory.
- Set `FITCHECK_CORS_ORIGINS` to a comma-separated list if the frontend runs on a different origin.
- `FITCHECK_SCORING_WEIGHTS` accepts a JSON object with `aesthetic`, `color`, `fit`, `occasion`, and `weather_rotation` values. Defaults are 30%, 25%, 20%, 15%, and 10%; custom values are normalized.
- No API key or paid model is needed. Add wardrobe details manually; recommendations are based only on stored items.
- If deploying the API separately, set `VITE_API_URL` to its public HTTPS URL when building the frontend. When serving the frontend and API on one HTTPS domain, leave it unset.

## Tests and build

```powershell
Set-Location C:\Users\saharsh\Documents\FITCHECK\backend
.\.venv\Scripts\python.exe -m pytest
Set-Location ..\frontend
npm run lint
npm run build
```

## Included flows

- Add, edit, remove, search, filter, sort, favorite, and update laundry state for wardrobe pieces.
- Add an item with or without an image; bulk-upload multiple images as draft pieces.
- Generate an outfit by aesthetic, occasion, and season; save it, schedule it, reroll it, or mark it worn.
- Browse planned looks, favorites, laundry, and wear history.
- Rule-based recommendations reject dirty/unavailable pieces, respect core outfit categories and supported aesthetic constraints, explain selections, and prefer unseen combinations.
