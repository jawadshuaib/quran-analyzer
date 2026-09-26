# Revision r1: gharib-al-quran-fi-shir-al-arab

Reviser's log (2026-09-26), responding to `verification-r1.md`.
File edited: `roots/frontend/src/content/dictionary-guides/guides/gharib-al-quran-fi-shir-al-arab.ts`. Research notes extended (§11).
Validator: `node scripts/validate-dictionary-guides.mjs gharib-al-quran-fi-shir-al-arab` passes with no ✗ errors and no warnings. It reports 7 root links, 4 excerpts and 1,099 words (lede + body). The count was 1,088 at verification; the additions were offset by trims.

## Flagged claims

### C30 (needs qualification): now fixed
- Before: "…rests on one Cairo manuscript and numbers 250 questions;[^ed1993|p. 20]"
- After: "…rests on one Cairo manuscript[^ed1993|p. 20] and numbers its questions to 250;[^ed1993|no. 250, p. 283]"
- Evidence: the Shamela contents list (https://shamela.ws/book/23622) runs from (١) to (٢٥٠). The last question, "(٢٥٠) خ ف ي [أخفيها]", is on page-id 273, whose `data-page-num` = 283. p. 20 is kept for the manuscript only: "…كما وردت في الأصل المخطوط المحفوظ في دار الكتب المصرية تحت رقم ١١٦ مجاميع م".
- Also changed: "which our copy follows" became "which our copy matches", to agree with the C54 qualification.

### C31 (needs qualification): locator kept at p. 7, URL added. See Disputed.
### C34 (needs qualification): locator kept at p. 5. See Disputed.
- The samarrai source now has a URL: https://archive.org/details/lis_ak87/lis_ak8709.pdf. The bare item page `lis_ak87` has no title and holds 16 unrelated PDFs, so I link the file itself. The citation now says: "Consulted in the Internet Archive scan (file lis_ak8709), whose printed page numbers are visible."

### C42 (needs qualification): now fixed
- Before: "The entry in Lisān al-ʿArab reports both readings of the verse and quotes the same line, glossed the other way"
- After: "The entry in Lisān al-ʿArab reports several readings of the verse, balance and hardship among them, and quotes the same line, glossed the other way"
- The verifier found that Lisān entry 16990 gives al-Farrāʾ's "منتصباً معتدلاً" (balance) and "وقيل: في شدّة ومشقة" (hardship) among five or more readings.

### C54 (needs qualification): now fixed
- Before: "Our text follows the 1993 Beirut edition, as reproduced on arabiclexicon.hawramani.com: the same wording and headings, without the editors' question numbers and footnotes.[^ed1993][^hawramani]"
- After: "Our text comes from arabiclexicon.hawramani.com, which does not name its source.[^hawramani] In every entry we compared, it matches the 1993 Beirut edition word for word, headings included, without the editors' question numbers and footnotes.[^ed1993]"
- Each citation now supports only its own sentence. The identification rests on collation:
  - Drafter: 12 entries (research notes §0).
  - Verifier: kbd, mrD, $wb, qbs.
  - Rechecked in this round against the Shamela pages: bwr (no. 169, p. 200), mrD second exchange (no. 224, p. 257), rkz (no. 177, p. 208) and $wb (no. 35, p. 64). All are identical apart from footnote markers.

## Brief issues (suggestions)

- **fwm "son of Umm al-Azraq"**: adopted. "Our copy leaves out the frame, so the unnamed قال ("he said") alternates between questioner and answerer (once, Ibn ʿAbbās calls the questioner "son of Umm al-Azraq")." The stored fwm text has "قال: يا ابن أم الأزرق" (entry 17535).
- **Numbers piling up / word ceiling**: adopted. I removed the al-Ṭabarānī count and the "left out a dozen or so" sentence, and dropped "in his mosque" and "at Jundīsābūr" from the chain sentence. I also tightened several phrases (see Changed).
- **Editors identify some "unnamed" poets**: adopted, with a more informative example than the verifier's. I checked the edition page for all 19 displayed exchanges that credit only الشاعر. The editors name the poet in 4 of them (research notes §11):
  - Umayya ibn Abī l-Ṣalt, p. 64 n. 2
  - Abū Zubayd al-Ṭāʾī, p. 184 n. 2
  - Dhū l-Rumma, p. 208 n. 2
  - ʿAdī ibn Zayd, p. 277 n. 2

  The guide uses Dhū l-Rumma, because his date matters for how a reader weighs the evidence. See New claims.
- **Older title in Wansbrough p. 218**: partly adopted. I confirmed the passage: "One title recorded for the collection otherwise known as Masāʾil Nāfiʿ b. Azraq is Kitāb gharīb al-Qurʾān" (footnote to Mittwoch, 'Ahlwardt No. 683', 341). To keep within the word limit, I did not add the Wansbrough sentence. Instead, "The name on our panel … is recent" now reads "The **full** name on our panel … is recent". That is exactly what the 1993 editors say they added (p. 20: "أضفنا إلى العنوان الرئيسي عنوانا جديدا … وهو: غريب القرآن في شعر العرب"), and it no longer implies that every part of the name is modern.
- **samarrai URL**: added (see above). Wansbrough is left unlinked.

## Changed (all edits)

1. Body ¶1: "The name on our panel" became "The full name on our panel".
2. Body ¶1: "Its two editors, publishing in Beirut in 1993, say they added it to the older title so that readers would grasp what the book is about." became "Its two editors (Beirut, 1993) say they added it to the older title to make the subject clear." This is a shorter paraphrase of p. 20 "كي يقع هذا العنوان على نظر القارئ ويتفهم المراد منه".
3. Body ¶2: the fwm parenthesis was added and "simply" was dropped.
4. Body, chain sentence: "in his mosque" and "at Jundīsābūr" were removed.
5. Body, routes paragraph:
   - "By the count of Bint al-Shāṭiʾ, who compared them, … only a handful" became "By Bint al-Shāṭiʾ's count, … a handful".
   - "al-Ṭabarānī thirty-one" was removed.
   - "Al-Suyūṭī says he left out a dozen or so.[^itqan|vol. 2, p. 105]" was removed.
   - C30 was fixed, and "follows" became "matches".
6. Body, kbd: the C42 fix. "the 1993 editors themselves gloss … in place of" became "the 1993 editors gloss … for". "One exchange gives you one early reading and one witness, and the witness can be read more than one way." became "One exchange gives one early reading and one witness, which can be read more than one way."
7. Body, "Using it well": a new sentence on the editors' poet identifications and Dhū l-Rumma, with a root link to rkz in this dictionary.
8. onOurSite: the C54 rewording.
9. sources.samarrai: the scan note and URL were added.

## Removed claims

- "al-Ṭabarānī thirty-one" (Bint al-Shāṭiʾ's count; C27). It was supported and was removed only to reduce the number of figures, as the verifier suggested.
- "Al-Suyūṭī says he left out a dozen or so" (Itqān 2:105; C29). It was supported and was removed for length.
- "in his mosque" and "at Jundīsābūr" (details of C21/C22). They were supported and were removed for length.
- "[^hawramani]" as support for the edition identification (C54). It is now cited only for the fact that the text comes from hawramani and that hawramani names no source.

## New claims

1. **"The 1993 editors name a few [of the unnamed poets], among them Dhū l-Rumma for the line on ر ك ز *rikz* (Q 19:98); he died in 117/735, nearly fifty years after Ibn ʿAbbās.[^ed1993|p. 208 n. 2]"**
   - Source: ed1993 no. 177, https://shamela.ws/book/23622/198 (`data-page-num` 208).
     - Text: "أما سمعت الشاعر «٢» وهو يقول: وقد توجّس ركزا مقفر ندس ... ينتابه الصّوت ما في سمعه كذب".
     - n. 1: "سورة مريم الآية: ٩٨".
     - n. 2: "الشاعر: ذو الرمة: وهو غيلان بن عقبة بن نهيس بن مسعود العدوي … توفي بأصبهان سنة (١١٧) هـ الموافق (٧٣٥) م".
   - Our displayed entry (rkz, entry 15840) credits only "الشاعر", with the same line, so it counts among the 19.
   - "A few": the editors name the poet in 4 of the 19 (list above; research notes §11).
   - "Nearly fifty years": 117 − 68 = 49 lunar years (735 − 687/8 = 47–48 solar years). Ibn ʿAbbās's death date is from ed1993 p. 12 n. 1, already cited in the guide.
   - Corroboration, in the notes only and not cited: al-Mubarrad, *al-Kāmil* (https://ablibrary.net/book_content/14124/92): "والنبأة الصوت، قال ذو الرمة: وقد توجس ركزا مقفر ندس * بنبأة الصوت ما في سمعه كذب". This means an early transmitter of some of the Masāʾil himself credits the line to Dhū l-Rumma.
   - The guide gives no birth date for Dhū l-Rumma and does not say the line is certainly his. It reports the editors' identification.
2. **"The 1993 edition … numbers its questions to 250 [^ed1993|no. 250, p. 283]"**. This restates C30 with a new locator. Evidence is under C30 above.
3. **"once, Ibn ʿAbbās calls the questioner 'son of Umm al-Azraq'"**. Source: the stored fwm entry, 17535: "قال: يا ابن أم الأزرق ومن قرأها على قراءة عبد الله بن مسعود (الثوم)…". A grep shows no other displayed entry with أم الأزرق. The verifier also noted that fwm is the one case.
4. **samarrai scan**: printed page numbers are visible (see Disputed).

## Disputed

### C31 / C34: the al-Sāmarrāʾī page numbers are correct as drafted (p. 7 and p. 5)

The verifier inferred p. 8 and p. 6 from OCR leaf numbering. I rendered the page images of the scan (https://archive.org/download/lis_ak87/lis_ak8709.pdf, image-only PDF, 107 pages) with `pdftoppm` and read the printed page-foot numerals directly:

| PDF page | printed page-foot numeral | content |
|---|---|---|
| 6 | "- ٥ -" (p. 5) | first page of المقدمة: "ذلك ان ابن عباس قد اعتمد فيها منهجا لم يسبق اليه وهو شرح ألفاظ القرآن والاستدلال عليها بما جاء في شعر العرب" |
| 7 | "- ٦ -" (p. 6) | "…الاصل المخطوط المحفوظ في دار الكتب المصرية ١١٦ مجاميع م …" |
| 8 | "- ٧ -" (p. 7) | first lines: "وتشغل هذه « المسائل » من المجموع جملة أوراق تقع بين الورقة ١٢٤ الى الورقة ١٤٤ • وهي بالقلم النسخي الجميل ويبدو أن خطها حديث وقد خلت من تاريخ يشير الى النسخ" |
| 9–16 | "- ٨ -" to "- ١٥ -" | consecutive, no gaps |

PDF page 1 is a blog advert; pages 2–5 are cover and logo leaves. The PDF page is therefore always printed page + 1, which explains the verifier's off-by-one reading of "leaf" numbers. The claims keep [^samarrai|p. 7] and [^samarrai|p. 5]. The next verifier can check this by opening the viewer URL now given in the source list and reading the page feet.

## Site-data issues (unchanged from r1, restated)

1. Author label "ʿAbdullāh ibn ʿAbbās" should read "attributed to ʿAbdullāh ibn ʿAbbās".
2. Stored date 687 is his death, not a date of the text. The recorded versions date from the late 9th to 10th c. CE.
3. The title is the 1993 editors' addition. The older name is *Masāʾil / Suʾālāt Nāfiʿ ibn al-Azraq*.
4. Misfiled entries:
   - خَبَتْ (Q 17:97) is on xbt; it belongs on xbw.
   - عَنَتِ (Q 20:111) is on Ent; it belongs on Enw.
   - سِنَةٌ (Q 2:255) is on snh; it belongs on wsn.
5. The nqb English cites Q 35:44; the correct reference is Q 50:36.
6. Some harmonized English calls the witnesses "pre-Islamic" (Amr, nqb). This round adds that the editors attribute the displayed rkz line to Dhū l-Rumma (d. 117/735). I checked the rkz harmonized English: it does not call the line pre-Islamic. No change is needed there, but the general "pre-Islamic" labels elsewhere should be reviewed.
