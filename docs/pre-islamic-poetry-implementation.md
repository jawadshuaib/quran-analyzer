# Qurʾān ↔ Pre-Islamic Poetry: Implementation Architecture

*Engineering counterpart to `pre-islamic-poetry-comparison.md` (the research/methodology doc).*
*Drafted 2026-06-21. Status: proposal for your review — nothing built yet.*

---

## 0. The one insight that shapes everything

You imagined a multi-agent loop that "reviews a couple of verses and the poetry at a time," paced over several days with `ScheduleWakeup`. That loop is exactly right — **but it can't draft a single comparison until the poetry is acquired, authentication-tiered, and indexed by root.** There is no point asking an agent "how does the K-F-R root differ in the poetry?" until the system can hand it *the actual authenticated lines that use K-F-R*.

So the build is two big movements:

1. **Phase 0 — Corpus** (the prerequisite, mostly one-time): get the poetry in, tier it for trustworthiness, and index it by root so it's queryable. *This is the real new engineering.*
2. **Phase 1+ — Generation** (the days-long agent loop you described): for each root / verse, draft the comparison, **adversarially verify it** (the objectivity gate), and queue it for your review.

Everything else — serving, frontend, admin review — is a near-exact mirror of what you already shipped for exegesis. **~80% of this feature reuses patterns that already exist in the repo.** The genuinely new parts are (a) the poetry corpus + root index, and (b) one new agent role: the *adversarial reviewer* that operationalizes the objectivity rules.

---

## 1. The whole system on one page

```
┌─────────────────────────────────────────────────────────────────────────┐
│ PHASE 0 — CORPUS  (poetry_corpus.py, mostly one-time)                     │
│                                                                           │
│  Muʿallaqāt (hand-curated, Tier A) ─┐                                     │
│  Kaggle/aldiwan scrape (Tier C) ────┼─▶ poetry_poems ─▶ poetry_lines      │
│  Mufaḍḍaliyyāt etc. (Tier B, later) ┘         │                           │
│                                               ▼                           │
│                          tier assignment + LLM root-extraction            │
│                                               ▼                           │
│                                       poetry_line_roots  (root index)     │
└───────────────────────────────────────────────┬──────────────────────────┘
                                                 │  (queryable by root)
┌────────────────────────────────────────────────▼──────────────────────────┐
│ PHASE 1 — GENERATION  (poetry_gen.py + .claude/loop_poetry.md, paced loop) │
│                                                                            │
│   ScheduleWakeup ──▶ poetry_gen.py next ──▶ small batch (2 roots / 4 verses)│
│        ▲                                          │                         │
│        │                                          ▼                         │
│        │                              ┌───────────────────────┐             │
│        │                              │ DRAFTER agent         │ reads Quran │
│        │                              │  draft comparison     │ profile +   │
│        │                              └───────────┬───────────┘ poetry lines│
│        │                                          ▼                         │
│        │                              ┌───────────────────────┐             │
│        │                              │ ADVERSARIAL REVIEWER  │ counter-    │
│        │                              │  try to REFUTE it     │ search,     │
│        │                              └───────────┬───────────┘ tier-check  │
│        │                                          ▼                         │
│        │                          survives? ──▶ poetry_gen.py add (pending) │
│        └───── schedule next wake ◀── else ──▶ skip / flip to continuity     │
└────────────────────────────────────────────────┬───────────────────────────┘
                                                  │  (review_status='pending')
┌──────────────────────────────────────────────────▼─────────────────────────┐
│ REVIEW + SERVE + RENDER  (mirrors exegesis exactly)                         │
│                                                                             │
│  /admin/poetry review queue ──approve──▶ root_poetry_comparisons (live)     │
│                                          verse_poetry_notes       (live)    │
│                                                  │                          │
│   app.py endpoints ──▶ /api/root/<bw>/poetry, /api/verse envelope,          │
│                        /api/surah has_poetry_note, v1 ?fields=all           │
│                                                  │                          │
│   Frontend ──▶ RootPage "In Pre-Islamic Poetry"  · VerseDisplay/Reader note │
│               · Ask-the-Quran context · admin review tab                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data model (new tables)

All follow existing conventions: `chapter/verse` keys, Buckwalter roots, `review_status`/`hidden` like `verse_exegesis`, a `*_configs` sibling like `ai_translation_configs`, and idempotent `_ensure_*_table()` creation in `app.py`.

### 2.1 Corpus tables

```sql
-- One row per poem.
CREATE TABLE poetry_poems (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    poet         TEXT,            -- normalized Arabic name
    poet_latin   TEXT,
    era          TEXT,            -- 'jahili', 'mukhadram', ...
    title        TEXT,
    meter        TEXT,            -- al-baḥr, if known
    rhyme        TEXT,            -- qāfiya / rawiyy letter, if known
    auth_tier    TEXT NOT NULL,   -- 'A' | 'B' | 'C' | 'D'  (see §3.2 of research doc)
    source       TEXT,            -- 'muallaqat' | 'kaggle:mdanok' | 'mufaddaliyat'
    source_ref   TEXT,            -- edition / citation
    full_text    TEXT,
    notes        TEXT,
    created_at   TEXT DEFAULT CURRENT_TIMESTAMP
);

