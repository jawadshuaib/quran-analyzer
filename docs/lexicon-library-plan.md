# The Lexicon Library — Project Plan

**Internal classical-dictionary reference for al-nuqta.com.**
Give every Qur'anic **root** and **word** a panel of **harmonized English definitions
drawn from the great classical Arabic dictionaries** (sourced respectfully from
arabiclexicon.hawramani.com), one per author, ordered by author date — rewritten
for readability while preserving nuance/grammar/etymology, each linking to a second
view with the **original Arabic + a faithful English translation**. Surfaced on the
root page, word page, and word-hover tooltip; ejtaal.net stays as an external
"additional reference." Built gradually via a **`/loop`** on the Claude subscription
(no paid API), reusing the `root_poetic_lexicon` → admin-review → prod-sync machinery.

Intellectual spine: **Ibn Fāris's Maqāyīs** gives each root's *semantic core*;
**al-Rāghib's Mufradāt** gives its *Qur'anic realization*.

## 1. Surfaces & views
- **Root page** `/root/<bw>`: "Classical Dictionaries" accordion, one row per author
  (date-ordered), harmonized English definition + author/date/description + "View original →".
- **Word page** `/word/<s>:<a>/<pos>`: same panel via the word's root; the specific
  Qur'anic form is highlighted (root-primary granularity — no fabricated per-word entries).
- **Tooltip**: internal "Dictionaries" link alongside the retained ejtaal + Quranic-Corpus links.
- **View 2 (sources)**: per author, original Arabic beside a faithful English translation,
  with a provenance link back to hawramani + ejtaal.

## 2. Dictionary selection (Qur'an-first; hawramani WordPress category IDs)

**Phase 1 (8, all public-domain), ordered by author death year:**
| Author (d.) | Work | cat | lang | role |
|---|---|---|---|---|
| Ibn ʿAbbās (687) | Gharīb al-Qurʾān fī Shiʿr al-ʿArab | 41 | ar | earliest Qur'an gloss, proven from pre-Islamic poetry |
| al-Farāhīdī (786) | Kitāb al-ʿAin | 5 | ar | earliest attestation |
| Ibn Fāris (1004) | Maqāyīs al-Lugha | 9 | ar | root semantic-core / etymology |
| al-Rāghib (1109) | al-Mufradāt fī Gharīb al-Qurʾān | 33 | ar | Qur'anic semantics (core) |
| al-Zamakhsharī (1143) | Asās al-Balāgha | 11 | ar | literal vs figurative |
| Ibn Manẓūr (1311) | Lisān al-ʿArab | 3 | ar | comprehensive + shawāhid |
| al-Fayyūmī (1368) | al-Miṣbāḥ al-Munīr | 19 | ar | clean baseline gloss |
| E. W. Lane (1876) | Arabic-English Lexicon | 50 | **en** | English anchor (halves translation cost, roots ا→ق) |

**Phase 2 (depth):** al-Jawharī Ṣiḥāḥ (8), Ibn Sīda al-Muḥkam (10), Abū Ḥayyān Tuḥfat
al-Arīb (18), Firūzābādī al-Qāmūs (21), al-Zabīdī Tāj al-ʿArūs (27), Salmone (52, en),
and **Farāhī Mufradāt al-Qurʾān (40)** *only after clearing the Iṣlāḥī critical-edition
copyright — source Farāhī's own text, not the editor's apparatus*.

**Excluded** (per the Qur'an-only principle): all hadith gharīb (Abū ʿUbayd 6, al-Nihāya
13, al-Majmūʿ al-Mughīth 12), toponyms (Muʿjam al-Buldān 53), personal names (Sultan
Qaboos 49, Ishtiqāq al-Asmāʾ 4), and the *iṣṭilāḥāt* technical-term glossaries (al-Taʿrīfāt
20, Kashshāf 26, Maqālīd 22, al-Tawqīf 24, Dastūr al-ʿUlamāʾ 25 — they codify post-Qur'anic
jargon, the exact thing the site avoids); Dozy (34, French/post-classical); modern
in-copyright monographs (Maududi 44, al-Badawī 43, al-Barakātī 29).

## 3. Data model (clone the lexicon stack; add a source dimension)
- `dictionaries(id, slug, name_ar, name_en, author, author_death_year, century,
  description_en, language, is_quran_specific, hawramani_category_id, source_url_base,
  phase, sort_order)`
- `dictionary_entries(id, root_buckwalter, root_arabic, dictionary_id, original_text_ar,
  translation_en, harmonized_en, source_url, source_anchor, scrape_hash,
  review_status DEFAULT 'pending', hidden DEFAULT 0, confidence, gen_meta, raw_response,
  created_at, edited_at, UNIQUE(root_buckwalter, dictionary_id))`
