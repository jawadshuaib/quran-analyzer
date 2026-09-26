# Verification round 2: al-misbah-al-munir

This is an independent fact-check of `roots/frontend/src/content/dictionary-guides/guides/al-misbah-al-munir.ts` as it stands after revision r1.

I did not open research-notes.md or revision-r1.md. I read verification-r1.md only to see which points had been flagged.

- **Sources.** Every source was re-opened for this round, with curl, WebFetch or the Wayback copy.
- **Entries.** Every example entry was read with `_dict_guide_tool.py entry`.
- **Counts.** Every count was re-run over the 901 displayed entries.

## Evidence opened (keys used in the table)

**Sources on the work and its author**

- **INTRO**: the introduction on Wikisource, fetched as raw wikitext (`action=raw`) from the listed page.
  - It contains the full muqaddima.
  - It contains the rule for filing a word whose middle root letter is hamza (*medial hamza*): "وَإِنْ وَقَعَتِ الْهَمْزَةُ عَيْنًا وَانْكَسَرَ مَا قَبْلَهَا جَعَلْتُهَا مَكَانَ الْيَاءِ … وَإِنِ انْضَمَّ مَا قَبْلَهَا جَعَلْتُهَا مَكَانَ الْوَاوِ … وَكَذَا إنِ انْفَتَحَ مَا قَبْلَهَا لِأَنَّهَا تُسَهَّلُ إلَى الْأَلِفِ وَالْأَلِفُ الْمَجْهُولَةُ كَوَاوٍ كَالْفَأْسِ وَالرَّأْسِ".
- **KH711 / KH712 / KH684**: Shamela book 12145, pages 3531, 3532 and 3503. Their page-number fields read vol. 2, pp. 711, 712 and 684.
  - p. 711: "وَقَدْ اقْتَصَرْتُ فِي هَذَا الْفَرْعِ أَيْضًا عَلَى مَا يَتَعَلَّقُ بِأَلْفَاظِ الْفُقَهَاءِ وَسَلَكْتُ فِي كَثِيرٍ مِنْهُ مَسَالِكَ التَّعْلِيمِ لِلْمُبْتَدِئِ وَالتَّقْرِيبِ عَلَى الْمُتَوَسِّطِ".
  - p. 711: "وَهَذَا مَا وَقَعَ عَلَيْهِ الِاخْتِيَارُ مِنْ اخْتِصَارِ الْمُطَوَّلِ وَكُنْتُ جَمَعْتُ أَصْلَهُ مِنْ نَحْوِ سَبْعِينَ مُصَنَّفًا … فَمِنْ ذَلِكَ التَّهْذِيبُ لِلْأَزْهَرِيِّ … وَدِيوَانُ الْأَدَبِ" (the list continues on p. 712 with "لِلْفَارَابِيِّ وَالصِّحَاحُ لِلْجَوْهَرِيِّ").
  - p. 712: "وَسَمَّيْتُهُ غَالِبًا فِي مَوَاضِعِهِ حَيْثُ يُبْنَى عَلَيْهِ حُكْمٌ".
  - p. 712, colophon: "فِي الْعَشْرِ الْأَوَاخِرِ مِنْ شَعْبَانَ الْمُبَارَكِ سَنَةَ أَرْبَعٍ وَثَلَاثِينَ وَسَبْعِمِائَةٍ".
  - p. 684 opens "[الْخَاتِمَةُ]" with verb morphology.
- **SH-CARD**: the Shamela 12145 book card.
  - "الناشر: المكتبة العلمية - بيروت، عدد الأجزاء: ٢ (متسلسلة الترقيم)".
  - Author line: "الفيومي ثم الحموي، أبو العباس (ت نحو ٧٧٠ هـ)".
  - Description: "شرح فيه ألفاظ الفقه على المذهب الشافعي".
- **SH-ATY / SH-RWY**: Shamela 12145, pages 17 and 1253.
  - Page 17 is "(ء ت ي)". It has "قَالَ الشَّاعِرُ (١)" with the footnote "(١) العَجَّاجُ.".
  - Page 1253 is "(ر وي)", vol. 1 pp. 246–247. It contains "وَرَأَيْتُ الشَّيْءَ رُؤْيَةً أَبْصَرْتُهُ بِحَاسَّةِ الْبَصَرِ".
- **DURAR**: Shamela 6674/371. The page field reads vol. 1, p. 372, and this is entry ٧٨٧.
  - "نشأ بالفيوم … وجمع في العربية عند أبي حيان ثم ارتحل إلى حماة فقطنها ولما بنى الملك المؤيد إسماعيل جامع الدهشة قرره في خطابتها وكان فاضلا عارفا باللغة والفقه صنف في ذلك كتابا سماه المصباح المنير … وقد نقل غالبه ولده في كتاب تهذيب المطالع وكأنه عاش إلى بعد سنة ٧٧٠".
  - The book card gives the 2nd Hyderabad edition, 6 vols, 1392–96 AH / 1972–76.
