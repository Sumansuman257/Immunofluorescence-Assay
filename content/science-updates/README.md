# Science updates for The Pipettes Solution

Ready-to-paste Blogger HTML for [thepipettesolution.blogspot.com](https://thepipettesolution.blogspot.com/).

## Produce the next update (repeat anytime)

```bash
./scripts/produce-science-update.sh
# or
python3 -m blogger_agent.cli science-next
```

This rotates `data/science-updates.txt`, writes a new Bench Notes HTML file here, and appends `INDEX.md`.

Reusable Cursor agent prompt: [PROMPT.md](./PROMPT.md)

## Drafts

See [INDEX.md](./INDEX.md) for the full list. Seed draft:

- `2026-10-07-bench-notes-plasmid-assembly-pei-delivery-and-fluorescent-readout.html`

## Publish

1. Open Blogger → The Pipettes Solution → **New post**.
2. Switch to **HTML** view and paste a dated draft file’s contents.
3. Title: keep the `Bench Notes: …` headline.
4. Labels: `science update`, `molecular cloning`, `lab methods`, `research highlights`.
5. Review citations/abstracts, then **Publish** (or save as draft first).

### Upload existing HTML as Blogger drafts (not live)

Once credentials exist locally:

```bash
./scripts/upload-science-drafts.sh          # Blogger API, isDraft=True
./scripts/upload-science-drafts.sh --email  # post-by-email → Drafts
# or
python3 -m blogger_agent.cli upload-science-updates
```

Setup (pick one):

1. **API:** `client_secret.json` + `pipette-blogger-agent auth` → `token.json`
2. **Email:** Blogger Settings → Email → Post using email (save as drafts) + `.env` SMTP fields

Do not invent Blogspot credentials in cloud agents. Manual paste into Blogger → New post → save as draft also works.
