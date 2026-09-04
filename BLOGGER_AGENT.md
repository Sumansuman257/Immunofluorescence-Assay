# The Pipette Solution Blogger Draft Agent

This local agent researches molecular cloning and virology topics, writes a cited Blogger-ready HTML draft, and can upload the post to `thepipettesolution.blogspot.com` as an unpublished Blogger draft.

The default workflow is intentionally draft-first: a scientist should review the citations, image licenses, biosafety language, and any protocol-related claims before publishing.

## What it does

- Takes a title or topic from the command line or a daily topic queue.
- Searches Europe PMC for relevant papers.
- Searches Wikimedia Commons for open-license illustrative images.
- Writes a 300-500 word educational draft by default.
- Adds references and image attribution.
- Saves a local HTML copy in `drafts/`.
- Optionally uploads the content to Blogger with `isDraft=True`.

If you add an OpenAI-compatible API key and model in `.env`, the agent asks the model to write a more polished article. Without that key, it still creates a structured cited draft using a local template.

## Safety note for virology content

The agent is configured for educational scientific communication. It avoids step-by-step instructions for engineering, recovering, propagating, optimizing, or enhancing viruses or pathogens. For protocol-related articles, it produces protocol-planning notes, controls, decision points, and references to institution-approved SOPs instead of operational wet-lab conditions.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
cp .env.example .env
```

Edit `.env` if needed. The default blog URL is already:

```bash
BLOGGER_BLOG_URL=https://thepipettesolution.blogspot.com
```

## Blogger authorization

1. Open Google Cloud Console.
2. Enable the Blogger API.
3. Create an OAuth Client ID for a Desktop app.
4. Download the client JSON as `client_secret.json` in this repo folder.
5. Run:

```bash
pipette-blogger-agent auth
```

This opens a browser login on your local computer and saves `token.json`. Both files are ignored by git.

## Generate one local draft

```bash
pipette-blogger-agent draft \
  --topic "Golden Gate cloning for viral vector design"
```

This saves an HTML file in `drafts/` and does not upload.

## Upload as a Blogger draft

```bash
pipette-blogger-agent draft \
  --topic "Golden Gate cloning for viral vector design" \
  --upload
```

The Blogger API call uses `isDraft=True`, so the post is created as a draft, not published.

## Daily topic queue

Create a local topic queue:

```bash
mkdir -p data
cp data/topics.txt.example data/topics.txt
```

Add one topic per line. The daily command consumes the first non-comment line:

```bash
pipette-blogger-agent run-next --upload
```

## Run daily on a local computer

Open your crontab:

```bash
crontab -e
```

Add a line like this, replacing `/path/to/repo` with your local folder:

```cron
0 8 * * * cd /path/to/repo && . .venv/bin/activate && pipette-blogger-agent run-next --upload >> blogger-agent.log 2>&1
```

That creates one Blogger draft every day at 08:00 local machine time when topics remain in `data/topics.txt`.

## Preview research before drafting

```bash
pipette-blogger-agent research \
  --topic "Reverse genetics systems in RNA virus research"
```

Use this to inspect the papers retrieved before generating a post.

## Optional LLM writing

Set these in `.env`:

```bash
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=your_preferred_chat_model
```

The agent will then use the configured model for more fluid prose, while keeping the same draft-first and biosafety-aware instructions.
