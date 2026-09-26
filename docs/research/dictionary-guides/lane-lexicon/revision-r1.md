# Lane's Lexicon guide — revision after verification round 1

Guide: `roots/frontend/src/content/dictionary-guides/guides/lane-lexicon.ts`
Reviser, 2026-09-26. Worked from `verification-r1.md` (6 NQ, 0 U, 6 brief suggestions).

Sources I opened myself for this round:
- Internet Archive item `LAB1865AREN`. I downloaded the OCR text of the files labelled "VOL. 1" (Preface), "VOL. 3" (Part 7) and "VOL. 5" (Part 5, then Lane-Poole's Editor's Preface and Postscript). I also downloaded the "VOL. 3" PDF and rendered printed p. 2487 as an image.
- `_dict_guide_tool.py entry` for Hnf (6343) and Swm (5692), plus `grep` counts over the displayed Lane entries.

Validator after revision: `node scripts/validate-dictionary-guides.mjs lane-lexicon` → **ok**, 0 errors, 0 warnings. 4 root links, 3 excerpts, **1,100 words** (lede + body, excluding excerpts); onOurSite is about 168 words. `tsc --noEmit` reports nothing for this file.

## Flagged claims

### C51 (must-fix): "Up to that point … every article ready"
**Change.** The "After the letter qāf" section now:
1. Explains why Lane-Poole found the articles in mixed states. Lane had written in the *Ṣiḥāḥ*'s order, by a root's last letter [^lane-preface|p. xiv], and finished articles as the printers neared them. So Lane-Poole found articles "in three different stages", from bare notes to text ready for the press.
2. Attributes the "up to قد" statement to Lane-Poole ("Up to قد, he reported, every article was ready") and keeps the collation quote.
3. Keeps Haywood, now saying he called "Lane-Poole's estimate" inaccurate, the lexicon being "a very inadequate reference work" after قد.
4. Rewrites the sentence introducing the qtl excerpt: "Even ق ت ل, which precedes قد, was left as notes: the main text says 'See Supplement', and our entry is that note" [^lexicon|pp. 2487, 2984].

The page no longer implies that every root before قد is a finished article. It shows the counter-example openly.

**Evidence.**
- Editor's Preface, July 1877 (VOL. 5 OCR, checked against the page wording the verifier saw in the image): "I found articles in three different stages: some consisting only of Mr. Lane's own notes, without any reference to the original authorities; others written, but needing to be collated with one or two manuscripts acquired later; and some completely written and ready for the press. The difference is explained by the fact that Mr. Lane was of necessity obliged to write in the order of the Sihah, and that as the printers gradually approached him he finished those articles which were likely to be speedily wanted …" / "At the time of his death my Uncle was engaged on the article [قد]. Up to this point every article is ready for the printers. Of the rest the majority are written, but some need collation."
- Preface p. xiv (VOL. 1 OCR), on the *Ṣiḥāḥ*: "mentioning each word according to the place of the last letter of the root, and then the first and second, in the usual order of the alphabet".
- Printed p. 2487 (VOL. 3 PDF, page 15 rendered and viewed). The top of the left column reads "[قتع / قتل / قتم / قتن / قتو / See Supplement.]" and is followed by the article قث.
- I wrote "was left as notes" rather than the verifier's "were never written up". The Postscript says the Supplement holds "such notes as Mr. Lane had made from time to time with a view to the eventual writing of these articles".

