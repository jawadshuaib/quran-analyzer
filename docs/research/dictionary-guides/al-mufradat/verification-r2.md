# al-Mufradāt guide: verification round 2

- **Checked file:** `roots/frontend/src/content/dictionary-guides/guides/al-mufradat.ts` (the version after revision r1)
- **Verifier:** independent fact-check agent, 2026-09-26.
- **Independence:** I did not open research-notes.md or any revision-*.md file. I read verification-r1.md only for the list of earlier flags. Every verdict below rests on sources I opened myself in this round.

## Sources I opened myself (this round)

**Dāwūdī edition**, shamela.ws/book/23636

- Book card: ed. Ṣafwān ʿAdnān al-Dāwūdī; Dār al-Qalam / al-Dār al-Shāmiyya, Damascus–Beirut; 1st ed. 1412 AH; "ترقيم الكتاب موافق للمطبوع".
- I checked the printed page numbers in each page's `fld_goto_top` field:
  - id 1 = p. 5
  - ids 17–22 = pp. 21–26
  - ids 33–34 = pp. 37–38
  - ids 35–38 = pp. 53–56
  - id 238 = p. 256
  - ids 378–379 = pp. 396–397
  - ids 696–699 = pp. 714–717
- I read the text of every one of these pages.

**Key**, *Language between God and the Poets*

- Source: the OAPEN PDF, archive.org item `oapen-20.500.12657-29479`.
- The title page confirms UC Press, Oakland 2018, DOI 10.1525/luminos.54, CC-BY.
- I read printed pp. 11–13 (PDF pp. 28–30), 89–90 (PDF 106–107) and 106–108 (PDF 123–125).

**Encyclopaedia Iranica**, "Rāḡeb Eṣfahāni"

- Author G. J. van Gelder; published 1 Jan 2000; updated 8 Nov 2012.
- The live URL returns a Cloudflare 403 to curl, so I read the Wayback copy of the same URL.

**al-Zarkashī**

- Islamweb, *Burhān* ch. 18: HTTP 200. The quotation is at print p. 394.
- islamicbook.ws albrhan-004: HTTP 200. The quotation is present.

**UC Press page for Key:** HTTP 200. It is the book page (open access). doi.org/10.1525/luminos.54 → luminosoa.org and library.oapen.org both returned 403 to curl.

**arabiclexicon.hawramani.com dictionary page:** HTTP 200. It has an intro blurb ("d. c. 1109 CE / 502 AH") and a headword list, and names no edition.

**Stored entries** (`_dict_guide_tool.py`)

- Mufradāt: Hmd (54), kfr (157), sjd (1465), Swm (5683), twb (1559), rbw (4753), fjj (11977).
- Ibn Fāris kfr (163).
- `root` output for Hqq, rbb, Slw and kwn.
- Regex counts over the displayed Mufradāt, Tāj and Lane entries.

**Local API:** `/api/root/kfr/dictionaries` shows the panel order: … Ibn Sīda, al-Rāghib, al-Zamakhsharī …

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

### Header and summary fields

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title / titleAr *al-Mufradāt fī Gharīb al-Qurʾān* المفردات في غريب القرآن | S | Shamela book card. |
| C2 | titleGloss "The Single Words: On the Unfamiliar Vocabulary of the Qurʾān" | S | A fair rendering of *mufradāt* and *gharīb*. |
| C3 | author / authorAr / authorFull "Abū l-Qāsim al-Ḥusayn ibn Muḥammad ibn al-Mufaḍḍal al-Rāghib al-Iṣfahānī" | S | Dāwūdī p. 53: "قال الشيخ أبو القاسم الحسين بن محمد بن المفضل الراغب". Key p. 11 has the same form. Iranica: "Abu'l-Qāsem Ḥosayn b. Moḥammad b Mofażżal". |
| C4 | period "early 11th century CE (death date disputed)"; sortYear 1020 | S | Iranica: "(d. early 5th/11th cent.)". Key p. 11: alive in or before 1018. Dāwūdī pp. 37–38 lists dates from 402 to 503 AH and prefers c. 425. |
| C5 | kind "Dictionary of Qurʾānic words" | S | Dāwūdī p. 55: "كتاب مستوف فيه مفردات ألفاظ القرآن على حروف التهجي". |
| C6 | summary: a dictionary of the Qur'an's own vocabulary from the early eleventh century | S | As C4 and C5. Key p. 90 adds that it takes in some non-Qur'anic words; "the Qur'an's own vocabulary" is still fair. |
| C7 | summary + lede: "Many entries" start from a basic sense and follow it through the verses; "some" explain borrowing, extension or narrowing, or near-synonym differences (fix from r1) | S | Verse citation: 1,250 of 1,267 displayed entries match `[sura/ n]`. Comparatives: 61 entries match أخص/أعم/أبلغ من; the r1 counts for أصل and استعير are in the same range. "Many" and "some" match the evidence. |

