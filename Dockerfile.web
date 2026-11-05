# Multi-stage build: Vite SPA → nginx (linux/arm64)
FROM node:22-alpine AS builder

ARG APP_ENV=production

WORKDIR /app

COPY package.json package-lock.json .npmrc ./

RUN npm ci

COPY . .

# Vite reads .env.[mode]; repo keeps env.* templates (see ENVIRONMENT_SETUP.md)
RUN cp "env.${APP_ENV}" ".env.${APP_ENV}" && \
    if [ "$APP_ENV" = "staging" ]; then \
      npm run build:staging; \
    else \
      npm run build; \
    fi && \
    test -f dist/index.html

FROM nginx:alpine

RUN rm -f /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
