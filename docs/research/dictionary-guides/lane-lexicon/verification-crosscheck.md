# Lane's Lexicon: verification of the cross-check revision (round 99)

Verifier: independent fact-check of the changes listed for this revision only. I did not read
research-notes.md or revision-*.md. I opened the sources myself.

Guide file: roots/frontend/src/content/dictionary-guides/guides/lane-lexicon.ts

## Sources opened

- Lane, Preface, OCR of Internet Archive LAB1865AREN, file "Arabic-english lexicon by Lane E W (VOL. 1)_djvu.txt".
  Page headers in the OCR: "xvili PREFACE." at line 1041, "PREFACE. xix" at line 1093, "xx PREFACE" at line 1147.
- al-Zabīdī, *Tāj al-ʿArūs*, vol. 1 (Kuwait, 1965), OCR of Internet Archive ZUB1965AR, file
  "1 - تاج العروس_djvu.txt", and the item's archive.org metadata. The details page returns HTTP 200.
- The validator, run on the current file.

## Changed passages and new claims

### 1. "In Cairo he built on al-Zabīdī's *Tāj al-ʿArūs*, compiled there in the 1760s and 1770s,[lane-preface p. xviii][kuwait-ed] which he called 'the medium through which I have drawn most of the contents of my lexicon'.[lane-preface p. xix]"

- **Cairo, and the start.** SUPPORTED. On p. xviii (OCR lines 1075–1079), Lane says the Tāj "is said to have been commenced, in Cairo, soon after the middle of the last century", and that al-Zabīdī "states that it occupied him fourteen years and some days".
- **The 1760s–1770s dates.** SUPPORTED by kuwait-ed. Farrāj's introduction has a section "تأليف تاج العروس" (OCR lines 442–446). It says al-Zabīdī began about seven years after he came to Egypt, at the age of 29, which points to about 1174 AH (1760). The digits are garbled in the OCR, but the age and the arrival date fix the year. The introduction also lists dated letter-endings, ending "وآخر الكتاب فى رجب سنة 1188" (OCR line 1208). Rajab 1188 AH falls in September–October 1774. At lines 887–891 Farrāj argues that the 1181 AH banquet reported by al-Jabartī marked completion of the first part only.
- **A difference between the sources, recorded but not changed.** On the same page xviii, Lane quotes al-Jabartī for a finish in "A.D. 1767 or 1768". That is the banquet date Farrāj reinterprets. The guide follows the later edition's dating and does not attribute 1770s to Lane, so the citations are accurate. A reader who opens Lane p. xviii will still see the earlier date. That is a minor point in a Lane guide. The *Tāj* guide (taj-al-arus.ts) gives the same 1760s–1770s span, citing the Kuwait editor, so the two guides agree.
- **The quotation.** SUPPORTED verbatim. It is OCR line 1134, which falls on p. xix (lines 1093–1146): "As the Taj el-'Aroos is the medium through which I have drawn most of the contents of my lexicon".
- The link [[guide:taj-al-arus|…]] resolves; the slug is in registry.ts.

### 2. New source kuwait-ed

SUPPORTED.
- The archive.org metadata lists "المجلد 1 / عبد الستار فراج / 1965".
- The OCR has "مطبعة حكومة الكويت" (line 19) and the signature "كتبه: عبد الستار أحمد فراج" (lines 55 and 1377).
- The full title "تاج العروس من جواهر القاموس" and the author "مرتضى الزبيدي" are correct.
- The URL https://archive.org/details/ZUB1965AR returns 200.
- The citation's description (editor's introduction, the list of dated letter-endings, the last in Rajab 1188 AH / 1774) matches what I read.

### 3. "generally on the authority of the Asás" ([[guide:asas-al-balagha|al-Zamakhsharī's *Asās al-Balāgha*]])

SUPPORTED.
- The quoted words are on Lane's preface p. xxiv–xxv (OCR line 1476).
- Lane identifies the Asás as the work of Ez-Zamakhsheree at OCR lines 878, 1112 and 2497 (the table of authorities).
- The site's dictionary al-zamakhshari-asas-al-balagha maps to guide asas-al-balagha in registry.ts. The link validates.

### 4. Lede: "putting the medieval Arabic dictionaries into English"

SUPPORTED as a characterisation. The works Lane translates from are medieval: the Ṣiḥāḥ, Muḥkam, Asās, Lisān, Miṣbāḥ, Mughrib and Qāmūs. His main channel, the Tāj, is an 18th-century compilation of those works, and the summary already says he read them "mainly through the *Tāj al-ʿArūs*". The change removes the evaluative word "great". The citation after the sentence (Lane-Poole, for thirty-four years) was not changed, so I did not re-check it.

### 5. Heading renamed from "How to read an entry" to "Initials, daggers and brackets"

No broken references.
- Nothing in src/ or scripts/ points to the old heading. The only other "How to read an entry" is a heading inside asas-al-balagha.ts, which has nothing to do with this page.
- The section still covers initials, ‡/† and the ↓ arrow. Brackets are explained in the first section, and the excerpt discussion refers back to them.

## Validator

`node scripts/validate-dictionary-guides.mjs lane-lexicon`: **ok**
- 4 root links, 3 excerpts, example roots Swm, Hnf, qtl.
- 1,107 words in lede + body. That is 7 over the 1,100 guideline. There is no warning, and nothing is padded.

## Fixes made

None. Every changed passage and every new claim is supported.
