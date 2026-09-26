# Revision round 1 — Mukhtār al-Ṣiḥāḥ

Guide: `roots/frontend/src/content/dictionary-guides/guides/mukhtar-al-sihah.ts`
Responds to: `verification-r1.md` (64 claims: 61 S, 3 NQ, 0 U; 4 suggestions)
Date: 2026-09-26
Validator after revision: `node scripts/validate-dictionary-guides.mjs mukhtar-al-sihah` passes with 0 errors and 0 warnings. It finds 11 root links (10 distinct pairs), 2 excerpts and **1,100 words** (lede + body).

## Flagged claims

### C27 (NQ): "al-Rāzī in at most one in twenty"
- **Now:** "…al-Jawharī quotes verse in about four entries in five, al-Rāzī in **fewer than one in ten**, and…"
- **Evidence (own recount, read-only SQL with the tool's SHOWN filter, 856 shared roots):**
  - Verse markers alone in al-Rāzī (`...`/`…`/الشاعر/أنشد/الراجز): 46 entries (5.4%).
  - Markers plus "قال/قول + named poet": **58 (6.8%)**. The extra roots include ESr, Ebd, Eyr, Sdr, fyA, grm, mkn, ndd, nfl, nwq, srr and xbv, the same kind of hits the verifier found (55).
  - A cross-check found al-Jawharī's verse lines, taken after أنشد / قال الشاعر / قال + poet, that reappear in al-Rāzī's entry for the same root. With the marker set this gives 48 roots in total.
  - An asterisk-based cross-check was discarded because `*` in al-Jawharī also marks non-verse text (it falsely "found" verse in hdy and ydy).
  - Every method gives 46–58 of 856, well under 86 (10%). "Fewer than one in ten" holds whichever detection method is used. I preferred it to "about one in sixteen" because the exact figure depends on the pattern.
  - The al-Jawharī figure was re-confirmed at 679 of 856 (79%), and the length ratio at 0.41.

### C44 (NQ): citation for "al-Rāzī kept al-Jawharī's rhyme arrangement"
- **Now:** "Al-Rāzī kept al-Jawharī's "rhyme" arrangement,[^ima][^khatir-1916|preface, p. د] which files roots by their last letter.[^haywood|p. 68]"
- Haywood p. 68 now supports only the definition. The claim that al-Rāzī kept the order rests on IMA and Khāṭir.
- **Evidence (opened myself):**
  - Khāṭir 1916, page image n9 (https://archive.org/download/RZY1916AR/page/n9.jpg), headed (د), which I viewed. The djvu OCR has the same passage:
    > وجليّ أن الإمام الرازي جرى على أسلوب الجوهري في إيراد الكلم باعتبار أواخرها
    ("It is clear that Imam al-Rāzī followed al-Jawharī's method of setting out words by their final letters.")
  - The same page carries the already-cited "مع حذف ما لا ينبغي أن يطرق مسامع النشء", so the one locator "p. د" serves both.
- In the same sentence, I added `[^razi-1999]` after "the 1999 Beirut edition our text matches" to support "re-sort by first letter" (C45, already S). I opened Shamela 23193/2175 myself. Its breadcrumb reads "فهرس الكتاب › باب العين › ع ذ ب", and its table of contents lists ع ج ل … ع ذ ب … ع ز ا together under باب العين, which is first-letter order.

### C48 (NQ): "wa-bābuhu … some 520 of the 877 entries"
- **Now:** "One unflagged addition runs through some 520 of the 877 entries we display, and through none of al-Jawharī's: *wa-bābuhu*, "and its class is", or *min bāb*, "of the class of", followed by a model verb."
- **Evidence (own recount, unvowelled text, model verb = one of the 20 in the introduction pp. 7–8):**
  - وبابه/وبابهما/وبابها/وبابهن + model verb: 299 entries.
  - من باب + model verb: 280 entries, of which 223 have no *wa-bābuhu*.
  - Either formula: **522 of 877**. Al-Jawharī: **0 of 866**.

## Suggestions

1. **ع ذ ب, the printed edition: adopted.**
   - **Now:** "…[[root:E*b|…|ع ذ ب]] records only sweet water, as does the printed 1999 edition,[^razi-1999|p. 203] while al-Jawharī's entry also has *al-ʿadhāb*, "punishment". Whether al-Rāzī cut the word or his text lost it before print, we could not check against a manuscript."
   - **Evidence:** I opened https://shamela.ws/book/23193/2175 (page title "ص203 - كتاب مختار الصحاح - ع ذ ب"). The whole entry reads:
     > ع ذ ب: (الْعَذْبُ) الْمَاءُ الطَّيِّبُ وَبَابُهُ سَهُلَ.
     The next item in the table of contents is ع ذ ر.
   - The `razi-1999` source citation now reads "introduction pp. 7–10 and entries".
2. **"The note shows…": adopted.** It now reads "Notes like this show what the book can offer a Qur'an reader…".
3. **Stat clustering: adopted, partly.**
   - Kept: the two most telling statistics, one on verse and length, one on how many notes there are.
   - Cut: "the source they name most often is al-Azharī (our count)". Al-Azharī remains visible through the introduction quotation, the ydy close reading and the new ع م ل sentence.
   - Merged the note count and the Qur'an share into one clause.
4. **Jurists' usage: adopted, one sentence, linked and quoted accurately.**
   - **Now:** "One shows the jurist in him: under [[root:Eml|zayn-al-din-al-razi-mukhtar-al-sihah|ع م ل]], al-Rāzī says the jurists' term *māʾ mustaʿmal*, "used water", can be justified only by analogy with al-Azharī's *istaʿmala al-labin*, "he built with the bricks". For him the legal term extends attested usage; it is not an instance of it."
   - **Evidence:** the displayed entry Eml (id 581, `_dict_guide_tool.py entry Eml zayn-al-din-al-razi-mukhtar-al-sihah`):
     > قُلْتُ: قَالَ الْأَزْهَرِيُّ: يُقَالُ: (اسْتَعْمَلَ) فُلَانٌ اللَّبِنَ إِذَا بَنَى بِهِ بِنَاءً. قُلْتُ: وَقَوْلُ الْفُقَهَاءِ مَاءٌ (مُسْتَعْمَلٌ) قِيَاسٌ عَلَى هَذَا وَإِلَّا فَلَا وَجْهَ لِصِحَّتِهِ غَيْرُ هَذَا القِيَاسِ.
     ("I say: al-Azharī said: one says *istaʿmala* so-and-so the bricks when he built a building with them. I say: the jurists' expression 'used water' is an analogy on this; otherwise there is no ground for its correctness other than this analogy.")
   - Both statements sit inside *qultu* notes, so they are al-Rāzī's additions. "Jurist" rests on al-Ziriklī (C16, already cited in the essay).
   - The last sentence is the essay's interpretation of the note, stated in the essay's voice.
   - **Scope check:** a grep of displayed entries for الفقهاء/أبو حنيفة/الشافعي/أصحابنا found only Eml, Eql and Smm. In Eql and Smm the jurist material (Abū Ḥanīfa vs Ibn Abī Laylā; Abū ʿUbayd on the jurists' *ishtimāl al-ṣammāʾ*) is not inside a *qultu* note. So the essay says "One [note] shows", not "Some".

## Cuts made to stay within ~1,100 words (all previously supported)
- The full name in the body's first sentence was cut; it is still in the header (`authorFull`).
- "visited Egypt and Syria" (Ziriklī).
- "a rare sixth class is stated case by case" (intro p. 8).
- "our English versions do not always show the seam". The same advice remains in `onOurSite` ("in the English versions, check the Arabic to see where a note ends").
- The parenthesis "(*Bāb* also means a chapter, as in 'the chapter of *dāl*'.)"
- Wording tightened, with no change of substance:
  - "refuting the view that he lived in the eighth Islamic century" became "…that he belonged to the eighth Islamic century". Ziriklī: من رجال القرن الثامن.
  - "His evidence is a named earlier lexicographer, al-Azharī, and …" became "His evidence is al-Azharī and …".
  - "The dictionary's date has been disputed" became "The book's date is disputed".

## New claims (each with source)
1. The printed 1999 edition also has only the one-line ع ذ ب entry. Source: Shamela 23193/2175, p. 203 (opened; quoted above).
2. In ع م ل, al-Rāzī (in *qultu* notes) says the jurists' *māʾ mustaʿmal* is justified only by analogy with al-Azharī's *istaʿmala al-labin* ("built with bricks"). Source: displayed entry Eml, id 581 (quoted above).
3. That note "shows the jurist in him". This rests on al-Ziriklī vol. 6 p. 55 ("وهو من فقهاء الحنفية"), already cited in the essay and verified as C16.
4. The bāb formula count now includes *min bāb* (522/877; al-Jawharī 0/866). Source: own count (above).
5. Citation additions, not new claims: `[^khatir-1916|preface, p. د]` for al-Rāzī keeping the last-letter order (quoted above); `[^razi-1999]` for the 1999 edition's first-letter order (Shamela TOC, above).

## Removed claims
- "al-Rāzī [quotes verse] in at most one in twenty [entries]". Replaced by "fewer than one in ten".
- "the source they name most often is al-Azharī (our count)". Cut to reduce the run of statistics; it was supported.
- "visited Egypt and Syria"; "a rare sixth class is stated case by case"; "our English versions do not always show the seam" (kept in `onOurSite`). Cut for length; all were supported.
- "The note shows what the book offers a Qur'an reader". Softened to "Notes like this show what the book can offer…".

## Disputed
None. I accepted all three qualifications.

## Not changed
- `summary`, `lede`, `onOurSite` and `period`, and all other sources.
- The site-data issue raised by the verifier still stands for whoever owns the database. The stored year 1268 is Ziriklī's "after 666 AH = after 1268", so it is a terminus post quem, not a death year.
