from __future__ import annotations

from pathlib import Path

from blogger_agent.cli import _blog_draft_from_html, _pop_next_topic, _science_html_paths
from blogger_agent.config import AgentConfig
from blogger_agent.science_queue import resolve_theme, rotate_next_theme_id


def test_pop_next_topic_consumes_first_non_comment_line(tmp_path: Path) -> None:
    topics_file = tmp_path / "topics.txt"
    topics_file.write_text(
        "# Daily blog queue\n\nFirst molecular cloning topic\nSecond virology topic\n",
        encoding="utf-8",
    )

    assert _pop_next_topic(topics_file) == "First molecular cloning topic"

    remaining = topics_file.read_text(encoding="utf-8")
    assert "First molecular cloning topic" not in remaining
    assert "Second virology topic" in remaining


def test_pop_next_topic_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert _pop_next_topic(tmp_path / "missing.txt") is None


def test_rotate_next_theme_id_recycles_to_bottom(tmp_path: Path) -> None:
    queue = tmp_path / "science-updates.txt"
    queue.write_text("# queue\n\nsequencing-verification\ntransfection-expression\n", encoding="utf-8")

    assert rotate_next_theme_id(queue) == "sequencing-verification"
    remaining = queue.read_text(encoding="utf-8")
    assert remaining.strip().endswith("sequencing-verification")
    assert remaining.splitlines()[2].strip() == "transfection-expression"


def test_resolve_theme_known_id() -> None:
    theme = resolve_theme("fluorescence-imaging")
    assert theme.title.startswith("Bench Notes:")
    assert theme.queries


def test_science_html_paths_filters_preview(tmp_path: Path) -> None:
    (tmp_path / "2026-10-07-bench-notes-demo.html").write_text("<h2>Demo</h2>", encoding="utf-8")
    (tmp_path / "preview.html").write_text("<h2>Preview</h2>", encoding="utf-8")
    paths = _science_html_paths(tmp_path, None)
    assert [p.name for p in paths] == ["2026-10-07-bench-notes-demo.html"]


def test_blog_draft_from_html_reads_h2(tmp_path: Path) -> None:
    path = tmp_path / "2026-10-07-bench-notes-demo.html"
    path.write_text("<h2>Bench Notes: demo title</h2><p>body</p>", encoding="utf-8")
    config = AgentConfig(
        blog_url="https://thepipettesolution.blogspot.com",
        blog_id=None,
        client_secret_path=tmp_path / "client_secret.json",
        token_path=tmp_path / "token.json",
        default_labels=("molecular cloning",),
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
    draft = _blog_draft_from_html(path, config)
    assert draft.title == "Bench Notes: demo title"
    assert "science update" in draft.labels
