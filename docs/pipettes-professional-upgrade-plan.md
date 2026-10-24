# Pipettes Solution — professional upgrade plan

Goal: make https://thepipettesolution.blogspot.com/ clearly more polished and useful than https://www.zubairkhalid.com/ for a lab audience — original Pipettes design (inspiration-only IA).

## Status snapshot (2026-10-24)

| Layer | State |
|-------|--------|
| Audit / plan / mockups / packs | **Complete** (store + mirrored to git PR branch) |
| Live Blogger apply | **Blocked** — auth exhausted on VM; low-frequency silent probes only |
| Offline polish | **In progress** — a11y, mobile, tools depth, draft paste cards |

## Live vs paste-ready

| Deliverable | Live | Paste-ready path |
|-------------|------|------------------|
| Theme CSS | No | `blogger-theme/tps-professional-shell.css` or `paste-order/01-*.css` |
| Homepage shell | No (old welcome) | `tps-homepage-ALL-IN-ONE.html` / `paste-order/02-*.html` |
| About page | 404 | `tps-about-page.html` / `paste-order/03-*.html` |
| Nav | Mixed | `tps-nav-linklist.txt` / `paste-order/04-*.txt` |
| Footer | Default | `tps-footer-gadget.html` / `paste-order/05-*.html` |
| Lab tools page | Partial (calcs exist) | `tps-tools-page.html` (categorized) |
| Kan/SOC draft | Not on blog | `paste-order/06-kan-soc-*` + `DRAFTS-PASTE-READY.md` |

Apply clicks: `blogger-theme/APPLY.md` · Checklist: `CHECKLIST.md`

## Stage checklist

### A — Audit & gap map
- [x] `zubair-inspiration-audit.md`
- [x] This plan

### B — Theme / homepage / nav
- [x] Shell CSS + ALL-IN-ONE + mockups + screenshots
- [x] Mobile / a11y / motion polish (focus-visible, 44px CTAs, landscape hero)
- [x] Tools page depth (categories + SOP note)

### C — Content system
- [x] About, footer, post template, labels, nav
- [ ] Live apply (auth exhausted)

### D — Quality pass
- [x] Quality compare with live vs paste-ready table
- [x] Media evidence set

### E — Draft backlog
- [x] Paste-ready cards for Kan/SOC (+ high-value index)
- [ ] Upload when session exists (draft-only)

## Brand tokens (locked)

```css
--tps-navy: #0b2f5c;
--tps-teal: #0f766e;
--tps-ink: #0b1220;
--tps-muted: #4a5a6a;
--tps-wash: #e8f1f4;
--tps-line: #c5d5de;
```

Fonts: IBM Plex Sans + Source Serif 4.

## Auth policy

Do not ask the user. Keep 15‑minute silent probes. Prefer offline pack permanence in git until session returns.
