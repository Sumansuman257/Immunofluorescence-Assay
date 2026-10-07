# Science updates for The Pipettes Solution

Ready-to-paste Blogger HTML for [thepipettesolution.blogspot.com](https://thepipettesolution.blogspot.com/).

## Latest draft

- `2026-10-07-bench-notes-plasmid-assembly-pei-delivery-and-fluorescent-readout.html` — Bench Notes roundup with Europe PMC DOIs
- `preview.html` — local browser preview wrapper

## Publish

1. Open Blogger → The Pipettes Solution → **New post**.
2. Switch to **HTML** view and paste the dated draft file contents.
3. Title: keep the `Bench Notes: …` headline.
4. Labels: `science update`, `molecular cloning`, `lab methods`, `research highlights`.
5. Review citations/abstracts, then **Publish** (or save as draft first).

Or regenerate and upload via the agent (requires OAuth or post-by-email setup):

```bash
pipette-blogger-agent draft \
  --topic "Bench Notes: plasmid assembly, PEI delivery, and fluorescent readout" \
  --science-update \
  --upload
```
