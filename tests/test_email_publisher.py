from __future__ import annotations

from pathlib import Path

from blogger_agent.config import AgentConfig
from blogger_agent.email_publisher import build_blogger_email
from blogger_agent.writer import BlogDraft


def test_build_blogger_email_contains_html_alternative(tmp_path: Path) -> None:
    config = AgentConfig(
        blog_url="https://thepipettesolution.blogspot.com",
        blog_id=None,
        client_secret_path=tmp_path / "client_secret.json",
        token_path=tmp_path / "token.json",
        default_labels=("molecular cloning", "virology"),
        openai_api_key=None,
        openai_base_url="https://api.openai.com/v1",
        openai_model=None,
        safety_mode="educational",
        draft_dir=tmp_path / "drafts",
        blogger_email_to="secret-address@blogger.com",
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username="sender@example.com",
        smtp_password="app-password",
        smtp_from="sender@example.com",
        gemini_api_key=None,
        gemini_base_url="https://generativelanguage.googleapis.com/v1beta",
        gemini_text_model=None,
        gemini_image_model=None,
        gemini_image_count=2,
    )
    draft = BlogDraft(
        title="Draft title",
        html="<h2>Draft title</h2><p>Hello Blogger.</p>",
        labels=("molecular cloning",),
    )

    message = build_blogger_email(config, draft)

    assert message["To"] == "secret-address@blogger.com"
    assert message["From"] == "sender@example.com"
    assert message["Subject"] == "Draft title"
    assert message.is_multipart()
    assert "Hello Blogger." in message.get_body(("html",)).get_content()
