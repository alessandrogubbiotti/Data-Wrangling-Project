<!-- Copilot instructions for AI coding agents working on this repo -->
# Copilot instructions — Data-Wrangling-Project

Purpose: give AI coding agents the exact, actionable knowledge needed to make safe, small, high-confidence changes in this repository.

- Project roots: the working processing code and site live under `epstein-docs.github.io/` (OCR, entity extraction, analysis, and 11ty site). Data outputs live in `epstein-docs.github.io/results/`, `analyses.json`, `dedupe.json`, and `_site/` (generated).

- Quick dev setup (local):
  - Python: create/activate venv and install requirements from the repository root or the `epstein-docs.github.io/requirements.txt` where appropriate.
    - Example: `python -m venv .venv && source .venv/bin/activate && pip install -r epstein-docs.github.io/requirements.txt`
  - Node: build the static site in `epstein-docs.github.io/` with `npm install && npm run build` (or `npm start` for dev server).
  - API config: copy `epstein-docs.github.io/.env.example` → `.env` and set `OPENAI_API_URL`, `OPENAI_API_KEY`, and optional `OPENAI_MODEL`.

- Main workflows and entry points (what to change when adding features):
  - Image OCR + extraction: `epstein-docs.github.io/process_images.py` (flags: `--limit`, `--workers`, `--no-resume`). It writes JSON per image into `results/` and maintains `processing_index.json` for resume support.
  - Cleanup retries: `epstein-docs.github.io/cleanup_failed.py` (dry-run vs `--doit` options for reprocessing/removing invalid JSON).
  - Deduplication: `epstein-docs.github.io/deduplicate.py` and `epstein-docs.github.io/deduplicate_types.py` — they produce `dedupe.json` and `dedupe_types.json` consumed by the site build.
  - Document analysis: `epstein-docs.github.io/analyze_documents.py`. Important details:
    - Uses `OPENAI_API_URL`/`OPENAI_API_KEY` and an `OpenAI` client wrapper.
    - Groups pages by normalized document number (see `normalize_doc_num`) and sorts pages by a parsed page number (handles both ints and strings like "24 of 66").
    - Truncates long text to ~8000 chars before sending to LLM and expects strict JSON back; it attempts to recover JSON from code fences.
  - Site generation: `epstein-docs.github.io/` (source files in `epstein-docs.github.io/src/` and Eleventy config `.eleventy.js`). The build expects `dedupe.json` and `analyses.json` when present.

- Data conventions to preserve when editing scripts or generators:
  - Per-image/per-page JSON files in `results/*/*.json` contain at least: `full_text`, `entities` (keys: `people`, `organizations`, `locations`, `dates`, `reference_numbers`), and `document_metadata` (common keys: `document_number`, `page_number`). Changes that break these fields will break grouping, dedupe, and site generation.
  - `analyses.json` is an array-like object `{ total, analyses: [...] }` produced by `analyze_documents.py`. Keep formatting stable to avoid site build regressions.
  - `dedupe.json`/`dedupe_types.json` are canonical mapping files. The build uses them; if you change mapping formats, also update the Eleventy templates in `src/`.

- Coding patterns and common pitfalls:
  - Scripts are CLI-first (use `argparse`); add flags rather than changing global behavior when possible.
  - Many scripts are resume-friendly — prefer incremental writes and avoid reprocessing large numbers of files by default.
  - Generated artifacts (`_site/`, `results/`, `processing_index.json`, `analyses.json`, `dedupe*.json`) should not be edited manually in PRs unless the change is part of a reproducible process.
  - LLM integrations expect OpenAI-compatible semantics and sometimes return non-JSON — scripts include tolerant extraction heuristics; keep those heuristics when improving reliability.

- Integration points and external dependencies:
  - External LLM endpoint: configured via `OPENAI_API_URL` and `OPENAI_API_KEY` in `.env`.
  - Site CI/CD: GitHub Pages build is triggered by pushes; local site preview via `npm start`.
  - Data source: upstream `downloads/` directory for images (local) or external datasets used to populate `results/`.

- When you open a PR, preferred small-change pattern:
  1. Run `python process_images.py --limit 5` (or `--no-resume`) in a dev env to verify processing behavior on a tiny sample.
  2. If touching LLM prompts, include sample input/output (redact secrets) and add unit-like checks for JSON extraction.
  3. If changing JSON shape, update `epstein-docs.github.io/src/` templates and include a small example `results/` JSON in tests/docs.

- Files to inspect for concrete examples:
  - `epstein-docs.github.io/process_images.py` (OCR loop, options)
  - `epstein-docs.github.io/analyze_documents.py` (grouping, normalization, prompt format)
  - `epstein-docs.github.io/deduplicate.py` and `deduplicate_types.py` (mapping outputs)
  - `epstein-docs.github.io/src/` (Eleventy templates that consume `results/` and `dedupe*.json`)

- Safety & scope for AI edits:
  - Safe changes: docstrings, small refactors, adding CLI flags, improving parsing robustness, updating prompts with tests, fixing typos in README/docs.
  - Dangerous changes (avoid without human review): large refactors that change JSON schema, secrets changes, modifying deployment/CI config, edits to `_site/` or mass-editing `results/` data.

If anything here is unclear or you'd like more detail (examples, exact env values, or tests), tell me which section to expand. Thank you!
