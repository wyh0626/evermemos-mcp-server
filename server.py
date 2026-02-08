"""
EverMemOS MCP Server

Provides long-term memory capabilities to AI coding assistants (Windsurf, Cursor, Claude Desktop)
through the Model Context Protocol (MCP).

Tools:
    - store_memory: Save conversation content into long-term memory
    - search_memory: Search relevant memories by natural language query
    - get_memories: Retrieve memories by user/group/type
    - delete_memory: Remove memories for a user or group

Environment Variables:
    EVERMEM_API_KEY    - API key for EverMemOS Cloud (get from console.evermind.ai)
    EVERMEM_API_URL    - Custom API URL (default: cloud if key set, else localhost:8001)
    EVERMEM_API_VERSION - API version (default: v0)
    EVERMEM_USER_ID    - Default user ID (default: windsurf_user)
    EVERMEM_GROUP_ID   - Default group/project ID (default: windsurf_project)
"""

import json
import logging
import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from evermemos_client import EverMemOSClient

# Configure logging to stderr (STDIO MCP servers must NOT write to stdout)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("evermemos-mcp")

# Initialize MCP server
mcp = FastMCP("evermemos-memory")

# Initialize EverMemOS client
client = EverMemOSClient()

# Default identifiers
DEFAULT_USER_ID = os.getenv("EVERMEM_USER_ID", "windsurf_user")
DEFAULT_GROUP_ID = os.getenv("EVERMEM_GROUP_ID", "windsurf_project")


def _format_search_results(data: dict) -> str:
    """Format search API response into readable text for LLM context."""
    result = data.get("result", data)
    memories = result.get("memories", [])
    scores = result.get("scores", [])
    total = result.get("total_count", 0)

    if not memories:
        return "No relevant memories found."

    lines = [f"Found {total} relevant memories:\n"]

    for i, mem in enumerate(memories):
        # Handle both flat and grouped (dict) memory formats
        if isinstance(mem, dict) and any(isinstance(v, list) for v in mem.values()):
            # Grouped format: {group_id: [memory_list]}
            for group_id, mem_list in mem.items():
                score_dict = scores[i] if i < len(scores) and isinstance(scores[i], dict) else {}
                score_list = score_dict.get(group_id, [])
                lines.append(f"── Group: {group_id} ──")
                for j, m in enumerate(mem_list if isinstance(mem_list, list) else [mem_list]):
                    s = score_list[j] if j < len(score_list) else 0
                    lines.append(_format_single_memory(m, s))
        else:
            # Flat format
            s = scores[i] if i < len(scores) and isinstance(scores[i], (int, float)) else 0
            lines.append(_format_single_memory(mem, s))

    return "\n".join(lines)


def _format_single_memory(mem: dict, score: float = 0) -> str:
    """Format a single memory item."""
    mem_type = ""
    summary = ""
    timestamp = ""
    episode = ""

    if isinstance(mem, dict):
        mem_type = mem.get("memory_type", "")
        summary = mem.get("summary", "")
        timestamp = mem.get("timestamp", "")
        episode = mem.get("episode", "")
    elif hasattr(mem, "memory_type"):
        mem_type = getattr(mem, "memory_type", "")
        summary = getattr(mem, "summary", "")
        timestamp = str(getattr(mem, "timestamp", ""))
        episode = getattr(mem, "episode", "")

    parts = []
    if score:
        parts.append(f"[relevance: {score:.2f}]")
    if timestamp:
        parts.append(f"({timestamp})")
    if mem_type:
        parts.append(f"[{mem_type}]")

    header = " ".join(parts)
    content = episode or summary or "(no content)"

    return f"• {header}\n  {content}\n"


def _format_get_results(data: dict) -> str:
    """Format get memories API response."""
    result = data.get("result", data)
    memories = result.get("memories", [])

    if not memories:
        return "No memories found for this user."

    lines = [f"Retrieved {len(memories)} memories:\n"]
    for mem in memories:
        if isinstance(mem, dict):
            for group_id, mem_list in mem.items():
                lines.append(f"── Group: {group_id} ──")
                for m in (mem_list if isinstance(mem_list, list) else [mem_list]):
                    lines.append(_format_single_memory(m))
        else:
            lines.append(_format_single_memory(mem))

    return "\n".join(lines)


# ==================== MCP Tools ====================


