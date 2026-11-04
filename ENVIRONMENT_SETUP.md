# Environment Configuration Setup

This project uses Vite mode files for development, staging, and production.

## Files

- `env.development` — local development
- `env.staging` — staging
- `env.production` — production
- `.env.example` — template

Copy a file to `.env.[mode]` before running Vite:

```bash
cp env.development .env.development
cp env.staging .env.staging
cp env.production .env.production
```

## Scripts

```bash
npm run dev            # development
npm run dev:staging    # staging config
npm run build          # production
npm run build:staging
npm run preview
```

- `VITE_APP_ENV` — current environment (`development` / `staging` / `production`)
- `VITE_API_BASE_URL` — Catalog Muse API. Every environment uses `https://catalog-muse-api.asinzen.com`
