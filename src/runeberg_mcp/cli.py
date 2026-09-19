"""Command-line interface for runeberg-mcp."""

import argparse
import sys
from runeberg_mcp.search import search
from runeberg_mcp.client import fetch_page, fetch_work_info
from runeberg_mcp.server import run as run_server


def main():
    parser = argparse.ArgumentParser(
        prog="runeberg-mcp",
        description="Search and read digitized Nordic literature from Project Runeberg (runeberg.org)."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # search command
    search_parser = subparsers.add_parser("search", help="Full-text search in Project Runeberg")
    search_parser.add_argument("query", type=str, help="Search terms")
    search_parser.add_argument("-n", "--num", type=int, default=10, help="Max results (default: 10)")

    # read command
    read_parser = subparsers.add_parser("read", help="Read a page from a work")
    read_parser.add_argument("target", type=str, help="Page URL (or work slug)")
    read_parser.add_argument("page", nargs="?", default=None, help="Page number or filename (if target is slug)")

    # info command
    info_parser = subparsers.add_parser("info", help="Get information and table of contents for a work")
    info_parser.add_argument("slug", type=str, help="Work slug (e.g. 'dasakungen')")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the MCP server on stdio")

    args = parser.parse_args()

    if args.command == "search":
        print(f"Söker efter '{args.query}' på Projekt Runeberg...\n")
        results = search(args.query, max_results=args.num)
        if not results:
            print("Inga träffar hittades.")
            return
        for i, r in enumerate(results, 1):
            print(f"{i}. {r.title}")
            print(f"   URL:  {r.url}")
            if r.work_slug:
                p_str = f", sida {r.page}" if r.page else ""
                print(f"   Verk: {r.work_slug}{p_str}")
            if r.snippet:
                print(f"   Utdrag: {r.snippet}")
            print()

    elif args.command == "read":
        data = fetch_page(args.target, args.page)
        print("=" * 60)
        print(f"{data['title']}")
        print(f"Källa: {data['url']}")
        if data.get("image_url"):
            print(f"Faksimil: {data['image_url']}")
        print("=" * 60)
        print()
        print(data["text"])

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
        # Default to running the MCP server when run without arguments (e.g. from an MCP host)
        run_server()


if __name__ == "__main__":
    main()
