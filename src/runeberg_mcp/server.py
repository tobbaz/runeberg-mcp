"""MCP server for Project Runeberg with historical name, surname, and place search capabilities."""

import logging
from typing import List, Optional

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP  # type: ignore

from runeberg_mcp.search import search
from runeberg_mcp.client import fetch_page_with_context, fetch_work_info, search_in_work

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("runeberg-mcp")

mcp = FastMCP(
    name="runeberg-mcp",
    instructions="""
Du är en specialiserad forskningsassistent med tillgång till Projekt Runeberg (runeberg.org), 
det främsta digitala arkivet för fri äldre nordisk litteratur, källskrifter och lexikon.

Ditt primära fokus är historisk forskning kring:
1. PERSONER & SLÄKTER (t.ex. officerare, präster, adelsätter, borgare, bönder, hantverkare).
2. PLATSER & TOPOGRAFI (t.ex. gårdar, byar, säterier, socknar, härader, slott, städer och bruk).

Viktiga referensverk på Runeberg som du kan söka i eller hänvisa till:
- 'karlxiioff': Adam Lewenhaupts "Karl XII:s officerare. Biografiska anteckningar" (alla officerare under Stora nordiska kriget).
- 'sbh': "Svenskt biografiskt handlexikon" (Hofberg m.fl., tusentals historiska personbiografier).
- 'anrep': Gabriel Anreps "Svenska adelns ättar-taflor" (stamtavlor för alla introducerade ätter).
- 'rosenberg': C.M. Rosenbergs "Geografiskt-statistiskt handlexikon öfver Sverige" (uppslagsverk för ALLA svenska byar, gårdar, socknar och socknar under 1880-talet).
- 'hgsl': "Historiskt-geografiskt och statistiskt lexikon öfver Sverige" (utförliga historiska gårds- och godshistoriker).
- 'nf', 'nfa', 'nfb', 'nfc', 'nfda': "Nordisk familjebok" (det stora svenska uppslagsverket, alla upplagor).

Strategier för historisk sökning:
- Stavningen i äldre källor varierar ofta (t.ex. 'Carl/Karl', '-hausen/-haussen/-husen', '-stierna/-stjerna', '-torp/-torff').
- Använd parametern `variants` i `runeberg_search` för att skicka med historiska stavningsvarianter som du känner till.
- Vid läsning av biografier eller gårdsbeskrivningar som bryts vid sidbyten, använd `context_pages=1` i `runeberg_read_page` för att få med nästa sida.
"""
)


@mcp.tool()
def runeberg_search(
    query: str,
    variants: Optional[List[str]] = None,
    max_results: int = 10
) -> str:
    """Search across all digitized books, encyclopedias, and documents on Project Runeberg.
    
    Supports searching for historical people, surnames, places, farms, and terms.
    Automatically handles common historical spelling shifts, and you can provide additional
    expected spelling variants via the `variants` parameter.
    
    Args:
        query: Main search query (e.g. 'Hilpershausen', 'Piiksborg', 'Carl von Linné', 'Långtora').
        variants: Optional list of additional historical spelling variants to search simultaneously 
                  (e.g. ['Hilperhaussen', 'Hilpershusen']).
        max_results: Maximum total deduplicated results to return (default: 10).
    """
    try:
        results = search(query, variants=variants, max_results=max_results)
        if not results:
            msg = f"Inga träffar hittades på Projekt Runeberg för: '{query}'."
            if variants:
                msg += f" (Provade även varianterna: {', '.join(variants)})"
            return msg
        
        output = [f"Funna träffar på Projekt Runeberg ({len(results)} st):\n"]
        for i, r in enumerate(results, 1):
            output.append(f"{i}. **{r.title}**")
            output.append(f"   URL: {r.url}")
            if r.work_slug:
                page_info = f" (Sida: {r.page})" if r.page else ""
                output.append(f"   Verks-ID: `{r.work_slug}`{page_info}")
            if r.matched_term and r.matched_term.lower() != query.lower():
                output.append(f"   Träff via variant: *{r.matched_term}*")
            if r.snippet:
                output.append(f"   Utdrag: {r.snippet}")
            output.append("")
        return "\n".join(output)
    except Exception as e:
        return f"Fel vid sökning på Projekt Runeberg: {str(e)}"


