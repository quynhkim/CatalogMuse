"""The commercial Muse API is what copy and scene call."""

from __future__ import annotations

import io
import json
import urllib.error

import pytest

from PIL import Image

from catalogmuse.muse_api import MuseError, edit_images, segment_image, spark_text
from catalogmuse.tools import Tools, _apply_masks, _attached_parts, _choose_masks, _concept, _cutout_view, _named_concept


class _Body:
    def __init__(self, payload: dict) -> None:
        self._raw = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._raw

    def __enter__(self) -> _Body:
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def test_spark_calls_the_commercial_model(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "secret")
    seen: dict = {}

    def urlopen(request, timeout=0):
        seen["url"] = request.full_url
        seen["auth"] = request.get_header("Authorization")
        seen["body"] = json.loads(request.data.decode())
        seen["timeout"] = timeout
        return _Body({"choices": [{"message": {"content": "{\"styles\":[\"oak\"]}"}}]})

    monkeypatch.setattr("catalogmuse.muse_api.urllib.request.urlopen", urlopen)
    assert spark_text("hello", {"type": "json_schema", "json_schema": {"name": "x", "schema": {}}}) == '{"styles":["oak"]}'
    assert seen["url"] == "https://api.meta.ai/v1/chat/completions"
    assert seen["auth"] == "Bearer secret"
    assert seen["body"]["model"] == "muse-spark-1.3"
    assert seen["body"]["messages"][0]["content"] == "hello"
    assert "secret" not in json.dumps(seen["body"])


def test_spark_can_see_the_supplier_photo(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "secret")
    seen: dict = {}

    def urlopen(request, timeout=0):
        seen["body"] = json.loads(request.data.decode())
        return _Body({"choices": [{"message": {"content": "{\"concept\":\"headphones\"}"}}]})

    monkeypatch.setattr("catalogmuse.muse_api.urllib.request.urlopen", urlopen)
    assert spark_text("name it", {}, b"jpeg-bytes") == '{"concept":"headphones"}'
    content = seen["body"]["messages"][0]["content"]
    assert content[0] == {"type": "text", "text": "name it"}
    assert content[1]["type"] == "image_url"
    assert content[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert content[1]["image_url"]["detail"] == "low"


def test_image_edit_sends_the_cutout_and_asks_for_each_variation(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "secret")
    seen: dict = {}

    def urlopen(request, timeout=0):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data.decode())
        blob = __import__("base64").b64encode(b"jpeg-bytes").decode()
        return _Body({"data": [{"b64_json": blob}, {"b64_json": blob}]})

    monkeypatch.setattr("catalogmuse.muse_api.urllib.request.urlopen", urlopen)
    images = edit_images(b"png-bytes", "oak counter", 2)
    assert images == [b"jpeg-bytes", b"jpeg-bytes"]
    assert seen["url"] == "https://api.meta.ai/v1/images/edits"
    assert seen["body"]["model"] == "muse-image-1.0"
    assert seen["body"]["n"] == 2
    assert seen["body"]["images"][0]["image_url"].startswith("data:image/png;base64,")
    assert seen["body"]["tool_enablement"]["enable_image_search"] is False


def test_sam_sends_the_product_name_with_the_photo(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "secret")
    seen: dict = {}

    def urlopen(request, timeout=0):
        seen["url"] = request.full_url
        seen["body"] = json.loads(request.data.decode())
        return _Body({"output": []})

    monkeypatch.setattr("catalogmuse.muse_api.urllib.request.urlopen", urlopen)
    with pytest.raises(MuseError, match="did not return a mask"):
        segment_image(b"png-bytes", "garlic press", "image/png")
    content = seen["body"]["input"][0]["content"]
    assert seen["url"] == "https://api.meta.ai/v1/responses"
    assert seen["body"]["model"] == "sam-3.1"
    assert content[0] == {"type": "input_text", "text": "garlic press"}
    assert content[1]["image_url"].startswith("data:image/png;base64,")
    assert seen["body"]["metadata"]["mask_encoding"] == "one_bit"


def test_cutout_keeps_only_the_masked_pixels() -> None:
    image = Image.new("RGBA", (4, 3), (10, 20, 30, 255))
    cutout = _apply_masks(
        image,
        [{"raster": b"\x00\x01\x01\x00", "width": 2, "height": 2, "left": 1, "top": 1}],
    )
    assert cutout.getpixel((0, 0))[3] == 0
    assert cutout.getpixel((2, 1))[3] == 255
    assert cutout.getpixel((1, 2))[3] == 255
    assert cutout.getpixel((2, 2))[3] == 0
    assert cutout.getpixel((1, 1))[3] == 0
    assert _concept({"name": "Stainless steel garlic press"}, "") == "Stainless steel garlic press"
    assert _concept({"name": "garlic press"}, "") == "garlic press"
    assert _concept({"name": "Stainless steel garlic press"}, "garlic press") == "garlic press"
    assert _concept({"name": "Grado RS1 Headphone"}, "", "Headphones") == "headphones"
    assert _concept({"name": "Grado RS1 Headphone"}, "ear cups", "headphones") == "ear cups"
    assert _concept({"name": "tumbler"}, "tumbler and straw.", "tumbler") == "tumbler and straw"
    assert _concept({"name": "tumbler"}, "Tumbler with Handle and Straw", "tumbler") == "tumbler with handle and straw"
    assert _concept({"name": "tumbler"}, "the straw", "tumbler") == "straw"
    assert _concept({"name": "tumbler"}, "include the straw", "tumbler") == "tumbler"
    press = {"raster": b"\x01\x01", "width": 2, "height": 1, "confidence": 0.91}
    board = {"raster": b"\x01", "width": 1, "height": 1, "confidence": 0.42}
    close = {"raster": b"\x01", "width": 1, "height": 1, "confidence": 0.88}
    assert _choose_masks([press, board]) == [press]
    assert _choose_masks([press, close]) == [press, close]


