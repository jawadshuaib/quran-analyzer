# Kitāb al-ʿAyn: verification round 2 (independent fact-check)

Page checked: `roots/frontend/src/content/dictionary-guides/guides/kitab-al-ayn.ts` (the version after revision r1).
Checked 2026-09-26. I did not open research-notes.md or any revision-*.md file. I read verification-r1.md only for the list of earlier flags. I re-fetched every source myself and did not rely on round 1's readings.

## Evidence base (all opened in this round)

- **ayn-ed / ayn-intro**: Shamela book 1682. The card reads "المحقق: د مهدي المخزومي، د إبراهيم السامرائي؛ الناشر: دار ومكتبة الهلال؛ عدد الأجزاء: ٨؛ ترقيم الكتاب موافق للمطبوع". Printed page numbers come from each page title. Pages read:
  - vol. 1: pp. 16–18 (ids 12–14), 27 (23), 31–34 (27–30), 43–44 (35–36) and 47–60 (37–50), i.e. the whole introduction
  - vol. 2: pp. 48–55 (403–410)
  - vol. 5: pp. 341–342 (1913–1914)
  - vol. 8: pp. 162–164 (2933–2935)
- **muzhir**: Shamela book 6936. The card reads "فؤاد علي منصور؛ دار الكتب العلمية - بيروت؛ الأولى ١٤١٨هـ/١٩٩٨م؛ ٢ أجزاء". I read vol. 1, pp. 50–82 (ids 44–76), which covers the whole cited range, pp. 61–68.
- **maqayis-ed**: Shamela book 21710. The card reads "هارون؛ مصطفى البابي الحلبي؛ الثانية ١٩٦٩–١٩٧٢؛ ٦ أجزاء". I read vol. 1, pp. 3–5 (ids 47–49).
- **haywood**: archive.org `in.gov.ignca.12555`. The metadata reads "Arabic lexicography / Haywood, John A. / 1960", and the title page reads "…in the General History of Lexicography … Leiden, E. J. Brill". I read the djvu text for pp. 26–27 and 38–43.
- **hawramani**: https://arabiclexicon.hawramani.com/al-khalil-b-ahmad-al-farahidi-kitab-al-ain/ returns HTTP 200. The page names no printed edition. Its blurb says al-Layth "organized" the work.
- **Stored entries**, from `_dict_guide_tool.py entry` and `/api/dictionary-entry/<id>`:
  - Kitāb al-ʿAin: Ebd = 372, ESb = 9811, Zlm = 287, ktb = 21, Elm = 35, Hrm = 1622, all displayed
  - Ibn Fāris: Zlm = 295
  - `root Eml` and `root rHm` list no al-khalil entry
- **Machine diff.** I normalised both texts (vowel marks, hamza forms and punctuation stripped) and compared the stored Ebd, Zlm and ktb against the printed text on the pages above. There were **no deletions or substitutions on the stored side**. The only printed-side extras are footnote text and the neighbouring chapters on the same pages.
- **Direct database counts** (same display filter as the tool):
  - 505 displayed entries.
  - 418 begin with باب, and 416 carry مستعمل/يستعمل in their heading.
  - The blessing abbreviation ص appears after رسول الله/النبي in Ebd, kvr and hrb; ع appears after النبي in klm.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Kitāb al-ʿAyn* / كتاب العين | S | Shamela 1682 card "الكتاب: كتاب العين". |
