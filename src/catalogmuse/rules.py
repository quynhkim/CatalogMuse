"""Listing rules the agents do not get to override."""

from __future__ import annotations

from typing import Any

TITLE_MAX = 200
BULLET_MAX = 200
BULLET_COUNT = 5
DESCRIPTION_MAX = 1000
BANNED = ("best", "guaranteed", "#1", "free shipping", "cure")

MARKETPLACES = ("amazon", "walmart")
WALMART_TITLE_MAX = 200
WALMART_SHORT_MAX = 1000
WALMART_SHELF_MAX = 4000
WALMART_BULLET_MIN = 3
WALMART_BULLET_MAX = 10
WALMART_BANNED = (
    "#1 rated",
    "best selling",
    "best seller",
    "bestseller",
    "high quality",
    "free shipping",
    "sold on amazon",
    "sold on ebay",
    "ships in",
    "ship time",
    "our company",
    "our store",
    "sold by",
    "promotion",
    "coupon",
    "guaranteed",
    "#1",
    "best",
    "shipping",
    "alexa",
    "price",
)
_TITLE_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 .,'-/&+")


def spec_from_text(text: str) -> dict[str, Any]:
    raw = (text or "").strip()[:2000]
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    name = lines[0][:120] if lines else "Uploaded product"
    spec: dict[str, Any] = {
        "name": name,
        "spec_sheet": raw,
        "brand": "",
        "material": "as shown in the photo",
        "size": "as shown in the photo",
        "power": "",
        "includes": raw[:400] or "the item in the photo",
        "notes": raw[:400] or "Uploaded supplier photo.",
        "supplier_claims": "",
    }
    labels = {"brand": "brand", "material": "material", "size": "size", "capacity": "size", "power": "power"}
    for line in lines[1:]:
        if any(phrase in line.lower() for phrase in BANNED) and not spec["supplier_claims"]:
            spec["supplier_claims"] = line[:300]
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        field = labels.get(key.strip().lower())
        if field and value.strip():
            spec[field] = value.strip()[:120]
    return spec


def check_copy(title: str, bullets: list[str], description: str = "") -> list[str]:
    violations: list[str] = []
    blob = (title + " " + " ".join(bullets) + " " + description).lower()
    for phrase in BANNED:
        if phrase in blob:
            violations.append(f"Banned phrase: {phrase}")
    if len(title) > TITLE_MAX:
        violations.append(f"Title is over {TITLE_MAX} characters")
    if len(bullets) != BULLET_COUNT:
        violations.append(f"Need {BULLET_COUNT} bullets")
    for index, bullet in enumerate(bullets, start=1):
        if len(bullet) > BULLET_MAX:
            violations.append(f"Bullet {index} is over {BULLET_MAX} characters")
    if not description.strip():
        violations.append("Need a description")
    elif len(description) > DESCRIPTION_MAX:
        violations.append(f"Description is over {DESCRIPTION_MAX} characters")
    return violations


def normalize_marketplaces(values: list[str] | None) -> list[str]:
    """Amazon when the caller omits the field. A blank entry is ignored."""
    if not values:
        return ["amazon"]
    chosen: list[str] = []
    for item in values:
        name = str(item or "").strip().lower()
        if not name:
            continue
        if name not in MARKETPLACES:
            raise ValueError(name)
        if name not in chosen:
            chosen.append(name)
    if not chosen:
        return ["amazon"]
    return [name for name in MARKETPLACES if name in chosen]


def is_refurbished(spec: dict[str, Any] | None) -> bool:
    return "refurbished" in " ".join(str(value).lower() for value in (spec or {}).values())


def walmart_short_description(bullets: list[str]) -> str:
    items = "".join(f"<li>{_html_text(item)}</li>" for item in bullets)
    return f"<ul>{items}</ul>"


def walmart_shelf_description(text: str) -> str:
    body = " ".join(str(text or "").split())
    if not body:
        return ""
    if "<p" in body.lower():
        return body
    return f"<p>{_html_text(body)}</p>"


def check_walmart(
    title: str,
    bullets: list[str],
    short_description: str,
    shelf_description: str,
    spec: dict[str, Any] | None = None,
) -> list[str]:
    violations: list[str] = []
    visible = " ".join([title, " ".join(bullets), short_description, shelf_description])
    folded = visible.lower()
    for phrase in WALMART_BANNED:
        if phrase in folded:
            violations.append(f"Banned phrase: {phrase}")
    if "$" in visible or "product cost" in folded:
        violations.append("Price or cost is not allowed")
    if len(title) > WALMART_TITLE_MAX:
        violations.append(f"Title is over {WALMART_TITLE_MAX} characters")
    if any(char not in _TITLE_CHARS for char in title):
        violations.append("Title contains a special character")
    brand = str((spec or {}).get("brand") or "").strip()
    if brand and not title.lower().startswith(brand.lower()):
        violations.append("Title must start with the brand")
    listing = short_description.lower()
    count = listing.count("<li>")
    if count < WALMART_BULLET_MIN or count > WALMART_BULLET_MAX:
        violations.append(f"Short description needs {WALMART_BULLET_MIN} to {WALMART_BULLET_MAX} bullets")
    if not listing.startswith("<ul>") or not listing.endswith("</ul>"):
        violations.append("Short description must be an HTML list")
    if len(short_description) > WALMART_SHORT_MAX:
        violations.append(f"Short description is over {WALMART_SHORT_MAX} characters")
    if not shelf_description.strip():
        violations.append("Need a shelf description")
    elif "<p" not in shelf_description.lower():
        violations.append("Shelf description must use HTML paragraphs")
    elif len(shelf_description) > WALMART_SHELF_MAX:
        violations.append(f"Shelf description is over {WALMART_SHELF_MAX} characters")
    if is_refurbished(spec):
        if "refurbished" not in title.lower():
            violations.append("Refurbished must appear in the title")
        if "refurbished" not in short_description.lower() or "refurbished" not in shelf_description.lower():
            violations.append("Refurbished must appear in the description")
    return violations


def review_listing(
    drafted: dict[str, Any],
    marketplaces: list[str] | None,
    spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    chosen = [name for name in MARKETPLACES if name in (marketplaces or ["amazon"])] or ["amazon"]
    several = len(chosen) > 1
    violations: list[str] = []
    result: dict[str, Any] = {"marketplaces": chosen}
    if "amazon" in chosen:
        found = check_copy(
            str(drafted.get("title") or ""),
            [str(item) for item in drafted.get("bullets") or []],
            str(drafted.get("description") or ""),
        )
        result["amazon"] = {"violations": found, "clear": not found}
        violations.extend(_tagged(found, "Amazon", several))
    if "walmart" in chosen:
        item = drafted.get("walmart") if isinstance(drafted.get("walmart"), dict) else {}
        found = check_walmart(
            str(item.get("title") or ""),
            [str(entry) for entry in item.get("bullets") or []],
            str(item.get("short_description") or ""),
            str(item.get("shelf_description") or ""),
            spec,
        )
        result["walmart"] = {"violations": found, "clear": not found}
        violations.extend(_tagged(found, "Walmart", several))
    result["violations"] = violations
    result["clear"] = not violations
    return result


def _tagged(found: list[str], name: str, several: bool) -> list[str]:
    if not several:
        return list(found)
    return [f"{name}: {item}" for item in found]


def _html_text(value: str) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
