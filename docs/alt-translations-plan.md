# Alternative translations: plan + pilot (2026-10-19)

> **Status 2026-10-20: built, public-domain only, loaded locally, not on prod.**
> Candidates: Pickthall (1930) and Yusuf Ali (1934) while permissions for the
> other six are looked into (`PUBLIC_DOMAIN`; `--sources` widens it).
> Full run over 6,236 verses: glm-5.3 + deepseek-v4-pro judges ($49), then
> two passes added after this plan was written:
> - **verify**: every claimed error in OUR translation is re-checked by one
>   glm-5.3 reasoning call (deepseek tags "BEST drops 'Indeed'" as
>   `ours_omits`). Calibrated 10/10 planted errors confirmed, 5/5 reversed
>   claims rejected. Of 90 real claims: 25 confirmed, 22 defensible
>   (→ tier 2), 43 rejected. Unverified claims count as rejected.
> - **notes**: the reader note is written from the judges' structured
>   differences in the owner's format — "Pickthall's translation keeps the
>   traditional wording "believed in" for *ʾāmanū*, while our translation
>   renders it as "trusted in"" — with transliterations italicised on load
>   and turned into hover anchors by `align_note_anchors.py` (`alt_notes`).
> Result: tier 3 = 6, tier 2 = 367, tier 1 = 2,476, tier 0 = 3,387; 24 in the
> review queue. Link text: "See translation by X". Total spend ≈ $64.
>
> Pipeline: `judge` (per model) → `verify` → `load --verified` → `notes` →
> `load --verified --notes` → `align_note_anchors.py`. Outputs live in
> `roots/backend/data/alt_translations_cache/runs/` (gitignored).

Under each verse's root-based translation, offer the most Qur'an-faithful of
the openly served quran.com English translations, graded by how much it adds
to ours. Budget: $100 of ollama.com credits.

## What it does

For every verse, two LLM judges see the Arabic, a word-by-word morphology
table (root, lemma, case, person, voice, mood, verb form, attached pronouns),
our translation with its departure notes, and the 8 candidates **blind**
(letters A–H, shuffled per verse with a fixed seed, so translator reputation
and list position cannot sway them). Each judge:

