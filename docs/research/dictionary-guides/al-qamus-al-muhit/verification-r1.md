# al-Qāmūs al-Muḥīṭ — independent verification, round 1

Checked file: `roots/frontend/src/content/dictionary-guides/guides/al-qamus-al-muhit.ts` (as of 2026-09-26).
The research notes and any revision files were NOT opened. Every source below was opened by the verifier.

Primary evidence used:

- **Risāla** = al-Fīrūzābādī, *al-Qāmūs al-Muḥīṭ*, Muʾassasat al-Risāla, 8th ed. 2005, page-matched text on Shamela, https://shamela.ws/book/7283 (Shamela page n = print page n+24 in the preface; print page read from each page's page-number field). Preface = print pp. 25–32.
- **Sakhāwī** = *al-Ḍawʾ al-Lāmiʿ*, Dār Maktabat al-Ḥayāt, vol. 10 (page title "ج10 - ص79"), biography no. 274, https://shamela.ws/book/6675/2983 to /2990 (= pp. 79–86).
- **Tāj intro** = al-Zabīdī, *Tāj al-ʿArūs*, introduction, Shamela book 7030, page 73 (https://shamela.ws/book/7030/73).
- **Haywood** = *Arabic Lexicography* (1960), archive.org djvu text (URL in the guide), pp. 75, 83–88.
- **Lane** = Preface to the *Lexicon*, laneslexicon.github.io transcription, pp. xvi–xviii, xxii.
- **EI2** = Fleisch, "al-Fīrūzābādī": only the free abstract (birth 729/1329 at Kāzarūn near Shīrāz; Shīrāz, Wāsiṭ, Baghdad 745/1344; Damascus 750/1349).
- **Baalbaki** = Google Books, snippet view only. Search for "hardly substantiate" → p. 393 snippet: "…hardly substantiate its author's claim that it contains the digest of two thousand works (ṣarḥ alfay muṣannaf). Most of these additions are names of Companions of the Prophet, scholars of Ḥadīth, poets, place names and plants…". A search for "medical" also returns p. 393 among 4 hits (snippet not read). After that Google put up a CAPTCHA, which was not bypassed, so pp. 392, 394 and 398 **could not be checked**.
- **DB** = `_dict_guide_tool.py entry …` (displayed entries only) plus a direct count over the 174 displayed Qāmūs entries.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title al-Qāmūs al-Muḥīṭ / القاموس المحيط (title, titleAr) | S | Risāla preface p. 27 "وسميته القاموس المحيط"; Shamela card |
| C2 | Gloss "The Encompassing Ocean" (titleGloss) | S | Preface p. 27 "لأنه البحر الأعظم"; Haywood p. 83 "the Surrounding Ocean" |
| C3 | Author al-Fīrūzābādī; full name Majd al-Dīn Abū l-Ṭāhir Muḥammad ibn Yaʿqūb; الفيروزآبادي | S | EI2 abstract; Sakhāwī p. 79 "المجد أبو الطاهر … الفيروزابادي"; Shamela card "مجد الدين أبو طاهر محمد بن يعقوب الفيروزآبادى (ت ٨١٧هـ)" |
| C4 | Period 729–817 AH / 1329–1415 CE (period) | NQ | Sakhāwī p. 86: died the night of 20 Shawwāl 817 at Zabīd (≈ 2 Jan 1415 by calculation); birth Rabīʿ II or Jumādā II 729 (p. 79; EI2). But Lane p. xvi gives death as 816, Haywood p. 83 gives birth 726/1326, and Hawramani gives "816 or 17". The variant is not acknowledged anywhere |
| C5 | Kind "Condensed general lexicon" | S | Preface p. 27 (كتاب وجيز); Lane p. xvii |
| C6 | Summary: 14th-c.; vast vocabulary in terse lists; abbreviations; most quotations and sources dropped | S | Existed by 790/1388 (Sakhāwī pp. 85–86); preface pp. 27–28; Haywood p. 87 |
| C7 | Summary: "Written to add to and correct al-Jawharī's *al-Ṣiḥāḥ*" | NQ | Preface p. 27: its stated purpose is a concise digest of the planned *Lāmiʿ* (i.e. *al-Muḥkam* + *al-ʿUbāb*); marking what *al-Ṣiḥāḥ* lacks and flagging its errors is a secondary aim he states afterwards ("ولما رأيت إقبال الناس على صحاح الجوهري…"). The body gets this right, but the summary makes it the purpose |
| C8 | Summary: useful for surveying senses, vowellings, variants | S | Interpretive; consistent with preface p. 28 and entries |
| C9 | Lede: removed quotations and "superfluities"; sixty volumes would shrink thirtyfold | S | Preface p. 27 "خمنته في ستين سفرا … محذوف الشواهد مطروح الزوائد … لخصت كل ثلاثين سفرا في سفر" |
| C10 | Lede: wrote with *al-Ṣiḥāḥ* in view, adding and correcting | S | Preface pp. 27–28 |
| C11 | Born 729/1329 in Fārs near Shiraz | S | Sakhāwī p. 79 "بكازرون من أعمال شيراز"; EI2 abstract |
| C12 | Studied in Iraq | S | Sakhāwī pp. 79–80 (Wāsiṭ, Baghdad); EI2 |
| C13 | Long stretches in Mecca | S | Sakhāwī p. 83 (al-Kirmānī: "جاور بمكة مدة عشر سنين أو أكثر"); p. 85 (al-Fāsī: 5 or 6 consecutive years, repeated stays) |
| C14 | Last two decades as chief judge of Yemen at Zabīd; died there 817/1415 | S | Sakhāwī p. 81 (arrived Zabīd Ramaḍān 796; qāḍī of all Yemen Dhū l-Ḥijja 797; "مدة تزيد على عشرين سنة"); p. 86 (death at Zabīd, 817) |
| C15 | A contemporary quoted by al-Sakhāwī says he wrote the *Qāmūs* in Mecca, first at length then abridged | S | Sakhāwī p. 83, al-Taqī al-Kirmānī: "وصنف بها … والقاموس مطولا في مجلدات عديدة ثم أمره والدي باختصاره فاختصر في مجلد ضخم" |
| C16 | al-Maqrīzī last met him in Mecca in 790/1388; the author handed him a copy | S | Sakhāwī pp. 85–86: "قال أن آخر ما اجتمع به في مكة سنة تسعين … وناولني قاموسه وأجازني". (*Nāwalanī* is formal transmission by handing over, *munāwala*; "handed him a copy" is fair.) 790 AH = 1388 CE |
| C17 | Preface: began a book uniting *al-Muḥkam* and *al-ʿUbāb*; sixty volumes; too much for students; asked for a concise book | S | Preface pp. 26–27 |
| C18 | Quotation وألفت هذا الكتاب محذوف الشواهد مطروح الزوائد + translation | S | Preface p. 27, verbatim; translation accurate |
| C19 | "every thirty volumes into one"; named for "the greatest sea" | S | Preface p. 27 |
| C20 | The larger work was never finished; al-Sakhāwī saw a note in his hand that five volumes were done | S | Sakhāwī p. 82 "رأيت بخطه أيضا أنه كمل منه مجاليد خمسة"; Lane pp. xvii–xviii (non-completion "certain") |
| C21 | Two main sources *al-Muḥkam* and *al-ʿUbāb* | S | Preface p. 27; Lane p. xvii |
| C22 | Baalbaki: additions "modest, mostly proper names, places, plants and medical terms"; "hardly substantiate" the preface's claim of two thousand books | NQ | The p. 393 snippet confirms "hardly substantiate", the two-thousand-works claim, and the list "Companions, scholars of Ḥadīth, poets, place names and plants". "Modest" and "medical terms" were not seen in anything readable. The claim itself is at Risāla p. 32 ("صريح ألفي مصنف"). Haywood p. 88 does report critics' complaint of "too many technical terms, especially medical" |
| C23 | Poetry rare; scholars' names usually gone | S | Haywood p. 87 ("omitted all reference to them and their authors, as well as the usual illustrative examples"); Lane p. xvii ("scarcely any examples from the poets") |
| C24 | Excerpt, أ ل ه (Alh), and its translation | S | DB entry 114; matches Risāla p. 1242; translation checked, accurate |
| C25 | *Ṣiḥāḥ* on أ ل ه: derives the name from *ilāh*; explains the lost hamza; Abū ʿAlī's argument; Sībawayh's alternative; verse for *ilāha* as a place and as the sun | S | DB entry 109 |
| C26 | *Qāmūs* drops the verse; gives snake and new moon, which *al-Ṣiḥāḥ* does not | S | Entries 114 vs 109 (*al-Ṣiḥāḥ* mentions a snake only in the story behind the verse, not as a sense of *ilāha*) |
| C27 | Preface: people took to *al-Ṣiḥāḥ* "and it deserves that"; it missed "half the language or more", whole roots or rare senses | S | Preface p. 27 |
| C28 | Red ink for roots it lacked; flags where al-Jawharī "went against what is right", "not to disparage him", because teachers relied on it | S | Preface pp. 27–28 |
| C29 | In the 174 displayed entries al-Jawharī is named 16 times, always to correct him | S | DB regex count over the displayed entries: exactly 16 (nSr, xlf, Ahl, rjl, Elw, *hb, gfl, sEy, Esy, xzy, srq, kAs, lwy, dhn, rqy, Dgv), each a correction (غلط / وهم / باطل / تصحيف) |
| C30 | Excerpt, أ ه ل (Ahl), and its translation | S | DB entry 1117; Risāla pp. 963–964 |
| C31 | *Ṣiḥāḥ*: say *ahl*, not *mustaʾhil*, "the common people say it"; neither entry gives evidence for the ruling | S | DB entry 1112 "ولا تقل: مستأهل، والعامة تقوله" |
| C32 | Lane, defending al-Jawharī: many corrections borrowed unacknowledged from earlier critics, many wrong | S | Lane p. xvii |
| C33 | al-Shidyāq's sample count found more entries in *al-Ṣiḥāḥ* once proper names were set aside | S | Haywood p. 75 |
| C34 | "al-Zabīdī counted twenty thousand items in the *Qāmūs* that *al-Ṣiḥāḥ* lacks" [^baalbaki p. 393] | NQ | Not verifiable at Baalbaki p. 393. Primary text, Tāj intro (Shamela 7030/73): "جمع فيه ستين ألف مادة، زاد على الجوهري بعشرين ألف مادة". That is a statement of totals (60,000 entries, 20,000 more than al-Jawharī), not an item-by-item count |
| C35 | Arranged by last radical (chapter), then first (section); *ilāh* in the chapter of *hāʾ* | S | Risāla table of contents; p. 1242 "[باب الهاء] فصل الهمزة … أله"; Haywood p. 88 (rhyme order) |
| C36 | Abbreviations ع د ة ج م | S | Preface p. 28 |
| C37 | Our entries also use جج for plural of plural | S | Sakhāwī p. 84 ("وعن جمع الجمع بجج"); Haywood p. 86; DB (frq, *hb, fwq, ESm, lwy) |
| C38 | *bi-hāʾ* = add the ending *-a* | S | Preface p. 28 "وهي بهاء"; Haywood p. 87. Not cited in the essay |
| C39 | Vowelling: undescribed = *a*; "with *u*/*i*"; *muḥarraka*; *yuthallath*; model words such as *fariḥa* | S | Preface p. 28; Haywood p. 87. *Yuthallath* is not in Haywood but is attested in entries (e.g. Alh, Hyv) |
| C40 | A verb without its present tense conjugates like *kataba* | S | Preface p. 28 (with the proviso "ولا مانع") |
| C41 | "A dash stands for the verb just given." | NQ | No citation. The dash (وـ) repeats the headword just given, which may be a noun: in the displayed أ ه ل entry, "وأهل الأمر: ولاته، وـ للبيت: سكانه" repeats the noun *ahl*. The symbol also belongs to the printed edition's layout; the preface does not describe it |
| C42 | في: العين in *ahl* points to the *ʿayn* chapter, where the proverb is explained under *sarʿān* | S | Risāla p. 964 ("و'سرعان ذا إهالة'، في: العين"); p. 727 (the proverb's origin explained in س ر ع) |
| C43 | Lane: "what was once 'well known' has long ceased to be so"; glosses "meant to be understood in post-classical senses" | S | Lane p. xxii (the transcription's typo "was one" aside) |
| C44 | Excerpt 1, د ر س (drs), and its translation | S | DB entry 8655; Risāla (Shamela 7283/520 = p. 544) |
| C45 | Threshing, camel mange and a worn-out garment follow | S | Entry 8655 (a sexual sense sits in between; omitting it is not an error) |
| C46 | The entry does not relate effacement to reading | S | Entry 8655 |
| C47 | Excerpt 2 (Idrīs; *dārasta*) and its translation | S | Entry 8655; translation accurate |
| C48 | *Ṣiḥāḥ*: "it is said" Idrīs was named for his much study of God's book (Q 19:56) | S | DB entry 8652 "ويقال سمى إدريس … لكثرة دراسته كتاب الله تعالى"; Q 19:56 names Idrīs (verses table) |
| C49 | *Qāmūs* rejects this without naming anyone; gives a reason, not evidence | S | Entry 8655 |
| C50 | Our site's text of Q 6:105 reads *darasta*; *dārasta* is another reading; the *Qāmūs* does not attribute the gloss | S | verses table: "وَلِيَقُولُوا۟ دَرَسْتَ"; entry 8655 |
| C51 | *Tāj* gives *dārasta* as the reading of Ibn Kathīr and Abū ʿAmr and credits the gloss to Ibn ʿAbbās | S | DB Tāj entry drs "في قراءة ابن كثير وأبي عمرو، وفسره ابن عباس … قرأت على اليهود، وقرؤوا عليك" |
| C52 | *Tāj* reports the Idrīs view the *Qāmūs* dismissed, "while judging the *Qāmūs*'s view sounder" | NQ | Tāj: "وقال ابن خطيب الدهشة: وهو اسم أعجمي … وقيل: إنما سمي به لكثرة درسه، ليكون عربيا. والأول أصح." The verdict follows a quotation from Ibn Khaṭīb al-Dahsha and may be his, not al-Zabīdī's. The Tāj also reports Ibn al-Jawwānī's derivation (from studying thirty ṣaḥīfas) without refuting it |
| C53 | Good at range; cannot show how old a sense is or who used it | S | Interpretive; follows from C9, C23 |
| C54 | Excerpt, ب د ل (*al-abdāl*): not a Qur'anic word, defined with no source or date | S | DB entry 2636; no أبدال in the verses table |
| C55 | *Tāj* quotes the *Qāmūs* and restores authorities, quotations and missing words | S | Lane p. xviii ("exhibiting fully and clearly, from the original sources, innumerable explanations which are so abridged in the latter work…"). Baalbaki p. 398 not seen |
| C56 | *qāmūs* came to mean "dictionary" | S | Haywood pp. 83, 85. Baalbaki p. 392 not seen |
| C57 | onOurSite: 174 roots displayed | S | `_dict_guide_tool.py dicts` |
| C58 | Hawramani does not say which edition it follows | S | https://arabiclexicon.hawramani.com/firuzabadi-al-qamus-al-muhit/ (no edition statement found on the page) |
| C59 | The *ilāh*, *ahl* and *darasa* entries match the Risāla edition word for word | S | Risāla pp. 1242, 963–964, 544 |
| C60 | Red ink lost; و/ي article signs lost; ص ل ي shows only the *yāʾ* article; *ṣalāt* is in the *wāw* article, not displayed | S | Risāla p. 1303 ("ي: صلى اللحم…" then "و: الصلا … والصلاة: الدعاء"); DB: no displayed Qāmūs entry for Slw |
| C61 | The و ج ه line is the separate *kunābid* article | S | Risāla p. 315 "• وجه كنابد، بالضم: قبيح." |
| C62 | Some one- or two-line entries are not the article for their root | S | DB short entries vwb, Abl, jwE, bld, Drb, jml, bHr, ArD are all phrase-headed lines from other articles |

**Totals: 62 claims — 56 supported, 6 need qualification, 0 unsupported.**

## Flagged items and fixes

1. **C4, period / death date.** Keep 817/1415 (al-Sakhāwī gives an exact date, 20 Shawwāl 817), but acknowledge the variant. In the body change "where he died in 817/1415" to "where he died in 817/1415 (some sources give 816)". Cite Sakhāwī p. 86 for the date and Lane p. xvi for 816. In `period` you can keep "729–817 AH / 1329–1415 CE"; this variant does not need a "c.".
2. **C7, summary.** Replace "Written to add to and correct al-Jawharī's *al-Ṣiḥāḥ*;" with "A concise digest of *al-Muḥkam* and *al-ʿUbāb*, written with al-Jawharī's *al-Ṣiḥāḥ* in view, marking what it lacked and what he thought it got wrong;".
3. **C22, Baalbaki on additions.** Drop "modest" and "medical terms", or read p. 393 in full and confirm them. Suggested wording: "Ramzi Baalbaki notes that its additions to them, mostly names of Companions, ḥadīth scholars, poets, places and plants, 'hardly substantiate' the author's claim that the book distils two thousand works[^baalbaki|p. 393]". Add a citation for the claim itself: [^qamus-risala|p. 32] ("صريح ألفي مصنف").
4. **C34, al-Zabīdī's 20,000.** Change to: "while al-Zabīdī put the *Qāmūs* at sixty thousand entries, twenty thousand more than *al-Ṣiḥāḥ*". Cite the *Tāj* introduction (Shamela 7030, p. 73: "جمع فيه ستين ألف مادة، زاد على الجوهري بعشرين ألف مادة"), which means adding a Tāj edition source, or keep [^baalbaki|p. 393] only after confirming that page says this.
5. **C41, the dash.** Change "A dash stands for the verb just given." to "In printed texts a dash (ـ) repeats the headword just given, verb or noun, as in وـ للبيت 'the *ahl* of a house'."
6. **C52, Tāj verdict on Idrīs.** Change "…and reports the view on Idrīs that the *Qāmūs* dismissed, while judging the *Qāmūs*'s view sounder." to "…and reports the derivation of Idrīs's name that the *Qāmūs* dismissed, along with a verdict, quoted after Ibn Khaṭīb al-Dahsha, that the non-Arabic origin is sounder."

## Brief issues (not factual)

- **suggestion:** The page is at 1,099 words (lede + body), the ceiling. Any wording added in revision (e.g. fix 1) must be offset by cuts. The first two paragraphs of "A big book made small" (itinerary, al-Maqrīzī) could lose a clause.
- **suggestion:** Several claims carried only by Baalbaki cannot be checked from the snippet view (pp. 392, 394, 398). Add co-citations to sources that were seen: Haywood pp. 83, 85 for *qāmūs* = "dictionary"; Haywood p. 88 / Risāla table of contents for the rhyme arrangement; Lane p. xviii for the *Tāj* restoring what was abridged.
- **suggestion:** The *bi-hāʾ* sentence (C38) has no citation; add [^qamus-risala|p. 28] or [^haywood|p. 87].
- **suggestion:** "vowelled (*muḥarraka*)" needs a brief gloss: second consonant also takes *a*, as in *ḥasan* (Haywood p. 87). Otherwise readers will not know what it means.
- **suggestion:** The *al-abdāl* example makes its point (no source, no date), but it does not tell readers what kind of term this is. If a reliable source can be cited identifying it as a post-Qur'anic religious concept, one clause would serve the site's aim of flagging later usage. If not, leave it as is. Do not assert it unsourced.
- **suggestion:** The "Threshing … follow" sentence silently skips one sense. Fine as a summary; optionally "…follow, among others".
- No must-fix brief issues. The essay is not padded, gives no rankings, reads as an essay, links every root, labels its translations, keeps the author's voice separate from al-Jawharī's and the *Tāj*'s, and does not force a root-meaning narrative. onOurSite is specific and does not promise missing material.

## Sources and URLs

| Source | Opens? | Is the stated work? | Notes |
|---|---|---|---|
| sakhawi, https://shamela.ws/book/6675/2983 | yes | yes: Dār Maktabat al-Ḥayāt ed., page title "ج10 - ص79", no. 274 | pp. 79–86 all read |
| ei2-fleisch, Brill | yes (curl 200; WebFetch 403) | yes: H. Fleisch, EI2 | only the abstract is visible (birth, early study); the citation states this honestly. It does not itself support the Mecca/Zabīd/death part of the sentence; al-Sakhāwī does |
| qamus-risala, https://shamela.ws/book/7283 | yes | yes: Risāla 8th ed. 1426/2005, "ترقيم الكتاب موافق للمطبوع" | pp. 26–28, 32, 315, 544, 727, 963–964, 1242, 1303 checked. The Shamela preface has bracketed glosses added by the Shamela preparer; the essay's quotation contains none |
| baalbaki, Google Books | yes | yes: Brill 2014 | snippet view only for me (p. 393 "No preview available"); the citation's "read in the Google Books preview" for pp. 392–93 could not be reproduced (previews vary by user). Google CAPTCHA blocked further searches (not bypassed) |
| haywood, archive.org djvu text | yes | yes | pp. 75, 83–88 read |
| lane-preface, laneslexicon.github.io | yes | yes | pp. xvi–xviii, xxii read |
| hawramani | yes | yes | no edition statement |

No source is listed but unused. No fabricated URL found.

## Validator

`node scripts/validate-dictionary-guides.mjs al-qamus-al-muhit` → **ok** (10 root links, 5 excerpts, 1,099 words; example roots Alh, Ahl, drs, bdl, Sly, wjh). The guide slugs `al-muhkam` and `taj-al-arus` exist in registry.ts.

## Site-data issues

1. Stored author label "Firūzābādī" is missing the macron on the first vowel. EI2 and the guide use **al-Fīrūzābādī** (Arabic الفيروزآبادي).
2. Stored date **1414**. al-Sakhāwī (vol. 10, p. 86) dates his death to the night of 20 Shawwāl **817**, which calculates to about 2 January **1415** CE. Lane p. xvi gives 816 (= 1413–14); Hawramani gives "1414 CE / 816 or 17 AH". If the site follows 817, the CE year should be 1415. This does not change the panel order (al-Fayyūmī 1368 < 1414/1415 < al-Zabīdī 1790).
