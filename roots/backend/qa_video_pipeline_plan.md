# Q&A Video Pipeline — Design Proposal

**Status:** proposal for review (not yet implemented)
**Author:** Claude (planner)
**Date:** 2026-06-14
**Scope:** A new offline-built, gate-hardened pipeline that turns rated‑5 AI Q&A
pairs into punchy 60–90s YouTube videos (verse → intriguing question →
triangulated answer, in a teaching voice), pushed to the live channel.

---

## 0. TL;DR

We already run a mature 3-phase channel pipeline (`educational_*`). The new
"Q&A video" series is best built as a **4th video type inside that framework**,
sourced from `assistant_conversations` rows with `quality_score = 5`, reusing the
Remotion renderer, the ElevenLabs narration cache, the global YouTube uploader,
and the per-pipeline scheduler — adding three new pieces:

1. A **compression + teaching-voice script generator** that turns a 700–990‑char
   stored answer into a ~150‑word spoken script that keeps the triangulation
   skeleton and the cited refs, and *speaks to* the viewer.
2. A **two-headed gate**: (A) an editorial *punchiness / quality* gate and
   (B) an **airtight script ↔ video match gate** that makes the on-screen verse
   highlighting provably correspond to what the narration claims.
3. An **offline build → online push** path: build, gate, render, and *visually
   QC the MP4 locally*, then ship the verified row + MP4 to prod where the
   existing uploader posts it on schedule.

The single biggest engineering risk — the highlight mismatch you've seen — is
characterized precisely below (116 divergent verses, two deterministic buckets)
and the gate is designed around that ground truth.

---

## 1. Goals & non-goals

### Goals
- **Quality over quantity.** Most rated‑5 Q&A will *not* become videos. Skipping
  is success, exactly as it is in `qa_gen`. We publish only scroll-stopping ones.
- **Punchy.** 60–90s (default a Short, ≤60s). The question lands in the first
  ~8 seconds; the answer pays off and stops.
- **Teaching voice, not preaching.** "Okay — here's where it gets interesting…",
  "Notice what it does *not* say…". Speaks *to* the viewer, triangulates meaning,
  proportions confidence ("suggests", "the most we can fairly say"). Inherits
  `qa_workflow_brief.md` verbatim.
- **Airtight verse-highlight correctness.** The word lit up on screen is provably
  the word the narration is talking about — no silent drift, ever.
- **Pre-built offline, pushed online.** Scripts authored + gated + (ideally)
  rendered locally, then pushed to the live DB/uploader.

### Non-goals (for v1)
- No live, on-the-fly generation from user traffic. This is a curated, batch,
  human-approved channel feed.
- No theological commentary beyond what the Quran-internal Q&A already says
  (doctrine inherited from `qa_workflow_brief.md`).
- No new TTS vendor; we reuse ElevenLabs + its sha256 cache.

---

## 2. Where this plugs into what already exists

The channel already has everything except the Q&A-specific content + gate:

| Capability | Existing asset | Reuse plan |
|---|---|---|
| Renderer (Remotion, 1080×1920@30, slide JSON → MP4) | `roots/video-renderer` (`scripts/render.mjs`) | Reuse as-is; add a small bespoke slide vocabulary (§6) |
| Narration TTS + karaoke alignment | `roots/video-renderer/scripts/narration.mjs` (ElevenLabs `/with-timestamps`, sha256 cache) | Reuse as-is; durations auto-fit narration |
| Python → renderer bridge | `educational_render_remotion.py` (`_verse_data`, `_strip_uthmani_marks`, `_align_emphasis_to_positions`, `resolve_morphology_word_pos`, `_word_lens_data_for`, `_stage_outro_audio`) | Reuse helpers; add a `build_qa_payload` + `render_qa_video` |
| Render dispatch + status lifecycle | `educational_render.py:~950` | Add a `qa_insight` branch |
| Script generation (Claude, 4-beat) | `educational_scripts.py` (`enrich_payload`, `generate_script`, `sanitize_for_tts`) | Clone into a Q&A script generator with compression + voice |
| Quality gate | `educational_interestingness.py` (`judge_script` → `{verdict,score,reason,pass}`) | Clone + harden (fail-*closed*) into the Q&A punchiness gate |
| Safety gate | `educational_safety.py` (verse moderation, sticky cache) | Reuse |
| Scheduler daemon | `_scheduler_loop` in `app.py` (ticks `_educational_scheduler_tick` etc. every 30s) | Add `_qa_scheduler_tick` (or reuse educational scheduling) |
| YouTube uploader | `_youtube_upload_tick` + `_perform_educational_youtube_upload` (`youtube_upload_schedule` singleton; OAuth refresh token; ffprobe silent-guard; circuit breaker) | Add a 3rd eligible-row branch for the Q&A table |
| Per-item review UI | `AdminEducational.tsx` (VideoRow → expand → script preview → render → override) | Clone into `AdminQAVideos.tsx` at `/admin/qa-videos` |
| Offline → prod | `sync_tables_to_prod.sh` (per-table `INSERT OR REPLACE` over ssh+docker) | Use for rows; add MP4 transport (§8) |
| Source data | `assistant_conversations` (`quality_score=5` → 443 rows; `generation_meta.cited_refs`) | The candidate pool |

