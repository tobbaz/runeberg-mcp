"""Command-line interface for runeberg-mcp."""

import argparse
from runeberg_mcp.search import search
from runeberg_mcp.client import fetch_page_with_context, fetch_work_info, search_in_work
from runeberg_mcp.server import run as run_server


def main():
    parser = argparse.ArgumentParser(
        prog="runeberg-mcp",
        description="Search and read digitized Nordic literature, people, and places from Project Runeberg (runeberg.org)."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # search command
    search_parser = subparsers.add_parser("search", help="Full-text search in Project Runeberg")
    search_parser.add_argument("query", type=str, help="Search terms")
    search_parser.add_argument("-v", "--variant", action="append", default=[], help="Additional spelling variants")
    search_parser.add_argument("-n", "--num", type=int, default=10, help="Max results (default: 10)")
    search_parser.add_argument("--no-expand", action="store_true", help="Disable automatic historical variant expansion")

    # read command
    read_parser = subparsers.add_parser("read", help="Read a page from a work")
    read_parser.add_argument("target", type=str, help="Page URL (or work slug)")
    read_parser.add_argument("page", nargs="?", default=None, help="Page number or filename (if target is slug)")
    read_parser.add_argument("-c", "--context", type=int, default=0, help="Number of subsequent context pages to read")

    # in-work command
    in_work_parser = subparsers.add_parser("in-work", help="Fuzzy-search within a specific work (e.g. karlxiioff, sbh, anrep)")
    in_work_parser.add_argument("slug", type=str, help="Work slug")
    in_work_parser.add_argument("query", type=str, help="Name or term to search for")
    in_work_parser.add_argument("-n", "--num", type=int, default=5, help="Max matches (default: 5)")

    # info command
    info_parser = subparsers.add_parser("info", help="Get information and table of contents for a work")
    info_parser.add_argument("slug", type=str, help="Work slug (e.g. 'dasakungen', 'karlxiioff')")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the MCP server on stdio")

    args = parser.parse_args()

    if args.command == "search":
        variants = args.variant if args.variant else None
        print(f"Söker efter '{args.query}' på Projekt Runeberg...")
        if variants:
            print(f"Med angivna varianter: {', '.join(variants)}")
        print()
        results = search(args.query, variants=variants, max_results=args.num, auto_expand=not args.no_expand)
        if not results:
            print("Inga träffar hittades.")
            return
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.title}")
            print(f"   URL:  {r.url}")
            if r.work_slug:
                p_str = f", sida {r.page}" if r.page else ""
                print(f"   Verk: {r.work_slug}{p_str}")
            if r.matched_term and r.matched_term.lower() != args.query.lower():
                print(f"   Variant: *{r.matched_term}*")
            if r.snippet:
                print(f"   Utdrag: {r.snippet}")
            print()

    elif args.command == "read":
        data = fetch_page_with_context(args.target, args.page, context_pages=args.context)
        print("=" * 60)
        print(f"{data['title']}")
        print(f"Källa: {data['url']}")
        if data.get("image_url"):
            print(f"Faksimil: {data['image_url']}")
        if data.get("total_pages_read", 1) > 1:
            print(f"(Läste {data['total_pages_read']} sammanhängande sidor)")
        print("=" * 60)
        print()
        print(data["text"])

    elif args.command == "in-work":
        print(f"Söker efter '{args.query}' i verket '{args.slug}'...\n")
        matches = search_in_work(args.slug, args.query, max_results=args.num)
        if not matches:
            print("Inga träffar hittades.")
            return
        for i, m in enumerate(matches, 1):
            score_pct = int(m.get("score", 1.0) * 100)
            print(f"{i}. {m['title']} (Likhet: {score_pct}%)")
            print(f"   URL:  {m['url']}")
            if m.get("matched_word"):
                print(f"   Match: *{m['matched_word']}*")
            if m.get("matched_line"):
                print(f"   Rad:   {m['matched_line'].strip()}")
            print()

    elif args.command == "info":
        info = fetch_work_info(args.slug)
        print("=" * 60)
        print(f"Titel:   {info['title']}")
        print(f"Verk-ID: {info['slug']}")
        print(f"URL:     {info['url']}")
        if info.get("author"):
            print(f"Skapare: {info['author']}")
        if info.get("date"):
            print(f"År:      {info['date']}")
        print("=" * 60)
        chapters = info.get("chapters", [])
        if chapters:
            print(f"\nTillgängliga sidor/kapitel ({len(chapters)} st):")
            for ch in chapters[:25]:
                print(f" - {ch['title']} ({ch['filename']}) -> {ch['url']}")
            if len(chapters) > 25:
                print(f" ... och ytterligare {len(chapters) - 25} sidor.")

    elif args.command == "serve":
        run_server()

    else:
        run_server()


if __name__ == "__main__":
    main()
