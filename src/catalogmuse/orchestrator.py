"""Runs one listing job and exposes it to the HTTP handlers."""

from __future__ import annotations

import base64
import threading
import uuid
from pathlib import Path
from typing import Any

from langgraph.types import Command

from catalogmuse.blobs import file_url, put_file
from catalogmuse.graph import build_graph
from catalogmuse.rules import normalize_marketplaces, spec_from_text
from catalogmuse.status import StatusBoard
from catalogmuse.tools import Tools


class JobError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class Orchestrator:
    def __init__(self, data_dir: Path, checkpointer: Any, tools: Tools | None = None, public_url: str = "") -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.public_url = public_url.rstrip("/")
        self.status = StatusBoard(str(data_dir / "status.sqlite"))
        self.tools = tools or Tools()
        self.graph = build_graph(self.tools, checkpointer, self.status.mark)
        self._busy: set[str] = set()
        self._guard = threading.Lock()

    def start(self, spec_text: str, image: bytes, marketplaces: list[str] | None = None) -> dict[str, Any]:
        if not spec_text.strip():
            raise JobError(400, "A spec sheet is required")
        if not image:
            raise JobError(400, "A supplier photo is required")
        try:
            chosen = normalize_marketplaces(marketplaces)
        except ValueError:
            raise JobError(400, "Marketplace must be amazon or walmart") from None
        job_id = "job_" + uuid.uuid4().hex[:12]
        work = self.data_dir / "jobs" / job_id
        work.mkdir(parents=True)
        image_path = work / "supplier.jpg"
        image_path.write_bytes(image)
        put_file(job_id, image_path)
        self.status.create(job_id, chosen)
        initial = {
            "job_id": job_id,
            "marketplaces": chosen,
            "spec_text": spec_text,
            "spec": spec_from_text(spec_text),
            "image_path": str(image_path),
            "work_dir": str(work),
            "feedback": {},
        }
        self._launch(job_id, initial)
        return self.view(job_id)

    def decide(
        self,
        job_id: str,
        action: str,
        note: str = "",
        agent: str | None = None,
        prompt: str = "",
        styles: list[str] | None = None,
        variations: int | None = None,
        images: list[str] | None = None,
    ) -> dict[str, Any]:
        if action not in {"approve", "changes"}:
            raise JobError(400, "Action must be approve or changes")
        if action == "changes" and not note.strip():
            raise JobError(400, "A change request needs a note")
        with self._guard:
            if job_id in self._busy:
                raise JobError(409, "An agent is still running")
            current = self.view(job_id)
            if current["status"] != "waiting" or not current["pending_agent"]:
                raise JobError(409, "This job is not waiting for a person")
            if agent and agent != current["pending_agent"]:
                raise JobError(409, f"The waiting agent is {current['pending_agent']}")
            if action == "approve" and not current["approve_allowed"]:
                raise JobError(409, "Approve stays closed until the rule list is clear")
            choice = None
            picked: list[str] | None = None
            director = next((item for item in current["agents"] if item["name"] == "art_director"), {})
            naming = not ((director.get("output") or {}).get("styles"))
            if current["pending_agent"] == "art_director" and action == "approve" and not naming:
                choice = _scene_request(styles or [], prompt, variations)
            if current["pending_agent"] == "scene" and action == "approve":
                picked = _image_request(current, images or [])
            self._busy.add(job_id)
        resume: dict[str, Any] = {"action": action, "note": note.strip()}
        if choice:
            resume["styles"] = choice["styles"]
            resume["variations"] = choice["variations"]
            resume["prompt"] = choice["styles"][0]
        elif prompt.strip():
            resume["prompt"] = prompt.strip()[:500]
        if picked is not None:
            resume["images"] = picked
        self._launch(job_id, Command(resume=resume))
        return self.view(job_id)

    def view(self, job_id: str) -> dict[str, Any]:
        board = self.status.snapshot(job_id)
        if board is None:
            raise JobError(404, "Unknown job")
        board["pending_agent"] = None
        board["approve_allowed"] = False
        for agent in board["agents"]:
            agent["output"] = _with_urls(self.public_url, job_id, agent["output"])
        if job_id in self._busy:
            board["status"] = "running"
            return board
        if board["status"] == "failed":
            return board
        payload = _interrupt_value(self.graph.get_state({"configurable": {"thread_id": job_id}}))
        if payload:
            board["status"] = "waiting"
            board["pending_agent"] = payload.get("agent")
            board["approve_allowed"] = bool(payload.get("approve_allowed"))
            return board
        if board["status"] == "approved" or _all_approved(board):
            board["status"] = "approved"
        return board

    def file(self, job_id: str, name: str) -> Path:
        path = (self.data_dir / "jobs" / job_id / name).resolve()
        root = (self.data_dir / "jobs" / job_id).resolve()
        if path.parent != root or not path.is_file():
            raise JobError(404, "File not found")
        return path

    def _launch(self, job_id: str, payload: Any) -> None:
        with self._guard:
            self._busy.add(job_id)

        def run() -> None:
            config = {"configurable": {"thread_id": job_id}, "recursion_limit": 60}
            try:
                self.graph.invoke(payload, config)
                snapshot = self.graph.get_state(config)
                if not _interrupt_value(snapshot) and _all_approved(self.status.snapshot(job_id) or {"agents": []}):
                    self.status.finish(job_id)
            except Exception as exc:
                self.status.fail(job_id, str(exc))
            finally:
                with self._guard:
                    self._busy.discard(job_id)

        threading.Thread(target=run, name=f"catalogmuse-{job_id}", daemon=True).start()


