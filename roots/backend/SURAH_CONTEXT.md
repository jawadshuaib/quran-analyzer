# Surah Context Pipeline (Qur'an-Only)

This document describes the new offline surah-context system that powers the frontend section:

- `What Has Happened So Far`

It is intentionally Qur'an-only: no tafsir, no hadith, no external historical sources.

## Purpose

For any target verse `S:A`, generate a concise synthesis of what has happened in that surah from `S:1` to `S:A`, prioritizing new synthesis over literal restatement.

The output is stored once in SQLite and served instantly to users.

## Guardrails

The generator enforces:

- Use only the provided verse evidence (`S:1..A`) from the database.
- Use existing translation + translation notes as internal evidence only.
- No tafsir/hadith/secondary material.
- `summary_so_far` is the primary output (highest quality required).
- Prefer synthesis of progression/turning points over repeating one verse.
- Citation-backed summary points (`summary_points[].refs`) must be valid verse refs.

## Data Model

Tables in `quran.db`:

- `surah_context_configs`
- `verse_surah_contexts`

Key columns used by the current summary-first config:

- `summary_so_far` (displayed to users)
- `summary_points_json` (evidence-backed support)
- `signal_score` and `verifier_report_json` (quality gating)

Legacy fields remain in schema for compatibility but are intentionally empty in the current config:

- `current_verse_focus`
- `key_verses_json`
- `lexical_continuity_json`

## API

Endpoint:

- `GET /api/verse/<surah>:<ayah>/surah-context`

Useful query params:

- `config=<name>`: select a specific config/version
- `include_all=1`: bypass high-signal display gating

Frontend currently requests:

- `config=surah-context-quran-only-v2-summary`

## Current Active Config

- `config_name`: `surah-context-quran-only-v2-summary`
- `prompt_version`: `v2-summary`
- default model: `qwen3:14b` (local Ollama)

This isolates summary-first behavior from older in-progress runs/configs.

## CLI Usage

Run from `roots/backend`:

```bash
# Generate for all verses in all surahs (resumable)
python surah_context_ai.py

# Force regenerate everything for current config
python surah_context_ai.py --force

# Generate subset
python surah_context_ai.py --verses "21:1-112"

# Single verse
python surah_context_ai.py --verses "21:9"

# Dry-run validation
python surah_context_ai.py --verses "21:1-10" --dry-run

# Explicit model/config
python surah_context_ai.py --model qwen3:14b --config surah-context-quran-only-v2-summary
```

Resumability behavior:

- Without `--force`, existing `(chapter, verse, config_id)` rows are skipped.
- You can stop the process at any time and re-run to continue.

## Frontend Behavior

File: `roots/frontend/src/components/SurroundingContext.tsx`

Current UX:

- Shows only `What Has Happened So Far`
- Does not show:
  - `How XX:XX Fits In`
  - `Lexical Continuity In This Surah`
  - `Key Earlier Verses In This Surah`
- If no surah context exists, the summary card is hidden (no fallback message shown).

Verse references in the summary use the same tooltip system as translation notes:

- Component: `VerseRefText`
- Hovering `21:4` or `21:1-3` shows verse preview tooltip
- In this section, click-through navigation is disabled; tooltip-only interaction is used

## Operational Notes

- Local generation requires Ollama reachable at `localhost:11434`.
- If a long older run is writing to a different config, it will not affect the frontend as long as frontend remains pinned to `surah-context-quran-only-v2-summary`.
- To roll out a new prompt strategy safely:
  1. Create a new config name and prompt version.
  2. Generate/evaluate.
  3. Switch frontend `config` query parameter.

