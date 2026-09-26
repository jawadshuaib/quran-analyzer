# al-Mufradāt guide: verification round 3

- **Checked file:** `roots/frontend/src/content/dictionary-guides/guides/al-mufradat.ts` (the version after revision r2)
- **Verifier:** independent fact-check agent, 2026-09-26.
- **Independence:** I did not open research-notes.md or any revision-*.md file. I read verification-r2.md for its list of flags only. I re-checked every claim below against sources I opened myself in this round.

## Sources opened this round

**Dāwūdī edition**, shamela.ws/book/23636

- Book card: ed. Ṣafwān ʿAdnān al-Dāwūdī; Dār al-Qalam / al-Dār al-Shāmiyya, Damascus–Beirut; 1st ed. 1412 AH; "ترقيم الكتاب موافق للمطبوع".
- Printed page numbers, taken from each page's `data-page-num`:
  - id 1 = p. 5
  - id 17 = p. 21
  - ids 20–22 = pp. 24–26
  - ids 33–34 = pp. 37–38
  - ids 35–38 = pp. 53–56
  - id 238 = p. 256
  - ids 378–379 = pp. 396–397
  - ids 696–700 = pp. 714–718
- I read the full text of each page.

**Key**, *Language between God and the Poets*

- Source: the OAPEN PDF from archive.org, item `oapen-20.500.12657-29479`, extracted with pdftotext.
- Printed pp. 11–13 (PDF 28–30), 89–90 (PDF 106–107) and 106–108 (PDF 123–125).

**Encyclopaedia Iranica**, "Rāḡeb Eṣfahāni" (van Gelder)

- The live URL returns 403 (Cloudflare) to curl.
- I read the Wayback snapshot of 2025-04-21 of the same URL, in full.

**al-Zarkashī**

- Islamweb *Burhān* ch. 18: HTTP 200. The phrase is at print p. 394.
- islamicbook.ws albrhan-004: HTTP 200. The passage is present.

**Other web sources**

- UC Press book page: HTTP 200. Title: "Language between God and the Poets by Alexander Key". Marked Open Access.
- doi.org/10.1525/luminos.54 resolves to luminosoa.org, which returns 403 to curl.
- arabiclexicon.hawramani.com Mufradāt page: HTTP 200. It has a blurb with "d. c. 1109 CE / 502 AH" and a headword list containing حق, رب, صلا and كان. It gives no edition statement.

**Stored data** (`_dict_guide_tool.py`, plus a read-only sqlite query on the same `SHOWN` filter)

- Entries read in full: Mufradāt Hmd (54), kfr (157), sjd (1465), Swm (5683), twb (1559), rbw (4753), fjj (11977); Maqāyīs kfr (163).
- `root` for Hqq, rbb, Slw and kwn.
- Regex counts over all 1,267 displayed Mufradāt entries, 1,600 Tāj entries and 1,410 Lane entries.
- A random sample of 25 entry openings (seed 7).
- A scan of entries that end without terminal punctuation.

**Local API:** `/api/root/kfr/dictionaries`. The panel order shows Ibn Sīda (1066) and then al-Rāghib (1109).

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

### Header and summary

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title / titleAr *al-Mufradāt fī Gharīb al-Qurʾān* المفردات في غريب القرآن | S | Shamela card: "الكتاب: المفردات في غريب القرآن". |
| C2 | titleGloss "The Single Words: On the Unfamiliar Vocabulary of the Qurʾān" | S | A fair rendering of *mufradāt* and *gharīb*. |
| C3 | author, authorAr and authorFull "Abū l-Qāsim al-Ḥusayn ibn Muḥammad ibn al-Mufaḍḍal al-Rāghib al-Iṣfahānī" | S | Dāwūdī p. 53: "قال الشيخ أبو القاسم الحسين بن محمد بن المفضل الراغب". Key p. 11 has the identical form. Iranica: "Abul'l-Qāsem Ḥosayn b. Moḥammad b Mofażżal". |
| C4 | period "early 11th century CE (death date disputed)" | S | Iranica: "(d. early 5th/11th cent.)". Key p. 11: alive in or before 1018. Dāwūdī pp. 37–38: dates from 402 to 503 AH reported; he prefers c. 425. |
| C5 | kind "Dictionary of Qurʾānic words" | S | Dāwūdī p. 55: "كتاب مستوف فيه مفردات ألفاظ القرآن على حروف التهجي". |
| C6 | summary: a dictionary of the Qur'an's own vocabulary from the early eleventh century | S | As C4 and C5. Key p. 90 notes that he includes some non-Qur'anic words; the summary's wording is still fair. |
| C7 | summary + lede: "Many entries" start from a basic sense and follow it through the verses; "some" explain borrowing, extension or narrowing, or near-synonym differences | S | Verse citations: 1,250 of 1,267 entries. Opening "أصل / في الأصل / في اللغة" in the first 60 characters: 119 entries. In my random sample of 25 openings, about half give a plain or physical sense (Tlq, kwr, Zhr, qbD, fSl, kdy, TbE…) and 5 open with a verse. "استعير / مستعار": 124 entries. "في الشرع / في الشريعة": 13. Comparatives "(أخص\|أعم\|أبلغ) من": 61. "Many" and "some" fit these numbers. |