### Lede

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C8 | "built his dictionary around the words of a single book" | S | p. 55, as C5. |
| C9 | Lexicon and commentary share the page | S | Entry 1465: the ضربان analysis, and qīla readings of Q 2:34 and 72:18. Key p. 13. |

### Body: biography

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C10 | Almost nothing is known of his life beyond a name linking him to Isfahan and books on ethics, exegesis and theology | S | Iranica: "Next to nothing is known about his life … One may assume on the evidence of Rāḡeb's nesba that he was born in Isfahan". Its lemma lists works on "Islamic ethics, Qurʾanic exegesis, Islamic theology, and Arabic philology". |
| C11 | Later works often date his death to 502/1108 without clear evidence | S | Iranica: "It is often stated, without any clear evidence, that he died in 502/1108". Dāwūdī p. 37 names Ḥājjī Khalīfa, Brockelmann, al-Ziriklī and Kaḥḥāla for 502. |
| C12 | Modern research places him in the early 11th c. | S | Iranica: "Madelung's study has confirmed that Rāḡeb lived 'in the first part of the fifth century'". Key p. 11. |
| C13 | Key, citing the oldest manuscript (409/1018), concludes he was alive in or before 1018 [Key p. 11] | S | Key p. 11: "ascertain from the oldest manuscript witness to his Quranic glossary that ar-Rāġib was alive in or before 1018", n. 11 "ar-Rāġib (409/1018)". |
| C14 | Dāwūdī put his death at about 425/1033–34 [pp. 37–38] | S | p. 38: "إن الأرجح أنّ وفاته في حوالي سنة ٤٢٥ هـ". 425 AH = 1033–34. |
| C15 | "Either way he was a contemporary of Ibn Fāris" [Key p. 90] | S | Key p. 90: "the dictionary of his contemporary Ibn Fāris". |
| C16 | Some four centuries after the Qur'an | S | Arithmetic. |
| C17 | Also known as *Mufradāt alfāẓ al-Qurʾān* [Iranica] (NEW) | S | Iranica: "The first, more often entitled Mofradāt alfāẓ al-Qorʾān, is a very useful alphabetical dictionary of Qorʾanic Arabic". |