def test_cutout_stays_within_1600_pixels(monkeypatch, tmp_path) -> None:
    source = Image.new("RGB", (1800, 900), (20, 40, 60))
    photo = tmp_path / "supplier.jpg"
    source.save(photo, quality=95)

    def fake(image: bytes, concept: str, mime: str = "image/jpeg") -> list[dict]:
        opened = Image.open(io.BytesIO(image))
        assert opened.size == (1600, 800)
        width, height = opened.size
        return [{"raster": bytes([1]) * (width * height), "width": width, "height": height, "left": 0, "top": 0, "confidence": 0.9}]

    monkeypatch.setattr("catalogmuse.tools.segment_image", fake)
    monkeypatch.setattr("catalogmuse.tools.put_file", lambda job_id, path: None)
    result = Tools().segment(str(photo), str(tmp_path), {"name": "tumbler"}, "", "black tumbler")
    assert result["concept"] == "black tumbler"
    assert Image.open(tmp_path / "cutout.png").size == (1600, 800)


def test_separate_parts_from_the_photo_are_added_to_the_cutout(monkeypatch, tmp_path) -> None:
    source = Image.new("RGB", (8, 8), (0, 0, 0))
    photo = tmp_path / "supplier.jpg"
    source.save(photo, quality=95)
    seen: list[str] = []

    def fake_sam(image: bytes, concept: str, mime: str = "image/jpeg") -> list[dict]:
        seen.append(concept)
        if concept == "straw":
            return [{"raster": b"\x01", "width": 1, "height": 1, "left": 4, "top": 0, "confidence": 0.89}]
        if concept == "cable":
            return [{"raster": b"\x01", "width": 1, "height": 1, "left": 80, "top": 0, "confidence": 0.9}]
        if concept == "table":
            return [{"raster": b"\x01" * 8, "width": 8, "height": 1, "left": 0, "top": 0, "confidence": 0.8}]
        return [{"raster": b"\x01" * 4, "width": 4, "height": 1, "left": 0, "top": 0, "confidence": 0.93}]

    def fake_spark(prompt, schema, image=None, mime="image/jpeg"):
        if "headphones" in prompt:
            return '{"parts":[]}'
        return '{"parts":["straw","cable","black tumbler","table"]}'

    monkeypatch.setattr("catalogmuse.tools.segment_image", fake_sam)
    monkeypatch.setattr("catalogmuse.tools.spark_text", fake_spark)
    monkeypatch.setattr("catalogmuse.tools.put_file", lambda job_id, path: None)
    spec = {"name": "tumbler", "spec_sheet": "Includes 1 reusable straw."}
    result = Tools().segment(str(photo), str(tmp_path), spec, "", "black tumbler")
    assert seen == ["black tumbler", "straw", "cable", "table"]
    assert result["concept"] == "black tumbler and straw"
    cutout = Image.open(tmp_path / "cutout.png")
    assert cutout.getpixel((0, 0))[3] == 255
    assert cutout.getpixel((4, 0))[3] == 255
    assert _attached_parts({"name": "headphones"}, "headphones", b"jpeg") == []


def test_art_director_sees_the_cutout(monkeypatch, tmp_path) -> None:
    cutout = Image.new("RGBA", (40, 80), (0, 0, 0, 0))
    cutout.putpixel((4, 8), (10, 20, 30, 255))
    path = tmp_path / "cutout.png"
    cutout.save(path)
    seen: dict = {}

    def fake(prompt, schema, image=None, mime="image/jpeg"):
        seen["prompt"] = prompt
        seen["image"] = image
        return '{"styles":["On a kitchen counter, morning light, 16:9.","On a picnic table, daylight, 16:9.","On white, soft shadow, 16:9."]}'

    monkeypatch.setattr("catalogmuse.tools.spark_text", fake)
    styles = Tools().art_director({"name": "tumbler"}, "", str(path))
    assert len(styles["styles"]) == 3
    assert "cut out" in seen["prompt"]
    view = Image.open(io.BytesIO(seen["image"]))
    assert view.size == (40, 80)
    assert view.getpixel((0, 0)) == (255, 255, 255)
    assert view.getpixel((4, 8)) != (255, 255, 255)
    assert _cutout_view("") is None


def test_spark_names_the_product_with_its_color(monkeypatch) -> None:
    seen: dict = {}

    def fake(prompt, schema, image=None, mime="image/jpeg"):
        seen["prompt"] = prompt
        seen["image"] = image
        return '{"concept":"black tumbler"}'

    monkeypatch.setattr("catalogmuse.tools.spark_text", fake)
    concept = _named_concept({"name": "SKU: TMB-30-SS-BLK"}, "", b"jpeg-bytes")
    assert concept == "black tumbler"
    assert "black tumbler" in seen["prompt"]
    assert "Do not include a brand" in seen["prompt"]
    assert seen["image"] == b"jpeg-bytes"


def test_missing_key_is_reported(monkeypatch) -> None:
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    with pytest.raises(MuseError, match="MODEL_API_KEY"):
        spark_text("hello", {})


def test_api_error_message_is_kept(monkeypatch) -> None:
    monkeypatch.setenv("MODEL_API_KEY", "secret")

    def urlopen(request, timeout=0):
        raise urllib.error.HTTPError(
            request.full_url,
            401,
            "unauthorized",
            hdrs=None,
            fp=io.BytesIO(b'{"error":{"message":"Invalid API key"}}'),
        )

    monkeypatch.setattr("catalogmuse.muse_api.urllib.request.urlopen", urlopen)
    with pytest.raises(MuseError, match="Invalid API key"):
        spark_text("hello", {})