- **ENCY**: arab-ency.com.sy/details/8678, by Sakīna Mawʿid.
  - Printed in "المجلد الخامس عشر، طبعة 2006، دمشق … رقم الصفحة … 90".
  - "نشأ بالفيوم بمصر".
  - "قال الزركلي في الأعلام: «وعلّق محمد بن السّابق الحموي على إحدى النسخ المخطوطة من الدرر الكامنة بأنه توفي في حدود760هـ»".
- **HAYWOOD**: the archive.org djvu text.
  - "the "Misbah al-Munir" by the Egyptian al-Fayyumi (died 766/1364) … full of technical terms of jurisprudence and philology".
  - The index gives "al-Fayyumi, 108".
  - Title page: "LEIDEN E. J. BRILL 1966" (OCR), with "Copyright 1960".
- **HALLAQ**: Iranica.
  - The live URL returns 403 to scripts but is the URL Google indexes. The Wayback copy (20260407) was read.
  - Header: "Vol. X, Fasc. 4, pp. 372-374".
  - "al-Wasīṭ … later abridged as al-Wajīz … ʿAbd-al-Karīm Rāfeʿī (d. 623/1226) … wrote a commentary on al-Wājīz, entitled Fatḥ al-ʿazīz".
- **WALTERS**: the W.590 description.
  - "Al-Miṣbāḥ al-munīr fī gharīb al-Sharḥ al-Kabīr … originally written as a gloss on the commentary of ʿAbd al-Karīm al-Rāfiʿī (d. 623 AH / 1226 CE) on al-Wajīz … entitled Fatḥ al-ʿazīz".
  - "copied … in 1083 AH / 1673 CE".
- **LANE**: Lane's Preface, from laneslexicon.github.io.
  - Source list: "Notwithstanding its title, it comprises a very large collection of classical words and phrases and significations of frequent occurrence … I have therefore constantly drawn from it".
  - Abbreviation list: "†Mṣb "The Miṣbáḥ" of El-Feiyoomee".
  - Chronology: "Aboo-Ḥeiyán: born in 654: died in 745", and "El-Feiyoomee (author of the "Miṣbáh," which he finished in 734)".
- **HAWR**: the hawramani Miṣbāḥ index page. It gives a description and a list of contents. It names no edition, publisher or editor.
- **NLI**: the National Library of Israel record, "تحفة الأريب بما في القرآن من الغريب … تأليف أثير الدين أبي حيان الأندلسي".

**Checks on our own data**

- **DB**: read-only queries on `dictionary_entries`.
  - The Miṣbāḥ has 901 approved (displayed) entries, 526 `deferred` and 1 `pending`.
  - The deferral policy is in `_dict_defer_redundant.py`: one general-dictionary slot per root.
  - All 901 displayed roots have a Qur'an frequency of at least 1.
- **Edition comparison (my own)**: I downloaded about 400 random Shamela 12145 pages.
  - For every page whose heading matched a displayed entry (112 entries), I compared the unvowelled text.
  - All 112 scored ≥ 0.97 similarity, and 111 scored ≥ 0.99. Most were identical, e.g. zyt, brz, fyD, bTl, qbD, $ms, brj, frd, jml, rqy, $kk, Awl.
  - I did not re-derive the exact figure "896 of 901". The sample is fully consistent with it.

**Counts over the 901 displayed entries** (`_dict_guide_tool.py grep` and DB)

