# Tāj al-ʿArūs guide: verification, round 3

**Page checked:** `roots/frontend/src/content/dictionary-guides/guides/taj-al-arus.ts` (the text after revision r2)

**Date:** 2026-09-26

**Independence:** I did not open research-notes.md or any revision-*.md file. I read verification-r2.md only to learn which points round 2 flagged. I checked every claim below again, against sources I downloaded and read myself in this round.

## Sources opened in this round

- **Tāj, author's introduction.** Kuwait edition as paginated in al-Maktaba al-Shāmila, https://shamela.ws/book/7030/1 to /12, fetched and read in full for pp. 2–11.
  - The book card (https://shamela.ws/book/7030) reads «وزارة الإرشاد والأنباء في الكويت… عدد الأجزاء: ٤٠، أعوام النشر: (١٣٨٥ - ١٤٢٢ هـ) = (١٩٦٥ - ٢٠٠١ م)… [ترقيم الكتاب موافق للمطبوع]».
- **Ibn Manẓūr, *Lisān al-ʿArab*, introduction.** https://shamela.ws/book/1687/8. The page title is «ج1 - ص8 - كتاب لسان العرب - مقدمة المؤلف».
  - The card (https://shamela.ws/book/1687) reads «الناشر: دار صادر - بيروت، الطبعة: الثالثة - ١٤١٤ هـ، عدد الأجزاء: ١٥، [ترقيم الكتاب موافق للمطبوع]».
- **al-Jabartī, *ʿAjāʾib al-Āthār*.** https://shamela.ws/book/11998/801–803 and /810–811 (vol. 2, pp. 103–105 and 112–113, section «سنة خمس ومائتين وألف»). The card reads «الناشر: دار الجيل بيروت».
- **Kuwait ed. vol. 1 (1965), editor's front matter.** The archive.org OCR "1 - تاج العروس_djvu.txt" from https://archive.org/details/ZUB1965AR. It is signed «كتبه: عبد الستار احمد فراج». I read the sections «تأليف تاج العروس», «طريقة تاج العروس», «احتفال الزبيدي بإنجاز التاج», «صلة الزبيدي بالقاموس» and «التعريف بالزبيدي», plus the colophon list («وآخر الكتاب في رجب سنة 1188»).
- **Lane, *Lexicon* Book I (Williams and Norgate, 1863), Preface.** The full OCR of https://archive.org/details/arabicenglishlex0001edwa.
  - Page headers: "PREFACE. xix" at OCR line 1084 and "xX" at line 1158.
  - page_numbers.json: leaf 31 = XXV, so index n24 (leaf 25) = xix.
- **Haywood, *Arabic Lexicography* (1960).** The OCR of https://archive.org/details/in.gov.ignca.12555: pp. 67–70 and 86–90.
- **Baalbaki, JAS 6 (2019) 185–208.** The PDF at the AUB URL, converted with pdftotext. The passage is on p. 203.
- **arab-ency.com.sy/details/4285** (Bishr ibn Abī Khāzim). The page footer reads «المجلد الخامس، طبعة 2002، دمشق – رقم الصفحة ضمن المجلد: 119», and the author is إحسان النص.
- **shamela.ws/author/711** (al-Shihāb al-Khafājī).
- **IslamWeb, *al-Qāmūs*, author's introduction** (bk_no=123, ID=2).
- **The hawramani category page.**
- **Shamela Tāj 7030/3326–3330** (vol. 6, pp. 547–551, the entry صلح).
- **Stored entries**, read with `_dict_guide_tool.py entry`:
  - Tāj: rHm (13), fsd (2385), Slw (1396), SlH (690), kfr (159), xlq (49), dyn (1388)
  - Qāmūs: fsd (2390)
  - Lisān: fsd (2384)
  - Lane: nhy (2264)
- **Read-only SQL** over the 1,600 displayed Tāj entries.

## Claims table

S = supported. NQ = needs qualification. U = unsupported.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | title / titleAr تاج العروس من جواهر القاموس | S | Tāj intro vol. 1 p. 11: «وسميته. (تاج العروس من جواهر القاموس)» |
| C2 | titleGloss "The Bride's Crown, from the Jewels of al-Qāmūs" | S | A fair rendering of C1 |
| C3 | author / authorAr Murtaḍā al-Zabīdī | S | Jabartī vol. 2 p. 104: «الشهير بمرتضى الحسيني الزبيدي» |
| C4 | authorFull Abū l-Fayḍ Muḥammad ibn Muḥammad al-Ḥusaynī al-Zabīdī, known as Murtaḍā | S | Jabartī p. 104 (name chain); p. 105: «وكناه… بابي الفيض»; the Kuwait editor, «التعريف بالزبيدي» |
| C5 | period d. 1205 AH / 1791 CE | S | Jabartī p. 112, in the 1205 section: «وأصيب بالطاعون في شهر شعبان… وتوفي يوم الأحد». Shaʿbān 1205 ≈ April 1791. Lane Preface p. xviii: "died A.D. 1791 (in the year of the Flight 1205)" |
| C6 | kind: commentary on al-Qāmūs | S | Intro p. 4: «في وضع شرح عليه، ممزوج العبارة» |
| C7 | Summary: an 18th-century commentary wrapping the Qāmūs in quotations, Qur'anic and poetic evidence, disputes, corrections and additions | S | Lane p. xviii: "interwoven commentary on the Kámoos… corrections of mistakes… examples in prose and verse; and a very large collection of additional words"; entries fsd, Slw, SlH, kfr |
| C8 | Summary: useful for finding who recorded a meaning and on what evidence, once the voices are told apart | S (interpretation) | The fsd and Slw entries; Kuwait editor, «ينسب كثيرا من التفسير اللغوي إلى قائليه» |
| C9 | Lede: working in Cairo in the 1760s and 1770s | S | Kuwait editor: began seven years after arriving in 1167 (i.e. c. 1174 / 1760–61); colophon «وآخر الكتاب في رجب سنة 1188»; al-Zabīdī's letter: «مكثت مشتغلا به أربعة عشر عاما وشهرين» |
| C10 | Lede: phrase-by-phrase commentary that names who gave a meaning, adds verse or poem, reports disputes, corrects slips, supplies missing words | S | Entries fsd, rHm, kfr (e.g. «لا شبهة في أنه غلط… قال شيخنا. قلت: لا غلط»), SlH supplement; Kuwait editor, «يستدرك ما نقص» |
| C11 | Lede: reading well means tracking the voices of the Qāmūs, al-Zabīdī and the scholars he quotes | S | Kuwait editor: «لو أزيلت الحدود… لكان من الصعب معرفة ما لهذا أو ما لذاك» |
| C12 | By al-Zabīdī's account the Qāmūs was prized for concision and so attracted commentators | S | Intro p. 2: «أوجز لفظه وأشبع معناه… ولما كان إبرازه في غاية الإيجاز… تصدى لكشف غوامضه ودقائقه رجال» |
| C13 | Among the fullest was his teacher al-Fāsī's; "my mainstay in this discipline"; translations are the guide's own | S | Intro p. 3: «ومن أجمع ما كتب عليه… شرح شيخنا… محمد بن الطيب… الفاسي… وهو عمدتي في هذا الفن». Jabartī p. 104 names «ابن الطيب» among his teachers. Translation label present |
| C14 | His plan: *mamzūj al-ʿibāra*, noting where copies differ, quoting sources explicitly, gathering verses as evidence | S | Intro p. 4: «ممزوج العبارة… واف ببيان ما اختلف من نسخه»; p. 5: «والإنباه عن مضاربه ومآخذه بصريح النقول، والتقاط أبيات الشواهد له» |
| C15 | He wrote for scholars, especially teachers of the rare vocabulary of hadith and of the major works on Arabic | S | Intro p. 4: «فاقة الأفاضل… ولا سيما من انتدب منهم لتدريس علم غريب الحديث، وإقراء الكتب الكبار من قوانين العربية» |
| C16 | Born 1145 AH (1732–33) | S | Kuwait editor: «ولد سنة خمس وأربعين ومائة وألف»; Jabartī p. 104: «كما سمعته من لفظه ورايته بخطه» |
| C17 | Later sources say he was born in Bilgram, India, but the Kuwait editor finds nothing clear in al-Zabīdī's own writings that places him in India | S | Kuwait editor: *Abjad al-ʿUlūm*, *Nashr al-ʿArf*, *Fihris al-Fahāris* and the 2nd printing «ذكروا أنه ولد ببلد هندي هو بلجرام»; «فنحن لا نجد نصا واضحا في كلامه يدل على أنه من الهند». Round-2 flag resolved |
| C18 | Studied in the Hijaz and Yemen | S | Jabartī p. 104: «حج مرارا… بمكة… ونزل بالطائف بعد ذهابه إلى اليمن»; Kuwait editor, his Qāmūs *isnād* taken in Zabīd and Medina |
| C19 | Reached Cairo 1167 AH (1753) | S | Jabartī p. 104: «ثم ورد إلى مصر في تاسع سفر سنة سبع وستين ومائة وألف» (≈ 6 Dec. 1753) |
| C20 | Died there in Shaʿbān 1205, spring 1791 | S | Jabartī p. 112 (plague, Shaʿbān); p. 113: buried at al-Sayyida Ruqayya (Cairo) |
| C21 | In Cairo's libraries he found many of the 100+ works his introduction lists, from the Lisān to works on history and medicine | S | Intro pp. 5–9: the Lisān on p. 5; *Taʾrīkh Dimashq* on p. 8; «والتذكرة في الطب، للحكيم داود الأنطاكي» on p. 9. Named *khizāna*s: Azbak, Ṣarghatmish, al-Muʾayyad, Qāytbāy, al-Maḥmūdiyya. Lane p. xviii: "more than a hundred are enumerated". Kuwait editor: «ظفر في مصر بأمهات الكتب… وجده بالقاهرة» |
| C22 | The Kuwait editor, from dates recorded in the text, puts completion in Rajab 1188 AH (1774) | S | Kuwait editor, list of end-of-letter colophons: «وآخر الكتاب في رجب سنة 1188». Rajab 1188 ≈ Sept. 1774 |
| C23 | Autograph: line over the Qāmūs words. Students' copies: red. Printed editions: round brackets. Otherwise hard to tell whose words are whose | S | Kuwait editor, «طريقة تاج العروس»: «يضع كلمة القاموس وفوقها خط… باللون الأحمر… بين قوسين». Haywood p. 89: "put the contents of the 'Qamus' in brackets" |
| C24 | On our site bracketed words are usually al-Fīrūzābādī's | S | Tāj fsd (2385) against Qāmūs fsd (2390); Slw; SlH |
| C25 | In his own voice *al-muṣannif* alone = al-Fīrūzābādī | S | Intro p. 7: «…والمثلثات، الأربعة للمصنف»; kfr: «والعجب من المصنف كيف لم ينبه» (about the Qāmūs) |
| C26 | *shaykhunā* = al-Fāsī | S | Intro p. 3: «شرح شيخنا… الفاسي»; p. 4: «وقد تكفل شيخنا بالرد عليه» |
| C27 | *qultu* introduces his own view | S | rHm (13); kfr (159): «قاله شيخنا. قلت: لا غلط» |
| C28 | *intahā* closes a quotation, as Lane notes under nhy | S | Lane nhy (2264): "اِنْتَهَى It is ended: a word put to mark the end of a quotation" |
| C29 | *wa-mimmā yustadrak ʿalayh* opens the end-of-entry supplement (SlH), adding what the Qāmūs lacks | S | SlH (690): «ومما يستدرك عليه: قوم صلوح…». Kuwait editor: «وبعد انتهاء المادة… يستدرك ما نقص» |
| C30 | After his list of sources come 28 lines taken almost word for word, without acknowledgement, from Ibn Manẓūr's introduction | S | Kuwait editor: «نقل ثمانية وعشرين سطرا من مقدمة ابن منظور… دون أن يشير إلى ذلك، وغير بعض الألفاظ القليلة… وأضاف بضعة ألفاظ… انظر هذا النص بعد تعداده للكتب التي رجع إليها». My own comparison of Tāj pp. 9–11 with Lisān vol. 1 p. 8 confirms near-verbatim identity |
| C31 | In them he praises the work, disclaims merit, makes the original authors answerable for right or wrong | S | Tāj p. 10: «بديع الإتقان… حللت بوضعه ذروة الحفاظ… وليس لي في هذا الشرح فضيلة… فعهدته على المصنف الأول» |
| C32 | Block quotation «وليس لي في هذا الشرح فضيلة أمت بها … سوى أنني جمعت فيه ما تفرق في تلك الكتب», its translation, and the attribution "adapting Ibn Manẓūr's introduction… (translation for this guide)" | S | Verbatim on Tāj p. 10. The translation is accurate. Lisān p. 8 has the same sentence with «في هذا الكتاب» and «أتمسك بسببها». Round-2 C31 resolved |
| C33 | Ibn Manẓūr had written "this book" | S | Lisān p. 8: «وليس لي في هذا الكتاب فضيلة» |
| C34 | Ibn Manẓūr credited al-Azharī and Ibn Sīda where al-Zabīdī credits "our shaykh" | S | Lisān p. 8: «لم يترك فيها الأزهري وابن سيده لقائل مقالا… فإنهما عينا في كتابيهما عمن رويا». Tāj p. 10: «لم يترك فيها شيخنا لقائل مقالا… فإنه عني في شرحه عمن روى». See brief issue B2 (clarity) |
| C35 | The modest self-portrait is borrowed | S | Follows from C30–C34 |
| C36 | In practice he weighs and corrects, even his teacher | S | rHm (13): «قلت: وفي نقله عن العباب نظر». kfr (159): «قلت: لا غلط، والصواب ما ذهب إليه الجوهري» against al-Fāsī |
| C37 | In rHm al-Fāsī cites al-Ṣaghānī's *al-ʿUbāb* against a usage; three markers appear together | S | rHm: «ونقل شيخنا عن العباب للصاغاني أن ترحمت عليه لحن… انتهى سياق شيخنا. قلت:» |
| C38 | rHm excerpt and translation | S | Matches entry 13 verbatim; the translation is accurate («مصنفه» correctly rendered "its author", i.e. al-ʿUbāb's) |
| C39 | Qāmūs fsd: bare equivalents; excerpt and translation | S | Entry 2390: «والفَسادُ: أخْذُ المالِ ظُلْماً، والجَدْبُ.» |
| C40 | In the Tāj the same words are in round brackets | S | Entry 2385: «(والفَسَادُ: أَخْذُ المالِ ظُلْماً)… (الجَدْبُ)» |
| C41 | Tāj fsd excerpt and translation | S | Matches entry 2385; the translation is accurate |
| C42 | Two Qāmūs senses are tied to named authorities' readings of Q 28:83 and Q 30:41 | S | Entry 2385: «هكاذا فسر مسلم البطين» (28:83); «وهاذا قول الزجاج» (30:41) |
| C43 | "In our view… one of the Tāj's most useful habits…" | S (labelled opinion) | Framed as the guide's view. The habit is attested by the Kuwait editor: «ينسب كثيرا من التفسير اللغوي إلى قائليه» |
| C44 | The entry also gives grammar, poetry, a report, a hadith, and al-Fāsī's note (*baṭala* vs *taghayyara*; most read Q 21:22 the first way) | S | Entry 2385: Sībawayh; verses; ʿAbd al-Malik *khabar*; *ghīla* hadith; «قال شيخنا… فقيل: فسد الشيء: بطل واضمحل، ويكون بمعنى تغير، ومن الأول عند الأكثر: {لو كان فيهما…}». Round-2 B4 wording fixed |
| C45 | Much of this is in the Lisān, incl. Q 30:41 credited to "al-Zajjājī"; Muslim al-Baṭīn and al-Fāsī's note are not | S | Lisān fsd (2384): «هذا قول الزجاجِيِّ». Sībawayh, verses, *khabar*, hadith present. No البطين, no شيخنا |
| C46 | Lane called the Tāj "the medium through which I have drawn most of the contents of my lexicon" | S | Lane 1863, p. xix (OCR line 1139, under the "PREFACE. xix" header): verbatim. Round-2 B2 framing fixed |
| C47 | Lane found its quotations faithfully transcribed | S | p. xx: "a most laborious collation of passages quoted in it… in every instance I found that they had been faithfully transcribed" |
| C48 | In most articles he compared, 3/4 to 9/10 of the additions stood verbatim in the Lisān; he faulted al-Zabīdī for not saying so | S | p. xx: "in most of the articles in the former, from three-fourths to about nine-tenths of the additions… existed verbatim in the Lisán… want of candour… by not stating…" |
| C49 | Baalbaki counts the Lisān among his major sources | S | Baalbaki p. 203: "al-Zabīdī (d. 1205/1790), in spite of utilizing the Lisān as one of his major sources in Tāj al-ʿarūs…" |
| C50 | One entry cannot confirm Lane's proportions but shows what they mean | S (interpretation) | Appropriately hedged |
| C51 | Slw: the bracketed Qāmūs gives five senses of *ṣalāt* | S | Entry 1396: (الدعاء), (الرحمة), (الاستغفار), (حسن الثناء من الله… على رسوله…), (عبادة فيها ركوع وسجود) |
| C52 | The commentary calls supplication "the root of its meanings", citing Q 9:103 and al-Aʿshā's wine-jar verse | S | Entry 1396: «(الدعاء)، وهو أصل معانيها… {وصل عليهم}… قول الأعشى: وصلى على دنها وارتسم أي دعا لها أن لا تحمض» |
| C53 | Slw excerpt and translation | S | Matches entry 1396. The translation is accurate, and «وفي الكل نظر، انتهى» is correctly inside al-Fāsī's quotation |
| C54 | Further authorities from Ibn al-Athīr to al-Rāzī on new coinage vs old word extended; the entry does not decide | S | Entry 1396: Ibn al-Athīr; *al-Miṣbāḥ* (*naql* vs *majāz*); al-Rāghib; al-Munāwī quoting al-Rāzī (Muʿtazila «الأسماء الشرعية» vs «المجازات المشهورة»). It then moves to *al-Ṣiḥāḥ* without a verdict |
| C55 | SlH: *ṣilāḥ* "reconciliation" attested in a verse the entry attributes to Bishr ibn Abī Khāzim | S | Entry 690: «(وصالحه مصالحة، وصلاحا)… قال بشر بن أبي خازم: يسومون الصلاح بذات كهف…» |
| C56 | Bishr: pre-Islamic poet of the late 6th century | S | arab-ency 4285 (al-Naṣṣ, vol. 5, 2002, p. 119): «(… ـ نحو 598م)… من فحول شعراء الجاهلية… عاش في أواخر القرن السادس الميلادي» |
| C57 | Near the end, the supplement defines *iṣṭilāḥ* as "the agreement of a particular group on a particular matter", citing al-Khafājī | S | Entry 690, at character ~4,550 of ~4,840, after «ومما يستدرك عليه»: «والاصطلاح: اتفاق طائفة مخصوصة على أمر مخصوص؛ قاله الخفاجي» |
| C58 | Most likely al-Shihāb al-Khafājī (d. 1069/1659), whose works al-Zabīdī lists among his sources | S (hedged) | Intro p. 9: «وشرح الشفاء، للشهاب الخفاجي. وشفاء الغليل، له أيضا». SlH itself cites «الشهاب… شرح الشفاء». Shamela author 711: «(٩٧٧ - ١٠٦٩ هـ = ١٥٦٩ - ١٦٥٩ م)» |
| C59 | Some ten centuries separate the two; the page does not say so | S | c. 598 to 1659 CE; no dates in the entry |
| C60 | The Tāj maps who said what; it cannot give a word's meaning in a particular verse or date a usage | S (interpretation) | Consistent with C42 and C54 |
| C61 | In the borrowed passage he disclaims having heard words face to face or travelled for them | S | Tāj p. 10: «لا أدعي فيه دعوى فأقول: شافهت، أو سمعت، أو شددت، أو رحلت». Lisān p. 8, same formula. Now correctly labelled as borrowed (round-2 C58 resolved) |
| C62 | Introducing his list of sources, he says he quoted the books directly, "not through intermediaries" | S | Tāj p. 5: «ونقلت بالمباشرة لا بالوسائط عنها… فأول هذه المصنفات…». This passage is outside the borrowed stretch (pp. 9–11) |
| C63 | Each item is as old as its source, not as old as the Tāj | S (interpretation) | Follows from C59 |
| C64 | onOurSite: 1,600 entries from hawramani, which names no source | S | `dicts`: 1,600 displayed. The hawramani page (HTTP 200) has only a blurb ("d. 1790 CE / 1205 AH… from Belgram"), with no edition named |
| C65 | Matches the Shamela Kuwait text word for word, gaps and misprints included | S | SlH (690) against shamela 7030/3326–3330 (vol. 6 pp. 547–551). Identical: «(سقط: لم يستكن لتهدد وتنمر», misprint «وسموا صلاخا», stray «من فلان.)», the Bishr verse, «قاله الخفاجي» |
| C66 | Roughly a third of entries (e.g. kfr, xlq) lack Qāmūs brackets | S | My SQL: 521/1,600 lack «(و)»; 488/1,600 lack both «(و)» and any bracket in the first 80 characters. kfr and xlq open unbracketed |
| C67 | Round brackets also enclose verse; curly brackets mostly Qur'an; stray { } ! | S | kfr (verse in parentheses); fsd {Qur'an}; Slw «( {الصَّلاَ», «إِنَّ! الصَّلاةَ» |
| C68 | (سقط: …) notes mark gaps | S | SlH; 56 displayed entries contain سقط |
| C69 | dyn is defective and runs into another root's text | S | Entry 1388: «(وَمَا لَا أَجَلَ لَهُ فَقَرْضٌ) التَّدَهْقُنُ…» |
| C70 | Qāmūs abbreviations ج, ة, ع, د, م [qamus-intro p. 40] | S | IslamWeb: after «[ص: 40]»: «مكتفيا بكتابة ع، د، ة، ج، م، عن قولي: موضع، وبلد، وقرية، والجمع، ومعروف». SlH: «(والصالحية: ة قرب الرهى)» |
| C71 | "Already mentioned" / "will come" refer to the book's own order, by the root's last letter [^haywood\|p. 88] | **NQ** | The claim is true. Slw: «وقد ذكرنا شيئا من ذلك في حرف الثاء»; Haywood p. 88 says the Qāmūs's "choice of the rhyme order was deliberate". But p. 88 never says the order runs by the last letter. That definition is on Haywood p. 69: "in alphabetical order according to the last radical. Thus the rhyme…". The citation supports only part |

**Totals: 71 claims. 70 supported, 1 needs qualification (C71), 0 unsupported.**

## Round-2 flags: status

- **C15 (motive borrowed from the Lisān)**: resolved. The motive clause is deleted. The p. 4 audience sentence, which is al-Zabīdī's own, remains (C15 here).
- **C17 (Bilgram)**: resolved. The Kuwait editor's doubt is stated, and his wording supports it exactly (C17).
- **C31 and B1 (borrowed modesty passage)**: resolved. The borrowing is announced before the quotation, the attribution line names Ibn Manẓūr, and a Lisān source is added.
  - I verified the Lisān source myself: Dār Ṣādir, 3rd ed. 1414, vol. 1 p. 8, paginated as the print. The follow-up sentence ("this book"; al-Azharī and Ibn Sīda versus "our shaykh") is exact.
- **C58 (fieldwork disclaimer)**: resolved. It is labelled "in the borrowed passage". The p. 5 "not through intermediaries" statement is al-Zabīdī's own and lies outside the copied stretch.
- **Brief issues from round 2**: all resolved.
  - B2: Lane's framing is fixed.
  - B3: the banquet and colophon material is merged.
  - B4: "The entry also gives" is in place.
  - B5: "a verse the entry attributes to Bishr" is in place.

## New claims introduced in revision r2: all checked

- **The 28 lines after the source list.** Kuwait editor text quoted in C30. The Tāj and the Lisān agree in every sentence from «فجاء بحمد الله تعالى هذا الشرح واضح المنهج» (p. 9) to «وسميته» (p. 11). Supported.
- **The quoted sentence lies inside the borrowed passage.** Supported (C32).
- **"This book" versus "this commentary"; al-Azharī and Ibn Sīda versus "our shaykh".** Supported (C33–C34).
- **The fieldwork disclaimer lies inside the borrowed passage.** Supported (C61).
- **P. 5, "not through intermediaries".** Supported (C62).
- **The Kuwait editor's doubt about India.** Supported (C17).
- **The lisan-intro source.** The URL opens (200), and the card details are as cited.

## Flagged items and fixes

### C71 (NQ): the Haywood locator supports only part of the claim

**Evidence:**
- Haywood p. 88 establishes that the *Qāmūs* uses the "rhyme order".
- The definition, arrangement by the last radical, is on p. 69 (OCR: "in alphabetical order according to the last radical. Thus the rhyme…").

**Fix:** change `[^haywood|p. 88]` to `[^haywood|pp. 69, 88]`. Also widen the source citation's page range from "pp. 88–90" to "pp. 69, 88–90".

## Brief issues

- **B1 (suggestion, length).** The validator counts **1,130 words** (lede + body), above the house range of 700–1,100. Round 2 counted 1,100. Trim about 30 words. Options:
  - Shorten "In our view, this is one of the *Tāj*'s most useful habits for a reader of the Qur'an: it shows…" to "In our view, this habit is among the *Tāj*'s most useful: it shows…".
  - Cut "One entry cannot confirm Lane's proportions, but it shows what they mean in practice." to "One entry cannot confirm Lane's proportions."
  - Drop "from lexicons such as Ibn Manẓūr's *Lisān al-ʿArab* to works on history and medicine" down to "from lexicons to works on history and medicine". The Lisān is named again two paragraphs later.
- **B2 (suggestion, clarity).** "Ibn Manẓūr had written 'this book', and credited al-Azharī and Ibn Sīda where al-Zabīdī credits 'our shaykh'" does not say what is credited. Suggest: "…and credited al-Azharī and Ibn Sīda with naming their authorities, where al-Zabīdī gives that credit to 'our shaykh'". Lisān p. 8 has «فإنهما عيّنا في كتابيهما عمن رويا»; Tāj p. 10 has «فإنه عني في شرحه عمن روى».
- **Checks that passed.** No padding, rankings or generic praise. Opinion is labelled ("In our view"). Translations are labelled, both in the in-text note and in the quote attribution. Every root mention is linked, and each link leads to a displayed entry that supports the statement. There is no forced "original root meaning" narrative; the *ṣalāt* section reports the debate without resolving it. The borrowed-introduction passage now teaches the "whose voice?" point openly.

## Source URLs

| id | URL | Status |
|---|---|---|
| zabidi-intro | https://shamela.ws/book/7030 | 200. Kuwait ed. card; pp. 2–11 read |
| jabarti | https://shamela.ws/book/11998/802 | 200. «ج2 - ص104… سنة خمس ومائتين وألف»; Dār al-Jīl |
| kuwait-ed | https://archive.org/details/ZUB1965AR | 200. Vol. 1 OCR, «كتبه: عبد الستار احمد فراج» |
| lisan-intro | https://shamela.ws/book/1687/8 | 200. «ج1 - ص8… مقدمة المؤلف»; Dār Ṣādir, 3rd ed., 1414 AH |
| lane-preface | https://archive.org/details/arabicenglishlex0001edwa/page/n24/mode/1up | 200. 1863 Williams and Norgate; n24 = p. xix |
| haywood | https://archive.org/details/in.gov.ignca.12555 | 200. Haywood 1960; pp. 69, 88–90 used |
| baalbaki | AUB bitstream | 200. PDF, JAS 6 (2019) 185–208; p. 203 |
| hawramani | category page | 200 |
| shamela-ed | https://shamela.ws/book/7030/3326 | 200. Vol. 6 p. 547, where [صلح] begins; runs to p. 551 (/3330) |
| bishr | https://arab-ency.com.sy/details/4285 | 200. Iḥsān al-Naṣṣ; vol. 5, 2002, p. 119 |
| khafaji | https://shamela.ws/author/711 | 200 |
| qamus-intro | IslamWeb bk_no=123 ID=2 | 200. Marker [ص: 40] precedes the abbreviation sentence |

All listed sources are cited in the text and say what they are cited for. There are no unused or unusable sources.

## Validator

`node scripts/validate-dictionary-guides.mjs taj-al-arus` gives **ok**:
- 11 root links (10 distinct pairs)
- 4 excerpts
- **1,130 words** (see B1)
- example roots SlH, rHm, fsd, Slw, kfr, xlq, dyn
- 1/1 guides pass

## Site-data issues

1. **Stored death year 1790.** Al-Jabartī (vol. 2 p. 112, in the 1205 section) puts his death in Shaʿbān 1205 ≈ April 1791, and Lane (Preface p. xviii) gives 1791. The year 1790 is the Gregorian year in which 1205 AH began (as in hawramani and Baalbaki, "1205/1790"). Suggest storing 1791. Panel order is unaffected.
2. **Title form.** The stored slug and the hawramani title read "fī Jawāhir al-Qāmūs"; the author's own title (intro p. 11) is "min Jawāhir al-Qāmūs".
3. **Stored-text defects.**
   - dyn (1388) carries دهقن text after its first definition.
   - 56 entries contain (سقط: …) gap notes.
   - About a third of entries (488–521 of 1,600 by heuristic) lack the round brackets that separate the Qāmūs from the commentary.
4. **Source-site blurb (not displayed by us).** Hawramani's blurb states as fact that he was "from Belgram in West Bengal". Bilgram's Indian origin is disputed by the Kuwait editor, and the town is not in West Bengal. Do not copy that blurb into any site text.
