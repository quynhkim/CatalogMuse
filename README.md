# Catalog Muse engine

One supplier photo and a spec sheet become a listing draft. A person approves each step. This service does not publish the listing.

Put `MODEL_API_KEY` in `.env.local`. That file is not committed. Then:

```bash
./scripts/start.sh
```

The engine listens on http://127.0.0.1:8790. Ctrl+C stops it.

`Dockerfile` builds the engine image.
