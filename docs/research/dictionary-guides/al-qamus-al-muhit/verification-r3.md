# al-Qāmūs al-Muḥīṭ: independent verification, round 3

Checked file: `roots/frontend/src/content/dictionary-guides/guides/al-qamus-al-muhit.ts` (state on 2026-09-26, after revision r2).
I did not open research-notes.md or any revision-*.md. I read verification-r2.md only for the earlier flags. Unless the table says otherwise, I opened every source below myself in this round.

Evidence used this round:

- **Risāla**: al-Fīrūzābādī, *al-Qāmūs al-Muḥīṭ*, Muʾassasat al-Risāla, 8th ed., on Shamela (book 7283). Each page carries its own "صNNN" field. Shamela page = print page − 24. I fetched print pp. 26, 27, 28, 29, 32 (preface), 315, 544–545, 727, 963–964, 1242 and 1303. I compared the stored *ilāh*, *ahl* and *darasa* entries with the Risāla text letter by letter, ignoring vowel marks and punctuation: 0 differences in 68, 152 and 138 words.
- **Sakhāwī**: *al-Ḍawʾ al-Lāmiʿ*, vol. 10, pp. 79–86 (Shamela 6675/2983–2990; each page is labelled "ج10 - صNN"). Biography no. 274 begins on p. 79.
- **Tāj intro**: Shamela 7030/73, labelled "ج1 - ص73".
- **Haywood**: archive.org djvu text. I read pp. 71, 75 and 83–90, locating each by its page header.
- **Lane**: Preface at laneslexicon.github.io. Each page's roman numeral is printed inline where the page begins. I mapped every quoted passage to its page by character offset (details under C14, C20, C32, C43 and C57).
- **Britannica**: "Sufism", section "Sufi thought and practice", read in the browser pane. The byline reads "Annemarie Schimmel, Britannica Editors, Sep. 21, 2026".
- **Baalbaki**: Google Books pages return a reCAPTCHA, which I did not bypass. The Books API quota is exhausted. The legacy Google Books feed (`google.com/books/feeds/volumes?q=…`) did return search snippets for volume cme7AwAAQBAJ (*The Arabic Lexicographical Tradition*); these are quoted under C21.
- **EI²**: Brill SIM-2383 returns HTTP 403 to curl, to the DOI redirect and in the browser pane. Crossref confirms that DOI 10.1163/1573-3912_islam_sim_2383 is "al-Fīrūzābādī", *Encyclopaedia of Islam, Second Edition*. Crossref lists no author, so the attribution to Fleisch is unconfirmed.
- **DB**: `_dict_guide_tool.py` entry/grep/root/dicts; the `verses` table; `/api/root/drs/dictionaries`.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title al-Qāmūs al-Muḥīṭ / القاموس المحيط | S | Risāla p. 27 «وَسَمَّيْتُهُ "الْقَامُوسَ الْمُحِيطَ"»; Hawramani page title |
| C2 | Gloss "The Encompassing Ocean" | S | p. 27 «لِأَنَّهُ الْبَحْرُ الْأَعْظَمُ»; Haywood p. 83 "the Surrounding Ocean" |
| C3 | al-Fīrūzābādī; Majd al-Dīn Abū l-Ṭāhir Muḥammad ibn Yaʿqūb; الفيروزآبادي | S | Sakhāwī p. 79 «محمد بن يعقوب … المجد أبو الطاهر … الفيروزابادي الشيرازي اللغوي»; Haywood p. 83 "Majd al-Din Muhammad ibn Yaʿqub al-Firuzabadi" |
| C4 | Period 729–817 AH / 1329–1415 CE | S | Sakhāwī p. 79 (born Rabīʿ II, or Jumādā II, 729 ≈ Feb–Apr 1329); p. 86 «مات … في ليلة عشرى شوال سنة سبع عشرة بزبيد». I recomputed the tabular date: 20 Shawwāl 817 = JD 2237887.5 = 2 Jan 1415 (Julian). Haywood p. 83 gives 726/1326–817/1414; the body notes the 816 variant |
| C5 | Kind "Condensed general lexicon" | S | p. 27 «كِتَابٍ وَجِيزٍ»; Lane p. xvii ("an enormous vocabulary … abridged") |
| C6 | Summary: fourteenth-century digest of *al-Muḥkam* and *al-ʿUbāb* | S | p. 27 «وَضَمَّنْتُهُ خُلَاصَةَ مَا فِي "الْعُبَابِ"، وَ"الْمُحْكَمِ"»; in circulation by 790 (Sakhāwī pp. 85–86) |
| C7 | Summary: written with *al-Ṣiḥāḥ* in view, marking what it lacked and where he judged it wrong | S | pp. 27–28 |
| C8 | Summary: terse, abbreviated, few quotations; good for surveying senses and vowellings | S | p. 28 (abbreviations, vowelling rules); Haywood p. 87; Lane p. xvii ("scarcely any examples from the poets") |
| C9 | Lede: quotations and "superfluities" removed; sixty volumes shrunk thirtyfold | S | p. 27 «خَمَّنْتُهُ فِي سِتِّينَ سِفْرًا … مَحْذُوفَ الشَّوَاهِدِ، مَطْرُوحَ الزَّوَائِدِ … وَلَخَّصْتُ كُلَّ ثَلَاثِينَ سِفْرًا فِي سِفْرٍ» |
| C10 | Lede: *al-Ṣiḥāḥ* in view, adding and correcting | S | pp. 27–28 |
| C11 | Born 729/1329 in Fārs, near Shiraz | S | Sakhāwī p. 79 «بكازرون من أعمال شيراز» (Haywood p. 83: Kārzīn) |
| C12 | Studied in Iraq | S | Sakhāwī p. 79 «وارتحل إلى العراق فدخل واسط … ثم دخل بغداد»; p. 80 (Baghdad); Haywood p. 83 |
| C13 | Last two decades as chief judge of Yemen at Zabīd; died there 817/1415 | S | Sakhāwī p. 81: entered Zabīd in Ramaḍān 796; «أضاف إليه قضاء اليمن كله … أول ذي الحجة سنة سبع وتسعين … فاستقرت قدمه بزبيد … إلى حين وفاته وهي مدة تزيد على عشرين سنة»; p. 86 (death at Zabīd) |
| C14 | "though some sources give 816" | S | Lane p. xvi "born in the year of the Flight 729, and died in 816" (offset 52761; marker xvi at 49233, xvii at 53264); Hawramani "816 or 17 AH" |
| C15 | A contemporary quoted by al-Sakhāwī says he wrote the *Qāmūs* in Mecca, first at length, then abridged it | S | Sakhāwī p. 83, «قال التقي الكرماني … ثم جاور بمكة مدة عشر سنين أو أكثر وصنف بها تصانيف منها … والقاموس مطولا في مجلدات عديدة ثم أمره والدي باختصاره فاختصر في مجلد ضخم» |
| C16 | By 790/1388 he had handed a copy to al-Maqrīzī | S | Sakhāwī p. 85 «وطول المقريزي في عقوده ترجمته وقال أن آخر ما اجتمع به في مكة سنة تسعين»; p. 86 «وقرأت عليه بعض مصنفاته وناولني قاموسه وأجازني» |
| C17 | Preface: began a work combining *al-Muḥkam* and *al-ʿUbāb*; sixty volumes; beyond students; asked for something concise | S | p. 26 «شَرَعْتُ فِي كِتَابِي … الْجَامِعِ بَيْنَ الْمُحْكَمِ وَالْعُبَابِ»; p. 27 «خَمَّنْتُهُ فِي سِتِّينَ سِفْرًا، يُعْجِزُ تَحْصِيلُهُ الطُّلَّابَ، وَسُئِلْتُ تَقْدِيمَ كِتَابٍ وَجِيزٍ» |
| C18 | Quotation وألفت هذا الكتاب محذوف الشواهد مطروح الزوائد + translation | S | p. 27, verbatim; the translation is accurate |
| C19 | "every thirty volumes into one"; "the greatest sea" | S | p. 27 |
| C20 | The larger work was never finished | S | Lane p. xviii (offset 59068, after the xviii marker at 58012): al-Suyūṭī's "direct assertion that this work was never completed"; Sakhāwī p. 82 «رأيت بخطه أيضا أنه كمل منه مجاليد خمسة» |
| C21 | Baalbaki: the *Qāmūs*'s additions hardly bear out the claim to distil two thousand works; most are names of Companions, ḥadīth scholars, poets and places, or plants [baalbaki p. 393][qamus-risala p. 32] | S (locator inferred) | Google Books feed snippets from cme7AwAAQBAJ: "…additions which hardly substantiate its author's claim that it contains the digest of two thousand works (ṣarīḥ alfay muṣannaf).625 Most of these additions are names of Companions of the Prophet, scholars of Ḥadīṯ, poets, place names and plants, in addition to medical terms which he seems to have recorded in Yemen…". "Its author" makes these the *Qāmūs*'s additions, so the reworded sentence matches the source. Page: a separate snippet shows notes 619–623 printed over the running head "392 CHAPTER 3", so note 625 most likely falls on p. 393. I did not see a page image. The source line honestly says "search snippet only". The two-thousand-works claim is confirmed at Risāla p. 32 |
| C22 | The preface claims to distil two thousand works | S | Risāla p. 32 «وَكِتَابِي هَذَا … صَرِيحُ أَلْفَيْ مُصَنَّفٍ مِنَ الْكُتُبِ الْفَاخِرَةِ» |
| C23 | Poetry rare; the scholars behind a statement usually go unnamed | S | Haywood p. 87 ("omitted all reference to them and their authors, as well as the usual illustrative examples"); Lane p. xvii ("scarcely any examples from the poets") |
| C24 | Excerpt أ ل ه + translation | S | DB entry 114; matches Risāla p. 1242 (0 word differences). The translation is accurate; "[Its first vowel] may be any of the three" correctly renders «ويثلث» |
| C25 | *Ṣiḥāḥ* أ ل ه: derives the name from *ilāh*, explains the lost hamza, reports Abū ʿAlī's argument and Sībawayh's alternative, quotes verse for *ilāha* as a place and as the sun | S | DB entry 109: «وأصله إلاه على فعال … حذفت الهمزة تخفيفا … وسمعت أبا على النحوى يقول … وجوز سيبويه … كفى حزنا … تروحنا من اللعباء …» |
| C26 | The *Qāmūs* drops the verse but lists the snake and the new moon, absent from the *Ṣiḥāḥ* | S | Entries 114 vs 109. In 109 the snake appears only in the story behind the verse («وكان قد نهشته حية»), and there is no *hilāl* |
| C27 | Preface: *al-Ṣiḥāḥ* popular, "and it deserves that"; missed "half the language or more", whole roots or rare senses | S | p. 27 «وَهُوَ جَدِيرٌ بِذَلِكَ، غَيْرَ أَنَّهُ فَاتَهُ نِصْفُ اللُّغَةِ أَوْ أَكْثَرُ، إِمَّا بِإِهْمَالِ الْمَادَّةِ، أَوْ بِتَرْكِ الْمَعَانِي الْغَرِيبَةِ النَّادَّةِ» |
| C28 | Red ink for roots it lacked; al-Jawharī's errors ("went against what is right") flagged "not to disparage him" but because teachers relied on his book | S | p. 27 «فَكَتَبْتُ بِالْحُمْرَةِ الْمَادَّةَ الْمُهْمَلَةَ لَدَيْهِ»; p. 28 «رَكِبَ فِيهَا الْجَوْهَرِيُّ … خِلَافَ الصَّوَابِ، غَيْرَ طَاعِنٍ فِيهِ … وَاخْتَصَصْتُ كِتَابَ الْجَوْهَرِيِّ … لِتَدَاوُلِهِ وَاشْتِهَارِهِ … وَاعْتِمَادِ الْمُدَرِّسِينَ عَلَى نُقُولِهِ». (The preface gives the teachers' reliance as the reason for singling out al-Jawharī's book. It also gives self-protection against being blamed for copied errors, which the essay omits. The compression is fair) |
| C29 | In the 174 entries al-Jawharī is named sixteen times, always to correct him | S | `grep الصحاح\|جوهري` finds 16 entries, and `الجوهر.*الجوهر` finds 0 (one mention each). Each is a correction: غلط (nSr, Elw, sEy, Esy, xzy, lwy, Dgv), وهم (xlf, rjl, *hb, gfl, srq, kAs, rqy), باطل (Ahl), تصحيف (dhn) |
| C30 | Excerpt أ ه ل + translation | S | DB entry 1117; Risāla pp. 963–964 (0 word differences) |
| C31 | *Ṣiḥāḥ*: say *ahl*, not *mustaʾhil*, "the common people say it"; neither entry gives evidence | S | DB entry 1112 «وتقول: فلان أهل لكذا، ولا تقل: مستأهل، والعامة تقوله». Its verse (استأهلي) illustrates the *ihāla* sense, not the ruling |
| C32 | Lane, defending al-Jawharī: many corrections borrowed without acknowledgement, and many wrong | S | Lane p. xvii (offsets 54725–55902): "inserting criticisms of others, without acknowledgement … borrowed from the Annotations … generally when they are false, (which is often the case) … in defence of El-Jowharee" |
| C33 | The "half the language" claim is disputed; al-Shidyāq's sample count found more entries in *al-Ṣiḥāḥ*, excluding proper names | S | Haywood p. 75 |
| C34 | al-Zabīdī, the eighteenth-century commentator, credited the *Qāmūs* with 60,000 entries, 20,000 more than *al-Ṣiḥāḥ* | S | Tāj vol. 1 p. 73, in his own voice after «قلت»: «فإنه جمع فيه ستين ألف مادة، زاد على الجوهري بعشرين ألف مادة»; Haywood p. 89 ("compiled in Egypt in the Eighteenth Century") |
| C35 | Like *al-Ṣiḥāḥ*, filed by last letter, then first; *ilāh* in the chapter of *hāʾ* | S | Risāla p. 1242 «[باب الهاء] فصل الهمزة … ألَهَ»; Haywood p. 71 ("arranged his roots according to their final radicals … Within each chapter, roots are entered according to the first"), p. 88 |
| C36 | Abbreviations ع د ة ج م | S | p. 28 «مُكْتَفِيًا بِكِتَابَةِ: ع، د، ة، ج، م، عَنْ قَوْلِي: مَوْضِعٌ، وَبَلَدٌ، وَقَرْيَةٌ، وَالْجَمْعُ، وَمَعْرُوفٌ» |
| C37 | Our entries also use جج for a plural of a plural | S | Sakhāwī p. 84 «وعن جمع الجمع بجج»; Haywood p. 86 ("Two jims meant the plural of a plural"); DB frq, *hb, fwq |
| C38 | *bi-hāʾ* = add the ending *-a* | S | p. 28 «أَتْبَعْتُهَا الْمُؤَنَّثَ بِقَوْلِي: وَهِيَ بِهَاءٍ» |
| C39 | Vowelling: a word left unmarked has *a*, and no reliance on pen marks; "with *u*/*i*", *muḥarraka* (as in *ḥasan*), *yuthallath*, model words | S | p. 28 «وَكُلُّ كَلِمَةٍ عَرَّيْتَهَا عَنِ الضَّبْطِ فَإِنَّهَا بِالْفَتْحِ … فَأُقَيِّدُهُ بِصَرِيحِ الْكَلَامِ، غَيْرَ مُقْتَنِعٍ بِتَوْشِيحِ الْقِلَامِ»; Haywood p. 87 ("muharrak … hasan"; "with damma"/"with kasra"; model words); «ويثلث» in the Alh entry |
| C40 | A verb given without its imperfect conjugates like *kataba* | S | p. 28 «أَوِ الْمَاضِيَ بِدُونِ الْآتِي، وَلَا مَانِعَ؛ فَالْفِعْلُ عَلَى مِثَالِ كَتَبَ» |
| C41 | In print a dash repeats the word just defined (وـ للبيت) | S | Risāla p. 963 «وأهل الأمر: ولاته، وـ للبيت: سكانه»; in drs, «وـ المرأة … وـ الكتاب» repeats the verb |
| C42 | في: العين points to the chapter of roots ending in *ʿayn*, where the proverb is explained under *sarʿān* | S | p. 964 «و"سرعان ذا إهالة"، في: العين»; p. 727 «وأما "سرعان ذا إهالة" فأصله…» (root س ر ع, chapter of *ʿayn*) |
| C43 | Lane: "what was once 'well known' has long ceased to be so"; words "meant to be understood in post-classical senses" | S | Lane p. xxii (offsets 82384 and 82885; marker xxii at 77696, xxiii at 83058). The transcription has the typo "one" for "once" |
| C44 | Excerpt 1 د ر س + translation | S | DB entry 8655; Risāla p. 544 (0 word differences over the whole entry, pp. 544–545) |
| C45 | Threshing, mange, worn garment follow, among others | S | Entry 8655 |
| C46 | No stated relation between an effaced trace and reading | S | Entry 8655 |
| C47 | Excerpt 2 (Idrīs; *dārasta*) + translation | S | Entry 8655; the translation is accurate |
| C48 | *Ṣiḥāḥ*, with "it is said": Idrīs named for his much study of God's book (Q 19:56) | S | DB entry 8652 «ويقال سمى إدريس عليه السلام لكثرة دراسته كتاب الله تعالى»; `verses` 19:56 has إِدْرِيسَ |
| C49 | The *Qāmūs* rejects this without naming anyone, giving a reason rather than evidence | S | Entry 8655 «ليس من الدراسة، كما توهمه كثيرون، لأنه أعجمي» |
| C50 | Our text of 6:105 reads *darasta*; *dārasta* is another reading; the *Qāmūs* does not say whose gloss it is | S | `verses` 6:105 «وَلِيَقُولُوا۟ دَرَسْتَ»; entry 8655 |
| C51 | The *Tāj* "fills in the names" (r2 rewording of "puts back what was cut") | S | The claim is now neutral. The *Tāj* does name people the *Qāmūs* does not (next two rows). It no longer implies that these names were removed from the *Qāmūs* |
| C52 | The *Tāj* gives *dārasta* as the reading of Ibn Kathīr and Abū ʿAmr and credits the gloss to Ibn ʿAbbās | S | DB Tāj entry 8653 «وليقولوا دارست في قراءة ابن كثير وأبي عمرو، وفسره ابن عباس رضي الله عنهما بقوله: قرأت على اليهود، وقرؤوا عليك» |
| C53 | *Tāj* on Idrīs: Ibn Khaṭīb al-Dahsha for foreign origin, then a verdict that it is sounder; Ibn al-Jawwānī for derivation from study | S | Entry 8653 «وقال ابن خطيب الدهشة: وهو اسم أعجمي … وقيل: إنما سمي به لكثرة درسه، ليكون عربيا. والأول أصح. وقال ابن الجواني: سمي إدريس لدرسه الثلاثين صحيفة». The essay leaves the verdict unattributed, which is right, because the text does not say whose it is |
| C54 | Good at range; cannot show how old a sense is, who used it, or whether it is Qur'anic-era | S | Interpretive; follows from C9 and C23 |
| C55 | *al-abdāl*: not a Qur'anic word; a rank in the Sufi hierarchy of saints [britannica-sufism] | S | `verses`: no match for أبدال after removing vowel marks. Britannica "Sufism" (Schimmel and Editors, Sep. 21, 2026), read in the browser: "The invisible hierarchy of saints consists of the 40 abdāl ('substitutes'; for when any of them dies another is elected by God…)…" |
| C56 | Excerpt ب د ل + translation; defined with no source or date | S | DB entry 2636 «والأبدال: قوم بهم يقيم الله عز وجل الأرض، وهم سبعون: أربعون بالشام، وثلاثون بغيرها» |
| C57 | The *Tāj* quotes the *Qāmūs* and adds explanations, authorities, quotations and further words | S | Lane p. xviii (offset 62274): "an interwoven commentary on the Ḳámoos; exhibiting fully … innumerable explanations … examples in prose and verse; and a very large collection of additional words"; Haywood pp. 89–90 ("contents of the Qamus in brackets … amplification of definitions, the mention of authorities … illustrative quotations … additional words … entirely new roots") |
| C58 | *qāmūs*, "ocean", came to mean "dictionary" | S | Haywood p. 83 ("came to mean a dictionary"), p. 85 |
| C59 | onOurSite: only 174 roots | S | `dicts`: displayed entries = 174 |
| C60 | onOurSite: Hawramani names no edition; the *ilāh*, *ahl* and *darasa* entries match the Risāla edition | S | Hawramani page (no edition statement). My word-level comparisons found 0 differences in all three |
| C61 | onOurSite: red ink lost; و/ي signs lost; ص ل ي shows only the *yāʾ* article; *ṣalāt* belongs to the *wāw* article, which is not displayed | S | Risāla p. 1303 «• ي: صلى اللحم …» then «• و: الصلا … والصلاة: الدعاء»; entry 4186 begins without «ي:»; `root Slw` shows no *Qāmūs* entry. (Preface p. 27 also advertises «تَخْلِيصُ الْوَاوِ مِنَ الْيَاءِ».) |
| C62 | onOurSite: the و ج ه line is the separate *kunābid* article; some short entries are not their root's article | S | Risāla p. 315 «• وجه كنابد، بالضم: قبيح.» (under ك ن ب د); DB entry 1679 |