### Lede

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C8 | "built his dictionary around the words of a single book" | S | Dāwūdī p. 55, as C5. |
| C9 | Lexicon and commentary share the page | S | Entry 1465: the ضربان analysis, and qīla readings of Q 2:34 and 72:18. Key p. 13. |

### Body: biography

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C10 | Almost nothing is known of his life beyond a name linking him to Isfahan and books on ethics, exegesis and theology [iranica] | S | Iranica: "Next to nothing is known about his life"; "One may assume on the evidence of Rāḡeb's nesba that he was born in Isfahan". His works are on "Islamic ethics, Qurʾanic exegesis, Islamic theology, and Arabic philology". |
| C11 | Later works often date his death to 502/1108, without clear evidence [iranica] | S | Iranica: "It is often stated, without any clear evidence, that he died in 502/1108 (e.g., Ḥāji Ḵalifa…)". Dāwūdī p. 37 also lists Ḥājjī Khalīfa, Brockelmann, al-Ziriklī and Kaḥḥāla for 502. |
| C12 | Modern research places him in the early 11th century [iranica] | S | Iranica: "Wilferd Madelung's study has confirmed that Rāḡeb lived 'in the first part of the fifth century'". |
| C13 | Key, citing the *Mufradāt*'s oldest manuscript (409/1018), concludes he was alive in or before 1018 [key p. 11] | S | Key p. 11: "ascertain from the oldest manuscript witness to his Quranic glossary that ar-Rāġib was alive in or before 1018"; n. 11: "Al-Ǧawharǧī (1986), Key (2012, 32f), ar-Rāġib (409/1018)". Dāwūdī p. 38 reports al-Jawharjī's manuscript, copied in 409. |
| C14 | "the book's modern editor, Ṣafwān Dāwūdī, put his death at about 425/1033–34" [dawudi pp. 37–38] | **NQ** | The date is supported. Dāwūdī p. 38: "إن الأرجح أنّ وفاته في حوالي سنة ٤٢٥ هـ", and 425 AH = 1033–34. But "the book's modern editor" implies there is only one. Iranica's bibliography lists other modern editions: Kaylānī (Cairo 1961), Khalaf-Allāh (Cairo 1970) and Marʿashlī (Beirut 1972). Dāwūdī is the editor of the edition our text matches. |
| C15 | "Either way he was a contemporary of Ibn Fāris" [key p. 90] | S | Key p. 90: "the dictionary of his contemporary Ibn Fāris". |
| C16 | Some four centuries after the Qur'an | S | Arithmetic. |
| C17 | Also known as *Mufradāt alfāẓ al-Qurʾān* [iranica] | S | Iranica: "The first, more often entitled Mofradāt alfāẓ al-Qorʾān, is a very useful alphabetical dictionary of Qorʾanic Arabic". |

