# al-Mufradāt guide: verification round 4

- **Checked file:** `roots/frontend/src/content/dictionary-guides/guides/al-mufradat.ts` (the version after the final revision)
- **Verifier:** independent fact-check agent, 2026-09-26.
- **Independence:** I did not open research-notes.md or any revision-*.md file. I read verification-r3.md for its list of flags only. I fetched every source again myself in this round, into my own scratch files. I recounted every figure from the database myself, using my own read-only queries with the site's `SHOWN` filter.

## Sources opened this round

**Dāwūdī edition** (shamela.ws/book/23636; fetched again into `r4sh/`)

Printed page numbers come from each page's `data-page-num`:

| Shamela id | Printed page |
|---|---|
| 1 | 5 |
| 17 | 21 |
| 20–22 | 24–26 |
| 33–34 | 37–38 |
| 35–38 | 53–56 |
| 238 | 256 |
| 378–379 | 396–397 |
| 696–700 | 714–718 |

I read the full text and notes of each page.

**Key**, *Language between God and the Poets*

- Downloaded afresh from archive.org, item `oapen-20.500.12657-29479` (4.78 MB), and extracted with pdftotext.
- Printed page numbers were read from the running heads:
  - "Contexts 11" = PDF 28
  - "Contexts 13" = PDF 30
  - "90 The Lexicon" = PDF 107
  - "The Lexicon 107" = PDF 124

**Encyclopaedia Iranica**, van Gelder, "Rāḡeb Eṣfahāni"

- The live URL returns 403 to curl.
- I read the Wayback 2025 snapshot (HTTP 200) in full.
- The page gives "Last Updated November 8, 2012 / Published January 1, 2000".

**al-Zarkashī**

- Islamweb *Burhān* ch. 18: HTTP 200.
- islamicbook.ws albrhan-004: HTTP 200.

**Other web pages**

- UC Press: HTTP 200. Title "Language between God and the Poets by Alexander Key", marked "Open Access".
- hawramani Mufradāt page: HTTP 200.

**Stored data**

- `_dict_guide_tool.py entry` for Mufradāt Hmd (54), kfr (157), sjd (1465) and fjj (11977), and for Maqāyīs kfr (163).
- `root` for Hqq, rbb, Slw and kwn.
- `grep` for "في الشرع|في الشريعة".
- My own sqlite counts on the `SHOWN` filter.
- A fresh random sample of 20 entry openings (seed 2026).
- `/api/root/kfr/dictionaries` gives the panel order: … Ibn Fāris 1004, Ibn Sīda 1066, al-Rāghib 1109, al-Zamakhsharī 1143 …

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

### Header and summary

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title / titleAr *al-Mufradāt fī Gharīb al-Qurʾān* المفردات في غريب القرآن | S | The Shamela book card title. The hawramani page header is "المفردات في غريب القرآن للراغب الأصفهاني". |
| C2 | titleGloss "The Single Words: On the Unfamiliar Vocabulary of the Qurʾān" | S | A fair rendering of مفردات and غريب. |
| C3 | authorFull "Abū l-Qāsim al-Ḥusayn ibn Muḥammad ibn al-Mufaḍḍal al-Rāghib al-Iṣfahānī"; authorAr | S | Dāwūdī p. 53: "قال الشيخ أبو القاسم الحسين بن محمد بن المفضل الراغب". Iranica: "Abul'l-Qāsem Ḥosayn b. Moḥammad b Mofażżal". |
| C4 | period "early 11th century CE (death date disputed)" | S | Iranica headword: "(d. early 5th/11th cent.)". Key p. 11: alive in or before 1018. Dāwūdī pp. 37–38 lists reported dates from 402 to 503 AH. |
| C5 | kind "Dictionary of Qurʾānic words" | S | Dāwūdī p. 55: "كتاب مستوف فيه مفردات ألفاظ القرآن على حروف التهجي". |
| C6 | summary: a dictionary of the Qur'an's own vocabulary from the early eleventh century | S | The oldest manuscript is dated 409/1018 (Key p. 11 n. 11; Dāwūdī p. 38), so the book predates 1018 whichever death date is right. |
| C7 | summary + lede: many entries start from a basic sense and follow it through the verses; some explain borrowing, extension or narrowing, or near-synonym differences | S | Verse references: 1,250 of 1,267. My sample of 20 openings: about 14 open with a plain or physical sense (شفع ضم الشيء, خبط, عسل, كهف, عرش في الأصل …); 4 open with a verse. استعير/مستعار/استعارة: 154 entries. في الشرع/الشريعة: 13. (أخص\|أعم\|أبلغ) من: 61. |