### Body: "Bricks for a building"

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C18 | "Recalling his earlier writings" [pp. 53–54] (NEW) | S | p. 53: "كنت قد ذكرت في «الرسالة المنبهة على فوائد القرآن»". p. 54: "وأشرت في كتاب «الذريعة…»" and "وذكرت أنّ أول ما يحتاج…". Editor's n. 3 on p. 54 identifies "تلك الرسالة" as the *Dharīʿa*, so the plural "writings" is the safe wording. |
| C19 | He puts the verbal sciences first, and among them the precise understanding of single words | S | p. 54: "أول ما يحتاج أن يشتغل به من علوم القرآن العلوم اللفظية، ومن العلوم اللفظية تحقيق الألفاظ المفردة". |
| C20 | The Arabic "bricks" quotation | S | Verbatim on p. 54. |
| C21 | Its translation | S | Accurate. Labelled "translation for this guide". |
| C22 | He promises a book that "covers" (*mustawfin*) the single words, arranged alphabetically by first root letter [p. 55] | S | p. 55: "كتاب مستوف … على حروف التهجي … معتبرا فيه أوائل حروفه الأصلية دون الزوائد". |
| C23 | It points out the relations (*munāsabāt*) between borrowed and derived words [p. 55] | S | p. 55: "والإشارة فيه إلى المناسبات التي بين الألفاظ المستعارات منها والمشتقات". A condensed but fair rendering. |
| C24 | Key shows him repeatedly explaining Qur'anic words as *istiʿāra* borrowed from nomadic life [p. 107] | S | Key p. 107: "remarked on this process … at multiple points in his Quranic glossary, using the word for 'metaphor' (istiʿārah) … sought to read God as having taken phrases from a nomadic lifestyle". |
| C25 | A planned sequel on synonyms "and the subtle differences between them" (labelled); qalb / fuʾād / ṣadr [pp. 55–56] | S | p. 55: "الألفاظ المترادفة على المعنى الواحد، وما بينها من الفروق الغامضة … ذكر القلب مرّة والفؤاد مرة والصدر مرّة". |
| C26 | He dismisses the idea that glossing *al-ḥamdu li-llāh* as "thanks be to God" explains the Qur'an [pp. 55–56] | S | pp. 55–56: "فيقدّر أنه إذا فسّر: الحمد لله بقوله: الشكر لله … فقد فسّر القرآن ووفّاه التبيان". |
| C27 | Dāwūdī could not find the sequel [p. 55] | S | p. 55, n. 2: "لم نجد هذا الكتاب". |
| C28 | "the habit surfaces in a few dozen of the *Mufradāt* entries we display, among them ح م د" (NEW, fixes C18 of r1) | S | 61 displayed entries match (أخص\|أعم\|أبلغ) من. I read all 61 contexts: most compare near-synonyms (عمل/فعل, معرفة/علم, مرية/شك, صفح/عفو, ظل/فيء…); a minority compare forms of one root. |

### Body: the ḥ-m-d example

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C29 | The Hmd excerpt's Arabic matches the stored entry | S | Entry 54. Identical on Dāwūdī p. 256. |
| C30 | Hmd translation "*Ḥamd* to God Most High: praising Him for [His] excellence. It is narrower than *madḥ* and broader than *shukr*." (fix from r1) | S | Accurate for "الحمد لله تعالى: الثناء عليه بالفضيلة، وهو أخصّ من المدح وأعمّ من الشكر". |
| C31 | *Madḥ* can praise a handsome face as readily as generosity; *ḥamd* only the latter kind; *shukr* only answers a favour [p. 256] | S | Entry 54 / p. 256: "فقد يمدح الإنسان بطول قامته وصباحة وجهه، كما يمدح ببذل ماله وسخائه … والحمد يكون في الثاني دون الأول، والشّكر لا يقال إلا في مقابلة نعمة". |

### Body: "Reading an entry" (k-f-r)

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C32 | kfr locator pp. 714–717 | S | The entry begins on p. 714 (id 696) and the text continues through p. 717 (id 699). |
| C33 | The kfr excerpt's Arabic matches the stored entry | S | Entry 157. The same text is on p. 714. |
| C34 | The kfr translation | S | Accurate. |
| C35 | He starts "in the language" with covering, citing two half-lines by poets he does not name | S | Entry 157: "ألقت ذكاء يمينها في كافر" and "قال الشاعر: كالكرم إذ نادى من الكافور", each used twice, never with a poet's name. Dāwūdī's notes on p. 714 name Thaʿlaba b. Ṣuʿayr and al-ʿAjjāj. |
| C36 | "The first time, he quotes one to correct some philologists who took *kāfir* in it as a name for night and sower; for him the word only describes them" (NEW) | S | Entry 157: "ووصف الليل بالكافر … والزّرّاع … وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع: ألقت ذكاء يمينها في كافر". The site's own faithful translation and the harmonized English read it the same way ("correcting philologists who assumed otherwise"). Ibn Fāris (entry 163) reports that same line being glossed with *kāfir* as a noun ("مغيب الشمس", "البحر"), which fits. See brief issues for a wording nuance. |
| C37 | He reaches ingratitude through verses setting *kufr* against *shukr* (Q 14:7, Q 27:40) | S | Entry 157: [النمل/ 40], [البقرة/ 152], [إبراهيم/ 7]. The definition via "ترك أداء شكرها" comes first. |
| C38 | Denial grows out of ingratitude (Q 2:41) | S | "ولمّا كان الكفران يقتضي جحود النّعمة صار يستعمل في الجحود، قال: وَلا تَكُونُوا أَوَّلَ كافِرٍ بِهِ". |
| C39 | Notes on which form is used more for which sense are tendencies, not rules | S | "أكثر استعمالا … أكثر … فيهما جميعا". |
| C40 | *mutaʿāraf* marks the familiar religious meaning; the gloss "conventionally understood" is now labelled | S | "والكافر على الإطلاق متعارف فيمن يجحد الوحدانيّة…". |
| C41 | Rival interpretations with *qīla* (labelled); Q 57:20 sowers or unbelievers | S | "قيل: عنى بالكفّار الزّرّاع … وقيل: بل عنى الكفار". |
| C42 | Once he refers the reader to his own ethical treatise, the *Dharīʿa* | S | "وقد بيّنته في كتاب «الذّريعة إلى مكارم الشّريعة»". Iranica describes the *Dharīʿa* as ethics ("the underlying ethical foundations of the law"). |

