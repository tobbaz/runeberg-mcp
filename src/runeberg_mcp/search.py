"""Search backends and historical name/place variant generator for Project Runeberg."""

from dataclasses import dataclass
import os
import re
from typing import Dict, List, Optional, Set
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
    matched_term: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "work_slug": self.work_slug,
            "page": self.page,
            "matched_term": self.matched_term,
        }


def _extract_slug_and_page(url: str) -> tuple[Optional[str], Optional[str]]:
    """Extract work slug and page filename from a runeberg.org URL."""
    m = re.match(r"^https?://(?:www\.)?runeberg\.org/([^/]+)(?:/(\d{4}|[^/]+)\.html)?", url)
    if m:
        slug = m.group(1)
        page = m.group(2)
        return slug, page
    return None, None


def generate_historical_variants(term: str) -> List[str]:
    """Generate common historical spelling variants for Swedish/German names and places.
    
    Covers common orthographic shifts across 16th-19th century documents:
    - German/Nordic place and noble suffixes (-hausen/-haussen/-husen, -borg/-borgh, -torp/-torff)
    - Noble name elements (-stierna/-stjerna, -hielm/-hjelm, -sköld/-skiöld)
    - Historical spelling transitions (c/k, f/v/fv/w, dt/t, ss/s, qv/kv)
    """
    variants: Set[str] = set()
    raw = term.strip()
    if not raw:
        return []

    # -ershausen <-> -erhaussen / -ershusen / -erhausen
    if re.search(r"ershausen$", raw, re.IGNORECASE):
        variants.add(re.sub(r"ershausen$", "haussen", raw, flags=re.IGNORECASE))
        variants.add(re.sub(r"ershausen$", "erhaussen", raw, flags=re.IGNORECASE))
        variants.add(re.sub(r"ershausen$", "erhausen", raw, flags=re.IGNORECASE))
    elif re.search(r"erhaussen$", raw, re.IGNORECASE):
        variants.add(re.sub(r"erhaussen$", "ershausen", raw, flags=re.IGNORECASE))
        variants.add(re.sub(r"erhaussen$", "erhausen", raw, flags=re.IGNORECASE))

    # -hausen <-> -haussen <-> -husen
    if re.search(r"hausen$", raw, re.IGNORECASE):
        variants.add(re.sub(r"hausen$", "haussen", raw, flags=re.IGNORECASE))
        variants.add(re.sub(r"hausen$", "husen", raw, flags=re.IGNORECASE))
    elif re.search(r"haussen$", raw, re.IGNORECASE):
        variants.add(re.sub(r"haussen$", "hausen", raw, flags=re.IGNORECASE))
        variants.add(re.sub(r"haussen$", "husen", raw, flags=re.IGNORECASE))
    elif re.search(r"husen$", raw, re.IGNORECASE):
        variants.add(re.sub(r"husen$", "hausen", raw, flags=re.IGNORECASE))
        variants.add(re.sub(r"husen$", "haussen", raw, flags=re.IGNORECASE))

    # -stierna <-> -stjerna
    if "stierna" in raw.lower():
        variants.add(re.sub(r"stierna", "stjerna", raw, flags=re.IGNORECASE))
    elif "stjerna" in raw.lower():
        variants.add(re.sub(r"stjerna", "stierna", raw, flags=re.IGNORECASE))

    # -hielm <-> -hjelm
    if "hielm" in raw.lower():
        variants.add(re.sub(r"hielm", "hjelm", raw, flags=re.IGNORECASE))
    elif "hjelm" in raw.lower():
        variants.add(re.sub(r"hjelm", "hielm", raw, flags=re.IGNORECASE))

    # -sköld <-> -skiöld
    if "sköld" in raw.lower():
        variants.add(re.sub(r"sköld", "skiöld", raw, flags=re.IGNORECASE))
    elif "skiöld" in raw.lower():
        variants.add(re.sub(r"skiöld", "sköld", raw, flags=re.IGNORECASE))

    # -torp <-> -torff <-> -dorp
    if re.search(r"torp$", raw, re.IGNORECASE):
        variants.add(re.sub(r"torp$", "torff", raw, flags=re.IGNORECASE))
        variants.add(re.sub(r"torp$", "dorp", raw, flags=re.IGNORECASE))
    elif re.search(r"torff$", raw, re.IGNORECASE):
        variants.add(re.sub(r"torff$", "torp", raw, flags=re.IGNORECASE))

    # -borg <-> -borgh
    if re.search(r"borg$", raw, re.IGNORECASE):
        variants.add(re.sub(r"borg$", "borgh", raw, flags=re.IGNORECASE))
    elif re.search(r"borgh$", raw, re.IGNORECASE):
        variants.add(re.sub(r"borgh$", "borg", raw, flags=re.IGNORECASE))

    # -berg <-> -bergh
    if re.search(r"berg$", raw, re.IGNORECASE):
        variants.add(re.sub(r"berg$", "bergh", raw, flags=re.IGNORECASE))
    elif re.search(r"bergh$", raw, re.IGNORECASE):
        variants.add(re.sub(r"bergh$", "berg", raw, flags=re.IGNORECASE))

    # -ström <-> -ströhm
    if re.search(r"ström$", raw, re.IGNORECASE):
        variants.add(re.sub(r"ström$", "ströhm", raw, flags=re.IGNORECASE))
    elif re.search(r"ströhm$", raw, re.IGNORECASE):
        variants.add(re.sub(r"ströhm$", "ström", raw, flags=re.IGNORECASE))

    # Carl <-> Karl, Fredric/Fredrik, Gustaf/Gustav
    if raw.startswith("Carl "):
        variants.add("Karl " + raw[5:])
    elif raw.startswith("Karl "):
        variants.add("Carl " + raw[5:])
    if "Fredrik" in raw:
        variants.add(raw.replace("Fredrik", "Fredric"))
    elif "Fredric" in raw:
        variants.add(raw.replace("Fredric", "Fredrik"))
    if "Gustav" in raw:
        variants.add(raw.replace("Gustav", "Gustaf"))
    elif "Gustaf" in raw:
        variants.add(raw.replace("Gustaf", "Gustav"))

    if "hülph" in raw.lower():
        variants.add(re.sub(r"hülph", "hilph", raw, flags=re.IGNORECASE))
    elif "hilph" in raw.lower():
        variants.add(re.sub(r"hilph", "hülph", raw, flags=re.IGNORECASE))

    variants.discard(raw)
    return list(variants)


