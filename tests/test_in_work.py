"""Tests for in-work lemma bisection and fuzzy search."""

from runeberg_mcp.client import search_in_work


def test_in_work_lemma_bisection_hilpershausen():
    # Searching for 'Hilpershausen' should automatically bisect to lemma 'Hilletan'
    # and find 'Hilperhaussen' on page 0311.html
    results = search_in_work("karlxiioff", "Hilpershausen", max_results=3)
    assert len(results) > 0
    top = results[0]
    assert top["matched_word"] == "Hilperhaussen"
    assert "0311.html" in top["url"]
    assert top["score"] >= 0.90


def test_in_work_exact_match():
    # Searching for exact officer name 'Hilletan'
    results = search_in_work("karlxiioff", "Hilletan", max_results=2)
    assert len(results) > 0
    assert any("0311.html" in r["url"] for r in results)