def decode_image(image_base64: str) -> bytes:
    try:
        data = base64.b64decode(image_base64, validate=False)
    except Exception as exc:
        raise JobError(400, "Image data is not valid") from exc
    if not data:
        raise JobError(400, "A supplier photo is required")
    if len(data) > 8_000_000:
        raise JobError(400, "Image must be under 8 MB")
    return data


def _interrupt_value(snapshot: Any) -> dict[str, Any] | None:
    interrupts = getattr(snapshot, "interrupts", None) or ()
    if not interrupts:
        return None
    item = interrupts[0]
    value = getattr(item, "value", item)
    return value if isinstance(value, dict) else None


def _all_approved(board: dict[str, Any]) -> bool:
    agents = board.get("agents") or []
    return bool(agents) and all(agent["state"] == "approved" for agent in agents)


def _image_request(current: dict[str, Any], images: list[str]) -> list[str]:
    scene = next((item for item in current["agents"] if item["name"] == "scene"), {})
    known = [
        str(item.get("file"))
        for item in ((scene.get("output") or {}).get("images") or [])
        if isinstance(item, dict) and item.get("file")
    ]
    wanted = [str(item).strip() for item in images if str(item).strip()]
    if not wanted:
        if not known:
            raise JobError(400, "Select at least one image")
        return known
    missing = [name for name in wanted if name not in set(known)]
    if missing:
        raise JobError(400, "Choose images from this scene")
    chosen: list[str] = []
    for name in wanted:
        if name not in chosen:
            chosen.append(name)
    return chosen


def _scene_request(styles: list[str], prompt: str, variations: int | None) -> dict[str, Any]:
    chosen = [_style_sentence(item) for item in styles if str(item).strip()]
    if not chosen and prompt.strip():
        chosen = [_style_sentence(prompt)]
    if not chosen:
        raise JobError(400, "Select at least one style")
    if len(chosen) > 8:
        raise JobError(400, "Select at most 8 styles")
    count = 1 if variations is None else variations
    if count < 1 or count > 4:
        raise JobError(400, "Images per style must be from 1 to 4")
    return {"styles": chosen, "variations": count}


def _style_sentence(value: Any) -> str:
    sentence = " ".join(str(value).split())
    if "16:9" not in sentence:
        sentence = sentence.rstrip(".") + ", 16:9."
    return sentence[:500]


def _with_urls(public_url: str, job_id: str, output: Any) -> Any:
    if not isinstance(output, dict):
        return output
    result = dict(output)
    if "file" in result:
        result["url"] = file_url(public_url, job_id, str(result["file"]))
    images = result.get("images")
    if isinstance(images, list):
        result["images"] = [
            {**item, "url": file_url(public_url, job_id, str(item["file"]))}
            if isinstance(item, dict) and item.get("file")
            else item
            for item in images
        ]
    return result
