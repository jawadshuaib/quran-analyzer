# Kitāb al-ʿAyn: verification round 3 (independent fact-check)

Page checked: `roots/frontend/src/content/dictionary-guides/guides/kitab-al-ayn.ts` (the version after revision r2).
Checked 2026-09-26. I did not open research-notes.md or any revision-*.md file. I read verification-r2.md only for its list of flags. Every source below was re-fetched by me in this round, into a fresh folder (`scratchpad/r3_ayn/`), not reused from earlier agents' downloads.

## Evidence base (all opened in this round)

- **ayn-ed / ayn-intro**: Shamela book 1682. Card: "المؤلف: أبو عبد الرحمن الخليل بن أحمد بن عمرو بن تميم الفراهيدي البصري (ت ١٧٠هـ) المحقق: د مهدي المخزومي، د إبراهيم السامرائي الناشر: دار ومكتبة الهلال عدد الأجزاء: ٨ [ترقيم الكتاب موافق للمطبوع]". Pages read (printed page from each page title):
  - vol. 1: pp. 16–18 (ids 12–14), 27 (23), 31–34 (27–30), 43–44 (35–36), 47–60 (37–50: the whole introduction)
  - vol. 2: pp. 48–55 (403–410), the whole ع ب د chapter with footnotes
  - vol. 5: pp. 341–342 (1913–1914), the ك ت ب chapter
  - vol. 8: pp. 162–164 (2933–2935), the ظ ل م chapter