### Body: "Bricks for a building"

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C18 | "Recalling his earlier writings" [raghib-intro pp. 53–54] | S | p. 53: "كنت قد ذكرت في «الرسالة المنبهة على فوائد القرآن»". p. 54: "وأشرت في كتاب «الذريعة…»" and "وذكرت أنّ…". |
| C19 | He opens by putting the verbal sciences first, and among them the precise understanding of single words | S | p. 54: "وذكرت أنّ أول ما يحتاج أن يشتغل به من علوم القرآن العلوم اللفظية، ومن العلوم اللفظية تحقيق الألفاظ المفردة". |
| C20 | The Arabic "bricks" quotation [p. 54] | S | Verbatim on p. 54. |
| C21 | Its translation (labelled) | S | Accurate. |
| C22 | He promises a book that "covers" (*mustawfin*) the single words, arranged alphabetically by first root letter [p. 55] | S | p. 55: "استخرت الله تعالى في إملاء كتاب مستوف فيه مفردات ألفاظ القرآن على حروف التهجي … معتبرا فيه أوائل حروفه الأصلية دون الزوائد". |
| C23 | It points out the relations (*munāsabāt*) between borrowed and derived words [p. 55] | S | p. 55: "والإشارة فيه إلى المناسبات التي بين الألفاظ المستعارات منها والمشتقات حسبما يحتمل التوسع في هذا الكتاب". |
| C24 | Key shows him repeatedly explaining Qur'anic words as *istiʿāra* borrowed from nomadic life [key p. 107] | S | Key p. 107: "remarked on this process of language evolution at multiple points in his Quranic glossary, using the word for 'metaphor' (istiʿārah) … His dictionary sought to read God as having taken phrases from a nomadic lifestyle". |
| C25 | A planned sequel on synonyms "and the subtle differences between them" (labelled); *qalb* / *fuʾād* / *ṣadr* [pp. 55–56] | S | p. 55: "وأتبع هذا الكتاب … بكتاب ينبئ عن تحقيق الألفاظ المترادفة على المعنى الواحد، وما بينها من الفروق الغامضة … نحو ذكر القلب مرّة والفؤاد مرة والصدر مرّة". |
| C26 | He dismisses the idea that glossing *al-ḥamdu li-llāh* as "thanks be to God" explains the Qur'an [pp. 55–56] | S | pp. 55–56: "ممّا يعدّه من لا يحقّ الحقّ … فيقدّر أنه إذا فسّر: الحمد لله بقوله: الشكر لله … فقد فسّر القرآن ووفّاه التبيان". |
| C27 | Dāwūdī could not find the sequel [p. 55] | S | p. 55, n. 2: "لم نجد هذا الكتاب". |
| C28 | The habit surfaces in "a few dozen" displayed entries, among them ح م د | S | 61 displayed entries match (أخص\|أعم\|أبلغ) من. Entry 54 is among them. |
| C29 | The Hmd excerpt's Arabic | S | Entry 54. Identical on Dāwūdī p. 256. Validator OK. |
| C30 | The Hmd translation | S | Accurate for "الثناء عليه بالفضيلة، وهو أخصّ من المدح وأعمّ من الشكر". |
| C31 | *Madḥ* can praise a handsome face as readily as generosity; *ḥamd* only the latter; *shukr* only answers a favour [p. 256] | S | "فقد يمدح الإنسان بطول قامته وصباحة وجهه، كما يمدح ببذل ماله وسخائه … والحمد يكون في الثاني دون الأول، والشّكر لا يقال إلا في مقابلة نعمة". |

