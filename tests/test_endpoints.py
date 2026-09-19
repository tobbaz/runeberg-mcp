"""Tests for MCP server tool endpoints."""

from runeberg_mcp.server import (
    runeberg_search,
    runeberg_read_page,
    runeberg_search_in_work,
    runeberg_get_work_info,
)


def test_mcp_read_page():
    res = runeberg_read_page("dasakungen", "0005")
    assert "FÖRORD" in res
    assert "https://runeberg.org/dasakungen/0005.html" in res


def test_mcp_search_in_work():
    res = runeberg_search_in_work("karlxiioff", "Hilpershausen")
    assert "Hilperhaussen" in res
    assert "0311.html" in res


def test_mcp_get_work_info():
    res = runeberg_get_work_info("karlxiioff")
    assert "karlxiioff" in res
    assert "1920" in res
