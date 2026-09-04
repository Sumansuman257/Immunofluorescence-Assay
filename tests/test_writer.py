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
        gemini_api_key=None,
        gemini_base_url="https://generativelanguage.googleapis.com/v1beta",
        gemini_text_model=None,
        gemini_image_model=None,
        gemini_image_count=2,
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

    assert "Methods and protocol overview" in draft.html
    assert "Expected results and interpretation" in draft.html
    assert "Conclusions" in draft.html
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


def test_template_draft_always_includes_generated_visual(tmp_path: Path) -> None:
    draft = create_blog_draft("Plasmid maps for student cloning projects", [], [], _config(tmp_path))

    assert "Visual explanation" in draft.html
    assert draft.html.count("data:image/svg+xml") >= 3
    assert "Generated teaching schematic" in draft.html
    assert "Additional open-license images" not in draft.html


def test_deep_template_includes_additional_papers(tmp_path: Path) -> None:
    literature = [
        LiteratureResult(
            title=f"Paper {index} about plasmid verification",
            authors="Doe J",
            year="2026",
            journal="Teaching Virology",
            doi=f"10.1000/example-{index}",
            pmid=None,
            abstract="This paper discusses sequence verification and controls in cloning.",
            url=f"https://doi.org/10.1000/example-{index}",
        )
        for index in range(8)
    ]

    draft = create_blog_draft(
        "Plasmid verification for students",
        literature,
        [],
        _config(tmp_path),
        deep_research=True,
    )

    assert "Additional papers reviewed in deep mode" in draft.html
    assert "Paper 7 about plasmid verification" in draft.html