### Body: "Reading an entry" (k-f-r)

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C32 | kfr locator pp. 714–717 | S | "[كفر]" starts on p. 714 (id 696). The entry continues through p. 717 (id 699). p. 718 starts with كفل. |
| C33 | The kfr excerpt's Arabic | S | Entry 157. The same text is on p. 714 (minus the edition's verse numbers 387–388). Validator OK. |
| C34 | The kfr translation | S | Accurate, including "الأشخاص" rendered as "people" and "أكثر استعمالا … أكثر … فيهما جميعا". |
| C35 | He starts "in the language" with physical covering, citing two half-lines by unnamed poets | S | Entry 157: "لمّا سمع: ألقت ذكاء يمينها في كافر" and "قال الشاعر: كالكرم إذ نادى من الكافور". No poet is named. Dāwūdī p. 714 n. 2 calls the first a عجز (second hemistich) by Thaʿlaba b. Ṣuʿayr; n. 3 says the second is rajaz by al-ʿAjjāj. See brief issues for "half-line". |
| C36 | "He first quotes one as the line in which some philologists took *kāfir* for a name of night and sower; for him the word only describes them." | S | Entry 157: "ووصف الليل بالكافر … والزّرّاع … وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع: ألقت ذكاء يمينها في كافر". "لهما" supports "night and sower". Ibn Fāris (163) shows the same line glossed with *kāfir* as a noun ("مغيب الشمس", "البحر"). A wording suggestion is in the brief issues. |
| C37 | He reaches ingratitude through verses that set *kufr* against *shukr* (Q 14:7, Q 27:40) | S | Definition "سترها بترك أداء شكرها", then [النمل/ 40], [البقرة/ 152] and [إبراهيم/ 7], each pairing شكر and كفر. |
| C38 | Denial grows out of ingratitude (Q 2:41) | S | "ولمّا كان الكفران يقتضي جحود النّعمة صار يستعمل في الجحود، قال: وَلا تَكُونُوا أَوَّلَ كافِرٍ بِهِ [البقرة/ 41]". |
| C39 | Notes on which form is used more for which sense describe tendencies, not rules | S | "أكثر استعمالا … أكثر … فيهما جميعا". This is the guide's reading, and a fair one. |
| C40 | He marks the familiar religious meaning as *mutaʿāraf*, "conventionally understood" (labelled) | S | "والكَافِرُ على الإطلاق متعارف فيمن يجحد الوحدانيّة، أو النّبوّة، أو الشريعة". |
| C41 | Rival interpretations with *qīla*; at Q 57:20 the *kuffār* may be sowers or unbelievers | S | "[الحديد/ 20] قيل: عنى بالكفّار الزّرّاع … وقيل: بل عنى الكفار". |
| C42 | Once he refers the reader to his own ethical treatise, the *Dharīʿa* | S | "وقد بيّنته في كتاب «الذّريعة إلى مكارم الشّريعة»". Iranica treats the *Dharīʿa* among his ethical works ("the underlying ethical foundations of the law"). |

### Body: the Ibn Fāris comparison

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C43 | Ibn Fāris starts from covering, illustrated from ordinary speech (the mail-coat) | S | Entry 163: "أَصْلٌ صَحِيحٌ يَدُلُّ عَلَى مَعْنًى وَاحِدٍ، وَهُوَ السَّتْرُ وَالتَّغْطِيَةُ. يُقَالُ لِمَنْ غَطَّى دِرْعَهُ بِثَوْبٍ: قَدْ كَفَرَ دِرْعَهُ". |
| C44 | He reaches religion in one step: *kufr*, opposite of faith, "so called because it is a covering of the truth"; ingratitude "likewise" | S | "وَالْكُفْرُ: ضِدُّ الْإِيمَانِ، سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ. وَكَذَلِكَ كُفْرَانُ النِّعْمَةِ". |
| C45 | Al-Rāghib's *kāfir* of Q 24:55 also "conceals the truth", but he gets there via the Qur'an's pairing of *kufr* with thanks | S | "[النور/ 55] عني بالكافر السّاتر للحقّ" comes after the shukr verses and the "لمّا كان الكفران يقتضي جحود النّعمة" step. It is interpretive, and fair to the order of the entry. |
| C46 | "Neither records the word's history; each explains how its senses hang together" | S | This is the guide's judgement. Neither entry gives dated usage. |

### Body: "Where the lexicon becomes interpretation" (s-j-d)

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C47 | sjd locator pp. 396–397 | S | "[سجد]" is on p. 396 (id 378) and continues on p. 397 (id 379). |
| C48 | The sjd excerpt's Arabic | S | Entry 1465 = pp. 396–397. Validator OK. |
| C49 | The sjd translation | S | Accurate ("التطامن" = lowering oneself; "الركن المعروف من الصلاة"). |
| C50 | The entry keeps its layers apart; shadows and trees perform *sujūd* (Q 13:15, Q 55:6) | S | "[الرعد/ 15] … وظلالهم" and "وَالنَّجْمُ وَالشَّجَرُ يَسْجُدانِ [الرحمن/ 6]". |
| C51 | Q 4:154 glossed "humbled, submissive" (labelled), with no mention of posture | S | "ادْخُلُوا الْبابَ سُجَّداً [النساء/ 154]، أي: متذلّلين منقادين". |
| C52 | "in the religious Law" separates general from technical, undated; the same for fasting, repentance and usury | S | Swm "والصَّوْمُ في الشّرع"; twb "والتَّوْبَةُ في الشرع"; rbw "لكن خصّ في الشرع". None gives a date. |
| C53 | Unattributed analysis: *sujūd* by choice or by subjection; "a silent yet speaking indication" (labelled) | S | "وذلك ضربان: سجود باختيار … وسجود تسخير … وهو الدّلالة الصامتة الناطقة المنبّهة على كونها مخلوقة، وأنّها خلق فاعل حكيم". There is no qīla or name there. |
| C54 | Key: a blend of traditionist piety, Sufism and philosophical ethics seeped "however subtly" into the glossary [key p. 13] | S | Key p. 13: "traditionist piety …, the mystical approach … 'Sufism,' and the Aristotelian and Neoplatonic ethical heritage … Ar-Rāġib then allowed this combination to seep, however subtly, into his glossary of the Quran". |
| C55 | Read "kinds" schemes (*ḍarbān*, *awjuh*) as interpretation | S | Advice from the guide. ضربان\|أوجه occurs in 51 displayed entries. |