### Body: the Ibn Fāris comparison

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C43 | Ibn Fāris kfr: starts from covering, illustrated from ordinary speech (mail-coat covered with a garment) | S | Entry 163: "يُقَالُ لِمَنْ غَطَّى دِرْعَهُ بِثَوْبٍ: قَدْ كَفَرَ دِرْعَهُ". |
| C44 | He reaches religion in one step: kufr, opposite of faith, "so called because it is a covering of the truth"; ingratitude "likewise" | S | Entry 163: "وَالْكُفْرُ: ضِدُّ الْإِيمَانِ، سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ. وَكَذَلِكَ كُفْرَانُ النِّعْمَةِ". |
| C45 | Al-Rāghib calls the *kāfir* of Q 24:55 one who "conceals the truth" | S | "[النور/ 55] عني بالكافر السّاتر للحقّ". |
| C46 | "Neither records the word's history; each explains how its senses hang together" | S | This is the guide's own judgement, fairly drawn from entries 157 and 163; neither gives dated usage. |

### Body: "Where the lexicon becomes interpretation" (s-j-d)

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C47 | sjd locator pp. 396–397 | S | Shamela ids 378–379. |
| C48 | The sjd excerpt's Arabic matches the stored entry | S | Entry 1465 = pp. 396–397. |
| C49 | sjd translation | S | Accurate. |
| C50 | Shadows and trees perform *sujūd* (Q 13:15, Q 55:6) | S | Entry 1465: [الرعد/ 15] "وظلالهم", [الرحمن/ 6] "والنجم والشجر". |
| C51 | Q 4:154 is glossed "humbled, submissive" (labelled), with no mention of posture | S | "ادْخُلُوا الْبابَ سُجَّداً [النساء/ 154]، أي: متذلّلين منقادين". |
| C52 | "in the religious Law" separates general from technical, undated; the same for fasting, repentance and usury | S | Swm: "والصَّوْمُ في الشّرع". twb: "والتَّوْبَةُ في الشرع". rbw: "لكن خصّ في الشرع". None gives a date. |
| C53 | The entry sets out, "attributing it to no one", the choice/subjection analysis; "a silent yet speaking indication" (labelled) (NEW) | S | "وذلك ضربان: سجود باختيار … وسجود تسخير … وهو الدّلالة الصامتة الناطقة المنبّهة على كونها مخلوقة، وأنّها خلق فاعل حكيم". There is no qīla or name here, while the same entry uses qīla for Q 2:34, 20:130, 72:18 and 12:100. |
| C54 | Key: a blend of traditionist piety, Sufism and philosophical ethics seeped "however subtly" into the glossary [p. 13] | S | Key p. 13: "traditionist piety …, the mystical approach … 'Sufism,' and the Aristotelian and Neoplatonic ethical heritage … Ar-Rāġib then allowed this combination to seep, however subtly, into his glossary of the Quran". |
| C55 | Read "kinds" schemes (*ḍarbān*, *awjuh*) as interpretation | S | This is advice from the guide. The terms occur in 52 displayed entries (e.g. Elm, jEl, hdy, qbl). |