- `root_slug_index(normalized_root, arabic_slug, page_url, hawramani_post_id)` — built once
  from the sitemaps; resolves a Buckwalter root → the canonical hawramani page (handles the
  hamza-carrier gotcha: أ U+0623 ≠ ا U+0627).

Buckwalter-keyed throughout; `review_status`/`hidden` pending-by-default; ships via
`sync_tables_to_prod.sh dictionaries dictionary_entries`.

## 4. Scraper (`dict_scrape.py`) — respectful by design
- **One page = one root** (`/<arabic-root>/`) aggregating all dictionaries as labeled
  sections; text is in server-rendered HTML (plain GET). **REST is unusable** for
  text/search (content.rendered empty, collection queries time out) — use it only for
  the categories registry.
- **Discovery**: sitemaps (~149 static XML) → `root_slug_index`, once.
- **Fetch**: on-demand per Qur'anic root (~1,642 pages), **strictly serial, 1 req / 4 s**,
  exp backoff (4→15→60→300 s), whole-run pause on repeated slowness, 60–90 s timeout,
  transparent UA `al-nuqta-root-scraper/1.0 (+al-nuqta.com; jawad.php@gmail.com)`,
  courtesy email to Hawramani. ≈2 hrs, overnight.
- **Cache** raw HTML per slug (static since 2015 — never re-fetch); resumable work queue.
- **Parse**: split page DOM on dictionary-section headings; label each block by
  exact-matching its heading to the category name; store per (root, dictionary).

## 5. Harmonization `/loop` (subscription, no API)
Follows the lexicon "overnight run" pattern. **Unit = one root** (frequency-ordered).
Each iteration fans out one subagent per dictionary block to produce, *from the scraped
text only*: (a) `translation_en` (faithful, close), (b) `harmonized_en` (readable — keep
sense-distinctions, grammatical method, etymology, shawāhid; drop narrator chains,
redundant synonyms, digressions). A validator gates faithfulness (traceable to source —
anti-hallucination), attribution, length, no post-Qur'anic codified meanings, valid JSON.
`_apply_dict_drafts.py` writes **pending** → `/admin` review → approve → sync.
Paced `ScheduleWakeup` loop, self-terminating when the worklist is exhausted.

## 6. Serving + frontend
- `GET /api/root/<bw>/dictionaries` (harmonized, date-ordered + author meta, approved-only);
  `GET /api/dictionary-entry/<id>` (original_ar + translation_en for View 2).
- `DictionaryPanel.tsx` (accordion) + `DictionarySourcesPanel.tsx` (original|translation)
  wired into `RootPage.tsx` + `WordAnalysisPage.tsx`; internal "Dictionaries" link added to
  `WordTooltip.tsx`.

## 7. Admin + sync
Clone `_POETRY_ADMIN`/`AdminPoetry.tsx` with `kind='dictionary'` (approve/edit/hide/delete +
bulk, filter by dictionary/status). Server enforces `approved AND NOT hidden` on public reads.
Ship via `sync_tables_to_prod.sh` + restart.

## 8. Guardrails (scripture-adjacent)
We **report attributed lexicographers**, never assert one meaning; harmonization must be
faithful to the source (original always one click away); chronological ordering *is* the
methodology. Pre-codification sources (Ibn ʿAbbās, ʿAin, Maqāyīs, Asās) align with the
site's Qur'an-only-meaning principle.

## 9. Copyright & etiquette
Phase 1 = all PD (classical + Lane). Harmonize from the underlying text; write our own
English; never lift a modern editor's apparatus. Attribute + link back. Scrape at 1 req/4s,
cached, backoff, transparent UA, courtesy email.

## 10. Coverage & phasing
- Scrape ~1,642 root pages (one-time, overnight, ~2 hrs).
- Harmonize Phase-1: ~8 dicts × ~1,500 roots ≈ ~12k definitions via `/loop`,
  frequency-ordered (top ~300 roots first).
- Then serving+UI, then Phase-2 dictionaries.

## 11. Status (as of 2026-07-24)

### Done
- **Sitemap slug-index** (`root_slug_index`, 116,821 slugs): built once, resolves ALL
  1,642 Qur'anic roots to their hawramani page(s), including the bare/hamza-carrier
  split. This already covers the full corpus — **no re-crawl needed** to scrape the
  remaining roots later, only more page fetches.
- **Dictionary roster locked at 16** (Phase 1's 8 + Phase 2's Ṣiḥāḥ/Muḥkam/Tuḥfat
  al-Arīb/Qāmūs/Tāj al-ʿArūs/Salmoné + two user-approved additions, Mukhtār al-Ṣiḥāḥ
  and al-Muḥīṭ fī l-Lugha). Farāhī stays deferred (copyright).