**Totals: 62 claims: 62 supported, 0 need qualification, 0 unsupported.**

## Round-2 flags: status

| r2 flag | Status now |
|---|---|
| C51, "puts back what was cut" | Fixed: "fills in the names … sets out both sides". Neutral and accurate (entry 8653) |
| C21, Baalbaki sentence | Fixed: no "to those two sources" and no quotation marks. A Google Books snippet (legacy feed) confirms the substance: "additions which hardly substantiate its author's claim … Most of these additions are names of Companions of the Prophet, scholars of Ḥadīṯ, poets, place names and plants…". The page number p. 393 is inferred from footnote numbering, not seen, and the source line says so |
| C55, al-abdāl citation | Fixed: [^britannica-sufism] replaces EI² "Abdāl"; the quoted sentence is confirmed in the browser |
| r2 brief issues (vowelling cite, p. 727, "adds", Baalbaki locators, source line) | All applied. The vowelling sentence now cites Risāla p. 28; the locator is p. 727; the *Tāj* "adds"; Baalbaki pp. 392/394/398 are gone; the source line now reads "search snippet (no page view)" |

## Checks on r2's new claims

- **Britannica "hierarchy of saints … 40 abdāl"**: confirmed verbatim; byline "Annemarie Schimmel, Britannica Editors, Sep. 21, 2026". (Britannica gives 40 abdāl; the *Qāmūs* gives 70. The essay does not state a number in its own voice, so there is no conflict.)
- **The *Tāj* adds "explanations"**: Lane p. xviii "innumerable explanations which are so abridged in the latter work as to be unintelligible"; Haywood p. 89 "amplification of definitions". Confirmed.
- **Haywood p. 71 co-citation for the arrangement**: confirmed.
- **Risāla p. 28 for the vowelling rule**: confirmed, «وَكُلُّ كَلِمَةٍ عَرَّيْتَهَا عَنِ الضَّبْطِ فَإِنَّهَا بِالْفَتْحِ … غَيْرَ مُقْتَنِعٍ بِتَوْشِيحِ الْقِلَامِ».

