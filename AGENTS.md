# Codex agent instructions

## Scope

Maintain a small, testable Python 3.11 CLI pipeline:
legal source text -> source-traceable story cards -> approved story -> 6-shot illustrated asset pack -> optional FFmpeg video.

Never add scrapers or request logic that bypasses login, subscriptions, paywalls, DRM, digital signatures, or device restrictions. Novel Radar remains the collection/research system.

## Current architecture

- src/book_story_factory/reader.py: EPUB/TXT/PDF input, source indexes and offsets
- distill.py: optional LLM candidate extraction with strict exact short-source anchors
- episode.py: deterministic starter storyboards and subtitle file
- render.py: local-image video compilation
- cli.py: CLI commands
- docs/CANGJIE.md: the upstream Cangjie integration contract

## Development rules

1. Keep raw copyrighted books, text indexes, stories derived from full texts, model credentials, and generated media outside Git. Public repository.
2. Do not claim exact historical authenticity when only a book excerpt is verified. Distinguish book source matching and external fact checking.
3. Do not fabricate missing character motivations, dates, events, chapters or source quotations.
4. Avoid copying a substantial amount of source text into public output; generated scripts must use original narration and copyright review.
5. Keep new modules optional and dependency-light. Run unit tests after changes.
6. Prefer stable JSON adapters; do not vendor all of Cangjie or create a second Novel Radar datastore.
7. If changing the research boundary, compare docs/ARCHITECTURE.md before implementing.

## Priority next tasks

P0: Finish end-to-end local smoke validation, confirm GitHub CI, and fix actual failures.
P0: Build an explicit Cangjie export-to-story adapter with provenance and missing-field diagnostics.
P1: Introduce an optional model-based rewrite and storyboarding pass (human approval before render).
P1: Add still-image quality checks and per-story identity/wardrobe consistency prompts.
P1: Plug in chosen TTS provider and timed subtitle alignment.
P2: Optional image-generation provider and Ken Burns motion; benchmarking cost and outputs.
