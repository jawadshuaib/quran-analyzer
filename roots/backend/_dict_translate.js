export const meta = {
  name: 'dict-translate-backfill',
  description: 'Backfill the faithful translation_en ONLY for the 46 giant dictionary entries whose translation field was stubbed at the two-field output limit. harmonized_en already exists; this fills the verbatim faithful-translation view. Draft-only; admin review is the gate.',
  phases: [{ title: 'Translate' }],
}

// args = array of dictionary_entries.id. Big raw Arabic stays in the dump file;
// each subagent reads ONLY its own entry by id (keeps prompts small). Because we
// produce ONE field here (not two), each agent has ~2x the output budget the
// original two-field draft had — enough for even the giant Lisān/Tāj entries.
const IDS = Array.isArray(args) ? args : JSON.parse(args)
const DUMP = '/Users/jawadshuaib/Desktop/projects/quran-related/roots/backend/data/dict_translate_dump.json'

const READ = (id) =>
  `python3 -c "import json; d=[r for r in json.load(open('${DUMP}',encoding='utf-8')) if r['id']==${id}][0]; ` +
  `print('ROOT', d['root_buckwalter'], d['root_arabic']); ` +
  `print('DICTIONARY', d['name_en'], '—', d['author'], '(d.'+str(d['author_death_year'])+' CE)'); ` +
  `print('LANGUAGE', d['language'], '| QURAN_SPECIFIC', d['is_quran_specific']); ` +
  `print('=== ORIGINAL ==='); print(d['original_text_ar'])"`

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'integer' },
    translation_en: { type: 'string' },
    confidence: { type: 'number' },
    issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['id', 'translation_en', 'confidence', 'issues'],
}

function prompt(id) {
  return `You are producing the FAITHFUL, close English translation of ONE classical Arabic dictionary entry for a single Qur'anic ROOT, for an internal scholarly reference on al-nuqta.com. A readable digest of this same entry already exists; your job here is ONLY the faithful translation_en field. The end goal is understanding the Qur'an's own language, so meaning is derived from attested usage — never from later codified doctrine.

STEP 1 — read the exact entry (run this):
\`\`\`
${READ(id)}
\`\`\`

STEP 2 — from the ORIGINAL ARABIC ABOVE ONLY (do not add senses from memory or from other dictionaries), produce translation_en: a FAITHFUL, close translation. Keep it COMPLETE for the lexical substance — every distinct sense, the grammatical/morphological notes (wazn, iʿrāb, plural patterns), the derivation/etymology, and the poetic or Qur'anic shawāhid (citations) with their attributions. Give Arabic head-words/examples in Arabic followed by a parenthesised English gloss.

For a very long entry (e.g. Lisān al-ʿArab, Tāj al-ʿArūs): this is a faithful, complete translation, NOT a first-line paraphrase. You MAY drop pure transmission chains ("A told us from B…") and collapse verbatim repetition of the same shāhid, but never summarise a distinct sense away and never invent a citation. This is the ONLY field you are producing, so use the full budget to render the whole entry.

If the source is already English (Lane, Salmoné): translation_en = the original lightly cleaned and re-typeset.

VOICE + INTEGRITY — hard rules:
- Present this as THIS lexicographer's account, described neutrally as evidence. No advocacy, no first person ("we"), no warning the reader toward or away from a reading.
- Do NOT import later codified juristic/theological senses the Arabic does not state (do not gloss ṣalāt as "the five daily ritual prayers", zakāt as "the alms-tax", ḥajj as "the pilgrimage rite", īmān as a creed) UNLESS the entry itself says so — and then attribute it to this author, not as fact.
- Every clause must trace to the Arabic above. Never pad.
- translation_en MUST be a REAL, complete output — NEVER write "placeholder", "unused", "see above", or stub it. Condense faithfully if long, but it must carry the whole entry's genuine content.

Return id=${id}, translation_en, confidence (0–1: how faithful+complete you judge it), and issues (array; note any truncation/garbling/uncertainty, else []).`
}

log(`Backfilling translation_en for ${IDS.length} entries (translation-only)`)
const results = await parallel(
  IDS.map((id) => () => agent(prompt(id), { schema: SCHEMA, label: `trans:${id}`, phase: 'Translate' }))
)
const out = results.filter(Boolean)
log(`Translated ${out.length}/${IDS.length}`)
return out