### Body: "Evidence and its limits"

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C56 | Nearly every displayed entry quotes at least one verse | S | 1,250 of 1,267 contain a bracketed sura/verse reference. |
| C57 | Poetry is sparse; Dāwūdī counts no more than 500 lines [p. 25] | S | p. 25: "بينما كتاب الراغب لا يتجاوز ٥٠٠ بيت". |
| C58 | "the text seldom names the poet; most attributions in the printed edition come from the editor's notes" [p. 5] (r2 fix) | S | "قال الشاعر / قول الشاعر" occurs in 238 displayed entries. A named poet (النابغة, لبيد, زهير, طرفة, الأعشى, العجاج, الهذلي …) appears in 12. p. 5, method item 6: "نسبة الأبيات الشعرية لقائليها". p. 714 nn. 2–3 show the editor doing it. The r2 flag is resolved. |
| C59 | He cites variant readings without separating accepted from irregular ones [p. 26] | S | p. 26: "لم يميّز بين القراءات المتواترة والشاذة، بل يكتفي أن يقول: وقرئ كذا". |
| C60 | Some sayings he attributes to the Prophet are not hadith [p. 26] | S | p. 26: "نسبته بعض الأقوال إلى الرسول، وليست هي من قوله … «لا جبر ولا تفويض»". |
| C61 | He names earlier philologists in only about 60 of our entries | S | A regex over 22 philologist names gives 67 entries. I inspected the ambiguous names: at least 3 are false hits (الخليل = friend in sjr; ثعلب = fox in rwg and DbH). So about 60–64. |
| C62 | Dāwūdī traces heavy, unacknowledged use of Ibn Fāris's *al-Mujmal*, not the *Maqāyīs* [p. 21] (locator narrowed in r2) | S | p. 21 (id 17): "كتاب «المجمل في اللغة» لابن فارس. ويبدو أنّ الراغب قد اعتمد عليه كثيرا، مع أنه لم يذكره باسمه … وقد بيّنا ذلك في خلال تعليقاتنا". |
| C63 | So an unattributed definition may be older than al-Rāghib, sometimes taken over word for word | S | p. 21: "والتشابه الكبير في العبارة، وربما ينقل عنه حرفيا". |
| C64 | A view introduced by *qīla* (in about half our entries) is reported, not necessarily endorsed | S | "قيل" appears in 646 of 1,267 entries (51%). "قيل:" with a colon, the view-introducing use, appears in 560 (44%). "About half" holds. |
| C65 | His own voice is surest in first-person asides like the *Dharīʿa* reference | S | The guide's own reading. It is consistent with p. 21 (unacknowledged borrowing) and with "وقد بيّنته" in entry 157. |
| C66 | Al-Fīrūzābādī and al-Samīn al-Ḥalabī reworked it into their own books [p. 24] | S | p. 24 (id 20): Fīrūzābādī "عكف على كتاب الراغب، واختصره، وزاد فيه … «بصائر ذوي التمييز»"; al-Samīn "جعل كتاب الراغب لبّ كتابه" in *ʿUmdat al-ḥuffāẓ*. |
| C67 | *Tāj al-ʿArūs* names him in some 340 of our entries | S | "الراغب" occurs in 340 displayed Tāj entries. The contexts I sampled ("وقال الراغب في المفردات", "عبارة الراغب في المفردات") are citations of him. |
| C68 | Lane names him in about 265, often via the *Tāj* | S | 265 displayed Lane entries match "R[aá]ghib". 159 of them have "…Rághib, TA". |
| C69 | "one definition in several dictionaries may be a single witness repeated" | S | The guide's inference, supported by C67 and C68 and by Dāwūdī p. 24 (Tāj among those who copied him). |
| C70 | al-Zarkashī is fourteenth-century | S | Iranica: d. 794/1392. |
| C71 | Zarkashī: "hunts out meanings from the context" (يتصيد المعاني من السياق) (labelled) | S | Islamweb *Burhān* ch. 18, print p. 394: "ومن أحسنها كتاب " المفردات " للراغب . وهو يتصيد المعاني من السياق". Iranica quotes it too. |
| C72 | Zarkashī: a qualification beyond the philologists "because he caught it from the context" (labelled) | S | islamicbook.ws: "فيذكر قيدا زائدا على أهل اللغة في تفسير مدلول اللفظ لأنه اقتنصه من السياق". Also quoted by Dāwūdī p. 25. |
| C73 | Closing judgement: a nuance caught from context is a reading, not outside evidence; his links are early-11th-century explanations, not records of usage | S | Explicitly the guide's advice. It is consistent with Key pp. 106–107 ("a theory of … language change"). |