**Design principle: extend, don't fork.** Every box above already works in
production for three series; the Q&A series is a fourth tenant.

---

## 3. The source data (verified)

- **"Rated 5" == `assistant_conversations.quality_score = 5.0`.** 443 rows today,
  all `source='ai'`. (Distribution: 5.0→443, 4.0→2963, 3.0→527.)
- Each row: `page_key` = `chapter:verse` (the **anchor verse**); `question`;
  `answer` (markdown, 700–990 chars, `**bold**` pivots, `*italic*`
  transliterations); `category` (implication 1628 / lexical 722 /
  cross_reference 613 / rhetorical 409 / grammar 238 / semantic 207 /
  morphology 66 / cognate 50).
- `generation_meta` JSON carries the gold for video assembly:
  - **`cited_refs`** — the exact verses the answer triangulates across (e.g. 4:3 →
    `["4:127","4:3"]`; 39:42's answer cites 6:60, 2:255). These are the verses the
    video should *display*, and the targets the highlight gate validates.
  - `source_notes`, `flags` (`[]` = clean), `score_v1`, `regraded`,
    **`needs_voice_revision`** (true on many rated‑5 rows — flags prose not yet
    voice-ready; the compression step *is* that voice pass).
- **Caveat:** rated‑5 rows are essentially all `review_status='pending'` (only 3
  approved corpus-wide). So `quality_score=5` is an *AI* confidence signal, not a
  human sign-off. The pipeline therefore adds its **own** human approval step
  (§7, §9) rather than assuming `review_status='approved'`.

**Reference content (what "great" looks like), pulled from the DB:**
- `39:42` (id 3913): one verb *yatawaffā* for death *and* sleep → 6:60 (*baʿatha*
  for waking) → 2:255 ("no slumber takes Him"). The exemplar you cited.
- `13:28` (id 139): hearts *find rest* vs 8:2 hearts *tremble* → 39:23's *thumma*
  resolves them as two moments of one motion.
- `17:1` (id 140): the Prophet named only "His servant" at his most exalted
  moment → 53:10, 18:1, 25:1, 72:19.

These three become the **video-format gold exemplars** (compressed) in the script
generator's prompt, so the voice is anchored, not improvised.

---

## 4. The script model — compressing the answer without losing the voice

Stored answers are ~150–230 words. A 60–90s spoken Short is ~150–225 words *total*
across all beats. So compression is modest but must be ruthless about filler while
*adding* connective teaching beats. The script is a **structured object**, not
free prose, so the renderer payload can be compiled from it deterministically
(this is what makes the match gate possible — see §5).

### 4.1 Beat structure (the "triangulation arc")

```
HOOK         (~12–20 spoken words)  Pose the question on the anchor verse.
                                    Name the concrete artifact (the word/refrain).
                                    DO NOT answer yet. Open the loop.
SET          (~20–35 words)         Show the anchor verse; highlight the pivot
                                    word(s). "Notice what it does NOT say…"
TURN         (~25–45 words)         The cross-reference that reframes it.
                                    "Okay — here's where it gets interesting:" →
                                    second verse, highlight the parallel word.
(TURN-2)     (optional, ~20 words)  A third verse only if it's the keystone
                                    (e.g. 2:255 for 39:42). Skip if it bloats.
LAND         (~20–35 words)         The quiet resolution. Proportioned confidence.
                                    "The most we can fairly say is…"
OUTRO        (silent)               Brand splash + SUBSCRIBE. No narration.
```

Total target: **120–180 spoken words → ~55–80s**. Hard ceiling 95s.

### 4.2 The structured script object (persisted as `script_json`)

```jsonc
{
  "qa_id": 3913,
  "anchor_ref": "39:42",
  "title": "Why does the Qur'an use the death-verb for sleep?",   // = the question, curiosity-gap
  "theme": "death-and-sleep",
  "beats": [
    { "kind": "hook",
      "narration": "One Arabic verb — yatawaffā, 'to take in full' — does two jobs in this verse: dying, and falling asleep. Why the same word?",
      "verse": null,                       // hook may show an Arabic artifact, not a full verse
      "artifact_arabic": "يَتَوَفَّى", "artifact_translit": "yatawaffā", "artifact_gloss": "takes in full"
    },
    { "kind": "set",
      "narration": "Notice what it doesn't say — not that sleep resembles death, but that one verb performs both. Then it forks: He holds one self back, and sends the other on.",
      "verse": { "ref": "39:42",
                 "highlight_phrase_en": "takes the souls",
                 "highlight_words_ar": ["يَتَوَفَّى"] }     // SEMANTIC intent, by surface form
    },
    { "kind": "turn",
      "narration": "Now 6:60 runs the same scene with a bolder verb — baʿatha, the resurrection word — for waking up in the morning.",
      "verse": { "ref": "6:60",
                 "highlight_phrase_en": "raises you up",
                 "highlight_words_ar": ["يَبْعَثُكُمْ"] }
    },
    { "kind": "land",
      "narration": "So sleep is spoken of as death, and waking as resurrection. The proof offered for a second raising isn't exotic — it's last night.",
      "verse": null }
  ],
  "outro": { "kind": "outro" }
}
```

**Key move:** beats carry *semantic* highlight intent —
`highlight_phrase_en` + `highlight_words_ar` (by **surface form**), **not** raw
indices. Indices are *compiled* later from the DB (§5.2). This is what lets the
gate re-derive and verify rather than trust hand-authored numbers.

### 4.3 Voice rules (inherited + video-specific)

- Inherit `qa_workflow_brief.md` *in full*: Quran-internal only; never fabricate a
  ref; Arabic terms transliterated **and** glossed, never bare Latin identity
  labels; distinguish stated vs. inferred; proportion confidence.
- Add the **spoken register**: 1–2 connective teaching beats max
  ("Okay — here's where it gets interesting", "Notice what it doesn't say"),
  each of which must *precede a real turn* (guarded so they're not filler).
- **TTS hygiene** (via `sanitize_for_tts` + extensions): verse refs spoken as
  words ("six, verse sixty" not "6:60"); Arabic words spoken via their
  transliteration; numbers spelled; no markdown.

---

## 5. THE TWO GATES

Every candidate passes **both** gates before it can become an upload-eligible row.
Both gates **fail closed**: on an LLM timeout / malformed output / any ambiguity,
the verdict is **reject**, not pass. (This *inverts* the existing
`educational_interestingness` default, which fails open — deliberate, because the
channel's mandate here is quality over quantity.)

### 5.1 Gate A — Editorial / punchiness ("would someone subscribe?")

**Deterministic pre-checks (cheap, run first):**
- Spoken word count within [110, 190]; estimated duration ≤ 95s (model in §5.4).
- No post-Quranic terminology (reuse the label-scan: `Muslims|Islamic|in Islam|
  halal|hadith|…`; transliterated Quranic terms *with a gloss* are fine).
- Question present in the hook; answer **not** leaked in the hook (open-loop check).
- ≤ 2 verses displayed total (punchiness).
- Every `cited_ref` and every displayed verse exists in `verses`.

**LLM judge panel (fail-closed, diverse lenses — per the workflow quality
patterns).** Three judges, distinct personas, each returns a structured verdict:
- **The scroller** — "In the first 3 seconds, is there a reason not to swipe?"
  Scores hook strength + curiosity gap. Rejects synonym-swaps and non-questions.
- **The student** — Does it actually triangulate (converge via named evidence)?
  Does the payoff *answer* the hook? Is the teaching voice present (speaks-to, not
  preaches), confidence proportioned?
- **The doctrine checker** — Quran-internal? No fabricated/────off-point refs? No
  post-Quranic terms? Arabic rendered Arabic+English?

A composite **subscribe-worthiness** must clear a threshold AND no hard axis
(hook, payoff, doctrine) may fail. Majority-reject ⇒ reject. Verdicts + reasons
are stored on the row for the admin UI.

**Repair-once loop:** on a *soft* fail (e.g. too long, weak hook), auto-attempt
one re-compression / hook-regeneration, then re-judge. Still failing ⇒ **skip the
Q&A** (record reason; do not force a weak video).

### 5.2 Gate B — Airtight script ↔ video match (the part you said must be airtight)

This is the centerpiece. The defense is layered so no single bug class survives.

#### The verified ground truth (why naive index math fails)
Morphology `word_pos` in `quran.db` is keyed at the **word level** (with a
separate `segment` column for proclitics), so for *most* verses `word_pos` count
== whitespace-token count. **But 116 verses diverge**, in two deterministic
buckets:

1. **Basmala / verse‑1 offset (delta 4):** every surah-opening verse (2:1, 3:1,
   4:1, …). When `arabicText` is basmala-stripped before rendering, highlight
   indices shift by 4. *This is exactly the 95:1 / 97:1 class you already hit.*
2. **Orthographic multi-token words (delta 1):** 2:181, 8:6, 13:37, 37:130 —
   morphology counts `إِلْ يَاسِينَ` as **one** `word_pos`, but the renderer's
   `arabicText.split(/\s+/)` makes it **two** tokens, so every highlight after it
   drifts +1.

The renderer (`VerseFlowPage.tsx`) highlights by 1‑based **whitespace** index of
the *string it is handed*, and silently no-ops a bad index or a non-substring
English phrase. So the gate must validate against the **exact shipped string**,
by **surface form**, not by trusting `word_pos == whitespace_index`.

#### Layer 0 — Single source of truth (eliminate hand-authoring)
The payload is **compiled from the structured script**, never hand-written. The
compiler (`build_qa_payload`) does, per verse beat:
1. Fetch verse text + translation from the **same** source the website shows
   (`_verse_data` → `ai_translations.revised_text || translations.text_en`).
2. Produce `arabicText` via the **same** `_strip_bismillah` + `_strip_uthmani_marks`
   the renderer path uses → this is the *exact* string shipped.
3. Tokenize that shipped string `split(/\s+/)`; locate `highlight_words_ar`
   (the script's intended surface forms) **within that token list** to get the
   1-based indices. (Surface-form match auto-corrects both divergence buckets:
   if the basmala wasn't stripped, or an orthographic split shifted things, the
   form won't match at the wrong index.)
4. Resolve `highlight_phrase_en` against the **actual** `translation` string;
   require it to be a real case-insensitive substring.

#### Layer 1 — Deterministic assertions (Python, pre-render, fail-closed)
For every verse beat in the compiled payload, assert:
- `arabicText` **hash-equals** the freshly DB-derived stripped text (no
  hand-authored drift, no `^`-artifact strings).
- Every `highlightWordIndices` entry ∈ `[1, len(tokens)]`.
- The **token at each highlighted index equals the intended surface form**
  (`highlight_words_ar[i]`) after a normalization (NFC + strip tatweel) — this is
  the assertion that actually kills the 116-verse drift class.
- `highlightTranslationText` is a verbatim case-insensitive substring of
  `translation` (else the English pill silently vanishes ⇒ hard fail).
- `translation` hash-equals the DB translation.
- Every displayed `ref` and every `cited_ref` exists; the displayed Arabic equals
  the canonical verse (reuse `verse_integrity_review.py`'s correspondence check so
  the Arabic↔English pairing itself is sound).

#### Layer 2 — Renderer self-report (close the Python↔renderer gap)
Add a `--verify` mode to `render.mjs` (or a tiny `verify.mjs`) that runs the
*actual* slide logic (the same union of `highlightWordIndices` + legacy
`highlightWordIndex`, the same quote normalization) and emits a JSON sidecar:
`{ slideIndex, painted_token_indices, painted_tokens, english_span }`. Python
asserts **renderer-truth == intent**. This catches any divergence between our
Python derivation and the renderer's real behavior (e.g. the legacy-field union,
curly-quote handling) without pixels.

#### Layer 3 — Visual probe (optional belt-and-suspenders)
Render the single frame where each highlight is on-screen; assert (via Remotion
DOM data-attributes, not OCR) that the pill wraps the intended token. Strongest,
but heavier; recommended as an opt-in for a first batch / spot-checks, not every
video, since Layer 2 already gives deterministic renderer-truth.

#### Layer 4 — Provenance lock (defense against later DB edits)
Store on the row a `match_snapshot` = hashes of (each `arabicText`, each
`translation`, the resolved index sets). **Re-assert at render time AND again at
pre-upload** against the live (prod) DB. If a verse/translation was edited after
the script was built, the hash mismatch **blocks** render/upload (fail-closed).
This is what makes the gate *stay* airtight after the row leaves your machine.

#### Layer 5 — Caption + audio integrity
- Karaoke alignment spans the full narration (no uncovered tail).
- Karaoke is suppressed on opted-out slide types (the bespoke hook/answer cards),
  matching `KARAOKE_OPTED_OUT`, so captions never overlap baked-in text.
- The render's MP4 has a non-silent audio stream (the uploader's ffprobe guard
  already refuses silent videos; we assert it earlier so we fail in QC, not at
  upload). Guard the ElevenLabs `DISABLE_GENERATION` kill switch is **off** for
  real builds.

> **Net effect:** a video can only become upload-eligible if, for every verse it
> shows, the lit word is provably the intended word (by surface form, confirmed by
> the renderer itself), the English pill provably renders, the Arabic↔English
> pairing is sound, and none of it has drifted from the DB since. The 116-verse
> divergence and the basmala class are caught structurally, not by luck.

### 5.3 Gate ordering & cost discipline
```
candidate
  → Gate A deterministic pre-checks         (free)
  → Safety gate (verse moderation, cached)  (cheap)
  → script compression (Claude)             ($ — only on survivors)
  → Gate A LLM panel (fail-closed)          ($ — only on survivors)        ──reject──▶ skip (logged)
  → Gate B Layers 0–1 (deterministic)       (free)                          ──fail──▶ repair-once → skip
  → render (Remotion) + Gate B Layer 2/(3)  ($ TTS once, cached)            ──fail──▶ skip
  → status = gate_passed   (awaits human approval)
```
TTS is only ever paid on a script that already cleared A + Gate B static checks,
and is cached by text hash so re-renders are free.

### 5.4 Duration model
Total length is **narration-driven** (renderer bumps each slide to audio+0.4s).
So duration is a function of spoken text. We fit a words-per-second constant from
the **existing `audio-cache`** (we have real ElevenLabs mp3 durations + their
texts) to predict duration from word count, then enforce the ≤95s ceiling at the
deterministic pre-check — before paying for TTS.

---

## 6. Renderer / slide vocabulary

The Q&A arc (question → verse → cross-ref → land) maps cleanly onto existing
slides, but the *framing* differs from the three existing series, so the channel
benefits from a distinct visual identity.

**Recommended (Phase 1): a small bespoke "Ponder" series look** — its own accent
color (proposal: deep emerald or indigo, distinct from rose/amber/yellow) with:
- `qa-question` (NEW): the hook card — verse ref + big Arabic artifact +
  transliteration + the question text. Karaoke-opted-out (text baked in).
- `verse-flow` (REUSE): the verse on screen with the pivot word(s) highlighted +
  English phrase pill. Used for SET and TURN beats.
- `qa-land` (NEW) *or* reuse `word-lens`: the closing payoff card — the resolution
  line, optionally over the keystone Arabic word. Karaoke-opted-out.
- `outro` (REUSE): brand splash + SUBSCRIBE (silent).

Adding a slide type costs: a zod variant in `types.ts`, a `src/slides/*.tsx`
component, a `SlideRenderer` case, and a **renderer rebuild + redeploy**.

**Fast path (Phase 0, ship-this-week):** compose only *existing* slides —
repurpose `translation-reveal` as the question card (relabel its rows) +
`verse-flow` ×1–2 + `word-lens` as the land + `outro`. Zero renderer code change;
validates the whole pipeline end-to-end before investing in bespoke visuals.

I recommend **Phase 0 to prove the pipeline + gates, then Phase 1 for identity.**

---

## 7. Offline build → online push → upload

Your constraint: build the script offline here, push to the live DB. Two viable
shapes; I recommend the first because it keeps the airtight gate where pixels can
be inspected.

### Recommended: build + gate + render + QC offline, ship the verified MP4
1. **Offline batch builder** `qa_video_gen.py` (mirrors the existing `*_ai.py`
   CLIs): resumable, idempotent (`UNIQUE(qa_id)`), `--dry-run`, writes gate
   verdicts to a journal (`reviews/qa_video.jsonl`). For each rated‑5 Q&A: run the
   whole §5.3 flow locally, producing a `gate_passed` row + an MP4 + a
   `match_snapshot`.
2. **Local visual QC** (the place to catch the matching bug): Layer 2 self-report
   on every video; Layer 3 frame probe on the first batch; eyeball the first N.
3. **Push** rows via `sync_tables_to_prod.sh qa_videos qa_pipelines …` (existing,
   additive `INSERT OR REPLACE`).
4. **MP4 transport** (the gap: the sync script moves *rows, not files*): add a
   thin authenticated `POST /api/admin/qa-videos/<id>/import-mp4` (multipart) that
   stores the file under the prod video dir and sets `status='rendered'`,
   `triggered_by='scheduler'`. (Alternatively `scp`/`docker cp`; the endpoint is
   cleaner and auditable.)
5. **Pre-upload re-gate (Layer 4)** on prod: in the existing sanity-check slot,
   re-assert the `match_snapshot` against the prod DB. Drift ⇒ `auto_upload_skipped`.
6. **Upload**: the existing `_youtube_upload_tick` drains `status='rendered'`,
   `triggered_by='scheduler'` rows oldest-first on the global schedule — add a
   third eligible-row branch for `qa_videos` and a `_perform_qa_youtube_upload`
   (clone of the educational one). Title = the question; description = 1-line
   teaser + `al-nuqta.com/read/<ref>` + cited refs; tags from theme.

### Alternative: push script only, render on prod
Push `script_json` + `payload_json` + `match_snapshot`; render on prod from the
synced script (prod has the renderer in Docker). Reproducible *iff* prod
`quran.db` matches local (it's synced). Saves MP4 transport but moves the visual
QC away from where you can inspect it. Layer 4 still guards drift. Viable, but I
prefer rendering offline so the *pixels you approve are the pixels that ship.*

---

## 8. Admin UI

- **New page `AdminQAVideos.tsx` at `/admin/qa-videos`** (clone `AdminEducational`):
  list rows (anchor ref, theme, status pill, gate scores) → expand to preview the
  **script beats**, the **gate verdicts** (A panel + B layer results), and the
  **rendered MP4** (served via `?token=` query like the educational video route) →
  **one-click Approve** (`gate_passed → approved`, making it upload-eligible) or
  Reject/Edit-script-and-re-gate. Mirrors `overrideEducationalJudge` semantics.
- **A 5th tab on `/admin/scheduler#qa`** for the generation + upload cadence
  (reuses the schedule-card + activity-table pattern). The global YouTube upload
  schedule already covers posting; this tab adds the Q&A generation schedule.
- **Wiring checklist (don't miss any):** `App.tsx` route allowlist regex appears
  in **two** places (isKnownRoute + auth gate); `AdminPage.tsx` `getAdminRoute()`
  + `ADMIN_SECTIONS`; `SchedulerPage.tsx` `TabKey` + `HASH_TO_TAB` + `TabBar` +
  render switch. Four/five edit sites.

The existing `/admin/qa` (AdminAssistantQA) stays the *content* queue; the new
page is the *video* queue. A row in the video queue links back to its `qa_id`.

---

## 9. Data model

New tables, modeled on the educational ones (kept separate so we don't have to
rebuild the educational `type` CHECK constraint):

```sql
CREATE TABLE qa_videos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  qa_id INTEGER NOT NULL,                 -- FK assistant_conversations.id (provenance)
  anchor_ref TEXT NOT NULL,               -- 'chapter:verse'
  theme TEXT,
  title TEXT,                             -- the question (curiosity-gap)
  script_json TEXT,                       -- the structured script (§4.2)
  payload_json TEXT,                      -- the compiled renderer payload
  match_snapshot TEXT,                    -- hashes for Layer-4 drift lock
  format TEXT DEFAULT 'short',
  filename TEXT, file_size INTEGER,
  status TEXT DEFAULT 'candidate',        -- candidate→script_ready→gate_passed→approved→rendered→uploaded ; rejected_* ; failed
  -- Gate A
  punch_score REAL, punch_verdict TEXT, punch_reason TEXT, punch_model TEXT,
  -- Gate B
  match_ok INTEGER, match_report TEXT,    -- JSON: per-layer results
  -- safety
  safety_ok INTEGER,
  -- youtube
  triggered_by TEXT, uploaded_to_youtube INTEGER DEFAULT 0, youtube_video_id TEXT,
  auto_upload_skipped INTEGER DEFAULT 0,
  youtube_title TEXT, youtube_description TEXT, youtube_tags TEXT,
  error_message TEXT, created_at TEXT DEFAULT (datetime('now')), completed_at TEXT,
  pipeline_id INTEGER,
  UNIQUE(qa_id)
);
CREATE INDEX idx_qa_videos_status ON qa_videos(status);

-- mirror educational_pipelines / _schedules / _schedule_runs for cadence,
-- each *_runs table with UNIQUE(scheduled_time) to prevent double-fires under
-- multiple gunicorn workers.
```

Status lifecycle:
```
candidate → script_ready → gate_passed → approved → rendered → uploaded
                  └─(Gate A/B/safety reject)→ rejected_uninteresting | rejected_match | rejected_unsafe
   (any) → failed (with error_message)
```
Note the **human approval** state (`gate_passed → approved`) — automated gates
make a video *eligible*; a human still confirms before it can upload.

---

## 10. Features you may not have asked for (worth considering)

1. **Surface-form highlight validation** (the keystone, §5.2 Layer 1) — validating
   the *word*, not the *index*, is what makes the gate immune to the 116-verse
   divergence and any future tokenization change.
2. **Renderer self-report `--verify`** — the renderer tells us which tokens it
   actually painted; we diff against intent. Kills script↔render drift
   deterministically, no OCR.
3. **Provenance lock + pre-upload re-gate** — the video can't drift from the DB
   after it leaves your laptop; a late verse edit blocks the post, not ships a bug.
4. **Hook A/B + judge** — generate 3 opening lines, judge picks the thumb-stopper.
   The first 3 seconds decide the video.
5. **Open-loop enforcement** — a structural check that the answer doesn't leak in
   the hook; retention depends on the unresolved question.
6. **Anti-repetition / freshness ledger** — track used verses, cross-refs, and
   "moves" (e.g. "same verb for X and Y") so the channel never feels formulaic;
   the planner de-prioritizes near-duplicate insights. (Reuses `assign_themes_ai`.)
7. **Theme tagging → auto-playlists** — route videos into series playlists
   ("death & sleep", "light", "the pen", "mercy"); the uploader already supports
   playlists.
8. **Two-tier output** — a ≤60s Short (default) and an optional ~90s cut, mirroring
   educational's short/long voiceovers.
9. **Cost guard + dry-run estimate** — TTS only on gate-passed scripts; a
   `--dry-run` prints predicted ElevenLabs spend + predicted durations before any
   API call.
10. **Read-aloud naturalness gate** — flags tongue-twisters, ref formatting TTS
    mangles, and an Arabic-in-narration policy (speak the gloss, show the Arabic).
11. **Self-healing batch** — failed gate ⇒ one auto-repair attempt ⇒ else skip;
    loop the batch until a target count of *passing* videos is reached, not a
    target count of *attempts* (quality-anchored, like loop-until-dry).
12. **"Evidence faithfulness" check** — every verse the script quotes/paraphrases
    is checked that the gloss is faithful to the DB translation (reusing the
    `verse_integrity_review` correspondence judge), so the triangulation can't
    misquote a cross-ref.
13. **Frame-0 thumbnail export** (for the long cut / non-Shorts) — export the
    question card as a still for a curiosity-gap thumbnail.
14. **Per-video "why we skipped" log** — surfaced in the admin UI so you can see
    *why* a rated‑5 Q&A didn't become a video (too long, weak hook, match fail) —
    transparency into the quality bar.

---

## 11. Risks & mitigations

| Risk | Mitigation |
|---|---|
| **Highlight mismatch (your #1 concern)** | §5.2 surface-form validation + renderer self-report + provenance lock + pre-upload re-gate; the 116 divergent verses are enumerated and caught structurally |
| Silent English-pill no-op (non-substring) | Hard-fail Layer 1 substring assertion |
| Basmala / verse-1 offset (95:1 class) | Compile indices against the *shipped* basmala-stripped string; surface-form match catches any offset |
| LLM gate fails open → ships junk | Both gates **fail closed**; human approval still required |
| Silent (audio-less) MP4 uploaded | ffprobe guard + assert `DISABLE_GENERATION` off; fail in QC not at upload |
| Voice drift under compression | Inherit `qa_workflow_brief.md` + 3 compressed gold exemplars; a voice-axis judge; repair-once |
| MP4 doesn't reach prod | Dedicated import endpoint (rows-only sync won't carry files) |
| Double-fires under multiple workers | `UNIQUE(scheduled_time)` on every new `*_runs` table |
| OAuth circuit breaker stalls all uploads | Pre-existing behavior; surfaced in the scheduler UI; unchanged |
| Fabricated/off-point cross-ref | Existence + faithfulness checks on every `cited_ref` (doctrine: never fabricate) |
| Burning ElevenLabs/Claude budget on rejects | Gate ordering: TTS/LLM only on survivors; sha256 cache; dry-run cost estimate |

---

## 12. Phased rollout

- **Phase 0 — Prove it (compose existing slides, ~1 batch of 5).** Builder +
  compression + both gates + render via `translation-reveal`/`verse-flow`/
  `word-lens`/`outro`. Manual MP4 transport. Eyeball + Layer 2/3 verify. Goal:
  validate the gate catches a *planted* mismatch (mirror the integrity-review
  smoke test) and that the voice survives compression.
- **Phase 1 — Identity + UI.** Bespoke `qa-question` / `qa-land` slides + accent
  color; `AdminQAVideos.tsx` review queue; import-MP4 endpoint; scheduler tab.
- **Phase 2 — Scale + automation.** Scheduler-driven generation; freshness ledger;
  playlists; two-tier output; cost dashboards. Run the 443-row pool through,
  expecting only a fraction to clear the bar.
- **Phase 3 — Polish.** Hook A/B, thumbnails, read-aloud gate, analytics
  feedback (which themes/hook styles retain best → bias the planner).

---

## 13. Decisions I need from you (with my recommendations)

1. **Slide visuals:** Phase 0 compose-existing first, then build bespoke
   `qa-question`/`qa-land` slides? *(Rec: yes — prove pipeline before pixels.)*
2. **Render location:** render+QC offline and ship the MP4 (my rec), or push
   script and render on prod? *(Rec: offline — approve the exact pixels that ship.)*
3. **Approval bar:** gate on `quality_score=5` + automated gates + **human
   approve** (my rec), or also require the Q&A itself be `review_status='approved'`
   first (near-empty today)? *(Rec: score‑5 + gates + new human approve step.)*
4. **Tables:** new `qa_videos*` tables (my rec, avoids touching the educational
   CHECK constraint) or extend educational with a 4th type?
5. **Series name / brand:** working title "Ponder" / "One Verse, One Question" /
   "Worth Pausing On" — your call on naming + accent color.
6. **Match-gate depth for v1:** Layers 0/1/2/4 as the airtight core (deterministic,
   no OCR), with Layer 3 frame-probe as opt-in spot-check? *(Rec: yes.)*

---

*Nothing here is built yet. On your sign-off (and answers to §13) I'll implement
Phase 0 end-to-end against a 5-video batch so you can watch the gates work — including a
deliberately planted highlight mismatch to prove Gate B catches it — before we scale.*
