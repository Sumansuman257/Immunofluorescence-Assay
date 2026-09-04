from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from blogger_agent.blogger import authorize, create_blogger_draft
from blogger_agent.config import load_config
from blogger_agent.email_publisher import send_blogger_email_draft
from blogger_agent.research import debug_search_url, search_images, search_literature
from blogger_agent.writer import create_blog_draft, save_draft


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="pipette-blogger-agent",
        description="Research, write, and upload Blogger drafts for The Pipette Solution.",
    )
    parser.add_argument("--env", default=None, help="Path to a .env file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    draft_parser = subparsers.add_parser("draft", help="Generate a draft from one topic.")
    draft_parser.add_argument("--topic", required=True, help="Title or topic to research.")
    draft_parser.add_argument("--words", default="300-500", help="Target length, for LLM mode.")
    draft_parser.add_argument("--upload", action="store_true", help="Upload to Blogger as a draft.")
    draft_parser.add_argument("--email", action="store_true", help="Email to Blogger's post-by-email draft address.")
    draft_parser.add_argument("--no-save", action="store_true", help="Do not save local HTML.")

    next_parser = subparsers.add_parser("run-next", help="Draft the next topic from a topics file.")
    next_parser.add_argument(
        "--topics-file",
        default="data/topics.txt",
        help="Plain-text queue with one topic per line.",
    )
    next_parser.add_argument("--words", default="300-500", help="Target length, for LLM mode.")
    next_parser.add_argument("--upload", action="store_true", help="Upload to Blogger as a draft.")
    next_parser.add_argument("--email", action="store_true", help="Email to Blogger's post-by-email draft address.")

    subparsers.add_parser("auth", help="Authorize the local computer with Blogger.")

    research_parser = subparsers.add_parser("research", help="Preview research results for a topic.")
    research_parser.add_argument("--topic", required=True, help="Title or topic to research.")
    research_parser.add_argument("--limit", type=int, default=7, help="Maximum papers to return.")

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
            upload=args.upload,
            email_upload=args.email,
            save=True,
            config=config,
        )

    parser.print_help()
    return 1


def _draft_topic(topic: str, words: str, upload: bool, email_upload: bool, save: bool, config) -> int:
    if upload and email_upload:
        print("Choose either --upload for Blogger API or --email for Blogger post-by-email, not both.")
        return 2

    print(f"Researching: {topic}")
    literature = search_literature(topic)
    images = search_images(topic)
    draft = create_blog_draft(topic, literature, images, config, requested_words=words)

    if save:
        path = save_draft(draft, config.draft_dir)
        print(f"Saved local draft: {path}")

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
