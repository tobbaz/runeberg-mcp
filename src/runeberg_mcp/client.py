"""Client for fetching, reading, and searching within works on Project Runeberg."""

import difflib
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
import httpx

USER_AGENT = "runeberg-mcp/0.2.0 (+https://github.com/tobbaz/runeberg-mcp)"
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
    """Fetch and parse a single page from Project Runeberg, returning cleaned text and metadata."""
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
        text = a.get_text().replace(" ", " ").lower()
        if not prev_page and ("prev" in text or "föreg" in text):
            prev_page = a["href"]
        elif not next_page and ("next" in text or "nästa" in text):
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


def fetch_page_with_context(
    url_or_slug: str, page: Optional[Any] = None, context_pages: int = 0
) -> Dict[str, Any]:
    """Fetch a target page along with optional subsequent context pages (e.g. context_pages=1 for next page)."""
    base_data = fetch_page(url_or_slug, page)
    
    if context_pages <= 0 or not base_data.get("next_page"):
        return base_data

    combined_text = [base_data["text"]]
    current_data = base_data
    pages_read = 1

    base_dir = base_data["url"].rsplit("/", 1)[0]

    while pages_read <= context_pages and current_data.get("next_page"):
        next_ref = current_data["next_page"]
        if next_ref.startswith("http"):
            next_url = next_ref
        elif next_ref.startswith("/"):
            next_url = f"{BASE_URL}{next_ref}"
        else:
            next_url = f"{base_dir}/{next_ref}"
            
        try:
            next_data = fetch_page(next_url)
            combined_text.append(f"\n--- [Nästa sida: {next_data['title']}] ---\n")
            combined_text.append(next_data["text"])
            current_data = next_data
            pages_read += 1
        except Exception:
            break

    result = dict(base_data)
    result["text"] = "\n".join(combined_text)
    result["total_pages_read"] = pages_read
    return result


def fetch_work_info(work_slug: str) -> Dict[str, Any]:
    """Fetch metadata, chapter links, and alphabetic lemma headings for a work from Project Runeberg."""
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
    
    meta: Dict[str, str] = {}
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property")
        content = tag.get("content")
        if name and content:
            meta[name.lower()] = content.strip()
            
    chapters: List[Dict[str, str]] = []
    chapters_by_href: Dict[str, Dict[str, str]] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.endswith(".html") and not href.startswith(("http", "/", "mailto:")) and not href.startswith("index"):
            label = a.get_text().strip()
            if ">>" in label or "<<" in label:
                continue
                
            prev = a.previous_sibling
            heading = ""
            if prev and isinstance(prev, str):
                clean_prev = prev.replace("\xa0", " ").strip().rstrip("-. ").strip()
                if clean_prev and re.match(r"^[A-Za-zÅÄÖåäö]", clean_prev):
                    heading = clean_prev

            if href not in chapters_by_href:
                full_page_url = f"{BASE_URL}/{slug}/{href}"
                item = {
                    "title": heading if heading else (label or href),
                    "page_label": label,
                    "heading": heading,
                    "filename": href,
                    "url": full_page_url
                }
                chapters_by_href[href] = item
                chapters.append(item)
            else:
                if heading and not chapters_by_href[href].get("heading"):
                    chapters_by_href[href]["heading"] = heading
                    chapters_by_href[href]["title"] = heading
                
    result = {
        "slug": slug,
        "url": url,
        "title": meta.get("dc.title", title),
        "author": meta.get("dc.creator", meta.get("dc.publisher")),
        "date": meta.get("dc.date"),
        "language": meta.get("dc.language", "sv"),
        "chapters_count": len(chapters),
        "chapters": chapters,
    }
    _WORK_CACHE[url] = result
    return result


def search_in_work(work_slug: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Scan and fuzzy-search within a specific work or encyclopedia on Project Runeberg.
    
    If the work is an alphabetical encyclopedia or dictionary (like karlxiioff, sbh, anrep, rosenberg),
    it uses lemma bisection to instantly jump to the exact candidate pages, then performs deep
    fuzzy matching on the text.
    """
    work = fetch_work_info(work_slug)
    chapters = work.get("chapters", [])
    if not chapters:
        return []

    query_clean = query.strip()
    query_lower = query_clean.lower()

    # Identify if work contains alphabetic lemma headings
    alpha_headings = [c for c in chapters if c.get("heading")]
    candidate_chapters: List[Dict[str, str]] = []

    if len(alpha_headings) >= 10:
        # Alphabetical encyclopedia bisection!
        # Sort headings by alphabetic order
        sorted_alphas = sorted(alpha_headings, key=lambda c: c["heading"].lower())
        
        # Find the latest heading <= query_lower
        candidates = [c for c in sorted_alphas if c["heading"].lower() <= query_lower]
        if candidates:
            match_idx = sorted_alphas.index(candidates[-1])
            # Inspect the page itself and the next 2 adjacent pages
            for i in range(max(0, match_idx - 1), min(len(sorted_alphas), match_idx + 3)):
                candidate_chapters.append(sorted_alphas[i])
        else:
            candidate_chapters = sorted_alphas[:3]
    else:
        # Standard chapter scan: look for query prefix or text in chapter titles
        prefix = query_lower[:3] if len(query_lower) >= 3 else query_lower
        for ch in chapters:
            ch_title = ch["title"].lower()
            if prefix in ch_title or query_lower in ch_title:
                candidate_chapters.append(ch)
        if not candidate_chapters:
            candidate_chapters = chapters[:15]

    matches: List[Dict[str, Any]] = []

    for ch in candidate_chapters[:8]:
        try:
            page_data = fetch_page(ch["url"])
            text = page_data["text"]
            text_lower = text.lower()
            
            # 1. Exact match
            if query_lower in text_lower:
                for line in text.splitlines():
                    if query_lower in line.lower():
                        matches.append({
                            "title": page_data["title"],
                            "url": page_data["url"],
                            "matched_word": query_clean,
                            "matched_line": line.strip(),
                            "score": 1.0,
                        })
                        break
            else:
                # 2. Fuzzy match against words on page
                words = re.findall(r"\b[A-Za-zåäöÅÄÖ\-]+\b", text)
                best_score = 0.0
                best_word = ""
                best_line = ""
                
                for line in text.splitlines():
                    line_words = re.findall(r"\b[A-Za-zåäöÅÄÖ\-]+\b", line)
                    for w in line_words:
                        if abs(len(w) - len(query_clean)) <= 3 and len(w) >= 4:
                            ratio = difflib.SequenceMatcher(None, query_lower, w.lower()).ratio()
                            if ratio > best_score:
                                best_score = ratio
                                best_word = w
                                best_line = line
                                
                if best_score >= 0.78:
                    matches.append({
                        "title": page_data["title"],
                        "url": page_data["url"],
                        "matched_word": best_word,
                        "matched_line": best_line.strip(),
                        "score": round(best_score, 3),
                    })
        except Exception:
            continue

    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches[:max_results]
