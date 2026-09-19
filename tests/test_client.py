"""Tests for Project Runeberg client (fetching, normalizing, and context reading)."""

from runeberg_mcp.client import normalize_page_url, fetch_page, fetch_page_with_context, fetch_work_info


def test_normalize_page_url():
    assert normalize_page_url("dasakungen", 5) == "https://runeberg.org/dasakungen/0005.html"
    assert normalize_page_url("dasakungen/0005") == "https://runeberg.org/dasakungen/0005.html"
    assert normalize_page_url("https://runeberg.org/sbh/0100.html") == "https://runeberg.org/sbh/0100.html"
    assert normalize_page_url("karlxiioff") == "https://runeberg.org/karlxiioff/"


def test_fetch_page_clean_text():
    page = fetch_page("dasakungen", 5)
    assert page["url"] == "https://runeberg.org/dasakungen/0005.html"
    assert "FÖRORD" in page["text"]
    assert "faksimil" in page["image_url"].lower() or ".jpg" in page["image_url"].lower()
    # Ensure footer is stripped
    assert "Project Runeberg" not in page["text"]


def test_fetch_page_with_context():
    # Read page 311 of karlxiioff with 1 subsequent context page (page 312)
    data = fetch_page_with_context("https://runeberg.org/karlxiioff/0311.html", context_pages=1)
    assert data["total_pages_read"] == 2
    assert "Hilperhaussen" in data["text"]
    assert "Nästa sida:" in data["text"]


def test_fetch_work_info():
    info = fetch_work_info("karlxiioff")
    assert info["slug"] == "karlxiioff"
    assert info["chapters_count"] > 500
    assert any(c.get("heading") for c in info["chapters"])
