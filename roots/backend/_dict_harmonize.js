export const meta = {
  name: 'dict-harmonize',
  description: 'Harmonize scraped classical-dictionary root entries into a faithful translation_en + a readable harmonized_en (Qur’an-only voice). Draft-only + paced for usage economy; admin review is the faithfulness gate.',
  phases: [{ title: 'Draft' }],
}

// args = array of dictionary_entries.id to harmonize. The big raw Arabic stays in
// the dump file; each subagent reads ONLY its own entry by id (keeps prompts small).
const IDS = Array.isArray(args) ? args : JSON.parse(args)
const DUMP = '/Users/jawadshuaib/Desktop/projects/quran-related/roots/backend/data/dict_harmonize_dump.json'

const READ = (id) =>
  `python3 -c "import json; d=[r for r in json.load(open('${DUMP}',encoding='utf-8')) if r['id']==${id}][0]; ` +
  `print('ROOT', d['root_buckwalter'], d['root_arabic']); ` +
  `print('DICTIONARY', d['name_en'], '—', d['author'], '(d.'+str(d['author_death_year'])+' CE)'); ` +
  `print('LANGUAGE', d['language'], '| QURAN_SPECIFIC', d['is_quran_specific']); ` +
  `print('=== ORIGINAL ==='); print(d['original_text_ar'])"`

const DRAFT_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'integer' },
    translation_en: { type: 'string' },
    harmonized_en: { type: 'string' },
    confidence: { type: 'number' },
    issues: { type: 'array', items: { type: 'string' } },
  },
  required: ['id', 'translation_en', 'harmonized_en', 'confidence', 'issues'],
}

const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'integer' },
    ok: { type: 'boolean' },
    faithful: { type: 'boolean' },
    no_codified: { type: 'boolean' },
    complete: { type: 'boolean' },
    attribution_ok: { type: 'boolean' },
    severity: { type: 'string', enum: ['none', 'minor', 'major'] },
    reason: { type: 'string' },
  },
  required: ['id', 'ok', 'faithful', 'no_codified', 'complete', 'attribution_ok', 'severity', 'reason'],
}

function draftPrompt(id) {
  return `You are harmonizing ONE classical Arabic dictionary's entry for a single Qur'anic ROOT, for an internal scholarly reference on al-nuqta.com. The end goal is understanding the Qur'an's own language, so meaning is derived from attested usage — never from later codified doctrine.

STEP 1 — read the exact entry (run this):
\`\`\`
${READ(id)}
\`\`\`

STEP 2 — from the ORIGINAL ARABIC ABOVE ONLY (do not add senses from memory or from other dictionaries), produce TWO English renderings of THIS one entry:

(A) translation_en — a FAITHFUL, close translation. Keep it complete for the lexical substance: every distinct sense, the grammatical/morphological notes (wazn, iʿrāb, plural patterns), the derivation/etymology, and the poetic or Qur'anic shawāhid (citations) with their attributions. You MAY drop pure transmission chains ("A told us from B…") and collapse verbatim repetition, but never summarise a sense away. Give Arabic head-words/examples in Arabic followed by a parenthesised English gloss.

(B) harmonized_en — the SAME content made READABLE for a serious non-Arabist. Clear modern English, as short sense-numbered points or brief paragraphs. KEEP every sense-distinction, the grammatical method, the etymology, and the key shawāhid. REMOVE: isnād chains, piles of near-synonyms, tangents, and edition/scribal apparatus. Trim length, but do NOT flatten distinct senses into one or lose nuance. For a very long entry (e.g. Lisān), this is a faithful digest, not a paraphrase of the first line.

VOICE + INTEGRITY — hard rules:
- Present this as THIS lexicographer's account, described neutrally as evidence. No advocacy, no first person ("we"), no warning the reader toward or away from a reading.
- Meaning comes from the attested usage this entry records. Do NOT import later codified juristic/theological senses the Arabic does not state (do not gloss ṣalāt as "the five daily ritual prayers", zakāt as "the alms-tax", ḥajj as "the pilgrimage rite", īmān as a creed) UNLESS the entry itself says so — and then attribute it to this author, not as fact.
- Faithfulness over completeness: every clause in BOTH renderings must trace to the Arabic above. If the entry is terse, your renderings are terse. Never pad, never invent a citation.
- If the source is already English (Lane, Salmoné): translation_en = the original lightly cleaned; harmonized_en = a readable condensation.
- BOTH fields must be REAL, complete outputs — NEVER write "placeholder", "unused", "see above", or stub a field. For a very long entry, condense faithfully (drop repeated shawāhid + isnād) so both stay a reasonable length, but each must carry genuine content.

Return id=${id}, translation_en, harmonized_en, confidence (0–1: how faithful+complete you judge your renderings), and issues (array; note any truncation/garbling/uncertainty, else []).`
}

function verifyPrompt(id, draft) {
  return `You are the FAITHFULNESS CHECKER for a harmonized classical-dictionary entry. Be strict and adversarial: your job is to catch invented meaning, imported doctrine, flattened senses, and editorializing.

STEP 1 — read the ORIGINAL (run this):
\`\`\`
${READ(id)}
\`\`\`

STEP 2 — judge this DRAFT against the original:
--- translation_en ---
${draft.translation_en}
--- harmonized_en ---
${draft.harmonized_en}

Checks (each true = passes):
- faithful: every sense/claim/citation in BOTH renderings traces to the original Arabic; nothing invented, no citation fabricated.
- no_codified: the draft did NOT import post-Qur'anic codified juristic/theological definitions that the original does not itself state.
- complete: the original's main sense-distinctions are all present (not collapsed into one); grammatical/etymological substance retained where the original has it.
- attribution_ok: neutral evidence voice — no advocacy, no first person, no reader-warnings; reads as this author's account.

ok = (faithful AND no_codified AND complete AND attribution_ok). severity = 'major' if faithful or no_codified failed, 'minor' if only complete/attribution slipped, else 'none'. reason = one line citing the specific problem (or "clean"). Return id=${id}.`
}

log(`Harmonizing ${IDS.length} dictionary entries (draft-only, paced)`)
const results = await parallel(
  IDS.map((id) => () => agent(draftPrompt(id), { schema: DRAFT_SCHEMA, label: `draft:${id}`, phase: 'Draft' }))
)
const out = results.filter(Boolean)
log(`Drafted ${out.length}/${IDS.length}`)
return out
