"""The Go backend can create a job, watch agents, and approve or send work back."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

from catalogmuse.app import create_app
from catalogmuse.rules import review_listing, walmart_shelf_description, walmart_short_description

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
SPEC = "Stainless steel garlic press\nBrand: North Kitchen\nMaterial: 18/8 stainless steel\nSize: 7.5 inches"


class FakeTools:
    def __init__(self) -> None:
        self.copy_notes: list[str] = []
        self.scene_prompts: list[str] = []
        self.scene_variations = 0

    def name_product(self, image_path: str, spec: dict, feedback: str) -> dict:
        concept = feedback.strip() if feedback.strip() else "garlic press"
        return {"model": "fake", "concept": concept, "feedback": feedback}

    def segment(self, image_path: str, work_dir: str, spec: dict, feedback: str, concept: str = "") -> dict:
        return {"file": "cutout.png", "model": "sam-3.1", "concept": concept or spec.get("name", ""), "feedback": feedback}

    def art_director(self, spec: dict, feedback: str, image_path: str = "") -> dict:
        styles = [
            "A garlic press on an oak counter, soft morning light, 16:9.",
            "A garlic press on a dining table, warm indoor light, 16:9.",
            "A garlic press on a white studio background, soft shadow, 16:9.",
        ]
        return {"model": "fake", "styles": styles, "prompt": styles[0], "variations": 4, "feedback": feedback}

    def scene(self, cutout_path: str, work_dir: str, prompts: list[str], variations: int, feedback: str, progress=None) -> dict:
        self.scene_prompts = list(prompts)
        self.scene_variations = variations
        images = []
        for style, prompt in enumerate(prompts, start=1):
            for variation in range(1, variations + 1):
                images.append({"file": f"hero-{style}-{variation}.jpg", "prompt": prompt, "style": style, "variation": variation})
                if progress:
                    progress(len(images))
        return {
            "file": images[0]["file"],
            "images": images,
            "prompt": prompts[0],
            "variations": variations,
            "feedback": feedback,
        }

    def copy(self, spec: dict, feedback: str, marketplaces: list[str] | None = None) -> dict:
        self.copy_notes.append(feedback)
        chosen = list(marketplaces or ["amazon"])
        drafted: dict = {"model": "fake", "marketplaces": chosen, "feedback": feedback}
        if "amazon" in chosen:
            if feedback:
                drafted["bullets"] = [
                    "Made of 18/8 stainless steel.",
                    "Measures 7.5 inches.",
                    "Dishwasher safe.",
                    "Includes a cleaning brush.",
                    "See the supplier photo.",
                ]
                drafted["title"] = "North Kitchen Stainless Steel Garlic Press"
                drafted["description"] = "Stainless steel garlic press, 7.5 inches."
            else:
                drafted["bullets"] = [
                    "The best garlic press, guaranteed to crush every clove.",
                    "Made of 18/8 stainless steel.",
                    "Measures 7.5 inches.",
                    "Dishwasher safe.",
                    "Includes a cleaning brush.",
                ]
                drafted["title"] = "Best North Kitchen Garlic Press"
                drafted["description"] = "A stainless steel garlic press."
        if "walmart" in chosen:
            if feedback:
                bullets = [
                    "Made of 18/8 stainless steel.",
                    "Measures 7.5 inches.",
                    "Dishwasher safe.",
                ]
                title = "North Kitchen Stainless Steel Garlic Press 7.5 inches"
                shelf = "Stainless steel garlic press, 7.5 inches."
            else:
                bullets = ["High quality steel.", "Measures 7.5 inches.", "Dishwasher safe."]
                title = "Best North Kitchen Garlic Press"
                shelf = "A high quality garlic press with free shipping."
            drafted["walmart"] = {
                "title": title,
                "bullets": bullets,
                "short_description": walmart_short_description(bullets),
                "shelf_description": walmart_shelf_description(shelf),
            }
        return drafted

    def rules(self, drafted: dict, marketplaces: list[str] | None = None, spec: dict | None = None) -> dict:
        return review_listing(drafted, marketplaces or drafted.get("marketplaces"), spec or {})


def _wait(client: TestClient, job_id: str, agent: str | None = None) -> dict:
    last: dict = {}
    for _ in range(100):
        last = client.get(f"/v1/jobs/{job_id}").json()
        if last.get("status") == "failed":
            raise AssertionError(last)
        if agent and last.get("status") == "waiting" and last.get("pending_agent") == agent:
            return last
        if agent is None and last.get("status") == "approved":
            return last
        time.sleep(0.02)
    raise AssertionError(last)


def test_person_can_send_a_step_back_and_then_approve(tmp_path) -> None:
    app = create_app(tmp_path, FakeTools(), public_url="http://agents.local")
    with TestClient(app) as client:
        created = client.post("/v1/jobs", json={"spec": SPEC, "image_base64": PNG})
        assert created.status_code == 202
        job_id = created.json()["id"]

        chosen_images: list[str] = []
        for agent in ("segment", "art_director", "scene"):
            view = _wait(client, job_id, agent)
            assert view["approve_allowed"] is True
            if agent == "segment":
                cutout = next(item for item in view["agents"] if item["name"] == "segment")
                assert cutout["output"]["concept"] == "garlic press"
            body: dict = {"action": "approve"}
            if agent == "art_director":
                body = {
                    "action": "approve",
                    "styles": [
                        "Edited garlic press on a stone counter, morning light, 16:9.",
                        "A garlic press on a picnic table, late light, 16:9.",
                    ],
                    "variations": 2,
                }
            elif agent == "scene":
                scene = next(item for item in view["agents"] if item["name"] == "scene")
                prompts = [item["prompt"] for item in scene["output"]["images"]]
                assert prompts == [
                    "Edited garlic press on a stone counter, morning light, 16:9.",
                    "Edited garlic press on a stone counter, morning light, 16:9.",
                    "A garlic press on a picnic table, late light, 16:9.",
                    "A garlic press on a picnic table, late light, 16:9.",
                ]
                assert scene["output"]["variations"] == 2
                assert scene["output"]["images"][0]["url"].startswith("http://agents.local/")
                files = [item["file"] for item in scene["output"]["images"]]
                missing = client.post(
                    f"/v1/jobs/{job_id}/decisions",
                    json={"action": "approve", "images": ["missing.jpg"]},
                )
                assert missing.status_code == 400
                assert client.get(f"/v1/jobs/{job_id}").json()["pending_agent"] == "scene"
                chosen_images = [files[0], files[-1]]
                body = {"action": "approve", "images": chosen_images}
            assert client.post(f"/v1/jobs/{job_id}/decisions", json=body).status_code == 202

        held = _wait(client, job_id, "rules")
        assert held["pending_agent"] == "rules"
        assert held["approve_allowed"] is False
        assert any(agent["state"] == "waiting" and agent["name"] == "copy" for agent in held["agents"])
        separate = client.post(f"/v1/jobs/{job_id}/decisions", json={"action": "approve", "agent": "copy"})
        assert separate.status_code == 409
        rejected = client.post(f"/v1/jobs/{job_id}/decisions", json={"action": "approve"})
        assert rejected.status_code == 409

        changed = client.post(
            f"/v1/jobs/{job_id}/decisions",
            json={"action": "changes", "note": "Remove the supplier claim."},
        )
        assert changed.status_code == 202
        revised = _wait(client, job_id, "rules")
        copy = next(agent for agent in revised["agents"] if agent["name"] == "copy")
        assert copy["output"]["feedback"] == "Remove the supplier claim."
        assert revised["approve_allowed"] is True
        assert client.post(f"/v1/jobs/{job_id}/decisions", json={"action": "approve"}).status_code == 202
        finished = _wait(client, job_id)
        assert finished["status"] == "approved"
        assert [agent["state"] for agent in finished["agents"]] == ["approved"] * 5
        kept = next(agent for agent in finished["agents"] if agent["name"] == "scene")
        assert kept["output"]["selected"] == chosen_images


def test_a_scene_note_recuts_and_waits(tmp_path) -> None:
    app = create_app(tmp_path, FakeTools(), public_url="http://agents.local")
    with TestClient(app) as client:
        created = client.post("/v1/jobs", json={"spec": SPEC, "image_base64": PNG})
        job_id = created.json()["id"]
        for agent in ("segment", "art_director"):
            _wait(client, job_id, agent)
            body: dict = {"action": "approve"}
            if agent == "art_director":
                body = {"action": "approve", "styles": ["A garlic press on a counter, morning light, 16:9."], "variations": 1}
            assert client.post(f"/v1/jobs/{job_id}/decisions", json=body).status_code == 202
        waiting = _wait(client, job_id, "scene")
        assert waiting["pending_agent"] == "scene"
        recut = client.post(
            f"/v1/jobs/{job_id}/decisions",
            json={"action": "changes", "note": "black tumbler"},
        )
        assert recut.status_code == 202
        again = _wait(client, job_id, "segment")
        assert again["pending_agent"] == "segment"
        segment = next(agent for agent in again["agents"] if agent["name"] == "segment")
        assert segment["state"] == "waiting"
        assert segment["output"]["feedback"] == "black tumbler"


def test_health_and_missing_photo(tmp_path) -> None:
    app = create_app(tmp_path, FakeTools(), public_url="")
    with TestClient(app) as client:
        assert client.get("/health").json()["service"] == "catalogmuse-engine"
        page = client.get("/")
        assert page.status_code == 200
        assert "Request changes" in page.text
        assert "Choose scene styles" in page.text
        assert "Choose images" in page.text
        assert "Add a style" in page.text
        assert "Images per style" in page.text
        assert "Walmart" in page.text
        assert "Drop this when the React app is ready." in page.text
        missing = client.post("/v1/jobs", json={"spec": SPEC, "image_base64": ""})
        assert missing.status_code == 400


def test_browser_preflight_is_allowed(tmp_path) -> None:
    app = create_app(tmp_path, FakeTools(), public_url="")
    with TestClient(app) as client:
        preflight = client.options(
            "/v1/jobs",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert preflight.status_code == 200
        assert preflight.headers["access-control-allow-origin"] == "*"
        assert "POST" in preflight.headers["access-control-allow-methods"].upper()
        health = client.get("/health", headers={"Origin": "https://app.asinzen.com"})
        assert health.headers["access-control-allow-origin"] == "*"


def test_both_marketplaces_stay_closed_until_walmart_is_clear(tmp_path) -> None:
    app = create_app(tmp_path, FakeTools(), public_url="")
    with TestClient(app) as client:
        created = client.post(
            "/v1/jobs",
            json={"spec": SPEC, "image_base64": PNG, "marketplaces": ["walmart", "amazon"]},
        )
        assert created.status_code == 202
        assert created.json()["marketplaces"] == ["amazon", "walmart"]
        job_id = created.json()["id"]
        for agent in ("segment", "art_director", "scene"):
            _wait(client, job_id, agent)
            body: dict = {"action": "approve"}
            if agent == "art_director":
                body = {"action": "approve", "styles": ["Oak counter, morning light, 16:9."], "variations": 1}
            assert client.post(f"/v1/jobs/{job_id}/decisions", json=body).status_code == 202
        held = _wait(client, job_id, "rules")
        assert held["approve_allowed"] is False
        rules = next(agent for agent in held["agents"] if agent["name"] == "rules")["output"]
        assert rules["amazon"]["clear"] is False
        assert rules["walmart"]["clear"] is False
        assert any(item.startswith("Walmart:") for item in rules["violations"])
        assert client.post(f"/v1/jobs/{job_id}/decisions", json={"action": "approve"}).status_code == 409
        assert client.post(
            f"/v1/jobs/{job_id}/decisions",
            json={"action": "changes", "note": "Remove the supplier claim."},
        ).status_code == 202
        revised = _wait(client, job_id, "rules")
        walmart = next(agent for agent in revised["agents"] if agent["name"] == "copy")["output"]["walmart"]
        assert walmart["title"].startswith("North Kitchen")
        assert walmart["short_description"].startswith("<ul>")
        assert revised["approve_allowed"] is True
        assert client.post(f"/v1/jobs/{job_id}/decisions", json={"action": "approve"}).status_code == 202
        assert _wait(client, job_id)["status"] == "approved"


def test_unknown_marketplace_is_rejected(tmp_path) -> None:
    app = create_app(tmp_path, FakeTools(), public_url="")
    with TestClient(app) as client:
        rejected = client.post(
            "/v1/jobs",
            json={"spec": SPEC, "image_base64": PNG, "marketplaces": ["ebay"]},
        )
        assert rejected.status_code == 400
        assert rejected.json()["error"] == "Marketplace must be amazon or walmart"


def test_scene_keeps_the_requested_styles_and_rejects_more_than_four(tmp_path) -> None:
    tools = FakeTools()
    app = create_app(tmp_path, tools, public_url="")
    with TestClient(app) as client:
        created = client.post("/v1/jobs", json={"spec": SPEC, "image_base64": PNG})
        job_id = created.json()["id"]
        _wait(client, job_id, "segment")
        assert client.post(f"/v1/jobs/{job_id}/decisions", json={"action": "approve"}).status_code == 202
        _wait(client, job_id, "art_director")
        too_many = client.post(
            f"/v1/jobs/{job_id}/decisions",
            json={"action": "approve", "styles": ["Oak counter, morning light, 16:9."], "variations": 5},
        )
        assert too_many.status_code == 400
        empty = client.post(f"/v1/jobs/{job_id}/decisions", json={"action": "approve", "styles": ["  "], "variations": 2})
        assert empty.status_code == 400
        extras = [f"Style {index}, 16:9." for index in range(9)]
        over = client.post(f"/v1/jobs/{job_id}/decisions", json={"action": "approve", "styles": extras, "variations": 1})
        assert over.status_code == 400
        still = client.get(f"/v1/jobs/{job_id}").json()
        assert still["pending_agent"] == "art_director"
        accepted = client.post(
            f"/v1/jobs/{job_id}/decisions",
            json={"action": "approve", "prompt": "Blue tile counter, noon light", "variations": 3},
        )
        assert accepted.status_code == 202
        scene = _wait(client, job_id, "scene")
        output = next(agent for agent in scene["agents"] if agent["name"] == "scene")["output"]
        assert tools.scene_variations == 3
        assert tools.scene_prompts == ["Blue tile counter, noon light, 16:9."]
        assert len(output["images"]) == 3
        assert {item["variation"] for item in output["images"]} == {1, 2, 3}


def test_job_image_url_uses_s3_when_a_signed_url_is_available(monkeypatch) -> None:
    from catalogmuse.orchestrator import _with_urls

    monkeypatch.setattr(
        "catalogmuse.blobs.signed_url",
        lambda job_id, name: f"https://s3.example/{job_id}/{name}",
    )
    output = _with_urls(
        "http://agents.local",
        "job_1",
        {"file": "cutout.png", "images": [{"file": "hero-1-1.jpg", "variation": 1}]},
    )
    assert output["url"] == "https://s3.example/job_1/cutout.png"
    assert output["images"][0]["url"] == "https://s3.example/job_1/hero-1-1.jpg"


def test_signed_url_uses_the_bucket_region(monkeypatch) -> None:
    import catalogmuse.blobs as blobs

    monkeypatch.setenv("CATALOGMUSE_S3_BUCKET", "asinzen-catalogmuse")
    monkeypatch.setenv("AWS_REGION", "us-east-2")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    blobs._CLIENT = None
    url = blobs.signed_url("job_1", "cutout.png")
    blobs._CLIENT = None
    assert url.startswith(
        "https://asinzen-catalogmuse.s3.us-east-2.amazonaws.com/jobs/job_1/cutout.png?"
    )
    assert "X-Amz-Expires=43200" in url
