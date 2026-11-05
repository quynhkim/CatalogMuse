# Catalog Muse

One supplier photo and a spec sheet become a listing draft. The Python engine does the work. The React app is where a person reviews each step. Nothing is published automatically.

## Engine

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/catalogmuse
```

The engine listens on http://127.0.0.1:8790. Put `MODEL_API_KEY` in `.env.local`. That file is not committed.

## App

```bash
cp env.development .env.development
npm install
npm run dev
```

Local development calls the engine on this machine. Staging and production call https://catalog-muse-api.asinzen.com. The deployed app is https://catalog-muse-demo.asinzen.com/.

## Images

`Dockerfile` builds the engine. `Dockerfile.web` builds the React app into nginx.
