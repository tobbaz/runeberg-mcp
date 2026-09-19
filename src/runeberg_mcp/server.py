"""MCP server for Project Runeberg."""

import logging
from typing import Optional

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP  # type: ignore

from runeberg_mcp.search import search
from runeberg_mcp.client import fetch_page, fetch_work_info

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("runeberg-mcp")

mcp = FastMCP(
    name="runeberg-mcp",
    instructions="""
Du är en forskningsassistent med tillgång till Projekt Runeberg (runeberg.org), 
det största digitala arkivet för fri äldre nordisk litteratur, fackböcker, 
biografier och historiska lexikon (såsom Nordisk familjebok, Svenskt biografiskt 
handlexikon, Salmonsens konversationsleksikon, m.fl.).

Verktyg som finns tillgängliga:
- `runeberg_search`: Fritextsökning i böckernas text på runeberg.org.
- `runeberg_read_page`: Läser och returnerar hela texten för en specifik boksida.
- `runeberg_get_work_info`: Hämtar metadata, författare och kapitelöversikt för ett specifikt verk.

Använd dessa verktyg för att söka efter historiska personer, händelser, gårdar,
släkter, äldre terminologi och citat i klassiska verk.
"""
)


@mcp.tool()
def runeberg_search(query: str, max_results: int = 10) -> str:
    """Full-text search across digitized books, encyclopedias, and literature in Project Runeberg (runeberg.org).
    
    Args:
        query: Search keywords or phrases (e.g. "Abraham Brodersson", "Dödsdansen", or "Falun gruva").
        max_results: Maximum number of search results to return (default: 10).
    """
    try:
        results = search(query, max_results=max_results)
        if not results:
            return f"Inga träffar hittades på Projekt Runeberg för sökfrågan: '{query}'."
        
        output = [f"Funna träffar på Projekt Runeberg ({len(results)} st):\n"]
        for i, r in enumerate(results, 1):
            output.append(f"{i}. **{r.title}**")
            output.append(f"   URL: {r.url}")
            if r.work_slug:
                page_info = f" (Sida: {r.page})" if r.page else ""
                output.append(f"   Verks-ID: `{r.work_slug}`{page_info}")
            if r.snippet:
                output.append(f"   Utdrag: {r.snippet}")
            output.append("")
        return "\n".join(output)
    except Exception as e:
        return f"Fel vid sökning på Projekt Runeberg: {str(e)}"


@mcp.tool()
def runeberg_read_page(url_or_slug: str, page: Optional[str] = None) -> str:
    """Read the cleaned, transcribed/OCR text of a specific book page from Project Runeberg.
    
    Args:
        url_or_slug: Full page URL (e.g. 'https://runeberg.org/pvmhall/0105.html') or work slug (e.g. 'pvmhall').
        page: Optional page number if slug was provided (e.g. '0105' or 105).
    """
    try:
        data = fetch_page(url_or_slug, page)
        output = [
            f"# {data['title']}",
            f"Källa: {data['url']}",
        ]
        if data.get("image_url"):
            output.append(f"Faksimilbild: {data['image_url']}")
        if data.get("prev_page") or data.get("next_page"):
            nav = []
            if data.get("prev_page"):
                nav.append(f"Föregående sida: {data['prev_page']}")
            if data.get("next_page"):
                nav.append(f"Nästa sida: {data['next_page']}")
            output.append(" | ".join(nav))
            
        output.append("\n---\n")
        output.append(data["text"] if data["text"] else "(Ingen text hittades på denna sida.)")
        return "\n".join(output)
    except Exception as e:
        return f"Fel vid hämtning av sidan: {str(e)}"


@mcp.tool()
def runeberg_get_work_info(work_slug: str) -> str:
    """Get metadata, publication details, and table of contents/chapter list for a work in Project Runeberg.
    
    Args:
        work_slug: The work identifier (e.g. 'dasakungen', 'sbh', 'nfda', 'salmonsen').
    """
    try:
        info = fetch_work_info(work_slug)
        output = [
            f"# {info['title']}",
            f"Verks-ID: `{info['slug']}`",
            f"URL: {info['url']}",
        ]
        if info.get("author"):
            output.append(f"Författare/Utgivare: {info['author']}")
        if info.get("date"):
            output.append(f"Publiceringsår: {info['date']}")
        if info.get("language"):
            output.append(f"Språk: {info['language']}")
            
        chapters = info.get("chapters", [])
        if chapters:
            output.append(f"\nKapitel/Sidor ({info.get('chapters_count', len(chapters))} tillgängliga):")
            for ch in chapters[:20]:
                output.append(f"- [{ch['title']}]({ch['url']}) (`{ch['filename']}`)")
            if len(chapters) > 20:
                output.append(f"... och ytterligare {len(chapters) - 20} sidor.")
        return "\n".join(output)
    except Exception as e:
        return f"Fel vid hämtning av verksinfo för `{work_slug}`: {str(e)}"


def run():
    """Run the MCP server via stdio transport."""
    logger.info("Starting Runeberg MCP Server...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