- **Scrape: top-300 roots** (of 1,642 distinct roots in the Qur'an), frequency-ordered,
  0 page-misses. These 300 roots account for **41,705 of 49,968 root-bearing word
  tokens in the Qur'an — 83.5% of all occurrences** — so the current corpus already
  covers the large majority of what a reader actually encounters verse to verse. The
  remaining 1,342 roots are the long tail (16.5% of occurrences; many appear only a
  handful of times in the whole text).
- **3,571 dictionary entries** harmonized (avg. 11.9 dicts/root; some dicts are
  genuinely sparse over this root-set — e.g. Ibn ʿAbbās's early gloss only 5/300,
  Kitāb al-ʿAin 95/300 — that's the source, not a gap in scraping).
- **Translation backfill** (task #125): all 46 entries flagged `translation_pending`
  (giant Lisān/Tāj/Lane articles that stubbed `translation_en` under output budget)
  were filled via a dedicated translation-only pass. 0 blank/pending translations
  remain across all 3,571 rows.
- **Full self-review pass** (task #126): every one of the 3,571 entries was reviewed
  by a paced `/loop` (91 batches of ~40, Claude-subscription subagents, no API) against
  a 5-test rubric (faithful / no imported post-Qur'anic doctrine / neutral evidence
  voice / complete / well-formed). Result: **3,567 approved (incl. 117 edited first —
  typos, garbled Arabic/romanization, mis-provenance, stub-translation repairs), 4
  rejected+hidden as wrong-root misfilings** (id 214 `ywm`, 655 `smE`, 2085 `qDy`, 2268
  `nhy`), **1 deferred to a human call** (id 1190 `Amm` — a source misattribution the
  reviewer couldn't resolve itself; since reviewed and approved in `/admin/dictionaries`).
  Doctrine-sensitive roots (ṣalāt, zakāt/niṣāb, jihād, ḥajj, ikhlāṣ/tawḥīd, shafāʿa,
  hijra, badāʾ, waṣiyy/farḍ, nushūz, anṣāb, jizya, ribā, shayṭān, munkar…) were kept as
  each author's *attributed* account, never asserted as fact.
- **Serving + admin + frontend built and verified in preview**: `GET
  /api/root/<bw>/dictionaries` + `GET /api/dictionary-entry/<id>` (self-healing
  tables); `/api/admin/dictionaries[/stats]` + PATCH + bulk (mirrors the poetry admin
  pattern); `DictionaryPanel.tsx` wired into `RootPage`/`WordAnalysisPage`/
  `WordTooltip`; `AdminDictionaries.tsx` review tab. `npm run build` clean.

### Not yet done
- **Not synced to prod / not live on al-nuqta.com.** `sync_tables_to_prod.sh
  dictionaries dictionary_entries` has deliberately not been run.
- **Design changes pending before go-live** (open, not yet specified — 2026-07-24
  decision: finalize these before the current 300-root corpus is shipped to
  production; do not treat the plan above as final UI/UX until that pass happens).
- **The remaining ~1,342 rarer roots are not yet scraped, harmonized, or reviewed** —
  see §12 for the path to completing them. **The scrape cycle has not been restarted**
  and should not begin until explicitly requested.

## 12. Path to completing all 1,642 roots (future work, not started)

The pipeline built for the top-300 pass is a proven, reusable asset — completing the
long tail is a matter of re-running the same stages over the remaining root-set, not
building anything new.

1. **Scrape the remaining ~1,342 roots.** `root_slug_index` already resolves all of
   them, so this is a straight `python3 dict_scrape.py scrape <roots>` (or a `top`
   run over the full 1,642) at the same respectful 1 req/4s serial cadence — no new
   sitemap crawl. Expect lower page-hit density per root than the top-300 (rarer
   roots have thinner coverage in some dictionaries, e.g. Kitāb al-ʿAin, Ibn ʿAbbās).
2. **Harmonize the new entries** via the existing paced `/loop`
   (`_dict_harmonize.js` draft-only Workflow + `_harmonize_tick.py` +
   `_apply_dict_drafts.py`), same mechanics as the top-300 run.
3. **Translation backfill** for any new giant/stubbed entries, reusing
   `_dict_translate.js` + `_apply_translate.py` (the same pass that cleared the 46
   giants in the top-300 set).
4. **Self-review** the new entries with the now-proven loop (`_dict_review.js` +
   `_dict_review_tick.py`, same 5-test rubric) — this pass is validated at 3,571/3,571
   entries with 0 agent errors across 91 batches, so it scales directly.
5. **Admin spot-check** anything newly deferred or rejected, same as the 5 human-flagged
   items from the top-300 pass.
6. **Sync the additions** to prod with the same `sync_tables_to_prod.sh dictionaries
   dictionary_entries` command (incremental — safe to run again over a larger table).

None of this begins until (a) the pending design changes are finalized and the
top-300 corpus has gone live, and (b) the user explicitly asks for the scrape to
resume.
