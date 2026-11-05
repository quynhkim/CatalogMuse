"""Commercial Meta Model API.

Muse Spark writes the scene styles and the listing. Muse Image paints each
scene from the product cutout. The key stays in MODEL_API_KEY.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any


class MuseError(RuntimeError):
    pass


def text_model() -> str:
    return os.environ.get("CATALOGMUSE_TEXT_MODEL", "muse-spark-1.3")


def image_model() -> str:
    return os.environ.get("CATALOGMUSE_IMAGE_MODEL", "muse-image-1.0")


def sam_model() -> str:
    return os.environ.get("CATALOGMUSE_SAM_MODEL", "sam-3.1")


def spark_text(prompt: str, schema: dict[str, Any], image: bytes | None = None, mime: str = "image/jpeg") -> str:
    content: Any = prompt
    if image:
        encoded = base64.b64encode(image).decode("ascii")
        content = [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}", "detail": "low"}},
        ]
    payload = _post(
        "/chat/completions",
        {
            "model": text_model(),
            "messages": [{"role": "user", "content": content}],
            "temperature": 0.2,
            "response_format": schema,
        },
        120,
    )
    try:
        return str(payload["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise MuseError("Muse Spark did not return text") from exc


def segment_image(image: bytes, concept: str, mime: str = "image/png") -> list[dict[str, Any]]:
    """Ask SAM 3.1 for every match of one noun phrase. Each mask is box-local."""
    phrase = " ".join(concept.split())
    if not phrase:
        raise MuseError("SAM 3.1 needs the product name")
    encoded = base64.b64encode(image).decode("ascii")
    payload = _post(
        "/responses",
        {
            "model": sam_model(),
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": phrase[:240]},
                        {"type": "input_image", "image_url": f"data:{mime};base64,{encoded}"},
                    ],
                }
            ],
            "metadata": {"mask_encoding": "one_bit", "include_confidence": "true"},
        },
        180,
    )
    text = _output_text(payload)
    if not text.strip():
        raise MuseError("SAM 3.1 did not return a mask")
    return _masks(text, phrase)


def edit_images(png: bytes, prompt: str, count: int) -> list[bytes]:
    encoded = base64.b64encode(png).decode("ascii")
    payload = _post(
        "/images/edits",
        {
            "model": image_model(),
            "prompt": prompt,
            "images": [{"image_url": f"data:image/png;base64,{encoded}"}],
            "n": count,
            "size": "1792x1024",
            "response_format": "b64_json",
            "output_format": "jpeg",
            "reasoning_strength": "low",
            "tool_enablement": {
                "enable_image_search": False,
                "enable_web_search": False,
                "enable_shell": False,
            },
        },
        300,
    )
    data = payload.get("data")
    if not isinstance(data, list):
        raise MuseError("Muse Image did not return images")
    images: list[bytes] = []
    for item in data:
        raw = item.get("b64_json") if isinstance(item, dict) else None
        if not raw:
            continue
        try:
            images.append(base64.b64decode(raw))
        except (ValueError, TypeError) as exc:
            raise MuseError("Muse Image returned an image that could not be read") from exc
    if len(images) < count:
        raise MuseError("Muse Image returned fewer images than requested")
    return images[:count]


def _post(path: str, body: dict[str, Any], timeout: int) -> dict[str, Any]:
    root = os.environ.get("CATALOGMUSE_MUSE_URL", "https://api.meta.ai/v1").rstrip("/")
    request = urllib.request.Request(
        root + path,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        message = _error_message(detail) or f"Muse API returned {exc.code}"
        raise MuseError(message) from exc
    except urllib.error.URLError as exc:
        raise MuseError("The Muse API could not be reached") from exc
    except TimeoutError as exc:
        raise MuseError("The Muse API took too long") from exc
    except json.JSONDecodeError as exc:
        raise MuseError("The Muse API returned a response that is not JSON") from exc
    if not isinstance(payload, dict):
        raise MuseError("The Muse API returned a response that is not JSON")
    return payload


def _output_text(payload: dict[str, Any]) -> str:
    chunks: list[str] = []
    output = payload.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("text"):
                        chunks.append(str(part["text"]))
            if isinstance(item.get("text"), str):
                chunks.append(item["text"])
    if isinstance(payload.get("output_text"), str):
        chunks.append(payload["output_text"])
    return "\n".join(chunks)


def _masks(text: str, concept: str) -> list[dict[str, Any]]:
    try:
        from meta_sam_parser import CompletedOutcome, decode_mask_to_raster, image_segmentation_format
    except ImportError as exc:
        raise MuseError("The SAM response parser is not installed") from exc
    parser = image_segmentation_format().create_parser()
    parser.push(text if text.endswith("\n") else text + "\n")
    result = parser.finish(CompletedOutcome()).result
    masks: list[dict[str, Any]] = []
    for record in result.records:
        if getattr(record, "kind", None) != "mask":
            continue
        raster = decode_mask_to_raster(record.mask)
        if len(raster) != record.mask.width * record.mask.height:
            raise MuseError("SAM 3.1 returned a mask that could not be read")
        masks.append(
            {
                "raster": raster,
                "width": record.mask.width,
                "height": record.mask.height,
                "left": int(record.bounds.left),
                "top": int(record.bounds.top),
                "confidence": record.confidence,
            }
        )
    if not masks:
        raise MuseError(f"SAM 3.1 did not find {concept}. Name the object, such as garlic press.")
    return masks


def _key() -> str:
    key = os.environ.get("MODEL_API_KEY", "").strip()
    if not key:
        raise MuseError("Set MODEL_API_KEY to use the Muse API")
    return key


def _error_message(detail: str) -> str:
    try:
        payload = json.loads(detail)
    except json.JSONDecodeError:
        return ""
    error = payload.get("error") if isinstance(payload, dict) else None
    if isinstance(error, dict) and error.get("message"):
        return str(error["message"])[:300]
    return ""
