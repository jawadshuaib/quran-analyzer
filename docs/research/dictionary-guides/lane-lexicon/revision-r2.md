# Lane's Lexicon guide — revision after verification round 2

Guide: `roots/frontend/src/content/dictionary-guides/guides/lane-lexicon.ts`
Reviser, 2026-09-26. Worked from `verification-r2.md` (1 NQ, 0 U, 4 brief suggestions).

Sources I opened myself this round:
- Internet Archive `LAB1865AREN`, file "(VOL. 5)": `_page_numbers.json` and `_djvu.txt`, downloaded and read.
- The same item, page images: VOL. 4 leaf 0472 (printed p. 1749, art. صوم) and VOL. 2 leaf 0293 (printed p. 658, art. حنف), both viewed.
- https://laneslexicon.github.io/lexicon/site/lane/preface/ (HTTP 200; Preface text checked).
- `_dict_guide_tool.py entry Swm william-edward-lane-arabic-english-lexicon` (entry 5692).

Validator after revision: `node scripts/validate-dictionary-guides.mjs lane-lexicon` gives **ok**, 0 errors, 0 warnings. It reports 4 root links, 3 excerpts and **1,099 words** (lede + body, excluding excerpts). `tsc --noEmit` reports nothing for this file.

## Flagged claim

### C77 (needs qualification): where Lane-Poole's texts sit in the "VOL. 5" file
**Change.** In the `lane-poole` source citation, "where both follow Part 5 in the file labelled 'VOL. 5'" became "where both are printed at the front of the file labelled 'VOL. 5', after the Part 5 title page and before Lane-Poole's Memoir". This is the verifier's wording.

**Evidence** (my own reading of the VOL. 5 page map and OCR):
- **Page map.**
  - Leaf 3: page "i", OCR values "5", "1874".
  - Leaves 4–5: pp. ii–iii ("1876", "1877").
  - Leaf 6: p. iv ("1893").
  - Leaf 7: p. v ("1801", "1814").
  - Leaf 44: page number "1760", the first lexicon page of Part 5.
- **OCR, in file order:**
  - l. 117–125: "BOOK I.—PART 5. … 1874."
  - l. 128: "EDITOR'S PREFACE." It opens: "Since the Fifth Part of this work was published, the hand that wrote it has become still. After thirty-four years of labour at the Lexicon, Mr. Lane died, on the tenth of August, 1876."
  - l. 218–219: "STANLEY LANE POOLE. July, 1877."
  - l. 222: "POSTSCRIPT". It is signed at l. ~275: "S. LANE-POOLE. 1st January, 1893."
  - Then comes "EDWARD WILLIAM LANE. 1801—1825. The life of a great scholar …", which is the Memoir.
- **The Memoir is Lane-Poole's own.** The Editor's Preface (l. 180–181) says: "The appearance of this Part has been delayed by the difficulties presented in the composition of the Memoir which is prefixed. I have had to tell the story of a life …".

## Brief suggestions

- **‡ on "from speech" (adopted).**
  - **The excerpt.** In the صوم excerpt, the first "…" now gives the skipped words in part: "and … by a tropical application, ( TA ,) ( tropical :) from speech: …". I left out the source groups "( S , * M , &c.)" and "( S , * M , Mgh , Msb , * K , TA :)". Quoting them would have needed a sentence explaining Lane's asterisk, and the essay is at its word limit.
  - **The essay sentence.** "Lane files Ibn ʿAbbās's reading of Mary's vow in Q 19:26, abstaining from speech, under his †" became "Abstaining 'from speech' is figurative (‡) on the *Tāj*'s word; Ibn ʿAbbās's reading of Mary's vow in Q 19:26 carries Lane's own †."
  - **Why.** A reader can now see that the "from speech" sense is marked figurative on an Arabic authority's word. Only the verse reading is marked on Lane's own judgment. The two marks in one excerpt also show the ‡/† distinction explained in the paragraph before it.
  - **Other sentences.** "Apart from the brackets and the † mark, every claim here is credited to someone else" stays true, because the ‡ is credited to TA.
  - **Evidence.** See New claims 1.
