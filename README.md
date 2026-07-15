# DevOps Copilot 🚀

**An autonomous, self-learning AI DevOps Assistant & CLI Client that manages bare-metal servers with Memory-First Architecture, Experiential Learning (`ExpeL`), Semantic Guardrails, and Real-Time SSH Tunneling.**

---

## 💡 About The Project

Managing infrastructure via traditional CLI tools or basic AI wrappers often leads to dangerous mistakes, repetitive debugging dead-ends, and fragmented server logs. **DevOps Copilot** redefines server management by combining a **Memory-First Agent Architecture** with **Closed-Loop Experiential Learning (ExpeL)** directly in your terminal.

Unlike standard AI chat wrappers that forget previous troubleshooting sessions, `DevOps Copilot` builds a permanent, structured **ChromaDB Vector Knowledge Base** of your infrastructure:

- **🧠 Memory-First Architecture:** A multi-store memory system (`SemanticStore`, `LessonStore`, `EpisodicStore`, `UserFactStore`, `ProceduralStore`) that reads context before every agent turn and writes extracted facts after each interaction — ensuring the agent remembers your servers, preferences, and past incidents across sessions.
- **🔁 LangGraph StateGraph Agent:** Fully stateful agent built on LangGraph with dedicated nodes for memory retrieval (`read_memory`), reasoning (`agent`), tool execution (`tools`), self-correction (`evaluator`), and memory persistence (`write_memory`).
- **🧠 Zero-Click Experiential Learning (ExpeL & Reflexion):** Every time an incident or bug is diagnosed and resolved, the agent distills the entire session into a structured Postmortem (`Problem`, `Real Cause`, `What didn't work`, `What worked`). Before tackling new errors, relevant past lessons are **automatically retrieved and injected** into the agent's context—ensuring it *never repeats a dead end*.
- **🔍 LangSmith Observability:** Full tracing of every graph node, tool call, memory read/write, human-in-the-loop interrupt, and self-correction retry — all via environment variables with zero code changes.
- **🛡️ Semantic Security Guardrails:** Local vector search intercepts and blocks catastrophic shell commands (e.g., `rm -rf /`, `mkfs`) before they ever touch your servers.
- **🧑‍💻 Human-in-the-Loop (HITL) Approvals:** State-modifying actions dynamically prompt for explicit admin confirmation (`[y/N]`) inside the terminal using LangGraph's native `interrupt` mechanism.
- **⚡ Real-Time Async Execution Tunnel:** Streams LLM reasoning, SSH `stdout`, and `stderr` line-by-line via resilient WebSockets with automatic reconnection and exponential backoff.
- **🔒 Zero-Trust Credential Encryption:** Passwords and SSH private keys are encrypted at rest using AES-256 (`Fernet`).

---

## 🏛️ System Architecture

```
+-----------------------------------------------------------------------------------+
|                                 DevOps Copilot CLI                                |
|  (Typer Async Client + Real-Time WebSocket Tunnel + [y/N] Terminal Approval)      |
+-----------------------------------------------------------------------------------+
                                   |           ^
                   REST Auth/CRUD  |           | WebSocket Stream (stdout/stderr)
                                   v           |
+-----------------------------------------------------------------------------------+
|                              FastAPI Backend Server                               |
|                                                                                   |
|  +------------------------+   +-----------------------+   +--------------------+  |
|  |     Auth Module        |   |    Servers Module     |   | Guardrails Module  |  |
|  |  (JWT & AES Fernet)    |   |  (AsyncSSH Execution) |   | (Vector Blacklist) |  |
|  +------------------------+   +-----------------------+   +--------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  |                     LangGraph StateGraph Agent                               |  |
|  |                                                                              |  |
|  |  read_memory ──> agent ──> tools ──> evaluator ──> agent ──> write_memory    |  |
|  |       │                      │           │                        │           |  |
|  |       │            ┌─────────┘           │ (self-correction ×3)   │           |  |
|  |       ▼            ▼                                              ▼           |  |
|  |  MemoryManager   SSH / Knowledge                          ExtractionPipeline  |  |
|  |  (read_context)  Guardrails / HITL                       ConsolidationPipeline|  |
|  |                                                          EpisodicSummarizer   |  |
|  +-----------------------------------------------------------------------------+  |
|                                       │                                           |
|                                       ▼                                           |
|  +-----------------------------------------------------------------------------+  |
|  |                      ChromaDB Multi-Store Knowledge Base                     |  |
|  |                                                                              |  |
|  |  command_history │ server_logs │ server_configs │ lessons_learned            |  |
|  |  episodic_summaries │ user_facts │ procedural_tools                          |  |
|  +-----------------------------------------------------------------------------+  |
|                                                                                   |
|  +-----------------------------------+                                            |
|  |   LangSmith Tracing (Optional)    |                                            |
|  |   Full graph & tool observability |                                            |
|  +-----------------------------------+                                            |
+-----------------------------------------------------------------------------------+
```

### The LangGraph Agent Flow

1. **`read_memory`** — Retrieves episodic summaries, lessons learned, user facts, and knowledge from ChromaDB before the agent reasons.
2. **`agent`** — LLM reasoning node (OpenRouter) with all tools bound. Decides next action or generates final response.
3. **`tools`** — Executes tools (`execute_ssh_command`, `search_knowledge`, `fetch_server_logs`, etc.) via `ainvoke()`.
4. **`evaluator`** — Inspects tool results. Routes back to `agent` for self-correction on failures (up to 3 retries). Skips non-retryable infrastructure errors (SSH timeouts, auth failures).
5. **`write_memory`** — Background extraction of facts, preferences, and episodic summaries via non-streaming LLM.