### Lede

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C8 | Built around the words of a single book | S | Dāwūdī p. 55, as for C5. |
| C9 | Lexicon and commentary share the page | S | sjd (1465): the ضربان analysis, and the قيل readings of Q 2:34 and 72:18. kfr (157): the reference to the *Dharīʿa*. |

### Body: biography

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C10 | Almost nothing is known of his life beyond a name linking him to Isfahan and books on ethics, exegesis and theology [iranica] | S | Iranica: "Next to nothing is known about his life"; "One may assume on the evidence of Rāḡeb's nesba that he was born in Isfahan". His works are on "Islamic ethics, Qurʾanic exegesis, Islamic theology, and Arabic philology". The essay's list leaves out philology; see brief issues. |
| C11 | Later works often date his death to 502/1108, without clear evidence [iranica] | S | Iranica: "It is often stated, without any clear evidence, that he died in 502/1108 (e.g., Ḥāji Ḵalifa…)". Dāwūdī p. 37: Ḥājjī Khalīfa, Brockelmann, al-Ziriklī and Kaḥḥāla give 502. |
| C12 | Modern research places him in the early 11th century [iranica] | S | Iranica: "Wilferd Madelung's study has confirmed that Rāḡeb lived 'in the first part of the fifth century'". |
| C13 | Key, citing the oldest manuscript (409/1018), concludes he was alive in or before 1018 [key p. 11] | S | Key p. 11 (PDF 28): "ascertain from the oldest manuscript witness to his Quranic glossary that ar-Rāġib was alive in or before 1018". n. 11: "Al-Ǧawharǧī (1986), Key (2012, 32f), ar-Rāġib (409/1018)". Dāwūdī p. 38: the Damascus manuscript "نسخت سنة ٤٠٩ هـ". |
| C14 | **(revised)** "Ṣafwān Dāwūdī, whose edition our text follows, put his death at about 425/1033–34" [dawudi pp. 37–38] | S | Dāwūdī p. 38: "إن الأرجح أنّ وفاته في حوالي سنة ٤٢٥ هـ"; the p. 37 list of dates leads up to it. 425 AH = 1033–34 CE. "whose edition our text follows" is confirmed (see C74). The implication of a single modern editor is gone; Iranica lists Kaylānī 1961, Khalaf-Allāh 1970 and Marʿashlī 1972. **The r3 flag is resolved.** |
| C15 | Either way, a contemporary of Ibn Fāris [key p. 90] | S | Key p. 90 (PDF 107): "the dictionary of his contemporary Ibn Fāris". |
| C16 | Some four centuries after the Qur'an | S | Arithmetic: 7th century to early 11th century. |
| C17 | Also known as *Mufradāt alfāẓ al-Qurʾān* [iranica] | S | Iranica: "The first, more often entitled Mofradāt alfāẓ al-Qorʾān, is a very useful alphabetical dictionary of Qorʾanic Arabic". |

