#!/usr/bin/env bash
# Produce the next Bench Notes science-update draft for The Pipettes Solution.
# Re-run anytime — the theme queue rotates and never empties.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export PATH="${HOME}/.local/bin:${PATH}"
export DRAFT_DIR="${DRAFT_DIR:-content/science-updates}"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

EXTRA_ARGS=()
if [[ "${1:-}" == "--upload" || "${1:-}" == "--email" ]]; then
  EXTRA_ARGS+=("$1")
fi

python3 -m blogger_agent.cli science-next "${EXTRA_ARGS[@]}"

echo
echo "Paste-ready HTML is under ${DRAFT_DIR}/"
echo "Publish steps: content/science-updates/README.md"
echo "Blog: https://thepipettesolution.blogspot.com/"
