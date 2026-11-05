"""Walmart listing checks stay in code, beside the Amazon checks."""

from catalogmuse.rules import (
    check_walmart,
    normalize_marketplaces,
    walmart_shelf_description,
    walmart_short_description,
)

SPEC = {"name": "Garlic Press", "brand": "North Kitchen", "material": "stainless steel", "size": "7.5 inches"}


def _clean() -> dict[str, str | list[str]]:
    bullets = ["Made of stainless steel.", "Measures 7.5 inches.", "Dishwasher safe."]
    return {
        "title": "North Kitchen Stainless Steel Garlic Press 7.5 inches",
        "bullets": bullets,
        "short_description": walmart_short_description(bullets),
        "shelf_description": walmart_shelf_description("Stainless steel garlic press, 7.5 inches."),
    }


def test_a_plain_walmart_listing_is_clear() -> None:
    item = _clean()
    assert check_walmart(item["title"], item["bullets"], item["short_description"], item["shelf_description"], SPEC) == []


def test_walmart_rejects_marketing_price_and_other_marketplaces() -> None:
    item = _clean()
    item["title"] = "Best North Kitchen Garlic Press™"
    item["shelf_description"] = walmart_shelf_description("High quality press. Sold on Amazon. $12.")
    found = check_walmart(item["title"], item["bullets"], item["short_description"], item["shelf_description"], SPEC)
    assert "Banned phrase: best" in found
    assert "Banned phrase: high quality" in found
    assert "Banned phrase: sold on amazon" in found
    assert "Title contains a special character" in found
    assert "Price or cost is not allowed" in found


def test_walmart_short_description_needs_three_to_ten_html_bullets() -> None:
    item = _clean()
    short = walmart_short_description(["Made of stainless steel.", "Measures 7.5 inches."])
    found = check_walmart(item["title"], item["bullets"], short, item["shelf_description"], SPEC)
    assert "Short description needs 3 to 10 bullets" in found


def test_refurbished_must_be_named() -> None:
    item = _clean()
    spec = {**SPEC, "spec_sheet": "Refurbished garlic press"}
    found = check_walmart(item["title"], item["bullets"], item["short_description"], item["shelf_description"], spec)
    assert "Refurbished must appear in the title" in found
    assert "Refurbished must appear in the description" in found
    item["title"] = "North Kitchen Refurbished Garlic Press"
    item["bullets"] = ["Refurbished.", "Made of stainless steel.", "Measures 7.5 inches."]
    item["short_description"] = walmart_short_description(item["bullets"])
    item["shelf_description"] = walmart_shelf_description("Refurbished stainless steel garlic press.")
    assert check_walmart(item["title"], item["bullets"], item["short_description"], item["shelf_description"], spec) == []


def test_omitted_marketplaces_mean_amazon() -> None:
    assert normalize_marketplaces(None) == ["amazon"]
    assert normalize_marketplaces(["walmart", "amazon", "walmart"]) == ["amazon", "walmart"]
    try:
        normalize_marketplaces(["ebay"])
    except ValueError as exc:
        assert str(exc) == "ebay"
    else:
        raise AssertionError("ebay should be rejected")