### onOurSite

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C74 | The stored text matches Dāwūdī's edition (1412/1991–92) word for word in every entry compared, without footnotes | S | Hmd = p. 256, sjd = pp. 396–397, kfr = p. 714. They are identical apart from the edition's verse numbers, note markers and headword brackets. The Shamela card gives 1412 AH. |
| C75 | hawramani, where it was collected, does not name its source | S | The hawramani page has a blurb and a headword list, with no edition statement. |
| C76 | Bracketed sura/verse references are Dāwūdī's additions [p. 5]; poets' names from his notes are absent; verse runs into the prose | S | p. 5 item 3: "تخريج الآيات القرآنية، وذكر أرقامها وسورها. وجعلناها في المتن". Entry 157 compared with p. 714 nn. 2–3. Stored: "لمّا سمع: ألقت ذكاء يمينها في كافر والْكَافُورُ…". |
| C77 | 1,267 entries displayed; articles such as حقّ, ربّ, صلا and كان did not reach our copy | S | `dicts` gives 1267. `root` for Hqq, rbb, Slw and kwn lists no Mufradāt entry, while the hawramani headword list contains حق, رب, صلا and كان. |
| C78 | "A few entries are cut short, such as ف ج ج" | S | fjj (11977) ends "…ويستعمل في الطّريق الواسع، وجمعه". ywm also ends mid-sentence, on a comma, after an appended يس article (see site-data issues). |
| C79 | The panel orders the works by a stored 1109 CE (502 AH), which modern scholarship doubts; so it lists him after Ibn Sīda, although he was a contemporary of Ibn Fāris | S | `dicts`: Ibn Sīda 1066, al-Rāghib 1109. The API order for kfr matches. Iranica and Key p. 11 cast doubt on the date; Key p. 90 calls him a contemporary of Ibn Fāris. |

### Sources

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C80 | Citation details are accurate | S | Dāwūdī: Dār al-Qalam / al-Dār al-Shāmiyya, 1412; the introduction runs pp. 5–38 (p. 38 is signed "صفوان داودي"). Author's introduction: pp. 53–56. Key: UC Press 2018, open access, DOI 10.1525/luminos.54 (PDF title page). Iranica: van Gelder, published 1 Jan 2000, updated 8 Nov 2012. Zarkashī: ch. 18 "النوع الثامن عشر معرفة غريبه", and the tafsīr section "ما لم يرد فيه نقل عن المفسرين". |

**Totals: 80 claims. 79 supported, 1 needs qualification, 0 unsupported.**

## Status of the round-2 flags and suggestions

