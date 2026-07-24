export const meta = {
  name: 'dict-review',
  description: 'Self-review the harmonized Lexicon-Library entries against their original Arabic: approve / edit-then-approve / reject(hide) / defer-to-human. Faithfulness + neutral Qur’an-only voice + no imported codified doctrine. Paced for usage economy.',
  phases: [{ title: 'Review' }],
}

// args = array of dictionary_entries.id. Big raw Arabic + both generated fields
// live in the dump file; each subagent reads ONLY its own entry by id.
const IDS = Array.isArray(args) ? args : JSON.parse(args)
const DUMP = '/Users/jawadshuaib/Desktop/projects/quran-related/roots/backend/data/dict_review_dump.json'

const READ = (id) =>
  `python3 -c "import json; d=[r for r in json.load(open('${DUMP}',encoding='utf-8')) if r['id']==${id}][0]; ` +
  `print('ROOT', d['root_buckwalter'], d['root_arabic']); ` +
  `print('DICTIONARY', d['name_en'], '—', d['author'], '(d.'+str(d['author_death_year'])+' CE)'); ` +
  `print('LANGUAGE', d['language'], '| QURAN_SPECIFIC', d['is_quran_specific']); ` +
  `print('=== ORIGINAL ARABIC (ground truth) ==='); print(d['original_text_ar']); ` +
  `print('=== translation_en (faithful view under review) ==='); print(d['translation_en'] or '(blank)'); ` +
  `print('=== harmonized_en (readable view under review) ==='); print(d['harmonized_en'] or '(blank)')"`

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    id: { type: 'integer' },
    decision: { type: 'string', enum: ['approve', 'edit', 'reject', 'defer'] },
    severity: { type: 'string', enum: ['none', 'minor', 'major'] },
    reason: { type: 'string' },
    // Only when decision === 'edit'. Provide the CORRECTED full field(s) you changed;
    // leave the other one '' to keep it unchanged.
    harmonized_en: { type: 'string' },
    translation_en: { type: 'string' },
  },
  required: ['id', 'decision', 'severity', 'reason', 'harmonized_en', 'translation_en'],
}

function prompt(id) {
  return `You are the SCHOLARLY REVIEWER and moderator for al-nuqta.com's Lexicon Library. One harmonized classical-dictionary entry for a Qur'anic ROOT is under review. You decide its fate. The reference exists so users understand the Qur'an's OWN language: meaning is derived from attested usage and pre-Islamic (contemporaneous) evidence, NEVER from later codified juristic/theological doctrine.

STEP 1 — read the entry (run this). The ORIGINAL ARABIC is the ground truth; the two English fields are what you are judging:
\`\`\`
${READ(id)}
\`\`\`

STEP 2 — judge both English fields against the ORIGINAL ARABIC on five tests:
 A. FAITHFUL: every sense/claim/citation traces to the Arabic above; nothing invented, no fabricated shāhid, right root.
 B. NO IMPORTED DOCTRINE: it does NOT state later codified juristic/theological definitions as fact that the Arabic does not itself state (e.g. glossing ṣalāt as "the five daily ritual prayers", zakāt as "the alms-tax", ḥajj as "the pilgrimage rite", īmān as a creed). If the entry itself records such a sense, it must be attributed to THIS author, not asserted as fact.
 C. NEUTRAL EVIDENCE VOICE: reads as this lexicographer's account described neutrally; no advocacy, no first person ("we"/"I"), no warning the reader toward or away from a reading.
 D. COMPLETE: the original's main sense-distinctions are present (not flattened into one); grammar/etymology/shawāhid retained where the original has them. (A deliberately terse original may have a terse rendering.)
 E. READABLE + WELL-FORMED: harmonized_en is clear modern English; translation_en is a faithful close rendering; no truncation garbage, no leftover stub text.

STEP 3 — choose ONE decision:
 • "approve" — passes A–E. Faithful, neutral, no imported doctrine, senses intact. (Most good entries are this — approve confidently when it is sound; do not nitpick trivial wording.)
 • "edit" — substantively sound but has a FIXABLE flaw you can correct yourself: a slip into advocacy/first person, a codified gloss stated as fact (re-attribute or neutralize it), a small completeness gap, leftover stub/typo, or awkward-but-fixable phrasing. Provide the CORRECTED full field(s): put the whole corrected harmonized_en and/or translation_en in the matching field; leave the OTHER field '' to keep it unchanged. Keep edits minimal, faithful to the Arabic, and in the neutral voice — fix the flaw, don't rewrite wholesale.
 • "reject" — broken beyond a quick fix: hallucinated/untraceable content, wrong root, senses fabricated, or garbled to the point of uselessness. This HIDES it from the public. Use sparingly.
 • "defer" — a genuinely hard SCHOLARLY call a human expert should make: a subtle doctrinal-boundary judgment, an authenticity/attribution ambiguity you cannot resolve with confidence, or a case where reasonable scholars would disagree. Use sparingly — only when you truly cannot decide, not merely because the entry is long.

Bias: lean "approve" for faithful, neutral entries; "edit" for fixable flaws; "reject" and "defer" are the exceptions, not the norm.

Return id=${id}, decision, severity ('none' for approve/clean, 'minor' or 'major' otherwise), reason (ONE line citing the specific basis — e.g. "faithful, neutral, senses intact" or "edited: neutralized 'ritual prayer' gloss to attributed sense"), harmonized_en (corrected full text ONLY if you edited it, else ''), translation_en (corrected full text ONLY if you edited it, else '').`
}

log(`Reviewing ${IDS.length} dictionary entries (self-review, paced)`)
const results = await parallel(
  IDS.map((id) => () => agent(prompt(id), { schema: SCHEMA, label: `review:${id}`, phase: 'Review' }))
)
const out = results.filter(Boolean)
const tally = out.reduce((m, r) => (m[r.decision] = (m[r.decision] || 0) + 1, m), {})
log(`Reviewed ${out.length}/${IDS.length} — ${JSON.stringify(tally)}`)
return out
