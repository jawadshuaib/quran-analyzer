# Grammar Insights (Archived / Paused)

Status: **paused in frontend**.  
The section is intentionally hidden from the verse UI, but the backend pipeline is preserved and documented for future reactivation.

This archive records:
- architecture and schema,
- generation/verifier methodology,
- what was learned during v1 -> v7 evolution,
- why display was disabled,
- what to do before re-enabling.

## Current Disable State

- **Frontend**:
  - `GrammarInsights` component is not mounted in `roots/frontend/src/App.tsx`.
  - `roots/frontend/src/components/GrammarInsights.tsx` remains in codebase for reuse/testing.
- **Backend**:
  - API and generators remain active and versioned.
  - Data continues to be queryable for offline QA.

## System Architecture

### Storage tables

- `grammar_insight_configs`
  - versioning metadata: `config_name`, `model_name`, `prompt_version`, notes, timestamps
- `verse_grammar_insights`
  - legacy + v7 fields:
    - `overview_text`, `insights_json`, `signal_score`, `verifier_report_json`
    - `generation_version`, `insights_v7_json`, `quality_json`
    - `overall_confidence`, `model_confidence_raw`, `display_json`
    - `evidence_json`, `raw_response`, latency columns

### API endpoint

- `GET /api/verse/<surah>:<ayah>/grammar-insights`
- optional params:
  - `config=<name>`
  - `include_all=1` (bypass display gate)

### Generator script

- `roots/backend/grammar_insights_ai.py`
- default config:
  - `grammar-insights-quran-only-v7-unified`
- default model:
  - local Ollama `qwen3:14b`
- resumable by `(chapter, verse, config_id)` unless `--force`

## Methodology Snapshot (v7)

### Evidence inputs (Qur'an-only)

Per verse, the generator uses:
- verse Arabic text,
- local translation,
- local translation notes,
- morphology rows,
- +/-2 verse local window signals.

No tafsir, hadith, or external commentary are used.

### Signal detection

Rule signals include:
- `time_perspective`
- `perspective_shift`
- `person_mixture`
- `royal_we_vs_i`
- `sound_communication`
- `gender_nuance`
- `conditional_structure`
- `exception_scope`
- `demonstrative_distance`
- `cognate_accusative` (conservative heuristic)
- `plural_type` (surface-pattern heuristic)
- `oath_structure` (conservative marker heuristic)

### Sanitization and guardrails

- reject weak confidence and redundant restatements,
- reject unsupported claim-feature combos,
- reject category/signal mismatches,
- reject out-of-scope verse references in text,
- counterfactual allow/ban gating,
- force morphology-grounded evidence,
- normalize and deduplicate outputs.

### Verifier and scoring

The v7 verifier computes:
- `evidence_sufficiency`
- `linguistic_correctness`
- `interpretive_value`
- `novelty`
- `clarity`
- `risk`
- `overall_confidence`

Additional atomized checks:
- observation atoms are extracted from claim text,
- each atom is matched against evidence/signals,
- unsupported core atoms raise risk and suppress display.

### Fallback system

Tiered fallback candidates are generated when model output is weak:
- tier 1: safer educational anchors,
- tier 2/3: selective investigative templates.

Anti-repetition memory tracks:
- template id,
- category,
- text skeleton.

Selection avoids near-adjacent template repetition where possible.

## Frontend UX That Was Built (Now Hidden)

The `GrammarInsights` component rendered:
- title,
- observation,
- why-this-matters,
- simple note,
- evidence chips.

Additional UX work done:
- Buckwalter -> Arabic conversion for display,
- root display in spaced Arabic form for tooltip compatibility,
- suppression of duplicate observation/payoff text,
- human-readable evidence chips (no raw `feature:PERF` style labels).

## Why Frontend Display Was Disabled

Despite substantial improvements, output quality still had unstable precision:

- occasional generic insights survived in some passages,
- fallback-heavy behavior produced repetitive patterns in ranges,
- some verses remained noisy or under-informative,
- score calibration varied by category and context.

The user decision was to disable frontend display until quality is consistently high.

## Known Failure Patterns

- malformed JSON from model (mitigated by cleanup + one strict retry),
- repetitive `other_grammar` fallback variants,
- low-value claims with weak payoff despite valid morphology,
- category drift under relaxed thresholds.

## Reactivation Criteria (Recommended)

Before re-enabling frontend display:

1. Build a gold QA set (250-400 verses), multi-annotator.
2. Hit minimum precision target on display-eligible insights.
3. Reduce fallback-only displayed share in contiguous ranges.
4. Tighten/retune `other_grammar` eligibility or split into safer subcategories.
5. Verify adjacent-verse anti-repetition behavior on long contiguous surah runs.

## Practical Commands

Run from `roots/backend`:

```bash
# Full run (resumable)
python grammar_insights_ai.py

# Specific range
python grammar_insights_ai.py --verses "16:1-40"

# Force overwrite for a range
python grammar_insights_ai.py --verses "107:1-7" --force

# Explicit config/model
python grammar_insights_ai.py --config grammar-insights-quran-only-v7-unified --model qwen3:14b
```

## Code Pointers

- Generator: `roots/backend/grammar_insights_ai.py`
- API/table migration: `roots/backend/app.py`
- Frontend component (not mounted): `roots/frontend/src/components/GrammarInsights.tsx`
- Frontend types: `roots/frontend/src/types/index.ts`
- Buckwalter helpers: `roots/frontend/src/utils/buckwalter.ts`
