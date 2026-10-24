#!/usr/bin/env bash
# Upload existing Bench Notes HTML to The Pipettes Solution as Blogger DRAFTS only.
# Requires client_secret.json + token.json (API) or BLOGGER_EMAIL_TO + SMTP (--email).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export PATH="${HOME}/.local/bin:${PATH}"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

if [[ "${1:-}" == "--email" ]]; then
  python3 -m blogger_agent.cli upload-science-updates --email
else
  python3 -m blogger_agent.cli upload-science-updates
fi
