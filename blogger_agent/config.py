from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_BLOG_URL = "https://thepipettesolution.blogspot.com"
DEFAULT_LABELS = (
    "molecular cloning",
    "virology",
    "protocol planning",
    "research update",
)


@dataclass(frozen=True)
class AgentConfig:
    blog_url: str
    blog_id: str | None
    client_secret_path: Path
    token_path: Path
    default_labels: tuple[str, ...]
    openai_api_key: str | None
    openai_base_url: str
    openai_model: str | None
    safety_mode: str
    draft_dir: Path


def _csv(value: str | None, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if not value:
        return fallback
    return tuple(item.strip() for item in value.split(",") if item.strip())


def load_config(env_path: str | os.PathLike[str] | None = None) -> AgentConfig:
    """Load local configuration from .env and environment variables."""

    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    return AgentConfig(
        blog_url=os.getenv("BLOGGER_BLOG_URL", DEFAULT_BLOG_URL).strip(),
        blog_id=os.getenv("BLOGGER_BLOG_ID") or None,
        client_secret_path=Path(os.getenv("BLOGGER_CLIENT_SECRET", "client_secret.json")),
        token_path=Path(os.getenv("BLOGGER_TOKEN", "token.json")),
        default_labels=_csv(os.getenv("BLOGGER_DEFAULT_LABELS"), DEFAULT_LABELS),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_model=os.getenv("OPENAI_MODEL") or None,
        safety_mode=os.getenv("SAFETY_MODE", "educational").strip().lower(),
        draft_dir=Path(os.getenv("DRAFT_DIR", "drafts")),
    )
