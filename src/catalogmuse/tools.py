"""The work each agent does. The graph decides the order and when to stop for a person."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from catalogmuse.blobs import put_file
from catalogmuse.muse_api import MuseError, sam_model, segment_image, spark_text, text_model
from catalogmuse.rules import (
    WALMART_TITLE_MAX,
    is_refurbished,
    review_listing,
    walmart_shelf_description,
    walmart_short_description,
)


class Tools:
    def name_product(self, image_path: str, spec: dict[str, Any], feedback: str) -> dict[str, Any]:
        """The art director names the visible object before SAM runs."""
        note = _short_noun(feedback)
        if note:
            return {"model": "reviewer", "concept": note, "feedback": feedback}
        image = Image.open(image_path).convert("RGB")
        image.thumbnail((1024, 1024))
        encoded = io.BytesIO()
        image.save(encoded, format="JPEG", quality=85)
        concept = _named_concept(spec, feedback, encoded.getvalue())
        return {"model": text_model(), "concept": concept, "feedback": feedback}

    def segment(self, image_path: str, work_dir: str, spec: dict[str, Any], feedback: str, concept: str = "") -> dict[str, Any]:
        dest = Path(work_dir) / "cutout.png"
        image = Image.open(image_path).convert("RGBA")
        image.thumbnail((1600, 1600))
        concept = _concept(spec, feedback, concept)
        encoded = io.BytesIO()
        image.convert("RGB").save(encoded, format="JPEG", quality=90)
        photo = encoded.getvalue()
        try:
            masks = _choose_masks(segment_image(photo, concept, "image/jpeg"))
        except MuseError as exc:
            fallback = _product_name(spec)
            # A reviewer's noun stands. Falling back to the product name looks like the note was ignored.
            if feedback.strip() or fallback.casefold() == concept.casefold() or "did not" not in str(exc):
                raise
            concept = fallback
            masks = _choose_masks(segment_image(photo, concept, "image/jpeg"))
        for part in _attached_parts(spec, concept, photo):
            try:
                extra = _choose_masks(segment_image(photo, part, "image/jpeg"))
            except MuseError:
                continue
            if not _part_fits(masks, extra):
                continue
            masks.extend(extra)
            concept = f"{concept} and {part}"
        cutout = _apply_masks(image, masks)
        cutout.save(dest)
        put_file(Path(work_dir).name, dest)
        scores = [item["confidence"] for item in masks if isinstance(item.get("confidence"), (int, float))]
        return {
            "file": dest.name,
            "model": sam_model(),
            "concept": concept,
            "masks": len(masks),
            "confidence": max(scores) if scores else None,
            "feedback": feedback,
        }

    def art_director(self, spec: dict[str, Any], feedback: str, image_path: str = "") -> dict[str, Any]:
        return _art_direction(spec, feedback, image_path)

    def scene(
        self,
        cutout_path: str,
        work_dir: str,
        prompts: list[str],
        variations: int,
        feedback: str,
        progress: Callable[[int], None] | None = None,
    ) -> dict[str, Any]:
        from catalogmuse.scene_pipeline import render_scene

        return render_scene(cutout_path, work_dir, prompts, variations, feedback, progress)

    def copy(self, spec: dict[str, Any], feedback: str, marketplaces: list[str] | None = None) -> dict[str, Any]:
        chosen = marketplaces or ["amazon"]
        drafted = _draft(spec, feedback, chosen)
        drafted["feedback"] = feedback
        drafted["marketplaces"] = chosen
        return drafted

    def rules(
        self,
        drafted: dict[str, Any],
        marketplaces: list[str] | None = None,
        spec: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return review_listing(drafted, marketplaces or drafted.get("marketplaces"), spec)


def _concept(spec: dict[str, Any], feedback: str, directed: str = "") -> str:
    """SAM searches for one visual noun. A short change note replaces the art director's noun."""
    note = _short_noun(feedback)
    if note:
        return note
    chosen = _visual_noun(directed)
    if chosen:
        return chosen
    return _product_name(spec)


_INSTRUCTIONS = {
    "include",
    "add",
    "use",
    "fix",
    "remove",
    "cut",
    "show",
    "keep",
    "make",
    "change",
    "find",
    "search",
    "only",
    "try",
    "please",
    "need",
    "missing",
}


