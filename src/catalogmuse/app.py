"""HTTP contract for the Go backend.

Create a job, poll or stream agent status, then approve or request changes
on the agent that is waiting. This process does not publish a listing.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Iterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from catalogmuse.orchestrator import JobError, Orchestrator, decode_image
from catalogmuse.tools import Tools


class CreateJob(BaseModel):
    spec: str
    image_base64: str = ""
    marketplaces: list[str] = []


class Decision(BaseModel):
    action: str
    note: str = ""
    agent: str | None = None
    prompt: str = ""
    styles: list[str] = []
    variations: int | None = None
    images: list[str] = []


def create_app(data_dir: Path | None = None, tools: Tools | None = None, public_url: str | None = None) -> FastAPI:
    root = data_dir or Path(os.environ.get("CATALOGMUSE_DATA", "data"))
    url = public_url if public_url is not None else os.environ.get("CATALOGMUSE_PUBLIC_URL", "http://127.0.0.1:8790")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> Iterator[None]:
        root.mkdir(parents=True, exist_ok=True)
        app.state.checkpoint = _checkpoint(root / "checkpoints.sqlite")
        app.state.orchestrator = Orchestrator(root, app.state.checkpoint, tools, url)
        yield
        closer = getattr(app.state.checkpoint, "close", None)
        if closer:
            closer()

    app = FastAPI(title="CatalogMuse agents", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "catalogmuse-engine"}

    @app.post("/v1/jobs", status_code=202)
    def create_job(body: CreateJob) -> JSONResponse:
        try:
            image = decode_image(body.image_base64)
            view = _orch(app).start(body.spec, image, body.marketplaces)
        except JobError as exc:
            return JSONResponse({"error": exc.message}, status_code=exc.status)
        return JSONResponse(view, status_code=202)

    @app.get("/v1/jobs/{job_id}")
    def get_job(job_id: str) -> JSONResponse:
        try:
            return JSONResponse(_orch(app).view(job_id))
        except JobError as exc:
            return JSONResponse({"error": exc.message}, status_code=exc.status)

    @app.get("/v1/jobs/{job_id}/events")
    def events(job_id: str) -> StreamingResponse:
        orch = _orch(app)

        def stream() -> Iterator[str]:
            last = ""
            for _ in range(2400):
                try:
                    view = orch.view(job_id)
                except JobError as exc:
                    yield _event("error", {"error": exc.message})
                    return
                payload = json.dumps(view)
                if payload != last:
                    yield _event("status", view)
                    last = payload
                if view["status"] in {"approved", "failed"}:
                    return
                time.sleep(0.5)
            yield _event("status", json.loads(last) if last else {"id": job_id})

        return StreamingResponse(stream(), media_type="text/event-stream")

    @app.post("/v1/jobs/{job_id}/decisions", status_code=202)
    def decide(job_id: str, body: Decision) -> JSONResponse:
        try:
            view = _orch(app).decide(
                job_id,
                body.action,
                body.note,
                body.agent,
                body.prompt,
                body.styles,
                body.variations,
                body.images,
            )
        except JobError as exc:
            return JSONResponse({"error": exc.message}, status_code=exc.status)
        return JSONResponse(view, status_code=202)

    @app.get("/v1/jobs/{job_id}/files/{name}")
    def download(job_id: str, name: str) -> FileResponse:
        try:
            path = _orch(app).file(job_id, name)
        except JobError as exc:
            return JSONResponse({"error": exc.message}, status_code=exc.status)  # type: ignore[return-value]
        media = "image/png" if path.suffix == ".png" else "image/jpeg"
        return FileResponse(path, media_type=media, headers={"Cache-Control": "no-store"})

    return app


def _orch(app: FastAPI) -> Orchestrator:
    return app.state.orchestrator


def _event(name: str, payload: dict[str, Any]) -> str:
    return f"event: {name}\ndata: {json.dumps(payload)}\n\n"


def _checkpoint(path: Path) -> Any:
    from langgraph.checkpoint.sqlite import SqliteSaver

    factory = getattr(SqliteSaver, "from_conn_string", None)
    if factory is None:
        connection = sqlite3.connect(str(path), check_same_thread=False)
        return SqliteSaver(connection)
    made = factory(str(path))
    if hasattr(made, "__enter__"):
        saver = made.__enter__()
        saver._catalogmuse_context = made
        original = getattr(saver, "close", None)

        def close() -> None:
            if original:
                original()
            made.__exit__(None, None, None)

        saver.close = close
        return saver
    return made


app = create_app()
