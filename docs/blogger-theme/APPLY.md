# Apply Pipettes professional shell on Blogspot

**Goal:** Replace the inset welcome-card homepage with a brand-first lab shell (navy `#0b2f5c` / teal `#0f766e`).  
**Rule:** Paste only files from this folder. Do not paste third-party site HTML.  
**Fast path:** numbered files in `paste-order/` (`01` … `06`) — same contents as the named packs below.

## Files (what each is for)

| # | File | Where it goes |
|---|------|----------------|
| 1 | `tps-professional-shell.css` | Theme → Customize → Advanced → **Add CSS** |
| 2 | `tps-homepage-ALL-IN-ONE.html` | Layout → HTML/JavaScript gadget **above Blog Posts** |
| 3 | `tps-about-page.html` | Pages → New/Edit **About** (HTML view) |
| 4 | `tps-nav-linklist.txt` | Header LinkList / Pages gadget (labels + URLs) |
| 5 | `tps-footer-gadget.html` | Layout → Footer HTML/JavaScript (optional) |
| 6 | `tps-post-template.html` | New Bench Notes posts (HTML view) |
| 7 | `tps-tools-page.html` | Optional Pages → Lab tools (`/p/lab-tools.html`) |
| — | `CHECKLIST.md` | Tick-box live apply checklist |
| — | `tps-shell-css-gadget.html` | Add CSS fallback |
| — | `tps-homepage-gadget.html` | Fallback if you already pasted shell CSS and want markup-only |
| — | `tps-label-taxonomy.md` | Label names for posts |
| — | `../../media/zubair-adapt/tps-home-mockup.html` | Offline preview (open in browser) |

## Exact order (do not skip)

### Step 1 — Theme CSS

1. Open [Blogger](https://www.blogger.com/) → blog **The Pipettes Solution**  
2. Left menu → **Theme** → **Customize**  
3. **Advanced** → **Add CSS**  
4. Select all existing custom CSS that conflicts with navy/teal (optional backup first)  
5. Paste **entire** contents of `tps-professional-shell.css`  
6. Click **Apply** (or Save), then **Back to Blogger**

**If Add CSS rejects length / `@import`:**  
Use ready fallback **`tps-shell-css-gadget.html`** — Layout → HTML/JavaScript titled `TPS Shell CSS`, place high above content. Still do Step 2 (ALL-IN-ONE).

### Step 2 — Homepage ALL-IN-ONE gadget (required)

1. **Layout**  
2. Find the HTML gadget that holds the old gray **Welcome** block — open it  
   - If none: **Add a gadget** → **HTML/JavaScript** → place **above** “Blog Posts”  
3. Delete old welcome HTML  
4. Paste **entire** `tps-homepage-ALL-IN-ONE.html` (includes its own `<style>` — that is intentional)  
5. Title gadget: `TPS Professional Home`  
6. If theme offers “show on homepage only”, enable it  
7. **Save** → **Save arrangement**

### Step 3 — About page

1. **Pages** → **New page** (or edit existing About)  
2. Title exactly: `About`  
3. Switch editor to **HTML** (not Compose)  
4. Paste entire `tps-about-page.html`  
5. Options / Permalink → custom: `about` → URL should be `/p/about.html`  
6. **Publish** (static page — OK live; posts stay draft-only)

### Step 4 — Science-first nav

1. **Layout** → open the header **LinkList** or **Pages** gadget  
2. Replace primary links with the five rows in `tps-nav-linklist.txt`  
3. Remove Softwares/Movies, Sports, Top Stories, Lok-Sewa / exam blocks from **primary** header  
4. Save arrangement  

### Step 5 — Footer (optional but recommended)

1. Layout → Footer → HTML/JavaScript  
2. Paste `tps-footer-gadget.html` → Save  

### Step 6 — Verify live

Open https://thepipettesolution.blogspot.com/ and check:

- [ ] First viewport is full-bleed navy→teal with **The Pipettes Solution** as the big brand  
- [ ] Two CTAs: Bench Notes + Lab tools  
- [ ] Lab tools grid appears below hero  
- [ ] Old gray welcome card is gone  
- [ ] Mobile: hero readable, CTAs tappable, tools stack  
- [ ] `/p/about.html` loads the new About  
- [ ] Post headings navy, links teal, no stray strikethrough  

Compare against mockups in `media/zubair-adapt/pipettes-mockup-*.png`.

## Draft backlog (after shell is live)

Kan/SOC teaching draft (draft-only, do not publish until reviewed):

- Quick card: **`kan-soc-PASTE-READY.md`** (title + labels + clicks)  
- HTML body: `../blogger-redesign-drafts/kan-soc-outgrowth-vs-amp.html`  
- Blogger → Posts → New post → HTML view → paste → **Save** (not Publish)

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Hero not full-bleed | Confirm ALL-IN-ONE pasted; hard-refresh (Ctrl/Cmd+Shift+R) |
| Old welcome still visible | Remove old welcome gadget HTML; shell CSS hides `.welcome-hero` when `.tps-pro-hero` exists |
| Fonts look generic | Keep Google Fonts `@import` / `<link>` in packs; allow fonts.googleapis.com |
| Theme Add CSS wiped gadgets | Re-paste ALL-IN-ONE; Add CSS only affects CSS, not Layout HTML |
| About 404 | Permalink must be `about`; publish the Page, not a Post |

## Brand tokens (locked)

```css
--tps-navy: #0b2f5c;
--tps-teal: #0f766e;
--tps-ink: #0b1220;
--tps-muted: #4a5a6a;
--tps-wash: #e8f1f4;
```

Fonts: IBM Plex Sans (UI) + Source Serif 4 (body).
