"""Test suite for Runeberg MCP Server."""

from runeberg_mcp.server import (
    runeberg_search,
    runeberg_read_page,
    runeberg_get_work_info,
)


def run_tests():
    print("=== Test 1: Search Project Runeberg (runeberg_search) ===")
    res1 = runeberg_search(query="Dödsdansen", max_results=3)
    print(res1)
    assert "Dödsdansen" in res1, "Expected 'Dödsdansen' in search results"
    print("✓ Search test passed.")

    print("\n=== Test 2: Read Page (runeberg_read_page) ===")
    res2 = runeberg_read_page(url_or_slug="dasakungen", page=5)
    print(res2[:400] + "...\n")
    assert "FÖRORD" in res2, "Expected 'FÖRORD' in dasakungen page 5"
    assert "Källa: https://runeberg.org/dasakungen/0005.html" in res2
    print("✓ Read page test passed.")

    print("\n=== Test 3: Get Work Info (runeberg_get_work_info) ===")
    res3 = runeberg_get_work_info(work_slug="dasakungen")
    print(res3[:400] + "...\n")
    assert "dasakungen" in res3
    assert "1946" in res3
    print("✓ Get work info test passed.")

    print("\n🎉 All tests passed successfully!")


if __name__ == "__main__":
    run_tests()
