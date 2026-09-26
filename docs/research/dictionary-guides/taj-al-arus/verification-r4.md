# Tāj al-ʿArūs guide: verification, round 4

**Page checked:** `roots/frontend/src/content/dictionary-guides/guides/taj-al-arus.ts`, the text after the final revision. The only change since round 3 is the Haywood locator.

**Date:** 2026-09-26

**Independence:** I did not open research-notes.md or any revision-*.md file. I read verification-r3.md only to see what round 3 flagged. For this round I downloaded every source again and re-read it myself, and I re-read every stored entry through `_dict_guide_tool.py` and read-only SQL.

## Sources opened in this round

- **Tāj, author's introduction (al-Maktaba al-Shāmila, book 7030, pp. 1–12).** Page titles read «ج1 - ص2 … ص11 - كتاب تاج العروس من جواهر القاموس». The book card reads «وزارة الإرشاد والأنباء في الكويت … عدد الأجزاء: ٤٠ أعوام النشر: (١٣٨٥ - ١٤٢٢ هـ) = (١٩٦٥ - ٢٠٠١ م) … [ترقيم الكتاب موافق للمطبوع]».
- **Ibn Manẓūr, *Lisān*, introduction (Shamela 1687/7–8).** The book card reads «دار صادر - بيروت، الطبعة: الثالثة - ١٤١٤ هـ».
- **al-Jabartī, *ʿAjāʾib al-Āthār* (Shamela 11998/801, 802, 810, 811 = vol. 2, pp. 103, 104, 112, 113, in the section «سنة خمس ومائتين وألف»).** The card reads «دار الجيل بيروت».
- **Kuwait edition, vol. 1 (1965).** The archive.org OCR "1 - تاج العروس_djvu.txt" from ZUB1965AR, signed «كتبه : عبد الستار احمد فراج».
- **Lane, *Lexicon*, Book I (1863).** The full OCR and page_numbers.json from archive.org, arabicenglishlex0001edwa. Metadata: "williams and norgate", 1863.
- **Haywood, *Arabic Lexicography* (1960).** The OCR 12555_djvu.txt from archive.org, in.gov.ignca.12555.
- **Baalbaki, JAS 6 (2019).** The PDF from the AUB bitstream, read with pdftotext. Page 19 of the PDF is journal p. 203.
- **arab-ency.com.sy/details/4285; shamela.ws/author/711; IslamWeb *Qāmūs* introduction (bk_no=123, ID=2); the hawramani category page; Shamela 7030/3326–3330 (vol. 6, pp. 547–551).**
- **Stored entries.**
  - Tāj: fsd 2385, rHm, Slw, SlH, kfr, xlq, dyn
  - Qāmūs: fsd
  - Lisān: fsd
  - Lane: nhy 2264
  - Read-only SQL over the 1,600 displayed Tāj entries.

## Claims table

