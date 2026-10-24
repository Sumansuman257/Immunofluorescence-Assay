from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from blogger_agent.blogger import authorize, create_blogger_draft
from blogger_agent.config import load_config
from blogger_agent.email_publisher import send_blogger_email_draft
from blogger_agent.gemini import generate_gemini_images
from blogger_agent.research import debug_search_url, search_images, search_literature
from blogger_agent.science_queue import (
    append_manifest,
    ensure_queue_file,
    resolve_theme,
    rotate_next_theme_id,
)
from blogger_agent.writer import SCIENCE_UPDATE_LABELS, BlogDraft, create_blog_draft, save_draft


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pipette-blogger-agent",
        description="Research, write, and upload Blogger drafts for The Pipette Solution.",
    )
    parser.add_argument("--env", default=None, help="Path to a .env file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    draft_parser = subparsers.add_parser("draft", help="Generate a draft from one topic.")
    draft_parser.add_argument("--topic", required=True, help="Title or topic to research.")
    draft_parser.add_argument("--words", default=None, help="Target length, for LLM mode.")
    draft_parser.add_argument("--deep", action="store_true", help="Use deeper research and a longer teaching structure.")
    draft_parser.add_argument(
        "--science-update",
        action="store_true",
        help="Write a cited science-highlights roundup for The Pipettes Solution.",
    )
    draft_parser.add_argument("--gemini-image-count", type=int, default=None, help="Override Gemini-generated image count.")
    draft_parser.add_argument("--upload", action="store_true", help="Upload to Blogger as a draft.")
    draft_parser.add_argument("--email", action="store_true", help="Email to Blogger's post-by-email draft address.")
    draft_parser.add_argument("--no-save", action="store_true", help="Do not save local HTML.")

    next_parser = subparsers.add_parser("run-next", help="Draft the next topic from a topics file.")
    next_parser.add_argument(
        "--topics-file",
        default="data/topics.txt",
        help="Plain-text queue with one topic per line.",
    )
    next_parser.add_argument("--words", default=None, help="Target length, for LLM mode.")
    next_parser.add_argument("--deep", action="store_true", help="Use deeper research and a longer teaching structure.")
    next_parser.add_argument(
        "--science-update",
        action="store_true",
        help="Write a cited science-highlights roundup for The Pipettes Solution.",
    )
    next_parser.add_argument("--gemini-image-count", type=int, default=None, help="Override Gemini-generated image count.")
    next_parser.add_argument("--upload", action="store_true", help="Upload to Blogger as a draft.")
    next_parser.add_argument("--email", action="store_true", help="Email to Blogger's post-by-email draft address.")

    subparsers.add_parser("auth", help="Authorize the local computer with Blogger.")

    research_parser = subparsers.add_parser("research", help="Preview research results for a topic.")
    research_parser.add_argument("--topic", required=True, help="Title or topic to research.")
    research_parser.add_argument("--limit", type=int, default=7, help="Maximum papers to return.")

    science_parser = subparsers.add_parser(
        "science-next",
        help="Generate the next rotating Bench Notes science-update draft.",
    )
    science_parser.add_argument(
        "--queue-file",
        default="data/science-updates.txt",
        help="Rotating theme-id queue (created from data/science-updates.txt.example if missing).",
    )
    science_parser.add_argument(
        "--output-dir",
        default="content/science-updates",
        help="Where to save paste-ready HTML (default: content/science-updates).",
    )
    science_parser.add_argument("--upload", action="store_true", help="Upload to Blogger as a draft.")
    science_parser.add_argument("--email", action="store_true", help="Email to Blogger's post-by-email draft address.")
    science_parser.add_argument(
        "--theme",
        default=None,
        help="Optional theme id or Bench Notes title (skips queue rotation when set).",
    )

    upload_parser = subparsers.add_parser(
        "upload-science-updates",
        help="Upload existing content/science-updates/*.html to Blogger as drafts (isDraft=True).",
    )
    upload_parser.add_argument(
        "--dir",
        default="content/science-updates",
        help="Directory of paste-ready HTML drafts.",
    )
    upload_parser.add_argument(
        "--email",
        action="store_true",
        help="Send via Blogger post-by-email instead of the API.",
    )
    upload_parser.add_argument(
        "--file",
        action="append",
        default=None,
        help="Optional specific HTML file (repeatable). Defaults to all dated Bench Notes HTML.",
    )

    args = parser.parse_args(argv)
    config = load_config(args.env)

    if args.command == "auth":
        authorize(config)
        print(f"Authorization complete. Token saved to {config.token_path}.")
        return 0

    if args.command == "research":
        literature = search_literature(args.topic, max_results=args.limit)
        print(json.dumps([paper.__dict__ for paper in literature], indent=2))
        print(f"\nEurope PMC query: {debug_search_url(args.topic)}")
        return 0

    if args.command == "draft":
        return _draft_topic(
            topic=args.topic,
            words=args.words,
            deep=args.deep,
            science_update=args.science_update,
            gemini_image_count=args.gemini_image_count,
            upload=args.upload,
            email_upload=args.email,
            save=not args.no_save,
            config=config,
        )

    if args.command == "run-next":
        topic = _pop_next_topic(Path(args.topics_file))
        if not topic:
            print(f"No queued topics found in {args.topics_file}.")
            return 0
        return _draft_topic(
            topic=topic,
            words=args.words,
            deep=args.deep,
            science_update=args.science_update,
            gemini_image_count=args.gemini_image_count,
            upload=args.upload,
            email_upload=args.email,
            save=True,
            config=config,
        )

    if args.command == "science-next":
        return _science_next(
            queue_file=Path(args.queue_file),
            output_dir=Path(args.output_dir),
            upload=args.upload,
            email_upload=args.email,
            theme_override=args.theme,
            config=config,
        )

    if args.command == "upload-science-updates":
        return _upload_science_updates(
            directory=Path(args.dir),
            files=args.file,
            email_upload=args.email,
            config=config,
        )

    parser.print_help()
    return 1


def _draft_topic(
    topic: str,
    words: str | None,
    deep: bool,
    science_update: bool,
    gemini_image_count: int | None,
    upload: bool,
    email_upload: bool,
    save: bool,
    config,
    queries: tuple[str, ...] | None = None,
    output_dir: Path | None = None,
    theme_id: str | None = None,
) -> int:
    if upload and email_upload:
        print("Choose either --upload for Blogger API or --email for Blogger post-by-email, not both.")
        return 2

    print(f"Researching: {topic}")
    if science_update:
        literature = _research_science_update(topic, queries=queries)
    else:
        literature = search_literature(topic, max_results=15 if deep else 7)

    images = [
        *generate_gemini_images(topic, config, count_override=gemini_image_count),
        *search_images(topic, max_results=6 if deep else 4),
    ]
    target_words = words or ("1800-2500" if deep else ("700-1000" if science_update else "900-1200"))
    draft = create_blog_draft(
        topic,
        literature,
        images,
        config,
        requested_words=target_words,
        deep_research=deep,
        science_update=science_update,
    )

    if save:
        draft_dir = output_dir or config.draft_dir
        path = save_draft(draft, draft_dir)
        print(f"Saved local draft: {path}")
        if science_update:
            dois = [paper.doi for paper in literature if paper.doi]
            append_manifest(
                Path(draft_dir) / "INDEX.md",
                title=draft.title,
                html_path=path,
                theme_id=theme_id or "science-update",
                dois=dois,
            )
            print(f"Updated manifest: {Path(draft_dir) / 'INDEX.md'}")

    if upload:
        result = create_blogger_draft(config, draft)
        print("Uploaded Blogger draft:")
        print(json.dumps({"id": result.get("id"), "url": result.get("url"), "title": result.get("title")}, indent=2))
    elif email_upload:
        result = send_blogger_email_draft(config, draft)
        print("Sent Blogger draft email:")
        print(json.dumps({"to": result.to_address, "subject": result.subject}, indent=2))
    else:
        print("Upload skipped. Add --upload for Blogger API or --email for Blogger post-by-email.")

    return 0


def _upload_science_updates(
    directory: Path,
    files: list[str] | None,
    email_upload: bool,
    config,
) -> int:
    """Push existing paste-ready HTML into Blogger as unpublished drafts only."""

    paths = _science_html_paths(directory, files)
    if not paths:
        print(f"No Bench Notes HTML found in {directory}.")
        return 1

    print(
        f"Uploading {len(paths)} file(s) to {config.blog_url} as Blogger drafts "
        f"(isDraft=True / post-by-email draft). Never publishes live."
    )

    results = []
    for path in paths:
        draft = _blog_draft_from_html(path, config)
        print(f"- {path.name} → {draft.title}")
        try:
            if email_upload:
                result = send_blogger_email_draft(config, draft)
                results.append(
                    {
                        "file": str(path),
                        "title": draft.title,
                        "method": "email",
                        "to": result.to_address,
                        "status": "sent as email draft (confirm in Blogger Drafts)",
                    }
                )
            else:
                result = create_blogger_draft(config, draft)
                results.append(
                    {
                        "file": str(path),
                        "title": draft.title,
                        "method": "api",
                        "id": result.get("id"),
                        "url": result.get("url"),
                        "status": "draft" if result.get("status") == "DRAFT" or result.get("id") else "uploaded",
                        "blogger_status": result.get("status"),
                    }
                )
        except FileNotFoundError as exc:
            print("\nBLOCKED: Blogger credentials missing.")
            print(str(exc))
            print(_credential_help())
            return 3
        except Exception as exc:  # noqa: BLE001 - surface setup failures clearly
            print(f"\nBLOCKED while uploading {path.name}: {exc}")
            print(_credential_help())
            return 3

    print(json.dumps(results, indent=2))
    print("\nConfirm in Blogger → Posts → Drafts. These should not appear as live posts.")
    return 0


def _science_html_paths(directory: Path, files: list[str] | None) -> list[Path]:
    if files:
        return [Path(item) for item in files]
    if not directory.exists():
        return []
    return sorted(
        path
        for path in directory.glob("*.html")
        if path.name.startswith("20") and "bench-notes" in path.name
    )


def _blog_draft_from_html(path: Path, config) -> BlogDraft:
    html = path.read_text(encoding="utf-8")
    match = re.search(r"<h2[^>]*>(.*?)</h2>", html, flags=re.IGNORECASE | re.DOTALL)
    if match:
        title = re.sub(r"<[^>]+>", "", match.group(1)).strip()
    else:
        title = path.stem.replace("-", " ").title()
    labels = tuple(dict.fromkeys([*SCIENCE_UPDATE_LABELS, *config.default_labels]))
    return BlogDraft(title=title, html=html, labels=labels)


def _credential_help() -> str:
    return """
Shortest owner steps to create Blogger drafts (not live posts):

Option A — Blogger API (recommended)
1. Google Cloud Console → enable Blogger API → create OAuth Desktop client.
2. Download JSON as client_secret.json in the repo root.
3. On a machine with a browser: pipette-blogger-agent auth
4. Copy token.json (and client_secret.json) into this environment, or run locally:
   python3 -m blogger_agent.cli upload-science-updates

Option B — Post by email (no Google Cloud)
1. Blogger → Settings → Email → Post using email → create address → save as Drafts.
2. Put in .env: BLOGGER_EMAIL_TO, SMTP_USERNAME, SMTP_PASSWORD (Gmail app password), SMTP_FROM.
3. python3 -m blogger_agent.cli upload-science-updates --email

Paste-ready HTML is already in content/science-updates/ if you prefer manual paste into Blogger Drafts.
""".strip()


def _science_next(
    queue_file: Path,
    output_dir: Path,
    upload: bool,
    email_upload: bool,
    theme_override: str | None,
    config,
) -> int:
    ensure_queue_file(queue_file, Path("data/science-updates.txt.example"))
    if theme_override:
        theme_key = theme_override
    else:
        theme_key = rotate_next_theme_id(queue_file)
        if not theme_key:
            print(f"No theme ids found in {queue_file}.")
            return 0

    theme = resolve_theme(theme_key)
    print(f"Science theme: {theme.theme_id}")
    return _draft_topic(
        topic=theme.title,
        words=None,
        deep=False,
        science_update=True,
        gemini_image_count=None,
        upload=upload,
        email_upload=email_upload,
        save=True,
        config=config,
        queries=theme.queries,
        output_dir=output_dir,
        theme_id=theme.theme_id,
    )


def _research_science_update(topic: str, queries: tuple[str, ...] | None = None):
    """Prefer theme-specific Europe PMC queries so roundups stay on-topic."""

    theme_queries = queries or (
        "CloneFast plasmid assembly phosphorothioate sticky ends",
        "PEI transfection plasmid DNA mammalian cells Expi293 OR ARPE",
        "immunofluorescence fluorescent nanobody labeling microscopy",
        "Golden Gate cloning plasmid assembly sequence verification",
        topic,
    )
    literature = []
    for query in theme_queries:
        for paper in search_literature(query, max_results=3):
            if paper.doi and any(existing.doi == paper.doi for existing in literature):
                continue
            if any(existing.title == paper.title for existing in literature):
                continue
            # Prefer recent papers for a newsy roundup voice.
            try:
                year = int(paper.year) if paper.year and paper.year.isdigit() else 0
            except ValueError:
                year = 0
            if year and year < 2022:
                continue
            literature.append(paper)
        if len(literature) >= 5:
            break
    return literature[:5]


def _pop_next_topic(path: Path) -> str | None:
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
    path.write_text("\n".join(remaining).rstrip() + ("\n" if remaining else ""), encoding="utf-8")
    return topic


if __name__ == "__main__":
    sys.exit(main())
