from __future__ import annotations

from pathlib import Path
from typing import Any

from blogger_agent.config import AgentConfig
from blogger_agent.writer import BlogDraft


BLOGGER_SCOPES = ["https://www.googleapis.com/auth/blogger"]


def authorize(config: AgentConfig) -> None:
    """Run the desktop OAuth flow and save a reusable local token."""

    _build_service(config)


def create_blogger_draft(config: AgentConfig, draft: BlogDraft) -> dict[str, Any]:
    """Insert a post into Blogger as a draft."""

    service = _build_service(config)
    blog_id = config.blog_id or _resolve_blog_id(service, config.blog_url)
    post_body = {
        "kind": "blogger#post",
        "title": draft.title,
        "content": draft.html,
        "labels": list(draft.labels),
    }
    return (
        service.posts()
        .insert(blogId=blog_id, isDraft=True, body=post_body)
        .execute()
    )


def _build_service(config: AgentConfig):
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise RuntimeError(
            "Blogger upload dependencies are missing. Run `python -m pip install -e .` first."
        ) from exc

    credentials = None
    token_path = config.token_path
    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), BLOGGER_SCOPES)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            if not config.client_secret_path.exists():
                raise FileNotFoundError(
                    f"Missing OAuth client secret file: {config.client_secret_path}. "
                    "Create a Google Cloud OAuth desktop client and download it to this path."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.client_secret_path),
                BLOGGER_SCOPES,
            )
            credentials = flow.run_local_server(port=0)
        _write_token(token_path, credentials.to_json())

    return build("blogger", "v3", credentials=credentials)


def _resolve_blog_id(service, blog_url: str) -> str:
    blog = service.blogs().getByUrl(url=blog_url).execute()
    blog_id = blog.get("id")
    if not blog_id:
        raise RuntimeError(f"Could not resolve Blogger blog ID from URL: {blog_url}")
    return str(blog_id)


def _write_token(path: Path, token_json: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token_json, encoding="utf-8")
