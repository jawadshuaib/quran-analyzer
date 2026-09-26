# Kitāb al-ʿAyn: verification round 4 (independent fact-check)

Page checked: `roots/frontend/src/content/dictionary-guides/guides/kitab-al-ayn.ts`, the version after the final revision.
Checked 2026-09-26. I did not open research-notes.md or any revision-*.md file. I read verification-r3.md only for its list of flags. I re-fetched every source myself in this round (scratchpad folder `r4ayn/`). This round adds one new kind of evidence: **scans of the printed al-Makhzūmī–al-Sāmarrāʾī edition** (archive.org item `8_20210413_202104`, vols 1, 5 and 8). Before this round, the edition's brackets had been checked only in the Shamela digitisation.

## Evidence base (all opened in this round)

- **ayn-ed / ayn-intro (Shamela 1682).** Card: "المؤلف: أبو عبد الرحمن الخليل بن أحمد بن عمرو بن تميم الفراهيدي البصري (ت ١٧٠هـ) المحقق: د مهدي المخزومي، د إبراهيم السامرائي الناشر: دار ومكتبة الهلال عدد الأجزاء: ٨ [ترقيم الكتاب موافق للمطبوع]". I read these pages; each printed page number is taken from the page title.
  - vol. 1: pp. 16–18 (ids 12–14), 27 (23), 31–34 (27–30), 43–44 (35–36), and 47–60 (37–50, the whole introduction)
  - vol. 2: pp. 48–55 (ids 403–410)
  - vol. 5: pp. 341–342 (1913–1914)
  - vol. 8: pp. 162–164 (2933–2935)
- **Printed edition scans (archive.org `8_20210413_202104`).** The vol. 1 title page reads "سلسلة المعاجم والفهارس / كتاب العين … تحقيق الدكتور مهدي المخزومي الدكتور إبراهيم السامرائي", so it is the same edition with the same pagination. I rendered these pages with pdftoppm:
  - **vol. 5, p. 341** (PDF p. 341; the page number "٣٤١" is printed at the foot). The chapter heading "باب الكاف والتاء والباء معهما / ك ت ب، ك ب ت، ب ك ت، ت ب ك، ب ت ك مستعملات" is printed **without square brackets**. On the same page the editors' real additions do carry brackets: "[على ولد غيرها]" and "[وفراء غرفيةٍ … خوارزها]".
  - **vol. 8, p. 163.** The print shows "[ والظُّلْمةُ: ذهابُ النور، وجمعه الظُّلَمُ ]⁽٤٣⁾" and "[كما لا يجمع نظائره نحو السواد والبياض]⁽٤٤⁾". Fn 43: "ما بين القوسين من التهذيب من أصل العين"; fn 44: "زيادة أخرى من التهذيب من أصل العين".
  - **vol. 8, p. 164.** "ليلة ظلماء [ويوم مظلم]"; "والظُّلم: الشِّرك … إن الشرك لظلم عظيم"; then "لمظ".
- **muzhir (Shamela 6936).** Card: "فؤاد علي منصور، دار الكتب العلمية - بيروت، الأولى ١٤١٨هـ ١٩٩٨م، ٢ أجزاء"; the author is dated "(ت ٩١١هـ)". I read vol. 1, pp. 61–68 (ids 55–62).
- **maqayis-ed (Shamela 21710).** Card: "تحقيق وضبط: عبد السلام محمد هارون … مصطفى البابي الحلبي … الطبعة: الثانية (١٩٦٩ - ١٩٧٢ م) … ٦ أجزاء". I read vol. 1, pp. 3–5 (ids 47–49).
- **haywood (archive.org `in.gov.ignca.12555`).** Metadata: "Arabic lexicography / Haywood, John A. / 1960". I read both the djvu text and **page images of the PDF** (`12555.pdf`):
  - PDF p. 44 carries the running head "AL-KHALĪL IBN AḤMAD 27" and ends ch. III.
  - PDF p. 45 is the unnumbered opening page of "CHAPTER FOUR / KITĀB al-ʿAIN". The contents list ch. IV at p. 28.
  - PDF p. 46 carries the running head "KITĀB AL-ʿAIN 29".
  - Pages 26, 38, 39 and 43 were identified the same way, from the running heads.