-- One row per bayt (line). A bayt = two hemistichs (ṣadr + ʿajuz).
CREATE TABLE poetry_lines (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    poem_id      INTEGER NOT NULL REFERENCES poetry_poems(id),
    line_no      INTEGER,
    hemistich1   TEXT,            -- ṣadr
    hemistich2   TEXT,            -- ʿajuz
    text_plain   TEXT,            -- normalized full bayt
    UNIQUE(poem_id, line_no)
);

-- Root index over poetry lines. LLM-extracted; quotable lines get verified=1.
CREATE TABLE poetry_line_roots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    line_id         INTEGER NOT NULL REFERENCES poetry_lines(id),
    root_buckwalter TEXT NOT NULL,
    root_arabic     TEXT,
    surface_word    TEXT,         -- the word as it appears in the bayt
    sense_hint      TEXT,         -- one-line gloss of how it's used here
    extractor_model TEXT,
    confidence      REAL,
    verified        INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_poetry_line_roots_root ON poetry_line_roots(root_buckwalter);
```

### 2.2 Config + content tables

```sql
-- Versioned generation config (mirrors ai_translation_configs et al.)
CREATE TABLE poetry_compare_configs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    config_name   TEXT NOT NULL UNIQUE,
    model_name    TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    methodology_notes TEXT,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- ROOT-LEVEL comparison — the abstract layer (mirrors term_surveys).
CREATE TABLE root_poetry_comparisons (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    root_buckwalter  TEXT NOT NULL UNIQUE,
    root_arabic      TEXT,
    config_id        INTEGER REFERENCES poetry_compare_configs(id),
    shift_type       TEXT,        -- continuity|narrowing|widening|elevation|
                                  -- theologization|referential_transfer|reassignment
    comparison_markdown TEXT,     -- reader-facing prose
    quran_usage_summary  TEXT,
    poetry_usage_summary TEXT,
    quoted_lines_json TEXT,       -- [{line_id,poet,arabic,translit,english,auth_tier}]
    collocations_json TEXT,       -- {"quran":[...], "poetry":[...]}  (§5.2 fingerprint)
    continuity       INTEGER DEFAULT 0,   -- 1 = verdict is agreement, not contrast
    counter_search_json TEXT,     -- what the adversarial step looked for & found
    confidence       REAL,
    auth_tier_max    TEXT,        -- highest tier among quoted lines
    adversarial_report TEXT,      -- reviewer agent's verdict
    review_status    TEXT DEFAULT 'pending',
    hidden           INTEGER DEFAULT 0,
    raw_response     TEXT,
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    edited_at        TEXT
);

