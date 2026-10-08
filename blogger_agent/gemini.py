from __future__ import annotations

import base64
import json
from typing import Any

import requests

from blogger_agent.config import AgentConfig
from blogger_agent.research import ImageResult, LiteratureResult


def generate_gemini_draft_json(
    topic: str,
    literature: list[LiteratureResult],
    images: list[ImageResult],
    config: AgentConfig,
    requested_words: str,
    deep_research: bool,
) -> dict[str, Any]:
    if not config.gemini_api_key or not config.gemini_text_model:
        raise RuntimeError("Gemini text generation requires GEMINI_API_KEY and GEMINI_TEXT_MODEL.")

    system = (
        "You are a careful scientific educator writing for virology and molecular biology students. "
        "Write in a natural human teaching voice with clear examples, analogies, and precise citations. "
        "Do not provide operational wet-lab instructions for engineering, recovering, propagating, "
        "optimizing, or enhancing viruses or pathogens. Protocol content must remain a safe planning "
        "overview that points to institution-approved SOPs for execution."
    )
    user_payload = {
        "topic": topic,
        "target_words": requested_words,
        "deep_research": deep_research,
        "required_sections": [
            "Introduction",
            "Methods and protocol overview",
            "Worked example",
            "Expected results and interpretation",
            "Common mistakes",
            "Conclusions",
            "Safety note",
            "References",
        ],
        "style": (
            "Human, detailed, student-friendly, beautifully explained, example-driven, "
            "and useful for exam preparation and beginner researchers."
        ),
        "literature": [
            {
                "title": item.title,
                "authors": item.authors,
                "year": item.year,
                "journal": item.journal,
                "doi": item.doi,
                "abstract": item.abstract[:1600],
                "citation": item.citation,
            }
            for item in literature
        ],
        "available_images": [
            {
                "title": item.title,
                "url": item.url,
                "attribution": item.attribution_html,
            }
            for item in images
        ],
        "output": (
            "Return strict JSON only with keys title, labels, html. "
            "The html must be Blogger-ready HTML, include references, and mention where each figure belongs."
        ),
    }

    response = requests.post(
        _gemini_model_url(config, config.gemini_text_model),
        params={"key": config.gemini_api_key},
        json={
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": json.dumps(user_payload)}]}],
            "generationConfig": {
                "temperature": 0.55,
                "responseMimeType": "application/json",
            },
        },
        timeout=120,
    )
    response.raise_for_status()
    return _extract_json(response.json())


def generate_gemini_images(
    topic: str,
    config: AgentConfig,
    count_override: int | None = None,
) -> list[ImageResult]:
    """Ask a Gemini image-capable model for student-friendly conceptual figures."""

    if not config.gemini_api_key or not config.gemini_image_model:
        return []

    prompts = [
        (
            f"Create a clean educational diagram for students about {topic}. "
            "Show conceptual relationships only. Avoid procedural wet-lab steps. "
            "Use labels such as design, controls, verification, interpretation, and safety."
        ),
        (
            f"Create a blog illustration for {topic} using a classroom teaching style. "
            "Use simple shapes, readable labels, and a calm scientific color palette. "
            "Avoid realistic pathogen manipulation or procedural instructions."
        ),
        (
            f"Create a protocol-planning overview image for {topic}. "
            "Show safe decision points: research question, model choice, controls, verification, "
            "data interpretation, and SOP review. Do not include reagent amounts, temperatures, "
            "timings, or operational steps."
        ),
        (
            f"Create a student results-interpretation figure for {topic}. "
            "Show how molecular evidence, controls, and biological readout must agree before "
            "a conclusion is trusted. Use a clean classroom infographic style."
        ),
        (
            f"Create a glossary-style visual for beginners learning {topic}. "
            "Use labeled cards for vector, insert, control, verification, readout, and biosafety."
        ),
        (
            f"Create a simple analogy illustration for {topic}. "
            "Use a railway or assembly-line metaphor to explain how design, controls, and validation "
            "connect. Keep it conceptual and safe."
        ),
    ]
    images: list[ImageResult] = []
    requested_count = max(count_override if count_override is not None else config.gemini_image_count, 0)
    selected_prompts = list(prompts)
    while len(selected_prompts) < requested_count:
        selected_prompts.append(
            f"Create an additional unique student-friendly teaching figure {len(selected_prompts) + 1} "
            f"for {topic}. Focus on a different conceptual angle than previous figures. "
            "Keep it high-level, safe, and free of procedural lab conditions."
        )

    for index, prompt in enumerate(selected_prompts[:requested_count], start=1):
        try:
            response = requests.post(
                _gemini_model_url(config, config.gemini_image_model),
                params={"key": config.gemini_api_key},
                json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
                },
                timeout=180,
            )
            response.raise_for_status()
        except requests.RequestException:
            continue

        for mime_type, data in _extract_inline_images(response.json()):
            images.append(
                ImageResult(
                    title=f"Gemini-generated teaching figure {index}",
                    url=f"data:{mime_type};base64,{data}",
                    page_url="https://ai.google.dev/gemini-api/docs/image-generation",
                    license_name="AI-generated image; review before publishing",
                    artist="Gemini",
                )
            )
            break
    return images


def _gemini_model_url(config: AgentConfig, model: str) -> str:
    return f"{config.gemini_base_url}/models/{model}:generateContent"


def _extract_json(payload: dict[str, Any]) -> dict[str, Any]:
    text = _extract_text(payload).strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        text = text.removesuffix("```").strip()
    return json.loads(text)


def _extract_text(payload: dict[str, Any]) -> str:
    for candidate in payload.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            if part.get("text"):
                return part["text"]
    raise RuntimeError("Gemini response did not contain text.")


def _extract_inline_images(payload: dict[str, Any]) -> list[tuple[str, str]]:
    images: list[tuple[str, str]] = []
    for candidate in payload.get("candidates", []):
        for part in candidate.get("content", {}).get("parts", []):
            inline_data = part.get("inlineData") or part.get("inline_data")
            if not inline_data:
                continue
            mime_type = inline_data.get("mimeType") or inline_data.get("mime_type") or "image/png"
            data = inline_data.get("data")
            if data and _is_base64(data):
                images.append((mime_type, data))
    return images


def _is_base64(value: str) -> bool:
    try:
        base64.b64decode(value, validate=True)
    except Exception:
        return False
    return True
