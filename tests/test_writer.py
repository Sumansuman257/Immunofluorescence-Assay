from __future__ import annotations

from pathlib import Path

from blogger_agent.config import AgentConfig
from blogger_agent.research import ImageResult, LiteratureResult
from blogger_agent.writer import create_blog_draft, save_draft


def _config(tmp_path: Path) -> AgentConfig:
    return AgentConfig(
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
        blogger_email_to=None,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_username=None,
        smtp_password=None,
        smtp_from=None,
    )


def test_template_draft_contains_references_and_safety_note(tmp_path: Path) -> None:
    literature = [
        LiteratureResult(
            title="Sequence verification in plasmid assembly",
            authors="Doe J, Smith A",
            year="2024",
            journal="Molecular Biology Reports",
            doi="10.1000/example",
            pmid="12345",
            abstract="Sequence verification improves confidence in cloned constructs before interpretation.",
            url="https://doi.org/10.1000/example",
        )
    ]
    images = [
        ImageResult(
            title="File:DNA structure.png",
            url="https://upload.wikimedia.org/example.png",
            page_url="https://commons.wikimedia.org/wiki/File:DNA_structure.png",
            license_name="CC BY-SA 4.0",
            artist="Example artist",
        )
    ]

    draft = create_blog_draft(
        "Golden Gate cloning for viral vector design",
        literature,
        images,
        _config(tmp_path),
    )

    assert "Protocol-planning notes" in draft.html
    assert "Safety and editorial note" in draft.html
    assert "Doe J, Smith A" in draft.html
    assert "CC BY-SA 4.0" in draft.html
    assert draft.labels == ("molecular cloning", "virology")


def test_save_draft_writes_html_file(tmp_path: Path) -> None:
    draft = create_blog_draft("Reporter genes in virology assays", [], [], _config(tmp_path))

    path = save_draft(draft, tmp_path / "drafts")

    assert path.exists()
    assert path.suffix == ".html"
    assert "Reporter genes in virology assays" in path.read_text(encoding="utf-8")
