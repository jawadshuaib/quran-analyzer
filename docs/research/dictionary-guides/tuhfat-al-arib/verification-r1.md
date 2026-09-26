# Verification round 1: tuhfat-al-arib

Guide checked: `roots/frontend/src/content/dictionary-guides/guides/tuhfat-al-arib.ts`
Checker: independent fact-check, round 1 (2026-09-26). I did not open research-notes.md or any revision file.

## Sources opened

- **Tuḥfa, Shamela 13304.** The book card reads: ed. Samīr al-Majdhūb, al-Maktab al-Islāmī, 1st ed. 1403/1983, 326 pp., "ترقيم الكتاب موافق للمطبوع". I downloaded all text pages (ids 3–288, printed pp. 40–326) and compared them with the database. The editor's introduction (pp. 3–39) is not in the Shamela text.
  - Author's introduction: id 3 = printed p. 40.
  - ح ل م: id 67 = p. 104.
  - "كما في ظ": id 16 = p. 53.
  - Colophon: id 288 = p. 326, "تم بتاريخ سنة ٩٤٣".
- **Ziriklī, *al-Aʿlām*, Shamela 12286/6389.** The page is vol. 7, p. 152, entry "أبو حيان النحوي", 15th ed., Dār al-ʿIlm li-l-Malāyīn, 2002.
- **al-Baḥr al-Muḥīṭ, Shamela 23591.** The card reads Dār al-Fikr 1420/2000, 11 vols, prepared by Ṣidqī al-ʿAṭṭār, Zuhayr Juʿayd and ʿIrfān Ḥassūna, paginated as printed. Pages checked:
  - id 7 = vol. 1, p. 10
  - id 9 = vol. 1, p. 12
  - id 1754 = vol. 3, p. 333
  - id 1794 = vol. 3, p. 373
  - id 6050 = vol. 10, p. 419
- **Hatib & Tekin, DergiPark article 1152423.** I read the full PDF (download/article-file/2570046). The printed journal page 55 is PDF p. 9.
- **arabiclexicon.hawramani.com.** The work's index page returns HTTP 200.
- **Local data.** `_dict_guide_tool.py entry …`, SQL counts over the 1,081 displayed entries (same filter as the tool), and `morphology` rows for 3:146, 23:76, 81:24 and ʿābidūn.

