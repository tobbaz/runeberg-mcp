# Runeberg MCP 📖

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Protocol-purple.svg)](https://modelcontextprotocol.io/)

A Model Context Protocol (MCP) server and CLI tool for searching and reading digitized classic Nordic literature, historical encyclopedias, biographies, and source documents from [Projekt Runeberg](https://runeberg.org).

Project Runeberg has been publishing free electronic editions of classic Nordic literature out of copyright since 1992. It includes vast cultural treasures such as *Nordisk familjebok*, *Svenskt biografiskt handlexikon*, *Salmonsens konversationsleksikon*, parish histories, memoirs, drama, and poetry.

---

## ✨ Features

- **🔎 Full-Text Search (`runeberg_search`):** Search the actual text of millions of scanned book pages across Projekt Runeberg.
- **📄 Clean Page Reading (`runeberg_read_page`):** Extract and format the transcribed/OCR text for any page, stripped of web markup and navigation. Includes links to original facsimile scans.
- **📚 Work & Chapter Inspector (`runeberg_get_work_info`):** Retrieve metadata, authors, publication years, and tables of contents/chapter links for any digitized volume.
- **⚡ Zero-Config by Default:** Works out-of-the-box using privacy-respecting search backends (DuckDuckGo/multi-engine) without requiring any API keys.
- **🚀 Optional Google Custom Search API:** Supports official Google Custom Search JSON API for high-volume or specialized setups.
- **🛠️ Dual-mode CLI & MCP:** Use directly in your terminal as a CLI or seamlessly integrate with LLM agents (Claude Desktop, Cursor, Antigravity, etc.).

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

To connect this MCP server to your AI assistant, add it to your client's configuration file.

### 1. Claude Desktop (`claude_desktop_config.json`)

On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`  
On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

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

### 2. Cursor / Antigravity / Other MCP Clients

Configure as a `stdio` MCP server with:
* **Command:** `uv`
* **Args:** `["--directory", "/path/to/runeberg-mcp", "run", "runeberg-mcp", "serve"]`

---

## 🔧 Search Engine Options

### Default: Zero-Config (No API keys needed)
By default, searches against `site:runeberg.org` run via multi-engine fallback (`ddgs`), requiring **no API keys or signups**.

### Optional: Google Custom Search JSON API
If you prefer to query Google's official Custom Search API:
1. Create an API key in the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a [Programmable Search Engine](https://programmablesearchengine.google.com/) configured to search `runeberg.org/*`.
3. Set the environment variables in your client configuration:

```json
{
  "mcpServers": {
    "runeberg": {
      "command": "uv",
      "args": ["--directory", "/path/to/runeberg-mcp", "run", "runeberg-mcp", "serve"],
      "env": {
        "GOOGLE_API_KEY": "your-google-api-key",
        "GOOGLE_CSE_ID": "your-custom-search-engine-id"
      }
    }
  }
}
```

---

## 💻 CLI Usage

You can test and use the tool directly in your terminal:

### Search for books or phrases:
```bash
uv run runeberg-mcp search "Dödsdansen"
uv run runeberg-mcp search "Abraham Brodersson"
```

### Read a specific page:
```bash
# By work slug and page number:
uv run runeberg-mcp read dasakungen 5

# Or by full URL:
uv run runeberg-mcp read https://runeberg.org/strindbg/dodsdans/0057.html
```

### View work metadata and chapters:
```bash
uv run runeberg-mcp info dasakungen
uv run runeberg-mcp info sbh
```

---

## 🧪 Testing

Run the test suite to verify search, retrieval, and text parsing:

```bash
uv run python test_server.py
```

---

## 📜 License

Distributed under the [MIT License](LICENSE). Digital works hosted on Projekt Runeberg are public domain cultural heritage.