- **hawramani.** https://arabiclexicon.hawramani.com/al-khalil-b-ahmad-al-farahidi-kitab-al-ain/ returns HTTP 200. Its blurb ("first dictionary … written by al-Khalīl … organized by … al-Layth") names no printed edition, editor or publisher.
- **Stored entries** (from `_dict_guide_tool.py entry`), all DISPLAYED:
  - Kitāb al-ʿAin: Ebd = 372, ESb, Zlm = 287, ktb = 21, Elm = 35, Hrm = 1622
  - Ibn Fāris: Zlm = 295
  - `root Eml` and `root rHm` list no al-khalil entry.
- **My own machine diff.** Stored Original Text against Shamela page text, after removing vowel marks, footnote markers and footnotes and normalising hamza seats and tāʾ marbūṭa:
  - Ebd: 1,134 = 1,134 tokens, identical.
  - Zlm: identical. The only differences are the neighbouring chapters' text on the same pages.
  - ktb: identical, except that Shamela wraps the heading in [ ].
- **My own DB count**, with the display filter used by the tool:
  - 505 displayed entries.
  - 430 begin with باب (after stripping a leading bracket or parenthesis).
  - 415 of those headings name the orders in use (مستعمل / يستعمل).
  - 23 have مهمل within their first 250 characters.
  - 307 headings list two or more letter orders.
  - The ص/ع blessing abbreviation occurs in Ebd, kvr, klm and hrb.
