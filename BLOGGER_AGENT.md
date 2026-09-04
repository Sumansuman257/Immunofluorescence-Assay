# The Pipette Solution Blogger Draft Agent

This local agent researches molecular cloning and virology topics, writes a cited Blogger-ready HTML draft, and can upload the post to `thepipettesolution.blogspot.com` as an unpublished Blogger draft.

The default workflow is intentionally draft-first: a scientist should review the citations, image licenses, biosafety language, and any protocol-related claims before publishing.

## What it does

- Takes a title or topic from the command line or a daily topic queue.
- Searches Europe PMC for relevant papers.
- Searches Wikimedia Commons for open-license illustrative images.
- Writes a longer 900-1200 word educational draft target by default when LLM writing is configured.
- Always embeds a generated concept-map image so visual explanations are not missed.
- Adds references and image attribution.
- Saves a local HTML copy in `drafts/`.
- Optionally uploads the content to Blogger with `isDraft=True`.
- Optionally emails the content to Blogger's private post-by-email address so you can avoid Google Cloud setup.

If you add a Gemini API key and model in `.env`, the agent asks Gemini to write a more polished article. Without Gemini, it can use an OpenAI-compatible model if configured. Without either key, it still creates a structured cited draft using a local template.

The built-in template is written for students: it includes visual explanation, introduction, key ideas, literature-reading guidance, protocol-planning notes, common mistakes, conclusions, safety note, and references.

For major teaching posts, use deep mode. Deep mode retrieves more papers and images, targets a longer article, and uses a full structure: introduction, methods and protocol overview, worked example, expected results and interpretation, common mistakes, conclusions, safety note, and references.

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

Skip this section if you prefer the no-Google-Cloud email method below.

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

For a shorter or longer LLM-assisted article, override the target:

```bash
pipette-blogger-agent draft \
  --topic "Golden Gate cloning for viral vector design" \
  --words "1500-1800"
```

For a longer student-focused article with more research and more generated teaching figures:

```bash
pipette-blogger-agent draft \
  --topic "Golden Gate cloning for viral vector design" \
  --deep
```

## Upload as a Blogger draft

```bash
pipette-blogger-agent draft \
  --topic "Golden Gate cloning for viral vector design" \
  --upload
```

The Blogger API call uses `isDraft=True`, so the post is created as a draft, not published.

## No-credit-card option: email drafts to Blogger

Blogger has a "post using email" feature. You can configure it to save emailed posts as drafts.

In Blogger:

1. Open your blog dashboard.
2. Go to **Settings**.
3. Find **Email**.
4. Find **Post using email**.
5. Create your private Blogger email address.
6. Choose the option that saves emailed posts as **drafts**.

Then edit `.env`:

```bash
BLOGGER_EMAIL_TO=your-private-blogger-address@blogger.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-gmail-address@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM=your-gmail-address@gmail.com
```

For Gmail, use an app password rather than your normal Google password:

1. Turn on 2-Step Verification for your Google account.
2. Open Google Account settings.
3. Search for **App passwords**.
4. Create an app password for Mail.
5. Paste that app password into `SMTP_PASSWORD`.

Send one generated article to Blogger's email draft inbox:

```bash
pipette-blogger-agent draft \
  --topic "Golden Gate cloning for viral vector design" \
  --email \
  --deep
```

This method does not use Google Cloud or the Blogger API. Keep your private Blogger email address secret because anyone who knows it could send posts to your blog.

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

Or use the email method:

```bash
pipette-blogger-agent run-next --email
```

For deeper daily drafts:

```bash
pipette-blogger-agent run-next --email --deep
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

### Gemini writing and image generation

If you like Gemini's writing style, use Gemini for the main article.

1. Open Google AI Studio.
2. Create an API key if your account supports it.
3. Add the key and model names to `.env`.

Example:

```bash
GEMINI_API_KEY=your_gemini_key
GEMINI_TEXT_MODEL=your_gemini_text_model
```

If your Gemini account has an image-generation model, you can also add:

```bash
GEMINI_IMAGE_MODEL=your_gemini_image_model
GEMINI_IMAGE_COUNT=2
```

When Gemini is configured, use deep mode for the best article:

```bash
pipette-blogger-agent draft \
  --topic "Golden Gate cloning for viral vector design" \
  --email \
  --deep
```

The agent still adds its own generated teaching schematics and open-license Wikimedia images, so visuals are included even if Gemini image generation is unavailable.

### OpenAI-compatible writing

Set these in `.env`:

```bash
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=your_preferred_chat_model
```

The agent will then use the configured model for more fluid prose, while keeping the same draft-first and biosafety-aware instructions.