def _short_noun(text: str) -> str:
    """A reviewer's phrase is the concept, at whatever length they wrote."""
    note = " ".join(str(text or "").split()).strip(".!? ")
    if not note or any(mark in note for mark in ".?!"):
        return ""
    if note.split()[0].lower() in _INSTRUCTIONS:
        return ""
    return _visual_noun(note, limit=None)


def _visual_noun(text: str, limit: int | None = 4) -> str:
    words = [word.strip(".,;:()[]\"'") for word in str(text or "").split()]
    words = [word for word in words if word]
    if limit is not None:
        words = words[:limit]
    while words and words[0].lower() in {"the", "a", "an"}:
        words = words[1:]
    return " ".join(words).lower()[:240]


def _named_concept(spec: dict[str, Any], feedback: str, image: bytes) -> str:
    note = feedback.strip()
    if note:
        prompt = (
            "The reviewer rejected the cutout. Their note decides which object to find. "
            "Reply as JSON with one key, concept. "
            "concept is that object, one to three words, lowercase. "
            "If the note names a part, such as a straw, a handle, or ear cups, use that part. "
            "Do not ignore the note. Do not include a brand or a model number. "
            f"Note: {note}. Spec: {json.dumps(spec, ensure_ascii=True)}"
        )
    else:
        prompt = (
            "You name the one product in the photo for a segmentation model. "
            "Reply as JSON with one key, concept. "
            "concept is the everyday visual name of that object, one to three words, lowercase. "
            "Name what a person can see, such as headphones, garlic press, or kettle. "
            "When the spec gives a color and that color is visible in the photo, put the basic color word first, such as black tumbler. "
            "Use black, not a finish such as matte black. "
            "Do not include a brand, a model number, a part, or a scene. "
            f"Spec: {json.dumps(spec, ensure_ascii=True)}"
        )
    try:
        raw = json.loads(spark_text(prompt, _CONCEPT_SCHEMA, image)).get("concept")
        concept = _visual_noun(str(raw or ""))
        if not concept:
            raise ValueError("need a noun")
        return concept
    except MuseError:
        raise
    except (json.JSONDecodeError, ValueError):
        return _product_name(spec)


def _attached_parts(spec: dict[str, Any], concept: str, image: bytes) -> list[str]:
    """SAM matches one noun per call. Each separate piece of the product needs its own search."""
    prompt = (
        "The photo is the supplier picture. The product will be cut out by searching for one object at a time. "
        f"The main search is {concept}. "
        "Reply as JSON with one key, parts. "
        "parts lists the other visible pieces that belong to this product and would be left out of that cutout. "
        "Each part is one or two lowercase words, such as straw, cable, strap, lid, or charger. "
        "Use the spec when it names a piece. Also include a piece you can see in the photo when the spec does not name it. "
        "Do not list the main object, its color, a brand, a model number, or anything in the background. "
        "If nothing separate is visible, return an empty array. "
        f"Spec: {json.dumps(spec, ensure_ascii=True)}"
    )
    try:
        raw = json.loads(spark_text(prompt, _PARTS_SCHEMA, image)).get("parts") or []
    except (MuseError, json.JSONDecodeError, ValueError, TypeError):
        return []
    if not isinstance(raw, list):
        return []
    main = set(concept.lower().split())
    chosen: list[str] = []
    for item in raw:
        part = _visual_noun(str(item or ""), limit=2)
        if not part or part == concept.lower() or part in main or part.rstrip("s") in main:
            continue
        if part.split()[0] in _INSTRUCTIONS:
            continue
        if part not in chosen:
            chosen.append(part)
        if len(chosen) == 3:
            break
    return chosen


def _part_fits(main: list[dict[str, Any]], extra: list[dict[str, Any]]) -> bool:
    """Keep a piece that is smaller than the product and sits against it. Drop the background."""
    main_area = sum(_mask_area(mask) for mask in main)
    extra_area = sum(_mask_area(mask) for mask in extra)
    if main_area <= 0 or extra_area <= 0 or extra_area >= main_area:
        return False
    left, top, right, bottom = _mask_bounds(main)
    span = max(right - left, bottom - top, 1)
    margin = max(40, int(span * 0.25))
    piece_left, piece_top, piece_right, piece_bottom = _mask_bounds(extra)
    if piece_right < left - margin or piece_left > right + margin:
        return False
    if piece_bottom < top - margin or piece_top > bottom + margin:
        return False
    return True


