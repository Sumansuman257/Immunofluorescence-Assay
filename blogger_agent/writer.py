from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import requests

from blogger_agent.config import AgentConfig
from blogger_agent.research import ImageResult, LiteratureResult


@dataclass(frozen=True)
class BlogDraft:
    title: str
    html: str
    labels: tuple[str, ...]


def create_blog_draft(
    topic: str,
    literature: list[LiteratureResult],
    images: list[ImageResult],
    config: AgentConfig,
    requested_words: str = "300-500",
) -> BlogDraft:
    """Create a Blogger-ready draft with an LLM when configured, otherwise use a local template."""

    if config.openai_api_key and config.openai_model:
        try:
            return _create_llm_draft(topic, literature, images, config, requested_words)
        except requests.RequestException:
            # Network/model failures should not stop daily drafting; fall back to a cited template.
            pass

    return _create_template_draft(topic, literature, images, config)


def save_draft(draft: BlogDraft, draft_dir: Path) -> Path:
    draft_dir.mkdir(parents=True, exist_ok=True)
    slug = _slugify(draft.title)
    path = draft_dir / f"{date.today().isoformat()}-{slug}.html"
    path.write_text(draft.html, encoding="utf-8")
    return path


def _create_llm_draft(
    topic: str,
    literature: list[LiteratureResult],
    images: list[ImageResult],
    config: AgentConfig,
    requested_words: str,
) -> BlogDraft:
    payload = {
        "model": config.openai_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write careful educational blog drafts for a virologist. "
                    "Use clear scientific language, figurative explanations, and accurate citations. "
                    "Do not provide operational wet-lab instructions for engineering, recovering, "
                    "propagating, optimizing, or enhancing viruses or pathogens. "
                    "When a topic touches protocols, write a protocol-planning overview with safety, "
                    "controls, decision points, and references to institution-approved SOPs."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "topic": topic,
                        "target_words": requested_words,
                        "safety_mode": config.safety_mode,
                        "literature": [
                            {
                                "title": item.title,
                                "authors": item.authors,
                                "year": item.year,
                                "journal": item.journal,
                                "doi": item.doi,
                                "abstract": item.abstract[:1200],
                                "citation": item.citation,
                            }
                            for item in literature
                        ],
                        "images": [
                            {
                                "title": item.title,
                                "url": item.url,
                                "attribution": item.attribution_html,
                            }
                            for item in images
                        ],
                        "format": (
                            "Return strict JSON with keys title, labels, html. "
                            "html must be Blogger-ready HTML with headings, figure tags, APA/Vancouver-style "
                            "references, and a short safety note."
                        ),
                    }
                ),
            },
        ],
        "temperature": 0.4,
    }
    response = requests.post(
        f"{config.openai_base_url}/chat/completions",
        headers={
            "Authorization": f"Bearer {config.openai_api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    parsed = _load_json_from_text(content)
    return BlogDraft(
        title=str(parsed.get("title") or topic).strip(),
        html=str(parsed.get("html") or ""),
        labels=tuple(parsed.get("labels") or config.default_labels),
    )


def _create_template_draft(
    topic: str,
    literature: list[LiteratureResult],
    images: list[ImageResult],
    config: AgentConfig,
) -> BlogDraft:
    safe_topic = html.escape(topic)
    lead = _lead_from_literature(literature)
    title = f"{topic}: a molecular cloning and virology research update"

    body: list[str] = [
        f"<h2>{html.escape(title)}</h2>",
        "<p><em>Draft generated for editorial review before publishing.</em></p>",
        (
            f"<p>{safe_topic} can be understood like assembling a precise molecular map: "
            "each fragment, control, and readout has to fit the biological question before the "
            "experiment becomes trustworthy. The recent literature around this topic highlights "
            f"{html.escape(lead)}</p>"
        ),
    ]

    if images:
        body.extend(_render_figures(images))

    body.extend(
        [
            "<h3>Why this matters</h3>",
            (
                "<p>For cloning-centered virology work, the strongest articles usually connect "
                "three layers: the genetic design, the delivery or expression context, and the "
                "assay used to confirm that the biology matches the design. A useful draft post "
                "should therefore explain not only what was cloned, but why the construct, control "
                "strategy, and validation readout were chosen.</p>"
            ),
            "<h3>Protocol-planning notes</h3>",
            (
                "<ul>"
                "<li>Define the biological question, construct architecture, and non-pathogenic model system before selecting a cloning workflow.</li>"
                "<li>List positive, negative, and sequence-confirmation controls in the article so readers can evaluate experimental logic.</li>"
                "<li>Separate conceptual workflow discussion from lab-specific operating conditions, which should come from validated institutional SOPs.</li>"
                "<li>Include biosafety context when viral vectors, infectious clones, or primary specimens are discussed.</li>"
                "</ul>"
            ),
            "<h3>What the cited work suggests</h3>",
            _render_literature_summary(literature),
            "<h3>Safety and editorial note</h3>",
            (
                "<p>This draft is intended for education and scientific communication. It avoids "
                "step-by-step pathogen engineering or propagation instructions and should be reviewed "
                "against local biosafety approvals, material transfer rules, and laboratory SOPs before "
                "publication.</p>"
            ),
            "<h3>References</h3>",
            _render_references(literature),
        ]
    )
    return BlogDraft(title=title, html="\n".join(body), labels=config.default_labels)


def _render_figures(images: Iterable[ImageResult]) -> list[str]:
    rendered: list[str] = ["<h3>Visual explanation</h3>"]
    for image in images:
        rendered.append(
            (
                "<figure>"
                f'<img src="{html.escape(image.url, quote=True)}" '
                f'alt="{html.escape(image.title.replace("File:", ""))}" '
                'style="max-width:100%;height:auto;" />'
                f"<figcaption>{image.attribution_html}</figcaption>"
                "</figure>"
            )
        )
    return rendered


def _render_literature_summary(literature: list[LiteratureResult]) -> str:
    if not literature:
        return (
            "<p>No literature results were retrieved automatically. Add manual references before "
            "publishing this draft.</p>"
        )

    items = []
    for paper in literature[:5]:
        abstract = paper.abstract or "The abstract was not available from Europe PMC."
        summary = _first_sentence(abstract)
        items.append(
            "<li>"
            f"<strong>{html.escape(paper.title)}</strong> "
            f"({html.escape(paper.year or 'n.d.')}) - {html.escape(summary)}"
            "</li>"
        )
    return "<ul>" + "\n".join(items) + "</ul>"


def _render_references(literature: list[LiteratureResult]) -> str:
    if not literature:
        return "<p>References to be added during editorial review.</p>"
    return "<ol>" + "\n".join(
        f"<li>{html.escape(item.citation)}</li>" for item in literature[:7]
    ) + "</ol>"


def _lead_from_literature(literature: list[LiteratureResult]) -> str:
    if not literature:
        return "the need to pair molecular design with strong controls, clear validation, and biosafety review."

    keywords = []
    source_text = " ".join(item.title for item in literature[:5]).lower()
    for candidate in (
        "vector",
        "assembly",
        "expression",
        "screening",
        "reverse genetics",
        "sequencing",
        "virus",
        "plasmid",
        "recombination",
    ):
        if candidate in source_text:
            keywords.append(candidate)
    if keywords:
        return "recurring themes such as " + ", ".join(keywords[:4]) + "."
    return "the importance of careful design, controls, validation, and transparent reporting."


def _first_sentence(text: str) -> str:
    match = re.search(r"(.{80,}?[.!?])\s", text)
    if match:
        return match.group(1)
    return text[:220].rstrip() + ("..." if len(text) > 220 else "")


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "blogger-draft"


def _load_json_from_text(value: str) -> dict:
    value = value.strip()
    if value.startswith("```"):
        value = re.sub(r"^```(?:json)?", "", value).strip()
        value = re.sub(r"```$", "", value).strip()
    return json.loads(value)
