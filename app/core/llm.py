from langchain_openai import ChatOpenAI
from app.core.config import settings


def _get_provider_config() -> dict:
    """Resolve LLM provider configuration.

    Supports two backends based on `LLM_PROVIDER`:
      1. **ollama** (local, free) — set ``OLLAMA_BASE_URL`` in ``.env``
      2. **openrouter** (cloud) — set ``OPENROUTER_API_KEY`` in ``.env``.
    """
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "ollama":
        if not settings.OLLAMA_BASE_URL:
            raise ValueError("OLLAMA_BASE_URL is required when LLM_PROVIDER is 'ollama'")
        return {
            "openai_api_key": "ollama",
            "openai_api_base": settings.OLLAMA_BASE_URL,
            "model": settings.OLLAMA_MODEL,
            "default_headers": {},
        }
    
    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required when LLM_PROVIDER is 'openrouter'")
        return {
            "openai_api_key": settings.OPENROUTER_API_KEY,
            "openai_api_base": "https://openrouter.ai/api/v1",
            "model": settings.OPENROUTER_MODEL,
            "default_headers": {
                "HTTP-Referer": "https://github.com/irzix/devops-copilot",
                "X-Title": "DevOps Copilot Agent",
            },
        }

    raise ValueError(f"Unsupported LLM_PROVIDER: '{provider}'. Use 'ollama' or 'openrouter'.")


def get_llm(callbacks=None) -> ChatOpenAI:
    """Streaming LLM for interactive agent turns.

    Use this ONLY inside agent_node where tokens need to be streamed
    to the active WebSocket. Do NOT use in background tasks.
    """
    config = _get_provider_config()
    return ChatOpenAI(
        openai_api_key=config["openai_api_key"],
        openai_api_base=config["openai_api_base"],
        model=config["model"],
        temperature=0.0,
        streaming=True,
        callbacks=callbacks or [],
        default_headers=config["default_headers"],
    )


def get_llm_non_streaming() -> ChatOpenAI:
    """Non-streaming LLM for background tasks (memory extraction, summarization, reflexion).

    Background tasks run via asyncio.create_task which inherits the parent's context,
    including active_websocket. Using a streaming LLM here would cause internal
    JSON (facts, summaries) to leak as tokens into the user's chat stream.
    Always use this factory for any LLM call that runs outside of agent_node.
    """
    config = _get_provider_config()
    return ChatOpenAI(
        openai_api_key=config["openai_api_key"],
        openai_api_base=config["openai_api_base"],
        model=config["model"],
        temperature=0.0,
        streaming=False,
        callbacks=[],
        default_headers=config["default_headers"],
    )