### Body: "Evidence and its limits"

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C56 | Nearly every displayed entry quotes at least one verse | S | 1,250 of 1,267. |
| C57 | Poetry is sparse; Dāwūdī counts no more than 500 lines [p. 25] | S | p. 25: "بينما كتاب الراغب لا يتجاوز ٥٠٠ بيت". |
| C58 | "the text seldom names the poet; the printed edition's attributions are the editor's" [p. 5] (NEW) | **NQ** | The first half is supported: "قال الشاعر / قول الشاعر" appears in 238 displayed entries, against 12 entries where al-Rāghib names the poet in the text (e.g. "قال النابغة" bEd, "قول لبيد" Hkm, "قال زهير" brj, "قال طرفة" gbr, "قال العجاج" krs). The second half overgeneralises. p. 5 (method item 6, "نسبة الأبيات الشعرية لقائليها") supports only that the editor supplied attributions in his notes. Some attributions in the printed text are al-Rāghib's own. |
| C59 | He cites variant readings without separating accepted from irregular ones [p. 26] | S | p. 26: "لم يميّز بين القراءات المتواترة والشاذة، بل يكتفي أن يقول: وقرئ كذا". |
| C60 | Some sayings he attributes to the Prophet are not hadith [p. 26] | S | p. 26: "نسبته بعض الأقوال إلى الرسول، وليست هي من قوله … «لا جبر ولا تفويض»". |
| C61 | He names earlier philologists in only about 60 of our entries | S | A regex over 22 philologist names gives 65 entries. That figure includes some false hits: الخليل in 19 entries, some of them Abraham's epithet. So about 60 is right. |
| C62 | Dāwūdī traces heavy, unacknowledged use of Ibn Fāris's *al-Mujmal*, not the *Maqāyīs* [pp. 21–23] | S | p. 21: "كتاب «المجمل في اللغة» لابن فارس. ويبدو أنّ الراغب قد اعتمد عليه كثيرا، مع أنه لم يذكره باسمه". The locator could be narrowed to p. 21; pp. 21–23 is the whole sources list. |
| C63 | So an unattributed definition may be older than al-Rāghib, sometimes taken over word for word (NEW) | S | p. 21: "والتشابه الكبير في العبارة، وربما ينقل عنه حرفيا". The p. 256 notes also point to *al-Mujmal* for حمم / حمر. |
| C64 | A view introduced by *qīla* (in about half our entries) is reported, not necessarily endorsed | S | 646 of 1,267 displayed entries (51%). |
| C65 | "His own voice is surest in first-person asides like that reference to the *Dharīʿa*" (NEW) | S | This is the guide's interpretation and is consistent with p. 21. It does not overstate. |
| C66 | Al-Fīrūzābādī and al-Samīn al-Ḥalabī reworked it into their own books [p. 24] | S | p. 24: Fīrūzābādī "اختصره، وزاد فيه … «بصائر ذوي التمييز»"; al-Samīn "جعل كتاب الراغب لبّ كتابه" in *ʿUmdat al-ḥuffāẓ*. |
| C67 | *Tāj al-ʿArūs* names him in some 340 of our entries (NEW figure) | S | `grep murtada… 'الراغب'` finds 340 displayed entries. The reviser reports one of them as the ordinary word. "Some 340" holds. |
| C68 | Lane names him in about 265, often via the *Tāj* | S | 265 displayed Lane entries match "R.ghib"; 159 of them have "Er-Rághib , TA". |
| C69 | "one definition in several dictionaries may be a single witness repeated" | S | The guide's inference, supported by C67 and C68. |

### Body: al-Zarkashī and the closing paragraph

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C70 | al-Zarkashī is fourteenth-century | S | d. 794/1392 (Iranica). |
| C71 | Zarkashī: "hunts out meanings from the context" (يتصيد المعاني من السياق) | S | Islamweb *Burhān* ch. 18, print p. 394: "ومن أحسنها كتاب " المفردات " للراغب. وهو يتصيد المعاني من السياق". |
| C72 | Zarkashī: a qualification beyond the philologists "because he caught it from the context" | S | islamicbook.ws: "فيذكر قيدا زائدا على أهل اللغة في تفسير مدلول اللفظ لأنه اقتنصه من السياق". The same passage is quoted by Dāwūdī on p. 25. |
| C73 | Closing judgement: a nuance caught from context is a reading, not outside evidence; his links are early-11th-c. explanations, not records of usage | S | Clearly the guide's own advice, and consistent with C24 and Key p. 106–107 (his istiʿāra accounts are a "theory of … language change"). |

