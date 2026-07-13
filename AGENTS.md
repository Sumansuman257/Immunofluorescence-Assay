# AGENTS.md

## Cursor Cloud specific instructions

### What this repo is
A single, self-contained static web app: the **Immunofluorescence Assay Tracker** (a lab-protocol step timer). It is 100% client-side HTML/CSS/vanilla JS with **no backend, no database, no dependencies, no build step, and no tests**.

### Non-obvious gotcha
The entire application HTML lives inside `README.md` (despite the `.md` extension, its contents are a complete `<!DOCTYPE html>` document). There is no `index.html`. `README.md` will not render as a page over HTTP/`file://` because of its `.md` extension/MIME type, so to run it you must serve its contents as `index.html`.

### Running it in dev mode
There is nothing to install. Serve a copy of `README.md` as `index.html` from a scratch directory (do not modify the repo), then open it:

```
mkdir -p /tmp/ifa-serve && cp README.md /tmp/ifa-serve/index.html
python3 -m http.server 8000 --directory /tmp/ifa-serve
# open http://localhost:8000/
```

Core functionality to verify: clicking a step's "Start" button disables it, shows a "Started at" time, and starts a red countdown that decrements each second.

### Lint / test / build
None configured. There is no linter, test suite, or build tooling in this repo.

### Note on `.gitignore`
The committed `.gitignore` is a leftover Java/BlueJ template and does not match this project's content. It is harmless.
