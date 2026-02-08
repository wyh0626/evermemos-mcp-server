# EverMemOS MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-Compatible-purple.svg)](https://modelcontextprotocol.io/)

让你的 AI 编程助手（Windsurf / Cursor / Claude Desktop）拥有**跨会话长期记忆**。

基于 [EverMemOS](https://github.com/EverMind-AI/EverMemOS) 和 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)。

**[English](README.md)**

## 功能

| Tool | 说明 | 使用场景 |
|------|------|---------|
| `store_memory` | 存储对话内容到长期记忆 | 记住项目偏好、构建步骤、架构决策 |
| `search_memory` | 通过自然语言搜索相关记忆 | 回忆之前的讨论、偏好、决策 |
| `get_memories` | 按用户/类型浏览记忆 | 查看所有已存储的记忆 |
| `delete_memory` | 删除不需要的记忆 | 清理过时或错误的记忆 |

## 快速开始

### 1. 前置要求

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) 包管理器
- EverMemOS API Key（云端）或本地 EverMemOS 实例

### 2. 获取 API Key

前往 [console.evermind.ai](https://console.evermind.ai/) 注册并创建 API Key。

### 3. 配置环境变量

```bash
# 添加到 ~/.zshrc 或 ~/.bashrc
export EVERMEM_API_KEY="your-api-key-here"

# 可选配置
export EVERMEM_USER_ID="my_username"          # 默认用户 ID（默认: windsurf_user）
export EVERMEM_GROUP_ID="my_project"          # 默认项目 ID（默认: windsurf_project）
export EVERMEM_API_URL="https://api.evermind.ai"  # API 地址（有 Key 时默认云端）

# 重新加载
source ~/.zshrc
```

### 4. 安装依赖

```bash
cd /path/to/evermemos-mcp-server
uv venv
source .venv/bin/activate
uv pip install -e .
```

### 5. 在 Windsurf 中配置 MCP Server

打开 Windsurf 设置 → 搜索 "MCP" → 编辑 MCP 配置文件，添加：

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

> ⚠️ 请将 `/absolute/path/to/evermemos-mcp-server` 替换为实际的绝对路径。

### 6. 重启 Windsurf

配置完成后重启 Windsurf，AI 助手就能使用记忆功能了。

---

## 使用效果演示

### 场景 1：记住项目构建偏好

**你说：**
> 我们项目用 Docker multi-stage build，基础镜像 python:3.12-slim，用 uv 管理依赖，构建命令是 `docker build -t myapp:latest .`

**AI 助手内部动作：**
```
→ 调用 store_memory(
    content="项目用 Docker multi-stage build，基础镜像 python:3.12-slim，用 uv 管理依赖，构建命令是 docker build -t myapp:latest .",
    role="user",
    flush=true
  )
→ Memory stored successfully. Status: queued
```

**AI 回复：**
> 好的，我已经记住了你的 Docker 构建偏好。以后你需要写 Dockerfile 或构建命令时，我会自动参考这些设置。

---

### 场景 2：下次对话自动回忆

**（新的对话会话）你说：**
> 帮我写个 Dockerfile

**AI 助手内部动作：**
```
→ 调用 search_memory(query="Dockerfile 构建偏好 Docker 配置")
→ Found 1 relevant memories:
  • [relevance: 0.92] (2025-02-07) [episodic_memory]
    项目用 Docker multi-stage build，基础镜像 python:3.12-slim，用 uv 管理依赖
```

**AI 回复：**
> 根据你之前的偏好，我来写一个使用 multi-stage build 的 Dockerfile：
> ```dockerfile
> FROM python:3.12-slim AS builder
> COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
> ...
> ```

---

### 场景 3：搜索之前的讨论

**你说：**
> 我们之前讨论过数据库选型，结论是什么？

**AI 助手内部动作：**
```
→ 调用 search_memory(query="数据库选型 讨论 结论")
→ Found 2 relevant memories:
  • [relevance: 0.88] 决定使用 PostgreSQL 作为主数据库，Redis 做缓存
  • [relevance: 0.75] 讨论了 MongoDB vs PostgreSQL，最终选择 PostgreSQL 因为需要事务支持
```

**AI 回复：**
> 根据之前的讨论记录，你们决定使用 **PostgreSQL** 作为主数据库（因为需要事务支持），**Redis** 做缓存层。

---

### 场景 4：查看所有记忆

**你说：**
> 看看你都记住了什么

**AI 助手内部动作：**
```
→ 调用 get_memories(memory_type="episodic_memory", limit=10)
→ Retrieved 3 memories:
  ── Group: my_project ──
  • (2025-02-05) Docker multi-stage build 偏好...
  • (2025-02-06) PostgreSQL + Redis 数据库选型...
  • (2025-02-07) API 接口用 RESTful 风格...
```

---

## 高级配置

### 连接本地 EverMemOS

如果你在本地部署了 EverMemOS（Docker），可以不需要 API Key：

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

### 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EVERMEM_API_KEY` | EverMemOS Cloud API Key | _(空)_ |
| `EVERMEM_API_URL` | API 地址 | 有 Key 时 `https://api.evermind.ai`，否则 `http://localhost:8001` |
| `EVERMEM_API_VERSION` | API 版本 | `v0` |
| `EVERMEM_USER_ID` | 默认用户 ID | `windsurf_user` |
| `EVERMEM_GROUP_ID` | 默认项目/分组 ID | `windsurf_project` |

### 检索方法

| 方法 | 说明 | 推荐场景 |
|------|------|---------|
| `hybrid` | 关键词 + 向量 + 重排序 | **默认推荐** |
| `keyword` | BM25 关键词匹配 | 精确术语查找 |
| `vector` | 语义向量搜索 | 模糊语义匹配 |
| `rrf` | RRF 融合排序 | 不需要 Rerank 时 |
| `agentic` | LLM 多轮智能检索 | 复杂查询 |

## 项目结构

```
evermemos-mcp-server/
├── server.py           # MCP Server 主入口（定义 Tools）
├── evermemos_client.py  # EverMemOS API 客户端封装
├── pyproject.toml       # 项目配置和依赖
├── README.md            # 英文文档
└── README_zh.md         # 本文件（中文文档）
```

## License

MIT