| Pattern | Entries |
|---|---|
| من باب | 600 (67%) |
| الأزهري | 133 |
| `{` (Qur'an quotation) | 208 |
| التنزيل | 64 |
| `«` (hadith; the contexts read are overwhelmingly Prophetic sayings) | 99 |
| الشرع\|شرعا\|شرعي\|شرعية | 31 |
| الفقهاء | 43 |
| Strict poetry markers (قال الشاعر\|الراجز\|أنشد\|قال الآخر) together with hemistich `...` | 53 |
| Named poets | 30 raw, of which about 15 are real citations |
| بالألف | 225 |
| بالتشديد | 58 |
| بالتثقيل\|والتثقيل | 77 |
| عامي | 8 |
| Footnote markers `(n)` in the stored original | 12 entries: Aty ArD Ax* Axr Abw Ajr A*n Axw vny Aby Abl Abb (11 under alif) |
| Lane entries with `\bMsb\b` | 1,261 of 1,410 |
| Lane entries with `Mṣb` | 0 |

The poetry total therefore comes to about 60–65 entries.

## Claims table

S = SUPPORTED, NQ = NEEDS QUALIFICATION, U = UNSUPPORTED.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | title al-Miṣbāḥ al-Munīr; titleAr المصباح المنير في غريب الشرح الكبير | S | INTRO "وَسَمَّيْتُهُ بِالْمِصْبَاحِ الْمُنِيرِ فِي غَرِيبِ الشَّرْحِ الْكَبِيرِ"; WALTERS; DURAR |
| C2 | titleGloss "The Light-Giving Lamp, on the Unusual Words of the Great Commentary" | S | Fair rendering of the title (*munīr* = illuminating; *gharīb* = unusual words) |
| C3 | author al-Fayyūmī / الفيومي | S | DURAR, ENCY, SH-CARD, INTRO |
| C4 | authorFull Abū l-ʿAbbās Aḥmad b. Muḥammad b. ʿAlī al-Fayyūmī, later of Ḥamāh | S | INTRO "أَبُو الْعَبَّاسِ أَحْمَدُ بْنُ مُحَمَّدِ بْنِ عَلِيٍّ الْفَيُّومِيُّ"; SH-CARD "الفيومي ثم الحموي"; DURAR |
| C5 | period: finished 734 AH / 1334 CE | S | KH712 colophon; LANE "which he finished in 734" |
| C6 | period: author d. c. 770 AH / 1368 CE (uncertain) | S | DURAR "كأنه عاش إلى بعد سنة ٧٧٠"; SH-CARD "ت نحو ٧٧٠"; the uncertainty is disclosed |
| C7 | kind "Lexicon for a law book" | S | INTRO "غَرِيبِ شَرْحِ الْوَجِيزِ لِلْإِمَامِ الرَّافِعِيِّ"; WALTERS |
| C8 | Summary: a 14th-century dictionary written to explain the difficult words of a Shāfiʿī law book | S | INTRO; SH-CARD; KH712 (734 AH) |
| C9 | Summary: compact and grammatical; fixes how words are voweled and conjugated | S | INTRO "وَقَيَّدْتُ … مِثْلُ فَلْسٍ وَفُلُوسٍ … مِنْ بَابِ قَتَلَ"; 600/901 *min bāb*; HAYWOOD counts it among "short and abridged dictionaries" |
| C10 | Summary: "sometimes notes where a legal sense narrows ordinary usage" (r1 fix) | S | Hjj 3297, bxl 6283, wly, Hyy, Swm, rkE, ymm, fqh, jdl; about 31 entries carry sharʿ terms. "sometimes" is accurate |
| C11 | Summary: weighs jurists' Arabic against earlier lexicographers | S | الفقهاء in 43 entries. Examples: jzy 1201 (defends the jurists against al-Azharī); ktb "وقول الفقهاء باب الكتابة فيه تسامح"; rwH "فقول الفقهاء … مخالف لهذا"; fkh "فلجهله بلغة العرب"; bny |
| C12 | Lede: compiled for readers of a law book; the title promises the difficult words of al-Rāfiʿī's *Great Commentary* | S | INTRO; WALTERS |
| C13 | Lede: a compact teaching lexicon fixing voweling, conjugation and plurals | S | KH711 "مَسَالِكَ التَّعْلِيمِ لِلْمُبْتَدِئِ"; INTRO; plurals by model words in the entries (Hjj "مِثْلُ: سِدْرَةٍ وَسِدَرٍ") |
| C14 | Lede: "in a number of entries, says plainly that" a word's sharʿ meaning has narrowed (r1 fix) | S | Hjj "ثُمَّ قُصِرَ اسْتِعْمَالُهُ فِي الشَّرْعِ"; Swm "ثم استعمل في الشرع في إمساك مخصوص"; rkE; wly "خص في الشرع"; ymm "في عرف الشرع" |
| C15 | Grew up in al-Fayyūm in Egypt | S | DURAR "نشأ بالفيوم"; ENCY "نشأ بالفيوم بمصر" |
| C16 | Studied Arabic with Abū Ḥayyān | S | DURAR "وجمع في العربية عند أبي حيان"; ENCY "في مصر عند أبي حيان الأندلسي"; the fDl entry calls him "شَيْخُنَا أَبُو حَيَّانَ" |
| C17 | Abū Ḥayyān is the author of *Tuḥfat al-Arīb* | S | NLI record. No citation is given in the essay (see brief issues) |
| C18 | Settled in Ḥamāh in Syria | S | DURAR "ارتحل إلى حماة فقطنها"; ENCY "حماة بسورية" |
| C19 | al-Malik al-Muʾayyad Ismāʿīl made him preacher of the Dahsha mosque he had built | S | DURAR "ولما بنى الملك المؤيد إسماعيل جامع الدهشة قرره في خطابتها"; ENCY |
| C20 | Ibn Ḥajar calls him learned in language and in law (vol. 1, p. 372) | S | DURAR "وكان فاضلا عارفا باللغة والفقه"; page field 372 |
| C21 | Death: after 770 AH (1368–9 CE), by Ibn Ḥajar's guess | S | DURAR "وكأنه عاش إلى بعد سنة ٧٧٠". 770 AH = Aug 1368 – Aug 1369 |
| C22 | Death around 760, from a note on a manuscript of Ibn Ḥajar's book, reported by al-Ziriklī (r1 suggestion) | S | ENCY quotes al-Ziriklī exactly, "على إحدى النسخ المخطوطة من الدرر الكامنة … في حدود760هـ". The essay attributes it correctly as a relay |
| C23 | 766 in Haywood (p. 108) | S | HAYWOOD "(died 766/1364)"; index "al-Fayyumi, 108" |
| C24 | Finished late in Shaʿbān 734, spring 1334 (vol. 2, p. 712) | S | KH712 "فِي الْعَشْرِ الْأَوَاخِرِ مِنْ شَعْبَانَ … سَنَةَ أَرْبَعٍ وَثَلَاثِينَ وَسَبْعِمِائَةٍ". Late Shaʿbān 734 ≈ late April / early May 1334 |
| C25 | The law book is al-Rāfiʿī's (d. 623/1226) commentary on *al-Wajīz*, the "Great Commentary" of the title | S | HALLAQ; WALTERS (which ties "al-Sharḥ al-Kabīr" to al-Rāfiʿī's commentary on al-Wajīz); INTRO "شَرْحِ الْوَجِيزِ لِلْإِمَامِ الرَّافِعِيِّ" |
| C26 | *al-Wajīz* is al-Ghazālī's abridged manual of Shāfiʿī law | S | HALLAQ "later abridged as al-Wajīz"; WALTERS |
| C27 | The introduction says he first compiled a longer book on the commentary's *gharīb*, with extra material on inflection, confusable words, and the grammar and meaning of quoted evidence (r1 suggestion) | S | INTRO "أَوْسَعْتُ فِيهِ مِنْ تَصَارِيفِ الْكَلِمَةِ … وَمِنَ الْأَلْفَاظِ الْمُشْتَبِهَاتِ وَالْمُتَمَاثِلَاتِ وَمِنْ إعْرَابِ الشَّوَاهِدِ وَبَيَانِ مَعَانِيهَا"; "longer" from KH711 "اخْتِصَارِ الْمُطَوَّلِ" |
| C28 | The earlier book was arranged by the shape of words, so a root's material was scattered; the Miṣbāḥ abridges it, regathered by root (first letter, then second) | S | INTRO "قَسَمْتُ كُلَّ حَرْفٍ مِنْهُ بِاعْتِبَارِ اللَّفْظِ … غَيْرَ أَنَّهُ افْتَرَقَتْ بِالْمَادَّةِ الْوَاحِدَةِ أَبْوَابُهُ … فَأَحْبَبْتُ اخْتِصَارَهُ … مُعْتَبِرًا فِيهِ الْأُصُولَ مُقَدِّمًا الْفَاءَ ثُمَّ الْعَيْنَ" |
| C29 | Does not promise to cover what the commentary itself makes clear | S | INTRO "لَمْ أَلْتَزِمْ ذِكْرَ مَا وَقَعَ فِي الشَّرْحِ وَاضِحًا وَمُفَسَّرًا" |
| C30 | Lane: despite its title, a large stock of ordinary classical words and senses | S | LANE "Notwithstanding its title, it comprises a very large collection of classical words and phrases and significations of frequent occurrence" |
| C31 | A grammatical closing section; at its end he says he kept to "what concerns the jurists' vocabulary", teaching "the beginner" and bringing things "within reach of the intermediate student" (vol. 2, p. 711) | S | KH684 (khātima starts); KH711 quotation above; the translation is accurate |
| C32 | Arabic of the introduction quotation "وَقَيَّدْتُ … مِنْ بَابِ قَتَلَ" | S | Verbatim in INTRO. The ellipsis skips "وَقُفْلٍ وَأَقْفَالٍ وَهَمْلٍ وَإِهْمَالٍ وَنَحْوِ ذَلِكَ" |
| C33 | Its translation ("Whatever needs its form fixed …") | S | Accurate; labelled "translation for this guide" |
| C34 | *min bāb* formulas in about two-thirds of the entries shown | S | 600/901 |
| C35 | *min bāb qatala* = the verb runs like *qatala, yaqtulu* | S | INTRO "مِثْلُ ضَرَبَ يَضْرِبُ أَوْ مِنْ بَابِ قَتَلَ"; entries |
| C36 | *bi-l-alif* marks the fourth form | S | 225 entries, e.g. bxl "وَأَبْخَلْته بِالْأَلِفِ", Hjj "أَحْجَجْتُ … بِالْأَلِفِ", jzy "أَجْزَأَ بِالْأَلِفِ" |
| C37 | *bi-l-tashdīd*, "with doubling", marks the second form | S | zkw "زَكَّى … بِالتَّشْدِيدِ" (58 entries). Incomplete: the synonym *bi-l-tathqīl* is commoner (77); see brief issues |
| C38 | *lugha* flags a variant | S | fDl "وَفِي لُغَةٍ"; Hjj "وَالْفَتْحُ لُغَةٌ" |
| C39 | *ʿāmmī* marks a rejected popular form, sometimes paired with *al-ṣawāb*; in zkw *zakātiyya* is *ʿāmmī* and the correct form is *zakawiyya* | S | zkw 2180 "وَقَوْلُهُمْ زَكَاتِيَّةٌ عَامِّيٌّ وَالصَّوَابُ زَكَوِيَّةٌ" |
| C40 | The original drew on some seventy books, beginning with al-Azharī's *Tahdhīb* (vol. 2, pp. 711–712) | S | KH711 "مِنْ نَحْوِ سَبْعِينَ مُصَنَّفًا … فَمِنْ ذَلِكَ التَّهْذِيبُ لِلْأَزْهَرِيِّ" |
| C41 | He usually names his authority "where a judgement rests on it" | S | KH712 "وَسَمَّيْتُهُ غَالِبًا فِي مَوَاضِعِهِ حَيْثُ يُبْنَى عَلَيْهِ حُكْمٌ" |
| C42 | al-Azharī is named in about 130 entries shown | S | 133 |
| C43 | "al-Fārābī", judging from the same list, is the author of *Dīwān al-Adab* | S | KH711–712 "وَدِيوَانُ الْأَدَبِ لِلْفَارَابِيِّ" |
| C44 | Hjj excerpt copied from the stored text | S | Entry 3297; validator OK |
| C45 | Hjj translation | S | Accurate (قصد = headed for; ومنه يقال = from this comes the saying; النسك = devotional rites) |
| C46 | *al-ḥijj*, the noun of the act; the form in Q 3:97 | S | 3297 "وَالِاسْمُ الْحِجُّ بِالْكَسْرِ"; Q 3:97 (Ḥafṣ) حِجُّ الْبَيْتِ. The verse pointer is the guide's own, and is framed as such |
| C47 | *ḥijja*, "a single occasion", with Thaʿlab: analogy calls for *ḥajja* but it "has not been heard from the Arabs" | S | 3297 "وَالْحِجَّةُ الْمَرَّةُ … قَالَ ثَعْلَبٌ قِيَاسُهُ الْفَتْحُ وَلَمْ يُسْمَعْ مِنْ الْعَرَبِ" |
| C48 | *ḥujja* = proof; *ḥājjahu* = he disputed with him (compare Q 2:258); the bone round the eye; the beaten road | S | 3297 "وَالْحُجَّةُ الدَّلِيلُ … وَحَاجَّهُ مُحَاجَّةً … وَحِجَاجُ الْعَيْنِ … الْعَظْمُ الْمُسْتَدِيرُ حَوْلَهَا … وَالْمَحَجَّةُ … جَادَّةُ الطَّرِيقِ"; Q 2:258 حَاجَّ إِبْرَاهِيمَ |
| C49 | No evidence for the older sense; "proof" and the eye-bone are not derived from it; the senses stand side by side (this entry only) | S | Reading of 3297: no poetry, verse or authority is given for قصد. The claim is explicitly limited to this entry |
| C50 | al-Jawharī's *Ṣiḥāḥ* is among his listed sources | S | KH712 "وَالصِّحَاحُ لِلْجَوْهَرِيِّ" |
| C51 | Ṣiḥāḥ Hjj: the same two-step story, as quoted; a line by al-Mukhabbal; "convention" where al-Fayyūmī says sharʿ | S | Ṣiḥāḥ entry 3295 "قال المخبل: … يحجون سب الزبرقان المزعفرا … هذا الأصلُ، ثم تُعورِفَ استعماله في القصد إلى مكة للنُسك"; the translation is accurate |
| C52 | The label names a register, not a date; Q 2:196 already speaks of completing the ḥajj and ʿumra | S | Interpretation, marked as the guide's; Q 2:196 "وَأَتِمُّوا الْحَجَّ وَالْعُمْرَةَ لِلَّهِ" |
| C53 | bxl excerpt and translation | S | Entry 6283 "وَالْبُخْلُ فِي الشَّرْعِ مَنْعُ الْوَاجِبِ وَعِنْدَ الْعَرَبِ مَنْعُ السَّائِلِ مِمَّا يَفْضُلُ عِنْدَهُ"; accurate |
| C54 | Neither definition comes with evidence; he does not say which the Qur'an's *bukhl* verses (Q 3:180, 47:38) intend | S | 6283 has no evidence and no verse; Q 3:180 يَبْخَلُونَ; Q 47:38 يَبْخَلُ |
| C55 | "by our count, sharʿ appears in only about thirty of the entries shown here" (new) | S | 31 entries (listed above). A few hits are not narrowing notes (qwm "أقام الرجل الشرع", drk "مدارك الشرع", $rE), and a few narrowing notes use other words (ETw, syr, HSn with الفقهاء). The figure counts the word itself, which is what the sentence says, and the minority point holds |
| C56 | jzy: matches *jazā* with *qaḍā* ("settle, discharge"), cites Q 2:48, later turns to the jurists' *ajzā*, "to suffice" | S | 1201 "جَزَى … مِثْلُ: قَضَى يَقْضِي قَضَاءً وَزْنًا وَمَعْنًى وَفِي التَّنْزِيلِ {…} [البقرة: 48] … وَأَمَّا أَجْزَأَ … فَبِمَعْنَى أَغْنَى" |
| C57 | jzy excerpt and translation | S | 1201; validator OK; accurate |
| C58 | The "I" is al-Azharī; *hādhā lafẓuhu* closes the quotation; *wa-fīhi naẓar* is al-Fayyūmī | S | Text-internal: "قَالَ الْأَزْهَرِيُّ … هَذَا لَفْظُهُ وَفِيهِ نَظَرٌ لِأَنَّهُ إنْ أَرَادَ…" (the "he" of أراد is al-Azharī). Lisān جزي has "قال الأزهري: وبعض الفقهاء يقول أجزى", which corroborates al-Azharī discussing the jurists' أجزى |
| C59 | The objection: softening is regular (*akhṭaʾtu* beside *akhṭaytu*), so the jurists used the lightened form; al-Akhfash reports *jazā* as Ḥijāzī and *ajzaʾa* as Tamīmī | S | 1201 "فَإِنَّ تَسْهِيلَ … قِيَاسِيٌّ … وَأَخْطَأْتُ وَأَخْطَيْتُ … فَالْفُقَهَاءُ جَرَى عَلَى أَلْسِنَتِهِمْ التَّخْفِيفُ"; "الثُّلَاثِيُّ مِنْ غَيْرِ هَمْزٍ لُغَةُ الْحِجَازِ وَالرُّبَاعِيُّ الْمَهْمُوزُ لُغَةُ تَمِيمٍ" |
| C60 | The jurists' Arabic is defended, by analogy and by report, against a lexicographer | S | 1201: قياسي (analogy) + "نَقَلَهُمَا الْأَخْفَشُ" (report) |
| C61 | fDl: the idiom *lā yamliku dirhaman faḍlan ʿan dīnārin*, "he does not own a dirham, let alone a dinar" | S | fDl 1341 "وَقَوْلُهُمْ لَا يَمْلِكُ دِرْهَمًا فَضْلًا عَنْ دِينَارٍ … فَكَيْفَ يَمْلِكُ دِينَارًا" |
| C62 | He reports that "our shaykh Abū Ḥayyān … may God preserve him" found no text showing the construction to be the speech of the Arabs | S | 1341 "وَقَالَ شَيْخُنَا أَبُو حَيَّانَ الْأَنْدَلُسِيُّ … أَبْقَاهُ اللَّهُ تَعَالَى وَلَمْ أَظْفَرْ بِنَصٍّ عَلَى أَنَّ مِثْلَ هَذَا التَّرْكِيبِ مِنْ كَلَامِ الْعَرَبِ وَبَسَطَ الْقَوْلَ". The quoted "I" belongs to Abū Ḥayyān, and "وبسط القول" is al-Fayyūmī's summary. This is the natural reading |
| C63 | A blessing for the living (Abū Ḥayyān d. 745) | S | LANE "Aboo-Ḥeiyán … died in 745"; the book was finished 734 (KH712) |
| C64 | "most useful on form, and, where it notes one, on the gap between a word's legal and ordinary sense" (r1 fix) | S | This is an evaluation, but it is qualified and rests on C34–C37 and C10. There is no ranking against other works |
| C65 | Quotes the Qur'an, with formulas such as *wa-fī l-tanzīl*, in roughly two hundred entries | S | 208 entries with {…}; التنزيل in 64 |
| C66 | Evidence mostly earlier scholars; hadith in about a hundred entries; poetry in only sixty or seventy (r1 fix) | S | 366 entries name at least one of 22 major philologists and 384 entries have "قال ال/ابن/أبو"; `«` = 99 (read: Prophetic hadith, e.g. rHm, jzy, Hsb, frq); poetry ≈ 60–65. "sixty or seventy" is at the generous end but acceptable |
| C67 | Its labels are a 14th-century teacher's classifications, not a history | S | Interpretation consistent with KH711 (teaching aim) |
| C68 | Lane drew on it constantly and cites it as "Mṣb", plain "Msb" in our copy, in most of his entries on our site | S | LANE "I have therefore constantly drawn from it"; abbreviation "Mṣb"; the site's Lane text has Msb in 1,261/1,410 and Mṣb in 0 |
| C69 | Tāj quotes "the *Miṣbāḥ*" by name; its smw entry takes Ibn al-Anbārī's remark on the gender of *samāʾ* from al-Fayyūmī | S | Tāj smw 224 "في المصباح: قال ابن الأنباري: السماء يذكر ويؤنث"; Miṣbāḥ smw 220 "قَالَ ابْنُ الْأَنْبَارِيِّ تُذَكَّرُ وَتُؤَنَّثُ" |
| C70 | Ibn Ḥajar: his son copied most of it into a book of his own | S | DURAR "وقد نقل غالبه ولده في كتاب تهذيب المطالع" |
| C71 | onOurSite: text from hawramani, which names no edition | S | HAWR (no edition, publisher or editor) |
| C72 | Agrees almost letter for letter with the ʿIlmiyya printing on Shamela (896/901), without its footnotes | S (sampled) | My comparison of 112 entries: all ≥ 0.97 and 111 ≥ 0.99. SH-ATY shows the printing's footnote, which the stored text lacks. The exact figure 896 was not re-derived |
| C73 | In a dozen entries, nearly all under alif, a stray "(1)" or similar marks a missing note (new) | S | DB scan: 12 entries, 11 under alif; SH-ATY footnote "(١) العَجَّاجُ." absent from stored Aty |
| C74 | We show the Miṣbāḥ for 901 Qur'anic roots | S | `dicts`: 901; all have Qur'an frequency ≥ 1 |
| C75 | The work covers more; some entries are held back where another dictionary fills the place, so a missing entry does not mean al-Fayyūmī passed over the root | S | DB: 526 deferred; `_dict_defer_redundant.py` one-slot policy; the Shamela book has about 3,500 heading pages |
| C76 | The introduction and the closing grammatical section are not shown | S | Displayed rows are per-root; no khātima text appears in them |
| C77 | He files a root whose middle letter is hamza under a weak letter (*yāʾ* after *i*, *wāw* after *u* or *a*) (r1 fix, new) | S | INTRO passage quoted above: kasra → ي; ḍamma → و; fatḥa → و |
| C78 | His treatment of *saʾala* is on the س و ل page | S | Entry 10115 "س و ل : سَوَّلْتُ … وَسَأَلْتُ اللَّهَ الْعَافِيَةَ …" |
| C79 | The ر أ ي page shows only his note on *al-riʾa*, "the lung" | S | Entry 275 "ر ء ي : الرِّئَةُ … مَجْرَى النَّفَسِ …" (lung only) |
| C80 | His account of *raʾā*, filed the same way, sits in an entry our copy lacks (new) | S | SH-RWY "(ر وي) … وَرَأَيْتُ الشَّيْءَ رُؤْيَةً أَبْصَرْتُهُ"; `find-root روي` = no match on the site; fatḥa before hamza → wāw per INTRO |
| C81 | Source durar: 2nd ed., 6 vols, Hyderabad 1972–76, vol. 1 p. 372, no. 787 | S | DURAR card and page |
| C82 | Source arabency: Sakīna Mawʿid, vol. 15, Damascus 2006, p. 90 | S | ENCY footer |
| C83 | Source haywood: Leiden: Brill, 1960 | S | Copyright 1960 on the linked scan. The scan's title page reads 1966 (OCR), i.e. a later printing; see brief issues |
| C84 | Source misbah-ed: ʿIlmiyya, 2 vols with continuous pagination, n.d.; introduction pp. 1–2 separately numbered; khātima vol. 2 pp. 684–712 | S | SH-CARD; KH684; KH712; page navigation "المقدمة 1 2" |
| C85 | Source hallaq: Iranica X/4 (2000), pp. 372–374 | S | HALLAQ header "Vol. X, Fasc. 4, pp. 372-374 … Published December 15, 2000" |
| C86 | Source walters: W.590, dated 1083/1673 | S | WALTERS |
| C87 | Source wikisource: introduction | S | Opened (HTTP 200); raw text as quoted |
| C88 | Source lane: Preface (sources, abbreviations "Mṣb", chronology) | S | LANE |
| C89 | Source hawramani | S | HAWR (HTTP 200) |

