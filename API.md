# al-nuqta Public API v1

A free, read-only REST API for Quranic text analysis — morphology, Semitic etymology, AI-powered translations, thematic context, and a structured learning curriculum.

**Base URL:** `https://al-nuqta.com/api/v1`

All endpoints are **GET-based**, require **no authentication**, and return **JSON** with a consistent response envelope.

---

## Response Format

Every successful response:

```json
{
  "ok": true,
  "data": { ... },
  "meta": { ... }
}
```

Every error response:

```json
{
  "ok": false,
  "error": {
    "code": "VERSE_NOT_FOUND",
    "message": "Verse 115:1 does not exist",
    "status": 404
  }
}
```

### Error Codes

| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `VERSE_NOT_FOUND` | 404 | The surah:ayah does not exist |
| `ROOT_NOT_FOUND` | 404 | The Buckwalter root is not in the database |
| `SURAH_NOT_FOUND` | 404 | The surah number is invalid |
| `WORD_NOT_FOUND` | 404 | No word at that position in the verse |
| `NO_DATA` | 404 | The verse exists but has no data for the requested resource (e.g., no AI translation generated yet) |
| `INVALID_PARAM` | 400 | Bad query parameter (unknown field name, etc.) |

---

## Endpoints

### 1. Verses

#### `GET /api/v1/verses/{surah}:{ayah}`

The primary endpoint. Returns verse text, translation, word-by-word data, and root summary by default. Use `?fields=` to include additional analysis in a single request.

**Query Parameters:**

| Param | Default | Description |
|-------|---------|-------------|
| `fields` | _(none)_ | Comma-separated list of extra data to include (see below) |
| `related_limit` | `10` | Max related verses when `related` field is requested (1–25) |
| `context_size` | `3` | Surrounding verses per side when `context` field is requested (1–6) |

**Available fields:**

| Field | Description |
|-------|-------------|
| `morphology` | Full morphological features (features_raw) on each word segment |
| `word-meanings` | AI-generated word meanings keyed by position |
| `roots` | Root summary with cognate data (included by default, this is a no-op) |
| `related` | Semantically similar verses ranked by IDF-weighted containment |
| `context` | Surrounding verses in the same surah |
| `ai-translation` | Context-based AI translation with departure notes |
| `thematic-context` | Passage theme, surah role, and Quran-wide thematic links |
| `surah-context` | Narrative progression up to this verse within the surah |
| `grammar` | Morphosyntactic grammar insights |
| `all` | Shorthand for every field above |

**Example — basic:**

```bash
curl "https://al-nuqta.com/api/v1/verses/67:1"
```

```json
{
  "ok": true,
  "data": {
    "surah": 67,
    "ayah": 1,
    "surah_name": "Al-Mulk",
    "text_uthmani": "تَبَـٰرَكَ ٱلَّذِى بِيَدِهِ ٱلْمُلْكُ وَهُوَ عَلَىٰ كُلِّ شَىْءٍ قَدِيرٌ",
    "translation": "Blessed is He in whose hand is dominion...",
    "words": [
      {
        "position": 1,
        "translation": "Blessed is",
        "segments": [
          {
            "form_arabic": "تَبَـٰرَكَ",
            "pos": "Verb",
            "root_arabic": "ب ر ك",
            "root_buckwalter": "brk",
            "lemma_arabic": "تَبَارَكَ",
            "lemma_buckwalter": "tabArak",
            "features": { "person": "3", "gender": "Masculine", "number": "Singular" }
          }
        ]
      }
    ],
    "roots_summary": [
      {
        "root_arabic": "ب ر ك",
        "root_buckwalter": "brk",
        "occurrences": 1,
        "cognate": {
          "transliteration": "b-r-k",
          "concept": "bless / chest",
          "derivatives": [
            { "language": "Hebrew", "word": "בָּרַךְ", "meaning": "To bless" }
          ]
        }
      }
    ],
    "previous": { "surah": 66, "ayah": 12 },
    "next": { "surah": 67, "ayah": 2 }
  },
  "meta": {
    "fields_included": ["default"],
    "response_time_ms": 8
  }
}
```

