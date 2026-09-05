# Kairos — Temporal Command Calendar

An advanced, fully customizable HTML calendar with living event popups, conflict radar, natural-language capture, and a unique **Orbit** day view.

## Open it

```bash
cd calendar
python3 -m http.server 8765
```

Then visit [http://localhost:8765](http://localhost:8765).

Or open `calendar/index.html` directly in Chrome or Edge.

## Highlights

- **Views:** Month, Week, Day, Agenda, and Orbit (radial day map)
- **Popups:** Toast alerts, fullscreen pulse modal, optional browser notifications + chime
- **Quick capture:** `Dentist tomorrow 3pm 45m`
- **Theme forge:** Colors, fonts, density, radius, motion, alert style
- **Conflict radar:** Overlapping events detected automatically
- **Command palette:** `Ctrl/Cmd + K`
- **Persistence:** Saved in your browser (`localStorage`) with JSON import/export
- **Recurring events:** Daily / weekly / monthly

## Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + K` | Command palette |
| `Ctrl/Cmd + N` | New event |
| Double-click time grid | Create event at that hour |

## Privacy

Everything stays local in your browser. No server, no account, no tracking.
