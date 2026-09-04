from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

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
    requested_words: str = "900-1200",
    deep_research: bool = False,
) -> BlogDraft:
    """Create a Blogger-ready draft with an LLM when configured, otherwise use a local template."""

    if config.openai_api_key and config.openai_model:
        try:
            return _create_llm_draft(topic, literature, images, config, requested_words, deep_research)
        except requests.RequestException:
            # Network/model failures should not stop daily drafting; fall back to a cited template.
            pass

    return _create_template_draft(topic, literature, images, config, deep_research)


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
    deep_research: bool,
) -> BlogDraft:
    payload = {
        "model": config.openai_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write careful educational blog drafts for a virologist. "
                    "Write like a thoughtful human teacher, not like a short abstract. "
                    "Use clear scientific language, vivid analogies, student-friendly explanations, "
                    "short paragraphs, and accurate citations. "
                    "Do not provide operational wet-lab instructions for engineering, recovering, "
                    "propagating, optimizing, or enhancing viruses or pathogens. "
                    "When a topic touches protocols, write a protocol-planning overview with safety, "
                    "controls, decision points, and references to institution-approved SOPs. "
                    "Always include useful visual explanations with figure captions."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "topic": topic,
                        "target_words": requested_words,
                        "deep_research": deep_research,
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
                            "html must be Blogger-ready HTML with these sections: Introduction, "
                            "Methods and protocol overview, Worked example, Expected results and interpretation, "
                            "Common mistakes, Conclusions, Safety note, and References. Include figure tags, "
                            "APA/Vancouver-style references, and teaching-focused visual explanations."
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
        html=_with_required_visuals(str(parsed.get("html") or ""), topic, literature, images),
        labels=tuple(parsed.get("labels") or config.default_labels),
    )