def search_duckduckgo_term(query_term: str, max_results: int = 10) -> List[SearchResult]:
    """Execute a single query term against site:runeberg.org using DDGS."""
    full_query = f"{query_term} site:runeberg.org"
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
                    matched_term=query_term,
                )
            )
    return results


def search_google_term(query_term: str, api_key: str, cse_id: str, max_results: int = 10) -> List[SearchResult]:
    """Execute a single query term using the official Google Custom Search JSON API."""
    full_query = f"{query_term} site:runeberg.org"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": full_query,
        "num": min(max_results, 10),
    }
    
    headers = {
        "User-Agent": "runeberg-mcp/0.2.0 (+https://github.com/tobbaz/runeberg-mcp)"
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
                matched_term=query_term,
            )
        )
    return results


def search(
    query: str,
    variants: Optional[List[str]] = None,
    max_results: int = 10,
    auto_expand: bool = True
) -> List[SearchResult]:
    """Search Project Runeberg with support for multiple spelling variants and balanced deduplication."""
    terms_to_try: List[str] = [query.strip()]
    
    if variants:
        for v in variants:
            v_clean = v.strip()
            if v_clean and v_clean not in terms_to_try:
                terms_to_try.append(v_clean)
                
    if auto_expand:
        expanded = generate_historical_variants(query)
        for exp in expanded:
            if exp not in terms_to_try:
                terms_to_try.append(exp)

    google_api_key = os.environ.get("GOOGLE_API_KEY")
    google_cse_id = os.environ.get("GOOGLE_CSE_ID")
    use_google = bool(google_api_key and google_cse_id)

    seen_urls: Set[str] = set()
    aggregated_results: List[SearchResult] = []

    # Limit search per term to leave room for variants
    per_term = max(4, max_results // min(len(terms_to_try), 4)) if len(terms_to_try) > 1 else max_results

    for term in terms_to_try:
        try:
            if use_google:
                term_results = search_google_term(
                    term, google_api_key, google_cse_id, max_results=per_term  # type: ignore
                )
            else:
                term_results = search_duckduckgo_term(term, max_results=per_term)
        except Exception:
            if use_google:
                use_google = False
                try:
                    term_results = search_duckduckgo_term(term, max_results=per_term)
                except Exception:
                    term_results = []
            else:
                term_results = []

        for res in term_results:
            norm_url = res.url.split("?")[0].rstrip("/")
            if norm_url not in seen_urls:
                seen_urls.add(norm_url)
                aggregated_results.append(res)

        if len(aggregated_results) >= max_results:
            break

    return aggregated_results[:max_results]