## Flagged items and fixes

None. No claim needs qualification or is unsupported.

## Brief issues (all suggestions; no must-fix)

1. **Haywood source line** says "pp. 75 and 83–90", but the body now also cites p. 71 (`[^haywood|pp. 71, 88]`). Change it to "pp. 71, 75 and 83–90".
2. **Baalbaki URL** points to `pg=PA392`, while the only locator is p. 393. Change it to `pg=PA393`, or leave it: Google Books shows a CAPTCHA either way. The page number rests on footnote numbering in the snippets (notes 619–623 fall on p. 392; the sentence carries note 625). If a later reader can open the page view, confirm p. 393.
3. **EI² Fleisch (`ei2-fleisch`)** returned 403 to every tool in rounds 2 and 3. Crossref confirms the article exists under that title, but I could not confirm its author or text. Its only use (birth in Fārs, study in Iraq) is fully supported by the co-cited Sakhāwī pp. 79–80. Consider dropping `[^ei2-fleisch]` and its source entry. That costs no words and removes a source no verifier could open. Keep it only if someone confirms the visible abstract again.
4. **Length**: lede + body is 1,098 words by the validator, at the ceiling. Keep any further edit word-neutral.
5. Otherwise the essay meets the brief. It is an essay, not a list. Translations are labelled and every root is linked. The author's voice is kept apart from al-Jawharī's, the *Tāj*'s and the scholars it quotes. There are no rankings and no forced "root-meaning" narrative. onOurSite is concrete and promises nothing the site lacks.

