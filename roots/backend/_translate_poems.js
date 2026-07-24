export const meta = {
  name: 'translate-poems-batch',
  description: 'Translate a batch of reference-linked pre-Islamic poems (their untranslated lines) into faithful English',
  phases: [{ title: 'Translate' }],
}
const POEMS = Array.isArray(args) ? args : (typeof args === 'string' ? JSON.parse(args) : [])
const RB = '/Users/jawadshuaib/Desktop/projects/quran-related/roots/backend'

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    poem_id: { type: 'integer' },
    translations: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: { line_id: { type: 'integer' }, english: { type: 'string' } },
      required: ['line_id', 'english'] } },
  },
  required: ['poem_id', 'translations'],
}

function prompt(pid) {
  return `You are translating ONE authenticated pre-Islamic (Jāhilī) Arabic poem into English for a Qurʾān-study site, so readers can read the full poem a quoted line comes from.

STEP 1 — fetch the lines (read-only):
\`cd ${RB} && python3 poetry_corpus.py trans-context ${pid}\`
It prints the poem header (poet, title, meter, rhyme) and the UNTRANSLATED lines, each as:  [<line_id>] (bayt N) <arabic bayt>

STEP 2 — translate EVERY listed line into clear, faithful, readable English — ONE English line per bayt:
- Render the classical Arabic as natural, flowing English that conveys the meaning and imagery; do NOT produce a stiff word-for-word gloss, and do NOT add commentary, footnotes, moralising, or bracketed explanations.
- Stay FAITHFUL: don't invent content the bayt doesn't carry. Keep proper names (poets, tribes, places) transliterated.
- A bayt is two hemistichs — translate the whole bayt as one English sentence/line.
- Pair each translation with its exact [line_id].

Return { poem_id: ${pid}, translations: [ { line_id, english }, ... ] } covering EVERY line trans-context listed. Return ONLY the structured object — no prose.`
}

log(`Translating ${POEMS.length} poems`)
const results = await parallel(POEMS.map((pid) => () =>
  agent(prompt(pid), { schema: SCHEMA, label: `trans:${pid}`, phase: 'Translate' })))
const clean = results.filter(Boolean)
log(`Done: ${clean.length}/${POEMS.length} poems, ${clean.reduce((a, r) => a + (r.translations?.length || 0), 0)} lines`)
return clean
