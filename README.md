# Catalog Muse

One supplier photo and a spec sheet become a listing draft. The Python engine does the work. The React app is where a person reviews each step. Nothing is published automatically.

Put `MODEL_API_KEY` in `.env.local`. That file is not committed. Then start the engine and the app together:

```bash
./scripts/start.sh
```

The engine listens on http://127.0.0.1:8790. The app listens on http://127.0.0.1:5173. Ctrl+C stops what the script started.

Local development calls the engine on this machine. Staging and production call https://catalog-muse-api.asinzen.com. The deployed app is https://catalog-muse-demo.asinzen.com/.

## Images

`Dockerfile` builds the engine. `Dockerfile.web` builds the React app into nginx.