@mcp.tool()
async def store_memory(
    content: str,
    role: str = "user",
    sender: Optional[str] = None,
    group_id: Optional[str] = None,
    flush: bool = False,
) -> str:
    """Save a conversation message into EverMemOS long-term memory.

    Use this tool when the user shares important information that should be remembered
    across sessions, such as: project preferences, coding conventions, architecture decisions,
    deployment procedures, personal preferences, etc.

    Args:
        content: The message content to remember. Be specific and include key details.
        role: Who sent this message - "user" for human messages, "assistant" for AI responses.
        sender: User ID for memory ownership. Defaults to EVERMEM_USER_ID env var.
        group_id: Project/group identifier to organize memories. Defaults to EVERMEM_GROUP_ID env var.
        flush: If True, force immediate memory extraction instead of waiting for natural conversation boundary detection.
    """
    user_id = sender or DEFAULT_USER_ID
    gid = group_id or DEFAULT_GROUP_ID

    try:
        # Ensure conversation meta exists for this group (idempotent)
        try:
            await client.save_conversation_meta(group_id=gid)
        except Exception:
            pass  # May already exist

        result = await client.add_memory(
            content=content,
            sender=user_id,
            group_id=gid,
            sender_name=user_id,
            role=role,
            flush=flush,
        )

        status = result.get("status", "unknown")
        message = result.get("message", "")
        request_id = result.get("request_id", "")

        return f"Memory stored successfully.\n- Status: {status}\n- Message: {message}\n- Request ID: {request_id}"

    except Exception as e:
        logger.error(f"Failed to store memory: {e}")
        return f"Failed to store memory: {str(e)}"


@mcp.tool()
async def search_memory(
    query: str,
    user_id: Optional[str] = None,
    group_id: Optional[str] = None,
    retrieve_method: str = "keyword",
    top_k: int = 5,
) -> str:
    """Search EverMemOS for relevant memories based on a natural language query.

    Use this tool when you need to recall past context, such as: project setup details,
    user preferences, previous decisions, coding patterns, deployment steps, etc.

    Args:
        query: Natural language search query describing what you're looking for.
        user_id: User ID to search memories for. Defaults to EVERMEM_USER_ID env var.
        group_id: Optional project/group filter to narrow search scope.
        retrieve_method: Search strategy - "keyword" (BM25, default), "vector" (semantic),
                        "hybrid" (keyword+vector+rerank, requires rerank service),
                        "rrf" (fusion), "agentic" (LLM-guided multi-round).
        top_k: Maximum number of results to return (1-20).
    """
    uid = user_id or DEFAULT_USER_ID

    try:
        result = await client.search_memories(
            query=query,
            user_id=uid,
            group_id=group_id,
            retrieve_method=retrieve_method,
            top_k=min(top_k, 20),
        )

        return _format_search_results(result)

    except Exception as e:
        logger.error(f"Failed to search memory: {e}")
        return f"Failed to search memory: {str(e)}"


@mcp.tool()
async def get_memories(
    user_id: Optional[str] = None,
    memory_type: str = "episodic_memory",
    group_id: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Retrieve stored memories by user ID and type.

    Use this tool to browse a user's memory collection without a specific search query.

    Args:
        user_id: User ID to fetch memories for. Defaults to EVERMEM_USER_ID env var.
        memory_type: Type of memory to retrieve - "episodic_memory" (conversation summaries),
                    "foresight" (predicted future needs), "event_log" (atomic facts), "profile" (user profile).
        group_id: Optional project/group filter.
        limit: Maximum number of results (1-50).
    """
    uid = user_id or DEFAULT_USER_ID

    try:
        result = await client.get_memories(
            user_id=uid,
            memory_type=memory_type,
            group_id=group_id,
            limit=min(limit, 50),
        )

        return _format_get_results(result)

    except Exception as e:
        logger.error(f"Failed to get memories: {e}")
        return f"Failed to get memories: {str(e)}"


@mcp.tool()
async def delete_memory(
    user_id: Optional[str] = None,
    group_id: Optional[str] = None,
    memory_type: Optional[str] = None,
) -> str:
    """Delete memories from EverMemOS.

    Use this tool when the user explicitly asks to forget or remove certain memories.
    This performs a soft delete.

    Args:
        user_id: User ID whose memories to delete. Defaults to EVERMEM_USER_ID env var.
        group_id: Optional group/project filter - only delete memories in this group.
        memory_type: Optional type filter - only delete this type (episodic_memory, foresight, event_log).
    """
    uid = user_id or DEFAULT_USER_ID

    try:
        result = await client.delete_memories(
            user_id=uid,
            group_id=group_id,
            memory_type=memory_type,
        )

        status = result.get("status", "unknown")
        message = result.get("message", "")
        return f"Delete completed.\n- Status: {status}\n- Message: {message}"

    except Exception as e:
        logger.error(f"Failed to delete memory: {e}")
        return f"Failed to delete memory: {str(e)}"


def main():
    """Entry point for the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
