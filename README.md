# EverMemOS MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)

Give your AI coding assistant (Windsurf / Cursor / Claude Desktop) **persistent long-term memory across sessions**.

Built on [EverMemOS](https://github.com/EverMind-AI/EverMemOS) and the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

**[中文文档](README_zh.md)**

## Features

| Tool | Description | Use Case |
|------|-------------|----------|
| `store_memory` | Save conversation content to long-term memory | Remember project preferences, build steps, architecture decisions |
| `search_memory` | Search relevant memories via natural language | Recall previous discussions, preferences, decisions |
| `get_memories` | Browse memories by user/type | View all stored memories |
| `delete_memory` | Remove unwanted memories | Clean up outdated or incorrect memories |

## Quick Start

### 1. Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- EverMemOS API Key (cloud) or a local EverMemOS instance

### 2. Get an API Key

Go to [console.evermind.ai](https://console.evermind.ai/) to sign up and create an API Key.

### 3. Set Environment Variables

```bash
# Add to ~/.zshrc or ~/.bashrc
export EVERMEM_API_KEY="your-api-key-here"

# Optional
export EVERMEM_USER_ID="my_username"               # Default user ID (default: windsurf_user)
export EVERMEM_GROUP_ID="my_project"               # Default project ID (default: windsurf_project)
export EVERMEM_API_URL="https://api.evermind.ai"   # API URL (defaults to cloud when key is set)

# Reload
source ~/.zshrc
```

### 4. Install Dependencies

```bash
cd /path/to/evermemos-mcp-server
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 5. Configure MCP Server in Windsurf

Open Windsurf Settings → Search "MCP" → Edit MCP config file, and add:

```json
{
  "mcpServers": {
    "evermemos-memory": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/evermemos-mcp-server",
        "run",
        "server.py"
      ],
      "env": {
        "EVERMEM_API_KEY": "your-api-key-here",
        "EVERMEM_USER_ID": "your_username",
        "EVERMEM_GROUP_ID": "your_project"
      }
    }
  }
}
```

> **Warning:** Replace `/absolute/path/to/evermemos-mcp-server` with the actual absolute path on your machine.

### 6. Restart Windsurf

After configuration, restart Windsurf and your AI assistant will have memory capabilities.

---

## Usage Examples

### Example 1: Remember Project Build Preferences

**You say:**
> Our project uses Docker multi-stage build, base image python:3.12-slim, uv for dependency management, build command is `docker build -t myapp:latest .`

**AI assistant internal action:**
```
→ store_memory(
    content="Project uses Docker multi-stage build, base image python:3.12-slim, uv for deps, build: docker build -t myapp:latest .",
    role="user",
    flush=true
  )
→ Memory stored successfully. Status: queued
```

**AI replies:**
> Got it, I've remembered your Docker build preferences. I'll reference these settings whenever you need a Dockerfile or build command.

---

### Example 2: Auto-recall in Next Session

**(New conversation session) You say:**
> Write me a Dockerfile

**AI assistant internal action:**
```
→ search_memory(query="Dockerfile build preferences Docker config")
→ Found 1 relevant memories:
  • [relevance: 0.92] (2025-02-07) [episodic_memory]
    Project uses Docker multi-stage build, base image python:3.12-slim, uv for deps
```

**AI replies:**
> Based on your previous preferences, here's a multi-stage Dockerfile:
> ```dockerfile
> FROM python:3.12-slim AS builder
> COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
> ...
> ```

---

### Example 3: Search Previous Discussions

**You say:**
> What was the conclusion from our database selection discussion?

**AI assistant internal action:**
```
→ search_memory(query="database selection discussion conclusion")
→ Found 2 relevant memories:
  • [relevance: 0.88] Decided to use PostgreSQL as primary DB, Redis for caching
  • [relevance: 0.75] Discussed MongoDB vs PostgreSQL, chose PostgreSQL for transaction support
```

**AI replies:**
> Based on previous records, you decided to use **PostgreSQL** as the primary database (for transaction support) and **Redis** as the caching layer.

---

### Example 4: View All Memories

**You say:**
> Show me what you remember

**AI assistant internal action:**
```
→ get_memories(memory_type="episodic_memory", limit=10)
→ Retrieved 3 memories:
  ── Group: my_project ──
  • (2025-02-05) Docker multi-stage build preferences...
  • (2025-02-06) PostgreSQL + Redis database selection...
  • (2025-02-07) RESTful API design style...
```

---

## Advanced Configuration

### Connect to Local EverMemOS

If you have a local EverMemOS deployment (Docker), no API Key is needed:

```json
{
  "mcpServers": {
    "evermemos-memory": {
      "command": "uv",
      "args": ["--directory", "/path/to/evermemos-mcp-server", "run", "server.py"],
      "env": {
        "EVERMEM_API_URL": "http://localhost:8001",
        "EVERMEM_API_VERSION": "v1"
      }
    }
  }
}
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EVERMEM_API_KEY` | EverMemOS Cloud API Key | _(empty)_ |
| `EVERMEM_API_URL` | API URL | `https://api.evermind.ai` if key is set, else `http://localhost:8001` |
| `EVERMEM_API_VERSION` | API version | `v0` |
| `EVERMEM_USER_ID` | Default user ID | `windsurf_user` |
| `EVERMEM_GROUP_ID` | Default project/group ID | `windsurf_project` |

### Retrieval Methods

| Method | Description | Recommended For |
|--------|-------------|-----------------|
| `hybrid` | Keyword + vector + reranking | **Default recommendation** |
| `keyword` | BM25 keyword matching | Exact term lookup |
| `vector` | Semantic vector search | Fuzzy semantic matching |
| `rrf` | RRF fusion ranking | When reranking is unavailable |
| `agentic` | LLM-guided multi-round retrieval | Complex queries |

## Project Structure

```
evermemos-mcp-server/
├── server.py            # MCP Server entry point (defines Tools)
├── evermemos_client.py  # EverMemOS API client wrapper
├── pyproject.toml       # Project config and dependencies
├── README.md            # This file (English)
└── README_zh.md         # Chinese documentation
```

## License

MIT