-- VERSE-LEVEL note — the specific layer (mirrors verse_exegesis).
CREATE TABLE verse_poetry_notes (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    chapter          INTEGER NOT NULL,
    verse            INTEGER NOT NULL,
    page_key         TEXT NOT NULL,
    focus_root_buckwalter TEXT,   -- the root the note hinges on
    note_markdown    TEXT NOT NULL,
    quoted_lines_json TEXT,
    continuity       INTEGER DEFAULT 0,
    confidence       REAL,
    auth_tier_max    TEXT,
    config_id        INTEGER REFERENCES poetry_compare_configs(id),
    adversarial_report TEXT,
    review_status    TEXT DEFAULT 'pending',
    hidden           INTEGER DEFAULT 0,
    raw_response     TEXT,
    created_at       TEXT DEFAULT CURRENT_TIMESTAMP,
    edited_at        TEXT,
    UNIQUE(chapter, verse)
);
```

That's the entire schema. Five tables; three of them are direct structural twins of tables you already have (`term_surveys`, `verse_exegesis`, `ai_translation_configs`).

---

## 3. Phase 0 — building the corpus (`poetry_corpus.py`)

This is the part with no existing analog, so it gets the most detail. One CLI, several subcommands.

### 3.1 Acquire

| Subcommand | What it does |
|---|---|
| `load-muallaqat` | Loads the ~10 hanging odes from a **hand-curated JSON** we check into the repo (`data/poetry/muallaqat.json`). Tier **A**. This is small, gold, and unblocks a credible v1 *by itself*. |
| `load-kaggle <csv>` | Loads the `mdanok/arabic-poetry-dataset` CSV, **filtered to `العصر == جاهلي`**. Tier **C** (statistics + candidate retrieval only, never the sole basis for a contrast). Normalizes into `poetry_poems`/`poetry_lines`. |
| `load-anthology <name> <path>` | Later: critical editions (*Mufaḍḍaliyyāt*, *Aṣmaʿiyyāt*, *Ḥamāsa*) as Tier **B**. Incremental. |

> **Why hand-curate the Muʿallaqāt rather than scrape them?** They are the backbone of every quotable claim. ~10 poems / a few hundred lines is small enough to enter by hand from a reliable edition (with the classical commentary references), guaranteeing Tier-A provenance. This is a half-day of careful data entry, not an engineering problem.

### 3.2 Authenticate (assign tiers)

| Subcommand | What it does |
|---|---|
| `tiers` | Assigns/upgrades `auth_tier`. Muʿallaqāt → A. Lines whose poet matches a known anthology poet and that also appear in a Tier-A/B source get **promoted**. Everything else from the scrape stays **C**. Lines scholars flag as doubtful → **D** (used only to *teach* the authentication problem). |

The rule from the research doc, enforced in code: **a contrast may only be published if its quoted evidence is Tier A or B.** Tier C feeds *frequency statistics and candidate discovery*; Tier D is display-only with a "disputed" label.

### 3.3 Root-index (the key technical decision)

We need to answer "which authenticated lines use root R?" — and **no Arabic morphology library is installed** (checked: no `camel_tools`, `farasa`, `pyarabic`; only `sentence-transformers` + `arabic-reshaper`).

**Decision: index by root using the LLM, not a morphology toolchain.** Rationale:

- Installing CAMeL Tools pulls in heavy ML deps and still needs sense-disambiguation; the project already runs everything through LLMs.
- We start with **~15–20 pilot roots**, so this is *root-driven retrieval*, not whole-corpus parsing: for each target root, ask the model to scan the (small, authenticated) corpus and return the lines that use a derivative of that root, with the surface word and a one-line sense.
- Output lands in `poetry_line_roots` with a `confidence` and `verified=0`. **Lines we actually quote get `verified=1` by a human** during review — so a model mistake can never silently become a published claim.

| Subcommand | What it does |
|---|---|
| `index-root <bw>` | LLM pass: scan authenticated poems, emit `poetry_line_roots` rows for root `<bw>` (surface word + sense hint + confidence). Cheap; can run via `anthropic_batch.py` (≈50% cheaper, resumable). |
| `verify-root <bw>` | Lists the candidate lines for human spot-check; flips `verified=1`. (Or done inline in the review UI.) |
| `stats` | Corpus coverage: poems/lines per tier, roots indexed, verified counts. |

*Upgrade path:* if we later want whole-corpus root coverage (for the frequency/negative-space maps over the full Jahilī vocabulary), we can add a CAMeL Tools batch job behind the same `poetry_line_roots` table without touching anything downstream.

---

## 4. Phase 1 — the generation engine (the multi-agent paced loop)

This is the loop you pictured. It mirrors the **exegesis** machinery exactly: a Python CLI for the mechanical plumbing + a `.claude/loop_*.md` doctrine the agent reads each wake + `ScheduleWakeup` for multi-day pacing. The one addition is a second agent role.

### 4.1 The CLI — `poetry_gen.py` (mirrors `qa_gen.py` / `exeg_next.py`)

```
poetry_gen.py next   --track root|verse [--count N]   # next un-done items + how many remain
poetry_gen.py context <root|S:A>                      # everything needed to draft it
poetry_gen.py add     <root|S:A> --file <json>        # write a pending draft (+ runs validators)
poetry_gen.py skip    <root|S:A> --reason "<line>"    # mark intentionally skipped
poetry_gen.py stats                                   # progress + review-queue counts
```

- **`next --track root`** returns the next pilot roots without a `root_poetry_comparisons` row.
- **`next --track verse`** returns the next verses where a *done* (approved) root comparison is load-bearing and no `verse_poetry_notes` row exists yet. (Verse track depends on root track — see §6 ordering.)
- **`context <root>`** returns: the root's full Qurʾān profile (occurrences, lemmas, AI root meaning, cognates — all already in the DB) **plus the verified poetry lines** for that root with their tiers. This is what makes "review the poetry" possible — the agent gets the actual lines in front of it.
- **`add`** runs validators before writing, exactly like `qa_gen add` does: reject fabricated verse refs, reject quoted poetry lines whose `line_id` isn't in the corpus, require `auth_tier_max ∈ {A,B}` for any `continuity=0` (contrast) verdict, flag post-Qurʾānic terminology. A draft that fails a validator comes back for a fix instead of being written.

### 4.2 The doctrine — `.claude/loop_poetry.md` (mirrors `.claude/loop.md`)

The loop file carries the **objectivity constitution** (Part 7 of the research doc) plus the per-iteration steps. The agent reads it every wake. Its non-negotiables, in the same spirit as the existing loop doctrine:

1. **Quote only verified, Tier-A/B lines for any contrast.** Never invent a line. If you can't cite a real one, make the claim at the level of the dictionaries (Lane / Lisān / al-Rāghib) and say so — or skip.
2. **Run the counter-search first.** Before asserting a contrast, look in the corpus for poetry that uses the word *the Qurʾān's way*. Found plenty? The verdict is `continuity`. Log what you searched for in `counter_search_json`.
3. **Genre ≠ inferiority.** A different poetic aim is not a Qurʾānic "win." Don't manufacture contrasts from register differences.
4. **Affirm shared values** where they exist (courage, generosity, hospitality). Surface continuities approvingly (the Labīd "all but God is vain" case is the model).
5. **State strong, earned contrasts plainly** — no false hedging — but only once 1–3 hold.
6. **No post-Qurʾānic terminology** (same rule as every other pipeline here).
7. **Zero output is a valid result.** A root with no meaningful, authenticated comparison is *skipped*, not forced. Quality over coverage — exactly the `loop.md` ethos.

### 4.3 The two agent roles per item (the "multiple agents" you asked for)

Each item flows through **two roles**. This is the heart of how objectivity becomes operational rather than aspirational:

- **① Drafter.** Reads `context <root>` (Qurʾān profile + verified poetry lines). Investigates — traces the root's sense across both corpora, picks a `shift_type`, drafts the prose, selects the lines to quote, builds the collocation lists. Produces a candidate.
- **② Adversarial Reviewer.** Gets the draft and is prompted to **refute it**: re-runs the counter-search, checks that every quoted line is verified and Tier A/B, asks "is this just genre difference?", and challenges the `shift_type`. Emits a verdict → `adversarial_report`. If it refutes the contrast, the item is **flipped to `continuity`** or **skipped**; if it survives, it's added as `pending` with the report attached.

Then — as with exegesis — the **human admin is the final gate.** Nothing goes live without your approval. The adversarial reviewer doesn't replace you; it raises the floor so what reaches you is already counter-searched and tier-checked.

### 4.4 How parallel to go (spend-cap aware)

You ran 3 agents for exegesis. Here the same dial applies, and the design works at every setting:

| Mode | What runs | Cost | When |
|---|---|---|---|
| **Sequential (default)** | One main-loop agent does Drafter then Adversarial passes itself, one item at a time. | Lowest — spend-safe. | Default. Proven by the exegesis loop. |
| **Role fan-out** | Drafter and Reviewer are *separate* sub-agents per item. | ~2× | When you want stricter independence between draft and critique. |
| **Item fan-out** | A few items (roots/verses) processed in parallel, each draft+review. | ~N× | Like your 3-agent exegesis burst, to move faster across a day. |

> **Recommendation:** default to **sequential**, since it's spend-safe and the adversarial pass works fine as a second prompt within one agent. Reach for **item fan-out (2–3)** only when you want to cover ground faster on a given day — and dial it back down between bursts. The `ScheduleWakeup` cadence (next section) matters more for total spend than per-item parallelism.

### 4.5 Pacing over several days (`ScheduleWakeup`)

The loop is driven by the dynamic `/loop` + `ScheduleWakeup` pattern. Each wake:

1. `poetry_gen.py next --track <t> --count <B>` → a small batch (start `B=2` roots, or `B=4` verses).
2. For each item: Drafter → Adversarial Reviewer → `add` (pending) or `skip`.
3. Print a one-line summary; if `next` returned empty, **stop** (don't reschedule). Otherwise schedule the next wake.

**Cadence:** unlike the qa_gen loop (purely local, so it rescheduled fast), this loop makes API calls and benefits from human review keeping pace. A gentle **20–40 min** between wakes is plenty — it spreads cost, keeps the review queue from ballooning, and naturally stretches a few hundred items across several days. The math: ~12 pilot roots (root track) is a day; their load-bearing verses (a curated subset of K-F-R's 465, W-Q-Y's 237, etc. — *not* every occurrence) are a few hundred notes → several days at this cadence. That is exactly the multi-day shape you wanted.

**Stop condition is explicit and safe:** `next` returns empty → the run is complete → no further wake is scheduled. (Same termination contract as `loop.md` step 1.)

---

## 5. Review, serve, render (mirrors exegesis — briefer)

### 5.1 Admin review queue
A new `/admin/poetry` tab mirroring the exegesis review queue: pending list → read the draft + the **adversarial report** + the quoted lines (with tier badges) → **approve / edit / hide**. The "verify this quoted line" action flips `poetry_line_roots.verified=1`. Reuses the `AdminAssistantQA` review patterns.

### 5.2 API (`app.py` + `api_v1.py`)
- `_ensure_root_poetry_table()` / `_ensure_verse_poetry_table()` — idempotent, like `_ensure_exegesis_table()`.
- `GET /api/root/<bw>/poetry` → approved, non-hidden `root_poetry_comparisons` row.
- `GET /api/verse/<s>:<a>` envelope → include `poetry_note` (approved only), and the root detail payload includes its poetry comparison.
- `GET /api/surah/<n>` → add `has_poetry_note` per verse (mirrors the `has_exegesis` flag you just added) so the reader knows when to show the block.
- v1 `?fields=all` → add a `poetry_note` / `poetry_comparison` section.

### 5.3 Frontend
- **RootPage** (`/root/<bw>`): a new **"In Pre-Islamic Poetry"** section, styled like the violet *AI Root Meaning* panel but with its own palette (a warm sand/amber tone reads well against the existing violet cognates → it visually says "looking *backward in time*" vs. cognates "looking *outward across languages*"). Shows the prose, the `shift_type` as a chip, quoted lines with **authentication-tier badges**, and the collocation fingerprints as two small ranked lists. Roots in the prose linkify + tooltip via the existing `VerseRefText`/`RootRefLink`.
- **VerseDisplay** + **ReaderVerse**: a poetry note block rendered **after** the Exegesis note (reader order becomes Translation → Exegesis → **Poetry** → Grammar), gated on `has_poetry_note`, through the existing `FormattedText` pipeline. Folds into the global notes toggle you just shipped.
- **Ask-the-Quran**: `context-builders.ts` gains a `## Pre-Islamic Poetry Comparison` section in `buildVerseContext` and the root survey in `buildRootContext` — so the assistant answers "how did the Arabs use this word?" from our authenticated notes, not its own memory.
- **Objectivity UI:** tier badges on every quote; distinct *continuity* vs *contrast* styling (continuity should look celebratory, not grudging); a "see the evidence" expander showing poet + poem + line + tier; a confidence indicator.

