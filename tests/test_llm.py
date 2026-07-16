"""Tests for the LLM provider configuration."""

import pytest
import os
from unittest.mock import patch

from app.core.llm import _get_provider_config


class TestLLMProviderConfig:
    """Test that the LLM factory correctly resolves providers."""

    def test_ollama_preferred_when_set(self):
        """Ollama should be selected when OLLAMA_BASE_URL is set."""
        with patch("app.core.llm.settings") as mock_settings:
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434/v1"
            mock_settings.OLLAMA_MODEL = "qwen2.5:7b"
            mock_settings.OPENROUTER_API_KEY = "sk-some-key"  # also set

            config = _get_provider_config()

            assert config["openai_api_base"] == "http://localhost:11434/v1"
            assert config["openai_api_key"] == "ollama"
            assert config["model"] == "qwen2.5:7b"

    def test_openrouter_fallback(self):
        """OpenRouter should be used when Ollama is not configured."""
        with patch("app.core.llm.settings") as mock_settings:
            mock_settings.OLLAMA_BASE_URL = None
            mock_settings.OPENROUTER_API_KEY = "sk-test-key"
            mock_settings.OPENROUTER_MODEL = "google/gemini-2.5-flash"

            config = _get_provider_config()

            assert "openrouter.ai" in config["openai_api_base"]
            assert config["openai_api_key"] == "sk-test-key"
            assert config["model"] == "google/gemini-2.5-flash"

    def test_no_provider_raises(self):
        """Should raise ValueError when no provider is configured."""
        with patch("app.core.llm.settings") as mock_settings:
            mock_settings.OLLAMA_BASE_URL = None
            mock_settings.OPENROUTER_API_KEY = None

            with pytest.raises(ValueError, match="No LLM provider configured"):
                _get_provider_config()

    def test_ollama_has_no_extra_headers(self):
        """Ollama config should have empty default_headers."""
        with patch("app.core.llm.settings") as mock_settings:
            mock_settings.OLLAMA_BASE_URL = "http://localhost:11434/v1"
            mock_settings.OLLAMA_MODEL = "llama3"
            mock_settings.OPENROUTER_API_KEY = None

            config = _get_provider_config()

            assert config["default_headers"] == {}

    def test_openrouter_has_referer_header(self):
        """OpenRouter config should include HTTP-Referer for rankings."""
        with patch("app.core.llm.settings") as mock_settings:
            mock_settings.OLLAMA_BASE_URL = None
            mock_settings.OPENROUTER_API_KEY = "sk-key"
            mock_settings.OPENROUTER_MODEL = "meta-llama/llama-3"

            config = _get_provider_config()

            assert "HTTP-Referer" in config["default_headers"]
            assert "X-Title" in config["default_headers"]