**Totals:**

- 89 claims.
- 89 supported.
- 0 need qualification.
- 0 unsupported.

## Round-1 flags: status

| Round-1 flag | Status | What now stands |
|---|---|---|
| C9 (summary and lede on sharʿ narrowing) | Fixed | "sometimes notes" and "in a number of entries" are both accurate (C10, C14). The new count "about thirty" is reproduced as 31 (C55) |
| C56 ("strongest on…") | Fixed | Replaced by a qualified evaluation (C64) |
| C58 (evidence profile) | Fixed | Hadith are added and "verse" becomes "poetry" (C66). Counts reproduced: hadith 99; poetry ≈ 60–65 |
| C68 (medial-hamza rule) | Fixed | Now matches the introduction exactly (C77). The *raʾā* addition is verified against Shamela vol. 1 pp. 246–247 (C80) |

All r1 suggestions were adopted and check out (C22, C27, C68, C73):

- the Durar-manuscript wording;
- *iʿrāb al-shawāhid*;
- Mṣb/Msb consistency;
- the footnote-marker warning.

## Flagged items and fixes

None.

## Brief issues (non-factual)

1. **suggestion: length.** The validator counts 1,144 words in the lede and body, above the "roughly 700–1,100" guideline; round 1 counted 1,099. Trim about 45 words. Candidates:
   - the Tāj/Ibn al-Anbārī clause in the last paragraph, which could be cut to "al-Zabīdī's *Tāj al-ʿArūs* quotes 'the *Miṣbāḥ*' by name (see [[root:smw|…]])";
   - one of the two sentences on the Ṣiḥāḥ's al-Mukhabbal line.
