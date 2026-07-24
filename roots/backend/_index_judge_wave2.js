export const meta = {
  name: 'index-judge-wave2',
  description: 'Judge AB-tier poetry candidates for 18 load-bearing roots (false-friend filtering); emit verdicts for index-add',
  phases: [{ title: 'Judge' }],
}
const SPECS = Array.isArray(args) ? args : (typeof args === 'string' ? JSON.parse(args) : [])
const RB = '/Users/jawadshuaib/Desktop/projects/quran-related/roots/backend'

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    root: { type: 'string' },
    scanned: { type: 'array', items: { type: 'integer' } },
    matches: { type: 'array', items: { type: 'object', additionalProperties: false,
      properties: {
        line_id: { type: 'integer' },
        surface_word: { type: 'string' },
        sense_hint: { type: 'string' },
        confidence: { type: 'number' },
      }, required: ['line_id', 'surface_word', 'sense_hint', 'confidence'] } },
  },
  required: ['root', 'scanned', 'matches'],
}

function prompt(s) {
  const formsArg = s.forms ? ` --forms "${s.forms}"` : ''
  return `You are the INDEXER for a Qur'an-only root-by-root project. Decide which authenticated (Tier A/B) poetry lines genuinely contain a word from ROOT **${s.fr}** (Arabic ${s.root_ar || ''}), in ANY sense.

STEP 1 — fetch the candidate batch (read-only):
\`cd ${RB} && python3 poetry_corpus.py index-next --tiers AB --count ${s.count || 99999}${formsArg} '${s.fr}'\`
It prints {"root","root_arabic","lines":[{"id":<int>,"text":"<arabic bayt>"}]}. The prefilter is a crude SUBSTRING match, so the batch is FULL OF FALSE FRIENDS — your job is to separate genuine occurrences of root ${s.fr} from look-alikes.

STEP 2 — judge EVERY line:
- A line MATCHES only if it contains an actual word DERIVED FROM the consonantal root ${s.fr} (${s.root_ar || ''}). Identify the specific surface word.
- REJECT false friends: words that merely share letters but belong to a DIFFERENT root, and function-word + pronoun/clitic accidents (e.g. for و-ل-ي, reject "وَ لي" = 'and to me'; for ح-ل-ل, reject ر-ا-ح-ل / م-ح-ا-ل from other roots). When in genuine doubt about the root, REJECT.
- Keep ALL genuine senses (concrete and abstract) — this feeds a lexicon that needs the full 6th-c. semantic field. Give a SHORT sense_hint (a few words, English or Arabic) for each match, and confidence 0.0-1.0 (use <0.6 only for borderline-but-plausible).

OUTPUT:
- root = "${s.fr}".
- scanned = the COMPLETE list of every line "id" you were shown (so they are marked done and never re-offered). Do not omit any.
- matches = the genuine ones only: { line_id, surface_word (the exact Arabic word as it appears), sense_hint, confidence }. Every line_id MUST be among scanned.
Return ONLY the structured object.`
}

log(`Index-judge Wave 2: ${SPECS.length} roots (AB tier)`)
const results = await parallel(SPECS.map(s => () =>
  agent(prompt(s), { schema: SCHEMA, label: `judge:${s.fr}`, phase: 'Judge' })))
const clean = results.filter(Boolean)
log(`Judged ${clean.length}/${SPECS.length}; total matches ${clean.reduce((a, r) => a + r.matches.length, 0)}`)
return clean
