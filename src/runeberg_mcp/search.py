"""Search backends for Project Runeberg."""

from dataclasses import dataclass
import os
import re
from typing import List, Optional
import httpx
from ddgs import DDGS


@dataclass
class SearchResult:
    """A search result pointing to a Project Runeberg page."""
    title: str
    url: str
    snippet: str
    work_slug: Optional[str] = None
    page: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "work_slug": self.work_slug,
            "page": self.page,
        }


def _extract_slug_and_page(url: str) -> tuple[Optional[str], Optional[str]]:
    """Extract work slug and page filename from a runeberg.org URL."""
    m = re.match(r"^https?://(?:www\.)?runeberg\.org/([^/]+)(?:/(\d{4}|[^/]+)\.html)?", url)
    if m:
        slug = m.group(1)
        page = m.group(2)
        return slug, page
    return None, None


def search_duckduckgo(query: str, max_results: int = 10) -> List[SearchResult]:
    """Search Project Runeberg using DuckDuckGo (zero-config, no API key required)."""
    full_query = f"{query} site:runeberg.org"
    results: List[SearchResult] = []
    
    with DDGS() as ddgs:
        ddg_results = ddgs.text(full_query, max_results=max_results)
        for r in ddg_results:
            url = r.get("href", "")
            if "runeberg.org" not in url:
                continue
            title = r.get("title", "")
            snippet = r.get("body", "")
            slug, page = _extract_slug_and_page(url)
            results.append(
                SearchResult(
                    title=title,
                    url=url,
                    snippet=snippet,
                    work_slug=slug,
                    page=page,
                )
            )
    return results


def search_google(query: str, api_key: str, cse_id: str, max_results: int = 10) -> List[SearchResult]:
    """Search Project Runeberg using the official Google Custom Search JSON API."""
    full_query = f"{query} site:runeberg.org"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": full_query,
        "num": min(max_results, 10),
    }
    
    headers = {
        "User-Agent": "runeberg-mcp/0.1.0 (+https://github.com/tobbaz/runeberg-mcp)"
    }
    
    with httpx.Client(timeout=10.0) as client:
        resp = client.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        
    results: List[SearchResult] = []
    items = data.get("items", [])
    for item in items:
        link = item.get("link", "")
        if "runeberg.org" not in link:
            continue
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        slug, page = _extract_slug_and_page(link)
        results.append(
            SearchResult(
                title=title,
                url=link,
                snippet=snippet,
                work_slug=slug,
                page=page,
            )
        )
    return results


def search(query: str, max_results: int = 10) -> List[SearchResult]:
    """Search Project Runeberg with automatic backend selection.
    
    Uses Google Custom Search API if GOOGLE_API_KEY and GOOGLE_CSE_ID are set,
    otherwise defaults to DuckDuckGo (zero-configuration).
    """
    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID")
    
    if google_api_key and google_cse_id:
        try:
            return search_google(query, google_api_key, google_cse_id, max_results=max_results)
        except Exception:
            return search_duckduckgo(query, max_results=max_results)
    
    return search_duckduckgo(query, max_results=max_results)
