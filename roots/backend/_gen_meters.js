export const meta = {
  name: 'generate-meters',
  description: 'Write a beginner-friendly teaching page for each Arabic metre (baḥr), then have a QA agent verify its prosody, transliteration and tone before applying',
  phases: [{ title: 'Write' }, { title: 'QA' }],
}

const KEYS = Array.isArray(args) ? args : (typeof args === 'string' ? JSON.parse(args) : [])
const RB = '/Users/jawadshuaib/Desktop/projects/quran-related/roots/backend'

const ARTICLE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    key: { type: 'string' },
    name_en: { type: 'string' },
    name_meaning: { type: 'string' },
    tafil_ar: { type: 'string' },
    tafil_latin: { type: 'string' },
    syllable_pattern: { type: 'string' },
    mnemonic_en: { type: 'string' },
    article_markdown: { type: 'string' },
    confidence: { type: 'number' },
    showcase: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          line_id: { type: 'integer' },
          transliteration: { type: 'string' },
          scansion: { type: 'string' },
          translation: { type: 'string' },
        },
        required: ['line_id', 'transliteration', 'scansion', 'translation'],
      },
    },
  },
  required: ['key', 'name_en', 'name_meaning', 'tafil_ar', 'tafil_latin',
    'syllable_pattern', 'mnemonic_en', 'article_markdown', 'confidence', 'showcase'],
}

const QA_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    verdict: { type: 'string', enum: ['pass', 'needs_fix'] },
    notes: { type: 'string' },
    corrected: ARTICLE_SCHEMA,
  },
  required: ['verdict', 'notes', 'corrected'],
}

const PATTERN_RULE =
  `syllable_pattern encodes the rhythm of ONE repetition of the foot-set: feet separated by "|", ` +
  `syllables space-separated, "-" = long syllable, "u" = short syllable. It MUST correspond exactly ` +
  `to tafil_latin (e.g. faʿūlun = "u - -", mafāʿīlun = "u - - -"). For Ṭawīl that is ` +
  `"u - - | u - - - | u - - | u - - -".`

function genPrompt(key) {
  return `You are writing a beginner-friendly teaching page about ONE classical Arabic poetic metre (baḥr) for an English-speaking audience on a Qurʾān-study site. Most readers do NOT read Arabic.

STEP 1 — read the metre's identity and candidate example lines (read-only):
\`cd ${RB} && python3 poetry_corpus.py meter-context ${key}\`
It prints the metre's Arabic name, its corpus variants, and a pool of real, already-translated pre-Islamic lines in this metre, each tagged [line_id].

STEP 2 — write the page. Requirements:
- name_en: the romanised name (e.g. "Ṭawīl"). name_meaning: a few words on what the name literally means.
- tafil_ar: the classical tafāʿīl in Arabic (e.g. فعولن مفاعيلن فعولن مفاعيلن). tafil_latin: the same romanised (faʿūlun mafāʿīlun …).
- syllable_pattern: ${PATTERN_RULE}
- mnemonic_en: an English "da-DUM" mnemonic an English speaker can chant, matching the pattern (e.g. "da-DUM-DUM da-DUM-DUM-DUM …").
- article_markdown: 3 short sections using "## " headings, in clear, warm, jargon-free English (define any term you must use):
    "## What it is" — the feel of the rhythm in plain words;
    "## Its character" — what poets reach for it to do (mood, pace), and roughly how common it is;
    "## A little history" — al-Khalīl ibn al-Aḥmad and the science of ʿarūḍ, where this metre sits, and a famous poem/poet who used it. Be factual; do not invent attributions.
  Keep it beginner-friendly and concrete. Use *italic* / **bold** sparingly. Do NOT use post-Qurʾānic religious terminology; these are pre-Islamic (Jahilī) poems — keep that texture, don't Islamise.
- showcase: choose 2–4 of the candidate [line_id]s that scan CLEANLY in this metre. For each, give:
    transliteration: a readable, beat-friendly romanisation an English reader can say aloud;
    scansion: the long/short marks for that exact line, space-separated "-"/"u", matching this metre's pattern;
    translation: keep the candidate's English (lightly polish only if needed).
  Use the EXACT line_id from meter-context — never invent one.

Return ONLY the structured object (key="${key}"). No prose outside it.`
}

function qaPrompt(key, draft) {
  return `You are the QA / conformity checker for a beginner teaching page about the Arabic metre "${key}". A draft is below. Independently verify it and return a corrected version.

DRAFT:
${JSON.stringify(draft, null, 2)}

You MAY re-read the source to check the example lines:
\`cd ${RB} && python3 poetry_corpus.py meter-context ${key}\`

Check, and FIX in your "corrected" object:
1. PROSODY: tafil_ar and tafil_latin are the correct classical tafāʿīl for THIS metre. ${PATTERN_RULE} syllable_pattern must match tafil_latin exactly. mnemonic_en must match the pattern's long/short shape.
2. SCANSION: each showcase line's scansion matches this metre and lines up with its transliteration's long/short syllables. Every showcase line_id must be one that meter-context actually lists (drop any that aren't).
3. TRANSLITERATION: readable and consistent; an English speaker could say it aloud.
4. TONE: genuinely beginner-friendly, no undefined jargon, factually careful history (no invented attributions).
5. LANGUAGE: no post-Qurʾānic religious terminology; pre-Islamic texture kept.

Set verdict="pass" if the draft was already sound (echo it, lightly cleaned, into "corrected"); verdict="needs_fix" if you changed anything substantive. "notes" = one or two sentences on what you checked/changed. "corrected" MUST be the full, final, correct article object (key="${key}"). Return ONLY the structured object.`
}

log(`Generating ${KEYS.length} metre pages (write → QA)`)

const results = await pipeline(
  KEYS,
  (key) => agent(genPrompt(key), { schema: ARTICLE_SCHEMA, label: `write:${key}`, phase: 'Write' }),
  (draft, key) => {
    if (!draft) return null
    return agent(qaPrompt(key, draft), { schema: QA_SCHEMA, label: `qa:${key}`, phase: 'QA' })
      .then((qa) => {
        if (!qa) return { ...draft, qa_status: 'pending', qa_notes: 'QA agent returned nothing' }
        return { ...qa.corrected, key, qa_status: qa.verdict, qa_notes: qa.notes }
      })
  },
)

const clean = results.filter(Boolean)
log(`Done: ${clean.length}/${KEYS.length} metre pages (${clean.filter((r) => r.qa_status === 'pass').length} passed QA cleanly)`)
return clean
