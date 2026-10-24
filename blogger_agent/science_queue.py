from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScienceTheme:
    theme_id: str
    title: str
    queries: tuple[str, ...]


# Rotating Bench Notes packs for The Pipettes Solution.
# Each pack is designed to produce a distinct Europe PMC–backed roundup.
SCIENCE_THEMES: dict[str, ScienceTheme] = {
    "assembly-delivery-readout": ScienceTheme(
        theme_id="assembly-delivery-readout",
        title="Bench Notes: plasmid assembly, PEI delivery, and fluorescent readout",
        queries=(
            "CloneFast plasmid assembly phosphorothioate sticky ends",
            "PEI transfection plasmid DNA mammalian cells Expi293 OR ARPE",
            "immunofluorescence fluorescent nanobody labeling microscopy",
            "Golden Gate cloning plasmid assembly sequence verification",
        ),
    ),
    "sequencing-verification": ScienceTheme(
        theme_id="sequencing-verification",
        title="Bench Notes: sequence verification before you trust a clone",
        queries=(
            "plasmid sequence verification Nanopore OR Sanger cloning",
            "whole plasmid sequencing assembly error detection",
            "cloning quality control sequencing orientation reading frame",
            "reporter construct sequence confirmation molecular cloning",
        ),
    ),
    "transfection-expression": ScienceTheme(
        theme_id="transfection-expression",
        title="Bench Notes: transfection ratios, filler DNA, and expression trust",
        queries=(
            "PEI MAX transfection Expi293 transient gene expression",
            "plasmid DNA PEI polyplex transfection efficiency viability",
            "filler DNA salmon sperm transfection mammalian expression",
            "AAV vector production PEI transfection suspension cells",
        ),
    ),
    "fluorescence-imaging": ScienceTheme(
        theme_id="fluorescence-imaging",
        title="Bench Notes: fluorescent tags, nanobodies, and imaging controls",
        queries=(
            "fluorescent nanobody live cell imaging microscopy",
            "immunofluorescence secondary antibody controls background",
            "ALFA tag nanobody fluorescent protein detection",
            "multiplex fluorescence microscopy genetic tags EMcapsulin",
        ),
    ),
    "seamless-assembly": ScienceTheme(
        theme_id="seamless-assembly",
        title="Bench Notes: Gibson, In-Fusion, and seamless fragment logic",
        queries=(
            "Gibson assembly seamless cloning overlap design",
            "In-Fusion cloning multidomain fusion protein vector",
            "homology based DNA assembly fidelity verification",
            "modular cloning viral vector design Golden Gate",
        ),
    ),
    "miniprep-and-qc": ScienceTheme(
        theme_id="miniprep-and-qc",
        title="Bench Notes: plasmid prep quality and what the OD hides",
        queries=(
            "plasmid miniprep purity A260 A280 transfection quality",
            "plasmid DNA quality control endotoxin transfection",
            "alkaline lysis plasmid preparation troubleshooting",
            "plasmid topology supercoiled open circular transfection",
        ),
    ),
}

DEFAULT_QUEUE = tuple(SCIENCE_THEMES.keys())


def resolve_theme(theme_id_or_title: str) -> ScienceTheme:
    key = theme_id_or_title.strip()
    if key in SCIENCE_THEMES:
        return SCIENCE_THEMES[key]
    for theme in SCIENCE_THEMES.values():
        if theme.title.lower() == key.lower():
            return theme
    # Ad-hoc topic: use the string as title and as the primary query.
    return ScienceTheme(
        theme_id="custom",
        title=key if key.lower().startswith("bench notes") else f"Bench Notes: {key}",
        queries=(key, "molecular cloning plasmid validation controls"),
    )


def ensure_queue_file(path: Path, example_path: Path | None = None) -> None:
    """Create a rotating queue file if missing, copying from example when present."""

    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    if example_path and example_path.exists():
        path.write_text(example_path.read_text(encoding="utf-8"), encoding="utf-8")
        return
    lines = [
        "# Rotating science-update queue for The Pipettes Solution.",
        "# science-next consumes the first non-comment theme id and moves it to the bottom.",
        "",
        *DEFAULT_QUEUE,
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def peek_next_theme_id(path: Path) -> str | None:
    if not path.exists():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return None


def rotate_next_theme_id(path: Path) -> str | None:
    """Pop the first theme id and append it to the bottom so the queue never empties."""

    if not path.exists():
        return None

    lines = path.read_text(encoding="utf-8").splitlines()
    topic_index = None
    topic = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            topic_index = index
            topic = stripped
            break

    if topic_index is None or topic is None:
        return None

    remaining = lines[:topic_index] + lines[topic_index + 1 :]
    # Keep a blank line before recycled ids when the file ends with comments only.
    body = "\n".join(remaining).rstrip()
    recycled = f"{body}\n{topic}\n" if body else f"{topic}\n"
    path.write_text(recycled, encoding="utf-8")
    return topic


def append_manifest(manifest_path: Path, *, title: str, html_path: Path, theme_id: str, dois: list[str]) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    doi_text = ", ".join(dois) if dois else "(none retrieved)"
    entry = (
        f"- `{html_path.name}` — **{title}** "
        f"(theme `{theme_id}`; DOIs: {doi_text})\n"
    )
    if manifest_path.exists():
        existing = manifest_path.read_text(encoding="utf-8")
        if html_path.name in existing:
            return
        if not existing.endswith("\n"):
            existing += "\n"
        manifest_path.write_text(existing + entry, encoding="utf-8")
        return

    header = (
        "# Science update draft index\n\n"
        "Paste-ready HTML for [thepipettesolution.blogspot.com](https://thepipettesolution.blogspot.com/).\n"
        "Newest entries are appended at the bottom.\n\n"
    )
    manifest_path.write_text(header + entry, encoding="utf-8")