---

## 6. Build order (dependency-correct checklist)

```
Phase 0 — Corpus  ───────────────────────────────────────── (unblocks everything)
  [ ] schema: poetry_poems, poetry_lines, poetry_line_roots
  [ ] poetry_corpus.py: load-muallaqat (hand-curated JSON, Tier A)
  [ ] poetry_corpus.py: load-kaggle (filtered jahili, Tier C) + tiers
  [ ] poetry_corpus.py: index-root for the ~12–15 pilot roots (LLM, batch)
  [ ] spot-verify the quotable lines (verified=1)

Phase 1 — Root-level generation  ────────────────────────── (the abstract layer)
  [ ] schema: poetry_compare_configs, root_poetry_comparisons
  [ ] poetry_gen.py: next/context/add/skip/stats  (--track root)
  [ ] .claude/loop_poetry.md  (objectivity doctrine + iteration steps)
  [ ] run the paced loop over the pilot roots (ScheduleWakeup)
  [ ] /admin/poetry review queue + approve

Phase 1b — Verse-level generation  ──────────────────────── (depends on approved roots)
  [ ] schema: verse_poetry_notes
  [ ] poetry_gen.py --track verse  (load-bearing verses of approved roots)
  [ ] run the paced loop; review/approve

Phase 2 — Serve + render  ────────────────────────────────── (mirrors exegesis)
  [ ] app.py endpoints + _ensure_* + has_poetry_note flag + v1 envelope
  [ ] RootPage "In Pre-Islamic Poetry" section
  [ ] VerseDisplay + ReaderVerse note block (after exegesis)
  [ ] Ask-the-Quran context-builders
  [ ] build + deploy (gitignore the raw corpus artifacts; sync tables to prod
      with sync_tables_to_prod.sh, like verse_exegesis)

Phase 3 — Depth (later)  ─────────────────────────────────── (the "wow" layers)
  [ ] thematic/motif inversion essays (aṭlāl, nāqa, khamr, fakhr, dahr)
  [ ] meter/rhyme engine (lean on external meter classifiers)
  [ ] negative-space + agency-reassignment maps (corpus-wide stats)
```