## Sources and URLs

| id | Opens? | Stated work? | Notes |
|---|---|---|---|
| sakhawi | yes (shamela.ws/book/6675/2983) | yes; vol. 10 pp. 79–86, no. 274 | all locators confirmed |
| ei2-fleisch | **no: HTTP 403** (curl, DOI redirect, browser pane) | exists per Crossref (title "al-Fīrūzābādī", EI² Online) | author and text unverified; co-cited claim supported by Sakhāwī (see brief issue 3) |
| qamus-risala | yes (shamela.ws/book/7283) | yes | pages 26–29, 32, 315, 544–545, 727, 963–964, 1242, 1303 confirmed |
| baalbaki | CAPTCHA (page view); snippets via Google Books feed | yes (volume cme7AwAAQBAJ, *The Arabic Lexicographical Tradition*) | wording confirmed by snippet; page inferred |
| haywood | yes | yes | pp. 71, 75, 83–90 read |
| lane-preface | yes | yes | pp. xvi, xvii, xviii, xxii confirmed by marker offsets |
| taj-intro | yes (shamela.ws/book/7030/73) | yes; "ج1 - ص73" | quotation confirmed |
| britannica-sufism | yes in the browser pane (403 to curl/WebFetch) | yes; Schimmel and Britannica Editors, Sep. 21, 2026 | quotation confirmed |
| hawramani | yes | yes | no edition statement; "d. 1414 CE / 816 or 17 AH" |