2. **suggestion: onOurSite length.** It runs to 172 words; the format asks for about 60–150. The *raʾā* sentence could lose "filed the same way", or the footnote-marker clause could be shortened.
3. **suggestion: the doubling formula.** *bi-l-tathqīl* is more frequent than *bi-l-tashdīd* in the displayed entries (77 vs 58). Examples:
   - zkw itself uses both ("زَكَّاهُ بِالْأَلِفِ وَالتَّثْقِيلِ");
   - swl opens with "سَوَّلْتُ … بِالتَّثْقِيلِ".

   A reader will meet *bi-l-tathqīl* unexplained. Change to "*bi-l-tashdīd* or *bi-l-tathqīl*, 'with doubling', the second."
4. **suggestion: Haywood citation.** The linked archive.org scan's title page reads "Leiden, E. J. Brill, 1966" (OCR), with "Copyright 1960". Either add "(linked copy: a later printing)" or leave it as is; p. 108 is confirmed in that copy's index.
5. **suggestion (minor): Tuḥfat al-Arīb.** "Abū Ḥayyān (author of *Tuḥfat al-Arīb*)" carries no citation. The fact is secure (NLI record; the site's own label), and the guide link partly covers it, so this is optional.
6. **Otherwise the essay passes on form:**
   - no padding, generic praise or ranking;
   - no forced "original root meaning" narrative: the Hjj reading explicitly says it describes one entry only;
   - every root mention is linked;
   - translations are labelled (the introduction and khātima quotations are marked "translation for this guide"/"our translation", and the shared box covers the excerpts);
   - the author's voice is kept separate from al-Azharī's and Abū Ḥayyān's.

## URL check

| Source | Result |
|---|---|
| durar https://shamela.ws/book/6674/371 | 200; vol. 1 p. 372, no. 787 |
| arabency https://arab-ency.com.sy/details/8678 | 200; the correct article |
| haywood archive.org item | 200; djvu text available; later printing (see brief issue 4) |
| misbah-ed https://shamela.ws/book/12145 | 200; ʿIlmiyya, Beirut, 2 vols |
| hallaq https://www.iranicaonline.org/articles/gazali/gazali-v-as-a-faqih/ | 403 to scripts (Cloudflare). This is the URL search engines index for the article; the content was verified via the Wayback copy of the equivalent /articles/gazali-v-as-a-faqih/. Should work in a browser |
| walters | 200; correct manuscript |
| wikisource https://ar.wikisource.org/wiki/المصباح_المنير/مقدمة | 200; correct text |
| lane https://laneslexicon.github.io/lexicon/site/lane/preface/ | 200; contains the cited material |
| hawramani | 200 |

Every listed source is cited in the text, and every source was consulted.

## Validator

`node scripts/validate-dictionary-guides.mjs al-misbah-al-munir` gives "=== al-misbah-al-munir — ok", 0 errors and 0 warnings:

- root links: 10 (10 distinct pairs);
- excerpts: 3;
- words: 1,144;
- example roots: zkw, Hjj, bxl, jzy, fDl, smw, swl, rAy.

Result: "1/1 guides pass".

## Site-data issues

- **Stored date 1368.** It corresponds to "c. 770 AH" (SH-CARD, WALTERS, HAWR) and is acceptable for ordering. The date is disputed: after 770 (Ibn Ḥajar), c. 760 (al-Ziriklī, from a Durar manuscript note), 766 (Haywood). The guide discloses this, so no change is needed.
- **Stored labels.** "al-Miṣbāḥ al-Munīr" / المصباح المنير / "al-Fayyūmī" are correct.
- **Missing ر و ي entry.** The site has no rwy root, so the Miṣbāḥ's ر و ي entry, which holds *raʾā* "to see", *riwāya* and *mirʾāh*, was never collected. The guide already tells readers this.
- **Footnote markers.** The 12 displayed originals that keep the printing's markers without the notes are Aty, ArD, Ax*, Axr, Abw, Ajr, A*n, Axw, vny, Aby, Abl and Abb. This is a cosmetic data issue that could be cleaned in the stored text; the guide already warns readers.
