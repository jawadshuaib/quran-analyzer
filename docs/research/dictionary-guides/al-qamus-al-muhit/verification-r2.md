# al-Qāmūs al-Muḥīṭ — independent verification, round 2

Checked file: `roots/frontend/src/content/dictionary-guides/guides/al-qamus-al-muhit.ts` (state on 2026-09-26, after revision r1).
I did not open research-notes.md or any revision-*.md. I read verification-r1.md only for the list of earlier flags. Every source below was opened by me in this round, except where the table says otherwise.

Evidence used:

- **Risāla**: al-Fīrūzābādī, *al-Qāmūs al-Muḥīṭ*, Muʾassasat al-Risāla, 8th ed. 1426/2005, page-matched text on Shamela (book 7283; the card says "ترقيم الكتاب موافق للمطبوع"). Shamela page n corresponds to print page n + 24. I read print pp. 25–29 and 32 (preface) and pp. 315, 544, 727–728, 963–964, 1242 and 1303 from each page's page-number field.
- **Sakhāwī**: *al-Ḍawʾ al-Lāmiʿ*, Dār Maktabat al-Ḥayāt, vol. 10, pp. 79–86 (Shamela 6675/2983–2990). Biography no. 274 starts on p. 79.
- **Tāj intro**: al-Zabīdī, *Tāj al-ʿArūs*, Kuwait ed. (Shamela 7030, card: 40 vols, 1385–1422 AH = 1965–2001), vol. 1 p. 73.
- **Haywood**: *Arabic Lexicography* (1960), archive.org djvu text. I located page headers and read pp. 2, 71–75 and 83–90.
- **Lane**: Preface, laneslexicon.github.io. Inline page markers were located: 816 is on p. xvi; the Qāmūs critique on p. xvii; the Lāmiʿ discussion on pp. xvii–xviii; the Tāj on p. xviii; "well known" and "post-classical" on p. xxii.
- **Britannica**: "Sufism", section "Sufi thought and practice" (A. Schimmel), https://www.britannica.com/topic/Sufism/Sufi-thought-and-practice, read in the browser.
- **DB**: `_dict_guide_tool.py entry/grep/roots/root`, all displayed entries, plus the `verses` table (`text_uthmani`).
- **Not openable this round**: Brill EI² (both SIM-2383 and SIM-0132 return HTTP 403 from CloudFront to curl, WebFetch and the browser pane). Google Books for Baalbaki returned a reCAPTCHA, which I did not bypass. The Books API reports its quota exhausted.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title al-Qāmūs al-Muḥīṭ / القاموس المحيط | S | Risāla p. 27 «وسميته القاموس المحيط»; Shamela card |
| C2 | Gloss "The Encompassing Ocean" | S | p. 27 «لأنه البحر الأعظم»; Haywood p. 83 "the Surrounding Ocean" |
| C3 | Author al-Fīrūzābādī; Majd al-Dīn Abū l-Ṭāhir Muḥammad ibn Yaʿqūb; الفيروزآبادي | S | Sakhāwī p. 79 «المجد أبو الطاهر … الفيروزابادي»; Shamela card «مجد الدين أبو طاهر محمد بن يعقوب الفيروزآبادى (ت ٨١٧هـ)» |
| C4 | Period 729–817 AH / 1329–1415 CE | S | Sakhāwī p. 79 (born Rabīʿ II, or Jumādā II, 729 ≈ Feb–Apr 1329); p. 86 (died the night of 20 Shawwāl 817 at Zabīd). The tabular calendar gives 20 Shawwāl 817 = 2 Jan 1415 (Julian), so 1415 is right, though close to the year boundary. Variants: Haywood p. 83 "726/1326–817/1414"; Lane p. xvi "died in 816". The body acknowledges 816. A 726 birth is a minority date and needs no mention |
| C5 | Kind "Condensed general lexicon" | S | p. 27 «كتاب وجيز»; Lane p. xvii |
| C6 | Summary: fourteenth-century digest of *al-Muḥkam* and *al-ʿUbāb* | S | p. 27 «وضمنته خلاصة ما في العباب والمحكم»; the book existed by 790 (Sakhāwī pp. 85–86) |
| C7 | Summary: written with *al-Ṣiḥāḥ* in view, marking what it lacked and where he judged it wrong | S | pp. 27–28 |
| C8 | Summary: terse lists, abbreviations, few quotations; useful for surveying senses and vowellings | S | p. 28; Haywood p. 87; Lane p. xvii |
| C9 | Lede: quotations and "superfluities" removed; sixty volumes shrunk thirtyfold | S | p. 27 «خمنته في ستين سفرا … محذوف الشواهد مطروح الزوائد … لخصت كل ثلاثين سفرا في سفر» |
| C10 | Lede: *al-Ṣiḥāḥ* in view, adding and correcting | S | pp. 27–28 |
| C11 | Born 729/1329 in Fārs, near Shiraz | S | Sakhāwī p. 79 «بكازرون من أعمال شيراز» (Haywood p. 83 gives Kārzīn, also in Fārs) |
| C12 | Studied in Iraq | S | Sakhāwī p. 79 (Wāsiṭ, then Baghdad); p. 80; Haywood p. 83 |
| C13 | Last two decades as chief judge of Yemen at Zabīd; died there 817/1415 | S | Sakhāwī p. 81 (Zabīd Ramaḍān 796; qāḍī of all Yemen Dhū l-Ḥijja 797; «مدة تزيد على عشرين سنة»); p. 86 |
| C14 | "though some sources give 816" | S | Lane p. xvi "who was born in the year of the Flight 729, and died in 816"; Hawramani page "816 or 17 AH" |
| C15 | A contemporary quoted by al-Sakhāwī says he wrote the *Qāmūs* in Mecca, first at length, then abridged | S | Sakhāwī p. 83, «قال التقي الكرماني … جاور بمكة مدة عشر سنين أو أكثر وصنف بها … والقاموس مطولا في مجلدات عديدة ثم أمره والدي باختصاره فاختصر في مجلد ضخم» |
| C16 | By 790/1388 he had handed a copy to al-Maqrīzī | S | Sakhāwī p. 85 «وطول المقريزي … وقال أن آخر ما اجتمع به في مكة سنة تسعين», continuing on p. 86 «وقرأت عليه بعض مصنفاته وناولني قاموسه وأجازني» |
| C17 | Preface: began a work uniting *al-Muḥkam* and *al-ʿUbāb*; sixty volumes; too much for students; asked for something concise | S | pp. 26–27 |
| C18 | Quotation وألفت هذا الكتاب محذوف الشواهد مطروح الزوائد + translation | S | p. 27, verbatim; translation accurate |
| C19 | "every thirty volumes into one"; "the greatest sea" | S | p. 27 |
| C20 | The larger work was never finished | S | Lane pp. xvii–xviii (al-Fāsī, quoting al-Suyūṭī: "never completed"); Sakhāwī p. 82 «رأيت بخطه أيضا أنه كمل منه مجاليد خمسة» (five of an estimated hundred volumes) |
| C21 | Baalbaki: the *Qāmūs*'s "additions to those two sources" are mostly names of Companions, ḥadīth scholars, poets, places and plants, and "hardly substantiate" the two-thousand-works claim [baalbaki p. 393] | NQ | Not verifiable this round (Google CAPTCHA; API quota). verification-r1 quotes a p. 393 snippet: "…hardly substantiate its author's claim that it contains the digest of two thousand works (ṣarḥ alfay muṣannaf). Most of these additions are names of Companions…". The snippet does not show what "these additions" are additions *to* (the two sources? *al-Ṣiḥāḥ*?), so "to those two sources" is the essay's reading. The gist is corroborated elsewhere: Haywood p. 88 (critics: "filling his work with geographical and other proper names"); Sakhāwī p. 84 «وتعرض فيه لأكثر ألفاظ الحديث والرواة»; the displayed ب د ل entry lists Companions and muḥaddithūn |
| C22 | The preface claims the book distils two thousand works | S | Risāla p. 32 «وكتابي هذا … صريح ألفي مصنف من الكتب الفاخرة» |
| C23 | Poetry rare; the scholars behind a statement usually go unnamed | S | Haywood p. 87 ("omitted all reference to them and their authors, as well as the usual illustrative examples"); Lane p. xvii ("scarcely any examples from the poets") |
| C24 | Excerpt أ ل ه + translation | S | DB entry 114; matches Risāla p. 1242; translation checked |
| C25 | *Ṣiḥāḥ* أ ل ه: derives the name from *ilāh*, explains the lost hamza, Abū ʿAlī's argument, Sībawayh's alternative, verse for *ilāha* as a place and as the sun | S | DB entry 109 («وأصله إلاه على فعال … حذفت الهمزة … وسمعت أبا على النحوي … وجوز سيبويه … كفى حزنا … تروحنا من اللعباء») |
| C26 | *Qāmūs* drops the verse and lists snake and new moon, absent in *al-Ṣiḥāḥ* | S | Entries 114 vs 109 (in *al-Ṣiḥāḥ* the snake appears only in the story behind the verse; there is no *hilāl*) |
| C27 | Preface: people took to *al-Ṣiḥāḥ* "and it deserves that"; it missed "half the language or more", roots or rare senses | S | p. 27 «وهو جدير بذلك، غير أنه فاته نصف اللغة أو أكثر، إما بإهمال المادة، أو بترك المعاني الغريبة النادة» |
| C28 | Red ink; flags where al-Jawharī "went against what is right", "not to disparage him", because teachers relied on him | S | p. 27 «فكتبت بالحمرة المادة المهملة لديه»; p. 28 «ركب فيها الجوهري … خلاف الصواب، غير طاعن فيه … لتداوله واشتهاره … واعتماد المدرسين على نقوله» |
| C29 | In the 174 entries al-Jawharī is named sixteen times, always to correct him | S | `grep … الجوهر` gives 16 entries; `الجوهر.*الجوهر` gives 0 (so once each). Every one is a correction (غلط / وهم / باطل / تصحيف) |
| C30 | Excerpt أ ه ل + translation | S | DB entry 1117; Risāla pp. 963–964 |
| C31 | *Ṣiḥāḥ*: say *ahl*, not *mustaʾhil*, "the common people say it"; neither entry gives evidence for its ruling | S | DB entry 1112 «ولا تقل: مستأهل، والعامة تقوله». The verse it quotes supports another sense (taking *ihāla*), not the ruling |
| C32 | Lane, defending al-Jawharī: many corrections borrowed unacknowledged, many wrong | S | Lane p. xvii ("inserting criticisms of others, without acknowledgement … generally when they are false, (which is often the case) … in defence of El-Jowharee") |
| C33 | "Half the language" disputed; al-Shidyāq's sample count found more entries in *al-Ṣiḥāḥ*, excluding proper names | S | Haywood p. 75 |
| C34 | al-Zabīdī, the *Qāmūs*'s eighteenth-century commentator, credited it with 60,000 entries, 20,000 more than *al-Ṣiḥāḥ* | S | Tāj intro vol. 1 p. 73, in his own voice after «قلت»: «فإنه جمع فيه ستين ألف مادة، زاد على الجوهري بعشرين ألف مادة»; Haywood p. 89 ("compiled in Egypt in the Eighteenth Century"). Haywood p. 90 repeats the totals from "amateur statisticians" |
| C35 | Like *al-Ṣiḥāḥ*, filed by last letter (chapter), then first (section); *ilāh* in the chapter of *hāʾ* | S | Risāla p. 1242 «[باب الهاء] فصل الهمزة … ألَهَ»; Haywood pp. 71–75 (*al-Ṣiḥāḥ*, "The Rhyme Arrangement") and p. 88. Baalbaki p. 394 not seen |
| C36 | Abbreviations ع د ة ج م | S | p. 28 «مكتفيا بكتابة: ع، د، ة، ج، م، عن قولي: موضع، وبلد، وقرية، والجمع، ومعروف» |
| C37 | Our entries also use جج for plural of plural | S | Sakhāwī p. 84 «وعن جمع الجمع بجج»; Haywood p. 86; DB (frq, fwq and others) |
| C38 | *bi-hāʾ* = add the ending *-a* | S | p. 28 «أتبعتها المؤنث بقولي: وهي بهاء (ولا أعيد الصيغة)»; Haywood p. 87 |
| C39 | Vowelling: undescribed = *a*; "with *u*/*i*"; *muḥarraka* (second consonant also *a*, as in *ḥasan*); *yuthallath*; model words | S | p. 28 «وكل كلمة عريتها عن الضبط فإنها بالفتح … فأقيده بصريح الكلام غير مقتنع بتوشيح القلام»; Haywood p. 87 (*muḥarrak*, *ḥasan*, damma/kasra, model words). *yuthallath* is in entries (Alh «ويثلث») |
| C40 | A verb without its present tense conjugates like *kataba* | S | p. 28 «أو الماضي بدون الآتي، ولا مانع؛ فالفعل على مثال كتب» |
| C41 | In print a dash repeats the word just defined, verb or noun (وـ للبيت) | S | Risāla p. 963 «وأهل الأمر: ولاته، وـ للبيت: سكانه»; drs entry «وـ المرأة … وـ الكتاب» repeats the verb. This is a description of the printed and stored text, not something the preface states |
| C42 | في: العين in *ahl* points to the *ʿayn* chapter, where the proverb is explained under *sarʿān* | S | p. 964 «و"سرعان ذا إهالة"، في: العين»; p. 727 (فصل السين of باب العين) «وأما "سرعان ذا إهالة" فأصله…». The explanation is all on p. 727; p. 728 only continues the root |
| C43 | Lane: "what was once 'well known' has long ceased to be so"; glosses "meant to be understood in post-classical senses" | S | Lane p. xxii (transcription typo "was one") |
| C44 | Excerpt 1 د ر س + translation | S | DB entry 8655; Risāla p. 544 |
| C45 | Threshing, mange, worn garment follow, among others | S | Entry 8655 (a sexual sense comes before threshing; "among others" covers it) |
| C46 | No relation stated between an effaced trace and reading | S | Entry 8655 |
| C47 | Excerpt 2 (Idrīs; *dārasta*) + translation | S | Entry 8655; translation accurate |
| C48 | *Ṣiḥāḥ*, with "it is said": Idrīs named for his much study of God's book (Q 19:56) | S | DB entry 8652 «ويقال سمى إدريس عليه السلام لكثرة دراسته كتاب الله تعالى»; verses 19:56 «إِدْرِيسَ» |
| C49 | *Qāmūs* rejects this without naming anyone; reason, not evidence | S | Entry 8655 «ليس من الدراسة، كما توهمه كثيرون، لأنه أعجمي» |
| C50 | Our text of Q 6:105 reads *darasta*; *dārasta* is another reading; the *Qāmūs* does not say whose gloss it is | S | verses 6:105 «وَلِيَقُولُوا۟ دَرَسْتَ»; entry 8655 |
| C51 | "al-Zabīdī's commentary … **puts back what was cut**", and then the examples: reading names, Ibn ʿAbbās, and on Idrīs Ibn Khaṭīb al-Dahsha and Ibn al-Jawwānī | NQ | Ibn Khaṭīb al-Dahsha (Maḥmūd b. Aḥmad al-Fayyūmī al-Ḥamawī) lived 750–834 AH / 1349–1431 CE (tarajm.com/people/24193, citing al-Sakhāwī, al-Shawkānī and al-Ziriklī). He died after al-Fīrūzābādī, so his view cannot have been "cut" from the *Qāmūs*. The displayed *al-Muḥkam* د ر س entry, one of the *Qāmūs*'s two sources, gives both readings of 6:105 without naming Ibn Kathīr, Abū ʿAmr or Ibn ʿAbbās. The *Tāj* adds these names; the essay cannot show they were "put back" |
| C52 | *Tāj* names *dārasta* as the reading of Ibn Kathīr and Abū ʿAmr and credits the gloss to Ibn ʿAbbās | S | DB Tāj entry 8653 «وليقولوا دارست في قراءة ابن كثير وأبي عمرو، وفسره ابن عباس … قرأت على اليهود، وقرؤوا عليك» |
| C53 | *Tāj* on Idrīs: Ibn Khaṭīb al-Dahsha for the foreign origin, followed by a verdict that it is sounder; Ibn al-Jawwānī for the derivation from study | S | Entry 8653 «وقال ابن خطيب الدهشة: وهو اسم أعجمي … وقيل: إنما سمي به لكثرة درسه، ليكون عربيا. والأول أصح. وقال ابن الجواني: سمي إدريس لدرسه الثلاثين صحيفة» |
| C54 | Good at range; cannot show a sense's age, users or Qur'anic-era status | S | Interpretive; follows from C9 and C23 |
| C55 | *al-abdāl*: a word the Qur'an does not use, and "a rank in the Sufi hierarchy of saints" [ei2-abdal] | NQ | Not in the Qur'an: no match in `verses`. The substance is correct: Britannica "Sufism" says "The invisible hierarchy of saints consists of the 40 abdāl ('substitutes'…)". But the cited EI² page (SIM-0132) returned HTTP 403 to every tool I tried, so I could not confirm what the citation is said to contain |
| C56 | Excerpt ب د ل + translation; defined with no source or date | S | DB entry 2636 |
| C57 | *Tāj* quotes the *Qāmūs* and restores the authorities, quotations and missing words | S | Lane p. xviii ("exhibiting fully and clearly, from the original sources, innumerable explanations which are so abridged in the latter work"); Haywood pp. 89–90 (the *Qāmūs* text in brackets; "mention of authorities", "illustrative quotations", "additional words … and also entirely new roots"). Baalbaki p. 398 not seen. "missing words" is a fair reading of "additional words" |
| C58 | *qāmūs*, "ocean", came to mean "dictionary" | S | Haywood pp. 2, 83, 85. Baalbaki p. 392 not seen |
| C59 | onOurSite: shown for only 174 roots | S | `dicts`: displayed entries = 174 |
| C60 | onOurSite: Hawramani names no edition; the *ilāh*, *ahl* and *darasa* entries match the Risāla edition | S | Hawramani page (no edition statement); I compared entries 114, 1117 and 8655 with Risāla pp. 1242, 963–964 and 544: identical |
| C61 | onOurSite: red ink lost; و/ي article signs lost; ص ل ي shows only the *yāʾ* article; *ṣalāt* is in the *wāw* article, not displayed | S | Risāla p. 1303 «• ي: صلى اللحم …» then «• و: الصلا … والصلاة: الدعاء»; entry 4186 begins without «ي:»; `root Slw` lists no Qāmūs entry |
| C62 | onOurSite: the و ج ه line is the separate *kunābid* article; some short entries are not the article for their root | S | Risāla p. 315 «• وجه كنابد، بالضم: قبيح.»; DB entry 1679; also vwb («ثوب خذاريم»), Abl («إبل محاليد»), jwE («جوع هلقت») |

