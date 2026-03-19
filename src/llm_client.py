"""Unified LLM client supporting multiple free open-source providers.

Supported Providers:
- Groq (FREE): llama-3.3-70b-versatile, mixtral-8x7b-32768, gemma-7b-it
- Hugging Face: meta-llama/Llama-3.3-70B-Instruct, mistralai/Mistral-7B-Instruct
- Cohere: command-r-plus, command-r
- Mistral: mistral-large-latest, mistral-small
- OpenAI: gpt-4-turbo-preview (paid fallback)
- Anthropic: claude-3-sonnet (paid fallback)
"""

import os
from typing import Optional, Dict, Any, Literal
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    import httpx
except ImportError:
    httpx = None


class FreeLLMClient:
    """Unified client for free open-source LLM providers.

    Usage:
        client = FreeLLMClient(provider="groq", api_key="your-key")
        response = client.invoke("Hello, how are you?")
    """

    def __init__(
        self,
        provider: Literal[
            "groq", "huggingface", "cohere", "mistral", "openai", "anthropic"
        ] = "groq",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs,
    ):
        self.provider = provider
        self.kwargs = kwargs

        # Set default models based on provider
        default_models = {
            "groq": "llama-3.3-70b-versatile",
            "huggingface": "meta-llama/Llama-3.3-70B-Instruct",
            "cohere": "command-r-plus",
            "mistral": "mistral-large-latest",
            "openai": "gpt-4-turbo-preview",
            "anthropic": "claude-3-sonnet-20240229",
        }

        self.model = model or default_models.get(provider, "llama-3.3-70b-versatile")

        # Initialize clients
        if provider == "groq":
            self._init_groq(api_key)
        elif provider == "huggingface":
            self._init_huggingface(api_key)
        elif provider == "cohere":
            self._init_cohere(api_key)
        elif provider == "mistral":
            self._init_mistral(api_key)
        else:
            raise ValueError(
                f"Provider {provider} requires setup. Use 'groq' for free tier."
            )

    def _init_groq(self, api_key: Optional[str]):
        """Initialize Groq client."""
        if Groq is None:
            raise ImportError("groq package not installed. Run: pip install groq")

        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise ValueError(
                "GROQ_API_KEY required. Get free key at https://console.groq.com"
            )

        self.client = Groq(api_key=key)

    def _init_huggingface(self, api_key: Optional[str]):
        """Initialize Hugging Face client."""
        key = api_key or os.environ.get("HF_TOKEN")
        if not key:
            raise ValueError(
                "HF_TOKEN required. Get free token at https://huggingface.co/settings/tokens"
            )

        self.client = None
        self.hf_token = key

    def _init_cohere(self, api_key: Optional[str]):
        """Initialize Cohere client."""
        key = api_key or os.environ.get("COHERE_API_KEY")
        if not key:
            raise ValueError(
                "COHERE_API_KEY required. Get free key at https://cohere.com"
            )

        self.client = None
        self.cohere_key = key

    def _init_mistral(self, api_key: Optional[str]):
        """Initialize Mistral client."""
        key = api_key or os.environ.get("MISTRAL_API_KEY")
        if not key:
            raise ValueError(
                "MISTRAL_API_KEY required. Get free key at https://mistral.ai"
            )

        self.client = None
        self.mistral_key = key

    def invoke(self, prompt: str, **kwargs) -> str:
        """Send a prompt and get response."""
        if self.provider == "groq":
            return self._groq_invoke(prompt, **kwargs)
        elif self.provider == "huggingface":
            return self._hf_invoke(prompt, **kwargs)
        elif self.provider == "cohere":
            return self._cohere_invoke(prompt, **kwargs)
        elif self.provider == "mistral":
            return self._mistral_invoke(prompt, **kwargs)
        else:
            raise ValueError(f"Provider {self.provider} not supported")

    def _groq_invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Groq API."""
        chat_completion = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens", 2048),
        )
        return chat_completion.choices[0].message.content

    def _hf_invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Hugging Face Inference API."""
        if httpx is None:
            raise ImportError("httpx package required. Run: pip install httpx")

        headers = {
            "Authorization": f"Bearer {self.hf_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": kwargs.get("max_tokens", 2048),
                "temperature": kwargs.get("temperature", 0.0),
                "return_full_text": False,
            },
        }

        # Use async API for better compatibility
        import asyncio

        async def _call():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api-inference.huggingface.co/models/{self.model}",
                    headers=headers,
                    json=payload,
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()
                # Handle different response formats
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                elif isinstance(result, dict) and "generated_text" in result:
                    return result["generated_text"]
                return str(result)

        return asyncio.run(_call())

    def _cohere_invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Cohere API."""
        if httpx is None:
            raise ImportError("httpx package required. Run: pip install httpx")

        headers = {
            "Authorization": f"Bearer {self.cohere_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "message": prompt,
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.0),
        }

        import asyncio

        async def _call():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.cohere.ai/v1/chat",
                    headers=headers,
                    json=payload,
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()
                return result.get("text", "")

        return asyncio.run(_call())

    def _mistral_invoke(self, prompt: str, **kwargs) -> str:
        """Invoke Mistral API."""
        if httpx is None:
            raise ImportError("httpx package required. Run: pip install httpx")

        headers = {
            "Authorization": f"Bearer {self.mistral_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": kwargs.get("max_tokens", 2048),
            "temperature": kwargs.get("temperature", 0.0),
        }

        import asyncio

        async def _call():
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120.0,
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]

        return asyncio.run(_call())


def create_llm_client(
    provider: Optional[str] = None, model: Optional[str] = None, **kwargs
) -> FreeLLMClient:
    """Factory function to create LLM client based on settings.

    Reads from environment variables or uses defaults.
    """
    from src.config import settings

    prov = provider or settings.llm_provider
    mod = model

    if prov == "groq":
        return FreeLLMClient(
            provider="groq",
            model=model or settings.groq_model,
            api_key=settings.groq_api_key,
            **kwargs,
        )
    elif prov == "huggingface":
        return FreeLLMClient(
            provider="huggingface",
            model=model or settings.hf_model,
            api_key=settings.hf_token,
            **kwargs,
        )
    elif prov == "cohere":
        return FreeLLMClient(
            provider="cohere",
            model=model or settings.cohere_model,
            api_key=settings.cohere_api_key,
            **kwargs,
        )
    elif prov == "mistral":
        return FreeLLMClient(
            provider="mistral",
            model=model or settings.mistral_model,
            api_key=settings.mistral_api_key,
            **kwargs,
        )
    else:
        raise ValueError(f"Provider {prov} not configured. Set LLM_PROVIDER in .env")
