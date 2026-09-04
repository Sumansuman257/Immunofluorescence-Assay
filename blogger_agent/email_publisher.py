from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage

from blogger_agent.config import AgentConfig
from blogger_agent.writer import BlogDraft


@dataclass(frozen=True)
class EmailResult:
    to_address: str
    subject: str


def send_blogger_email_draft(config: AgentConfig, draft: BlogDraft) -> EmailResult:
    """Send a generated draft to Blogger's private post-by-email address."""

    _validate_email_config(config)
    message = build_blogger_email(config, draft)

    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(config.smtp_username, config.smtp_password)
        smtp.send_message(message)

    return EmailResult(to_address=config.blogger_email_to or "", subject=draft.title)


def build_blogger_email(config: AgentConfig, draft: BlogDraft) -> EmailMessage:
    """Build the MIME message separately so tests can validate formatting."""

    _validate_email_config(config)
    message = EmailMessage()
    message["From"] = config.smtp_from
    message["To"] = config.blogger_email_to
    message["Subject"] = draft.title

    plain_text = (
        "This post was generated as HTML by The Pipette Solution Blogger Agent. "
        "Open the Blogger draft editor to review formatting, citations, and safety notes."
    )
    message.set_content(plain_text)
    message.add_alternative(draft.html, subtype="html")
    return message


def _validate_email_config(config: AgentConfig) -> None:
    missing = []
    if not config.blogger_email_to:
        missing.append("BLOGGER_EMAIL_TO")
    if not config.smtp_username:
        missing.append("SMTP_USERNAME")
    if not config.smtp_password:
        missing.append("SMTP_PASSWORD")
    if not config.smtp_from:
        missing.append("SMTP_FROM or SMTP_USERNAME")
    if missing:
        joined = ", ".join(missing)
        raise RuntimeError(f"Missing email upload configuration: {joined}")