**Totals: 62 claims: 59 supported, 3 need qualification, 0 unsupported.**

## Round-1 flags: status

| r1 flag | Status now |
|---|---|
| C4 death-date variant | Fixed: body says "though some sources give 816" [lane p. xvi], which I confirmed |
| C7 summary purpose | Fixed: the summary now leads with the digest of *al-Muḥkam* and *al-ʿUbāb* |
| C22 Baalbaki "modest"/"medical" | Those words are gone. The Baalbaki sentence itself is still unverifiable by me; see C21 |
| C34 al-Zabīdī's 20,000 | Fixed and confirmed at Tāj vol. 1 p. 73 |
| C41 dash | Fixed; confirmed at Risāla p. 963 |
| C52 Tāj verdict on Idrīs | Fixed: the attribution is now accurate (my C53). The new framing "puts back what was cut" introduces a separate problem (C51) |

## Flagged items and fixes

1. **C51, "puts back what was cut" (body, darasa section).** Ibn Khaṭīb al-Dahsha died in 834/1431, after al-Fīrūzābādī. The reading names and Ibn ʿAbbās are not in the displayed *al-Muḥkam* entry either. **Fix** (word-neutral): change "al-Zabīdī's commentary, [[root:drs|murtada-…|Tāj al-ʿArūs]], puts back what was cut:" to "al-Zabīdī's commentary, [[root:drs|murtada-…|Tāj al-ʿArūs]], supplies what is missing:". Or use "fills in the names:". The rest of the sentence can stay.
2. **C21, Baalbaki on the additions (body ¶3).** I could not open p. 393. The snippet quoted in round 1 does not show what the additions are additions *to*. **Fix:** either (a) have someone with preview access confirm on p. 393 both the wording and that the additions are to *al-Muḥkam*/*al-ʿUbāb*, or (b) make the sentence not depend on that referent and co-cite sources that were seen: "Much of what it adds is names (of Companions, ḥadīth scholars, poets and places) and plants; Ramzi Baalbaki finds this hardly bears out the preface's claim to distil two thousand works.[^baalbaki|p. 393][^qamus-risala|p. 32][^haywood|p. 88]". Under (b), drop "to those two sources" and the quotation marks around "hardly substantiate" unless the page is read.
3. **C55, al-abdāl citation.** The substance is confirmed, but EI² returned 403 to every tool, so the cited page could not be checked. **Fix:** add a co-citation to a source that opens: Annemarie Schimmel, "Sufism", *Encyclopaedia Britannica*, https://www.britannica.com/topic/Sufism/Sufi-thought-and-practice ("The invisible hierarchy of saints consists of the 40 abdāl ('substitutes')…"). Keep [^ei2-abdal] only if its text is confirmed.

## Brief issues

- **suggestion:** Lede + body is now 1,100 words, the ceiling. Every fix above must be word-neutral (fix 1 is).
- **suggestion:** The `baalbaki` source line says pp. 392–93 and 398 were "read in the Google Books preview". Neither verifier could reproduce this, and the r1 reviser reports he could not open p. 393. Unless someone did read those pages, change it to "search snippets only", or drop the Baalbaki-only locators that are already co-cited (pp. 392, 394, 398).
- **suggestion:** In the closing sentence, "restores the authorities, quotations and missing words" would be more exact as "adds the authorities, quotations and further words". Haywood pp. 89–90 describes additions, and some *Tāj* authorities are later than the *Qāmūs* (see C51).
- **suggestion:** The vowelling sentence cites only Haywood p. 87. "A word left undescribed normally has *a*" and the refusal to rely on pen-marks come from the preface itself; add [^qamus-risala|p. 28].
- **suggestion:** The cross-reference locator [^qamus-risala|pp. 727–728] could be p. 727 alone: the proverb's explanation is all on p. 727.
- No must-fix brief issues. The piece reads as an essay, not a list. Translations are labelled and every root is linked. The author's voice is kept apart from al-Jawharī's and the *Tāj*'s. No rankings, and no forced "root-meaning" narrative. onOurSite is concrete and does not promise material the site lacks.

## Sources and URLs

| id | URL opens? | Stated work? | Notes |
|---|---|---|---|
| sakhawi | yes (shamela.ws/book/6675/2983) | yes; card: Dār Maktabat al-Ḥayāt; page title "ج10 - ص79"; no. 274 | pp. 79–86 read |
| ei2-fleisch | **no: HTTP 403 (CloudFront) to curl, WebFetch and the browser pane** | could not confirm | Round 1 reports the abstract was visible then. Its only use (birth, study in Iraq) is co-cited to Sakhāwī pp. 79–80, which I confirmed |
| qamus-risala | yes (shamela.ws/book/7283) | yes; 8th ed. 1426/2005, Risāla, supervised by al-ʿArqsūsī | page mapping n + 24 confirmed from page fields |
| baalbaki | Google Books: reCAPTCHA in the browser; the edition page shows metadata only; API quota exhausted | yes (Brill 2014, ISBN 9789004274013) | no page text seen this round |
| haywood | yes (archive.org djvu text) | yes | pp. 2, 71–75, 83–90 read |
| lane-preface | yes | yes | pp. xvi–xviii, xxii located by inline markers |
| taj-intro | yes (shamela.ws/book/7030/73) | yes; card: Kuwait, 40 vols, 1385–1422 AH / 1965–2001; page title "ج1 - ص73" | quotation confirmed |
| ei2-abdal | **no: HTTP 403** | could not confirm | substance confirmed via Britannica (see fix 3) |
| hawramani | yes | yes | no edition statement; gives "d. 1414 CE / 816 or 17 AH" |

Every listed source is cited in the text. No fabricated URL found. The two EI² URLs have the right form for Brill's EI² Online, but I could not open them.

## Validator

`node scripts/validate-dictionary-guides.mjs al-qamus-al-muhit` → **ok**: 10 root links (10 distinct pairs), 5 excerpts, 1,100 words; example roots Alh, Ahl, drs, bdl, Sly, wjh. The guide slugs `al-muhkam` and `taj-al-arus` exist in registry.ts.

## Site-data issues

1. **Author label** "Firūzābādī" lacks the macron on the first vowel (al-Fīrūzābādī, الفيروزآبادي). Lane p. xvi records "Feyroozábádee / Feeroozábádee", so Fayrūzābādī is also heard, but "Firū-" matches neither.
2. **Stored date 1414.** Al-Sakhāwī (vol. 10, p. 86) gives the night of 20 Shawwāl 817. By the tabular calendar that is 2 January 1415 (Julian), and "the night of the 20th" is the evening of 1 January. So 1415 is the better CE year, though a one- or two-day sighting difference could put it on 31 December 1414. Haywood (p. 83) and Hawramani give 1414; Lane gives 816 AH. Either year is defensible, and the panel order is unaffected (al-Fayyūmī 1368 < 1414/1415 < al-Zabīdī 1790). No change is required. If the site follows al-Sakhāwī strictly, use 1415.
3. **Site English rendering of the أ ه ل entry (id 1117).** Both the "faithful translation" and the harmonized English render «و"سرعان ذا إهالة"، في: العين» as treated "under the root ʿ-y-n". That is wrong: في: العين means the chapter of roots ending in *ʿayn*, and the proverb is explained under س ر ع (Risāla p. 727). The essay is right; a reader comparing it with the site's English will meet a contradiction. The English rendering should be corrected.
