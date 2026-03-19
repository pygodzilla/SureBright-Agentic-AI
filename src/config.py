"""Configuration management using Pydantic Settings.

Free Open-Source LLM Providers:
- GROQ: https://console.groq.com - Free tier with Llama, Mixtral, Gemma
- HUGGING_FACE: https://huggingface.co/inference-endpoints - Free tier
- COHERE: https://cohere.com - Free trial with Command models
- MISTRAL: https://mistral.ai - Free tier with Mistral models
"""

import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # LLM Provider Selection (free open-source options)
    llm_provider: Literal[
        "groq", "huggingface", "cohere", "mistral", "openai", "anthropic"
    ] = "groq"

    # Groq (FREE - Recommended for trial)
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"  # Free tier model

    # Hugging Face (FREE tier)
    hf_token: Optional[str] = None
    hf_model: str = "meta-llama/Llama-3.3-70B-Instruct"  # Free tier

    # Cohere (Free trial)
    cohere_api_key: Optional[str] = None
    cohere_model: str = "command-r-plus"

    # Mistral (Free tier)
    mistral_api_key: Optional[str] = None
    mistral_model: str = "mistral-large-latest"

    # OpenAI (Paid - fallback)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4-turbo-preview"

    # Anthropic (Paid - fallback)
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-sonnet-20240229"

    # Vector Database
    chroma_db_path: str = "./data/chroma_db"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"  # Free embedding

    # Database
    database_url: str = "postgresql://user:pass@localhost:5432/claims"

    # Evaluation
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Logging
    log_level: str = "INFO"


settings = Settings()