**Example — kitchen sink:**

```bash
curl "https://al-nuqta.com/api/v1/verses/2:255?fields=all"
```

Returns all of the above plus `ai_translation`, `word_meanings`, `related_verses`, `context_verses`, `thematic_context`, `surah_context`, and `grammar_insights` — all in a single response.

---

#### Standalone Sub-Resource Endpoints

Each field is also available as its own endpoint:

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/verses/{s}:{a}/morphology` | Word-by-word morphological segments |
| `GET /api/v1/verses/{s}:{a}/ai-translation` | AI translation + departure notes |
| `GET /api/v1/verses/{s}:{a}/word-meanings` | AI word meanings keyed by position |
| `GET /api/v1/verses/{s}:{a}/related?limit=10` | Semantically similar verses |
| `GET /api/v1/verses/{s}:{a}/context?size=3` | Surrounding verses |
| `GET /api/v1/verses/{s}:{a}/thematic-context` | Passage theme & Quran-wide links |
| `GET /api/v1/verses/{s}:{a}/surah-context` | Narrative progression in surah |
| `GET /api/v1/verses/{s}:{a}/grammar` | Grammar insights |

Each returns `VERSE_NOT_FOUND` (404) if the verse doesn't exist, or `NO_DATA` (404) if the verse exists but the specific analysis hasn't been generated.

---

### 2. Words

#### `GET /api/v1/words/{surah}:{ayah}/{position}`

Full analysis of a single word: morphology segments, conventional gloss, AI meaning with detailed notes, Semitic cognates for the root, and up to 10 other verses where the same lemma appears.

**Example:**

```bash
curl "https://al-nuqta.com/api/v1/words/67:1/1"
```

```json
{
  "ok": true,
  "data": {
    "surah": 67,
    "ayah": 1,
    "word_pos": 1,
    "text_uthmani": "تَبَـٰرَكَ ٱلَّذِى بِيَدِهِ ٱلْمُلْكُ...",
    "translation": "Blessed is He in whose hand is dominion...",
    "segments": [ { "form_arabic": "تَبَـٰرَكَ", "pos": "Verb", "root_buckwalter": "brk", ... } ],
    "conventional_gloss": "Blessed is",
    "root_arabic": "ب ر ك",
    "root_buckwalter": "brk",
    "lemma_arabic": "تَبَارَكَ",
    "lemma_buckwalter": "tabArak",
    "cognate": { "concept": "bless / chest", "derivatives": [ ... ] },
    "ai_meaning": {
      "meaning_short": "Abundantly blessed is",
      "meaning_detailed": "...",
      "semantic_field": "Divine attributes",
      "departure_notes": "...",
      "preferred_translation": "Blessed is",
      "preferred_source": "conventional"
    },
    "other_occurrences": [
      {
        "surah": 7, "ayah": 54,
        "text_uthmani": "...",
        "translation": "...",
        "conventional_gloss": "Blessed is",
        "ai_meaning": "Abundantly blessed is"
      }
    ],
    "total_lemma_occurrences": 9
  },
  "meta": {}
}
```

---

### 3. Roots

#### `GET /api/v1/roots/{root_buckwalter}`

Root overview: Arabic form, total verse occurrences, derived lemmas, Semitic cognates, and up to 10 sample verses.

Buckwalter special characters are percent-encoded in the URL (e.g., `$` = `%24`, `*` = `%2A`, `>` = `%3E`).

**Example:**

```bash
curl "https://al-nuqta.com/api/v1/roots/mlk"
```

```json
{
  "ok": true,
  "data": {
    "root_arabic": "م ل ك",
    "root_buckwalter": "mlk",
    "total_occurrences": 206,
    "lemmas": [
      { "lemma_arabic": "مَلِك", "lemma_buckwalter": "malik" },
      { "lemma_arabic": "مَلَك", "lemma_buckwalter": "malak" },
      { "lemma_arabic": "مُلْك", "lemma_buckwalter": "mulok" }
    ],
    "cognate": {
      "concept": "reign / king",
      "derivatives": [
        { "language": "Hebrew", "word": "מֶלֶךְ", "meaning": "King" },
        { "language": "Akkadian", "word": "malāku", "meaning": "To advise, rule" }
      ]
    },
    "sample_verses": [
      {
        "surah": 1, "ayah": 4,
        "text_uthmani": "مَـٰلِكِ يَوْمِ ٱلدِّينِ",
        "translation": "Sovereign of the Day of Recompense.",
        "matched_positions": [1]
      }
    ]
  },
  "meta": {}
}
```

#### `GET /api/v1/roots/{root_bw}/cognates`

Semitic cognate data only.

#### `GET /api/v1/roots/{root_bw}/verses?limit=10&offset=0`

Paginated list of all verses containing this root.

| Param | Default | Max | Description |
|-------|---------|-----|-------------|
| `limit` | `10` | `50` | Results per page |
| `offset` | `0` | — | Skip first N results |

Response `meta` includes `total`, `offset`, and `limit` for pagination.

---

### 4. Surahs

#### `GET /api/v1/surahs`

All 114 surahs with English names and verse counts.

```bash
curl "https://al-nuqta.com/api/v1/surahs"
```

```json
{
  "ok": true,
  "data": [
    { "number": 1, "name": "Al-Fatihah", "verse_count": 7 },
    { "number": 2, "name": "Al-Baqarah", "verse_count": 286 },
    ...
  ],
  "meta": { "total": 114 }
}
```

#### `GET /api/v1/surahs/{number}`

Single surah metadata with a list of all verse numbers.

```bash
curl "https://al-nuqta.com/api/v1/surahs/67"
```

```json
{
  "ok": true,
  "data": {
    "number": 67,
    "name": "Al-Mulk",
    "verse_count": 30,
    "verses": [1, 2, 3, ..., 30]
  },
  "meta": {}
}
```

---

### 5. Search

#### `GET /api/v1/search`

Find verses containing specific roots and/or lemmas. All terms are intersected — results contain ALL specified terms.

**Query Parameters:**

| Param | Description |
|-------|-------------|
| `root` | Buckwalter root to search (repeatable: `?root=mlk&root=Elm`) |
| `lemma` | Buckwalter lemma to search (repeatable) |
| `limit` | Results per page (default 10, max 50) |
| `offset` | Skip first N results (default 0) |

**Example:**

```bash
curl "https://al-nuqta.com/api/v1/search?root=mlk&root=Elm&limit=5"
```

```json
{
  "ok": true,
  "data": {
    "terms_used": [
      { "search_type": "root", "search_key": "mlk" },
      { "search_type": "root", "search_key": "Elm" }
    ],
    "results": [
      {
        "surah": 20, "ayah": 114,
        "text_uthmani": "...",
        "translation": "...",
        "score": 3.482,
        "matched_positions": [4, 9]
      }
    ]
  },
  "meta": { "total_found": 12, "offset": 0, "limit": 5 }
}
```

---

### 6. Learning

The learning API exposes a structured curriculum for teaching Quranic Arabic through root words, visual mnemonics, and spaced repetition.

#### `GET /api/v1/learning/curriculum`

All learning units with their roots, mnemonic images, and top derivatives.

```bash
curl "https://al-nuqta.com/api/v1/learning/curriculum"
```

```json
{
  "ok": true,
  "data": {
    "units": [
      {
        "unit_number": 1,
        "unit_theme": "Creation and Divine Power",
        "roots": [
          {
            "root_buckwalter": "xlq",
            "root_arabic": "خ ل ق",
            "frequency_rank": 5,
            "theological_importance": 0.9,
            "anchor_verse": "96:1",
            "mnemonic_image_url": "/api/v1/learning/roots/xlq/mnemonic",
            "mnemonic_caption": "A potter's hands shaping clay on a wheel...",
            "top_derivatives": [
              { "lemma_arabic": "خَلَقَ", "meaning_gloss": "created" },
              { "lemma_arabic": "خَلْق", "meaning_gloss": "creation" }
            ]
          }
        ]
      }
    ]
  },
  "meta": {}
}
```

#### `GET /api/v1/learning/roots/{root_buckwalter}`

Full teaching package for a root: story, derivatives, cognates, and mnemonic data.

```bash
curl "https://al-nuqta.com/api/v1/learning/roots/xlq"
```

```json
{
  "ok": true,
  "data": {
    "root_buckwalter": "xlq",
    "root_arabic": "خ ل ق",
    "unit_number": 1,
    "unit_theme": "Creation and Divine Power",
    "theological_importance": 0.9,
    "root_story": "The root خ-ل-ق carries the fundamental meaning of creating...",
    "teaching_notes": "...",
    "mnemonic_image_url": "/api/v1/learning/roots/xlq/mnemonic",
    "mnemonic_caption": "A potter's hands shaping clay...",
    "derivatives": [
      {
        "lemma_buckwalter": "xalaq",
        "lemma_arabic": "خَلَقَ",
        "pos": "Verb",
        "verb_form": "I",
        "frequency": 184,
        "meaning_gloss": "created",
        "semantic_shift": null,
        "display_order": 1
      }
    ],
    "cognate": { "concept": "create / smooth", "derivatives": [ ... ] },
    "related_roots": [
      { "root_buckwalter": "bde", "root_arabic": "ب د ع", "unit_theme": "Creation and Divine Power" }
    ]
  },
  "meta": {}
}
```

#### `GET /api/v1/learning/roots/{root_buckwalter}/mnemonic`

Returns the mnemonic image (WebP) with immutable cache headers. Link directly to this URL in `<img>` tags.

---

## Buckwalter Transliteration

Root and lemma identifiers use [Buckwalter transliteration](https://corpus.quran.com/java/buckwalter.jsp). Some characters require percent-encoding in URLs:

| Arabic | Buckwalter | URL-encoded |
|--------|-----------|-------------|
| ش | `$` | `%24` |
| ء | `'` | `%27` |
| ذ | `*` | `%2A` |
| ة | `p` | `p` |
| إ | `<` | `%3C` |
| أ | `>` | `%3E` |

