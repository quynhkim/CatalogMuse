FROM python:3.12-slim-bookworm

WORKDIR /app

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . \
    && useradd --uid 1000 --create-home engine

ENV CATALOGMUSE_HOST=0.0.0.0 \
    CATALOGMUSE_PORT=8790 \
    CATALOGMUSE_DATA=/data \
    CATALOGMUSE_PUBLIC_URL=http://catalogmuse-engine.catalogmuse.svc.cluster.local:8790

EXPOSE 8790
USER 1000
CMD ["catalogmuse-engine"]
