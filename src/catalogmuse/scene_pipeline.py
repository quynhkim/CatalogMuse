"""Send the product cutout to Muse Image and save one scene per variation.

Each style is one commercial request. The variations in that request share the
prompt and come back together. A lock keeps two jobs from spending the API at once.
"""

from __future__ import annotations

import io
import threading
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from catalogmuse.blobs import put_file
from catalogmuse.muse_api import edit_images, image_model

_SCENE_LOCK = threading.Lock()


def render_scene(
    cutout_path: str,
    work_dir: str,
    prompts: list[str],
    variations: int,
    feedback: str,
    progress: Callable[[int], None] | None = None,
) -> dict[str, Any]:
    styles = [str(item).strip() for item in prompts if str(item).strip()]
    count = int(variations or 1)
    if not styles:
        raise RuntimeError("The art director has not written a scene prompt")
    if len(styles) > 8:
        raise RuntimeError("Select at most 8 styles")
    if count < 1 or count > 4:
        raise RuntimeError("Images per style must be from 1 to 4")
    cutout = Path(cutout_path).read_bytes()
    with _SCENE_LOCK:
        return _render_locked(cutout, Path(work_dir), styles, count, feedback, progress)


def _render_locked(
    cutout: bytes,
    work: Path,
    styles: list[str],
    variations: int,
    feedback: str,
    progress: Callable[[int], None] | None,
) -> dict[str, Any]:
    images: list[dict[str, Any]] = []
    total = len(styles) * variations
    for style_index, prompt in enumerate(styles, start=1):
        scene_prompt = prompt
        if feedback.strip():
            scene_prompt = f"{scene_prompt} The reviewer asked: {feedback.strip()}."
        if progress:
            progress(len(images) + 1)
        rendered = edit_images(cutout, _instruction(scene_prompt), variations)
        for variation, blob in enumerate(rendered, start=1):
            hero_path = work / f"hero-{style_index}-{variation}.jpg"
            _write_jpeg(blob, hero_path)
            put_file(work.name, hero_path)
            images.append(
                {
                    "file": hero_path.name,
                    "prompt": prompt,
                    "style": style_index,
                    "variation": variation,
                }
            )
            if progress:
                progress(len(images))
    return {
        "file": images[0]["file"],
        "images": images,
        "prompt": styles[0],
        "variations": variations,
        "count": total,
        "model": image_model(),
        "feedback": feedback,
    }


def _instruction(prompt: str) -> str:
    return (
        "The reference image is the supplier product on a transparent background. "
        "Keep that exact product, place one copy of it in the scene, and match the light. "
        "Do not invent a different product, add a second product, or add text. "
        + prompt
    )


def _write_jpeg(blob: bytes, dest: Path) -> None:
    try:
        image = Image.open(io.BytesIO(blob)).convert("RGB")
    except OSError as exc:
        raise RuntimeError("Muse Image returned an image that could not be read") from exc
    image.save(dest, format="JPEG", quality=90)