Most roots use only alphanumeric Buckwalter characters and need no encoding (e.g., `mlk`, `brk`, `Elm`).

---

## CORS

All `/api/v1/` endpoints include CORS headers (`Access-Control-Allow-Origin: *`), so they can be called directly from browser JavaScript.

---

## Rate Limits

The API is currently open with no rate limits. Please be respectful — this is a free educational resource. Excessive usage may result in IP-based throttling in the future.

**Recommended practices:**
- Use `?fields=all` to fetch everything in one request instead of making 9 separate calls
- Cache responses on your end — Quranic data doesn't change
- Use `offset`/`limit` for pagination instead of fetching all results at once

---

## Examples

### Fetch a verse with AI translation and related verses

```bash
curl "https://al-nuqta.com/api/v1/verses/2:255?fields=ai-translation,related&related_limit=5"
```

### Find all verses containing both root م-ل-ك (sovereignty) and root ع-ل-م (knowledge)

```bash
curl "https://al-nuqta.com/api/v1/search?root=mlk&root=Elm"
```

### Get the full word analysis for the first word of Surah Al-Mulk

```bash
curl "https://al-nuqta.com/api/v1/words/67:1/1"
```

### Get Semitic cognates for root ر-ح-م (mercy)

```bash
curl "https://al-nuqta.com/api/v1/roots/rHm/cognates"
```

### Browse the learning curriculum

```bash
curl "https://al-nuqta.com/api/v1/learning/curriculum"
```
