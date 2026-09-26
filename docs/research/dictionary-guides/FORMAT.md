# Classical-dictionary guides — file format and house rules

Each guide is one TypeScript module:

    roots/frontend/src/content/dictionary-guides/guides/<guide-slug>.ts

It is rendered at `/classical-dictionaries/<guide-slug>` and linked from the
"Classical Dictionaries" panel on every root and word page ("About this
dictionary"). The slug ↔ dictionary mapping is fixed in
`roots/frontend/src/content/dictionary-guides/registry.ts` — do not change it.

Research and verification notes are NOT part of the page. They live in
`docs/research/dictionary-guides/<guide-slug>/` (research-notes.md,
verification-rN.md, revision-rN.md).

## Skeleton

```ts
import type { DictionaryGuide } from '../types';

const guide: DictionaryGuide = {
  slug: 'maqayis-al-lugha',
  dictionarySlugs: ['ibn-faris-maqayis-al-lugha'],
  title: 'Maqāyīs al-Lugha',
  titleAr: 'مقاييس اللغة',            // only if verified
  titleGloss: 'The Standards of Language',   // optional English rendering of the title
  author: 'Ibn Fāris',
  authorFull: 'Abū l-Ḥusayn Aḥmad ibn Fāris ibn Zakariyyāʾ',   // optional, verified
  authorAr: 'ابن فارس',               // optional, verified
  period: 'd. 395 AH / 1004–5 CE',     // concise; approximate or disputed dates say so
  sortYear: 1004,                      // approximate CE year, only for ordering
  kind: 'Root-meaning dictionary',     // 2–4 words, shown above the title
  summary: `…`,                        // ≤ 45 words, plain text, overview card; no rankings
  lede: `…`,                           // opening paragraph: what is distinctive (≤ ~90 words)
  body: `…`,                           // the essay (markup below)
  onOurSite: `…`,                      // what al-nuqta shows for this work (markup below)
  sources: [
    { id: 'harun-ed', kind: 'edition', citation: 'Ibn Fāris, *Maqāyīs al-Lugha*, ed. ʿAbd al-Salām Muḥammad Hārūn, 6 vols (Cairo, 1946–52).', url: 'https://…' },
  ],
  limitedEvidence: `…`,                // ONLY when the account is deliberately short
  lastVerified: '2026-09-26',          // set by the final verification round
};

export default guide;
```

All prose fields are template literals. Never write a backtick or `${` inside
them. Plain text in `summary` (no links, no citations; *italic* is fine).

## Markup (lede, body, onOurSite)

Block level

- Paragraphs are separated by ONE blank line. Do not hard-wrap inside a paragraph.
- `## Heading` — a few headings where they help the reader; not one per question.
- `> ` quotation lines — a quotation from something other than our stored
  entries (e.g. the author's introduction). Consecutive `>` lines form one
  quote. A line that is Arabic renders right-to-left in the Arabic font. Put the
  attribution/translation label on a final line starting `— `, e.g.
  `> — Ibn Fāris, introduction to *Maqāyīs al-Lugha* (translation for this guide)`.
  Cite it with [^id].
- An excerpt from an entry that al-nuqta DISPLAYS:

      :::excerpt dxn|ibn-faris-maqayis-al-lugha
      الدَّالُ وَالْخَاءُ وَالنُّونُ أَصْلٌ وَاحِدٌ، وَهُوَ الَّذِي يَكُونُ عَنِ الْوَقُودِ
      ---
      "Dāl, khāʾ and nūn are a single root: that which comes from fuel…"
      :::

  The part above `---` must be copied from the stored original text of that
  entry (`python3 roots/backend/_dict_guide_tool.py entry <bw> <slug>`); the
  validator checks it (vowel marks and punctuation ignored). Use `…` to skip
  material. Below `---` goes a translation written FOR THIS GUIDE (the page
  labels it so). For English-language works (Lane, Salmoné) the original is
  English: omit `---` and the translation. The page adds the caption and a link
  to the entry automatically.

Inline

- `*italic*` for transliteration and titles; `**bold**` sparingly.
- `[[root:<bw>|<dictionary_slug>|<label>]]` — EVERY mention of a root. Renders
  as a link to `/root/<bw>#dict-<dictionary_slug>`, which opens the root page,
  expands that dictionary's entry and scrolls to it.
  - `<bw>` is the site's Buckwalter id (`_dict_guide_tool.py find-root د خ ن`);
    never guess it from the Arabic.
  - `<dictionary_slug>` is the dictionary being discussed — normally this
    guide's own; in a comparison, link the root once for EACH dictionary
    (e.g. "…as [[root:dxn|ibn-faris-maqayis-al-lugha|د خ ن]] in Ibn Fāris and
    [[root:dxn|al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran|in al-Rāghib]]…").
  - The link must lead to an entry the site DISPLAYS; the validator rejects any
    other. If you must name a root that this dictionary does not display on our
    site, use `none` as the slug and say so in the sentence ("our copy has no
    entry for it") — prefer choosing another example.
  - `<label>` is what the reader sees: usually the root letters spaced
    (`د خ ن`), optionally followed by a transliteration (`د خ ن *d-kh-n*`).
  - Bare spaced root letters (`د خ ن`) or hyphenated transliterated roots
    (`d-kh-n`) outside a root link are validation errors. Ordinary Arabic words
    (دُخَان *dukhān*) are fine unlinked.
- `[[guide:<guide-slug>|<label>]]` — link to another dictionary guide
  (slugs in registry.ts).
- `[^<source-id>]` or `[^<source-id>|<locator>]` — a citation, placed right
  after the words it supports (after punctuation). Locator = page, volume,
  entry, or section, e.g. `[^haywood|pp. 41–43]`, `[^harun-ed|vol. 1, p. 3]`.
  Only give a page number you actually saw.
- Qur'an references as `Q 41:11` (or `41:11`); they become verse links. Any
  `n:n` pattern is treated as a Qur'an reference and must exist.

## Validation

    cd roots/frontend && node scripts/validate-dictionary-guides.mjs <guide-slug>

(needs the local backend on http://localhost:5000). Fix every ✗ error; read
every ! warning.

## House rules (from the brief — non-negotiable)

- Central question: "What kind of guide is this dictionary, and how should I
  read it?" An engaging essay for a curious reader of Qur'anic Arabic — not an
  encyclopedia entry, not a list of answers. Plain English; explain necessary
  terms; Arabic where it helps, with translation.
- 700–1,100 words (lede + body) when reliable sources support it; substantially
  less when they don't — then fill `limitedEvidence` and say plainly what cannot
  be established. Never pad.
- Biography only where it explains the dictionary. No generic praise, no
  "greatest"/"most important" claims unless a cited source makes exactly that
  claim (and then attribute it), no lists of teachers or works.
- Describe each work on its own terms; do not force it into an "original root
  meaning" narrative.
- 2–3 verified root examples displayed on our site (fewer if evidence is thin),
  at least one read closely: root and Arabic words; the meanings the entry
  gives; the evidence/reasoning it uses; what that shows about method; any
  uncertainty. One example illustrates a method; it does not prove how every
  entry works.
- Brief comparison with another dictionary only when well supported — then link
  the root in BOTH dictionaries.
- Never invent an example, quotation, etymology, citation, page number or URL.
  Never attribute your own explanation to the author. Distinguish direct
  quotation / translation / paraphrase / interpretation; label translations made
  for the guide.
- Separate the author's own voice from the scholars he quotes.
- Do not treat the dictionary's date as the date of the usage it records; do not
  present one scholar's semantic proposal as established fact; acknowledge real
  disagreement (attribution, dating, method).
- Distinguish the original work from any abridgment, commentary, translation or
  edited selection; do not assume the person named in a title wrote the work.
- If the site shows only part of an entry or a condensed English rendering, do
  not promise the reader material that is not there.
- Sources: prefer the dictionary itself (introduction, entries), scholarly
  editions, academic research, reputable reference works (e.g. Encyclopaedia of
  Islam, Encyclopaedia Iranica, Baalbaki's *The Arabic Lexicographical
  Tradition*, Haywood's *Arabic Lexicography*). General pages (Wikipedia) only as
  a starting point, never the sole support for a claim. Every source listed must
  have been consulted; every URL opened and working.

## What the page renders around your text (do not repeat it)

1. Header: `kind` (eyebrow), `title` + `titleAr`, `titleGloss`, `author`
   (+ `authorAr`), `period`.
2. `lede`, then `body`.
3. A shared box on EVERY guide, "How al-nuqta presents this dictionary":

   > On root and word pages, each entry opens in a readable English version
   > written for al-nuqta. It is drafted by AI from the stored original and
   > checked against it in a separate AI review. It keeps the entry's
   > distinctions of meaning, grammar and quoted evidence but condenses — chains
   > of transmitters, repeated synonyms and digressions are dropped, and on some
   > long or multi-root entries it covers only part — so it is not the author's
   > own wording. "Original Text" shows the stored original (Arabic, or English
   > for Lane and Salmoné) as published on arabiclexicon.hawramani.com, beside a
   > closer English translation (for Lane and Salmoné, a lightly edited copy of
   > the English), also prepared for al-nuqta. On this page, the boxed excerpts
   > come from that stored original; other quotations come from the works listed
   > under Sources. Translations from Arabic were made for this guide unless
   > another translator is named.

4. `onOurSite` under the heading "This dictionary on al-nuqta": ONLY the
   work-specific facts — which text/edition the stored copy represents (if it
   can be established), how many roots we display, peculiarities of the stored
   text a reader will meet (abbreviations, markings, very short or very long
   entries, parts of the work that are missing), anything a reader should NOT
   expect to find. Plain, short (≈ 60–150 words).
5. `limitedEvidence` (if present) in a quiet note.
6. Numbered sources list (from `sources`, in citation order), each with its
   link.

## Site facts you may rely on (from the project's own records)

- The dictionary panel on root pages (`/root/<bw>`) and word pages
  (`/word/<s>:<a>/<pos>`) lists the works in order of the author's death year
  as stored in the `dictionaries` table (e.g. al-Rāghib is stored as 1109,
  al-Zabīdī as 1790). If your research shows a stored date is wrong or
  disputed, report it in your return value (`siteDataIssues`) — do not edit
  the database.
- The panel opens one entry by default (the site prefers Ibn Fāris, then
  al-Rāghib, then the Ibn ʿAbbās text, then Kitāb al-ʿAyn …) — a site choice,
  not a scholarly ranking; never present it as one.
- Texts were collected from arabiclexicon.hawramani.com, one page per root,
  split by dictionary section; `source_url` in each entry points back to it.
- 1,639 roots have at least one displayed entry; the per-dictionary counts are
  in `_dict_guide_tool.py dicts`. The same entries are live on al-nuqta.com.
