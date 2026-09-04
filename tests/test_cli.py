from __future__ import annotations

from pathlib import Path

from blogger_agent.cli import _pop_next_topic


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