def _create_template_draft(
    topic: str,
    literature: list[LiteratureResult],
    images: list[ImageResult],
    config: AgentConfig,
    deep_research: bool,
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
        *_render_generated_diagram(topic, literature),
        *_render_figures(images),
        "<h3>Introduction: why this matters</h3>",
        (
            "<p>For cloning-centered virology work, the strongest articles usually connect "
            "three layers: the genetic design, the delivery or expression context, and the "
            "assay used to confirm that the biology matches the design. A useful student article "
            "should therefore explain not only what was cloned, but why the construct, control "
            "strategy, and validation readout were chosen.</p>"
        ),
        (
            "<p>Students often remember this best by imagining the experiment as a railway system. "
            "The insert is the cargo, the vector is the carriage, the regulatory elements are the "
            "signals, and the validation assays are the stations where the scientist checks that the "
            "cargo arrived intact. If one signal is misunderstood, the whole journey can look successful "
            "on paper while failing biologically.</p>"
        ),
        "<h3>Key ideas for students</h3>",
        (
            "<ul>"
            "<li><strong>Design logic:</strong> What question does the construct answer, and what part of the system is being measured?</li>"
            "<li><strong>Context:</strong> Is the work about a plasmid, reporter, viral vector, pseudotyped system, cell-free assay, or clinical sample?</li>"
            "<li><strong>Controls:</strong> Which comparison tells the reader that the observed signal is real and not a cloning or assay artifact?</li>"
            "<li><strong>Verification:</strong> What evidence shows that the intended sequence, orientation, and reading frame were preserved?</li>"
            "<li><strong>Biosafety:</strong> Which parts of the workflow require institutional review, containment rules, or approved SOPs?</li>"
            "</ul>"
        ),
        "<h3>How to read the literature</h3>",
        (
            "<p>When reading papers on this topic, start with the figure that shows construct design "
            "or experimental logic. Then move backward to the methods overview and forward to the "
            "validation data. This habit helps students separate the central biological claim from "
            "the many technical choices that support it. A beautiful cloning workflow is not just a "
            "list of steps; it is an argument that the molecule being tested is the molecule the authors "
            "intended to build.</p>"
        ),
        "<h3>Methods and protocol overview</h3>",
        (
            "<p>For students, the methods section should read like a map of decisions rather than a "
            "recipe. In molecular cloning and virology communication, the useful questions are: What "
            "molecule or model is being built? Which safer model system is appropriate for teaching? "
            "How will the construct be checked? What result would support the hypothesis, and what "
            "result would show that the system failed?</p>"
        ),
        (
            "<ul>"
            "<li>Define the biological question, construct architecture, and non-pathogenic model system before selecting a cloning workflow.</li>"
            "<li>List positive, negative, and sequence-confirmation controls in the article so readers can evaluate experimental logic.</li>"
            "<li>Explain what must be verified before interpreting downstream virology data: identity, orientation, integrity, expression, and assay background.</li>"
            "<li>Separate conceptual workflow discussion from lab-specific operating conditions, which should come from validated institutional SOPs.</li>"
            "<li>Include biosafety context when viral vectors, infectious clones, or primary specimens are discussed.</li>"
            "</ul>"
        ),
        "<h3>Worked example for students</h3>",
        (
            f"<p>Imagine a student reading about {safe_topic} for the first time. A helpful example "
            "would not begin with temperatures, incubation times, or reagent volumes. It would begin "
            "with the purpose: a researcher wants to compare whether a genetic design produces the "
            "expected reporter or expression readout in a safer teaching system. The student should "
            "then identify the insert, the vector backbone, the control construct, the verification "
            "method, and the interpretation rule before thinking about any lab-specific execution.</p>"
        ),
        (
            "<p>This style of example teaches the scientific logic without turning the post into an "
            "unreviewed operating protocol. It also helps readers understand why sequence confirmation, "
            "negative controls, and biological replicates are not decorative details; they are the "
            "guardrails that keep a result from becoming a misleading story.</p>"
        ),
        "<h3>Expected results and interpretation</h3>",
        (
            "<p>A well-designed workflow should produce evidence that lines up across levels. The "
            "molecular check should support the intended construct identity. The control comparison "
            "should show that background signal is understood. The biological readout should answer "
            "the original question without overclaiming. If these layers disagree, the right conclusion "
            "is not failure; it is an invitation to troubleshoot design, verification, or assay context.</p>"
        ),
        "<h3>Common mistakes to watch for</h3>",
        (
            "<p>Common beginner mistakes include treating a colony, band, fluorescence signal, or PCR "
            "result as final proof without checking whether the construct sequence and biological "
            "readout agree. Another common issue is writing protocols as if all systems are interchangeable. "
            "In reality, a cloning decision that is harmless in a teaching plasmid can carry very different "
            "biosafety meaning in a virology context.</p>"
        ),
        "<h3>What the cited work suggests</h3>",
        _render_literature_summary(literature),
        *(_render_deep_research_notes(literature) if deep_research else []),
        "<h3>Conclusions</h3>",
        (
            f"<p>The practical lesson for {safe_topic} is to keep the molecular story visible. "
            "A strong post should help students see how the design, controls, validation, and safety "
            "review fit together. Once that map is clear, the technical details become easier to learn "
            "from an approved protocol or supervised laboratory SOP.</p>"
        ),
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
    return BlogDraft(title=title, html="\n".join(body), labels=config.default_labels)


def _render_figures(images: Iterable[ImageResult]) -> list[str]:
    image_list = list(images)
    if not image_list:
        return []
    rendered: list[str] = ["<h3>Additional open-license images</h3>"]
    for image in image_list:
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


def _with_required_visuals(
    draft_html: str,
    topic: str,
    literature: list[LiteratureResult],
    images: list[ImageResult],
) -> str:
    visuals = "\n".join([*_render_generated_diagram(topic, literature), *_render_figures(images)])
    if not draft_html.strip():
        return visuals
    if "</h2>" in draft_html:
        return draft_html.replace("</h2>", f"</h2>\n{visuals}", 1)
    return f"{visuals}\n{draft_html}"


def _render_generated_diagram(topic: str, literature: list[LiteratureResult]) -> list[str]:
    topic_label = _svg_text(topic, 42)
    evidence_label = _svg_text(_evidence_label(literature), 38)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="920" height="420" viewBox="0 0 920 420" role="img" aria-labelledby="title desc">
  <title id="title">Concept map for {html.escape(topic_label)}</title>
  <desc id="desc">A teaching diagram connecting the topic to construct design, controls, validation, interpretation, and safety review.</desc>
  <defs>
    <marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#2d5f8b" />
    </marker>
  </defs>
  <rect width="920" height="420" rx="24" fill="#f5fbff" />
  <rect x="35" y="28" width="850" height="70" rx="18" fill="#d8ecff" stroke="#2d5f8b" stroke-width="2" />
  <text x="460" y="58" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="#17324d">{html.escape(topic_label)}</text>
  <text x="460" y="82" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#17324d">student map: from molecular design to safe interpretation</text>
  <rect x="50" y="155" width="160" height="82" rx="16" fill="#ffffff" stroke="#70a9d7" stroke-width="2" />
  <text x="130" y="184" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="#17324d">1. Design</text>
  <text x="130" y="207" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#17324d">question + construct</text>
  <rect x="270" y="155" width="160" height="82" rx="16" fill="#ffffff" stroke="#70a9d7" stroke-width="2" />
  <text x="350" y="184" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="#17324d">2. Controls</text>
  <text x="350" y="207" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#17324d">compare signal vs noise</text>
  <rect x="490" y="155" width="160" height="82" rx="16" fill="#ffffff" stroke="#70a9d7" stroke-width="2" />
  <text x="570" y="184" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="#17324d">3. Verify</text>
  <text x="570" y="207" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#17324d">sequence + identity</text>
  <rect x="710" y="155" width="160" height="82" rx="16" fill="#ffffff" stroke="#70a9d7" stroke-width="2" />
  <text x="790" y="184" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="#17324d">4. Interpret</text>
  <text x="790" y="207" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#17324d">biology, not artifact</text>
  <line x1="210" y1="196" x2="270" y2="196" stroke="#2d5f8b" stroke-width="3" marker-end="url(#arrow)" />
  <line x1="430" y1="196" x2="490" y2="196" stroke="#2d5f8b" stroke-width="3" marker-end="url(#arrow)" />
  <line x1="650" y1="196" x2="710" y2="196" stroke="#2d5f8b" stroke-width="3" marker-end="url(#arrow)" />
  <rect x="155" y="300" width="610" height="68" rx="18" fill="#fff5df" stroke="#d59b2d" stroke-width="2" />
  <text x="460" y="327" text-anchor="middle" font-family="Arial, sans-serif" font-size="17" font-weight="700" fill="#5a3b00">Safety and SOP review sits under the whole workflow</text>
  <text x="460" y="350" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#5a3b00">{html.escape(evidence_label)}</text>
</svg>"""
    data_uri = "data:image/svg+xml;utf8," + quote(svg)
    figures = [
        "<h3>Visual explanation</h3>",
        (
            "<figure>"
            f'<img src="{data_uri}" alt="Concept map for {html.escape(topic, quote=True)}" '
            'style="max-width:100%;height:auto;" />'
            "<figcaption>Generated teaching schematic: the topic is framed as a concept map linking design, controls, verification, interpretation, and biosafety review.</figcaption>"
            "</figure>"
        ),
    ]
    figures.extend(_render_methods_diagram(topic))
    figures.extend(_render_results_diagram())
    return figures


def _render_methods_diagram(topic: str) -> list[str]:
    topic_label = _svg_text(topic, 36)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="920" height="360" viewBox="0 0 920 360" role="img">
  <rect width="920" height="360" rx="24" fill="#fffdf6" />
  <text x="460" y="42" text-anchor="middle" font-family="Arial, sans-serif" font-size="23" font-weight="700" fill="#303030">Protocol-planning ladder</text>
  <text x="460" y="70" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#303030">{html.escape(topic_label)} as a safe teaching workflow</text>
  <rect x="70" y="112" width="170" height="90" rx="16" fill="#e8f5e9" stroke="#4c9f50" stroke-width="2" />
  <text x="155" y="145" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#1b5e20">Question</text>
  <text x="155" y="170" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#1b5e20">What are we trying</text>
  <text x="155" y="188" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#1b5e20">to learn?</text>
  <rect x="280" y="112" width="170" height="90" rx="16" fill="#e3f2fd" stroke="#1976d2" stroke-width="2" />
  <text x="365" y="145" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#0d47a1">Model</text>
  <text x="365" y="170" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#0d47a1">Choose safer system</text>
  <text x="365" y="188" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#0d47a1">for learning</text>
  <rect x="490" y="112" width="170" height="90" rx="16" fill="#f3e5f5" stroke="#8e24aa" stroke-width="2" />
  <text x="575" y="145" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#4a148c">Controls</text>
  <text x="575" y="170" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#4a148c">Positive, negative,</text>
  <text x="575" y="188" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#4a148c">verification</text>
  <rect x="700" y="112" width="170" height="90" rx="16" fill="#fff3e0" stroke="#ef6c00" stroke-width="2" />
  <text x="785" y="145" text-anchor="middle" font-family="Arial, sans-serif" font-size="16" font-weight="700" fill="#7b3f00">SOP review</text>
  <text x="785" y="170" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#7b3f00">Use approved local</text>
  <text x="785" y="188" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" fill="#7b3f00">protocols only</text>
  <path d="M240 157 H280 M450 157 H490 M660 157 H700" stroke="#555" stroke-width="3" stroke-dasharray="7 5" />
  <rect x="140" y="250" width="640" height="56" rx="16" fill="#ffffff" stroke="#777" stroke-width="1.8" />
  <text x="460" y="283" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" fill="#303030">Good methods writing explains decisions, controls, and interpretation before lab-specific execution.</text>
</svg>"""
    return [
        (
            "<figure>"
            f'<img src="data:image/svg+xml;utf8,{quote(svg)}" alt="Protocol-planning ladder" '
            'style="max-width:100%;height:auto;" />'
            "<figcaption>Generated teaching schematic: protocol planning is shown as a ladder from question to model, controls, and SOP review.</figcaption>"
            "</figure>"
        )
    ]


def _render_results_diagram() -> list[str]:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="920" height="360" viewBox="0 0 920 360" role="img">
  <rect width="920" height="360" rx="24" fill="#f9f7ff" />
  <text x="460" y="44" text-anchor="middle" font-family="Arial, sans-serif" font-size="23" font-weight="700" fill="#28204a">How to interpret results</text>
  <text x="460" y="72" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#28204a">A student-friendly triangle for deciding whether the story is reliable</text>
  <polygon points="460,105 220,285 700,285" fill="#ffffff" stroke="#6a5acd" stroke-width="3" />
  <circle cx="460" cy="128" r="48" fill="#e8e1ff" stroke="#6a5acd" stroke-width="2" />
  <text x="460" y="124" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#28204a">Molecular</text>
  <text x="460" y="144" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#28204a">evidence</text>
  <circle cx="270" cy="265" r="48" fill="#e1f5fe" stroke="#0288d1" stroke-width="2" />
  <text x="270" y="261" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#014d75">Control</text>
  <text x="270" y="281" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#014d75">logic</text>
  <circle cx="650" cy="265" r="48" fill="#e8f5e9" stroke="#43a047" stroke-width="2" />
  <text x="650" y="261" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#1b5e20">Biological</text>
  <text x="650" y="281" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#1b5e20">readout</text>
  <text x="460" y="246" text-anchor="middle" font-family="Arial, sans-serif" font-size="15" fill="#28204a">Trust the conclusion only when all three corners agree.</text>
</svg>"""
    return [
        (
            "<figure>"
            f'<img src="data:image/svg+xml;utf8,{quote(svg)}" alt="Results interpretation triangle" '
            'style="max-width:100%;height:auto;" />'
            "<figcaption>Generated teaching schematic: reliable interpretation requires agreement between molecular evidence, controls, and biological readout.</figcaption>"
            "</figure>"
        )
    ]


def _evidence_label(literature: list[LiteratureResult]) -> str:
    for paper in literature:
        if paper.year and paper.title:
            return f"Evidence checkpoint: compare draft claims against cited work such as {paper.year} literature."
    return "Evidence checkpoint: compare draft claims against references before publishing."


def _svg_text(value: str, limit: int) -> str:
    compact = re.sub(r"\s+", " ", value).strip()
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


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


def _render_deep_research_notes(literature: list[LiteratureResult]) -> list[str]:
    if not literature:
        return []

    items = []
    for paper in literature[5:12]:
        items.append(
            "<li>"
            f"{html.escape(paper.title)} "
            f"({html.escape(paper.year or 'n.d.')})"
            "</li>"
        )
    if not items:
        return []

    return [
        "<h3>Additional papers reviewed in deep mode</h3>",
        (
            "<p>Deep mode reviews a wider set of papers so the draft can connect the main topic "
            "to nearby methods, validation strategies, and teaching examples. These extra papers "
            "should be checked during editorial review before the final post is published.</p>"
        ),
        "<ul>" + "\n".join(items) + "</ul>",
    ]


def _render_references(literature: list[LiteratureResult]) -> str:
    if not literature:
        return "<p>References to be added during editorial review.</p>"
    return "<ol>" + "\n".join(
        f"<li>{html.escape(item.citation)}</li>" for item in literature[:12]
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
