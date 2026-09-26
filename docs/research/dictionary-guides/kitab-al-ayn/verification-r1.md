# Kitāb al-ʿAyn: verification round 1 (independent fact-check)

Page checked: `roots/frontend/src/content/dictionary-guides/guides/kitab-al-ayn.ts`
Checked 2026-09-26. I did not open research-notes.md or any revision file. I opened every source and checked every claim against it myself.

## Evidence base (all opened in this round)

- **ayn-ed / ayn-intro**: Shamela book 1682 (https://shamela.ws/book/1682). The book card reads "المحقق: د مهدي المخزومي، د إبراهيم السامرائي؛ الناشر: دار ومكتبة الهلال؛ عدد الأجزاء: ٨؛ ترقيم الكتاب موافق للمطبوع". Pages read, with printed page numbers taken from each page title:
  - vol. 1: pp. 10–12 (Shamela ids 6–8), 16–19 (12–15), 26–27 (22–23), 31–34 (27–30), 43–44 (35–36), 47–52 (37–42) and 58–60 (48–50)
  - vol. 2: pp. 48–51 and 54–55 (ids 403–406 and 409–410)
  - vol. 5: pp. 341–342 (ids 1913–1914)
  - vol. 8: pp. 162–164 (ids 2933–2935)
- **muzhir**: Shamela book 6936. The card reads "تحقيق فؤاد علي منصور، دار الكتب العلمية، ١٤١٨هـ/١٩٩٨م". I read vol. 1, pp. 61–68 (ids 55–62).
- **maqayis-ed**: Shamela book 21710 (Hārūn, al-Bābī al-Ḥalabī, 2nd ed., 1969–72). I read vol. 1, pp. 3–5 (ids 47–49).
- **haywood**: archive.org item `in.gov.ignca.12555`. Its metadata reads "Arabic lexicography / Haywood, John A. / 1960". I read the full djvu text for pp. 25–27 (end of ch. 3 and start of ch. 4) and pp. 38–45 (ch. 4 and start of ch. 5).
- **hawramani**: https://arabiclexicon.hawramani.com/al-khalil-b-ahmad-al-farahidi-kitab-al-ain/ returns HTTP 200. The page names no printed edition. Its blurb credits al-Khalīl, and it says al-Layth "organized" the work.
- **Stored entries** (`_dict_guide_tool.py entry …`), all displayed: Ebd = 372, ESb = 9811, Zlm = 287, ktb = 21, Elm = 35 and Hrm = 1622 in Kitāb al-ʿAin, plus Zlm = 295 in Ibn Fāris. `root Eml` and `root rHm` list no Kitāb al-ʿAin entry.
- **Direct database counts** (same display filter as the tool):
  - 505 displayed entries in total.
  - 418 of the 505 begin with باب.
  - The blessing abbreviation ص after رسول الله/النبي appears in Ebd, kvr and hrb. The abbreviation ع appears in Elm, klm and qnTr.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Kitāb al-ʿAyn* / كتاب العين (title, titleAr) | S | Shamela card "الكتاب: كتاب العين". The editors' text uses كتاب العين throughout. |
| C2 | titleGloss: named after its first letter | S | Intro p. 47 (id 37): "فوجد العين ادخل الحروف في الحلق فجعلها أول الكتاب". |
| C3 | Author: al-Khalīl, as transmitted by al-Layth ibn al-Muẓaffar | S | Intro p. 48: "قال أبو معاذ عبد الله بن عائذ: حدثني الليث بن المظفر بن نصر بن سيار عن الخليل بجميع ما في هذا الكتاب". |
| C4 | authorFull: Abū ʿAbd al-Raḥmān al-Khalīl ibn Aḥmad al-Farāhīdī al-Baṣrī | S | Shamela card: "أبو عبد الرحمن الخليل بن أحمد بن عمرو بن تميم الفراهيدي البصري". |
| C5 | authorAr الخليل بن أحمد الفراهيدي | S | Same card. |
| C6 | Period: d. 170 or 175 AH / 786 or 791 CE | S | Muzhir vol. 1, p. 66: "توفي الخليل سنة سبعين ومائة وفي بعض الروايات سنة خمس وسبعين ومائة". The CE conversions are correct. |
| C7 | kind "Sound-ordered root dictionary" | S | Intro pp. 47–48 and 58 (letters ordered by makhraj). |
| C8 | summary: letters ordered by where they are sounded; each root filed with its rearrangements | S | Intro pp. 47–48 and 59. Haywood p. 38 ("roots are dealt with anagrammatically"). |
| C9 | summary: "Its entries set concrete usage beside Qur'anic readings and poetry" | NQ | Haywood p. 39 supports only "frequently quotes examples from religious literature and poetry" and the inclusion of everyday words. The qirāʾāt point rests on the Ebd entry alone. This generalises one entry to the whole work. |
| C10 | summary: who completed it is disputed | S | Muzhir vol. 1, pp. 62–67. |
| C11 | lede and §1: ʿayn "judged to come from deepest in the throat" | NQ | This matches the intro, p. 47 ("ادخل الحروف في الحلق") and p. 60 ("بالعين وهو أقصى الحروف"). But the same intro gives the hamza as "من أقصى الحلق" (p. 52) and places it "in the air" (p. 58). A report from Ibn Kaysān (in al-Suyūṭī, cited by the editors at vol. 1, p. 17) says al-Khalīl passed over hamza, alif and hāʾ and chose ʿayn as the "clearer" (أنصع) of the next pair. The editors (pp. 17–18) prefer that account and call the "furthest back" explanation "وهم محض". The guide presents only one account as if it were settled. |
| C12 | lede: files each root with every rearrangement found in use | S | Intro p. 59: "يُكتب مستعملها ويُلغى مهملها". Haywood p. 38. |
| C13 | lede: oldest surviving attempt to take in the whole vocabulary by a system | S | ayn-ed vol. 1, p. 18: "والعين بهذا أول معجم في العربية ولعله معجم موعب". Haywood p. 39 ("the first Arabic dictionary"; "planned to include all roots") and p. 43 ("the first exhaustive vocabulary"). |
| C14 | lede: the voices of al-Khalīl, al-Layth and later hands | S | Intro pp. 48, 50 and 52. Muzhir vol. 1, pp. 63 and 66 (later additions in copies). |
| C15 | §1: could not open with alif, a weak letter; "tasted" the letters (ab, at, aḥ, aʿ, agh); worked outward to mīm | S | Intro p. 47, nearly verbatim. Haywood pp. 27–28 translates the same passage. |
| C16 | §1: within each book, roots sorted doubled / sound triliteral / weak / quadriliteral and quinqueliteral | S | ayn-ed vol. 1, p. 16 lists six categories, including *lafīf*. Haywood p. 38. The guide's "weak" silently includes *lafīf*, which is acceptable. |
| C17 | §1: 6 / 24 / 120 arrangements; "the used are written down and the unused discarded" | S | Intro p. 59. The quoted words are said of the 24 quadriliteral arrangements; the guide's "of such arrangements" is a fair generalisation. |
| C18 | §1: a word is filed under its earliest letter in the order | S | Intro p. 47: "فمهما وجدت منها واحداً في الكتاب المقدم فهو في ذلك الكتاب". |
| C19 | §1: the intro never claims rearranged roots share a meaning (labelled as the author's reading) | S | Intro pp. 47–60 contain no such claim. Haywood p. 39 calls that idea a later "false idea". |
| C20 | §1 quotation بدأنا في مؤلفنا هذا بالعين… and its translation | S | Intro p. 60: "وقال الخليل: بَدَأَنَا في مُؤلَّفنا هذا بالعين وهو أقصَى الحروف، ونضُمُّ إليه ما بعده حتى نَسْتَوْعِبَ كلام العرب الواضحَ والغريب". The ellipsis is correct and the translation is fair. |
| C21 | §2: the intro opens "This is what al-Khalīl ibn Aḥmad of Basra composed" | S | Intro p. 47: "هذا ما ألفه الخليل بن أحمد البصريّ". |
| C22 | §2: chain Abū Muʿādh ʿAbdallāh ibn ʿĀʾidh ← al-Layth, "from al-Khalīl, everything in this book" | S | Intro p. 48. |
| C23 | §2: statements framed "al-Layth said: al-Khalīl said"; al-Layth speaks as "I" | S | Intro p. 48 ("قال الليث: قال الخليل"), p. 50 ("قال ليث: قلت لأبي الدقيش"), p. 52 ("قال الليث: قلت") and pp. 58–59. |
| C24 | §2: ESb excerpt and its translation, in the chapter filed under ع ص ب | S | Entry 9811, ṣ-b-ʿ section, verbatim. It is also rendered in the site's English. |
| C25 | §2: authorship argued since the 9th century | S | Muzhir vol. 1, pp. 66–67 (Abū Ḥātim, d. 255, c. 250 AH). |
| C26 | al-Suyūṭī d. 911 AH / 1505 CE | S | Shamela card for book 6936: "(ت ٩١١هـ)". |
| C27 | al-Azharī: al-Layth wrote it and put al-Khalīl's name on it so that it would sell | S | Muzhir vol. 1, p. 62: "عمل كتاب العين ونسبه إلى الخليل لينفق كتابه باسمه ويرغب فيه". |
| C28 | Others: al-Khalīl wrote up to *ghayn* and al-Layth completed it | S | Muzhir vol. 1, p. 62: "قال بعضهم: عمل الخليل من كتاب العين قطعة من أوله إلى حرف الغين وكمله الليث". |
| C29 | al-Zubaydī, the abridger: al-Khalīl laid the foundation and died before completing it | S | Muzhir vol. 1, p. 64 ("مؤلف مختصر العين") and p. 65 ("أن الخليل سبب أصله … ثم هلك قبل كماله"). |
| C30 | Arrived from Khurāsān c. 250 AH; Abū Ḥātim rejected it because al-Khalīl's students had not heard of it | S | Muzhir vol. 1, pp. 66–67. This is al-Qālī's report, quoted by al-Zubaydī. The guide's "it was argued" is acceptable. |
| C31 | Modern editors: in design and substance the book is al-Khalīl's | S | ayn-ed vol. 1, p. 27: "أن كتاب العين بتأسيسه وبحشوه … إنما هو كتاب الخليل". |
| C32 | Haywood: "will probably never be convincingly solved"; credits al-Khalīl with at least the plan | S | Haywood p. 26 ("…we must credit him with a major share at least in the planning"). |
| C33 | al-Suyūṭī read al-Zubaydī's list: arrangement, word-formation and alleged miscopying, not the genuineness of words; no bar to relying on it | S | Muzhir vol. 1, p. 68. |
| C34 | §2 advice: read unattributed text as the ʿAyn as transmitted, and "al-Khalīl said" as a quotation within it | NQ | Muzhir vol. 1, p. 63 reports (Isḥāq ibn Rāhawayh via a Khurāsānī) that al-Layth "سمّى لسانه الخليل": an unqualified "قال الخليل" would be al-Layth speaking of himself, and "قال الخليل بن أحمد" would be al-Khalīl. Haywood p. 27 calls "qāla l-Khalīl" "slightly ambiguous". The advice is reasonable, but it hides a live dispute about exactly this formula. |
| C35 | Ebd chapter heading excerpt and translation | S | Entry 372 = ayn-ed vol. 2, p. 48, verbatim. |
| C36 | "So this entry also holds baʿd and bidʿa" | NQ | This is true of the stored Arabic (entry 372 contains the d-ʿ-b, b-ʿ-d and b-d-ʿ sections). But both English views on the site (the faithful translation and the default harmonized English) stop at *al-ʿabādīd* and omit those three sections. A reader following the link will find *baʿd* and *bidʿa* only under "Original Text". |
| C37 | ʿabd excerpt and translation | NQ | The words are copied correctly. But the ellipsis after عبيد drops "وثلاثة أعبد، وهم العباد أيضاً" ("and they are also [called] al-ʿibād"). That qualifies the next sentence: the entry says owned slaves are also called *ʿibād* before saying common usage keeps the two apart. |
| C38 | ʿabada/yaʿbudu/ʿibāda "said only of one who worships God"; one does not say *ʿabadahu* of a slave | S | Entry 372; ayn-ed vol. 2, p. 48. |
| C39 | *wa-ʿabada l-ṭāghūt* (Q 5:60) "is read in seven ways", each parsed | S | Entry 372; ayn-ed vol. 2, p. 49. The entry says only "هذه الآية"; the guide's identification as Q 5:60 is correct. |
| C40 | Observation: in Q 5:60 the object is al-ṭāghūt, not God (labelled) | S | The entry's own gloss reads "عَبَدَ الطّاغوتَ من دون الله". |
| C41 | ʿabad ("disdain") excerpt and translation | S | Entry 372; ayn-ed vol. 2, p. 50. |
| C42 | Q 43:81 read through "disdain"; a second explanation given without a choice | S | Entry 372 ("ويقال: … فلست بأول من عبد الله من أهل مكة"). Editors' fn 6 identifies Q 43:81. |
| C43 | A saying of "the Commander of the Faithful" and a verse whose poet the editors could not identify | S | ayn-ed vol. 2, p. 50, fn 7: "لم نهتد إلى القائل، ولم تفدنا المراجع في القول شيئا". |
| C44 | bidʿa: two definitions; excerpt; ص abbreviates the blessing | S | ayn-ed vol. 2, p. 54 ("اسم ما ابتدع من الدين وغيره") and p. 55 ("ما استحدثت بعد رسول الله ص من أهواء وأعمال"). |
| C45 | The second bidʿa definition is by its own terms later than the Qur'an | S | Its wording, "بعد رسول الله". |
| C46 | The chapter gathers rather than theorises; no single meaning from which the rest derive (with the caveat that one chapter illustrates) | S | Entry 372 read in full. |
| C47 | It judges the common reading of Q 2:117 "more correct" | S | ayn-ed vol. 2, p. 55: "وقراءة العامة الرفع [وهو] أولى بالصواب". Editors' fn 27 identifies البقرة ١١٧. |
| C48 | ẓ-l-m runs from "*ẓalam*, the first dark", through snow, the gleam of teeth and the male ostrich, to wrongdoing | NQ | The order and senses are correct (entry 287; vol. 8, pp. 162–163). But the ʿAyn does not say "dark". It glosses *awwal dhī ẓalam* as "the first thing that blocks your sight in seeing", and no verb is derived from it. Calling it "the first dark" imports an interpretation. Ibn Fāris, by contrast, explains it as a figure likened to darkness. |
| C49 | Zlm excerpt and translation | S | Entry 287 = vol. 8, p. 163, verbatim with valid ellipses. |
| C50 | The entry ends with "ẓulm is shirk" citing Q 31:13, and never says how the senses hang together | S | Vol. 8, p. 164 (fn 47: لقمان ١٣). This is the end of the ẓ-l-m section; l-m-ẓ follows. |
| C51 | Ibn Fāris names the ʿAyn first among the five books the *Maqāyīs* is built on | S | Maqāyīs vol. 1, pp. 3–5: "فأعلاها وأشرفها كتاب … الخليل … المسمى كتاب العين … فهذه الكتب الخمسة معتمدنا". |
| C52 | Ibn Fāris quotes al-Khalīl; his excerpt and its translation | S | Entry 295, verbatim ("وَمِنْ هَذَا الْبَابِ مَا حَكَاهُ الْخَلِيلُ"). |
| C53 | Ibn Fāris files the dug ground and the slaughtered camel under his second root | S | Entry 295 ("والأصل الآخر … والأرض المظلومة … وإذا نحر البعير من غير علة فقد ظلم"). |
| C54 | The darkness sense is bracketed because the editors restored it from al-Azharī's *Tahdhīb*, which quotes the ʿAyn | S | Vol. 8, p. 163, fn 43: "ما بين القوسين من التهذيب من أصل العين". |
| C55 | Observation: "ẓulm is shirk" turns a verse into a definition (labelled) | S | Entry text and Q 31:13. This is interpretation, and it is labelled as such. |
| C56 | §5: "sets concrete, everyday uses beside Qur'anic citations, readings and poetry" [haywood p. 39] | NQ | Haywood p. 39 supports "did not invariably … omit common words … familiar in everyday speech" and "frequently quotes examples from religious literature and poetry". It says nothing about qirāʾāt or "concrete" uses. The citation supports only part of the claim. |
| C57 | Copies circulated with additions; al-Zubaydī found some citing Abū ʿUbayd, who was 16 or 21 when al-Khalīl died | S | Muzhir vol. 1, p. 66. |
| C58 | Our text rests on much later manuscripts | S | ayn-ed vol. 1, pp. 31–34 (1054, 1087 and c. 1350 AH). |
| C59 | *ʿamal* is inside ع ل م and *raḥma* inside ح ر م | NQ | The stored Arabic of Elm (35) has "عمل:" and of Hrm (1622) has "رحم:". Elm's English covers ʿamal. Hrm's English does not cover raḥma: the harmonized text says "this digest covers the ḥ-r-m section only". The reader must open "Original Text" to find raḥma. |
| C60 | The root pages ع م ل and ر ح م show no Kitāb al-ʿAyn entry | S | `root Eml` and `root rHm` list no al-khalil entry. |
| C61 | Each chapter is stored under the root that opens it | S | This holds for Ebd, Elm, Hrm, ESb, Zlm and ktb: the stored root is the first arrangement in each heading. |
| C62 | onOurSite: the stored text matches the al-Makhzūmī–al-Sāmarrāʾī edition word for word in Ebd, Zlm and ktb | S | Compared against vol. 2, pp. 48–55; vol. 8, pp. 162–164; and vol. 5, pp. 341–342. The only differences are footnote markers and some heading brackets (see C68). |
| C63 | arabiclexicon.hawramani.com does not name its source | S | The dictionary page (HTTP 200) names no edition. |
| C64 | Three late manuscripts; the oldest copied 1054 AH (1644–5 CE) | S | ayn-ed vol. 1, pp. 31–34 (the Ṣadr MS "١٠٥٤", Tehran 1087, al-Samāwī 1350s AH). The editors also used partial prints (K, 1913; M, 1967) per p. 44. |
| C65 | The editors reordered entries within chapters | S | ayn-ed vol. 1, pp. 43–44, item 6: "فأرجعناها إلى الترتيب الأصيل". |
| C66 | Square brackets mark the editors' additions, some from the *Tahdhīb* | S | p. 44, item 7 ("ما اقتضى السياق زيادته بين معقوفتين"). The *Tahdhīb* sources are in footnotes, e.g. vol. 8, p. 163, fnn 43–46, and vol. 5, p. 341, fn 2. |
| C67 | The footnotes are not shown | S | The stored texts contain no footnotes. |
| C68 | Some chapter headings the editors supplied appear without brackets [cited ayn-ed vol. 1, p. 44] | NQ | This is true: the ktb heading is printed "[باب الكاف والتاء والباء …]" in vol. 5, p. 341 but stored without brackets. But p. 44 does not say this. Cite vol. 5, p. 341 instead. |
| C69 | 505 entries displayed | S | `dicts`: "displayed entries=505". |
| C70 | Most entries are whole chapters headed by "in use" / "unused" lists | S | 418 of 505 stored entries begin with باب. Haywood p. 38. |
| C71 | One entry can cover several roots, while many roots have no entry | S | Ebd, Hrm and Elm cover several roots; Eml and rHm have none. |
| C72 | ص or ع occasionally abbreviates a blessing formula | S | ص in Ebd, kvr and hrb; ع in Elm, klm and qnTr. |

**Totals: 72 claims. 63 supported, 9 need qualification, 0 unsupported.**

## Flagged items and fixes

1. **C11 (why ʿayn comes first).** Keep the introduction's account, but attribute it and add the competing one. For example, after the §1 tasting sentence: "That is the introduction's own account. Another report, from Ibn Kaysān (preserved by al-Suyūṭī), has al-Khalīl pass over hamza, alif and hāʾ and choose ʿayn as the 'clearer' letter. The modern editors prefer it, since the introduction itself places the hamza furthest back [^ayn-ed|vol. 1, pp. 17–18]." In the lede, change "the sound its compiler judged to come from deepest in the throat" to "the sound the introduction places deepest in the throat".
2. **C34 (reading "al-Khalīl said").** Add one sentence with a citation: "Even this formula is disputed: one early report held that al-Layth called himself 'al-Khalīl', so that an unqualified *qāla l-Khalīl* would be al-Layth speaking [^muzhir|vol. 1, p. 63], and Haywood calls the phrase 'slightly ambiguous' [^haywood|p. 27]." Then soften the advice to "treat 'al-Khalīl said' as the book's attribution to al-Khalīl".
3. **C36 (baʿd and bidʿa).** Add "(in the Original Text: the site's English versions of this entry cover only the ʿ-b-d section)". Otherwise the bidʿa excerpts point readers to material the default English view does not show.
4. **C59 (raḥma inside ح ر م).** Add "…inside ح ر م, where it appears in the Original Text only: the English digest covers the ḥ-r-m section alone". Alternatively, choose another pair whose English includes the embedded root; ʿamal inside Elm does.
5. **C37 (ʿabd excerpt).** Restore the dropped words: "…وجمعه: عَبِيد، وثلاثة أعْبُد، وهم العباد أيضاً. إنّ العامّة…". Translate: "…its plural is ʿabīd, and 'three aʿbud'; and they too are called ʿibād. People in general agree…". This keeps the entry's own concession visible.
6. **C48 ("the first dark").** Change "*ẓalam*, the first dark" to "*ẓalam* ('the first thing that blocks your sight', as in 'I met him at the first *ẓalam*')". Or keep "dark" but mark it as the guide's interpretation.
7. **C56 (Haywood p. 39).** Either narrow the wording to what Haywood says ("everyday words beside examples from religious literature and poetry"[^haywood|p. 39]), or cite the Ebd entry (vol. 2, pp. 49–50) separately for Qur'anic readings.
8. **C9 (summary).** Change "Its entries set concrete usage beside Qur'anic readings and poetry" to "Its entries set everyday words beside Qur'anic citations and poetry". Do not generalise *qirāʾāt* from a single entry.
9. **C68 (unbracketed headings).** Replace the locator for this clause with `[^ayn-ed|vol. 5, p. 341]`. For example: "some chapter headings the editors supplied, such as that of ك ت ب, appear without their brackets". Keep vol. 1, p. 44 for the brackets convention.

## Brief (non-factual) issues

- **must-fix.** The essay's pointers to *baʿd*, *bidʿa* (Ebd) and *raḥma* (Hrm) lead readers to material missing from the site's default English view. The brief says not to promise material that is not shown. Say "Original Text" explicitly (see flags 3 and 4).
- **suggestion.** The first person ("As I read the introduction", "(my observation)" twice) sits oddly in a site essay. Use "this guide's reading" or "(our observation)" so the labelling is kept but the voice matches the other guides.
- **suggestion.** The Haywood source citation says "chs 3–4", but p. 43 is in ch. 5 (ch. 5 begins on p. 40). Change it to "chs 3–5".
- **suggestion.** The word count is 1,100, the ceiling. Any additions from flags 1–4 should be offset by trimming, e.g. the list of senses in §4's opening sentence or the repeated "one chapter illustrates a method" caveat.
- **suggestion.** onOurSite could say in one clause that on multi-root chapters the English digest may cover only the headword root, so readers know to open the Original Text.
- There is no generic praise or ranking. The Ibn Fāris comparison is well supported and linked in both dictionaries. Every root mention is linked. The translations are labelled.

## Source URLs

All six open and point to the stated works:

- `ayn-ed`: https://shamela.ws/book/1682. The card matches the al-Makhzūmī–al-Sāmarrāʾī edition, Dār wa-Maktabat al-Hilāl, 8 vols, with printed page numbering. It gives no publication year, and the guide's citation gives none either (correct).
- `ayn-intro`: https://shamela.ws/book/1682/37 opens at vol. 1, p. 47 [مقدمة الكتاب].
- `muzhir`: https://shamela.ws/book/6936/55 opens at vol. 1, p. 61. The edition details match the card.
- `maqayis-ed`: https://shamela.ws/book/21710/47 opens at vol. 1, p. 3 (author's preface).
- `haywood`: https://archive.org/details/in.gov.ignca.12555. The metadata says Haywood, *Arabic lexicography*, 1960. Pages 26, 27, 38, 39 and 43 were read.
- `hawramani`: the dictionary landing page, HTTP 200.

Every source was consulted, and none is unused.

## Validator

`node scripts/validate-dictionary-guides.mjs kitab-al-ayn` → **ok, 1/1 guides pass**. It reports 11 root links, 7 excerpts and 1,100 words, and two expected warnings for `[[root:Eml|none|…]]` and `[[root:rHm|none|…]]`. The sentence explains both warnings ("show no Kitāb al-ʿAyn entry of their own").

## Site-data issues (report only; not edited)

1. **English renderings of multi-root chapters cover only the headword root.**
   - Entry 372 (Ebd): the faithful translation and the harmonized English end at *al-ʿabādīd* and omit the d-ʿ-b, b-ʿ-d and b-d-ʿ sections, which are in the stored Arabic. The harmonized text does not say it is partial.
   - Entry 1622 (Hrm): the harmonized English says "this digest covers the ḥ-r-m section only". The r-ḥ-m, ḥ-m-r and other sections are Arabic-only.
   - Entry 35 (Elm) does cover ʿamal, so the behaviour is inconsistent. I have not measured how widespread it is.
2. **The harmonized English attributes content directly to al-Khalīl** (e.g. Ebd: "Al-Khalīl notes…", "Al-Khalīl reads Q 43:81…"; Zlm: "al-Khalīl equates ẓulm with shirk"). Authorship and the reference of "qāla l-Khalīl" are disputed (Muzhir vol. 1, pp. 62–67; Haywood pp. 26–27). A neutral "the *ʿAyn* …" would be safer.
3. **Title spelling.** The stored title is "Kitāb al-ʿAin", following hawramani. The guide uses the standard "al-ʿAyn", and the harmonized texts mix the two. Consider aligning the site label to *al-ʿAyn*.
4. **Stored date 786.** This corresponds to 170 AH, one of two reported death dates (175 AH / 791 CE is the other; Muzhir vol. 1, p. 66). It is acceptable for ordering, but it is not the only date.
5. **The stored text drops the editors' footnote markers and footnotes, and some heading brackets** (e.g. ktb: "[باب الكاف والتاء والباء …]" in print, vol. 5, p. 341, is unbracketed in storage). The guide already discloses this.
