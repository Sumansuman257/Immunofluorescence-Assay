# Prompt: Keep adding science updates to The Pipettes Solution

Copy everything below the line into a Cursor agent chat whenever you want the next Blogspot science update.

---

Keep updating **The Pipettes Solution** Blogspot with interesting science updates — again and again, not one-shot.

**Blog:** https://thepipettesolution.blogspot.com/  
**Repo:** `Sumansuman257/Immunofluorescence-Assay` (Blogger draft agent + `content/science-updates/`)  
**Branch/PR to keep current:** `cursor/blogspot-science-update-7c34` / PR #7 (or current science-update branch)

## Goal
Produce the **next** Bench Notes–style science-update draft: stronger voice, clear hierarchy, brand-forward navy/teal presentation (no generic AI purple/cream/broadsheet look). Cite **real** Europe PMC papers with DOIs — **never invent citations**.

## Do this
1. Prefer the repeatable flow:
   - `./scripts/produce-science-update.sh`  
   - or `python3 -m blogger_agent.cli science-next`  
   - or `pipette-blogger-agent draft --topic "Bench Notes: …" --science-update` with `DRAFT_DIR=content/science-updates`
2. Append new paste-ready HTML under `content/science-updates/` and update the draft index if present.
3. Rotate/advance the science-update queue (`data/science-updates.txt` from `data/science-updates.txt.example`) so the next run gets a different theme.
4. Commit + push on the science-update PR branch; keep the PR description current.
5. If you make UI/demo media, save under the Project store `media/` with verified paths.

## Publish (separate from code)
- **No Blogspot login in the agent** unless the owner already configured OAuth (`token.json`) or post-by-email (`BLOGGER_EMAIL_TO` + SMTP) in `.env`. Do not invent credentials.
- Default: leave **paste-ready HTML**; owner pastes into Blogger → New post → HTML view → labels `science update`, `molecular cloning`, `lab methods`, `research highlights` → review → Publish/draft.
- If auth is already configured locally: `--upload` (API draft) or `--email` (post-by-email draft) is OK.

## Cadence
When the user says “keep updating” / “add this again,” **run the next science update** (new theme, fresh papers), don’t redo the same post. Each run = one new Bench Notes draft ready to paste.

## Done when
- New file(s) in `content/science-updates/`
- PR updated
- Short note: what was added, how to re-run, publish blocker if any
