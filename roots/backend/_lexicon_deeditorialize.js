export const meta = {
  name: 'lexicon-deeditorialize',
  description: 'Strip advocacy/hedging meta-commentary from existing lexicon entries; preserve evidence + quote markers',
  phases: [{ title: 'Clean' }],
}
const ROOTS = Array.isArray(args) ? args : (typeof args === 'string' ? JSON.parse(args) : [])
const DUMP = '/tmp/lexicon_15_dump.json'

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    root_buckwalter: { type: 'string' },
    quran_internal_summary: { type: 'string' },
    lexicon_markdown: { type: 'string' },
    relation_to_quran: { type: 'string' },
    removed: { type: 'array', items: { type: 'string' } },
    markers_unchanged: { type: 'boolean' },
    note: { type: 'string' },
  },
  required: ['root_buckwalter', 'quran_internal_summary', 'lexicon_markdown', 'relation_to_quran', 'removed', 'markers_unchanged', 'note'],
}

function prompt(bw) {
  return `You are COPY-EDITING one entry in a strictly Qur'an-only contemporaneous-attestation lexicon. Your ONLY job is to remove agenda-sounding ADVOCACY / HEDGING meta-commentary. Keep ALL lexical evidence, every bayt example, every [[q:..]] marker, the teacher's voice, and the overall paragraph structure.

STEP 1 — read the current entry:
\`\`\`
python3 -c "import json; d=[r for r in json.load(open('${DUMP}')) if r['root_buckwalter']=='${bw}'][0]; print('ROOT', d['root_buckwalter'], d['root_arabic']); print('RELATION', d['relation_to_quran']); print('=== SUMMARY ==='); print(d['quran_internal_summary']); print('=== MARKDOWN ==='); print(d['lexicon_markdown'])"
\`\`\`

STEP 2 — clean BOTH quran_internal_summary and lexicon_markdown. REMOVE or rewrite any sentence/clause that:
- argues a thesis or warns the reader off a reading: "gives no warrant", "the honest caution", "crucially, the codified institution is NOT assumed", "we do not assume X = ...", "read INTO the word rather than OUT of it", "a development within the text, not a meaning already lying in the word", "supplied from outside the words", "the heavier institutional content is supplied from outside";
- names the later codified institution only to deny / argue against it (e.g. "the later fixed alms-tax", "a legally fixed schedule of timed prayers with set postures and counts", "the canonical pilgrimage rite"). Simply OMIT the codified institution — do NOT assert it and do NOT argue against it. Don't mention it at all.

REPLACE such material with NOTHING, or with at most ONE plain, descriptive sentence stating the neutral relation (e.g. "In the Qur'an the root concentrates on X." / "The same sense carries into the Qur'an, re-aimed toward God."). The entry must read as neutral evidence: attested 6th-c. sense(s) → the Qur'an's own usage, described → a one-line neutral relation. No advocacy, no first-person stance ("we", "the honest caution"), no warning.

HARD CONSTRAINTS:
- PRESERVE EVERY [[q:<id>|<arabic>]] marker EXACTLY — same ids, same Arabic fragments, same total count. Do not add or drop any. If a sentence you cut hosted a marker, move that marker into a neutral descriptive sentence so the marker SET is identical.
- Keep the attested-sense paragraph(s) and all poetry examples — those are the evidence, not advocacy.
- Keep genuine Qur'an refs (surah:ayah). Keep **bold**/*italic* styling.
- relation_to_quran: return the SAME label unless your cleaned prose genuinely no longer supports it.
- markers_unchanged: true only if you preserved the exact marker set.

Return root_buckwalter="${bw}", the cleaned quran_internal_summary + lexicon_markdown, relation_to_quran, removed (the phrases/sentences you struck), markers_unchanged, and a one-line note.`
}

log(`De-editorialize: cleaning ${ROOTS.length} lexicon entries`)
const results = await parallel(ROOTS.map(bw => () =>
  agent(prompt(bw), { schema: SCHEMA, label: `clean:${bw}`, phase: 'Clean' })))
const clean = results.filter(Boolean)
log(`Cleaned ${clean.length}/${ROOTS.length}; markers_unchanged on ${clean.filter(r => r.markers_unchanged).length}`)
return clean
