# Revision round 2: tuhfat-al-arib

Reviser, after verification-r2.md (2026-09-26). File edited:
`roots/frontend/src/content/dictionary-guides/guides/tuhfat-al-arib.ts`: one body sentence (C49), one onOurSite
clause (ح ل م), and the `hatib` source citation. Header fields, summary and lede are unchanged.

Validator: `node scripts/validate-dictionary-guides.mjs tuhfat-al-arib` returns "ok, 1/1 guides pass", with 0 errors
and the one expected warning (the `kyn|none` link, which the onOurSite sentence explains). Words (lede + body,
excluding excerpts): 1,081. The count was 1,068; the C49 fix added 13 words.

## Sources I opened for this revision

- **Stored entry, m ʿ n** (`_dict_guide_tool.py entry mEn …`). Entry 16654, displayed:
  "معن : {معين}: جار ظاهر. {الماعون}: كل عطية ومنفعة في الجاهلية، وأما في الإسلام فالزكوة والطاعة."
  It gives no verse number and no evidence.
- **Local `morphology` table.** Root `mEn` occurs once in the Qur'an, at 107:7:2 (مَاعُونَ).
- **Tuḥfa, Shamela 13304/67 (print p. 104).** The lines read "حرم: {والمحروم}: المحارَف. {محرومون}: ممنوعون من الرزق. / [حلم] / حكم: {حكمة}: والحكمة العقل."
  The ح ل م heading stands alone in square brackets, with nothing under it.
- **Stored entry, ḥ l m** (entry 4683). Displayed as "حلم :", with no brackets and no text.
- **Hatib & Tekin, full PDF** (dergipark download/article-file/2570046, 24 pp., HTTP 200). Page 1 (journal p. 47) gives three titles:
  - Turkish: "Ebû Hayyan El-Endelüsî'nin Tuhfat Al-Arib Adlı Kitabında Dilin Anlaşılması Zor Kelimeler Üzerindeki Etkisi"
  - Arabic: "الأثر اللغوي للغريب في كتاب تحفة الأريب لأبي حيان الأندلسي"
  - English: "The linguistic effect in Tuhfat Al-Arib by Abu Hayyan Al-Andalusi"
  - The citation block also confirms the volume, issue, pages and DOI: "Universal Journal of Theology 7/2 (2022): 47-65. https://doi.org/10.56108/ujte.1152423".

## Flagged claims

### C49 (needs qualification): "It cites no evidence and leaves Q 107:7 undecided"

- Before: "It cites no evidence and leaves Q 107:7 undecided, but it flags that a sense "in Islam" sits beside an older,
  general one: the very question a reader of that verse must weigh."
- Now: "It cites no evidence and names no verse. Its "in Islam" sense may be meant for Q 107:7, though the entry does
  not say so; either way, it sets that sense beside an older, general one: the very question a reader of the verse
  must weigh."
- Why: I accept the verifier's point. "Undecided" credited the entry with a neutral stance it never states. Its
  contrast "وأما في الإسلام فالزكوة والطاعة" can fairly be read as the Qur'an's own sense. The new wording does three things:
  - it states only what is certain: no evidence and no verse named;
  - it allows the reading the verifier describes, as a possibility ("may be meant");
  - it keeps the point the verifier marked as supported (C50): the entry sets a sense "in Islam" beside an older,
    general one.
- The link to Q 107:7 rests on two facts. The headword {الماعون} is the Qur'anic form, and in our `morphology`
  table this root occurs only at 107:7. The page does not claim that the word occurs only once.
- This combines the verifier's two suggested wordings. I did not use the first alone ("does not name Q 107:7, but it
  flags …"). Ending on "the very question a reader … must weigh" would still suggest that the entry leaves the
  question open.

## Brief issues and what I did

- **Length (suggestion).** Not trimmed. The page is 1,081 words, still under the 1,100 ceiling, and verification-r2
  judged it "not padded; each section does work". I did look at the two paragraphs it named:
  - The al-Fayyūmī paragraph carries the brief's cross-dictionary comparison, which is linked in both dictionaries.
    It also carries the Baḥr vol. 1 p. 12 statement of method, which ties the glossary to its author's practice.
  - "Reading it well" carries the counts that correct the Hatib & Tekin generalisation, and the page's closing advice
    on dating.
  - Any cut would remove verified substance rather than slack. The only growth this round is the 13 words the C49 fix needed.
- **hatib title (suggestion). Applied, with a note.** The bracket now reads "[The linguistic effect of the *gharīb* in
  *Tuḥfat al-Arīb* by Abū Ḥayyān al-Andalusī; the published English title omits "of the *gharīb*"]".
  - The old bracket was not a mistranslation. It was, word for word, the article's own published English title
    (PDF p. 1: "The linguistic effect in Tuhfat Al-Arib by Abu Hayyan Al-Andalusi").
  - It did not match the transliterated Arabic title, which includes للغريب.
  - The new bracket translates the Arabic title that is given, and says why the published English title differs, so a
    reader searching for the article is not misled.
- **Ewl / qwm / Sdy (optional).** No change. The verifier agrees that the hedge "Here, at least" covers it.
- **ح ل م bracket (optional). Applied.** onOurSite now reads "… is a heading with nothing under it, as in the printed
  text, where it stands in square brackets.[^tuhfa|p. 104]".
  - I did not write "the editor brackets it". The page already says that "the square brackets belong to that modern
    text, not to Abū Ḥayyān", and I have not seen the editor's own account of this bracket.
  - The wording states only what p. 104 shows.

## Removed claims

- "leaves Q 107:7 undecided" (C49), replaced as above.

## New claims (each checked in a source I opened)

1. **The entry's "in Islam" sense "may be meant for Q 107:7, though the entry does not say so."** This is a hedged
   interpretation, not a statement of fact.
   - Entry 16654: "{الماعون}: كل عطية ومنفعة في الجاهلية، وأما في الإسلام فالزكوة والطاعة". No verse is named.
   - `morphology`: root mEn occurs once, at 107:7:2 مَاعُونَ.
2. **The ح ل م heading stands in square brackets in the printed text** [tuhfa p. 104]. Shamela 13304/67: "… ممنوعون من الرزق. [حلم] حكم: {حكمة} …".
3. **The published English title of Hatib & Tekin omits "of the gharīb"** (sources list only). PDF p. 1:
   - English: "The linguistic effect in Tuhfat Al-Arib by Abu Hayyan Al-Andalusi"
   - Arabic: "الأثر اللغوي للغريب في كتاب تحفة الأريب لأبي حيان الأندلسي"

## Disputed

None. I accept the C49 flag. On the hatib suggestion, see above: the old English bracket was the authors' own
English title. I adopted the literal rendering and recorded that the published title differs.

## Site-data issues carried forward (not mine to fix; from verification-r2)

- **kwn (entry 117).** The site's English renderings call the editor's bracket "[جسرة]" a manuscript or variant
  reading. The guide calls it "editor's bracket".
- **Scrape gap.** About 55 printed headwords are missing from `dictionary_entries`. Several of them are on
  hawramani's own index.
- **mEn (entry 16654), harmonized English.** It contains an editorial aside ("This later sense is presented here as
  the author's own gloss …"). Readers who follow the guide's link to this entry will see it.

## Return values

- validatorPassed: true
- words (lede + body, excluding excerpts): 1,081