1. scores every candidate 1–5 for fidelity to the Arabic (accuracy plus no
   post-Qur'anic imports: tafsir insertions, named-but-unnamed people,
   honorifics, "Islam" as a religion's name, fiqh specifics) and picks BEST;
2. audits **our** translation word by word for omissions and grammar errors
   (a forced field; it is what made the judges actually check ours);
3. lists each concrete meaning difference between BEST and ours with a type.

The tier is computed **in code** from the difference types, not asked for, so
it is auditable and re-tunable without re-running the model:

| difference type | tier | meaning |
|---|---|---|
| `ours_omits` | 3 | Arabic has it, BEST has it, ours drops it |
| `ours_mistranslates` | 3 | ours breaks grammar (case, person, voice, negation…) |
| `alt_reading` | 2 | a different, Arabic-defensible construal of the syntax |
| `nuance` | 1 | a real shade of meaning ours leaves dim |
| `conventional_sense` | 0 | BEST keeps a traditional word sense our notes deliberately left (believe/trust, prayer/connection, scourge/separate) |
| `alt_imports`, `alt_worse`, wording | 0 | — |

Ensemble of the two judges:
- if either says ≥2, take the higher tier; else the lower (so a light-gray
  link needs both judges to see a real nuance);
- tier 3 auto-shows only when the other judge also says ≥2; otherwise it shows
  as tier 2. Every tier-3 claim goes to an admin review queue, because a
  claimed omission or grammar error in **our** translation is a fix candidate
  for us, not only a reason to show the alternative;
- the shown text is the pick of the judge that saw the most value (its
  explanation is about that text); ties go to the higher combined fidelity.

UI mapping (as requested):

| tier | display |
|---|---|
| 3 | alternative shown automatically under our translation |
| 2 | "Alternative translation by X" wavy-underlined link, dark gray |
| 1 | same link, light gray |
| 0 | nothing |

## Model choice

| judge | setting | $/verse | full Qur'an | notes |
|---|---|---|---|---|
| **glm-5.3** | `think: low` | $0.0084 | **$53** | sharpest on grammar (only one to catch 5:6 in v5); `think:false` is ignored and burns ~27k tokens |
| **deepseek-v4-pro** | `think: false` | $0.0071 | $44 peak / **$22 off-peak** | off-peak = outside 12:00–18:00 UTC weekdays, all weekend; `think:low` still burns 8–13k tokens |
| kimi-k3 | `think: false` | $0.0227 | $142 | no better on the controls than the two above; over budget |

**Recommendation: glm-5.3 + deepseek-v4-pro (off-peak), ≈ $75 for all
6,236 verses**, ~2.5 h per judge at 8 workers. Leaves ~$15 after the pilot for
re-runs of failures. Prices: ollama.com/pricing, per M tokens in/out — glm-5.3
$1.40/$4.40, deepseek-v4-pro $1.32/$3.96 (half off-peak), kimi-k3 $3/$15.
Cached input (the ~1.3k-token system prompt) is billed at ~1/5, so the real
bill should come in under the estimate.

## Pilot

44 verses (30 hand-picked traps — 1:7, 2:3, 3:19, 4:34, 5:6, 9:5, 24:31,
33:59… — plus 14 random) and 9 planted controls:

- 3 **bad candidates** slipped into the pool: a meaning reversal (49:13 "keep
  yourselves apart"), a one-word flip (19:23 "died *after* this"), and a
  tafsir-stuffed fake (2:43 "five obligatory daily prayers… 2.5%… in the
  mosque"). Must score ≤2 and never win.
- 6 **broken versions of our translation**: three dropped phrases (19:23
  destination, 2:43 "with those who bow", 3:15 "approval from Allah"), a
  dropped purpose clause (49:13), swapped persons (52:40), active→passive
  (43:65). Must reach tier 3.

Five prompt iterations, ~$9.40 spent in total:

| version | change | finding |
|---|---|---|
| v1 | gut 0–3 value grade | picking works on all models; value grading blind — deepseek/kimi caught 0/3 broken-ours |
| v2 | typed differences, code-computed tier | ~45% of verses flagged: judges labelled every conventional word our notes reject as "debatable" |
| v3 | forced audit of ours; `conventional_sense` → tier 0 | glm 6/6, deepseek 6/6, kimi 5/6 controls; deepseek still calls synonyms "nuance" |
| v4 | basmala stripped (glm flagged 76:1 "omits the basmala"); synonyms/articles/"or-nor" defined as wording | judges flip-flopped on 5:6 because the word table had no case marking |
| **v5** | case/person/voice/mood in the word table; drop identical-text differences | final, below |

v5 ensemble (glm-5.3 + deepseek-v4-pro):

- planted bad candidates: 3/3 rejected (fidelity 1–2), never picked;
- broken ours: 5/6 → tier 3; the 6th (49:13) → tier 2 + review queue (one
  judge missed it; nothing is lost, it just is not auto-shown);
- real verses: **57% hidden, 41% light gray, 2% dark gray, 0% auto-shown**;
- the one dark-gray case is a genuine one: **5:6** — ours says "wipe your
  heads and your feet", but the Ḥafṣ text we display has accusative
  وَأَرْجُلَكُمْ, which pairs the feet with *wash* (the faces/hands verb); "wipe"
  follows the genitive variant reading. Worth a look regardless of this feature;
- argued departures stay ours: 4:34 ("separate from them" vs "strike/scourge
  them"), 2:3 (trust/believe), 2:43 (connection/prayer) and 3:85
  (self-surrender/Islam) are all hidden (tier 0). In v1–v2 the judges had
  wanted to auto-show "scourge them" over our argued choice;
- picks are stable in quality: when the two judges choose different
  translations, ~2/3 of the time each scores the other's pick equal to its own.
  Winners overall: Saheeh International, Bridges, Pickthall; Hilali & Khan
  ranks last (≈2/5 — tafsir insertions).

Per-verse results: `roots/backend/eval/alt_translations_pilot/`
(`ensemble.json`, raw judge output, controls, verse list).

### Limits found

- Our translation is rarely contradicted on the Arabic, so auto-show (tier 3)
  will be rare in practice; the feature is mostly light-gray links.
- Subtle grammar (case-governed attachment, as in 5:6) is caught only by
  glm-5.3, and not on every run. The case data in the word table was the fix
  that worked; one judge alone would miss these.
- Tier 1 still includes some thin nuances (e.g. "All-Powerful" vs
  "powerful"). If 41% light-gray links is too many, require ≥2 nuances.
- Judge summaries are reviewer-facing ("G shows…"); the UI needs a separate
  reader-facing line (see build step 1).

## Build plan

1. **Prompt v6 (small):** add a `reader_note` field (one plain sentence for
   site visitors, no letters, no "BEST"); re-check on the 53 pilot jobs (~$1).
2. **Tables** (created in `app.py` like the other AI tables):
   - `alt_translation_sources(resource_id, chapter, verse, text)` — the 8
     cleaned translations (footnote markers and markup stripped);
   - `verse_alt_translations(chapter, verse, resource_id, translator, text,
     tier, needs_review, reader_note, judges_json, prompt_version,
     review_status, created_at)` — one ensemble row per verse; raw per-judge
     output kept in `judges_json`.
3. **Full run:** `alt_translations_ai.py judge` per judge over all verses (add a
   `--verses all` shorthand; the pilot passed explicit refs), writing
   JSONL (resumable: completed jobs are skipped on rerun), deepseek scheduled
   off-peak; then an `ensemble` step loads the DB table. Error/retry report
   after each run.
4. **API:** add `alt_translation: {translator, text, tier, note}` (tier ≥1
   only) to the verse payloads the reader and research view already fetch —
   no extra request.
5. **Frontend** (`VerseDisplay.tsx`, `reader/ReaderVerse.tsx`): one
   `AltTranslation` component under the translation — tier 3 expanded, tier
   2/1 a `decoration-wavy` link in stone-600 / stone-400 that expands in place;
   reader note as a tooltip.
6. **Admin:** a review tab for `needs_review` rows (claimed errors in ours),
   with approve/hide; this doubles as a fix queue for our own translation.
7. **Prod sync** of the two tables after review (data-only).

## Decisions for the owner

1. **Licensing.** Pickthall (1930) and Yusuf Ali (1934 original) are public
   domain. Abdel Haleem (OUP), Saheeh International, Usmani, Maududi, Bridges
   and Hilali-Khan are copyrighted; quran.com displays them under its own
   agreements, and being served by its API is not a licence to republish.
   Options: get permission, restrict to public-domain candidates, or show a
   short attributed excerpt with a link to the verse on quran.com.
2. **Light-gray density:** keep tier 1 at ~41% of verses, or tighten.
3. **Tier-3 gating:** auto-show on two-judge agreement (as planned), or only
   after admin approval.