- **Word limit (offsetting cuts).** The new sentence adds 5 counted words. I cut 6 to offset them:
  - "is tagged TA, reported from the *Tāj*" became "is tagged TA". TA is already expanded as "the *Tāj*" in the abbreviation paragraph.
  - "Lane's 'xix. 27' is Q 19:26 on this site" became "Lane's 'xix. 27' is our Q 19:26".
  - The result is 1,099 words.
- **Abbreviation paragraph (left as is).** It is already tight. Adding the asterisk convention would have lengthened it, and I avoided that.
- **Transcription link (adopted).** The `lane-preface` citation now reads "…on the Internet Archive, and in the transcription at laneslexicon.github.io/lexicon/site/lane/preface/". I opened that page (HTTP 200) and checked that it has the Preface text. It includes "As the Táj el-'Aroos is the medium through which I have drawn most of the contents of my lexicon", "It has two meanings: 'The Flow of the Sea' and 'The Extension of the Ḳámoos.'", and the closing "E. W. L. December , 1862." The research notes show the first draft used this transcription, so I kept the mention and made it traceable rather than dropping it. All page numbers in the guide still rest on the archive.org scans.

## Removed claims
1. "where both follow Part 5 in the file labelled 'VOL. 5'" (C77, wrong location in the scan). Replaced as above.
2. ", reported from the *Tāj*" (cut for length). The point survives as "tagged TA", with TA defined earlier.
3. "on this site" (cut for length; now "our Q 19:26").

## New claims (each checked in a source I opened)
1. **Abstaining "from speech" is figurative (‡) on the *Tāj*'s word.**
   - **Print p. 1749** (VOL. 4 leaf 0472, image viewed): "and (Ṣ,* M, &c.) by a tropical application, (TA,) ‡from speech: (Ṣ,* M, Mgh, Mṣb,* Ḳ, TA:)". The tag TA follows the words "by a tropical application", so the figurative label is credited to the *Tāj*.
   - **Stored entry 5692:** "and ( S , * M , &c.) by a tropical application, ( TA ,) ( tropical :) from speech: ( S , * M , Mgh , Msb , * K , TA :)".
   - **Where ‡ comes from.** The Preface, p. xxv, says ‡ marks "what is affirmed to be tropical … generally on the authority of the Asás". That passage was already cited in the guide.
2. **Ibn ʿAbbās's reading of Q 19:26 carries Lane's own †.** This was already verified (C40); only the wording changed. The same image of p. 1749 reads: "صَوْمًا means † [Verily I have vowed unto the Compassionate] an abstaining from speech. (Ṣ, M, Mṣb.)".
3. **Source locator (C77).** Both texts are at the front of the "VOL. 5" file, after the Part 5 title page and before Lane-Poole's Memoir. Evidence is given under C77 above.
4. **Source citation.** The Preface transcription is at laneslexicon.github.io/lexicon/site/lane/preface/, opened as described above.

## Disputed
None. I accepted C77 with the verifier's wording.

## Notes for the next verifier
- **صوم aorist.** The print (p. 1749) gives the aorist of صَامَ in full, "aor. يَصُومُ". The stored text, which the excerpt must copy, has "aor. ـُ".
  - The guide's general statement that "aor." marks the imperfect "often by its vowel alone" still holds for Lane's print. P. 658 (image viewed), art. حنف, has "حَنَفَ, aor. ـِ", "حَنِفَ, aor. ـَ" and "حَنُفَ, aor. ـُ", matching the stored Hnf entry.
  - The stored صوم line is therefore an abbreviation made in the digital text. The guide does not claim otherwise.
- **The "(tropical :)" in the excerpt.** The صوم excerpt now shows one "(tropical :)" and one "(assumed tropical :)". The sentence after the excerpt credits the first to TA and the second to Lane.
- **Site-data issues** from verification-r2, items 1–7, still stand. They are not for this guide to fix.
