"""
EverMemOS API Client

Supports both EverMemOS Cloud (api.evermind.ai) and local deployment (localhost:8001).
"""

import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import uuid

import httpx

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CLOUD_URL = "https://api.evermind.ai"
DEFAULT_LOCAL_URL = "http://localhost:1995"
DEFAULT_API_VERSION = "v1"


class EverMemOSClient:
    """Async HTTP client for EverMemOS API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        api_version: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("EVERMEM_API_KEY", "")
        self.api_version = api_version or os.getenv("EVERMEM_API_VERSION", DEFAULT_API_VERSION)

        if base_url:
            self.base_url = base_url.rstrip("/")
        elif os.getenv("EVERMEM_API_URL"):
            self.base_url = os.getenv("EVERMEM_API_URL").rstrip("/")
        elif self.api_key:
            self.base_url = DEFAULT_CLOUD_URL
        else:
            self.base_url = DEFAULT_LOCAL_URL

        self.memories_url = f"{self.base_url}/api/{self.api_version}/memories"
        self.timeout = timeout

        logger.info(f"EverMemOS client initialized: {self.base_url} (version: {self.api_version})")

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def save_conversation_meta(
        self,
        group_id: str,
        scene: str = "assistant",
        group_name: str = "MCP Memory Group",
        user_details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Save conversation metadata (required before first store on local API).

        Args:
            group_id: Group/project identifier
            scene: Scene type - "assistant" or "group_chat"
            group_name: Display name for the group
            user_details: Dict of user details {sender_name: {full_name, role, extra}}
        """
        meta_url = f"{self.base_url}/api/{self.api_version}/memories/conversation-meta"

        if user_details is None:
            user_details = {
                "User": {"full_name": "User", "role": "user", "extra": {}},
                "Assistant": {"full_name": "AI Assistant", "role": "assistant", "extra": {}},
            }

        payload = {
            "version": "1.0.0",
            "scene": scene,
            "scene_desc": {},
            "name": group_name,
            "description": f"MCP Memory - {scene} scene",
            "group_id": group_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "default_timezone": "UTC",
            "user_details": user_details,
            "tags": ["mcp", scene],
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                meta_url,
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def add_memory(
        self,
        content: str,
        sender: str,
        group_id: str = "",
        sender_name: str = "",
        role: str = "user",
        scene: str = "assistant",
        message_id: Optional[str] = None,
        flush: bool = False,
    ) -> Dict[str, Any]:
        """Store a message into EverMemOS for memory extraction.

        Args:
            content: Message content to store
            sender: Sender user ID (also used as user_id for memory ownership)
            group_id: Group/project identifier for organizing memories
            sender_name: Display name of the sender
            role: Message role - "user" or "assistant"
            scene: Scene type - "assistant" or "group_chat"
            message_id: Unique message ID (auto-generated if not provided)
        """
        if not group_id:
            group_id = f"{sender}_group"

        payload = {
            "message_id": message_id or f"msg_{uuid.uuid4().hex[:12]}",
            "create_time": datetime.now(timezone.utc).isoformat(),
            "sender": sender,
            "sender_name": sender_name or sender,
            "group_id": group_id,
            "content": content,
            "role": role,
            "type": "text",
            "scene": scene,
        }
        if flush:
            payload["flush"] = True

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                self.memories_url,
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def search_memories(
        self,
        query: str,
        user_id: str,
        group_id: Optional[str] = None,
        retrieve_method: str = "hybrid",
        memory_types: Optional[List[str]] = None,
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """Search for relevant memories.

        Args:
            query: Search query text
            user_id: User ID to search memories for
            group_id: Optional group ID filter
            retrieve_method: One of keyword, vector, hybrid, rrf, agentic
            memory_types: List of memory types to search (episodic_memory, foresight, event_log)
            top_k: Maximum number of results
        """
        params: Dict[str, Any] = {
            "user_id": user_id,
            "query": query,
            "retrieve_method": retrieve_method,
            "top_k": top_k,
        }
        if group_id:
            params["group_id"] = group_id
        if memory_types:
            params["memory_types"] = memory_types

        # Cloud API uses POST for search, local uses GET
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            if self.api_key:
                # Cloud API: POST with JSON body
                resp = await client.post(
                    f"{self.memories_url}/search",
                    json=params,
                    headers=self._headers(),
                )
            else:
                # Local API: GET with query params
                resp = await client.get(
                    f"{self.memories_url}/search",
                    params=params,
                    headers=self._headers(),
                )
            resp.raise_for_status()
            return resp.json()

    async def get_memories(
        self,
        user_id: str,
        memory_type: str = "episodic_memory",
        group_id: Optional[str] = None,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Retrieve memories by user ID and type.

        Args:
            user_id: User ID to fetch memories for
            memory_type: Type of memory (episodic_memory, foresight, event_log, profile)
            group_id: Optional group ID filter
            limit: Maximum number of results
        """
        params: Dict[str, Any] = {
            "user_id": user_id,
            "memory_type": memory_type,
            "limit": limit,
        }
        if group_id:
            params["group_id"] = group_id

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.get(
                self.memories_url,
                params=params,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    async def delete_memories(
        self,
        user_id: str,
        group_id: Optional[str] = None,
        memory_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Soft-delete memories.

        Args:
            user_id: User ID whose memories to delete
            group_id: Optional group ID filter
            memory_type: Optional memory type filter
        """
        payload: Dict[str, Any] = {"user_id": user_id}
        if group_id:
            payload["group_id"] = group_id
        if memory_type:
            payload["memory_type"] = memory_type

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.request(
                "DELETE",
                self.memories_url,
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()