@mcp.tool()
def runeberg_read_page(
    url_or_slug: str,
    page: Optional[str] = None,
    context_pages: int = 0
) -> str:
    """Read the cleaned, transcribed/OCR text of a specific book page from Project Runeberg.
    
    Optionally retrieves subsequent pages to seamlessly read biographies or entries that
    span across page breaks.
    
    Args:
        url_or_slug: Full page URL (e.g. 'https://runeberg.org/karlxiioff/0311.html') or work slug (e.g. 'karlxiioff').
        page: Optional page number/filename if slug was provided (e.g. '0311' or 311).
        context_pages: Number of additional subsequent pages to read (e.g. 1 to read this page and the next).
    """
    try:
        data = fetch_page_with_context(url_or_slug, page, context_pages=context_pages)
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
        if data.get("total_pages_read", 1) > 1:
            output.append(f"(Läste {data['total_pages_read']} sammanhängande sidor)")
            
        output.append("\n---\n")
        output.append(data["text"] if data["text"] else "(Ingen text hittades på denna sida.)")
        return "\n".join(output)
    except Exception as e:
        return f"Fel vid hämtning av sidan: {str(e)}"


@mcp.tool()
def runeberg_search_in_work(
    work_slug: str,
    query: str,
    max_results: int = 5
) -> str:
    """Fuzzy-search for a person, surname, or place within a specific work or encyclopedia on Project Runeberg.
    
    Ideal for targeted lookups in biographical or topographical reference works such as:
    - 'karlxiioff' (Karl XII:s officerare)
    - 'sbh' (Svenskt biografiskt handlexikon)
    - 'anrep' (Svenska adelns ättartaflor)
    - 'rosenberg' (Geografiskt-statistiskt handlexikon öfver Sverige)
    - 'hgsl' (Historiskt-geografiskt lexikon)
    
    Args:
        work_slug: Identifier for the work (e.g. 'karlxiioff', 'sbh', 'anrep/1').
        query: Person name, surname, or place to find (e.g. 'Hilperhaussen' or 'Ekenstjerna').
        max_results: Maximum matching pages to return (default: 5).
    """
    try:
        matches = search_in_work(work_slug, query, max_results=max_results)
        if not matches:
            return f"Inga träffar hittades för '{query}' i verket `{work_slug}`."
            
        output = [f"Fuzzy-träffar för '{query}' i `{work_slug}` ({len(matches)} st):\n"]
        for i, m in enumerate(matches, 1):
            score_pct = int(m.get("score", 1.0) * 100)
            output.append(f"{i}. **{m['title']}** (Likhet: {score_pct}%)")
            output.append(f"   URL: {m['url']}")
            if m.get("matched_word"):
                output.append(f"   Matchat ord: *{m['matched_word']}*")
            if m.get("matched_line"):
                output.append(f"   Kontext: {m['matched_line'].strip()}")
            output.append("")
        return "\n".join(output)
    except Exception as e:
        return f"Fel vid sökning i verket `{work_slug}`: {str(e)}"


@mcp.tool()
def runeberg_get_work_info(work_slug: str) -> str:
    """Get metadata, publication details, and table of contents/chapter list for a work in Project Runeberg.
    
    Args:
        work_slug: The work identifier (e.g. 'dasakungen', 'sbh', 'karlxiioff', 'rosenberg').
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
            output.append(f"\nTillgängliga kapitel/sidor ({info.get('chapters_count', len(chapters))} st):")
            for ch in chapters[:25]:
                output.append(f"- [{ch['title']}]({ch['url']}) (`{ch['filename']}`)")
            if len(chapters) > 25:
                output.append(f"... och ytterligare {len(chapters) - 25} sidor.")
        return "\n".join(output)
    except Exception as e:
        return f"Fel vid hämtning av verksinfo för `{work_slug}`: {str(e)}"


def run():
    """Run the MCP server via stdio transport."""
    logger.info("Starting Runeberg MCP Server v0.2.0...")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run()