| C2 | titleGloss: named after its first letter | S | ayn-intro p. 47 (id 37): "فوجد العين ادخل الحروف في الحلق فجعلها أول الكتاب". |
| C3 | author: al-Khalīl, as transmitted by al-Layth ibn al-Muẓaffar | S | ayn-intro p. 48: "حدثني الليث بن المظفر بن نصر بن سيار عن الخليل بجميع ما في هذا الكتاب". |
| C4 | authorFull: Abū ʿAbd al-Raḥmān al-Khalīl ibn Aḥmad al-Farāhīdī al-Baṣrī | S | Shamela card: "أبو عبد الرحمن الخليل بن أحمد بن عمرو بن تميم الفراهيدي البصري". |
| C5 | authorAr الخليل بن أحمد الفراهيدي | S | Same card. |
| C6 | period: d. 170 or 175 AH / 786 or 791 CE | S | Muzhir vol. 1, p. 66: "تُوفِّيَ الخليل سنة سبعين ومائة وفي بعض الروايات سنة خمس وسبعين ومائة". The conversions are correct. |
| C7 | kind "Sound-ordered root dictionary" | S | ayn-intro pp. 47–48 and 58. |
| C8 | summary: letters ordered by where they are sounded; each root filed with its rearrangements | S | ayn-intro pp. 47–48 and 59. Haywood p. 38 ("roots are dealt with anagrammatically"). |
| C9 | summary: entries set everyday words beside Qur'anic citations and poetry | S | Haywood p. 39: "did not invariably … omit common words which were familiar in everyday speech … frequently quotes examples from religious literature and poetry". Qur'anic citations appear in Ebd, Zlm, Elm and Hrm. |
| C10 | summary: who completed it is disputed | S | Muzhir vol. 1, pp. 62–67. |
| C11 | lede: starts with ʿayn, "the sound its introduction places deepest in the throat" | S | ayn-intro p. 47 ("ادخل الحروف في الحلق") and p. 60 ("بالعين وهو أقصى الحروف"). It is now attributed to the introduction, and the counter-evidence is given in §1 (C16, C17). |
| C12 | lede: each root filed with every rearrangement found in use | S | ayn-intro p. 59: "يُكتب مستعملها ويُلغى مهملها". Haywood p. 38. |
| C13 | lede: oldest surviving attempt to take in the whole vocabulary by a system | S | ayn-ed vol. 1, p. 18: "والعين بهذا أول معجم في العربية ولعله معجم موعب". Haywood p. 39 ("the first Arabic dictionary") and p. 43 ("the first exhaustive vocabulary"). The introduction states the aim itself, "حتى نستوعب كلام العرب" (p. 60). |
| C14 | lede: voices of al-Khalīl, al-Layth and later hands | S | ayn-intro pp. 48, 50 and 52. Muzhir vol. 1, p. 63 (Thaʿlab: "حشا الكتاب قومٌ علماء") and p. 66. |
| C15 | §1: alif is a weak letter; the compiler "tasted" the letters (ab, at, aḥ, aʿ, agh); ʿayn is deepest; it is made the first book; the order works outward to mīm | S | ayn-intro p. 47, nearly verbatim ("الأرفع فالأرفع حتى أتى على آخرها وهو الميم"). Haywood p. 27 translates the same passage. |
| C16 | §1 (new): the same introduction puts hamza "at the far end of the throat" | S | ayn-intro p. 52 (id 42): "وأمّا الهَمْزة فَمَخْرَجُها من أقصَى الحَلْق مَهْتُوتة مضغوطَة". Page confirmed. |
| C17 | §1 (new): Ibn Kaysān's report has al-Khalīl pass over hamza, alif and hāʾ and prefer ʿayn to ḥāʾ as the "clearer" letter; the modern editors favour this account | S | ayn-ed vol. 1, p. 17 (id 13): "قال ابن كيسان فيما حكى السيوطي: سمعت من يذكر عن الخليل انه قال: لم أبدأ بالهمزة … ولا بالالف … ولا بالهاء … فنزلت إلى الحيز الثاني وفيه العين والحاء فوجدت العين أنصع الحرفين فابتدأت به". The editors' own view on p. 17 is "وكان قد بدأ بالعين، لا لانها أول الحروف مخرجا، ولكنها أول الحروف نصاعة". On p. 18 they rely on "ما قدمناه من بيان، ومن نقل عن ابن كيسان". The guide's "a report passed on by Ibn Kaysān" is accurate: Ibn Kaysān himself heard it from an unnamed informant. The editors cite Muzhir 1/90 in another edition; I did not find the report in the 1998 edition's pp. 50–82, but the guide cites the editors, not the Muzhir, for it. |
| C18 | §1: within each book, roots sorted doubled / sound triliteral / weak / quadriliteral and quinqueliteral | S | ayn-ed vol. 1, p. 16 lists six classes; the guide's "weak" includes *lafīf*. Haywood p. 38. |
| C19 | §1: 6 / 24 / 120 arrangements; "the used are written down and the unused discarded" (labelled translation) | S | ayn-intro p. 59. |
| C20 | §1: a word is filed under its earliest letter in the order | S | ayn-intro p. 47: "فمهما وجدت منها واحداً في الكتاب المقدم فهو في ذلك الكتاب". |
| C21 | §1 (labelled as this guide's reading): the rearrangements are a check that nothing is missed; the introduction never claims rearranged roots share a meaning | S | I read intro pp. 47–60 in full and found no such claim. Haywood p. 39 calls the shared-meaning idea a later "false idea". The "check" reading fits p. 47 ("فلا يخرج منها عنه شيء") and is labelled as interpretation. |
| C22 | §1 quotation بدأنا في مؤلفنا هذا بالعين … and its translation | S | ayn-intro p. 60: "وقال الخليل: بَدَأَنَا في مُؤلَّفنا هذا بالعين وهو أقصَى الحروف، ونضُمُّ إليه ما بعده حتى نَسْتَوْعِبَ كلام العرب الواضحَ والغريب". The ellipsis is valid and the translation fair. "A statement credited to al-Khalīl" matches "وقال الخليل". |
| C23 | §2: "This is what al-Khalīl ibn Aḥmad of Basra composed" | S | ayn-intro p. 47: "هذا ما ألفه الخليل بن أحمد البصريّ". |
| C24 | §2: al-Layth passes on "from al-Khalīl, everything in this book" | S | ayn-intro p. 48. |
| C25 | §2: statements framed "al-Layth said: al-Khalīl said"; al-Layth speaks as "I" | S | ayn-intro p. 48 ("قال اللَّيث: قال الخليلُ"), p. 50 ("قال ليث: قلت لأبي الدقيش"), p. 52 ("قال الليث: قلت") and pp. 58–59. |
| C26 | §2: ESb excerpt and translation, in the chapter filed under ع ص ب | S | Entry 9811 (ṣ-b-ʿ section of the ع ص ب chapter), verbatim. The site's English also carries it. |
| C27 | Authorship argued since the 9th century | S | Muzhir vol. 1, pp. 63 and 66–67 (Isḥāq ibn Rāhawayh; Abū Ḥātim c. 250 AH). |
| C28 | al-Suyūṭī d. 911 AH / 1505 CE | S | Shamela 6936 card "(ت ٩١١هـ)". |
| C29 | al-Azharī: al-Layth wrote it and put al-Khalīl's name on it so that it would sell | S | Muzhir vol. 1, p. 62: "عمِل كتاب العين ونسبَه إلى الخليل لينفق كتابه باسمه ويرغب فيه". |
| C30 | Others: al-Khalīl wrote as far as *ghayn* and al-Layth finished it | S | Muzhir vol. 1, p. 62: "عَمِلَ الخليلُ من كتاب العين قطعة من أوَّله إلى حرف الغين وكَمَّله الليث". |
| C31 | al-Zubaydī, the abridger: al-Khalīl laid the foundation and died before completing it | S | Muzhir vol. 1, p. 64 ("مؤلف مختصر العين") and p. 65 ("أن الخليل سَبَّب أصله وثقَّف كلام العرب ثم هلَك قبل كَماله"). |
| C32 | Arrived from Khurāsān c. 250 AH; Abū Ḥātim al-Sijistānī rejected it; al-Khalīl's students had never heard of it ("it was argued") | S | Muzhir vol. 1, pp. 66–67 (al-Qālī via al-Zubaydī: "لما وَرَدَ كتابُ العَين من بلد خُراسان في زمن أبي حاتم أنكره"; "فيما قارب الخمسين والمائتين"). The Muzhir says only "Abū Ḥātim"; his death date there, 255, fits al-Sijistānī. |
| C33 | Modern editors: in design and substance the book is al-Khalīl's | S | ayn-ed vol. 1, p. 27: "أن كتاب العين بتأسيسه وبحشوه … إنما هو كتاب الخليل". |
| C34 | Haywood: the question "will probably never be convincingly solved" | S | Haywood p. 26, verbatim. |
| C35 | Haywood credits al-Khalīl "with at least the plan" | **NQ** | Haywood p. 26 says "a major share at least in the planning". In the same paragraph he doubts that the phonetic ideas behind the letter order were al-Khalīl's own ("it is too much to believe that his phonetic ideas were his own"). "At least the plan" gives al-Khalīl more than Haywood does. |
| C36 | al-Suyūṭī: al-Zubaydī's errors concern arrangement, word-formation and alleged miscopying, never whether a word is genuine; no bar to relying on it | S | Muzhir vol. 1, p. 68: "غالبُه من جهة التصريف والاشتقاق … وبعضُه ادعى فيه التصحيف وأما أنه يُخَطأ في لفظة من حيث اللغة … فمعاذَ الله لم يقع ذلك … راجعٌ إلى الترتيب والوضْع … لا يمنعُ الوثوقَ بالكتاب". |
| C37 | Advice: read unattributed text as the ʿAyn as transmitted, and "al-Khalīl said" as the book's attribution | S | This is reading advice, now worded as attribution and paired with the dispute (C38, C39). |
| C38 | (new) One report in al-Suyūṭī's collection has al-Layth call himself "al-Khalīl", so a bare "al-Khalīl said" is al-Layth | S | Muzhir vol. 1, p. 63 (id 57), a chain through Muḥammad b. ʿAbd al-Wāḥid al-Zāhid to Isḥāq ibn Rāhawayh: "وسمَّى نفسه الخليل … فسمَّى لسانه الخليل … إذا قالَ في الكتاب: قال الخليل بن أحمد: فهو الخليل. وإذا قال: وقال الخليلُ مطلقا فهو يحكي عن نفسه". Page confirmed. |
| C39 | (new) Haywood calls the phrase "slightly ambiguous" | S | Haywood p. 27 (opening of ch. 4): "The expression 'qala l-Khalil' (al-Khalil said) is slightly ambiguous." |
| C40 | Ebd heading excerpt and translation | S | Entry 372 = ayn-ed vol. 2, p. 48, verbatim. |
| C41 | (new) *baʿd* and *bidʿa* are in this entry "only in the Original Text, not our English versions" | S | Entry 372's stored Arabic has the بعد and بدع sections. API /372: both translation_en and harmonized_en end at *al-ʿabādīd*. |
| C42 | ʿabd excerpt (restored words) and translation | S | Entry 372 = ayn-ed vol. 2, p. 48, verbatim, including "وثلاثة أعْبُد، وهم العباد أيضاً". The translation is faithful. |
| C43 | *ʿabada/yaʿbudu/ʿibāda* "said only of one who worships God"; one does not say *ʿabadahu* of a slave serving his master | S | Entry 372; ayn-ed vol. 2, p. 48. |
| C44 | *wa-ʿabada l-ṭāghūt* (Q 5:60) "is read in seven ways", each parsed | S | ayn-ed vol. 2, p. 49. The entry says only "هذه الآية"; the phrase occurs in the Qur'an only at 5:60, so the identification is sound. |
| C45 | Observation (labelled): at Q 5:60 the object is al-ṭāghūt, not God | S | The entry's own gloss: "عَبَدَ الطّاغوتَ من دون الله". |
| C46 | ʿabad ("disdain") excerpt and translation | S | ayn-ed vol. 2, p. 50, verbatim. |
| C47 | Q 43:81 read through "disdain"; a second explanation recorded without a choice | S | ayn-ed vol. 2, p. 50 ("ويقال: … فلست بأوّل من عَبَدَ الله مِنْ أهلِ مكّة"). fn 6: "سورة الزخرف ٨١". |
| C48 | A saying attributed to "the Commander of the Faithful"; a verse whose poet the editors could not identify | S | ayn-ed vol. 2, p. 50, fn 7, placed on the verse after the saying: "لم نهتد إلى القائل، ولم تفدنا المراجع في القول شيئا". |
| C49 | bidʿa: two definitions; excerpt; ص abbreviates the blessing | S | ayn-ed vol. 2, p. 54 ("اسم ما ابتدع من الدين وغيره") and p. 55 ("ما استحدثت بعد رسول الله ص من أهواء وأعمال"). |
| C50 | The second definition is by its own terms later than the Qur'an | S | Its wording, "بعد رسول الله". |
| C51 | "This chapter, at least, gathers rather than theorises…" | S | Entry 372 read in full. The claim is scoped to this chapter. |
| C52 | It judges the common reading of Q 2:117 "more correct" | S | ayn-ed vol. 2, p. 55: "وقراءة العّامة الرّفع [وهو] أولى بالصواب". fn 27 on p. 54 identifies "سورة البقرة ١١٧". (The phrase also occurs at Q 6:101; the guide follows the editors.) |
| C53 | ẓ-l-m runs from *ẓalam* (gloss "when the first thing blocks your sight") through snow, the gleam of teeth and the male ostrich, to wrongdoing and its concrete uses | S | ayn-ed vol. 8, pp. 162–163 = entry 287: "لَقِيتُه أوَّلَ ذي ظَلَمٍ، وهو إذا كان أوَّلَّ شيءٍ سَدَّ بَصَرَكَ في الرُؤية … الثَّلْج … صفاء الأسنان وشدة ضوئها … الظَّليمُ: الذَكَّرُ من النَّعام … والظُّلْمُ: أخذُكَ حقَّ غَيْرك". |
| C54 | Zlm excerpt and translation | S | Entry 287 = vol. 8, p. 163, verbatim with valid ellipses. |
| C55 | "It ends with 'ẓulm is shirk', citing Q 31:13" | **NQ** | The ẓ-l-m section ends so (vol. 8, p. 164; fn 47 "سورة لقمان، الآية ١٣"). But the linked entry (287) goes on to the l-m-ẓ section (*lamẓ*, *lumāẓa*, a hadith). A reader who opens it will see the entry continue. |
| C56 | …and never says how these senses hang together | S | Entry 287 read in full. |
| C57 | Ibn Fāris names the ʿAyn first among the five books the *Maqāyīs* is built on | S | Maqāyīs vol. 1, pp. 3–5: "فأعلاها وأشرفُهَا كتابُ … الخليل بن أحمد، المسمَّى (كتابَ العين) … فهذِه الكتبُ الخمسةُ معتمَدُنَا". |
| C58 | Ibn Fāris quotes al-Khalīl; excerpt and translation | S | Entry 295, verbatim ("وَمِنْ هَذَا الْبَابِ مَا حَكَاهُ الْخَلِيلُ"). |
| C59 | Ibn Fāris files the dug ground and the slaughtered camel under his second root | S | Entry 295: "وَالْأَصْلُ الْآخَرُ … وَالْأَرْضُ الْمَظْلُومَةُ … وَإِذَا نُحِرَ الْبَعِيرُ مِنْ غَيْرِ عِلَّةٍ فَقَدْ ظُلِمَ". |
| C60 | "the *ʿAyn* supplies the material, the theory is Ibn Fāris's" | **NQ** | The second half is supported. The first half overstates: in entry 295 Ibn Fāris credits only one item to al-Khalīl (*awwal dhī ẓulma*). Much of his material is not in the ʿAyn entry at all: the proverb "man ashbaha abāhu fa-mā ẓalam" with Kaʿb's verse, *ẓalīm* for the earth dug up and for unready milk (*ẓalama waṭbahu*), and the verses on these. The ʿAyn is one of five named sources (Maqāyīs pp. 3–5). |
| C61 | "the darkness sense is bracketed in our copy because the editors restored it from al-Azharī's *Tahdhīb*, which quotes the *ʿAyn*" | **NQ** | The reason is supported: vol. 8, p. 163, fn 43, "ما بين القوسين من التهذيب من أصل العين". But only the definition "[والظُّلْمةُ: ذَهابُ النُّور، وجمعُه الظُّلَمُ]" is bracketed. The next clause, "والظَّلامُ اسم للظُّلْمة، لا يُجمَعُ، يُجْرَى مُجْرَى المصدر", is manuscript text, and so is "وليلةٌ ظَلْماءُ". Saying "the darkness sense" is bracketed suggests the manuscripts lack darkness altogether. |
| C62 | Observation (labelled): "ẓulm is shirk" turns a verse into a definition | S | Entry text; Q 31:13. This is labelled interpretation. |
| C63 | §5: "sets everyday words beside examples from religious literature and poetry" [haywood p. 39] | S | Haywood p. 39, as quoted under C9. |
| C64 | Its date is not the date of its evidence; some definitions are later than the Qur'an (bidʿa) | S | C50. |
| C65 | Copies circulated with additions; al-Zubaydī found some citing Abū ʿUbayd, who was 16 or 21 when al-Khalīl died | S | Muzhir vol. 1, p. 66: "أخبرنا المسعري عن أبي عُبيد … وأبو عبيد يومئذ ابنُ ست عشرة سنة. وعلى الرواية الأخرى ابن إحدى وعشرين". |
| C66 | Our text rests on much later manuscripts | S | ayn-ed vol. 1, pp. 31–34 (1054, 1087 and 1350s AH). |
| C67 | *ʿamal* "work" is treated inside ع ل م | S | Entry 35 heading "ع ل م، ع م ل…" and "عمل: عَمِلَ عَمَلاً". Its English also covers ʿamal. |
| C68 | *raḥma* is treated inside ح ر م "(in the Original Text only)" | S | Entry 1622, "رحم: الرَّحمن الرَّحيم: اسمانِ مُشتَقّانِ من الرَّحْمة". Its harmonized English says "this digest covers the ḥ-r-m section only", and neither English version has raḥma. |
| C69 | The root pages ع م ل and ر ح م show no Kitāb al-ʿAyn entry | S | `root Eml` and `root rHm` list no al-khalil entry. |
| C70 | Each chapter is stored under the root that opens it | S | This holds for Ebd, Elm, Hrm, ESb, Zlm and ktb: the stored root is the first arrangement in each heading. |
| C71 | onOurSite: the stored text matches the al-Makhzūmī–al-Sāmarrāʾī edition word for word in Ebd, Zlm and ktb | S | Machine diff (see Evidence base): no stored-side differences. |
| C72 | arabiclexicon.hawramani.com does not name its source | S | The landing page (HTTP 200) names no edition. |
| C73 | Three late manuscripts; the oldest copied 1054 AH (1644–5 CE) | S | ayn-ed vol. 1, pp. 31–34: "تاريخ كتابتها هو سنة اربع وخمسين وألف … لانها أقدم النسخ الثلاث". |
| C74 | The editors reordered entries within chapters | S | ayn-ed vol. 1, pp. 43–44, item 6: "فأرجعناها إلى الترتيب الاصيل". |
| C75 | Square brackets mark the editors' additions, some from the *Tahdhīb*; the footnotes are not shown | S | vol. 1, p. 44, item 7 ("ما اقتضى السياق زيادته بين معقوفتين"). Tahdhīb sources: vol. 8, p. 163, fnn 43–44, and vol. 5, p. 341, fn 2. The stored texts have no footnotes. |
| C76 | (new) At least one bracketed heading, that of ك ت ب, appears without its brackets | S | vol. 5, p. 341 prints "[باب الكاف والتاء والباء معهما ك ت ب، …مستعملات]". Stored entry 21 has no brackets. |
| C77 | 505 entries displayed | S | `dicts`: "displayed entries=505"; direct count 505. |
| C78 | Most entries are whole chapters headed by "in use" / "unused" lists | S | 418 of 505 begin with باب, and 416 have مستعمل/يستعمل in the heading. |
| C79 | One entry can cover several roots, while many roots have no entry of their own | S | Ebd, Hrm and Elm cover several roots; Eml and rHm have none. |
| C80 | (new) On such chapters the English may cover only the opening root | S | /372 and /1622 are partial; /35 covers ʿamal, which is why "may" is right. |
| C81 | Occasionally ص or ع abbreviates a blessing formula | S | ص in Ebd, kvr and hrb; ع in klm ("إدريس النبي ع"). |
| C82 | Source: Haywood, *Arabic Lexicography: Its History, and Its Place in the General History of Lexicography* (Brill, 1960), chs 3–5 | S | Title page in the djvu text. Cited pp. 26–27 fall in chs 3–4, pp. 38–39 in ch. 4, and p. 43 in ch. 5. |
| C83 | Source: Muzhir, ed. Fuʾād ʿAlī Manṣūr (Dār al-Kutub al-ʿIlmiyya, 1998), vol. 1, pp. 61–68 | S | Shamela 6936 card; pages read. |
| C84 | Source: Maqāyīs, ed. Hārūn, al-Bābī al-Ḥalabī, 2nd ed., 1969–72 | S | Shamela 21710 card. |

**Totals: 84 claims. 80 supported, 4 need qualification, 0 unsupported.**

## Status of round-1 flags

All nine round-1 flags have been addressed correctly. Each fix is covered by a claim above:

| Round-1 flag | Fixed in | Now |
|---|---|---|
| C11 | lede and §1 | C11, C16, C17 |
| C34 | §2 | C37–C39 |
| C36 | §3 | C41 |
| C59 | §5 | C68 |
| C37 | ʿabd excerpt | C42 |
| C48 | ẓalam gloss | C53 |
| C56 | §5 | C63 |
| C9 | summary | C9 |
| C68 | onOurSite | C76 |

The round-1 must-fix (promising material missing from the English view) is resolved: both places now say "Original Text". The source note now reads "chs 3–5". First-person voice is gone.

## Flagged items and fixes

1. **C35 (Haywood on authorship).**
   - Change "while crediting al-Khalīl with at least the plan" to "while crediting al-Khalīl with 'a major share at least in the planning'".
   - Optionally add "though he doubted that the phonetic ideas behind the letter order were al-Khalīl's own" [^haywood|p. 26].
2. **C55 (end of the ẓ-l-m entry).**
   - Change "It ends with 'ẓulm is shirk', citing Q 31:13" to "Its ẓ-l-m section ends with 'ẓulm is shirk', citing Q 31:13" (the stored entry goes on to l-m-ẓ).
3. **C60 (what Ibn Fāris took from the ʿAyn).**
   - Change "the *ʿAyn* supplies the material, the theory is Ibn Fāris's" to "these senses are already in the *ʿAyn*, but the two-root theory that sorts them is Ibn Fāris's".
   - Alternatively: "the *ʿAyn* is one of his sources; the theory is his own".
   - Do not imply that Ibn Fāris's material comes wholly from the ʿAyn. He adds the proverb *man ashbaha abāhu fa-mā ẓalam*, the "wronged" milk-skin and other matter that the ʿAyn entry lacks (entry 295).
4. **C61 (bracketed darkness).**
   - Change "the darkness sense is bracketed in our copy because…" to "the definition of *ẓulma* as 'the going of light' is bracketed in our copy because the editors restored it from al-Azharī's *Tahdhīb*, which quotes the *ʿAyn* [^ayn-ed|vol. 8, p. 163]; the next line, on *ẓalām*, is in the manuscripts".
   - This precision matters. The unbracketed ẓalām and laylat ẓalmāʾ lines show that the darkness sense is not solely an editorial import.

## Brief (non-factual) issues

- **suggestion.** The validator counts lede + body at **1,142 words**, over the brief's roughly 700–1,100 range. Trimming candidates:
  - the §2 list of verdicts (the al-Zubaydī clause could merge with the §5 Abū ʿUbayd point)
  - the §4 senses list
  - the §5 sentence "An entry maps a word's range…", which partly repeats the site-wide guidance
  - The fixes above add few or no words.
- **suggestion.** Short English renderings of the introduction are quoted inline without a label:
  - "This is what al-Khalīl ibn Aḥmad of Basra composed"
  - "from al-Khalīl, everything in this book"
  - "at the far end of the throat"
  - "clearer"

  The shared box says quotations "come from that stored original", but these come from the printed introduction, which the site does not store. Add one "(translations for this guide)" after the first of them in §2, or rely on the source citation.
- The remaining points need no change:
  - No generic praise or ranking.
  - Every root mention is linked. The Eml and rHm `none` links are explained in the sentence.
  - The comparison is linked in both dictionaries.
  - All excerpts are labelled as translations.
  - The essay does not force an "original root meaning" narrative, and it says outright that this chapter does not theorise.

## Source URLs

All six open and point to the stated works:

| Source | URL | What it opens |
|---|---|---|
| ayn-ed | https://shamela.ws/book/1682 | Card matches: al-Makhzūmī–al-Sāmarrāʾī, al-Hilāl, 8 vols, printed pagination |
| ayn-intro | https://shamela.ws/book/1682/37 | vol. 1, p. 47 [مقدمة الكتاب] |
| muzhir | https://shamela.ws/book/6936/55 | vol. 1, p. 61 |
| maqayis-ed | https://shamela.ws/book/21710/47 | vol. 1, p. 3 (author's preface) |
| haywood | https://archive.org/details/in.gov.ignca.12555 | Haywood 1960; the djvu text holds every cited page |
| hawramani | https://arabiclexicon.hawramani.com/al-khalil-b-ahmad-al-farahidi-kitab-al-ain/ | Landing page, HTTP 200 |

Every listed source is cited in the text, and none is unused.

## Validator

`node scripts/validate-dictionary-guides.mjs kitab-al-ayn` → **ok, 1/1 guides pass**. It reports:

- 12 root links (7 distinct root/dictionary pairs)
- 7 excerpts
- 1,142 words
- two expected warnings for `[[root:Eml|none|…]]` and `[[root:rHm|none|…]]`, both explained in the sentence

## Site-data issues (report only; not edited)

1. **English renderings of multi-root chapters cover only the headword root.**
   - Ebd (372): both English versions stop at *al-ʿabādīd*, and the harmonized text does not say it is partial.
   - Hrm (1622): the harmonized text says it covers ḥ-r-m only.
   - Elm (35) covers ʿamal, so the behaviour is inconsistent.
   - The guide now discloses this. The underlying data gap remains.
2. **The harmonized English attributes the content directly to al-Khalīl.** Examples: Ebd "Al-Khalīl notes…", "Al-Khalīl reads Q 43:81…"; Hrm "Al-Khalīl reports both readings…". Muzhir vol. 1, pp. 62–67 and Haywood pp. 26–27 dispute authorship and the reference of "qāla l-Khalīl", so "the *ʿAyn*" would be safer.
3. **Title spelling.**
   - The stored label is "Kitāb al-ʿAin", following hawramani. The guide uses *al-ʿAyn*.
   - Consider aligning the site label (the harmonized headers also say "Kitāb al-ʿAin").
4. **Author label and date.**
   - The stored author is "al-Khalīl al-Farāhīdī", with no mention of al-Layth's transmission. The harmonized headers say "d. 786".
   - 786 = 170 AH, one of two reported death dates; the other is 175 AH / 791 CE (Muzhir vol. 1, p. 66). This is fine for ordering, but it is not the only date.
5. **The stored text drops the editors' footnotes and some heading brackets** (ktb, vol. 5, p. 341). The guide discloses this.
6. **Shared box wording.** "Quotations on this page come from that stored original" is not true of quotations from a work's printed introduction, which this guide (like others) uses. The shared template could say "Excerpts from entries come from that stored original".
