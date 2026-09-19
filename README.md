# Runeberg MCP 📖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-purple.svg)](https://modelcontextprotocol.io/)

A Model Context Protocol (MCP) server and CLI tool for researching historical people, noble families, and places across digitized Nordic literature, encyclopedias, and archives on [Projekt Runeberg](https://runeberg.org).

Project Runeberg has been publishing free electronic editions of classic Nordic literature out of copyright since 1992. It is a treasure trove for genealogy and local history, containing monumental works like:
- **`karlxiioff`**: *Karl XII:s officerare. Biografiska anteckningar* (Adam Lewenhaupt)
- **`sbh`**: *Svenskt biografiskt handlexikon* (Hofberg et al.)
- **`anrep`** / **`elgenst`**: *Svenska adelns ättar-taflor* (Gabriel Anrep / Gustaf Elgenstierna)
- **`rosenberg`**: *Geografiskt-statistiskt handlexikon öfver Sverige* (C.M. Rosenberg – all Swedish villages, farms, and parishes)
- **`hgsl`**: *Historiskt-geografiskt och statistiskt lexikon öfver Sverige*
- **`nf`**: *Nordisk familjebok* (all editions)

---

## ✨ Features

- **🔎 Smart Global Search (`runeberg_search`):** Full-text search across all digitized works with automatic historical spelling expansion and support for caller/LLM-provided spelling variants (`variants`).
- **🎯 In-Work Lemma Bisection & Fuzzy Search (`runeberg_search_in_work`):** Instantly locates candidate pages in alphabetical encyclopedias (e.g. searching for *Hilpershausen* finds *Hilperhaussen* on page 297 of *Karl XII:s officerare* with 92% similarity).
- **📄 Page Reader with Context Window (`runeberg_read_page`):** Extracts clean OCR/proofread text with links to original facsimile images. Supports `context_pages` to read across page breaks seamlessly.
- **📚 Work & Chapter Inspector (`runeberg_get_work_info`):** Retrieves metadata, publication details, and full chapter/lemma index.
- **⚡ Zero-Config by Default:** Built-in multi-engine search (`ddgs`) requiring no API keys or setup.
- **🚀 Optional Google Custom Search API:** Set `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` to use Google's official API.

---

## 🛠️ Installation

Managed with modern Python packaging via [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/tobbaz/runeberg-mcp.git
cd runeberg-mcp
uv sync
```

---

## 🤖 MCP Server Configuration

Add to your MCP client configuration (`claude_desktop_config.json`, Cursor, Antigravity, etc.):

```json
{
  "mcpServers": {
    "runeberg": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/runeberg-mcp",
        "run",
        "runeberg-mcp",
        "serve"
      ]
    }
  }
}
```

---

## 💻 CLI Usage

Test and research directly in your terminal:

### 1. Global Search (with automatic historical variants):
```bash
# Finds hits across all of Runeberg, automatically testing historical spelling shifts
uv run runeberg-mcp search "Hilpershausen"

# Or provide your own historical variants:
uv run runeberg-mcp search "Hilpershausen" -v "Hilperhaussen" -v "Hilpershusen"
```

### 2. Targeted In-Work Fuzzy Search:
```bash
# Search within Karl XII:s officerare:
uv run runeberg-mcp in-work karlxiioff "Hilpershausen"

# Search within Svenskt biografiskt handlexikon:
uv run runeberg-mcp in-work sbh "Bellman"

# Search for a farm or village in Rosenberg:
uv run runeberg-mcp in-work rosenberg "Långtora"
```

### 3. Read Page (with optional context window):
```bash
# Read a single page:
uv run runeberg-mcp read dasakungen 5

# Read a page and the subsequent page across page breaks:
uv run runeberg-mcp read https://runeberg.org/karlxiioff/0311.html -c 1
```

### 4. Inspect Work:
```bash
uv run runeberg-mcp info karlxiioff
```

---

## 🧪 Running Tests

Run the test suite:

```bash
uv run python test_server.py
```

---

## 📜 License

Distributed under the [MIT License](LICENSE). Digital works hosted on Projekt Runeberg are public domain cultural heritage.