- **muzhir**: Shamela 6936. Card: "المحقق: فؤاد علي منصور الناشر: دار الكتب العلمية - بيروت الطبعة: الأولى، ١٤١٨هـ ١٩٩٨م عدد الأجزاء: ٢"; author "(ت ٩١١هـ)". Read vol. 1, pp. 61–68 (ids 55–62).
- **maqayis-ed**: Shamela 21710. Card: "تحقيق وضبط: عبد السلام محمد هارون … مصطفى البابي الحلبي … الطبعة: الثانية … (١٩٦٩ - ١٩٧٢ م) … عدد الأجزاء: ٦". Read vol. 1, pp. 3–5 (ids 47–49).
- **haywood**: archive.org `in.gov.ignca.12555`, metadata "Arabic lexicography / Haywood, John A. / 1960". The djvu text's title page reads "ARABIC LEXICOGRAPHY / ITS HISTORY, AND ITS PLACE IN THE GENERAL HISTORY OF LEXICOGRAPHY … LEIDEN / E. J. BRILL", and the imprint reads "Copyright 1960 by E. J. Brill". The contents list ch. III (p. 20), IV (p. 28 [OCR "2S"]), V (p. 41). I read pp. 26–27, 38–39 and 43.
- **hawramani**: https://arabiclexicon.hawramani.com/al-khalil-b-ahmad-al-farahidi-kitab-al-ain/ returns HTTP 200. The blurb names no edition, editor or publisher.
- **Stored entries** (`_dict_guide_tool.py entry`), all DISPLAYED: Kitāb al-ʿAin Ebd = 372, ESb, Zlm = 287, ktb = 21, Elm = 35, Hrm = 1622; Ibn Fāris Zlm = 295. `root Eml` and `root rHm` list no al-khalil entry.
- **My own machine diff.** I normalised the stored Original Text of Ebd, Zlm and ktb and the printed pages (vowel marks, hamza seats, tāʾ marbūṭa, punctuation removed) and aligned them with difflib. Every stored character is matched. Everything the print has and the stored text lacks is footnote text (e.g. "لم نهتد إلى القائل", "سورة الزخرف", "تكملة من التهذيب ١٠/ ١٥١ عن العين").
- **My own database counts** (same display filter as the tool): 505 displayed entries. 418 begin with باب. Of those 418 headings, 403 contain مستعمل/يستعمل, 141 contain فقط ("only"), and **only 16 contain مهمل ("unused")**. The ص/ع blessing abbreviation after رسول الله / النبي occurs in Ebd, kvr, klm and hrb.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title *Kitāb al-ʿAyn* / titleAr كتاب العين | S | Shamela 1682 card "كتاب العين"; Maqāyīs vol. 1, p. 3 "المسمَّى (كتابَ العين)". |
| C2 | titleGloss: named after its first letter | S | ayn-intro p. 47: "فوجد العيْن ادخَلَ الحروف في الحَلْقِ، فَجَعَلهَا أوّل الكتابِ". |
| C3 | author: al-Khalīl, as transmitted by al-Layth ibn al-Muẓaffar | S | ayn-intro p. 48: "حدَّثني الليثُ بنُ المُظَفَّر بن نصر بن سَيَّار عن الخليل بجميع ما في هذا الكتاب". |
| C4 | authorFull Abū ʿAbd al-Raḥmān al-Khalīl ibn Aḥmad al-Farāhīdī al-Baṣrī | S | Shamela 1682 card (quoted above). |
| C5 | authorAr الخليل بن أحمد الفراهيدي | S | Same card. |
| C6 | period: d. 170 or 175 AH / 786 or 791 CE | S | Muzhir vol. 1, p. 66: "تُوفِّيَ الخليل سنة سبعين ومائة وفي بعض الروايات سنة خمس وسبعين ومائة". Conversions correct. |
| C7 | kind "Sound-ordered root dictionary" | S | ayn-intro pp. 47–48, 57–58 (order by مخرج). |
| C8 | summary: letters ordered by where they are sounded in throat and mouth; each root filed with its rearrangements | S | ayn-intro pp. 47–48, 58–59; Haywood p. 38 ("roots are dealt with anagrammatically, all permutations … grouped together"). |
| C9 | summary: entries set everyday words beside Qur'anic citations and poetry | S | Haywood p. 39 ("did not invariably … omit common words which were familiar in everyday speech … frequently quotes examples from religious literature and poetry"); Qur'anic citations in Ebd (Q 5:60, 43:81, 46:9, 2:117) and Zlm (Q 31:13). |
| C10 | summary: who completed it is disputed | S | Muzhir vol. 1, pp. 62–67. |
| C11 | lede: starts with ʿayn, which "its introduction places deepest in the throat" | S | ayn-intro p. 47 ("ادخَلَ الحروف في الحَلْقِ"), p. 57 ("فأقصى الحروف كلها العين"), p. 60 ("بالعين وهو أقصَى الحروف"). |
| C12 | lede: files each root with every rearrangement found in use | S | ayn-intro p. 59; Haywood p. 38. |
| C13 | lede: oldest surviving attempt to take in the whole Arabic vocabulary by a system | S | ayn-ed vol. 1, p. 18: "والعين بهذا أول معجم في العربية ولعله معجم موعب"; Haywood p. 39 ("the first Arabic dictionary"), p. 43 ("the first exhaustive vocabulary"). The guide's "oldest surviving" is more cautious than its sources. |
| C14 | lede: voices of al-Khalīl, al-Layth and later hands | S | ayn-intro pp. 48, 50, 52; Muzhir p. 63 (Thaʿlab: "وقد حشا الكتاب أيضا قومٌ علماء"), p. 66 (al-Zubaydī on additions). |
| C15 | §1: label "translations on this page are this guide's own" | S | Editorial label; covers the inline renderings. |
| C16 | §1: unable to open with alif, a "weak" letter | S | ayn-intro p. 47: "فلم يمكنه أن يبتدىء التأليفُ من أول ا، ب، ت، ث، وهو الألف، لأن الألف حرف معتلّ". |
| C17 | §1: "tasted" the letters, opening his mouth on alif: *ab, at, aḥ, aʿ, agh* | S | ayn-intro p. 47: "وذاقَها … كان يَفْتَحُ فاهُ بالألفِ ثم يُظْهِرُ الحَرْفَ. نحو ابْ، اتْ، احْ، اعْ، اغْ". |
| C18 | §1: ʿayn deepest, made the first book, worked outward to mīm at the lips | S | ayn-intro p. 47 ("الأرفعُ فالأرفع حتى أتَى على آخرها وهو الميم"); p. 58 (ف ب م "شَفَويّة"). |
| C19 | §1: the same introduction puts hamza "at the far end of the throat" | S | ayn-intro p. 52: "وأمّا الهَمْزة فَمَخْرَجُها من أقصَى الحَلْق". |
| C20 | §1: the modern editors favour a report passed on by Ibn Kaysān in which al-Khalīl preferred ʿayn to ḥāʾ as the "clearer" letter | S | ayn-ed vol. 1, p. 17: "وكان قد بدأ بالعين، لا لانها أول الحروف مخرجا، ولكنها أول الحروف نصاعة"; "قال ابن كيسان …: سمعت من يذكر عن الخليل … فوجدت العين أنصع الحرفين". p. 18: "فالجواب عنه هو ما قدمناه من بيان، ومن نقل عن ابن كيسان". |
| C21 | §1: roots sorted by type within each book (doubled, sound triliteral, weak, four- and five-letter) | S | ayn-ed vol. 1, p. 16 (six classes: ثنائي مشدد، ثلاثي صحيح، ثلاثي معتل، لفيف، رباعي، خماسي); Haywood p. 38. |
| C22 | §1: 6 / 24 / 120 arrangements | S | ayn-intro p. 59. |
| C23 | §1: "the used are written down and the unused discarded" | S | ayn-intro p. 59: "يُكَتَب مُسْتَعْمَلها. ويُلغى مُهْمَلها". (Stated there of the quadriliteral; the five-letter line says "يُسْتَعْمَل أقَلُّه ويُلغى أكثره". Applying it to "such arrangements" generally is fair; Haywood p. 38 describes the same practice for triliterals.) |
| C24 | §1: a word is filed under whichever of its letters comes earliest in the order | S | ayn-intro p. 47: "فمهما وَجَدتَ منها واحداً في الكتاب المقدَّم فهو في ذلك الكتاب". |
| C25 | §1 (labelled as this guide's reading): rearrangements are a check that nothing is missed; the introduction never claims rearranged roots share a meaning | S | I read pp. 47–60 in full: no shared-meaning claim. p. 47 "فلا يخرج منها عنه شيء" fits the "check" reading. Haywood p. 39 calls the shared-meaning idea a later "false idea". |
| C26 | §1 quote بدأنا في مؤلفنا هذا بالعين وهو أقصى الحروف … حتى نستوعب كلام العرب الواضح والغريب, translation, and "words credited to al-Khalīl" | S | ayn-intro p. 60: "وقال الخليل: بَدَأَنَا في مُؤلَّفنا هذا بالعين وهو أقصَى الحروف، ونضُمُّ إليه ما بعده حتى نَسْتَوْعِبَ كلام العرب الواضحَ والغريب". Ellipsis valid; translation faithful. |
| C27 | §2: "This is what al-Khalīl ibn Aḥmad of Basra composed" | S | ayn-intro p. 47: "هذا ما ألفه الخليل بن أحمد البصريّ". |
| C28 | §2: al-Layth passes on "from al-Khalīl, everything in this book" | S | ayn-intro p. 48 (C3). |
| C29 | §2: many statements framed "al-Layth said: al-Khalīl said"; al-Layth sometimes speaks as "I" | S | pp. 48, 57, 58, 59 ("قال الليث: قال الخليل"); p. 50 ("قال ليث: قلت لأبي الدقيش"), p. 52 ("قال الليث: قلت"). |
| C30 | §2: ESb excerpt and translation (inside the chapter filed under ع ص ب) | S | Stored ESb entry: "قال الليث: قلت للخليل: ما علامة اسم التأنيث؟ قال: ثلاثة أشياء". |
| C31 | §2: al-Suyūṭī d. 911 AH / 1505 CE | S | Shamela 6936 card "(ت ٩١١هـ)"; 911 AH = 1505–6 CE. |
| C32 | §2: his collected verdicts go back to the ninth century | S | Muzhir p. 63 (Isḥāq ibn Rāhawayh; Thaʿlab), pp. 66–67 (Abū Ḥātim, c. 250 AH). |
| C33 | §2: al-Azharī: al-Layth wrote it and put al-Khalīl's name on it so that it would sell | S | Muzhir p. 62: "عمِل كتاب العين ونسبَه إلى الخليل لينفق كتابه باسمه ويرغب فيه". |
| C34 | §2: others: al-Khalīl wrote as far as *ghayn*, al-Layth finished it | S | Muzhir p. 62: "وقال بعضهم: عَمِلَ الخليلُ من كتاب العين قطعة من أوَّله إلى حرف الغين وكَمَّله الليث". |
| C35 | §2: al-Zubaydī, its abridger: al-Khalīl laid the foundation and died before finishing | S | Muzhir p. 64 ("مؤلف مختصر العين"), p. 65 ("أن الخليل سَبَّب أصله وثقَّف كلام العرب ثم هلَك قبل كَماله"). |
| C36 | §2: arrived from Khurāsān c. 250 AH; Abū Ḥātim al-Sijistānī rejected it; argued that al-Khalīl's students had never heard of it | S | Muzhir pp. 66–67: "لما وَرَدَ كتابُ العَين من بلد خُراسان في زمن أبي حاتم أنكره"; "وقد غَبر أصحابُ الخليل بعدُ مدة طويلة لا يعرفون هذا الكتابَ"; "فيما قارب الخمسين والمائتين لأن أبا حاتم تُوُفِّي سنة خمس وخمسين ومائتين" (d. 255 = al-Sijistānī). |
| C37 | §2: modern editors: the book in design and substance is al-Khalīl's | S | ayn-ed vol. 1, p. 27: "أن كتاب العين بتأسيسه وبحشوه … إنما هو كتاب الخليل". |
| C38 | §2: Haywood: "will probably never be convincingly solved" | S | Haywood p. 26: "The problem of the authorship of the [ʿAin] will probably never be convincingly solved". |
| C39 | §2 (round-2 fix): Haywood credits al-Khalīl with "a major share at least in the planning" | S | Haywood p. 26: "Knowing al-Khalīl's original mind, we must credit him with a major share at least in the planning". Verbatim. |
| C40 | §2: al-Suyūṭī: al-Zubaydī's errors concern arrangement, word-formation, alleged miscopying, never whether a word is genuine; no bar to relying on it | S | Muzhir p. 68: "غالبُه من جهة التصريف والاشتقاق … وبعضُه ادعى فيه التصحيف وأما أنه يُخَطأ في لفظة من حيث اللغة … فمعاذَ الله لم يقع ذلك … راجعٌ إلى الترتيب والوضْع … لا يمنعُ الوثوقَ بالكتاب". |
| C41 | §2: reading advice (unattributed text = the transmitted book; "al-Khalīl said" = its attribution) | S | Advice, framed as attribution and paired with the dispute (C42–C43). |
| C42 | §2: one report has al-Layth call himself "al-Khalīl", making a bare "al-Khalīl said" his own voice | S | Muzhir p. 63: "وسمَّى نفسه الخليل … وإذا قال: وقال الخليلُ مطلقا فهو يحكي عن نفسه". |
| C43 | §2: Haywood calls the phrase "slightly ambiguous" | S | Haywood p. 27: "The expression 'qala l-Khalil' (al-Khalil said) is slightly ambiguous." |
| C44 | §3: Ebd heading excerpt and translation | S | Entry 372 = ayn-ed vol. 2, p. 48, verbatim. |
| C45 | §3: this entry also holds *baʿd* and *bidʿa*, in the Original Text only | S | Entry 372 original has "بعد:" and "بدع:" sections; both English versions stop at *al-ʿabādīd* (checked). |
| C46 | §3: it begins with the human being; ʿabd excerpt and translation | S | Entry 372; vol. 2, p. 48. Translation faithful. |
| C47 | §3: *ʿabada/yaʿbudu/ʿibāda* "is said only of one who worships God"; not *ʿabadahu* of a slave serving his master | S | vol. 2, p. 48: "وأمّا عبَد يعبُد عِبادة فلا يقال إلا لمن يعبد الله … وأمّا عبدٌ خدَم مولاه، فلا يقال: عَبَدَه". |
| C48 | §3: *wa-ʿabada l-ṭāghūt* (Q 5:60) "is read in seven ways" and each parsed | S | vol. 2, p. 49: "وتقرأ هذه الآية على سبعة أوجه" followed by seven parsed readings. The phrase occurs only at Q 5:60. |
| C49 | §3 (labelled observation): object at Q 5:60 is al-ṭāghūt, not God | S | Entry's own gloss "عَبَدَ الطّاغوتَ من دون الله". |
| C50 | §3: ʿabad "disdain" excerpt and translation | S | vol. 2, p. 50, verbatim; translation faithful. |
| C51 | §3: Q 43:81 read through that sense; rendering of the verse | S | vol. 2, p. 50, fn 6 "سورة الزخرف ٨١". |
| C52 | §3: records a second explanation without choosing | S | vol. 2, p. 50: "ويقال: … فلست بأوّل من عَبَدَ الله مِنْ أهلِ مكّة", with no preference stated. |
| C53 | §3: backs "disdain" with a saying attributed to "the Commander of the Faithful" and a verse by an unnamed poet | S | vol. 2, p. 50: "ويروى عن أمير المؤمنين أنّه قال: عَبِدْتُ فَصَمَتُّ"; "قال «٧» :" with fn 7 "لم نهتد إلى القائل، ولم تفدنا المراجع في القول شيئا". |
| C54 | §3: bidʿa, first definition "whatever is newly introduced, in religion and otherwise" | S | vol. 2, p. 54: "والبِدْعَةُ: اسم ما ابتدع من الدين وغيره". |
| C55 | §3: bidʿa second definition excerpt and translation; ص abbreviates the blessing | S | vol. 2, p. 55, verbatim. |
| C56 | §3: second definition by its own terms later than the Qur'an | S | Its wording, "بعد رسول الله". |
| C57 | §3: this chapter gathers rather than theorises, no single meaning from which the rest derive | S | Entry 372 read in full; scoped to this chapter. |
| C58 | §3: judges the common reading of Q 2:117 "more correct" | S | vol. 2, p. 55: "وقراءة العّامة الرّفع [وهو] أولى بالصواب"; p. 54, fn 27 "سورة البقرة ١١٧". |
| C59 | §4: ẓ-l-m runs from *ẓalam* ("when the first thing blocks your sight") through snow, gleam of teeth, male ostrich, to wrongdoing and concrete uses | S | vol. 8, pp. 162–163 = entry 287: "وهو إذا كان أوَّلَّ شيءٍ سَدَّ بَصَرَكَ في الرُؤية … الثَّلْجُ … صفاء الأسنان وشدة ضوئها … الظَّليمُ: الذَكَّرُ من النَّعام … والظُّلْمُ: أخذُكَ حقَّ غَيْرك". |
| C60 | §4: Zlm excerpt and translation | S | Entry 287 = vol. 8, p. 163, verbatim with valid ellipses. |
| C61 | §4 (round-2 fix): the section closes with "ẓulm is shirk", citing Q 31:13, before the chapter moves on to *lamẓ* | S | vol. 8, p. 164: "والظُّلْمُ: الشِّرْك، قال الله- عز وجل-: إِنَّ الشِّرْكَ لَظُلْمٌ عَظِيمٌ «٤٧» . لمظ «٤٨» : اللَّمْظُ …"; fn 47 "سورة لقمان، الآية ١٣". Entry 287 identical. |
| C62 | §4: nowhere does it say how the senses hang together | S | Entry 287 read in full. |
| C63 | §4: Ibn Fāris names the ʿAyn first among the five books the *Maqāyīs* is built on | S | Maqāyīs vol. 1, pp. 3–5: "فأعلاها وأشرفُهَا كتابُ أبى عبد الرحمن الخليل بن أحمد، المسمَّى (كتابَ العين)" … "فهذِه الكتبُ الخمسةُ معتمَدُنَا". |
| C64 | §4 (new): Ibn Fāris cites al-Khalīl once | S | Entry 295 names al-Khalīl once: "وَمِنْ هَذَا الْبَابِ مَا حَكَاهُ الْخَلِيلُ … قَالَ: …". |
| C65 | §4: Ibn Fāris excerpt and translation | S | Entry 295, verbatim; translation faithful. |
| C66 | §4: he files the dug ground and the slaughtered camel under his second root | S | Entry 295: "وَالْأَصْلُ الْآخَرُ … وَالْأَرْضُ الْمَظْلُومَةُ … وَإِذَا نُحِرَ الْبَعِيرُ مِنْ غَيْرِ عِلَّةٍ فَقَدْ ظُلِمَ". |
| C67 | §4 (round-2 fix): these senses are already in the ʿAyn, but the two-root theory is Ibn Fāris's | S | Both senses in entry 287 (vol. 8, p. 163); the "أَصْلَانِ" scheme is entry 295's and absent from 287. |
| C68 | §4 (round-2 fix): the bracketed definition of *ẓulma* was restored by the editors from al-Azharī's *Tahdhīb*, which quotes the ʿAyn | S | vol. 8, p. 163, fn 43: "ما بين القوسين من التهذيب من أصل العين"; vol. 1, p. 44, item 7: "ووضعنا ما اقتضى السياق زيادته بين معقوفتين". |
| C69 | §4 (new): "but the next line, on *ẓalām*, is manuscript text" | **NQ** | vol. 8, p. 163: "، والظَّلامُ اسم للظُّلْمة، لا يُجمَعُ، يُجْرَى مُجْرَى المصدر [كما لا يجمع نظائره نحو السواد والبياض] «٤٤»", with fn 44 "زيادة أخرى من التهذيب من أصل العين". Only the first half of the ẓalām line is manuscript text; its closing clause is a second Tahdhīb bracket, and the stored entry 287 shows that bracket. So does the next line, "وليلةٌ ظَلْماءُ [ويَومٌ مظلم] «٤٥»". |
| C70 | §4 (labelled observation): "ẓulm is shirk" turns a verse into a definition | S | Entry text; Q 31:13 "إِنَّ الشِّرْكَ لَظُلْمٌ عَظِيمٌ". |
| C71 | §5: the ʿAyn's date is not the date of its evidence; some definitions later than the Qur'an (bidʿa) | S | C56. |
| C72 | §5: copies circulated with additions; al-Zubaydī found some citing Abū ʿUbayd, who was 16 or 21 when al-Khalīl died | S | Muzhir p. 66: "اختلافُ نُسَخِه واضطرابُ رواياته … أخبرنا المسعري عن أبي عُبيد … وأبو عبيد يومئذ ابنُ ست عشرة سنة. وعلى الرواية الأخرى ابن إحدى وعشرين". |
| C73 | §5: our text rests on much later manuscripts | S | ayn-ed vol. 1, pp. 31–34 (1054, 1087 and 1350/1354 AH). |
| C74 | §5: an entry maps a word's range, not its sense in a given verse | S | Reading advice. |
| C75 | §5: each chapter stored under its opening root; *ʿamal* inside ع ل م | S | Entry 35 heading "ع ل م، ع م ل، م ع ل، ل م ع مستعملات"; its English covers ʿamal. |
| C76 | §5: *raḥma* inside ح ر م (Original Text only) | S | Entry 1622 heading lists ر ح م; "رحم: الرَّحمن الرَّحيم: اسمانِ مُشتَقّانِ من الرَّحْمة". Its English says "this digest covers the ḥ-r-m section only"; neither English version has raḥma/mercy. |
| C77 | §5: root pages ع م ل and ر ح م have no entry from this dictionary | S | `root Eml`, `root rHm`: no al-khalil entry. |
| C78 | onOurSite: stored text matches the al-Makhzūmī–al-Sāmarrāʾī edition word for word in Ebd, Zlm, ktb | S | My diff: every stored character matched; print-only material is footnotes. |
| C79 | onOurSite: hawramani does not name its source | S | Landing page (HTTP 200) names no edition or editor. |
| C80 | onOurSite: three late manuscripts, oldest copied 1054 AH (1644–5 CE) | S | ayn-ed vol. 1, p. 31: "وتاريخ كتابتها هو سنة اربع وخمسين وألف … لانها أقدم النسخ الثلاث". |
| C81 | onOurSite: editors reordered entries within chapters | S | ayn-ed vol. 1, pp. 43–44, item 6: "رأينا في ترتيب المفردات داخل أبوابها اضطرابا … فأرجعناها إلى الترتيب الاصيل". |
| C82 | onOurSite: square brackets mark their additions, some from the *Tahdhīb*; footnotes not shown | S | vol. 1, p. 44, item 7; vol. 8, p. 163, fnn 43–44; vol. 5, p. 341, fn 2 ("تكملة من التهذيب ١٠/ ١٥١ عن العين"). Stored texts carry no footnotes. |
| C83 | onOurSite: the bracketed ك ت ب heading appears without brackets | S | vol. 5, p. 341: "[باب الكاف والتاء والباء معهما … مستعملات]"; stored entry 21 begins "باب الكاف والتاء والباء معهما …" with no bracket. |
| C84 | onOurSite: 505 entries displayed | S | `dicts` and my direct count: 505. |
| C85 | onOurSite: "Most are whole chapters headed by lists of letter orders 'in use' (مستعملات) and 'unused' (مهملات)" | **NQ** | 418 of 505 begin with باب and 403 headings name the orders in use, but only 16 name any unused order (e.g. Ebd "مهملان", ESb "مهملة"). Most headings list only the used orders, often with "فقط" ("only", 141 headings, e.g. Zlm "ظ ل م، ل م ظ يستعملان فقط"). |
| C86 | onOurSite: one entry can cover several roots; many roots have no entry | S | Ebd, Elm, Hrm, ktb cover several; Eml, rHm have none. |
| C87 | onOurSite: on such chapters the English may cover only the opening root | S | 372 and 1622 partial; 35 covers ʿamal, which is why "may" is right. |
| C88 | onOurSite: occasionally ص or ع abbreviates a blessing formula | S | ص in Ebd, kvr, hrb; ع in klm. |
| C89 | Source: Haywood, *Arabic Lexicography: Its History, and Its Place in the General History of Lexicography* (Leiden: Brill, 1960), chs 3–5 | S | Title page and "Copyright 1960 by E. J. Brill"; cited pp. 26 (ch. 3), 27–39 (ch. 4), 43 (ch. 5). |
| C90 | Source: ayn-ed as al-Makhzūmī–al-Sāmarrāʾī, 8 vols, Dār wa-Maktabat al-Hilāl, Shamela with printed pagination | S | Shamela 1682 card. |
| C91 | Source: Muzhir, ed. Fuʾād ʿAlī Manṣūr, Dār al-Kutub al-ʿIlmiyya 1998, vol. 1, pp. 61–68, quoting al-Sīrāfī, al-Azharī, Thaʿlab, al-Zubaydī and others | S | Shamela 6936 card; al-Sīrāfī p. 62, al-Azharī p. 62, Thaʿlab pp. 62–63, al-Zubaydī pp. 64–68. |
| C92 | Source: Maqāyīs ed. Hārūn, 6 vols, al-Bābī al-Ḥalabī, 2nd ed., 1969–72 | S | Shamela 21710 card. |

**Totals: 92 claims. 90 supported, 2 need qualification, 0 unsupported.**

## Status of round-2 flags

| Round-2 flag | Now | Verdict |
|---|---|---|
| C35 Haywood "at least the plan" | C39: exact quotation "a major share at least in the planning" | fixed; verbatim on p. 26 |
| C55 "It ends with 'ẓulm is shirk'" | C61: "This root's section closes … before the chapter moves on to *lamẓ*" | fixed; p. 164 and entry 287 confirm |
| C60 "the ʿAyn supplies the material" | C67: "these senses are already in the ʿAyn, but the two-root theory … is Ibn Fāris's" | fixed |
| C61 "the darkness sense is bracketed" | C68 + C69 | mostly fixed; the new clause on ẓalām is slightly over-precise (C69 below) |
| Brief: length 1,142 | now 1,096 (validator) | fixed |
| Brief: unlabelled inline translations | §1 now opens with "(translations on this page are this guide's own)" | fixed |

I checked each new claim the reviser reported: "citing al-Khalīl once" (C64, S), "before the chapter moves on to *lamẓ*" (C61, S), "a verse by an unnamed poet" (C53, S), the Haywood quotation (C39, S) and "the next line, on ẓalām, is manuscript text" (C69, NQ). The cuts the reviser reports removed no needed qualification. The Q 43:81 alternative explanation and the Abū ʿUbayd point both remain.

## Flagged items and fixes

1. **C69 (§4, ẓalām line).**
   - The words "ẓalām is a name for ẓulma" are manuscript text, but the same sentence ends with a second Tahdhīb bracket. The stored entry shows that bracket: "[كما لا يجمع نظائره نحو السواد والبياض]", fn 44 "زيادة أخرى من التهذيب من أصل العين". "The next line … is manuscript text" therefore overstates slightly.
   - Fix: change "but the next line, on *ẓalām*, is manuscript text" to "but the words that follow, '*ẓalām* is a name for *ẓulma*', are manuscript text". Keep the citation [^ayn-ed|vol. 1, p. 44; vol. 8, p. 163].
2. **C85 (onOurSite, chapter headings).**
   - Only 16 of 505 displayed entries name any "unused" (مهمل) order in their heading. 403 name the orders "in use", often adding "only" (فقط).
   - Fix: change "headed by lists of letter orders 'in use' (مستعملات) and 'unused' (مهملات)" to "headed by a list of the letter orders 'in use' (مستعملات), a few also naming those 'unused' (مهملات)".
   - Alternatively: "headed by the letter orders 'in use' (مستعملات)".

## Brief (non-factual) issues

- None must-fix.
- **suggestion.** The ẓ-l-m close reading lists the senses (snow, teeth, ostrich) but does not tell the reader that the chapter's darkness lines ("ليلة ظلماء" etc.) sit among several bracketed Tahdhīb additions. The C69 fix is enough, and nothing more is needed for length.
- Checked with no problem found:
  - Length is 1,096 words, inside 700–1,100.
  - Every root mention is linked, and the two `none` links are explained in the sentence.
  - The comparison is linked in both dictionaries.
  - All excerpts and inline renderings are labelled as the guide's translations.
  - There is no ranking or generic praise.
  - It does not force an "original root meaning" narrative.
  - Omitted material is not promised: "Original Text only" is stated for *baʿd*, *bidʿa* and *raḥma*.
  - The essay's voice is a reader's guide, not an encyclopedia entry.

## Source URLs

All six open (HTTP 200) and are the stated works:

| Source | URL | What it opens |
|---|---|---|
| ayn-ed | https://shamela.ws/book/1682 | Card: al-Makhzūmī–al-Sāmarrāʾī, al-Hilāl, 8 vols, printed pagination |
| ayn-intro | https://shamela.ws/book/1682/37 | vol. 1, p. 47 [مقدمة الكتاب] |
| muzhir | https://shamela.ws/book/6936/55 | vol. 1, p. 61 |
| maqayis-ed | https://shamela.ws/book/21710/47 | vol. 1, p. 3 (author's preface) |
| haywood | https://archive.org/details/in.gov.ignca.12555 | Haywood 1960 (Brill); djvu text holds every cited page |
| hawramani | https://arabiclexicon.hawramani.com/al-khalil-b-ahmad-al-farahidi-kitab-al-ain/ | Landing page of the stored text's source |

Every listed source is cited and was consulted.

## Validator

`node scripts/validate-dictionary-guides.mjs kitab-al-ayn` → **ok, 1/1 guides pass**. It reports:

- 12 root links (7 distinct root/dictionary pairs)
- 7 excerpts
- 1,096 words
- two expected warnings for the `none` links (Eml, rHm), both explained in the sentence

## Site-data issues (report only; not edited)

1. **Title spelling.** The stored label is "Kitāb al-ʿAin" (following hawramani); the guide uses *al-ʿAyn*. Consider aligning the site label.
2. **Author label.** The stored author is "al-Khalīl al-Farāhīdī", with no mention of al-Layth's transmission (ayn-intro p. 48) or the authorship dispute (Muzhir vol. 1, pp. 62–67).
3. **Date.** The stored date 786 = 170 AH is one of two reported death dates; the other is 175 AH / 791 CE (Muzhir vol. 1, p. 66). Fine for ordering.
4. **English of multi-root chapters covers only the headword root** (Ebd 372, Hrm 1622), and the Ebd harmonized text does not say so. The guide discloses this.
5. **The harmonized English attributes content directly to al-Khalīl** ("Al-Khalīl reads Q 43:81…"). Given the disputed authorship and the ambiguity of "qāla l-Khalīl" (Haywood p. 27; Muzhir p. 63), "the ʿAyn" would be safer.
6. **The stored text drops the editors' footnotes**, so readers cannot tell which bracketed words came from the Tahdhīb. It also drops some heading brackets (ktb).