### The Closed-Loop Experiential Learning (`ExpeL`) Flow

1. **Observe & Act:** Agent connects via `AsyncSSH`, runs non-destructive diagnostics or approved actions, and indexes outputs into `command_history` and `server_logs`.
2. **Judge & Extract:** When an incident is resolved, the postmortem endpoint triggers an automated LLM extraction (`Problem`, `Real Cause`, `What didn't work`, `What worked`) stored in `lessons_learned`.
3. **Zero-Click Injection:** On any future chat turn, `read_memory` queries `lessons_learned` and injects proven solutions directly into the agent's system prompt context.

---

## Key Features

- **Memory-First Agent Architecture:** Multi-store retrieval (`SemanticStore`, `LessonStore`, `EpisodicStore`, `UserFactStore`) on every turn with automatic fact extraction, consolidation, and episodic summarization after each interaction.
- **LangGraph StateGraph:** Fully stateful agent with dedicated nodes for memory I/O, tool execution, and self-correction — replacing the legacy agent loop.
- **Experiential Learning (ExpeL / Reflexion Postmortems):** Distills complex debugging sessions into structured `Lessons Learned` cards indexed into ChromaDB with zero-click context injection.
- **Self-Correction (Evaluator Node):** Automatic detection of tool execution failures (e.g. non-zero exit codes) in LangGraph, routing execution back to the agent with error details for self-healing (up to 3 retry attempts). Terminal infrastructure errors (SSH refused, auth failure) bypass retry.
- **Negative Feedback Reflexion:** Submitting negative feedback (thumbs-down) on AI responses triggers a background LLM Reflexion pipeline to analyze the failure, extract a lesson, and store it in ChromaDB's `LessonStore`.
- **LangSmith Observability:** Full tracing of LangGraph execution, tool calls, memory nodes, and interrupts — enabled via environment variables with zero code changes.
- **Lean RAG Knowledge Base:** Automatically chunks and indexes executed SSH command outputs, logs, and server configs into separate **ChromaDB** collections (7 stores total).
- **Semantic Guardrails:** Uses local vector search to intercept and block dangerous terminal commands.
- **Human-in-the-Loop (HITL):** Enforces admin approval (`[y/N]`) via LangGraph's native `interrupt` mechanism for state-modifying actions.
- **Auto Schema Migration:** Automatically detects and adds new database columns on startup without manual migration scripts.
- **CLI Connection Resilience:** Automatically reconnects to the WebSocket server using exponential backoff if the network drops.
- **Real-Time Streaming:** Streams LLM thoughts and active SSH `stdout`/`stderr` line-by-line using WebSockets with 30s execution timeouts.
- **Encrypted Credentials:** Securely encrypts passwords and SSH private keys using Fernet (AES-256).
- **Server & Session CRUD & Feedback:** Full REST API support for managing server connections, deleting sessions, and submitting user satisfaction ratings.
- **Flexible AI Models:** Powered by **OpenRouter** (supports Llama 3, Gemini, GPT, etc.).

---

## 📦 Quick Start (Backend Server)

### 1. Configure Settings
Copy the env file and populate keys:
```bash
cp .env.example .env
```
Make sure to add your `OPENROUTER_API_KEY` and a custom base64 `ENCRYPTION_KEY` in `.env`.

### 2. Enable LangSmith Tracing (Optional)
Get your API key from [smith.langchain.com](https://smith.langchain.com) and add to `.env`:
```bash
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_pt_...
LANGSMITH_PROJECT=devops-copilot
```
> For EU data residency, set `LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com`

### 3. Run with Docker Compose
```bash
docker compose up -d --build
```
The server will boot on port `8000`. Database tables, schema migrations, and security blacklist vectors are automatically seeded on startup.

---

## 💻 Quick Start (CLI Client)

### 1. Install Globally
Install the package in editable mode from your local repository root:
```bash
uv pip install -e .
```

### 2. Authenticate
Configure the server URL and log in to get your JWT access token:
```bash
devops-copilot login
```

### 3. Interactive Chat & Auto-Postmortems
Start the real-time DevOps chat session:
```bash
devops-copilot chat
```
*Ask the agent to check stats or run actions. Approve state-modifying commands directly in the prompt.*

Extract and index a structured Experiential Lesson Learned from any completed troubleshooting session:
```bash
devops-copilot lesson <session_id>
```

---

## 🏗️ Project Structure

```
app/
├── core/
│   ├── config.py            # Pydantic settings (env vars)
│   ├── database/            # Async SQLite engine + auto-migration
│   ├── llm.py               # LLM factories (streaming & non-streaming)
│   └── security.py          # Fernet AES-256 encryption
├── modules/
│   ├── auth/                # JWT authentication
│   ├── servers/             # Server CRUD + SSH credentials
│   ├── guardrails/          # Semantic command blacklist
│   ├── knowledge/           # ChromaDB indexing service
│   ├── chat/
│   │   ├── agent.py         # LangGraph StateGraph definition
│   │   ├── router.py        # WebSocket handler + REST endpoints
│   │   ├── models.py        # ChatSession, ChatMessage, AgentAction
│   │   └── schema.py        # Pydantic request/response schemas
│   └── memory/
│       ├── manager.py        # MemoryManager (read_context / write_after_turn)
│       ├── stores.py         # 7 ChromaDB collection wrappers
│       ├── extraction.py     # LLM fact extraction pipeline
│       ├── consolidation.py  # Deduplication before persistence
│       ├── summarizer.py     # Episodic session summarizer
│       ├── reflexion.py      # Negative feedback analysis pipeline
│       └── types.py          # AgentState, ExtractedFact, MemoryContext
└── cli/                      # Typer CLI client
```