### onOurSite

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C74 | The stored text matches Dāwūdī word for word in the entries compared, without footnotes; ed. Damascus and Beirut, 1412/1991–92 | S | I compared Hmd (p. 256), sjd (pp. 396–397) and kfr (p. 714). The text is identical apart from note markers, poem numbers and headword brackets. The Shamela card gives 1412 AH. (Iranica's bibliography lists a 1997 printing; that is a later printing, which does not affect the claim.) |
| C75 | hawramani does not name its source; bracketed sura/verse references are Dāwūdī's additions [p. 5]; poets' names from his notes are absent; verse runs into prose | S | The hawramani page has no edition statement. p. 5 item 3: "تخريج الآيات القرآنية، وذكر أرقامها وسورها. وجعلناها في المتن". Entry 157 compared with p. 714 nn. 2–3. |
| C76 | 1,267 entries displayed; articles such as حقّ، ربّ، صلا، كان missing, so some frequent roots show no entry | S | `dicts` gives 1267. `root` for Hqq, rbb, Slw and kwn shows no Mufradāt entry, and the hawramani headword list contains حق، رب، صلا، كان. |
| C77 | fjj is cut short | S | Entry 11977 ends "…ويستعمل في الطّريق الواسع، وجمعه". |
| C78 | The panel orders by a stored 1109 CE (502 AH), which modern scholarship doubts; "that is why it lists him after Ibn Sīda, although on the evidence above he was a contemporary of Ibn Fāris" (NEW wording) | S | `dicts`: Ibn Sīda 1066, al-Rāghib 1109. The API order for kfr has Ibn Sīda immediately before al-Rāghib. FORMAT.md: the panel sorts by stored year. Key p. 90 supports "contemporary". |

### Sources

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C79 | Dāwūdī citation (Dār al-Qalam / al-Dār al-Shāmiyya, 1412/1991–92; editor's introduction pp. 5–38) | S | The Shamela card. The introduction runs from p. 5 ("مقدّمة المحقّق") to p. 38 (signed "صفوان داودي"). |
| C80 | Key citation (Oakland: UC Press 2018; open access; DOI 10.1525/luminos.54) | S | PDF title and copyright pages. |
| C81 | Iranica citation (van Gelder, 2000; updated 2012) | S | "Published January 1, 2000", "Last Updated November 8, 2012". |
| C82 | Zarkashī citations: ch. 18 "Maʿrifat gharībih" and the tafsīr chapter on passages without transmitted explanation | S | Both pages opened. Ch. 18 is "النوع الثامن عشر: معرفة غريب القرآن", and the tafsīr chapter has "ما لم يرد فيه نقل عن المفسرين". |

**Totals: 82 claims. 81 supported, 1 needs qualification, 0 unsupported.**

## Status of the round-1 flags

| r1 flag | Status now |
|---|---|
| C7 "typically" | Fixed (C7). |
| C18 "runs through" | Fixed (C28). |
| C20 Hmd translation | Fixed (C30). |
| C31 kfr half-lines | Fixed (C35 and C36). |
| C44 sjd "his own analysis" / "bowing" / unlabelled | Fixed (C53). |
| C54 "His own voice is in the definitions" | Fixed with narrower wording (C63 and C65). The reviser's deviation from the suggested wording is justified: p. 21 undercuts treating unattributed classifications as certainly his. |
| C56 Tāj count | Fixed, now 340 (C67). |
| C70 "Ibn Fāris's generation" | Fixed (C78). The reviser declined "not after Ibn Sīda". That is justified: Dāwūdī p. 37 reports al-Dhahabī's 42nd ṭabaqa (deaths 440–470), and I confirmed this on the page. |

## Flagged items and fixes

1. **C58 (NQ): poet attributions.**
   - Problem: "the printed edition's attributions are the editor's" implies that every attribution in the edition is editorial. In fact al-Rāghib himself names the poet in about a dozen displayed entries: النابغة in bEd and AHd, لبيد in Hkm and HSr, زهير in brj and xbl, طرفة in gbr, الأعشى in x*l, العجاج in krs, أبو ذؤيب in nhr, الهذلي in $rb and sbE.
   - Fix: change to "the text seldom names the poet; most attributions in the printed edition come from the editor's notes [^dawudi|p. 5]". Alternatively: "…; the edition's footnote attributions are the editor's".

## Brief issues (not factual)

- *suggestion*: Lede + body now count **1,122 words** (validator), just over the 700–1,100 target. Trim about 25 words. Candidates:
  - the second half of the Ibn Fāris paragraph;
  - "Between these he sets the Qur'an's wider usage:" → "He also notes".
- *suggestion*: C36 wording. "he quotes one to correct some philologists" slightly misplaces the purpose: he quotes the line that those philologists heard and misread. A cleaner version: "The first time, the line is the one some philologists heard and took *kāfir* in as a name; for him the word only describes night and sower." Optional.
- *suggestion*: The C62 locator could be narrowed from pp. 21–23 to p. 21, where the *Mujmal* passage is.
- *suggestion*: onOurSite runs to 154 words, just above the ≈60–150 guide. Fine as is; trim if convenient.
- The essay has no padding, generic praise or rankings. All three excerpt translations are labelled by the page. The short glosses are now labelled. Every root mention is a link. The essay does not force an "original root meaning" narrative, and the religious-Law labels are handled with care.

## Source URL checks

| id | URL | Result |
|---|---|---|
| raghib-intro | https://shamela.ws/book/23636/36 | 200. This is printed p. 54 of the Dāwūdī ed.; the introduction starts at id 35 = p. 53. OK. |
| key | https://www.ucpress.edu/books/language-between-god-and-the-poets/paper | 200. The UC Press page for the book, open access. OK. (doi.org/10.1525/luminos.54 → luminosoa.org and library.oapen.org both gave 403 to curl, so the reviser's choice is sound. The DOI is kept in the citation text.) |
| iranica | https://www.iranicaonline.org/articles/rageb-esfahani/ | 403 (Cloudflare) to curl. Content confirmed via Wayback. It is probably fine in a normal browser; keep it, but note it. |
| dawudi | https://shamela.ws/book/23636/1 | 200. p. 5, the editor's introduction. OK. |
| zarkashi-gharib | islamweb.net … النوع الثامن عشر | 200. The quotation is present. OK. |
| zarkashi-tafsir | https://www.islamicbook.ws/qbook/alom/albrhan-004.html | 200. The quotation is present. OK. |
| hawramani | https://arabiclexicon.hawramani.com/al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran/ | 200. OK. |

Every listed source is cited in the text and every one was consulted. None is unusable.

## Validator

`node scripts/validate-dictionary-guides.mjs al-mufradat` gave **ok, 1/1 guides pass**:

- root links: 5 (5 distinct root/dictionary pairs)
- excerpts: 3
- words (lede + body, excluding excerpts): 1,122
- example roots: Hmd, kfr, sjd, fjj

## Site-data issues

1. **Stored death date 1109 CE (502 AH) is doubtful.**
   - Iranica: 502/1108 is stated "without any clear evidence"; Madelung places him in the first part of the 5th/11th century.
   - Key p. 11: he was alive in or before 1018 (manuscript of 409 AH).
   - Dāwūdī pp. 37–38 prefers c. 425/1033–34.
   - The panel therefore lists him after Ibn Sīda (1066). A value such as c. 1025 (marked approximate/disputed) would fit the evidence better.
   - The same "d. c. 1109 CE / 502 AH" appears on the hawramani source page.
2. **Missing articles.** Mufradāt articles present on hawramani are not displayed for حق (Hqq), رب (rbb), صلا (Slw) and كان (kwn). This is probably a parsing or matching failure for short or alif-spelled headwords.
3. **Truncated entry.** The fjj entry (id 11977) is cut off mid-sentence ("وجمعه").