The smallest shippable slice that proves the whole idea: **Phase 0 + Phase 1 + Phase 2 for ~12 roots** — root pages get a sourced, tier-badged "In Pre-Islamic Poetry" section. Verse notes and the depth layers follow once that's trusted.

---

## 7. Generation cost & modes (so spend is a knob, not a surprise)

- **Corpus indexing** (`index-root`) and any bulk mechanical pass → route through **`anthropic_batch.py`** (≈50% cheaper, resumable across laptop sleep). One-time-ish.
- **The drafting/adjudication loop** → the paced agent loop. Cost is governed mostly by **cadence** (wake interval) and **batch size**, secondarily by **parallelism**. All three are dials in `loop_poetry.md` / the `ScheduleWakeup` delay.
- **Default posture:** sequential, `B=2–4`, 20–40 min cadence. This is spend-safe and still finishes the pilot in a day and the verse pass in a few days. Turn the dials up only for a deliberate burst.

---

## 8. Decisions — LOCKED (2026-06-21)

| # | Decision | Choice | Build implication |
|---|---|---|---|
| 1 | **Pilot scope** | **~5 roots first** — K-F-R, W-Q-Y, D-H-R, K-R-M, J-N-N | Validate the whole loop end-to-end on the richest cases before scaling to the full Appendix-A set. |
| 2 | **Root extraction** | **LLM root-indexing** | No CAMeL Tools dependency. `index-root` is an LLM pass; humans verify any quoted line (`verified=1`). |
| 3 | **Corpus reach for v1** | **Muʿallaqāt (Tier A) + filtered Kaggle scrape (Tier C)** | Both loaders built in Phase 0. Contrast claims still gate on Tier A/B evidence; the scrape powers statistics + candidate discovery. |
| 4 | **Parallelism** | **Wire 2–3 agent item fan-out** | The loop is built to process a few items per wake in parallel (each draft→adversarial-review), dial-able down to sequential. Cadence still governs total spend. |

### External input required before Phase 0 can finish
- **The Kaggle CSV must be supplied by you.** `mdanok/arabic-poetry-dataset` is auth-gated; it can't be fetched programmatically here. Download it and drop it somewhere in the repo (e.g. `roots/backend/data/poetry/arabic-poetry.csv`); `load-kaggle <path>` takes it from there.
- **Muʿallaqāt text** is public-domain classical verse — sourced from a reliable digital edition (e.g. Arabic Wikisource), entered into `data/poetry/muallaqat.json` as Tier A. (The *verses* are ancient/public-domain; only modern editorial commentary would be restricted, and we don't reproduce that.)

**Next step:** build **Phase 0** — schema + `poetry_corpus.py` (with `load-muallaqat`, `load-kaggle`, `tiers`, `index-root`, `verify-root`, `stats`) + the seeded Muʿallaqāt JSON — then **stop for review** before any generation loop runs.

*— end of document —*