### Body: "Bricks for a building"

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C18 | Recalling his earlier writings [pp. 53–54] | S | p. 53: "كنت قد ذكرت في «الرسالة المنبهة على فوائد القرآن»". p. 54: "وأشرت في كتاب «الذريعة…»" and "وذكرت أنّ…". |
| C19 | Puts the verbal sciences first, and among them the precise understanding of single words | S | p. 54: "وذكرت أنّ أول ما يحتاج أن يشتغل به من علوم القرآن العلوم اللفظية، ومن العلوم اللفظية تحقيق الألفاظ المفردة". |
| C20 | The Arabic "bricks" quotation [p. 54] | S | Verbatim on p. 54 (id 36). The same wording is quoted by al-Zarkashī on islamicbook.ws. |
| C21 | Its translation (labelled) | S | Accurate. اللبن = (mud) bricks. |
| C22 | "covers" (*mustawfin*); alphabetical by first root letter [p. 55] | S | p. 55: "كتاب مستوف فيه مفردات ألفاظ القرآن على حروف التهجي … معتبرا فيه أوائل حروفه الأصلية دون الزوائد". |
| C23 | Relations (*munāsabāt*) between borrowed and derived words [p. 55] | S | p. 55: "والإشارة فيه إلى المناسبات التي بين الألفاظ المستعارات منها والمشتقات". |
| C24 | Key shows him repeatedly explaining Qur'anic words as *istiʿāra* borrowed from nomadic life [key p. 107] | S | Key p. 107 (PDF 124): he "remarked on this process of language evolution at multiple points in his Quranic glossary, using the word for 'metaphor' (istiʿārah…). His dictionary sought to read God as having taken phrases from a nomadic lifestyle". Examples: rawāḥ, midrār, sarḥ/tasrīḥ. |
| C25 | A planned sequel on synonyms "and the subtle differences between them" (labelled); *qalb* / *fuʾād* / *ṣadr* [pp. 55–56] | S | p. 55: "بكتاب ينبئ عن تحقيق «الألفاظ المترادفة على المعنى الواحد، وما بينها من الفروق الغامضة» … نحو ذكر القلب مرّة والفؤاد مرة والصدر مرّة". |
| C26 | He dismisses the idea that glossing *al-ḥamdu li-llāh* as "thanks be to God" explains the Qur'an [pp. 55–56] | S | pp. 55–56: "ممّا يعدّه من لا يحقّ الحقّ … فيقدّر أنه إذا فسّر: الحمد لله بقوله: الشكر لله … فقد فسّر القرآن ووفّاه التبيان". |
| C27 | Dāwūdī could not find the sequel [p. 55] | S | p. 55 n. 2: "لم نجد هذا الكتاب". |
| C28 | The habit surfaces in a few dozen displayed entries, including ح م د | S | 61 displayed entries match (أخص\|أعم\|أبلغ) من, among them Hmd, and TbE ("أعم من الختم وأخص من النقش"). |
| C29 | The Hmd excerpt's Arabic | S | Entry 54 opening. Identical on Dāwūdī p. 256 (id 238). Validator OK. |
| C30 | The Hmd translation | S | Accurate. |
| C31 | *Madḥ* can praise a handsome face as readily as generosity; *ḥamd* only the latter; *shukr* only answers a favour [p. 256] | S | Entry 54 and p. 256: "فقد يمدح الإنسان بطول قامته وصباحة وجهه، كما يمدح ببذل ماله وسخائه … والحمد يكون في الثاني دون الأول، والشّكر لا يقال إلا في مقابلة نعمة". |

