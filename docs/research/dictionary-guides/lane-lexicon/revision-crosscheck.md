# Lane guide: cross-guide consistency fixes (2026-09-26)

File edited: `roots/frontend/src/content/dictionary-guides/guides/lane-lexicon.ts`.
Validator: `node scripts/validate-dictionary-guides.mjs lane-lexicon` passes with no errors or warnings. Word count (lede + body) is 1,107, up from 1,099.

## Changes

1. **Tāj date (contradiction with the taj-al-arus guide).**
   - Before: "al-Zabīdī's *Tāj al-ʿArūs*, finished in the 1760s: "the medium …"".[^lane-preface|pp. xviii–xix]
   - After: "al-Zabīdī's [[guide:taj-al-arus|*Tāj al-ʿArūs*]], compiled there in the 1760s and 1770s,[^lane-preface|p. xviii][^kuwait-ed|vol. 1, editor's introduction] which he called "the medium …".[^lane-preface|p. xix]"
   - I wrote "there" instead of the critic's "in Cairo" because the sentence already opens "In Cairo".
   - I left out Lane's own 1767/8 date. It would add about 12 words to a guide already at the top of the length range, and the guide no longer states that date. It is logged below in case a later round wants it.
   - The old citation `pp. xviii–xix` backed the 1760s date with Lane's own figure. The new range ends in 1774, which Lane p. xviii contradicts, so the citation was split. Lane p. xviii now backs only "compiled in Cairo" and the start. Lane p. xix backs the quotation. The 1770s end rests on a new source, `kuwait-ed`.
2. **Links to other guides.**
   - The Tāj is linked in its first mention, as shown in change 1.
   - "generally on the authority of the Asás" is now followed by "([[guide:asas-al-balagha|al-Zamakhsharī's *Asās al-Balāgha*]])".
   - The abbreviation list is not linked.
3. **Lede.** "the great Arabic dictionaries" became "the medieval Arabic dictionaries". This matches the summary, which says "the medieval Arabic lexicons, read mainly through the *Tāj*".
   - Caveat: the *Tāj* is an 18th-century work. The phrase describes what Lane put into English, largely medieval lexicons that he read through the *Tāj* (p. xx: most of the *Tāj*'s additions stand word for word in the *Lisān*). It does not date every book he used. I judged this acceptable.
   - Lane-Poole's Editor's Preface, cited at that point, supports only "thirty-four years of labour at the Lexicon". It does not say "great".
4. **Heading.** "## How to read an entry" became "## Initials, daggers and brackets". No anchor anywhere in `src/` or `scripts/` pointed to the old heading.

## New claims

| Claim | Status | Source opened (this round) | Evidence |
|---|---|---|---|
| The *Tāj* was compiled in Cairo, beginning soon after the middle of the 18th century | S | Lane, Preface p. xviii. Internet Archive `LAB1865AREN`, "(VOL. 1)_djvu.txt", OCR lines 1075–1079; the page header "PREFACE. xix" follows at line 1093 | "is said to have been commenced, in Cairo, soon after the middle of the last century of our era, by the seyyid Murtaḍà Ez-Zebeedee. At the end of a copy of it in his own handwriting, he states that it occupied him fourteen years and some days." |
| The compilation ran into the 1770s, ending in Rajab 1188 AH (Sept–Oct 1774), per the Kuwait editor | S (attributed to the editor in the source note) | Kuwait ed. vol. 1 (1965), Farrāj's introduction. Internet Archive `ZUB1965AR`, file "1 - تاج العروس_djvu.txt", OCR lines 1185–1208 and 887–891 | "وإذا رجعنا إلى أواخر المواد فى تاج العروس نجد أن آخر حرف الذال كان فى ربيع الأول سنة 1187 … وآخر حرف اللام فى شعبان 1187 … وآخر الكتاب فى رجب سنة 1188". On the banquet: "ان المؤلف نفسه وهو الزبيدى نص على أنه أنجزه سنة 118[8] هجرية، وإذن تكون الوليمة … مناسبة إنجازه الجزء الأول". The quotations are normalised from the OCR, which garbles some letters and digits (e.g. "١184"); the final line reads 1188. |
| "1760s and 1770s" as a span | S (combined) | The two rows above | The work began soon after mid-century (Lane) and took al-Zabīdī "fourteen years and some days" (Lane). It ended in 1188/1774 (Kuwait editor). The taj-al-arus guide's lede uses the same span on the same basis (its research-notes.md, row "1760s and 1770s (lede)"). |
| Lane called the *Tāj* "the medium through which I have drawn most of the contents of my lexicon" | S (unchanged claim, re-cited to p. xix alone) | Lane, Preface. VOL. 1 OCR line 1134, after the "PREFACE. xix" header at line 1093 | "As the Taj el-'Aroos is the medium through which I have drawn most of the contents of my lexicon …" |
| ‡ is marked "generally on the authority of the Asás" (now linked to the Asās guide) | S (unchanged) | Lane, Preface p. xxv. VOL. 1 OCR lines 1475–1476 | "I have distinguished (by the mark ‡) what is affirmed to be tropical from what is proper; generally on the authority of the Asás." |
| New source `kuwait-ed`: Farrāj, editor of vol. 1, Kuwait, 1965 | S | `ZUB1965AR`: metadata ("المجلد 1 / عبد الستار فراج / 1965"); OCR line 19 "مطبعة حكومة الكويت" and OCR line 55 "كتبه : عبد الستار احمد فراج" (both normalised from garbled OCR) | The URL https://archive.org/details/ZUB1965AR returned HTTP 200 on 2026-09-26. |

## Not added (available if wanted)

- **Lane's own date.** Lane, p. xviii, names his source for the date: "According to the modern historian of Egypt, El-Jabartee, he was … finished the Táj el-'Aroos A.D. 1767 or 1768" (OCR lines 1077–1079).
- **Suggested wording if restored:** "(which Lane, following al-Jabartī, thought finished in 1767 or 1768)". This is accurate: Lane names al-Jabartī.
- **The Kuwait editor's reading.** He takes al-Jabartī's 1181 AH banquet to mark completion of the first part only.

## Removed claims

- "*Tāj al-ʿArūs*, finished in the 1760s". This follows Lane's al-Jabartī date. The Kuwait editor places completion in Rajab 1188 (1774), and that is now the guide's basis.
- "the great Arabic dictionaries". This was an unsupported evaluation.