S = supported. NQ = needs qualification. U = unsupported.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | titleAr تاج العروس من جواهر القاموس | S | Tāj intro vol. 1 p. 11: «وسميته. (تاج العروس من جواهر القاموس)» |
| C2 | titleGloss "The Bride's Crown, from the Jewels of al-Qāmūs" | S | A fair rendering of C1 |
| C3 | author / authorAr: Murtaḍā al-Zabīdī | S | Jabartī vol. 2 p. 104: «الشهير بمرتضى الحسيني الزبيدي» |
| C4 | authorFull: Abū l-Fayḍ Muḥammad ibn Muḥammad al-Ḥusaynī al-Zabīdī, known as Murtaḍā | S | Jabartī p. 104 name chain (Shamela misprints «أبو القبض»). Kuwait editor: «وكناه … أبو الأنوار بن وفا بأبي الفيض» |
| C5 | period: d. 1205 AH / 1791 CE | S | Jabartī p. 112 (section 1205): plague in Shaʿbān, «وتوفي يوم الأحد». Lane p. xviii: "died A.D. 1791 (in the year of the Flight 1205)" |
| C6 | kind: commentary on al-Qāmūs | S | Intro p. 4: «في وضع شرح عليه، ممزوج العبارة» |
| C7 | Summary: an 18th-century commentary wrapping the Qāmūs in quotations, Qur'anic and poetic evidence, disputes, corrections, additions | S | Lane p. xviii: "interwoven commentary on the Kámoos … corrections of mistakes … examples in prose and verse; and a very large collection of additional words". Also entries fsd, Slw, SlH |
| C8 | Summary: useful for finding who recorded a meaning, once its voices are told apart | S (interpretation) | fsd, Slw. Kuwait editor: «ينسب كثيرا من التفسير اللغوي إلى قائليه» |
| C9 | Lede: working in Cairo in the 1760s and 1770s | S | Kuwait editor: began about seven years after arriving (1167). Final colophon «وآخر الكتاب في رجب سنة 1188». Author's letter: «مكثت مشتغلا به أربعة عشر عاما وشهرين». Lane p. xviii: "commenced, in Cairo" |
| C10 | Lede: a phrase-by-phrase commentary that names sources, adds verse or poem, reports disputes, corrects slips, supplies missing words | S | fsd, Slw and kfr («قلت: لا غلط»). Elq: «وكم من إحالات للمصنف غير صحيحة». Kuwait editor: «يستدرك ما نقص» |
| C11 | Lede: reading well means tracking the voices of the Qāmūs, al-Zabīdī and the scholars he quotes | S | Kuwait editor: «لو أزيلت الحدود … لكان من الصعب معرفة ما لهذا أو ما لذاك» |
| C12 | By al-Zabīdī's account the Qāmūs was prized for concision and so attracted commentators | S | Intro p. 2: «أوجز لفظه وأشبع معناه … ولما كان إبرازه في غاية الإيجاز … تصدى لكشف غوامضه ودقائقه رجال» |
| C13 | Among the fullest was his teacher al-Fāsī's; "my mainstay in this discipline"; translations are the guide's own | S | Intro p. 3: «ومن أجمع ما كتب عليه … شرح شيخنا … محمد بن الطيب … الفاسي … وهو عمدتي في هذا الفن». Lane p. xix: "his preceptor, Mohammad Ibn-Et-Teiyib El-Fasee" |
| C14 | His plan: *mamzūj al-ʿibāra*, noting where copies differ, quoting sources explicitly, gathering verses as evidence | S | Intro p. 4: «ممزوج العبارة … واف ببيان ما اختلف من نسخه». Intro p. 5: «والإنباه عن مضاربه ومآخذه بصريح النقول، والتقاط أبيات الشواهد له» |
| C15 | Wrote for scholars, especially teachers of *gharīb al-ḥadīth* and of the major works on Arabic | S | Intro p. 4: «فاقة الأفاضل … ولا سيما من انتدب منهم لتدريس علم غريب الحديث، وإقراء الكتب الكبار من قوانين العربية» |
| C16 | Born 1145 AH (1732–33) | S | Jabartī p. 104: «ولد سنة خمس واربعين ومائة وألف كما سمعته من لفظه ورايته بخطه». The Kuwait editor gives the same year |
| C17 | Later sources say he was born in Bilgram, India; the Kuwait editor finds nothing clear in his own writings placing him in India | S | Kuwait editor: *Abjad al-ʿUlūm*, *Nashr al-ʿArf*, *Fihris al-Fahāris* and the 2nd printing «ذكروا أنه ولد ببلد هندي هو بلجرام»; «فنحن لا نجد نصا واضحا في كلامه يدل على أنه من الهند» |
| C18 | Studied in the Hijaz and Yemen | S | Jabartī p. 104: «وحج مرارا … بمكة … ونزل بالطائف بعد ذهابه إلى اليمن». Kuwait editor: his Qāmūs isnād taken in Zabīd and in Medina |
| C19 | Reached Cairo in 1167 AH (1753) | S | Jabartī p. 104: «ثم ورد إلى مصر في تاسع سفر سنة سبع وستين ومائة وألف». Lane p. xviii: "came to Cairo A.D. 1753" |
| C20 | Died there in Shaʿbān 1205, spring 1791 | S | Jabartī p. 112 (plague in Shaʿbān; died the following Sunday); p. 113: buried at al-Sayyida Ruqayya. 1 Shaʿbān 1205 ≈ early April 1791 |
| C21 | In Cairo's libraries he found many of the 100+ works his introduction lists, from lexicons such as the Lisān to works on history and medicine | S | Intro: Lisān p. 5; *Taʾrīkh Dimashq* p. 8; «والتذكرة في الطب، للحكيم داود الأنطاكي» p. 9. Named *khizāna*s: Azbak, Ṣarghatmish, al-Muʾayyad, Qāytbāy, al-Maḥmūdiyya. I count about 93 list items on pp. 5–9, several naming 2–4 works each. Lane p. xviii: "more than a hundred are enumerated". Kuwait editor: «ظفر في مصر بأمهات الكتب … وجده بالقاهرة» |
| C22 | The Kuwait editor, from dates recorded in the text, puts completion in Rajab 1188 (1774) | S (attributed) | Kuwait editor's list of end-of-letter colophons: «وآخر الكتاب في رجب سنة 1188». See brief issue B3: Lane p. xviii gives 1767–68, from al-Jabartī |
| C23 | Autograph: a line over the Qāmūs words; students' copies in red; printed editions in round brackets; otherwise hard to tell whose words are whose | S | Kuwait editor, «طريقة تاج العروس»: «كان يضع كلمة القاموس وفوقها خط … جعلوا كلمة القاموس باللون الأحمر … بين قوسين». Haywood p. 89: "put the contents of the 'Qamus' in brackets" |
| C24 | On our site bracketed words are usually al-Fīrūzābādī's | S | Tāj fsd (2385) against Qāmūs fsd: every bracketed phrase is in the Qāmūs text |
| C25 | *al-muṣannif* on its own = al-Fīrūzābādī, in al-Zabīdī's voice | S | Intro p. 7: «وبصائر ذوي التمييز … والمثلثات، الأربعة للمصنف» (all four are al-Fīrūzābādī's works). kfr: «والعجب من المصنف كيف لم ينبه» |
| C26 | *shaykhunā* = al-Fāsī | S | Intro p. 3: «شرح شيخنا … الفاسي»; p. 4: «وقد تكفل شيخنا بالرد عليه». Inside al-Fāsī's own quoted text «شيخنا» can mean his teacher (rHm: «شيخنا سيدي المهدي الفاسي»); the guide's "in al-Zabīdī's own voice" covers this |
| C27 | *qultu* introduces his own view | S | rHm; kfr: «قاله شيخنا. قلت: لا غلط» |
| C28 | *intahā* closes a quotation, as Lane notes under nhy | S | Lane nhy (2264): "اِنْتَهَى It is ended: a word put to mark the end of a quotation" |
| C29 | *wa-mimmā yustadrak ʿalayh* opens the end-of-entry supplement (SlH) | S | SlH: «ومما يستدرك عليه: قوم صلوح…». 1,404 of the 1,600 displayed entries contain the phrase. Kuwait editor: «وبعد انتهاء المادة … يستدرك ما نقص» |
| C30 | After the source list come 28 lines copied almost verbatim, without acknowledgement, from Ibn Manẓūr's introduction | S | Kuwait editor: «نقل ثمانية وعشرين سطرا من مقدمة ابن منظور … دون أن يشير إلى ذلك … انظر هذا النص بعد تعداده للكتب التي رجع إليها». My comparison: Tāj p. 9 «فجاء بحمد الله تعالى هذا الشرح واضح المنهج» to p. 11 «وسميته» parallels Lisān p. 8 sentence by sentence |
| C31 | In them he praises the work, disclaims merit, and makes the original authors answerable | S | Tāj pp. 9–10: «واضح المنهج … بديع الإتقان … وليس لي في هذا الشرح فضيلة … فعهدته على المصنف الأول» |
| C32 | Block quotation, its translation and attribution line | S | Verbatim on Tāj p. 10 («…أمت بها، ولا وسيلة أتمسك بها، سوى أنني جمعت فيه ما تفرق في تلك الكتب»); the elision is marked. The translation is accurate and labelled |
| C33 | Ibn Manẓūr had written "this book" | S | Lisān p. 8: «وليس لي في هذا الكتاب فضيلة أمت بها» |
| C34 | Ibn Manẓūr credited al-Azharī and Ibn Sīda where al-Zabīdī credits "our shaykh" | S | Lisān p. 8: «لم يترك فيها الأزهري وابن سيده لقائل مقالا … فإنهما عينا في كتابيهما عمن رويا». Tāj p. 10: «لم يترك فيها شيخنا لقائل مقالا … فإنه عني في شرحه عمن روى». See B2 (clarity) |
| C35 | The modest self-portrait is borrowed | S | Follows from C30–C34 |
| C36 | In practice he weighs and corrects, even his teacher | S | rHm: «قلت: وفي نقله عن العباب نظر». kfr: «قلت: لا غلط، والصواب ما ذهب إليه الجوهري» (against al-Fāsī) |
| C37 | In rHm al-Fāsī cites al-Ṣaghānī's *al-ʿUbāb* against a usage; three markers appear together | S | rHm: «ونقل شيخنا عن العباب للصاغاني أن ترحمت عليه لحن … انتهى سياق شيخنا. قلت:». Intro p. 6: «والعباب والتكملة … للرضي الصاغاني» |
| C38 | rHm excerpt and its translation | S | The stored text matches (validator ok). The translation is accurate; «مصنفه» = al-ʿUbāb's author |
| C39 | Qāmūs fsd: bare equivalents; excerpt and translation | S | Qāmūs fsd: «والفَسادُ: أخْذُ المالِ ظُلْماً، والجَدْبُ.» |
| C40 | In the Tāj the same words are in round brackets | S | Tāj fsd: «(والفَسَادُ: أَخْذُ المالِ ظُلْماً) … (الجَدْبُ)» |
| C41 | Tāj fsd excerpt and its translation | S | Matches entry 2385; the translation is accurate |
| C42 | Two Qāmūs senses tied to named authorities' readings of Q 28:83 and Q 30:41 | S | «هكاذا فسر مسلم البطين قوله تعالى: {للذين لا يريدون علوا…}»; «وهاذا قول الزجاج» |
| C43 | "In our view … most useful habits …" | S (labelled opinion) | Framed as the guide's view; the habit is shown in C42 |
| C44 | The entry also gives grammar, poetry, a report, a hadith, and al-Fāsī's note (*baṭala* / *taghayyara*; most read Q 21:22 the first way) | S | Tāj fsd: Sībawayh; «إن الشباب والفراغ والجده»; «وفي الخبر أن عبد الملك بن مروان»; the *ghīla* hadith; «قال شيخنا: وقد اختلفت عباراتهم … بطل واضمحل … تغير، ومن الأول عند الأكثر: {لو كان فيهما آلهة…}» |
| C45 | Much of this is in the Lisān, incl. Q 30:41 credited to "al-Zajjājī"; Muslim al-Baṭīn and al-Fāsī's note are not | S | Lisān fsd: «هذا قول الزجاجي», plus Sībawayh, the verse, the ʿAbd al-Malik *khabar* and the *ghīla* hadith. No «البطين», no «أخذ المال», no «شيخنا» |
| C46 | Lane called the Tāj "the medium through which I have drawn most of the contents of my lexicon" | S | Lane 1863, OCR line 1139, between the "PREFACE. xix" header and the "xx" header, so p. xix. Verbatim |
| C47 | Lane found its quotations faithfully transcribed | S | p. xx: "in every instance I found that they had been faithfully transcribed" |
| C48 | In most articles he compared, 3/4 to 9/10 of the additions were verbatim in the Lisān; he faulted al-Zabīdī for not saying so | S | p. xx: "in most of the articles … from three-fourths to about nine-tenths of the additions … existed verbatim in the Lisán … want of candour … by not stating" |
| C49 | Baalbaki counts the Lisān among his major sources | S | Baalbaki p. 203: "al-Zabīdī (d. 1205/1790), in spite of utilizing the Lisān as one of his major sources in Tāj al-ʿarūs…" |
| C50 | One entry cannot confirm Lane's proportions but shows what they mean | S (interpretation) | Hedged |
| C51 | Slw: the bracketed Qāmūs gives five senses of *ṣalāt* | S | (الدعاء), (الرحمة), (الاستغفار), (حسن الثناء من الله … على رسوله …), (عبادة فيها ركوع وسجود) |
| C52 | Supplication called "the root of its meanings", with Q 9:103 and al-Aʿshā's wine-jar verse | S | «(الدعاء)، وهو أصل معانيها … {وصل عليهم} … قول الأعشى: وصلى على دنها وارتسم أي دعا لها أن لا تحمض ولا تفسد» |
| C53 | Slw excerpt and its translation | S | Matches the stored text. The translation is accurate, and «وفي الكل نظر، انتهى» is correctly kept inside al-Fāsī's quotation |
| C54 | Further authorities from Ibn al-Athīr to al-Rāzī on new coinage vs old word extended; the entry does not decide | S | Ibn al-Athīr; *al-Miṣbāḥ* (*naql* vs *majāz*); al-Rāghib; al-Munāwī quoting al-Rāzī (Muʿtazila «الأسماء الشرعية» vs «المجازات المشهورة»). The entry then moves to *al-Ṣiḥāḥ* with no verdict of al-Zabīdī's own |
| C55 | SlH: *ṣilāḥ* "reconciliation" in a verse the entry attributes to Bishr ibn Abī Khāzim | S | «(صالحه مصالحة، وصلاحا)، بالكسر … قال بشر بن أبي خازم: يسومون الصلاح بذات كهف…» |
| C56 | Bishr: pre-Islamic poet of the late 6th century | S | arab-ency 4285 (Iḥsān al-Naṣṣ, vol. 5, 2002, p. 119): «(… ـ نحو 598م) … من فحول شعراء الجاهلية … عاش في أواخر القرن السادس الميلادي» |
| C57 | Near the end, the supplement defines *iṣṭilāḥ*, citing al-Khafājī | S | SlH, character ~3,486 of 3,703, after «ومما يستدرك عليه» (~3,068): «والاصطلاح: اتفاق طائفة مخصوصة على أمر مخصوص؛ قاله الخفاجي» |
| C58 | Most likely al-Shihāb al-Khafājī (d. 1069/1659), whose works he lists | S (hedged) | Intro p. 9: «وشرح الشفاء، للشهاب الخفاجي. وشفاء الغليل، له أيضا». SlH cites «الشهاب … شرح الشفاء». Shamela author 711: «الشهاب الخفاجي (٩٧٧ - ١٠٦٩ هـ = ١٥٦٩ - ١٦٥٩ م)» |
| C59 | Some ten centuries separate the two; the page does not say so | S | c. 598 vs 1659 CE; the entry gives no dates |
| C60 | The Tāj maps who said what; it cannot give a word's meaning in a verse or date a usage | S (interpretation) | Consistent with C42 and C54 |
| C61 | In the borrowed passage he disclaims hearing words face to face or travelling | S | Tāj p. 10: «لا أدعي فيه دعوى فأقول: شافهت، أو سمعت، أو شددت، أو رحلت». Lisān p. 8 has the same formula |
| C62 | Introducing his source list, he says he quoted directly, "not through intermediaries" | S | Tāj p. 5: «ونقلت بالمباشرة لا بالوسائط عنها». This lies outside the borrowed stretch (pp. 9–11) |
| C63 | Each item is as old as its source, not as old as the Tāj | S (interpretation) | Follows from C59 |
| C64 | onOurSite: 1,600 entries from hawramani, which names no source | S | `dicts`: 1,600 displayed. The hawramani page (HTTP 200) has only a blurb; no edition or source is named (grep for edition/Kuwait/Hidaya/طبعة found nothing) |
| C65 | Matches the Shamela Kuwait text word for word, gaps and misprints included | S | Stored SlH against Shamela 7030/3326–3330 after normalising: the only difference is the next root (صلبح) that follows on the Shamela page. «(سقط: …» and the misprint «وسموا صلاخا» are present in both |
| C66 | About a third of entries (e.g. kfr, xlq) lack Qāmūs brackets | S | SQL: 521/1,600 lack «(و)»; 477 lack both «(و)» and any bracket in the first 80 characters. kfr and xlq have no «(و)» |
| C67 | Round brackets also enclose verse; curly brackets mostly Qur'an; stray { } ! marks | S | kfr: verses in «( … )». In fsd, SlH and rHm every {…} is a Qur'an quotation. Slw has 64 stray braces and «إن! الصلاة» |
| C68 | (سقط: …) notes mark gaps | S | SlH «(سقط: لم يستكن…». 26 displayed entries contain «(سقط». The site's English renders it "[text defective here]" |
| C69 | dyn is defective and runs into another root's text | S | dyn: «(وما لا أجل له فقرض) التدهقن: التكيس. ودهقن الطعام…» |
| C70 | Qāmūs abbreviations ج ة ع د م [qamus-intro p. 40] | S | IslamWeb: the sentence «مكتفيا بكتابة ع، د، ة، ج، م، عن قولي: موضع، وبلد، وقرية، والجمع، ومعروف» lies between the markers [ص: 40] and [ص: 41] |
| C71 | "Already mentioned" / "will come" refer to the book's order by the root's last letter [^haywood\|pp. 69, 88] | S | Haywood p. 69: "in alphabetical order according to the last radical. Thus, the rhyme order…". p. 88: the Qāmūs's "choice of the rhyme order was deliberate". p. 68 defines it most directly: "roots were listed according to their final radicals". Stored cross-references agree: xrj (ج) «تقدم في حرف الباء»; dwr (ر) «سيأتي في حرف العين»; dhq (ق) «سيأتي في باب النون»; Slw (و) «ذكرنا … في حرف الثاء» |

**Totals: 71 claims. 71 supported, 0 need qualification, 0 unsupported.**

## Round-3 flag: status

- **C71 (Haywood locator): resolved.** The locator now reads `pp. 69, 88`, and the source citation reads "pp. 69, 88–90". I checked both pages in the OCR myself.
- **Optional improvement:** Haywood p. 68 (the opening of ch. 6) is the clearest statement of the definition, so `pp. 68–69, 88` would be slightly better. This is not required.
- **New claims in the final revision:** none. The sentence wording is unchanged.

## Flagged items

None.

## Brief issues

- **B1 (suggestion, length).** The validator counts **1,130 words** (lede + body), 30 over the 700–1,100 range. The depth is supported by the sources and there is no padding, but a light trim would bring the page into range. Candidates:
  - "In our view, this is one of the *Tāj*'s most useful habits for a reader of the Qur'an:" → "In our view, this habit is among the *Tāj*'s most useful:"
  - Cut ", but it shows what they mean in practice".
  - "from lexicons such as Ibn Manẓūr's *Lisān al-ʿArab* to works on history and medicine" → "from lexicons to works on history and medicine". The *Lisān* is named again two paragraphs later.
- **B2 (suggestion, clarity).** "credited al-Azharī and Ibn Sīda where al-Zabīdī credits 'our shaykh'" does not say what is credited. Suggest "credited al-Azharī and Ibn Sīda with naming their authorities, where al-Zabīdī gives that credit to 'our shaykh'". Lisān p. 8 has «فإنهما عيّنا في كتابيهما عمن رويا»; Tāj p. 10 has «فإنه عني في شرحه عمن روى».
- **B3 (suggestion, dating disagreement).** The completion date is correctly attributed to the Kuwait editor, but the page does not say that another date circulates.
  - Lane (Preface p. xviii), following al-Jabartī, has the Tāj "finished … A.D. 1767 or 1768". That is the 1181 AH banquet.
  - The Kuwait editor argues the banquet marked the first part, and relies on the colophons ending in Rajab 1188.
  - If words are available after B1, a half-clause would acknowledge this, e.g. "…puts the *Tāj*'s completion in Rajab 1188 AH (1774), later than the 1181 banquet al-Jabartī describes". This is optional.
- **Checks that passed.**
  - No generic praise or ranking.
  - Opinion is labelled.
  - Translations are labelled, both in the text and in the quote attribution.
  - Every root mention is a link to a displayed entry that supports what is said about it.
  - There is no forced "original root meaning" narrative.
  - The borrowed introduction is disclosed.
  - The page does not promise material the site lacks. It warns about unbracketed entries, gaps and the defective dyn entry.

## Source URLs

| id | URL | Status |
|---|---|---|
| zabidi-intro | https://shamela.ws/book/7030 | 200. Kuwait ed. card; pp. 2–11 read |
| jabarti | https://shamela.ws/book/11998/802 | 200. «ج2 - ص104 … سنة خمس ومائتين وألف»; obituary begins at the end of p. 103 |
| kuwait-ed | https://archive.org/details/ZUB1965AR | 200. Vol. 1 OCR, signed by Farrāj; metadata date 1965 |
| lisan-intro | https://shamela.ws/book/1687/8 | 200. «ج1 - ص8 … مقدمة المؤلف»; Dār Ṣādir, 3rd ed., 1414 |
| lane-preface | https://archive.org/details/arabicenglishlex0001edwa/page/n24/mode/1up | 200. 1863 Williams and Norgate; leaf 31 = XXV, so n24 = p. xix |
| haywood | https://archive.org/details/in.gov.ignca.12555 | 200. Haywood 1960; pp. 69, 88, 89 checked |
| baalbaki | AUB bitstream | 200. PDF, JAS 6 (2019) 185–208; the passage is on p. 203 |
| hawramani | category page | 200 |
| shamela-ed | https://shamela.ws/book/7030/3326 | 200. Vol. 6 p. 547; the entry صلح runs to p. 551 |
| bishr | https://arab-ency.com.sy/details/4285 | 200. Iḥsān al-Naṣṣ; vol. 5, 2002, p. 119 |
| khafaji | https://shamela.ws/author/711 | 200. «(٩٧٧ - ١٠٦٩ هـ = ١٥٦٩ - ١٦٥٩ م)» |
| qamus-intro | IslamWeb bk_no=123 ID=2 | 200. The abbreviation sentence is inside [ص: 40] |

Every listed source is cited in the text and supports what it is cited for.

## Validator

`node scripts/validate-dictionary-guides.mjs taj-al-arus` gives **ok**:
- 11 root links (10 distinct pairs)
- 4 excerpts
- **1,130 words** (see B1)
- example roots SlH, rHm, fsd, Slw, kfr, xlq, dyn
- 1/1 guides pass

## Site-data issues

1. **Stored death year 1790.**
   - He died in Shaʿbān 1205. Al-Jabartī places the death in the 1205 section (vol. 2 p. 112), and Shaʿbān 1205 ≈ April 1791. Lane (p. xviii) gives 1791.
   - The year 1790 is the CE year in which 1205 AH began; hawramani and Baalbaki write "1205/1790".
   - Suggest storing 1791. Panel order is unaffected.
2. **Title form.** The stored slug and the hawramani title use "fī Jawāhir al-Qāmūs". The author's own title (intro p. 11) is "min Jawāhir al-Qāmūs".
3. **Stored-text defects.**
   - dyn carries دهقن text after its first definition.
   - 26 displayed entries contain «(سقط: …» gap notes.
   - About 30% of entries (477–521 of 1,600, by heuristic) lack the brackets that separate the Qāmūs from the commentary.
4. **Hawramani blurb (not displayed by us).** It states that al-Zabīdī was "from Belgram in West Bengal". His Indian birth is doubted by the Kuwait editor, and Bilgram is not in West Bengal. Do not copy the blurb into site text.