### Body: "Reading an entry" (k-f-r)

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C32 | kfr locator pp. 714–717 | S | "[كفر]" is on p. 714 (id 696). The entry ends on p. 717 (id 699), where "[كفل]" starts. |
| C33 | The kfr excerpt's Arabic | S | Entry 157. The same text is on p. 714, apart from the edition's verse numbers 387–388 and note markers. Validator OK. |
| C34 | The kfr translation | S | Accurate. |
| C35 | He starts "in the language" with physical covering, citing two half-lines by unnamed poets | S | Entry 157 names no poet for either. Dāwūdī p. 714 n. 2 calls the first "عجز بيت". For the second (al-ʿAjjāj's rajaz), Dāwūdī's own cross-reference on p. 717 n. 2 says "الشطر تقدّم قريبا ص ٧١٤". So "half-line" is the editor's own term. The r3 suggestion on this point can be dropped. |
| C36 | He first quotes one as the line in which some philologists took *kāfir* for a name of night and sower; for him the word only describes them | S | "ووصف الليل بالكافر … والزّرّاع … وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع: ألقت ذكاء يمينها في كافر". "first" is accurate: he quotes the line again near the end of the entry (p. 717: "ويقال الكافر للسحاب الذي يغطي الشمس والليل"). There is a wording suggestion in the brief issues. |
| C37 | Reaches ingratitude through verses that set *kufr* against *shukr* (Q 14:7, Q 27:40) | S | The definition "سترها بترك أداء شكرها" is followed by [النمل/ 40], [البقرة/ 152] and [إبراهيم/ 7]. |
| C38 | Denial grows out of ingratitude (Q 2:41) | S | "ولمّا كان الكفران يقتضي جحود النّعمة صار يستعمل في الجحود، قال: وَلا تَكُونُوا أَوَّلَ كافِرٍ بِهِ [البقرة/ 41]". |
| C39 | Notes on which form is used more describe tendencies, not rules | S | "أكثر استعمالا … أكثر … فيهما جميعا". This is a fair reading. |
| C40 | *mutaʿāraf*, "conventionally understood" (labelled) | S | "والكَافِرُ على الإطلاق متعارف فيمن يجحد الوحدانيّة، أو النّبوّة، أو الشريعة". |
| C41 | Rival interpretations with *qīla*: at Q 57:20 the *kuffār* may be sowers or unbelievers | S | "[الحديد/ 20] قيل: عنى بالكفّار الزّرّاع … وقيل: بل عنى الكفار". |
| C42 | Once he refers the reader to his own ethical treatise, the *Dharīʿa* | S | "وقد بيّنته في كتاب «الذّريعة إلى مكارم الشّريعة»". Iranica treats the *Dharīʿa* among his works on ethics ("the underlying ethical foundations of the law"). |

### Body: the Ibn Fāris comparison

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C43 | Ibn Fāris starts from covering, illustrated by the mail-coat | S | Maqāyīs entry 163: "وَهُوَ السَّتْرُ وَالتَّغْطِيَةُ. يُقَالُ لِمَنْ غَطَّى دِرْعَهُ بِثَوْبٍ: قَدْ كَفَرَ دِرْعَهُ". |
| C44 | Religion in one step: "so called because it is a covering of the truth"; ingratitude "likewise" | S | "وَالْكُفْرُ: ضِدُّ الْإِيمَانِ، سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ. وَكَذَلِكَ كُفْرَانُ النِّعْمَةِ". |
| C45 | Al-Rāghib's *kāfir* of Q 24:55 "conceals the truth", reached via the pairing with thanks | S | "[النور/ 55] عني بالكافر السّاتر للحقّ" comes after the shukr verses and the step at Q 2:41. |
| C46 | Neither records the word's history; each explains how its senses hang together | S | This is the guide's own judgement. Neither entry gives dated usage. |

### Body: "Where the lexicon becomes interpretation" (s-j-d)

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C47 | sjd locator pp. 396–397 | S | "[سجد]" is on p. 396 (id 378). The entry ends on p. 397 (id 379), before [سجر]. |
| C48 | The sjd excerpt's Arabic | S | Entry 1465. Validator OK. |
| C49 | The sjd translation | S | Accurate. |
| C50 | Shadows and trees perform *sujūd* (Q 13:15, Q 55:6) | S | "وَظِلالُهُمْ … [الرعد/ 15]"; "وَالنَّجْمُ وَالشَّجَرُ يَسْجُدانِ [الرحمن/ 6]". |
| C51 | Q 4:154 is glossed "humbled, submissive" (labelled), with no posture mentioned | S | "ادْخُلُوا الْبابَ سُجَّداً [النساء/ 154]، أي: متذلّلين منقادين". |
| C52 | "in the religious Law" separates general from technical, undated; the same for fasting, repentance and usury | S | The grep for في الشرع/الشريعة gives 13 entries, including Swm ("والصوم في الشرع"), twb ("والتوبة في الشرع") and rbw ("لكن خص في الشرع"). None gives a date. |
| C53 | An unattributed analysis: by choice or by subjection; "a silent yet speaking indication" (labelled) | S | "وذلك ضربان: سجود باختيار … وسجود تسخير … وهو الدّلالة الصامتة الناطقة المنبّهة على كونها مخلوقة، وأنّها خلق فاعل حكيم". There is no قيل or name. |
| C54 | Key: the blend seeped "however subtly" into the glossary [key p. 13] | S | Key p. 13 (PDF 30): "traditionist piety …, the mystical approach … 'Sufism,' and the Aristotelian and Neoplatonic ethical heritage … Ar-Rāġib then allowed this combination to seep, however subtly, into his glossary of the Quran". |
| C55 | Read "kinds" schemes (*ḍarbān*, *awjuh*) as interpretation | S | Advice from the guide. ضربان\|أوجه occurs in 51 displayed entries. |

### Body: "Evidence and its limits"

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C56 | Nearly every displayed entry quotes at least one verse | S | 1,250 of 1,267 have a bracketed sura/verse reference. The 17 without one include jHm, fjj and kmh. |
| C57 | Poetry is sparse; Dāwūdī: no more than 500 lines [p. 25] | S | p. 25 (id 21): "بينما كتاب الراغب لا يتجاوز ٥٠٠ بيت". The edition numbers its verses (no. 390 is already reached under كفر). |
| C58 | The text seldom names the poet; most attributions come from the editor's notes [p. 5] | S | "قال/قول الشاعر": 238 entries. p. 5 item 6: "نسبة الأبيات الشعرية لقائليها". p. 714 nn. 2–3 and p. 397 n. 4 are examples. |
| C59 | He cites variant readings without separating accepted from irregular [p. 26] | S | p. 26 (id 22): "لم يميّز بين القراءات المتواترة والشاذة، بل يكتفي أن يقول: وقرئ كذا". |
| C60 | Some sayings he attributes to the Prophet are not hadith [p. 26] | S | p. 26: "نسبته بعض الأقوال إلى الرسول، وليست هي من قوله … «لا جبر ولا تفويض»". |
| C61 | He names earlier philologists in only about 60 entries | S | My own name list (al-Khalīl, Sībawayh, al-Farrāʾ, Abū ʿUbayda/ʿUbayd, al-Aṣmaʿī, al-Mubarrad, al-Zajjāj, Ibn al-Aʿrābī, Abū Zayd, al-Akhfash, Ibn al-Sikkīt, Abū ʿAmr, Ibn Durayd, Abū ʿAlī al-Fasawī, Ibn Qutayba, Abū l-ʿAbbās …) gives 58 entries. I removed non-person hits: يونس = sura name; ثعلب = fox; مبرد = file; زجاج = glass; sjr الخليل = friend. That leaves about 57–60. |
| C62 | Heavy, unacknowledged use of Ibn Fāris's *al-Mujmal*, not the *Maqāyīs* [p. 21] | S | p. 21 (id 17): "كتاب «المجمل في اللغة» لابن فارس. ويبدو أنّ الراغب قد اعتمد عليه كثيرا، مع أنه لم يذكره باسمه". |
| C63 | So an unattributed definition may be older, sometimes taken over word for word | S | p. 21: "والتشابه الكبير في العبارة، وربما ينقل عنه حرفيا". The p. 256 notes cite *al-Mujmal* for Hmd-adjacent material. |
| C64 | *qīla* in about half our entries; reported, not necessarily endorsed | S | "قيل": 646 of 1,267 (51%). "قيل:": 560 (44%). |
| C65 | His own voice is surest in first-person asides like the *Dharīʿa* reference | S | The guide's own reading. It is consistent with p. 21 (unacknowledged borrowing). The *Dharīʿa* is referred to in kfr, Sdq and $kl. |
| C66 | Al-Fīrūzābādī and al-Samīn al-Ḥalabī reworked it into their own books [p. 24] | S | p. 24 (id 20): Fīrūzābādī "عكف على كتاب الراغب، واختصره، وزاد فيه … «بصائر ذوي التمييز»"; al-Samīn "جعل كتاب الراغب لبّ كتابه" in *ʿUmdat al-ḥuffāẓ*. |
| C67 | *Tāj* names him in some 340 of our entries | S | "الراغب": 340 of 1,600 displayed Tāj entries. Dāwūdī p. 24 lists al-Zabīdī among those who quote him. |
| C68 | Lane names him in about 265, often via the *Tāj* | S | 265 of 1,410 displayed Lane entries match "R[aá]ghib". 165 of them have "TA" right beside the name, e.g. "( Er-Rághib , TA .)". |
| C69 | One definition in several dictionaries may be a single witness repeated | S | The guide's inference, supported by C66–C68. |
| C70 | al-Zarkashī is fourteenth-century | S | Iranica: "(d. 794/1392)". |
| C71 | "hunts out meanings from the context" (يتصيد المعاني من السياق) (labelled) | S | Islamweb ch. 18, print p. 394: "ومن أحسنها كتاب "المفردات" للراغب. وهو يتصيد المعاني من السياق". Iranica has the same quotation. |
| C72 | A qualification beyond the philologists "because he caught it from the context" (labelled) | S | islamicbook.ws: "فيذكر قيدا زائدا على أهل اللغة في تفسير مدلول اللفظ لأنه اقتنصه من السياق". Also quoted by Dāwūdī p. 25. |
| C73 | Closing judgement: a nuance caught from context is a reading, not outside evidence; his links are early-11th-century explanations | S | Explicitly the guide's advice. Consistent with Key p. 107 ("a theory of … language change"). |

### onOurSite

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C74 | Stored text matches Dāwūdī's edition (1412/1991–92) word for word in every entry compared, without footnotes | S | I compared the stored Hmd with p. 256, the kfr opening and ending with pp. 714 and 717, and the sjd ending with p. 397. They are identical apart from verse numbers, note markers and headword brackets. Shamela card: 1st ed. 1412 AH. (Iranica's bibliography cites a 1997 printing; not an error.) |
| C75 | hawramani does not name its source | S | The page has a blurb and a headword list, with no edition or editor statement. I found no "تحقيق" or "Dawudi". |
| C76 | Bracketed references are Dāwūdī's additions [p. 5]; the poets' names from his notes are absent; verse runs into the prose | S | p. 5 item 3: "تخريج الآيات القرآنية، وذكر أرقامها وسورها. وجعلناها في المتن". Stored kfr: "لمّا سمع: ألقت ذكاء يمينها في كافر والْكَافُورُ…", with no poet named. |
| C77 | 1,267 entries; حقّ, ربّ, صلا and كان did not reach our copy | S | `dicts`: 1,267. `root` Hqq/rbb/Slw/kwn: 8, 9, 6 and 13 dictionaries respectively; none is al-Rāghib. The hawramani headword list contains حق, رب, صلا and كان. |
| C78 | A few entries are cut short, such as ف ج ج | S | fjj (11977) ends "…ويستعمل في الطّريق الواسع، وجمعه". ywm also ends mid-sentence. |
| C79 | The panel orders by a stored 1109 CE (502 AH), which modern scholarship doubts; so he is listed after Ibn Sīda | S | `dicts`: Ibn Sīda 1066, al-Rāghib 1109. The API order for kfr matches. The doubts are in Iranica and Key p. 11. |