## Claims

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Tuḥfat al-Arīb* / titleAr تحفة الأريب بما في القرآن من الغريب | SUPPORTED | Shamela 13304 card: "تحفة الأريب بما في القرآن من الغريب" |
| C2 | titleGloss "A Gift for the Discerning: On the Unfamiliar Words in the Qurʾān" | SUPPORTED | Fair rendering of the verified title (interpretive gloss) |
| C3 | author / authorAr / authorFull (Athīr al-Dīn Abū Ḥayyān Muḥammad b. Yūsuf b. ʿAlī b. Yūsuf b. Ḥayyān al-Gharnāṭī al-Andalusī) | SUPPORTED | Ziriklī vol. 7 p. 152: "محمد بن يوسف بن علي بن يوسف ابن حيان الغرناطي الأندلسي الجياني، النفزي، أثير الدين، أبو حيان"; Tuḥfa p. 40: "أثير الدين أبو حيان الأندلسي" |
| C4 | period 654–745 AH / 1256–1344 CE | SUPPORTED | Ziriklī: "(٦٥٤ - ٧٤٥ هـ = ١٢٥٦ - ١٣٤٤ م)" |
| C5 | kind "Glossary of Qurʾānic gharīb" | SUPPORTED | Tuḥfa p. 40, introduction: the book is on the part of the vocabulary people "سموه: غريب القرآن" |
| C6 | summary: Andalusian grammarian and exegete who worked in Cairo | SUPPORTED | Ziriklī ("من كبار العلماء بالعربية والتفسير … أقام بالقاهرة"); Baḥr vol. 1 p. 10 |
| C7 | summary/lede: entries quote the Qur'anic form and usually give a one- or two-word equivalent, seldom with evidence; for most roots a single line | SUPPORTED | DB count: 1,605 braced glosses, of which 73% have a first clause of ≤ 2 words and 83% of ≤ 3 words. 1,069/1,081 entries have braces. Median stored length is 40 characters |
| C8 | summary/lede: a gloss is often the sense in one particular verse, and the entry does not name the verse | SUPPORTED | Hatib & Tekin p. 55: "مقتصراً على الألفاظ الموجودة في القرآن الكريم فقط دون ذكر الآية الواردة فيها، وشرح معناها اللغوي وما يتعلق بمعناها في السياق القرآني"; context-bound glosses such as Amm ({لبإمام}: طريق. {بإمامهم}: كتابهم) and Znn |
| C9 | lede: he set out to explain only the words ordinary Arabic speakers would not understand | SUPPORTED | Tuḥfa p. 40 (the two-kinds passage) |
| C10 | born near Granada 654/1256; after travelling, settled in Cairo; died there blind, 745/1344 | SUPPORTED | Ziriklī: "ولد في إحدى جهات غرناطة، ورحل إلى مالقة. وتنقل إلى أن أقام بالقاهرة. وتوفي فيها، بعد أن كف بصره" |
| C11 | late 710 (1311) appointed to teach tafsīr there and began *al-Baḥr* [bahr vol. 1 p. 10] | SUPPORTED | Baḥr 1:10: "بانتصابي مدرسا في علم التفسير في قبة السلطان الملك المنصور … في أواخر سنة عشر وسبعمائة … فعكفت على تصنيف هذا الكتاب" |
| C12 | "The *Tuḥfa* is a far smaller book, with no date of composition." | NEEDS QUALIFICATION | The author's own text gives no composition date. But the only date in the printed text is a colophon, "تم بتاريخ سنة ٩٤٣" (p. 326), which is a copying date. The editor's introduction (pp. 3–39) was not seen, so a scholarly dating cannot be excluded |
| C13 | Arabic quotation of the introduction (لغات القرآن العزيز على قسمين …) [tuhfa p. 40] | SUPPORTED | Verbatim on Shamela id 3, printed p. 40 |
| C14 | Translation of the introduction | SUPPORTED | Accurate. "Speak Arabic" renders المستعربة loosely; acceptable |
| C15 | He calls it a *mukhtaṣar*, covering only the second kind, alphabetical by root letters, limited to explaining the word as it occurs in the Qur'an [p. 40] | SUPPORTED | "والمقصود في هذا المختصر … وأن نرتبه على حروف المعجم … معتبرا في ذلك الحروف الأصلية لا الزائدة مقتصرا … على شرح الكلمة الواقعة في القرآن العزيز" |
| C16 | The introduction names no intended readers or sources | SUPPORTED | The whole introduction is on p. 40; it names neither |
| C17 | Entry shape: Qur'anic word in braces, then its equivalent; no survey of the root's other words; no sura or verse number [hatib p. 55] | SUPPORTED | Hatib & Tekin p. 55 ("دون ذكر الآية"); DB entries |
| C18 | Printed chapters follow the first letter; within a chapter, roots are grouped by last letter [tuhfa pp. 41–74] | SUPPORTED | Printed pp. 41–59, hamza chapter: أبب أرب أوب / ألت أمت / أثث / أجج / أدد أحد … / أثر … / … ; pp. 94–109 (ḥāʾ) likewise. Note: Hatib p. 55 describes the order as "معتمداً الحرف الأخير ثم الأول", and the order of last letters inside the hamza chapter follows the Maghribi sequence (… م ن ف ق س ه و ي). See brief issues |
| C19 | "about half the 1,081 entries … run to forty Arabic characters or fewer" | SUPPORTED (wording) | 549/1,081 (51%) are ≤ 40 characters of stored text, counting headword, spaces and punctuation. Counting Arabic letters only gives 758 (70%) |
| C20 | "more than half gloss a single Qur'anic word with no alternative" | SUPPORTED | 628/1,081 (58%): one braced word and no قيل/يقال/أو |
| C21 | ظ ن ن excerpt and translation | SUPPORTED | Entry 1913: "ظنن : {بظنين}: بمتهم. {يظنون}: يوقنون." Translation accurate |
| C22 | Q 81:24 has two readings; three of the seven read ẓāʾ ("suspected"), the rest ḍād ("miserly") [bahr vol. 10 p. 419] | SUPPORTED | Baḥr 10:419: "ومن السبعة النحويان وابن كثير: بظنين بالظاء، أي بمتهم … وباقي السبعة: بالضاد، أي ببخيل" |
| C23 | The ḍād reading is the Qur'an text on al-nuqta | SUPPORTED | `morphology` 81:24:5: بِضَنِينٍ, root Dnn |
| C24 | The ض ن ن entry glosses the ḍād form "miserly" | SUPPORTED | Entry 18771: "{بضنين}: ببخيل" |
| C25 | *ẓanna* usually means suppose; "certain" fits Q 2:46 and would invert Q 45:24; contrast labelled "ours" | SUPPORTED | Verse texts confirmed (2:46 يظنون أنهم ملاقو ربهم; 45:24 إن هم إلا يظنون); labelled interpretation |
| C26 | al-Fayyūmī excerpt and translation (attributing the main sense to al-Azharī "and others") | SUPPORTED | Entry 1909: "الظَّنُّ … وَهُوَ خِلَافُ الْيَقِينِ قَالَهُ الْأَزْهَرِيُّ وَغَيْرُهُ وَقَدْ يُسْتَعْمَلُ بِمَعْنَى الْيَقِينِ كَقَوْلِهِ {…}" |
| C27 | Fayyūmī gives the usual sense and marks certainty as occasional; Abū Ḥayyān records only the exception | SUPPORTED | Entries 1909 and 1913 (وقد يستعمل = "is sometimes used") |
| C28 | Baḥr lists a word's meanings where it first occurs "so that one can see which of those meanings suits it in each place where it occurs" [vol. 1 p. 12] | SUPPORTED | Baḥr 1:12: "وإذا كان للكلمة معنيان أو معان، ذكرت ذلك في أول موضع فيه تلك الكلمة، لينظر ما يناسب لها من تلك المعاني في كل موضع تقع فيه"; translation accurate |
| C29 | The *Tuḥfa* "as we read it" usually gives the result of that choice without the list | SUPPORTED | Labelled interpretation, consistent with C20 (58% single gloss) |
| C30 | *istakānū* at Q 3:146 and Q 23:76 | SUPPORTED | `morphology` 3:146:18 and 23:76:5 ٱسْتَكَانُ (root kyn) |
| C31 | ك و ن excerpt translation: "noble [variant: sturdy]" | NEEDS QUALIFICATION | The Arabic matches entry 117. But in this edition square brackets mark the editor's corrections or normalisations (e.g. "[الصواب: آذن كما في ظ]", "الحيوة [الحياة]"), not variants. The Baḥr (3:333) quotes the line with جسرة ("ينباع من زفرى غضوب جسرة"). Calling [جسرة] a "variant" misdescribes the bracket |
| C32 | First analysis: Form X of k-w-n with a radical long vowel. Second: Form VIII from *sukūn* with the vowel drawn out, as a poet drew out *yanbaʿu* into *yanbāʿu* [bahr vol. 3 p. 333] | SUPPORTED | Entry 117; Baḥr 3:333: "ينباع من زفرى غضوب جسرة … يريد ينبع فمطل" |
| C33 | The glossary gives the second view with a bare *wa-qīla* and supplies its proof-text | SUPPORTED | Entry 117 |
| C34 | In the Baḥr on Q 3:146 he names al-Farrāʾ and a group of grammarians and argues against them: *ishbāʿ* is for poetry only, and the verb keeps its long vowel in all forms (*yastakīnu, mustakīn*) [bahr vol. 3 p. 373] | SUPPORTED | Baḥr 3:373: "وقال الفراء وطائفة من النحاة: أنه افتعل من السكون، وأشبعت الفتحة … وهذا الإشباع لا يكون إلا في الشعر. وهذه الكلمة في جميع تصاريفها بنيت على هذا الحرف تقول: استكان يستكين فهو مستكين ومستكان له" |
| C35 | "Here, at least, the *Tuḥfa*'s *wa-qīla* reports a view without endorsing it." | SUPPORTED | Hedged inference from C34. (Same page also gives a third derivation from k-y-n, from al-Azharī and Abū ʿAlī; the essay omits it. See brief issues) |
| C36 | Most glosses don't say whether they give ordinary usage or a commentator's reading; a few do | SUPPORTED | grep: only Ebd, mEn, Swr ("وفي التفسير") and Hnf mark such layers |
| C37 | ع ب د excerpt and translation | SUPPORTED | Entry 368, verbatim; translation accurate |
| C38 | *ʿābidūn* occurs in several verses incl. Q 2:138 and Q 23:47; the lexical sense fits 23:47 "in our reading" | SUPPORTED | `morphology`: Ea(bid) at 2:138, 9:112, 21:53, 21:73, 21:84, 21:106, 23:47, 43:81, 66:5, 109:3–5; labelled interpretation |
| C39 | م ع ن excerpt and translation | SUPPORTED | Entry 16654 |
| C40 | That entry gives no evidence and doesn't say which sense Q 107:7 intends | SUPPORTED | Entry 16654 |
| C41 | *wa-qīla*/*yuqāl* introduce alternatives, almost always unattributed; about one entry in eight; only a handful name anyone | SUPPORTED (approx.) | 134/1,081 (12.4%) contain قيل/يقال. Strict alternatives (وقيل/قد قيل/قيل:/ويقال:) are 110 (10.2%). Named authorities appear in about 7 entries: Hyy (Sībawayh), sfh (Yūnus, Abū ʿUbayda), qnTr (al-Farrāʾ), sjl (Abū ʿUbayda, Ibn ʿAbbās), $nA (Basrans/Kufans) |
| C42 | *aw* strings senses; the د ي ن translation | SUPPORTED | Entry 1387; translation accurate |
| C43 | "A recent study says the *Tuḥfa* gives no poetic evidence, no differing views and no attributions, beyond occasional notes on dialects and readings." [hatib p. 55] | NEEDS QUALIFICATION | p. 55: "دون ذكر الشواهد أو الآراء المختلفة أو نسبة الأقوال إلى قائليها، لكنه قد يشير في بعض الأحيان إلى لهجات القبائل أو إلى اختلاف المعنى باختلاف القراءات". *Shawāhid* means proof-texts or attestations in general, not specifically poetry. Also, the article's footnote 31 points to the editor's introduction (Tuḥfa pp. 35–36), so the description may come from the editor |
| C44 | "That holds for most entries, though not, as *istakānū* shows, for all." | SUPPORTED | True as stated, but understated: about 110 entries report alternative views and about 7 name authorities (see C41) |
| C45 | The gloss was written "some seven centuries after the Qur'an" | SUPPORTED | Author d. 745/1344 |
| C46 | onOurSite: arabiclexicon.hawramani.com does not say which edition it used | SUPPORTED | The index page names no edition or editor |
| C47 | Every displayed entry matches the wording of the Majdhūb 1983 Shamela text, including bracketed corrections ("as in ظ") | SUPPORTED | Comparison of all 1,081 displayed entries with Shamela pp. 41–326 (diacritics and punctuation normalised): 1,079 match exactly. Ayy and swr each join two same-headword printed entries, and both parts match. Adn entry = p. 53 "[الصواب: آذن كما في ظ]" |
| C48 | "apparently a manuscript siglum" | SUPPORTED (hedged) | Plausible and hedged. The editor's introduction, which would confirm it, is not online |
| C49 | Printed before at Ḥamāh 1926 and in 1977 [hatib p. 55] | SUPPORTED | p. 55: first printing at Ḥamāh 1926 under Muḥammad Saʿīd al-Naʿsānī; second 1977, ed. Aḥmad Maṭlūb and Khadīja al-Ḥadīthī; third 1983, Majdhūb. (The article's Hijri years are garbled; the essay uses CE only) |
| C50 | Braces and square brackets belong to the modern text, not to Abū Ḥayyān | SUPPORTED | Brackets hold editorial "[الصواب: …]" corrections; braces are the digital Qur'an markup |
| C51 | 1,081 roots displayed | SUPPORTED | `_dict_guide_tool.py`/SQL: 1,081 |
| C52 | "A few headwords of the printed book have no entry here" | NEEDS QUALIFICATION | About 55 of about 1,140 printed headwords are absent from our data. Examples: أيك أرم ألي برزخ بكك بوس تخذ ثمد حصص رجأ سبأ سندس عدن عرجون فردس قطن كلاء مرو منو نجل نمرق ويل يئس. Hawramani's own index lists several of them (أيك, بكك, برزخ). "A few" understates |
| C53 | ح ل م is a heading with nothing under it, as in the printed text [p. 104] | SUPPORTED | Entry 4683 "حلم :"; Tuḥfa p. 104 "[حلم]" |
| C54 | Our word pages file *istakānū* under ك ي ن, where the *Tuḥfa* has no entry; its gloss is under ك و ن | SUPPORTED | `morphology` root kyn; no kyn entry in this dictionary; entry 117 under kwn |
| C55 | Source `tuhfa` citation (Majdhūb, al-Maktab al-Islāmī, 1st ed. 1403/1983, paginated as printed) | SUPPORTED | Shamela card |
| C56 | Source `hatib` citation (title, journal 7/2, 2022, pp. 47–65, DOI) | SUPPORTED | PDF header title "الأثر اللغوي للغريب في كتاب تحفة الأريب لأبي حيان الأندلسي" (the DergiPark metadata omits للغريب); DOI 10.56108/ujte.1152423 |
| C57 | Sources `zirikli` and `bahr` citations (editions, vol./page) | SUPPORTED | Shamela cards for 12286 and 23591 |

**Totals:** 57 claims. 53 supported, 4 need qualification, 0 unsupported.

## Flagged items and fixes

- **C12 (body, "Two kinds of words").** "The *Tuḥfa* is a far smaller book, with no date of composition."
  - Fix: "The *Tuḥfa* is a far smaller book, and its text gives no date of composition."
  - Optional addition: "the one date in the printed text, 943 AH at the end, is a copyist's."
- **C31 (kwn excerpt translation).** "[variant: sturdy]" misdescribes an editorial bracket.
  - Fix: render as "noble [editor's bracket: sturdy]", or "noble (the modern edition adds in brackets 'sturdy', the wording in other sources)". Do not call it a variant.
- **C43 ("Reading it well").** "no poetic evidence" narrows *shawāhid*.
  - Fix: "A recent study says the *Tuḥfa* cites no supporting texts (*shawāhid*), reports no differing views and names no authorities, apart from occasional notes on dialects and readings[^hatib|p. 55]."
  - Optionally make the following sentence concrete: "That holds for most entries, but about one in ten reports an alternative view, and a handful name authorities such as Sībawayh, al-Farrāʾ or Abū ʿUbayda."
- **C52 (onOurSite).** "A few headwords of the printed book have no entry here" understates the gap.
  - Fix: "About fifty headwords of the printed book (for example عدن, ويل, برزخ) have no entry here."

## Brief issues (non-factual)

- **suggestion — length.** 1,099 words (lede + body), at the ceiling of the range, for a one-line glossary with thin secondary literature. The task asked for a proportionate essay. Consider trimming, e.g. merge the ʿ-b-d and m-ʿ-n passages or shorten "Reading it well", to about 800–900 words.
- **suggestion — C19 wording.** "forty Arabic characters" is measured on the whole stored line (headword, spaces, punctuation). Say "forty characters" or "a line of about forty characters" to avoid a count readers can't reproduce.
- **suggestion — the Baḥr's third derivation.** Baḥr 3:373 also records a derivation of *istakāna* from k-y-n (from al-Azharī and Abū ʿAlī). That is the root our word pages use. One clause in onOurSite or the kwn paragraph would explain why the word pages file it under ك ي ن, instead of implying the site simply differs.
- **suggestion — arrangement detail (verify before adding).** Within each printed chapter the last-letter order follows the Maghribi (Andalusian) alphabet (… م ن ف ق س ه و ي, visible on pp. 50–56). Hatib p. 55 describes the ordering as "last letter, then first". This could help a reader of the printed book, but is not needed for our site, where entries are per root.
- **suggestion — a missed recurring feature.** Several entries add an *aṣluhu* ("its origin is …") note giving a concrete underlying sense. Examples: Ent "العنت: الهلاك وأصله المشقة"; rkD; kwr; hll; dmg; fDD; Hnf. A sentence would round out the "how to read it" advice. Do not force it into an original-root-meaning narrative; it is occasional.
- **No must-fix brief issues found.** There is no generic praise or ranking, translations are labelled (by the excerpt block and "translation for this guide"), roots are linked, the kyn link uses `none` and the sentence explains why, and interpretations are marked ("The contrast is ours", "in our reading", "as we read it").

## URL check

| Source | URL | Result |
|---|---|---|
| zirikli | https://shamela.ws/book/12286/6389 | Opens; vol. 7 p. 152, "أبو حيان النحوي" |
| bahr | https://shamela.ws/book/23591 | Opens; Dār al-Fikr 1420/2000 |
| tuhfa | https://shamela.ws/book/13304 | Opens; Majdhūb 1983 |
| hatib | https://dergipark.org.tr/en/pub/ujte/article/1152423 | Opens; PDF downloadable |
| hawramani | https://arabiclexicon.hawramani.com/abu-hayyan-al-gharnati-tuhfat-al-arib-bi-ma-fi-l-quran-min-al-gharib/ | HTTP 200 |

All five sources were consulted and used. None is unused.

## Validator

`node scripts/validate-dictionary-guides.mjs tuhfat-al-arib` passes ("1/1 guides pass"):

- 10 root links, 5 excerpts, 1,099 words.
- One warning: kyn `none` link. The sentence does explain it ("where the *Tuḥfa* has no entry").

## Site-data issues

- The stored author label "Abū Ḥayyān al-Gharnāṭī" and date 1344 (death year 745/1344) are correct.
- **Scrape gap.** About 55 headwords of the printed *Tuḥfa* are not in `dictionary_entries` at all, and several are listed on hawramani's index (أيك, بكك, برزخ …). ثرى is in the DB but not displayed. The Shamela entry علل is just "....." in print.
- **Merged entries.** Entries Ayy and swr each join two separate printed entries with the same headword. This is harmless.