### C11: lede "whose voice you are hearing"
**Change.** The lede now ends "…you can tell, line by line, which source Lane is reporting and where he speaks himself" (the verifier's wording). "How to read an entry" now opens "The initials after each sense name Lane's authority for it" instead of "name its source". This matches Lane's own term: p. xxvi says "I have inserted nothing in my lexicon without indicating at least one authority for it". It does not claim that the tag is the originator.
The point that a TA tag may cover matter taken from the *Lisān* was already in the body (p. xx) and is kept.

### C22: "Rather than reduce a root to one idea"
**Change.** Deleted. The sentence now begins "He orders a root's senses by their relations, marks the figurative ones …" [^lane-preface|p. xxv]. The only support is p. xxv: "Always, in the arrangement of significations, I have, to the utmost of my ability, paid attention to their relations, one to another."

### C24: definition of "classical"
**Change.** The sentence now reads: "By 'classical' he meant, following the Arab philologists, the Arabic of an age that 'nearly ended with the first century' of Islam: that of the pre-Islamic poets and of those who lived into Islam, with the best early Islamic poets also holding 'classical rank'." The next sentence is separate: "The Arabs, he notes, held the Qur'an to be the highest authority."
**Evidence.** Preface p. ix (VOL. 1 OCR): "for the classical age may be correctly defined as having nearly ended with the first century, when very few persons born before the establishment of El-Islám through Arabia were living. Thus the best of the Islámee poets may be regarded, and are generally regarded, as holding classical rank, though not as being absolute authorities … The highest of all authorities, however, on such points, prosody of course excepted, is held by the Arabs to be the Kur-án."

### C47: Abū ʿUbayda "unreconciled"
**Change.** The sentence now reads: "Abū ʿUbayda's report that pre-Islamic idol-worshippers called themselves *ḥanīf*, and that with Islam the name passed to the Muslim, sits beside the rest unweighed."
**Evidence.** Entry 6343 (Hnf), displayed original: "[or,] accord. to AO , the worshipper of idols, in the Time of Ignorance, called himself thus; and when El-Islám came, they thus called the Muslim: accord. to Akh , … accord. to Ez-Zejjájee, …: ( TA :)". Lane adds no verdict. "Pre-Islamic" renders "in the Time of Ignorance".

### C65: "CCC … is a conversion error"
**Change.** onOurSite now says: "A stray 'CCC' in some entries is not Lane's; it appears to be a digitisation artefact." "Some" replaces "a few" (22 displayed entries), and the cause is hedged.

## Brief suggestions

- **titleGloss attribution.** I changed the header gloss to "Madd al-Qāmūs, which Lane glossed as 'the flow of the sea' and 'the extension of the Qāmūs'", so the page now says the gloss is Lane's. I did not add a cited sentence to the body, because the body is at its word limit and the header already shows the two meanings. Source: Preface p. xxxii (VOL. 1 OCR): "I have adopted in imitation of that given to his lexicon by El-Feyroozábádee. It has two meanings: 'The Flow of the Sea' and 'The Extension of the Kámoos.'"
- **"Later senses" (could be read as chronological).** Now "Further down, the horse standing unfed and the still water carry †, the wind falling calm ‡."
  - Marks re-checked in entry 5692: horse "(assumed tropical :) The horse stood without eating of fodder"; wind "( tropical :) The wind became still, or calm"; water "(assumed tropical :) The water became still, or motionless".
  - The next paragraph now reads "This order follows relations between senses; it is not a dated history of the word."
- **"The commonest are".** Now "They include". The frequency claim is gone.
- **Abbreviation paragraph.** Left as it was. It is already tight.
- **Word count.** The body went from 1,099 to 1,172 after the fixes, then back to 1,100 after these cuts:
  - Cut the al-Dasūqī / thirteen-years sentence.
  - Dropped "later Duke of Northumberland" and the Lord Prudhoe funding clause, and merged the Golius sentence into "In 1842 Lane set out to draw not on Arabic 'epitomes or abstracts or manuals', as Golius had in Latin, but on 'the most copious Eastern sources'" (p. v: "IN the year 1842 … enabled me to undertake the composition of this work").
  - Shortened the square-brackets quotation.
  - Dropped "and his 'ii. 181' is Q 2:185", which is not in the excerpt.
  - Cut "Book II, planned for rare words, never appeared."
  - Made small wording trims.
- **onOurSite warning about the English version.** Added: "The readable English version drops most source initials and ‡/† labels, and can say more than Lane does; 'Original Text' shows whose sense is whose." I kept it general so it stays true if the Swm harmonized text is corrected. See the new claims below for the evidence.

## Removed claims
1. "Rather than reduce a root to one idea" (C22, the essay's own framing).
2. "whose voice you are hearing" (C11, overstated).
3. Abū ʿUbayda's report "stands, unreconciled, beside glosses meaning 'a Muslim'" (C47).
4. "CCC … is a conversion error" (C65, the cause was inferred).
5. "The commonest are S … K … TA …" (frequency claim never checked).
6. Cut for length, all previously verified: Lord Prudhoe "later Duke of Northumberland" funding the project; copying and collating the *Tāj* "mostly by his assistant Shaykh Ibrāhīm al-Dasūqī, took over thirteen years"; Lane's "ii. 181" = Q 2:185; "Book II, planned for rare words, never appeared"; "(Williams and Norgate, 1863–93)" in onOurSite (still in the source list).
7. "Up to that point … [Lane-Poole] found every article ready" as a flat statement. It is now attributed ("he reported") and set against the قتل counter-example.

## New claims (each checked in a source I opened)
1. **The *Ṣiḥāḥ* files a root under its last letter.** Lane, Preface p. xiv: "according to the place of the last letter of the root, and then the first and second".
2. **Lane wrote in the *Ṣiḥāḥ*'s order and finished articles as the printers neared them, so Lane-Poole found articles "in three different stages", from bare notes to text ready for the press.** Editor's Preface 1877; quotation under C51 above.
3. **قتل precedes قد yet was left as notes; the main text says "See Supplement".** Printed p. 2487 (image viewed: "[قتع قتل قتم قتن قتو See Supplement.]"); Supplement p. 2984 (verifier's image check, C57). Page 2487 has been added to the `lexicon` source citation.
4. **Many Supplement notes record the "contemporary speech" of Lane's day.** Postscript, 1 January 1893 (VOL. 5 OCR): "many of them are clearly the record of contemporary speech, which he would doubtless have excluded from a Lexicon of the classical language". I added it because it bears directly on the site's concern with the date of the usage an entry records.
5. **The best early Islamic poets hold "classical rank".** Preface p. ix; quotation under C24.
6. **Lane glossed the Arabic title himself (header).** Preface p. xxxii.
7. **The readable English version drops most source initials and ‡/† labels, and can say more than Lane does (onOurSite).**
   - Counts from `_dict_guide_tool.py grep`, displayed entries, original vs harmonized:

     | pattern | original | harmonized |
     |---|---|---|
     | `\bTA\b` | 1,361 | 119 |
     | `\bMsb\b` | 1,261 | 151 |
     | `tropical\|‡\|†` | 978 | 312 |

   - "assumed tropical" appears in 782 originals, while "assumed" appears in 26 harmonized texts.
   - "Say more than Lane does": the Swm harmonized text (entry 5692) ends "Throughout, Lane traces every sense back to a single underlying idea: standing still, holding back, or abstaining". It also heads the figurative senses "all built on the idea of stillness/holding-back" and says "Lane reports this as the primary, original meaning". Lane's original credits the primary sense to TA and marks complete breaks (A2–A4).
   - "Original Text" is the label of the stored-original view, per FORMAT.md's shared box.
8. **Haywood's "very inadequate reference work" applies "after قد".** Haywood p. 125: "after the article 'qadda'". This was already verified; only the wording of the paraphrase outside the quotation changed.
9. **Source locator:** Lane-Poole's Editor's Preface and Postscript follow Part 5 in the file labelled "VOL. 5" of `LAB1865AREN`. Confirmed: VOL. 5 OCR lines ~130–260 hold both texts.

## Disputed
None. I accepted every flagged item. For C51, C47 and C65 I used slightly different wording from the verifier, as explained above. In each case the new wording claims no more than the evidence.

## Notes for the next verifier
- Lane-Poole's "Up to this point every article is ready" is now reported, not endorsed. The page shows the قتل counter-example beside it, and Haywood's verdict.
- The onOurSite sentence on the English version depends on the site's generated texts. If those are regenerated, re-check the claim that they drop most source initials.
- The site-data issues in verification-r1 still stand: name_ar holds "Lane's Lexicon"; the Swm harmonized framing; verse numbers repeated in the English versions.