| r2 item | Status now |
|---|---|
| C58 NQ (poet attributions) | Fixed. It now reads "most attributions in the printed edition come from the editor's notes". This round's C58 is supported. |
| Length 1,122 | Fixed. The validator reports 1,098. |
| C36 wording | Reworded (this round's C36). It is supported; one optional refinement is listed below. |
| Mujmal locator | Narrowed to p. 21. Correct. |
| onOurSite 154 words | Now about 148. |

## Flagged items and fixes

1. **C14 (NQ): "the book's modern editor, Ṣafwān Dāwūdī".**
   - Problem: the definite article implies that Dāwūdī is the only modern editor. Iranica's bibliography lists at least three other modern editions: Kaylānī (Cairo 1961), Khalaf-Allāh (Cairo 1970) and Marʿashlī (Beirut 1972). Dāwūdī is the editor of the edition our stored text matches.
   - Fix: change "the book's modern editor, Ṣafwān Dāwūdī," to "Ṣafwān Dāwūdī, editor of the edition our text follows,". Alternatively: "the modern editor Ṣafwān Dāwūdī".
   - This adds no words to the count.

## Brief issues (not factual)

- *suggestion*: C36. "the line in which some philologists took *kāfir* for a name of night and sower" can suggest that the line mentions a sower. It does not: the line is about the sun setting into *kāfir*. A cleaner version: "He first quotes one as the line that led some philologists to treat *kāfir* as a name (of night, and of the sower); for him the word only describes them." Optional.
- *suggestion*: C35. "two half-lines". The second (كالكرم إذ نادى من الكافور) is a rajaz line by al-ʿAjjāj (Dāwūdī p. 714 n. 3). A rajaz line is not strictly a half-line. "two scraps of verse by unnamed poets" or "two verse fragments" would be exact. Optional.
- *suggestion*: "covers" (*mustawfin*) and "relations" (*munāsabāt*) are one-word glosses without the "translation for this guide" label that the other glosses carry. This is minor; the page's shared note covers translations generally.
- Length: lede + body is 1,098 words (in range). onOurSite is about 148 words. summary is 44 words.
- The essay has no padding, generic praise or rankings. The panel order is explained as a stored-date artefact, not a ranking. The essay does not force an "original root meaning" narrative. Every root mention is a link. The excerpt translations are labelled by the page, and the inline glosses are labelled.

## Source URL checks

| id | URL | Result |
|---|---|---|
| raghib-intro | https://shamela.ws/book/23636/36 | 200. This is printed p. 54 of the Dāwūdī ed.; the introduction begins at id 35 = p. 53. OK. |
| key | https://www.ucpress.edu/books/language-between-god-and-the-poets/paper | 200. The page title is "Language between God and the Poets by Alexander Key", marked Open Access. OK. |
| iranica | https://www.iranicaonline.org/articles/rageb-esfahani/ | 403 to curl (Cloudflare). The content was confirmed via Wayback (2025-04-21). It will probably work in a browser; keep it. |
| dawudi | https://shamela.ws/book/23636/1 | 200. p. 5, "مقدّمة المحقّق". OK. |
| zarkashi-gharib | islamweb.net … النوع الثامن عشر | 200. The quotation is present. OK. |
| zarkashi-tafsir | https://www.islamicbook.ws/qbook/alom/albrhan-004.html | 200. The quotation is present. OK. |
| hawramani | https://arabiclexicon.hawramani.com/al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran/ | 200. OK. |

Every listed source is cited and was consulted this round. None is unusable.

## Validator

`node scripts/validate-dictionary-guides.mjs al-mufradat` gave **ok, 1/1 guides pass**:

- root links: 5 (5 distinct root/dictionary pairs)
- excerpts: 3
- words (lede + body): 1,098
- example roots: Hmd, kfr, sjd, fjj

## Site-data issues

1. **Stored death date 1109 CE (502 AH) is doubtful.**
   - Iranica: 502/1108 is given "without any clear evidence"; Madelung places him in the first part of the 5th/11th century.
   - Key p. 11: he was alive in or before 1018.
   - Dāwūdī p. 38 prefers c. 425/1033–34.
   - The panel therefore lists him after Ibn Sīda (1066). An approximate value such as c. 1025, marked disputed, would match the evidence; the guide uses sortYear 1020.
   - hawramani repeats "d. c. 1109 CE / 502 AH".
2. **Missing articles.** The hawramani headword list has حق, رب, صلا and كان, but no Mufradāt entry is displayed for Hqq, rbb, Slw or kwn. This is probably a matching failure for short or alif-spelled headwords.
3. **Truncated or merged entries.**
   - fjj (11977) is cut off at "وجمعه".
   - ywm ends with the book's يس article appended ("يس يس قيل معناه يا إنسان …") and stops on a comma.
   - nAy contains the stray section marker "تمّ كتاب النون كتاب الهاء".
