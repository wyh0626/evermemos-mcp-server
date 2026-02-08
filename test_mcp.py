"""
Test script: Verify MCP Server tools work correctly with local EverMemOS.

Tests: store_memory → search_memory → get_memories → delete_memory
"""

import asyncio
import sys

# Add project root to path
sys.path.insert(0, ".")

from evermemos_client import EverMemOSClient


async def main():
    client = EverMemOSClient()
    print(f"📡 Connecting to: {client.memories_url}")
    print()

    # === Test 1: Store Memory ===
    print("=" * 50)
    print("📝 Test 1: store_memory")
    print("=" * 50)
    try:
        result = await client.add_memory(
            content="我喜欢用 Python 写代码，最常用的框架是 FastAPI 和 Django。部署用 Docker。",
            sender="test_user",
            group_id="test_project",
            sender_name="Test User",
            role="user",
            flush=True,  # Force immediate extraction
        )
        print(f"  ✅ Status: {result.get('status')}")
        print(f"  📋 Message: {result.get('message')}")
        print(f"  🔑 Request ID: {result.get('request_id')}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return

    # Store a second message
    print()
    print("📝 Storing second message...")
    try:
        result2 = await client.add_memory(
            content="我的数据库首选 PostgreSQL，缓存用 Redis，搜索引擎用 Elasticsearch。",
            sender="test_user",
            group_id="test_project",
            sender_name="Test User",
            role="user",
            flush=True,
        )
        print(f"  ✅ Status: {result2.get('status')}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    # === Wait for indexing ===
    print()
    print("⏳ Waiting 15 seconds for indexing (MongoDB → ES → Milvus)...")
    await asyncio.sleep(15)

    # === Test 2: Search Memory ===
    print()
    print("=" * 50)
    print("🔍 Test 2: search_memory (keyword)")
    print("=" * 50)
    try:
        result = await client.search_memories(
            query="用户喜欢什么编程语言",
            user_id="test_user",
            group_id="test_project",
            retrieve_method="keyword",
            top_k=5,
        )
        status = result.get("status", "")
        memories = result.get("result", {}).get("memories", [])
        total = result.get("result", {}).get("total_count", 0)
        print(f"  ✅ Status: {status}")
        print(f"  📊 Total results: {total}")
        if memories:
            for i, mem in enumerate(memories[:3]):
                if isinstance(mem, dict):
                    # Could be grouped or flat
                    for k, v in mem.items():
                        if isinstance(v, list):
                            print(f"  📁 Group '{k}': {len(v)} memories")
                            for m in v[:2]:
                                summary = m.get("summary", m.get("episode", ""))[:80]
                                print(f"      • {summary}")
                        else:
                            print(f"  • {k}: {str(v)[:80]}")
        else:
            print("  ⚠️ No memories found (indexing may still be in progress)")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    # === Test 3: Search with vector method ===
    print()
    print("=" * 50)
    print("🔍 Test 3: search_memory (vector)")
    print("=" * 50)
    try:
        result = await client.search_memories(
            query="数据库选型偏好",
            user_id="test_user",
            group_id="test_project",
            retrieve_method="vector",
            top_k=5,
        )
        status = result.get("status", "")
        total = result.get("result", {}).get("total_count", 0)
        print(f"  ✅ Status: {status}")
        print(f"  📊 Total results: {total}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        print(f"  💡 (Vector search requires embedding service - may not work without vLLM)")

    # === Test 4: Get Memories ===
    print()
    print("=" * 50)
    print("📋 Test 4: get_memories")
    print("=" * 50)
    try:
        result = await client.get_memories(
            user_id="test_user",
            memory_type="episodic_memory",
            group_id="test_project",
            limit=10,
        )
        status = result.get("status", "")
        memories = result.get("result", {}).get("memories", [])
        print(f"  ✅ Status: {status}")
        print(f"  📊 Memories count: {len(memories)}")
        if memories:
            for mem in memories[:3]:
                if isinstance(mem, dict):
                    for k, v in mem.items():
                        if isinstance(v, list):
                            print(f"  📁 Group '{k}': {len(v)} memories")
                            for m in v[:2]:
                                summary = m.get("summary", "")[:80]
                                print(f"      • {summary}")
                        else:
                            print(f"  • {k}: {str(v)[:80]}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    # === Test 5: Delete Memories ===
    print()
    print("=" * 50)
    print("🗑️ Test 5: delete_memory")
    print("=" * 50)
    try:
        result = await client.delete_memories(
            user_id="test_user",
            group_id="test_project",
        )
        status = result.get("status", "")
        message = result.get("message", "")
        print(f"  ✅ Status: {status}")
        print(f"  📋 Message: {message}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

    # === Summary ===
    print()
    print("=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    print("  All API endpoints tested!")
    print("  If store succeeded, the MCP Server is ready to use.")
    print("  Search results may be empty if indexing hasn't completed yet.")


if __name__ == "__main__":
    asyncio.run(main())