Every listed source is cited in the text. I found no fabricated URL or quotation.

## Validator

`node scripts/validate-dictionary-guides.mjs al-qamus-al-muhit` → **ok**: 10 root links (10 distinct pairs), 5 excerpts, 1,098 words; example roots Alh, Ahl, drs, bdl, Sly, wjh. The guide slugs `al-muhkam` and `taj-al-arus` are in registry.ts. `/api/root/drs/dictionaries` lists the *Ṣiḥāḥ*, *Qāmūs* and *Tāj* entries that the essay links.

## Site-data issues

1. **Author label** "Firūzābādī" lacks the long mark on the first vowel. The name is al-Fīrūzābādī (الفيروزآبادي); Lane also records Fayrūzābādī. "Firū-" matches neither.
2. **Stored date 1414.** Al-Sakhāwī (vol. 10, p. 86) gives the night of 20 Shawwāl 817, which is 2 Jan 1415 (Julian; tabular calendar, recomputed). Haywood and Hawramani give 1414, and Lane gives 816 AH. The panel order is unaffected either way; 1415 matches al-Sakhāwī.
3. **Site English for the أ ه ل entry (id 1117).** The faithful translation says the proverb «سرعان ذا إهالة» is treated "under the root ع-ي-ن (ʿ-y-n)". That is wrong. في: العين means the chapter of roots ending in *ʿayn*, and the proverb is explained under س ر ع (Risāla p. 727). The essay is right; the stored English should be corrected.