### Sources

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C80 | Citation details are accurate | S | Dāwūdī: Dār al-Qalam / al-Dār al-Shāmiyya, 1412; the introduction runs pp. 5–38 (p. 38 is signed "صفوان داودي"); the author's introduction is pp. 53–56. Key: UC Press 2018, open access. Iranica: van Gelder, 2000, updated 2012. Zarkashī: ch. 18, and the tafsīr section on passages with no transmitted explanation. |

**Totals: 80 claims. 80 supported, 0 need qualification, 0 unsupported.**

## Status of the round-3 flags and suggestions

| r3 item | Status now |
|---|---|
| C14 NQ ("the book's modern editor") | **Fixed.** It now reads "Ṣafwān Dāwūdī, whose edition our text follows". Supported. |
| C36 wording | Unchanged. It is still accurate; an optional refinement is below. |
| "two half-lines" | Unchanged, and **correct as it stands**: Dāwūdī calls the al-ʿAjjāj fragment "الشطر" (p. 717 n. 2). The suggestion should be withdrawn. |
| Unlabelled one-word glosses (covers, relations) | Unchanged. Minor; see below. |

## Flagged items

None.

## Brief issues (not factual)

- *suggestion*: **C36 wording.** "the line in which some philologists took *kāfir* for a name of night and sower" can suggest that the line mentions a sower; it is about the sun setting into *kāfir*. Optional rewording: "He first quotes one as the line that led some philologists to treat *kāfir* as a name (of night, and of the sower); for him the word only describes them."
- *suggestion*: **C10 list of works.** "books on ethics, exegesis and theology" leaves out philology, which Iranica lists alongside them. Philology is the relevant strand for a dictionary guide. Optional: "books on ethics, exegesis, theology and philology".
- *suggestion*: **Unlabelled glosses.** "covers" (*mustawfin*) and "relations" (*munāsabāt*) do not carry the "translation for this guide" label the other inline glosses have. This is minor; the shared box on the page covers translations generally.
- *note*: **Length.** Lede + body is 1,099 words by the validator, one under the 1,100 ceiling. Any further additions should be offset by cuts. summary: 44 words; lede: 84; onOurSite: about 148.
- **No other problems found.** There is no padding, generic praise or ranking. The panel order is explained as a stored-date artefact. There is no forced "original root meaning" narrative. The essay makes no promise of material the site lacks: fjj is presented as truncated, and the missing articles are named. Every root mention is linked; both kfr comparison links are present.

