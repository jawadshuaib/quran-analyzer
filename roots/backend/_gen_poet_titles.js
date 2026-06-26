export const meta = {
  name: 'poet-titles',
  description: 'Romanise pre-Islamic poet names and write concise English titles for poems that only have an Arabic name',
  phases: [{ title: 'Poets' }, { title: 'Titles' }],
}

const RB = '/Users/jawadshuaib/Desktop/projects/quran-related/roots/backend'
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const POETS = A.poets || []
const TITLE_IDS = A.titleIds || []

function chunk(arr, n) {
  const out = []
  for (let i = 0; i < arr.length; i += n) out.push(arr.slice(i, i + n))
  return out
}

const POET_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    poets: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { poet: { type: 'string' }, poet_latin: { type: 'string' } },
        required: ['poet', 'poet_latin'],
      },
    },
  },
  required: ['poets'],
}

const TITLE_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    titles: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: { poem_id: { type: 'integer' }, title_en: { type: 'string' } },
        required: ['poem_id', 'title_en'],
      },
    },
  },
  required: ['titles'],
}

function poetPrompt(names) {
  return `Romanise these pre-Islamic / early Arabic poet names into clean, scholarly English transliteration (ALA-LC style, with ʿayn ʿ and hamza ʾ and macrons where natural, e.g. "Imruʾ al-Qays", "Labīd ibn Rabīʿa", "al-Nābigha al-Dhubyānī", "ʿAntara ibn Shaddād"). Keep "ibn"/"al-" lowercase. If a value is not a personal name (e.g. "مجهول" = unknown), romanise it sensibly ("Anonymous").

Names:
${JSON.stringify(names, null, 2)}

Return { poets: [ { poet: "<exact Arabic input>", poet_latin: "<romanisation>" }, ... ] } covering EVERY name. Return ONLY the object.`
}

function titlePrompt(ids) {
  return `You are giving short ENGLISH titles to pre-Islamic Arabic poems for an English-speaking audience, so a reader who can't read Arabic knows what each poem is.

STEP 1 — fetch context (read-only):
\`cd ${RB} && python3 poetry_corpus.py titles-context --ids ${ids.join(',')}\`
It returns, per poem: poet, the Arabic title (usually the poem's opening words), and the first line (Arabic + its English translation if we have one).

STEP 2 — for EACH poem, write a concise, natural English title (about 3–8 words):
- If the Arabic title is a formal name like "معلقة امرئ القيس", render it as "The Muʿallaqa of Imruʾ al-Qays".
- Otherwise the title is the poem's opening words (the maṭlaʿ). Use the first line's English to craft a short, evocative title that captures its image or theme — e.g. for "Qifā nabki…" → "Halt, Let Us Weep". Title-case it. Do NOT just copy the whole translated line; distil it to a short title.
- Keep proper names transliterated. No quotation marks around the title. Pre-Islamic texture — do not Islamise or modernise.
- If there is no English first line to work from, translate the Arabic title itself into a short English title as best you can.

Return { titles: [ { poem_id, title_en }, ... ] } covering EVERY poem id listed. Return ONLY the object.`
}

log(`Romanising ${POETS.length} poets, titling ${TITLE_IDS.length} poems`)

const poetChunks = chunk(POETS, 60)
const titleChunks = chunk(TITLE_IDS, 22)

const poetResults = await parallel(poetChunks.map((names, i) => () =>
  agent(poetPrompt(names), { schema: POET_SCHEMA, label: `poets:${i + 1}`, phase: 'Poets' })))
const titleResults = await parallel(titleChunks.map((ids, i) => () =>
  agent(titlePrompt(ids), { schema: TITLE_SCHEMA, label: `titles:${i + 1}`, phase: 'Titles' })))

const poets = poetResults.filter(Boolean).flatMap((r) => r.poets || [])
const titles = titleResults.filter(Boolean).flatMap((r) => r.titles || [])
log(`Done: ${poets.length} poet romanisations, ${titles.length} titles`)
return { poets, titles }