def _mask_area(mask: dict[str, Any]) -> int:
    return sum(1 for value in mask["raster"] if value)


def _mask_bounds(masks: list[dict[str, Any]]) -> tuple[int, int, int, int]:
    left = min(int(mask["left"]) for mask in masks)
    top = min(int(mask["top"]) for mask in masks)
    right = max(int(mask["left"]) + int(mask["width"]) for mask in masks)
    bottom = max(int(mask["top"]) + int(mask["height"]) for mask in masks)
    return left, top, right, bottom


def _product_name(spec: dict[str, Any]) -> str:
    name = " ".join(str(spec.get("name") or "product").split())
    return (name or "product")[:80]


def _choose_masks(masks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep the mask SAM is sure about. A second mask is kept only when it is almost as sure."""
    scored = [mask for mask in masks if isinstance(mask.get("confidence"), (int, float))]
    if scored:
        best = max(float(mask["confidence"]) for mask in scored)
        return [mask for mask in scored if float(mask["confidence"]) >= best - 0.05]

    def area(mask: dict[str, Any]) -> int:
        return sum(1 for value in mask["raster"] if value)

    return [max(masks, key=area)]


def _apply_masks(image: Image.Image, masks: list[dict[str, Any]]) -> Image.Image:
    width, height = image.size
    alpha = bytearray(width * height)
    for mask in masks:
        raster = mask["raster"]
        mask_width = int(mask["width"])
        mask_height = int(mask["height"])
        left = int(mask["left"])
        top = int(mask["top"])
        for y in range(mask_height):
            dy = top + y
            if dy < 0 or dy >= height:
                continue
            row = y * mask_width
            for x in range(mask_width):
                if not raster[row + x]:
                    continue
                dx = left + x
                if 0 <= dx < width:
                    alpha[dy * width + dx] = 255
    if not any(alpha):
        raise MuseError("SAM 3.1 returned an empty mask")
    cutout = image.convert("RGBA")
    cutout.putalpha(Image.frombytes("L", image.size, bytes(alpha)))
    return cutout


def _art_direction(spec: dict[str, Any], feedback: str, image_path: str = "") -> dict[str, Any]:
    change = f" The reviewer asked: {feedback}." if feedback else ""
    prompt = (
        "You are the art director for one product photo. "
        "The photo is the product cut out from the supplier picture. "
        "Reply as JSON with one key, styles. "
        "styles is an array of exactly 3 sentences. "
        "Each sentence places this exact product in one setting, names the light, and ends with 16:9. "
        "Style 1 is a real room that fits the product. Style 2 is a second real setting. "
        "Style 3 is a white studio background with a soft shadow. "
        "Match the product in the photo. Use only the product in the spec. Do not add a second product, text, or a logo. "
        f"{change} Spec: {json.dumps(spec, ensure_ascii=True)}"
    )
    try:
        raw = json.loads(spark_text(prompt, _STYLES_SCHEMA, _cutout_view(image_path))).get("styles") or []
        styles = [_finish_style(str(item)) for item in raw if str(item).strip()]
        if len(styles) < 3:
            raise ValueError("need 3 styles")
        styles = styles[:3]
        model = text_model()
    except MuseError:
        raise
    except (json.JSONDecodeError, ValueError):
        styles = _style_fallback(spec, feedback)
        model = "spec sheet"
    return {"model": model, "styles": styles, "prompt": styles[0], "variations": 4, "feedback": feedback}


def _cutout_view(path: str) -> bytes | None:
    """A JPEG of the cutout on white, small enough for Spark to look at."""
    if not path or not Path(path).is_file():
        return None
    image = Image.open(path).convert("RGBA")
    background = Image.new("RGB", image.size, (255, 255, 255))
    background.paste(image, mask=image.getchannel("A"))
    background.thumbnail((1024, 1024))
    encoded = io.BytesIO()
    background.save(encoded, format="JPEG", quality=85)
    return encoded.getvalue()


def _finish_style(text: str) -> str:
    sentence = " ".join(text.split())
    if "16:9" not in sentence:
        sentence = sentence.rstrip(".") + ", 16:9."
    return sentence


def _style_fallback(spec: dict[str, Any], feedback: str) -> list[str]:
    name = (spec.get("name") or "the product in the photo").strip()
    material = (spec.get("material") or "").strip()
    subject = f"{material} {name}".strip()
    note = f" {feedback.strip()}." if feedback.strip() else ""
    return [
        f"{subject} in a setting that fits this product, soft morning light, 16:9.{note}",
        f"{subject} on a table in warm indoor light, 16:9.{note}",
        f"{subject} on a white studio background with a soft shadow, 16:9.{note}",
    ]


def _facts(spec: dict[str, Any]) -> list[str]:
    return [
        f"Made of {spec.get('material') or 'the material in the photo'}.",
        f"Measures {spec.get('size') or 'the size shown'}.",
        (spec.get("notes") or "See the supplier photo.").rstrip(".") + ".",
        f"Includes {spec.get('includes') or 'the item in the photo'}.",
        "A person approves this listing before it is published.",
    ]


def _draft(spec: dict[str, Any], feedback: str, marketplaces: list[str]) -> dict[str, Any]:
    drafted: dict[str, Any] = {"marketplaces": marketplaces}
    models: list[str] = []
    if "amazon" in marketplaces:
        amazon = _draft_amazon(spec, feedback)
        models.append(str(amazon.pop("model")))
        drafted.update(amazon)
    if "walmart" in marketplaces:
        walmart = _draft_walmart(spec, feedback)
        models.append(str(walmart.pop("model")))
        drafted["walmart"] = walmart
    drafted["model"] = models[0] if len(set(models)) == 1 else " / ".join(models)
    return drafted


def _draft_amazon(spec: dict[str, Any], feedback: str) -> dict[str, Any]:
    claim = (spec.get("supplier_claims") or "").strip()
    change = f" The reviewer asked for this change: {feedback}." if feedback else ""
    prompt = (
        "Write an Amazon listing as JSON with keys title, bullets, and description. "
        "title is one string under 180 characters. Start with the brand when the spec includes one, then the product name. "
        "bullets is an array of exactly 5 short factual strings, each under 180 characters. "
        "description is one factual paragraph under 500 characters. "
        "Use only the spec for product facts. Do not invent measurements, awards, certifications, or medical claims. "
        "Do not describe a room, a counter, food, or a bathroom unless the spec says so. "
        "Do not claim the product was photographed in a room. "
        "Do not use the words best, guaranteed, #1, free shipping, or cure, "
        "unless they already appear in supplier_claims. "
        "If supplier_claims is not empty, bullet 1 must be that claim copied exactly. Do not rewrite it. "
        f"{change} Spec: {json.dumps(spec, ensure_ascii=True)}"
    )
    try:
        data = json.loads(spark_text(prompt, _LISTING_SCHEMA))
        title = str(data.get("title") or spec.get("name") or "Product").strip()
        bullets = [str(item).strip() for item in data.get("bullets") or [] if str(item).strip()]
        description = str(data.get("description") or "").strip()
        model = text_model()
    except MuseError:
        raise
    except (json.JSONDecodeError, ValueError):
        title = (spec.get("name") or "Product").strip()
        bullets = ([claim] if claim else []) + _facts(spec)
        bullets = bullets[:5]
        description = ""
        model = "spec sheet"
    if claim and (not bullets or bullets[0] != claim):
        bullets = [claim] + [item for item in bullets if item != claim]
    while len(bullets) < 5:
        for fact in _facts(spec):
            if fact not in bullets:
                bullets.append(fact)
                break
        else:
            bullets.append("See the supplier photo.")
    if not description:
        description = (spec.get("name") or "See the supplier photo.").strip()
    return {"model": model, "title": title, "bullets": bullets[:5], "description": description[:1000]}


def _draft_walmart(spec: dict[str, Any], feedback: str) -> dict[str, Any]:
    change = f" The reviewer asked for this change: {feedback}." if feedback else ""
    prompt = (
        "Write a Walmart listing as JSON with keys title, bullets, and shelf_description. "
        "title starts with the brand when the spec includes one, then one defining quality written in the spec, "
        "then the item name, then the pack count, size, or color when the spec includes them. "
        "title is under 180 characters and uses only letters, numbers, spaces, and .,'-/&+. "
        "bullets is an array of 3 to 10 short factual key features, plain text, each under 180 characters. "
        "shelf_description is one or two factual paragraphs under 1500 characters, plain text, no HTML. "
        "Use only the spec for product facts. Do not invent measurements, awards, certifications, or medical claims. "
        "Do not mention the seller, shipping, a ship time, a price, a promotion, or a coupon. "
        "Do not name Amazon, eBay, or Alexa. "
        "Do not use best, guaranteed, #1, #1 rated, best selling, bestseller, high quality, or free shipping. "
        "If the spec says the item is refurbished, include the word Refurbished in the title and in shelf_description. "
        f"{change} Spec: {json.dumps(spec, ensure_ascii=True)}"
    )
    try:
        data = json.loads(spark_text(prompt, _WALMART_SCHEMA))
        title = " ".join(str(data.get("title") or "").split())
        bullets = [str(item).strip() for item in data.get("bullets") or [] if str(item).strip()]
        shelf = str(data.get("shelf_description") or "").strip()
        model = text_model()
    except MuseError:
        raise
    except (json.JSONDecodeError, ValueError):
        title = _walmart_title(spec)
        bullets = _walmart_facts(spec)
        shelf = (spec.get("name") or "See the supplier photo.").strip()
        model = "spec sheet"
    bullets = _fit_walmart_bullets(bullets, spec)
    if is_refurbished(spec):
        if "refurbished" not in title.lower():
            title = f"{title} Refurbished".strip()
        if not any("refurbished" in item.lower() for item in bullets):
            bullets = (bullets + ["Refurbished."])[:10]
        if "refurbished" not in shelf.lower():
            shelf = f"{shelf} Refurbished.".strip()
    if not shelf:
        shelf = (spec.get("name") or "See the supplier photo.").strip()
    return {
        "model": model,
        "title": title,
        "bullets": bullets,
        "short_description": walmart_short_description(bullets),
        "shelf_description": walmart_shelf_description(shelf),
    }


def _walmart_title(spec: dict[str, Any]) -> str:
    parts = [str(spec.get("brand") or "").strip(), str(spec.get("name") or "Product").strip()]
    size = str(spec.get("size") or "").strip()
    if size and "as shown" not in size.lower() and size.lower() not in parts[1].lower():
        parts.append(size)
    return " ".join(part for part in parts if part)[:WALMART_TITLE_MAX]


def _walmart_facts(spec: dict[str, Any]) -> list[str]:
    facts: list[str] = []
    material = str(spec.get("material") or "").strip()
    size = str(spec.get("size") or "").strip()
    if material and "as shown" not in material.lower():
        facts.append(f"Made of {material}.")
    if size and "as shown" not in size.lower():
        facts.append(f"Measures {size}.")
    notes = str(spec.get("notes") or "").strip()
    if notes:
        facts.append(notes.rstrip(".") + ".")
    return facts or ["See the supplier photo."]


def _fit_walmart_bullets(bullets: list[str], spec: dict[str, Any]) -> list[str]:
    chosen = bullets[:10]
    for fact in _walmart_facts(spec):
        if len(chosen) >= 3:
            break
        if fact not in chosen:
            chosen.append(fact)
    while len(chosen) < 3:
        chosen.append("See the supplier photo.")
    return chosen[:10]


_PARTS_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "product_parts",
        "schema": {
            "type": "object",
            "properties": {"parts": {"type": "array", "items": {"type": "string"}}},
            "required": ["parts"],
            "additionalProperties": False,
        },
    },
}

_CONCEPT_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "product_noun",
        "schema": {
            "type": "object",
            "properties": {"concept": {"type": "string"}},
            "required": ["concept"],
            "additionalProperties": False,
        },
    },
}

_STYLES_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "scene_styles",
        "schema": {
            "type": "object",
            "properties": {"styles": {"type": "array", "items": {"type": "string"}}},
            "required": ["styles"],
            "additionalProperties": False,
        },
    },
}

_WALMART_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "walmart_listing",
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "bullets": {"type": "array", "items": {"type": "string"}},
                "shelf_description": {"type": "string"},
            },
            "required": ["title", "bullets", "shelf_description"],
            "additionalProperties": False,
        },
    },
}

_LISTING_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "listing",
        "schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "bullets": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string"},
            },
            "required": ["title", "bullets", "description"],
            "additionalProperties": False,
        },
    },
}