## Source URL checks

| id | URL | Result |
|---|---|---|
| raghib-intro | https://shamela.ws/book/23636/36 | 200. This is printed p. 54 of the Dāwūdī ed.; the introduction begins at id 35 = p. 53. OK. |
| key | https://www.ucpress.edu/books/language-between-god-and-the-poets/paper | 200. The page is the correct book, marked Open Access. OK. |
| iranica | https://www.iranicaonline.org/articles/rageb-esfahani/ | 403 to curl (Cloudflare). The content was confirmed via Wayback. It is the correct article. Keep. |
| dawudi | https://shamela.ws/book/23636/1 | 200. p. 5 "مقدّمة المحقّق". OK. |
| zarkashi-gharib | islamweb.net … النوع الثامن عشر | 200. The quotation is at print p. 394. OK. |
| zarkashi-tafsir | https://www.islamicbook.ws/qbook/alom/albrhan-004.html | 200. The quotation is present. OK. |
| hawramani | https://arabiclexicon.hawramani.com/al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran/ | 200. OK. |

Every listed source is cited and was consulted. None is unusable.

## Validator

`node scripts/validate-dictionary-guides.mjs al-mufradat` gave **ok, 1/1 guides pass**:

- root links: 5 (5 distinct pairs)
- excerpts: 3
- words: 1,099
- example roots: Hmd, kfr, sjd, fjj

## Site-data issues

1. **Stored death year 1109 CE (502 AH) is doubtful.**
   - Iranica: 502/1108 is stated "without any clear evidence"; Madelung places him in the first part of the 5th/11th century.
   - Key p. 11: he was alive in or before 1018.
   - Dāwūdī p. 38 prefers c. 425/1033–34.
   - Because of the stored year, the panel lists him after Ibn Sīda (1066). An approximate, disputed value (c. 1020–1033) would match the evidence better. hawramani repeats "d. c. 1109 CE / 502 AH", which is probably where the stored year came from.
2. **Missing articles.** No Mufradāt entry is displayed for Hqq, rbb, Slw or kwn, although the hawramani headword list includes حق, رب, صلا and كان.
3. **Damaged stored entries.**
   - fjj (11977) is truncated at "وجمعه".
   - ywm has the book's يس article appended ("يس يس قيل معناه يا إنسان …") and ends on a comma.
   - nAy contains the stray section marker "تم كتاب النون كتاب الهاء" (confirmed by grep this round).
