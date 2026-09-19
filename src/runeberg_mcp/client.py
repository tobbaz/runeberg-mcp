"""Client for fetching and parsing pages and works from Project Runeberg."""

import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
import httpx

USER_AGENT = "runeberg-mcp/0.1.0 (+https://github.com/tobbaz/runeberg-mcp)"
BASE_URL = "https://runeberg.org"

# Simple in-memory cache to avoid duplicate HTTP requests
_PAGE_CACHE: Dict[str, Dict[str, Any]] = {}
_WORK_CACHE: Dict[str, Dict[str, Any]] = {}


def normalize_page_url(url_or_slug: str, page: Optional[Any] = None) -> str:
    """Normalize user input to a canonical runeberg.org page URL."""
    url = url_or_slug.strip()
    
    if url.startswith("http://") or url.startswith("https://"):
        return url
    
    # Handle slug + page argument, e.g. ("dasakungen", 5) or ("dasakungen", "0057")
    if page is not None:
        slug = url.strip("/")
        if isinstance(page, int):
            page_str = f"{page:04d}"
        else:
            page_str = str(page).strip()
            if page_str.isdigit() and len(page_str) < 4:
                page_str = page_str.zfill(4)
        if not page_str.endswith(".html"):
            page_str += ".html"
        return f"{BASE_URL}/{slug}/{page_str}"
    
    # Handle inputs like "dasakungen/0005" or "dasakungen/0005.html"
    parts = url.strip("/").split("/")
    if len(parts) == 2:
        slug, page_part = parts
        if page_part.isdigit() and len(page_part) < 4:
            page_part = page_part.zfill(4)
        if not page_part.endswith(".html"):
            page_part += ".html"
        return f"{BASE_URL}/{slug}/{page_part}"
    
    # Otherwise treat as base work directory or page
    if not url.endswith(".html") and not url.endswith("/"):
        url += "/"
    return f"{BASE_URL}/{url.lstrip('/')}"


def fetch_page(url_or_slug: str, page: Optional[Any] = None) -> Dict[str, Any]:
    """Fetch and parse a page from Project Runeberg, returning cleaned text and metadata."""
    url = normalize_page_url(url_or_slug, page)
    
    if url in _PAGE_CACHE:
        return _PAGE_CACHE[url]
    
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text
    
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text().strip() if soup.title else ""
    
    # Extract prev/next navigation if available
    prev_page = None
    next_page = None
    for a in soup.find_all("a", href=True):
        text = a.get_text()
        if "prev. page" in text or "föreg. sida" in text:
            prev_page = a["href"]
        elif "next page" in text or "nästa sida" in text:
            next_page = a["href"]
            
    # Scanned facsimile image link if available
    image_url = None
    for a in soup.find_all("a", href=True):
        if "Full resolution" in a.get_text() or "/img/" in a["href"]:
            href = a["href"]
            if href.startswith("/"):
                image_url = f"{BASE_URL}{href}"
            elif href.startswith("http"):
                image_url = href
            break
            
    # Extract main OCR/transcribed text
    cleaned_text = ""
    if "<!-- mode=normal -->" in html:
        text_part = html.split("<!-- mode=normal -->", 1)[1]
        # Trim footer starting with navigation links or graybox
        footer_match = re.search(
            r'<p align=[\"\']?center[\"\']?|<div class=[\"\']?graybox[\"\']?|<table|<hr\s*noshade',
            text_part,
            re.IGNORECASE,
        )
        if footer_match:
            text_part = text_part[:footer_match.start()]
            
        text_soup = BeautifulSoup(text_part, "html.parser")
        for tag in text_soup.find_all(["form", "table", "script", "style"]):
            tag.decompose()
        lines = [line.strip() for line in text_soup.get_text().splitlines() if line.strip()]
        cleaned_text = "\n".join(lines)
    else:
        # Fallback extraction: remove headers, footers, forms and extract body text
        for tag in soup.find_all(["form", "table", "script", "style", "div"]):
            if tag.get("class") and "graybox" in tag["class"]:
                tag.decompose()
        body = soup.find("body")
        if body:
            lines = [line.strip() for line in body.get_text().splitlines() if line.strip()]
            cleaned_text = "\n".join(lines)
            
    result = {
        "url": url,
        "title": title,
        "text": cleaned_text,
        "image_url": image_url,
        "prev_page": prev_page,
        "next_page": next_page,
    }
    _PAGE_CACHE[url] = result
    return result


def fetch_work_info(work_slug: str) -> Dict[str, Any]:
    """Fetch metadata and chapter links for a work from Project Runeberg."""
    slug = work_slug.strip("/").split("/")[-1]
    url = f"{BASE_URL}/{slug}/"
    
    if url in _WORK_CACHE:
        return _WORK_CACHE[url]
        
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        html = resp.text
        
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text().strip() if soup.title else slug
    
    # Extract Dublin Core metadata
    meta: Dict[str, str] = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property")
        content = tag.get("content")
        if name and content:
            meta[name.lower()] = content.strip()
            
    # Collect page and chapter links
    chapters: List[Dict[str, str]] = []
    seen_hrefs = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".html") and not href.startswith(("http", "/", "mailto:")) and not href.startswith("index"):
            chapter_title = a.get_text().strip()
            if ">>" in chapter_title or "<<" in chapter_title:
                continue
            if href not in seen_hrefs:
                seen_hrefs.add(href)
                chapter_title = a.get_text().strip()
                full_page_url = f"{BASE_URL}/{slug}/{href}"
                chapters.append({
                    "title": chapter_title or href,
                    "filename": href,
                    "url": full_page_url
                })
                
    result = {
        "slug": slug,
        "url": url,
        "title": meta.get("dc.title", title),
        "author": meta.get("dc.creator", meta.get("dc.publisher")),
        "date": meta.get("dc.date"),
        "language": meta.get("dc.language", "sv"),
        "chapters_count": len(chapters),
        "chapters": chapters[:50],
    }
    _WORK_CACHE[url] = result
    return result