- **Validator:** ok, 1/1. The details are at the end of this report.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title *Kitāb al-ʿAyn* / titleAr كتاب العين | S | Shamela 1682 card "كتاب العين"; Maqāyīs vol. 1, p. 3 "المسمَّى (كتابَ العين)". |
| C2 | titleGloss: named after its first letter | S | ayn-intro p. 47: "فوجد العيْن ادخَلَ الحروف في الحَلْقِ، فَجَعَلهَا أوّل الكتابِ". |
| C3 | author: al-Khalīl, as transmitted by al-Layth ibn al-Muẓaffar | S | ayn-intro p. 48: "حدَّثني الليثُ بنُ المُظَفَّر بن نصر بن سَيَّار عن الخليل بجميع ما في هذا الكتاب". |
| C4 | authorFull Abū ʿAbd al-Raḥmān al-Khalīl ibn Aḥmad al-Farāhīdī al-Baṣrī | S | Shamela 1682 card (above). |
| C5 | authorAr الخليل بن أحمد الفراهيدي | S | Same card. |
| C6 | period: d. 170 or 175 AH / 786 or 791 CE | S | Muzhir vol. 1, p. 66: "تُوفِّيَ الخليل سنة سبعين ومائة وفي بعض الروايات سنة خمس وسبعين ومائة". The conversions are right to the start year. |
| C7 | kind "Sound-ordered root dictionary" | S | ayn-intro pp. 47–48, 57–58 (order by مخرج). |
| C8 | summary: letters ordered by where they are sounded; each root filed with its rearrangements | S | ayn-intro pp. 47–48, 58–59; Haywood p. 38 ("roots are dealt with anagrammatically, all permutations … grouped together"). |
| C9 | summary: everyday words beside Qur'anic citations and poetry | S | Haywood p. 39 ("did not invariably … omit common words which were familiar in everyday speech … frequently quotes examples from religious literature and poetry"); Qur'anic citations in Ebd and Zlm. |
| C10 | summary: who completed it is disputed | S | Muzhir vol. 1, pp. 62–67. |
| C11 | lede: ʿayn, which its introduction places deepest in the throat | S | ayn-intro p. 47 ("ادخَلَ الحروف في الحَلْقِ"); p. 57 ("فأقصى الحروف كلها العين"); p. 60 ("بالعين وهو أقصَى الحروف"). |
| C12 | lede: files each root with every rearrangement found in use | S | ayn-intro p. 59; Haywood p. 38 ("each entry begins with the formula 'al-mustaʿmal'"). |
| C13 | lede: oldest surviving attempt to take in the whole vocabulary by a system | S | ayn-ed vol. 1, p. 18: "والعين بهذا أول معجم في العربية ولعله معجم موعب"; Haywood p. 39 ("the first Arabic dictionary"), p. 43 ("the first exhaustive vocabulary"); Muzhir p. 61: "أولُ مَنْ صَنَّف في جَمْع اللُّغَةِ الخليلُ". |
| C14 | lede: voices of al-Khalīl, al-Layth and later hands | S | ayn-intro pp. 48, 50, 52; Muzhir p. 63 (Thaʿlab: "وقد حشا الكتاب أيضا قومٌ علماء"); p. 66 (additions). |
| C15 | §1: "translations on this page are this guide's own" | S | Editorial label. |
| C16 | §1: could not open with alif, a "weak" letter | S | ayn-intro p. 47: "لأن الألف حرف معتلّ". |
| C17 | §1: "tasted" the letters, *ab, at, aḥ, aʿ, agh* | S | ayn-intro p. 47: "وذاقَها … يَفْتَحُ فاهُ بالألفِ ثم يُظْهِرُ الحَرْفَ. نحو ابْ، اتْ، احْ، اعْ، اغْ". |
| C18 | §1: ʿayn deepest, made first; outward to mīm at the lips | S | ayn-intro p. 47 ("الأرفعُ فالأرفع حتى أتَى على آخرها وهو الميم"); p. 58 (ف ب م "شَفَويّة"). |
| C19 | §1: hamza "at the far end of the throat" | S | ayn-intro p. 52: "وأمّا الهَمْزة فَمَخْرَجُها من أقصَى الحَلْق". |
| C20 | §1: the editors favour a report passed on by Ibn Kaysān (ʿayn "clearer" than ḥāʾ) | S | ayn-ed vol. 1, p. 17: "لا لانها أول الحروف مخرجا، ولكنها أول الحروف نصاعة"; "قال ابن كيسان …: سمعت من يذكر عن الخليل … فوجدت العين أنصع الحرفين"; p. 18: "فالجواب عنه هو ما قدمناه من بيان، ومن نقل عن ابن كيسان". |
| C21 | §1: roots sorted by type (doubled, sound, weak, four-, five-letter) | S | ayn-ed vol. 1, p. 16 (six classes); Haywood p. 38. |
| C22 | §1: 6 / 24 / 120 arrangements | S | ayn-intro p. 59. |
| C23 | §1: "the used are written down and the unused discarded" | S | ayn-intro p. 59: "يُكَتَب مُسْتَعْمَلها. ويُلغى مُهْمَلها". It is said of the quadriliteral; the five-letter line reads "يُسْتَعْمَل أقَلُّه ويُلغى أكثره". The chapter headings show the same practice for triliterals ("مستعملات … مهملان"). "Of such arrangements" is acceptable. |
| C24 | §1: filed under whichever letter comes earliest | S | ayn-intro p. 47: "فمهما وَجَدتَ منها واحداً في الكتاب المقدَّم فهو في ذلك الكتاب". |
| C25 | §1 (labelled as the guide's reading): the permutations are a completeness check; the introduction never claims shared meaning | S | I read pp. 47–60 in full and found no shared-meaning claim. p. 47 "فلا يخرج منها عنه شيء". Haywood p. 39 calls the shared-meaning idea a later "false idea". |
| C26 | §1: quote بدأنا … الواضح والغريب, its translation, "words credited to al-Khalīl" | S | ayn-intro p. 60: "وقال الخليل: بَدَأَنَا في مُؤلَّفنا هذا بالعين وهو أقصَى الحروف، ونضُمُّ إليه ما بعده حتى نَسْتَوْعِبَ كلام العرب الواضحَ والغريب". The ellipsis is valid and the translation faithful. |
| C27 | §2: "This is what al-Khalīl ibn Aḥmad of Basra composed" | S | ayn-intro p. 47: "هذا ما ألفه الخليل بن أحمد البصريّ". |
| C28 | §2: al-Layth passes on "from al-Khalīl, everything in this book" | S | ayn-intro p. 48 (C3). |
| C29 | §2: "al-Layth said: al-Khalīl said"; al-Layth sometimes speaks as "I" | S | pp. 48, 57, 58, 59 ("قال الليث: قال الخليل"); p. 50 ("قال ليث: قلت لأبي الدقيش"); p. 52 ("قال الليث: قلت"). |
| C30 | §2: ESb excerpt and translation, inside the chapter filed under ع ص ب | S | Stored ESb (heading "باب العين والصاد والباء … ع ب ص مهملة") contains "قال الليث: قلت للخليل: ما علامة اسم التأنيث؟ قال: ثلاثة أشياء". |
| C31 | §2: al-Suyūṭī d. 911 AH / 1505 CE | S | Shamela 6936 card "(ت ٩١١هـ)". |
| C32 | §2: verdicts going back to the ninth century | S | Muzhir p. 63 (Isḥāq ibn Rāhawayh; Thaʿlab); pp. 66–67 (Abū Ḥātim, c. 250 AH). |
| C33 | §2: al-Azharī: al-Layth wrote it and used al-Khalīl's name so that it would sell | S | Muzhir p. 62: "عمِل كتاب العين ونسبَه إلى الخليل لينفق كتابه باسمه ويرغب فيه". |
| C34 | §2: others: al-Khalīl wrote up to ghayn, al-Layth finished | S | Muzhir p. 62: "عَمِلَ الخليلُ من كتاب العين قطعة من أوَّله إلى حرف الغين وكَمَّله الليث". |
| C35 | §2: al-Zubaydī, its abridger: al-Khalīl laid the foundation and died before finishing | S | Muzhir p. 64 ("مؤلف مختصر العين"); p. 65 ("أن الخليل سَبَّب أصله وثقَّف كلام العرب ثم هلَك قبل كَماله"). |
| C36 | §2: arrived from Khurāsān c. 250 AH; Abū Ḥātim rejected it; al-Khalīl's students had never heard of it | S | Muzhir pp. 66–67: "لما وَرَدَ كتابُ العَين من بلد خُراسان في زمن أبي حاتم أنكره"; "وقد غَبر أصحابُ الخليل … لا يعرفون هذا الكتابَ"; "فيما قارب الخمسين والمائتين لأن أبا حاتم تُوُفِّي سنة خمس وخمسين ومائتين". |
| C37 | §2: editors: in design and substance al-Khalīl's | S | ayn-ed vol. 1, p. 27: "أن كتاب العين بتأسيسه وبحشوه … إنما هو كتاب الخليل". |
| C38 | §2: Haywood: "will probably never be convincingly solved" (p. 26) | S | Haywood p. 26 (before the "27" running head on PDF p. 44). |
| C39 | §2: Haywood: "a major share at least in the planning" (p. 26) | S | Haywood p. 26, verbatim. |
| C40 | §2: al-Suyūṭī: al-Zubaydī's errors concern arrangement, word-formation and miscopying, not whether words are genuine; no bar to relying on it | S | Muzhir p. 68: "غالبُه من جهة التصريف والاشتقاق … وبعضُه ادعى فيه التصحيف وأما أنه يُخَطأ في لفظة من حيث اللغة … فمعاذَ الله … لا يمنعُ الوثوقَ بالكتاب". |
| C41 | §2: reading advice | S | Advice, paired with the dispute (C42–C43). |
| C42 | §2: one report has al-Layth call himself "al-Khalīl" | S | Muzhir p. 63: "وسمَّى نفسه الخليل … وإذا قال: وقال الخليلُ مطلقا فهو يحكي عن نفسه". |
| C43 | §2: Haywood calls the phrase "slightly ambiguous" [^haywood\|p. 27] | **NQ** | The quotation is exact, but it sits on **p. 28**, the opening page of ch. IV. See the evidence base: PDF p. 44 is headed 27 and ends ch. III; PDF p. 45 is the chapter opening (contents: ch. IV = p. 28); PDF p. 46 is headed 29. The locator is wrong (round 3 also missed this). |
| C44 | §3: Ebd heading excerpt and translation | S | Entry 372 = ayn-ed vol. 2, p. 48, verbatim. |
| C45 | §3: the entry also holds *baʿd* and *bidʿa*, in the Original Text only | S | Entry 372 has "بعد:" and "بدع:" sections; both English versions stop at al-ʿabādīd. |
| C46 | §3: begins with the human being; ʿabd excerpt and translation | S | Entry 372; vol. 2, p. 48. |
| C47 | §3: *ʿabada/yaʿbudu/ʿibāda* only of worshipping God; not *ʿabadahu* of a slave | S | vol. 2, p. 48: "فلا يقال إلا لمن يعبد الله … فلا يقال: عَبَدَه ولا يعبُد مولاه". |
| C48 | §3: Q 5:60 "is read in seven ways", each parsed | S | vol. 2, p. 49: "وتقرأ هذه الآية على سبعة أوجه" + seven readings. |
| C49 | §3 (labelled observation): at Q 5:60 the object is al-ṭāghūt | S | Entry gloss "عَبَدَ الطّاغوتَ من دون الله". |
| C50 | §3: ʿabad "disdain" excerpt and translation | S | vol. 2, p. 50, verbatim. |
| C51 | §3: Q 43:81 read through that sense; the verse rendering | S | vol. 2, p. 50, fn 6 "سورة الزخرف ٨١". |
| C52 | §3: a second explanation, no choice made | S | vol. 2, p. 50: "ويقال: … فلست بأوّل من عَبَدَ الله مِنْ أهلِ مكّة". |
| C53 | §3: a saying attributed to "the Commander of the Faithful" and a verse by an unnamed poet | S | vol. 2, p. 50: "ويروى عن أمير المؤمنين …"; "قال «٧»" with fn 7 "لم نهتد إلى القائل". |
| C54 | §3: first bidʿa definition "in religion and otherwise" | S | vol. 2, p. 54: "والبِدْعَةُ: اسم ما ابتدع من الدين وغيره". |
| C55 | §3: second bidʿa excerpt and translation; ص = blessing | S | vol. 2, p. 55, verbatim. |
| C56 | §3: second definition is, by its terms, later than the Qur'an | S | Wording "بعد رسول الله". |
| C57 | §3: this chapter gathers rather than theorises | S | Entry 372 read in full; the claim is scoped to this chapter. |
| C58 | §3: common reading of Q 2:117 judged "more correct" | S | vol. 2, p. 55: "وقراءة العّامة الرّفع [وهو] أولى بالصواب"; p. 54, fn 27 "سورة البقرة ١١٧". |
| C59 | §4: ẓ-l-m runs from *ẓalam* through snow, teeth, ostrich to wrongdoing | S | vol. 8, pp. 162–163 = entry 287. |
| C60 | §4: Zlm excerpt and translation | S | Entry 287 = vol. 8, p. 163, with valid ellipses. |
| C61 | §4: the section closes with "ẓulm is shirk" (Q 31:13), then *lamẓ* | S | vol. 8, p. 164 (Shamela and the print scan); entry 287 is identical. |
| C62 | §4: nowhere says how the senses hang together | S | Entry 287 read in full. |
| C63 | §4: Ibn Fāris names the ʿAyn first among the five books the Maqāyīs rests on | S | Maqāyīs vol. 1, p. 3: "فأعلاها وأشرفُهَا كتابُ … الخليل بن أحمد، المسمَّى (كتابَ العين)"; p. 5: "فهذِه الكتبُ الخمسةُ معتمَدُنَا". |
| C64 | §4: Ibn Fāris cites al-Khalīl once | S | Entry 295 names al-Khalīl once: "مَا حَكَاهُ الْخَلِيلُ". |
| C65 | §4: Ibn Fāris excerpt and translation | S | Entry 295, verbatim. |
| C66 | §4: dug ground and slaughtered camel filed under his second root | S | Entry 295: "وَالْأَصْلُ الْآخَرُ … وَالْأَرْضُ الْمَظْلُومَةُ … وَإِذَا نُحِرَ الْبَعِيرُ مِنْ غَيْرِ عِلَّةٍ فَقَدْ ظُلِمَ". |
| C67 | §4: the senses are already in the ʿAyn; the two-root theory is Ibn Fāris's | S | Entries 287 and 295. |
| C68 | §4 (revised in r4): the bracketed ẓulma definition was restored by the editors from al-Azharī's Tahdhīb, which quotes the ʿAyn | S | **Printed vol. 8, p. 163 (scan)**: bracket + fn 43 "ما بين القوسين من التهذيب من أصل العين"; vol. 1, p. 44, item 7: "ووضعنا ما اقتضى السياق زيادته بين معقوفتين". The over-precise ẓalām clause (r3 C69) is gone. |
| C69 | §4 (labelled observation): "ẓulm is shirk" turns the verse into a definition | S | Entry text; Q 31:13. |
| C70 | §5: date ≠ date of evidence; bidʿa shows it | S | C56. |
| C71 | §5: copies with additions; al-Zubaydī found some citing Abū ʿUbayd, who was 16 or 21 when al-Khalīl died | S | Muzhir p. 66: "اختلافُ نُسَخِه واضطرابُ رواياته … أخبرنا المسعري عن أبي عُبيد … وأبو عبيد يومئذ ابنُ ست عشرة سنة. وعلى الرواية الأخرى ابن إحدى وعشرين". |
| C72 | §5: our text rests on much later manuscripts | S | ayn-ed vol. 1, pp. 31–34 (1054, 1087 and 1350/1354 AH). |
| C73 | §5: an entry maps range, not verse sense | S | Reading advice. |
| C74 | §5: each chapter stored under its opening root; *ʿamal* inside ع ل م | S | Entry 35 heading "ع ل م، ع م ل، م ع ل، ل م ع مستعملات"; its English covers ʿamal. I spot-checked grb, Hrb, nHt and mDg: in each, the stored root is the one whose section opens the stored text. |
| C75 | §5: *raḥma* inside ح ر م (Original Text only) | S | Entry 1622 heading lists ر ح م; "رحم: الرَّحمن الرَّحيم: اسمانِ مُشتَقّانِ من الرَّحْمة". Its English says "this digest covers the ḥ-r-m section only". |
| C76 | §5: root pages ع م ل and ر ح م have no entry from this dictionary | S | `root Eml`, `root rHm`. |
| C77 | onOurSite: stored text matches the al-Makhzūmī–al-Sāmarrāʾī edition word for word in Ebd, Zlm, ktb | S | My diff (evidence base). |
| C78 | onOurSite: hawramani does not name its source | S | Landing page. |
| C79 | onOurSite: three late manuscripts, oldest copied 1054 AH (1644–5 CE) | S | ayn-ed vol. 1, p. 31: "سنة اربع وخمسين وألف … لانها أقدم النسخ الثلاث". |
| C80 | onOurSite: editors reordered entries within chapters | S | ayn-ed vol. 1, pp. 43–44, item 6: "رأينا في ترتيب المفردات داخل أبوابها اضطرابا … فأرجعناها إلى الترتيب الاصيل". |
| C81 | onOurSite: square brackets mark their additions, some from the Tahdhīb; footnotes not shown | S | vol. 1, p. 44, item 7; vol. 8, p. 163, fnn 43–44 (print scan); vol. 5, p. 341, fn 2 "تكملة من التهذيب ١٠/ ١٥١ عن العين" (print scan). The stored texts carry no footnotes. |
| C82 | onOurSite: "At least one heading they supplied in brackets, that of ك ت ب, appears without them" [^ayn-ed\|vol. 5, p. 341] | **U** | **Contradicted by the printed page.** The scan of vol. 5, p. 341 prints the heading "باب الكاف والتاء والباء معهما / ك ت ب … مستعملات" with no brackets, while the editorial additions on the same page are bracketed. The brackets exist only in the Shamela digitisation, which also brackets its own section titles (e.g. "[مقدمة الكتاب]", "[وصف نسخ كتاب العين]", "[منهجنا في التحقيق]"). The editors did not supply this heading in brackets, so the stored text did not drop any editorial bracket here. Round 3 accepted this claim on the Shamela evidence alone. |
| C83 | onOurSite: 505 entries displayed | S | `dicts` and my direct count. |
| C84 | onOurSite (revised in r4): most are whole chapters headed by the letter orders "in use" (مستعملات) | S | 430/505 begin with باب; 415 headings name the orders in use. Haywood p. 38: "each entry begins with the formula 'al-mustaʿmal' (in use)". The revision fixes r3's C85. |
| C85 | onOurSite: one entry can cover several roots; many roots have no entry | S | 307 headings list ≥2 orders (e.g. Ebd, Elm, Hrm, ktb); Eml and rHm have none. |
| C86 | onOurSite: the English may cover only the opening root | S | 372 and 1622 are partial; 35 covers ʿamal ("may" is right). |
| C87 | onOurSite: occasionally ص or ع abbreviates a blessing formula | S | `grep`: ص in Ebd, kvr, hrb; ع in klm. |
| C88 | Source: Haywood, *Arabic Lexicography …* (Leiden: Brill, 1960), chs 3–5 | S | Title page and "Copyright 1960 by E. J. Brill"; cited pp. 26 (ch. III), 28, 38, 39 (ch. IV), 43 (ch. V). |
| C89 | Source: ayn-ed, 8 vols, Dār wa-Maktabat al-Hilāl, Shamela with printed pagination; chapters cited | S | Shamela 1682 card; the chapter page ranges match the page titles. |
| C90 | Source: Muzhir, ed. Fuʾād ʿAlī Manṣūr, 1998, vol. 1, pp. 61–68, quoting al-Sīrāfī, al-Azharī, Thaʿlab, al-Zubaydī and others | S | Shamela 6936 card; al-Sīrāfī p. 62, al-Azharī p. 62, Thaʿlab pp. 62–63, al-Zubaydī pp. 64–68. |
| C91 | Source: Maqāyīs ed. Hārūn, 6 vols, al-Bābī al-Ḥalabī, 2nd ed., 1969–72 | S | Shamela 21710 card. |
| C92 | Source: hawramani, "names no printed edition" | S | Landing page. |

**Totals: 92 claims. 90 supported, 1 needs qualification, 1 unsupported.**

## Status of round-3 flags

| Round-3 flag | Now | Verdict |
|---|---|---|
| C69 "but the next line, on ẓalām, is manuscript text" | Clause deleted; the sentence keeps only the ẓulma bracket (C68) | fixed. The print scan confirms fn 43 and fn 44. |
| C85 headings list "in use" and "unused" orders | Now "headed by the letter orders 'in use' (مستعملات)" (C84) | fixed. My count gives 415 of 505 headings naming the orders in use. |

The reviser reported no new claims, and I found none. Both edits are pure deletions or narrowings, and neither removed a needed qualification.

## Flagged items and fixes

1. **C82 (onOurSite, ك ت ب heading). UNSUPPORTED.**
   - The printed edition (vol. 5, p. 341, scan) sets the heading without square brackets. The brackets appear only in Shamela's digitisation, which marks its own headings that way.
   - Fix: delete the sentence "At least one heading they supplied in brackets, that of [[root:ktb|…|ك ت ب]], appears without them.[^ayn-ed|vol. 5, p. 341]".
   - Keep ك ت ب in the first sentence's list of compared chapters; that comparison (C77) holds.
   - If you want a ك ت ب example of a bracket, use one that is in the print: "[على ولد غيرها]" is an editors' addition "تكملة من التهذيب ١٠/ ١٥١ عن العين" (fn 2). The stored text shows it in brackets, but the footnote is not shown. The existing sentence "Square brackets mark their additions … the footnotes explaining them are not shown" already covers this, so deletion alone is enough.
   - The ayn-ed source citation can keep "كتب, vol. 5, pp. 341–342": it still supports C77.
2. **C43 (§2, Haywood "slightly ambiguous"). NEEDS QUALIFICATION (locator).**
   - The quotation is on p. 28, the first page of ch. IV, not p. 27.
   - Fix: change `[^haywood|p. 27]` to `[^haywood|p. 28]`.

## Brief (non-factual) issues

- **None must-fix.**
- **suggestion.** After C82 is deleted, onOurSite is about 150 words, within the ≈60–150 guidance, and it loses no reader-relevant fact.
- **suggestion.** `lastVerified` is not set in the file. FORMAT.md says the final verification round sets it; the reviser should add it once the two fixes above are made.
- **suggestion (carried over from r3, optional).** Several other darkness lines in ẓ-l-m are also bracketed Tahdhīb additions: "[ويوم مظلم]", and in Shamela's numbering also the أظلم علينا البيت line. The guide no longer makes any claim about them, so nothing is needed.
- Checked with no problem found:
  - Length is 1,087 words (validator), inside 700–1,100.
  - Every root mention is linked, and the two `none` links (Eml, rHm) are explained in the sentence.
  - The Ibn Fāris comparison is linked in both dictionaries.
  - Every excerpt and inline rendering is labelled as the guide's translation.
  - There is no ranking or generic praise.
  - It does not force an "original root meaning" narrative: it says Ibn Fāris's two-root theory is his, not the ʿAyn's.
  - Material the English lacks is flagged "Original Text only".
  - The essay separates the introduction's voice, al-Layth's, the editors', al-Suyūṭī's and Haywood's.

## Source URLs

All six open (HTTP 200) and are the stated works. Every listed source is cited in the text and was consulted.

| Source | URL | What it opens |
|---|---|---|
| ayn-ed | https://shamela.ws/book/1682 | Card: al-Makhzūmī–al-Sāmarrāʾī, al-Hilāl, 8 vols, printed pagination |
| ayn-intro | https://shamela.ws/book/1682/37 | vol. 1, p. 47 [مقدمة الكتاب] |
| muzhir | https://shamela.ws/book/6936/55 | vol. 1, p. 61 |
| maqayis-ed | https://shamela.ws/book/21710/47 | vol. 1, p. 3 (author's preface) |
| haywood | https://archive.org/details/in.gov.ignca.12555 | Haywood 1960 (Brill); PDF and djvu text hold every cited page |
| hawramani | https://arabiclexicon.hawramani.com/al-khalil-b-ahmad-al-farahidi-kitab-al-ain/ | Landing page of the stored text's source |

One caution for future rounds: the Shamela digitisation of this edition brackets some chapter headings that are unbracketed in print, as the vol. 5 heading here shows. Any claim about the editors' brackets should be checked against the printed page. The archive.org scans (`8_20210413_202104`) serve for this.

## Validator

`node scripts/validate-dictionary-guides.mjs kitab-al-ayn` → **ok, 1/1 guides pass**. It reports:

- 12 root links (7 distinct root/dictionary pairs)
- 7 excerpts
- 1,087 words
- example roots ESb, Ebd, Zlm, Elm, Hrm, ktb
- two expected warnings for the `none` links (Eml, rHm), both explained in the sentence

## Site-data issues (report only; not edited)

1. **Title spelling.** The stored label is "Kitāb al-ʿAin" (following hawramani); the guide uses the standard *al-ʿAyn*. Consider aligning the site label.
2. **Author label.** The stored author, "al-Khalīl al-Farāhīdī", omits al-Layth's transmission (ayn-intro p. 48) and the authorship dispute (Muzhir vol. 1, pp. 62–67).
3. **Date.** The stored 786 (= 170 AH) is one of two reported death dates; the other is 175 AH / 791 CE (Muzhir vol. 1, p. 66). It is fine for ordering.
4. **Harmonized English attributes content directly to al-Khalīl** (Ebd: "Al-Khalīl notes…", "Al-Khalīl reads Q 43:81…"; Zlm: "al-Khalīl equates ẓulm with shirk"). Its header reads "From Kitāb al-ʿAin (al-Khalīl al-Farāhīdī, d. 786)". Given the disputed authorship, "the ʿAyn" would be safer.
5. **English of multi-root chapters covers only the headword root** (Ebd 372, Hrm 1622). Hrm says so; Ebd does not. The guide discloses this.
6. **The stored text drops the editors' footnotes**, so readers cannot tell which bracketed words came from the Tahdhīb.
