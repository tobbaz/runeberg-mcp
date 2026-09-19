"""Test suite for Runeberg MCP Server v0.2.0."""

from runeberg_mcp.server import (
    runeberg_search,
    runeberg_read_page,
    runeberg_search_in_work,
    runeberg_get_work_info,
)


def run_tests():
    print("=== Test 1: Global Search with Historical Variant Expansion ===")
    res1 = runeberg_search(query="Hilpershausen", max_results=5)
    print(res1[:400] + "...\n")
    assert "runeberg.org" in res1
    print("✓ Global search test passed.")

    print("\n=== Test 2: In-Work Lemma Bisection & Fuzzy Search (karlxiioff) ===")
    # Search for "Hilpershausen" with 's' and ensure it finds "Hilperhaussen" in Karl XII:s officerare
    res2 = runeberg_search_in_work(work_slug="karlxiioff", query="Hilpershausen", max_results=3)
    print(res2)
    assert "Hilperhaussen" in res2, "Expected 'Hilperhaussen' to be found in Karl XII:s officerare"
    assert "0311.html" in res2
    print("✓ In-work fuzzy bisection search test passed.")

    print("\n=== Test 3: Read Page with Subsequent Context Pages (-c 1) ===")
    res3 = runeberg_read_page(url_or_slug="https://runeberg.org/karlxiioff/0311.html", context_pages=1)
    print(res3[:350] + "...\n")
    assert "Gustaf Fredrik" in res3
    assert "sammanhängande sidor" in res3
    print("✓ Context page reading test passed.")

    print("\n=== Test 4: Get Work Info and Lemma Index (karlxiioff) ===")
    res4 = runeberg_get_work_info(work_slug="karlxiioff")
    print(res4[:350] + "...\n")
    assert "karlxiioff" in res4
    print("✓ Work info test passed.")

    print("\n🎉 All v0.2.0 tests passed successfully!")


if __name__ == "__main__":
    run_tests()
