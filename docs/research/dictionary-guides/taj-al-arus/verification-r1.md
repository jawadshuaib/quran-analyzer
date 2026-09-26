# Tāj al-ʿArūs guide: verification, round 1

Checked: `roots/frontend/src/content/dictionary-guides/guides/taj-al-arus.ts`. This is an independent check. I did not open research-notes.md or any revision file.
Date: 2026-09-26.

## Sources opened for this check

- **Tāj, author's introduction.** Kuwait edition as paginated in al-Maktaba al-Shāmila: https://shamela.ws/book/7030/1 … /16, vol. 1, pp. 1–12. The book card at https://shamela.ws/book/7030 says: Kuwait, 40 vols, 1385–1422 AH / 1965–2001; "ترقيم الكتاب موافق للمطبوع".
- **al-Jabartī, *ʿAjāʾib al-Āthār*.** Dār al-Jīl, Beirut, per the Shamela card: https://shamela.ws/book/11998/801 … /811, vol. 2, pp. 103–113. The pages fall under the heading "سنة خمس ومائتين وألف".
- **Kuwait edition, vol. 1, editor's front matter.** OCR text at https://archive.org/download/ZUB1965AR/ (file "1 - تاج العروس_djvu.txt"). The archive metadata credits vol. 1 (1965) to ʿAbd al-Sattār Farrāj.
- **Lane, Lexicon, Book I (1863), Preface.** OCR at https://archive.org/details/anarabicenglish03lanegoog, pp. vi, xviii–xx, xxii.
- **Haywood, *Arabic Lexicography* (1960).** OCR at https://archive.org/details/in.gov.ignca.12555, pp. 88–90.
- **Baalbaki, "The Notion of gharīb in Arabic Lexica," JAS 6 (2019).** The AUB PDF at the cited URL, p. 203.
- **al-Qāmūs, author's introduction.** IslamWeb, the cited URL, which carries a page marker "[ص: 40]".
- **hawramani category page and Shamela author page 711.** Both opened.
- **Stored entries**, via `_dict_guide_tool.py entry`:
  - Tāj: fsd (2385), rHm (13), Slw (1396), SlH (690), kfr, xlq, dyn
  - Qāmūs: fsd (2390)
  - Lisān: fsd (2384)
  - Lane: nhy (2264)
- **SQL count over all 1,600 displayed Tāj entries**, to test the brackets claim.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Title; Arabic title تاج العروس من جواهر القاموس | S | Intro vol. 1 p. 11: «وسميته (تاج العروس من جواهر القاموس)» |
| C2 | titleGloss "The Bride's Crown, from the Jewels of al-Qāmūs" | S | A fair rendering of the title in C1 |
| C3 | author / authorAr Murtaḍā al-Zabīdī | S | Jabartī vol. 2 p. 104: «الشهير بمرتضى الحسيني الزبيدي» |
| C4 | authorFull: Abū l-Fayḍ Muḥammad ibn Muḥammad al-Ḥusaynī al-Zabīdī, known as Murtaḍā | S | Jabartī p. 104 gives the name chain; p. 105 says he was given the kunya أبو الفيض |
| C5 | period d. 1205 AH / 1791 CE | S | Jabartī p. 112: plague, Shaʿbān, in the 1205 section (Shaʿbān 1205 ≈ April 1791). Lane p. xviii: "died A.D. 1791 (in the year of the Flight 1205)" |
| C6 | kind: commentary on al-Qāmūs | S | Intro p. 4 «شرحٍ عليه ممزوج العبارة»; Lane p. xviii |
| C7 | Summary: commentary wrapping the Qāmūs in quotations, Qur'anic and poetic evidence, disputes, corrections, additions | S | Lane p. xviii ("corrections of mistakes…, examples in prose and verse; and a very large collection of additional words"); intro pp. 4–5; the entries |
| C8 | Lede: working in Cairo in the 1760s–1770s | S | Lane p. xviii ("commenced, in Cairo, soon after the middle of the last century"); Kuwait editor: finished Rajab 1188 / 1774 |
| C9 | Lede: running commentary that names sources, adds verses, reports disputes, corrects, supplies missing words | S | Entries fsd, rHm, SlH, kfr; Kuwait editor, "طريقة تاج العروس" |
| C10 | The Qāmūs was prized for concision and so attracted commentators | S | Intro pp. 2–3: «أوجز لفظه وأشبع معناه… ولما كان إبرازه في غاية الإيجاز… تصدى لكشف غوامضه… رجال» |
| C11 | Al-Fāsī's commentary was among the fullest; al-Zabīdī calls him "my mainstay in this discipline" | S | Intro p. 3: «ومن أجمع ما كتب عليه… شرح شيخنا… محمد بن الطيب… الفاسي… وهو عمدتي في هذا الفن» |
| C12 | His plan: *mamzūj al-ʿibāra*, noting where copies differ, explicit quotation of sources, collecting verses as evidence | S | Intro p. 4 «ممزوج العبارة… واف ببيان ما اختلف من نسخه»; p. 5 «بصريح النقول، والتقاط أبيات الشواهد» |
| C13 | He wrote for scholars, especially teachers of *gharīb al-ḥadīth* and the major works on Arabic | S | Intro p. 4: «فاقة الأفاضل… ولا سيما من انتدب منهم لتدريس علم غريب الحديث، وإقراء الكتب الكبار من قوانين العربية» |
| C14 | His motive: preserving the language on which the rulings of Qur'an and Sunna depend | S | Intro p. 11: «لم أقصد سوى حفظ هذه اللغة الشريفة إذ عليها مدار أحكام الكتاب العزيز والسنة النبوية» |
| C15 | Born 1145 AH (1732–33) | S | Jabartī p. 104: «ولد سنة خمس وأربعين ومائة وألف» |
| C16 | Bilgram in India per later sources; al-Jabartī does not name the town | S | Kuwait editor's introduction, which cites أبجد العلوم, نشر العرف, فهرس الفهارس and the 2nd printing. Jabartī p. 104 has only «نشأ ببلاده» |
| C17 | Travelled for study in the Hijaz and Yemen | S | Jabartī p. 104 (حج مرارا… الطائف… بعد ذهابه إلى اليمن) |
| C18 | Reached Cairo in 1167 AH (1753) | S | Jabartī p. 104: «ورد إلى مصر في تاسع صفر سنة سبع وستين ومائة وألف» (≈ Dec. 1753) |
| C19 | Died of plague, Shaʿbān 1205, spring 1791 | S | Jabartī p. 112: «وأصيب بالطاعون في شهر شعبان»; p. 113 |
| C20 | Found in Cairo's libraries many of the 100+ works his introduction lists (Lisān; hadith, history, genealogy, botany, medicine) | S | Intro pp. 5–9 lists the works: the Lisān on p. 5; النبات لأبي حنيفة and تذكرة داود الأنطاكي on p. 9. It names Cairo khizānas (Azbak, Ṣarghatmish, al-Muʾayyad, Qāytbāy). Lane p. xix: "more than a hundred are enumerated". The Kuwait editor has the same |
| C21 | Lane reports al-Zabīdī's note "fourteen years and some days" | S | Lane Preface p. xviii, verbatim |
| C22 | Al-Jabartī dates the completion banquet to 1181 AH | S | Jabartī p. 105: «ولما أكمله أولم وليمة… سنة احدى وثمانين ومائة وألف» |
| C23 | Kuwait editor, from the dated colophons, puts the end at Rajab 1188 and takes the banquet to mark the first part | S | Editor's introduction: «وآخر الكتاب في رجب سنة 1188…» and «تكون الوليمة… مناسبة إنجازه الجزء الأول» |
| C24 | Autograph: a line over the Qāmūs words; students' copies: red; printed editions: round brackets; otherwise hard to tell voices apart | S | Kuwait editor, "طريقة تاج العروس": «يضع كلمة القاموس وفوقها خط… باللون الأحمر… بين قوسين… لو أزيلت الحدود… لكان من الصعب». Haywood p. 89: "put the contents of the 'Qamus' in brackets" |
| C25 | On our site, bracketed words are usually al-Fīrūzābādī's | S | fsd, Slw and SlH entries compared with the Qāmūs fsd entry |
| C26 | *al-muṣannif* on its own = al-Fīrūzābādī | S | Intro p. 7 (the four works «للمصنف»: Baṣāʾir, Bulgha…); fsd entry («ونقل المصنف في البصائر») |
| C27 | *shaykhunā* = al-Fāsī | S | Intro p. 3 «شرح شيخنا… الفاسي»; p. 4 «وقد تكفل شيخنا بالرد عليه». See suggestion B3 on nested uses |
| C28 | *qultu* = al-Zabīdī, and *wa-mimmā yustadrak ʿalayh* opens his supplement. Cited to the Kuwait editor | NQ | Neither phrase is in the OCR of the editor's introduction. The editor says only that after the entry «يستدرك ما نقص». Both markers are real in stored entries: قلت in rHm (13) and kfr; ومما يستدرك عليه in SlH (690). The citation supports only part of the claim |
| C29 | *intahā* closes a quotation, as Lane notes under nhy | S | Lane nhy (2264): "اِنْتَهَى It is ended: a word put to mark the end of a quotation." |
| C30 | "His introduction presents his role modestly" | NQ | The quoted sentence is on p. 10. But the same page, just before it, praises the work lavishly (see flagged item) |
| C31 | Arabic quotation «وليس لي في هذا الشرح فضيلة… سوى أنني جمعت فيه ما تفرق في تلك الكتب» and its translation | S | Intro p. 10, verbatim; the translation is accurate |
| C32 | rHm: after al-Fāsī cites *al-ʿUbāb* against a usage, three markers appear together | S | Entry 13: «ونقل شيخنا عن العباب للصاغاني أن ترحمت عليه لحن… انتهى سياق شيخنا. قلت:…» |
| C33 | rHm excerpt and translation | S | Entry 13 text matches; the translation is accurate |
| C34 | Qāmūs fsd excerpt and translation | S | Entry 2390 |
| C35 | Tāj fsd excerpt (brackets as in the original) and translation | S | Entry 2385 matches; the translation is accurate |
| C36 | Two plain Qāmūs senses are tied in the Tāj to named authorities' readings of Q 28:83 and Q 30:41 | S | Entry 2385 (مسلم البطين; الزجاج) against entry 2390 |
| C37 | fsd also has the teacher's note (baṭala vs taghayyara; most read Q 21:22 the first way), Sībawayh on *fasdā*, verses, the ʿAbd al-Malik report, the hadith "disliked, not forbidden", and the war al-Fasād | S | Entry 2385 |
| C38 | The Lisān fsd has Sībawayh, the verses, the report, the hadith, and Q 30:41 credited to "al-Zajjājī", but lacks Muslim al-Baṭīn, the teacher and the war | S | Entry 2384 |
| C39 | Lane "drew 'most of the contents' of his lexicon through the Tāj" | U | The quoted phrase is not in Lane's Preface (searched the full OCR of pp. i–xxxii; "contents" occurs only in other contexts). What Lane does say: "While mainly composing from the Tāj el-ʿAroos…" (p. xxii or xxiii; the odd-page header is lost in the OCR, so confirm against the scan before citing); the Tāj "would of itself alone suffice…" (p. vi); and in the Preface's section "Indications of Authorities" (page number not confirmed in the OCR) that he drew his authorities "through the medium of the Tāj el-ʿAroos or the Lisān el-ʿArab" |
| C40 | Lane found the quotations faithfully transcribed. In most articles 3/4 to 9/10 of the additions stand verbatim in the Lisān, and he faulted al-Zabīdī for not saying so | S | Lane pp. xix–xx, verbatim ("faithfully transcribed"; "from three-fourths to about nine-tenths"; "want of candour") |
| C41 | Kuwait editor: 28 lines of Ibn Manẓūr's introduction were copied without acknowledgement | S | Editor's introduction: «نقل ثمانية وعشرين سطرا من مقدمة ابن منظور… دون أن يشير إلى ذلك» |
| C42 | Baalbaki counts the Lisān among his major sources | S | Baalbaki p. 203: "in spite of utilizing the Lisān as one of his major sources in Tāj al-ʿarūs" |
| C43 | Slw: the bracketed Qāmūs gives five senses of *ṣalāt* | S | Entry 1396: (الدعاء), (الرحمة), (الاستغفار), (حسن الثناء…), (عبادة فيها ركوع وسجود) |
| C44 | Slw: supplication called "the root of its meanings"; Q 9:103; al-Aʿshā's wine-jar verse | S | Entry 1396: «وهو أصل معانيها… وصل عليهم… قول الأعشى: وصلى على دنها وارتسم… أن لا تحمض» |
| C45 | Slw excerpt and translation | S | Entry 1396 matches; the translation is accurate |
| C46 | Ibn al-Athīr, al-Fayyūmī, al-Rāghib and (via al-Munāwī) al-Rāzī follow on "new coinage or old word extended"; the entry does not decide | S | Entry 1396, in this order: Ibn al-Athīr, al-Miṣbāḥ (with the *naql* vs *majāz* debate), al-Rāghib, al-Munāwī quoting al-Rāzī |
| C47 | SlH: Bishr ibn Abī Khāzim's verse for *ṣilāḥ*; a definition of *iṣṭilāḥ* from al-Khafājī | S | Entry 690: «قال بشر بن أبي خازم: يسومون الصلاح…»; «والاصطلاح: اتفاق طائفة مخصوصة على أمر مخصوص؛ قاله الخفاجي» |
| C48 | That al-Khafājī is al-Shihāb (d. 1069 AH / 1659 CE) | S (inference) | Dates: Shamela author 711. The identification is contextual: the same entry cites «الشهاب… شرح الشفاء», and intro pp. 4 and 9 name al-Shihāb al-Khafājī as a source. See suggestion B4 |
| C49 | SlH faults the Qāmūs for overlooking the well-known form *ṣalaḥa, yaṣluḥu* | S | Entry 690: «وأغفل المصنف اللغة المشهورة، وهي صلح كنصر يصلح ويصلح» |
| C50 | The Tāj cannot settle a verse's meaning or date a usage | S (interpretation) | Framed as the essay's own judgement |
| C51 | He disclaims hearing face to face, travelling, or judging who erred | S | Intro p. 10: «لا أدعي فيه دعوى فأقول: شافهت، أو سمعت، أو شددت، أو رحلت، أو أخطأ فلان أو أصاب» |
| C52 | His evidence comes from books | S | Intro p. 5 «ونقلت بالمباشرة لا بالوسائط عنها»; p. 10 «عن كل كتاب نقلت مضمونه» |
| C53 | 1,600 entries from hawramani, which names no source | S | `dicts` shows 1,600; the hawramani page gives no edition or source (it has only a description, with "d. 1790 CE") |
| C54 | Stored text matches the Shamela Kuwait text word for word, gaps and misprints included | S | Entry 690 compared with shamela.ws/book/7030/3326–3330 (vol. 6 pp. 547–551). The gap «(سقط: لم يستكن لتهدد وتنمر» and the misprint «سَجَات الأساس» are identical |
| C55 | About a third of entries lack the Qāmūs brackets (e.g. kfr, xlq) | S | My count: 531 of 1,600 (33%) have fewer than 3 round-bracket groups other than verse or sura references. kfr: all 18 "(" enclose verses; xlq opens unbracketed |
| C56 | Round brackets also enclose verse; curly brackets mostly enclose Qur'an; stray { } ! marks | S | kfr (verse in brackets); fsd (curly = Qur'an); Slw (stray { } !) |
| C57 | (سقط: …) notes mark gaps | S | Entry 690; 56 entries contain سقط |
| C58 | dyn is defective and runs into another root's text | S | dyn entry: after «وما لا أجل له فقرض» it continues with دهقن material |
| C59 | Qāmūs abbreviations: ج plural, ة village, ع place, د town, م well known | S | Qāmūs intro p. 40: «مكتفيا بكتابة ع، د، ة، ج، م، عن قولي: موضع، وبلد، وقرية، والجمع، ومعروف» |
| C60 | "Already mentioned" / "will come" refer to the book's order by final radical | S | Haywood p. 88 (the Qāmūs's rhyme order, which the Tāj follows); Slw «وقد ذكرنا شيئا من ذلك في حرف الثاء» |

**Totals: 60 claims. 57 supported, 2 need qualification, 1 unsupported.**

## Flagged items and fixes

**C39 (UNSUPPORTED): Lane "drew 'most of the contents' of his lexicon through the Tāj".**
- The quoted words are not in Lane's Preface.
- **Fix:** replace the quotation with Lane's own words, for example: "[[guide:lane-lexicon|Lane]], who composed his lexicon, he says, 'mainly' from the Tāj el-ʿAroos[^lane-preface|p. xxii or xxiii, confirm on the scan]". Alternatively, drop the quotation marks and paraphrase with a correct locator.
- **Also:** extend the lane-preface citation's page range, since that page lies outside the cited pp. xviii–xx.

**C28 (NEEDS QUALIFICATION): *qultu* and *wa-mimmā yustadrak ʿalayh* cited to the Kuwait editor.**
- The editor's introduction does not name these phrases. It says only that al-Zabīdī supplements what is missing after each entry.
- **Fix:** cite the phrases to the entries that show them. For example, attach the *qultu* gloss to the rHm excerpt, which already demonstrates it, and name SlH ([[root:SlH|…]] has «ومما يستدرك عليه»). Keep [^kuwait-ed] only for the general statement that a supplement follows the Qāmūs material.

**C30 (NEEDS QUALIFICATION): "His introduction presents his role modestly".**
- On the same page (vol. 1 p. 10), just before the quoted sentence, he calls the work «بديع الإتقان، صحيح الأركان» ("of wondrous precision, sound in its pillars"). He says that by composing it he has reached «ذروة الحفاظ» ("the summit of the memorisers"), and that it «غني ما فيه عن غيره وافتقر غيره إليه» ("its contents need no other book, while other books need it").
- The modest sentence also serves to place responsibility for errors on his sources («فعهدته على المصنف الأول»).
- **Fix:** write "In one passage his introduction plays down his own role" or "Amid high praise for the work, he describes his own share modestly". Optionally add that he makes his sources answerable for any error.

## Brief issues

- **B1 (suggestion).** The SlH sentence under "Old words, later senses" is too compressed for the heading's point. The reader is not told that Bishr's verse is pre-Islamic evidence while al-Khafājī's definition is 17th-century technical usage, printed side by side without dates. Spell it out if a cited source for Bishr's date can be added, or make the point without dating Bishr.
- **B2 (suggestion).** Two list-like sentences read as inventories:
  - fsd: "The entry also gives … Sībawayh …, verses, a report …, a hadith …, and a war …"
  - Slw: "Ibn al-Athīr, al-Fayyūmī, al-Rāghib and, through al-Munāwī, al-Rāzī follow …"
  - Consider naming one or two and summarising the rest.
- **B3 (suggestion).** "*shaykhunā* is al-Fāsī" holds for al-Zabīdī's own voice. Inside quoted passages the word can mean someone else's teacher. In rHm, within al-Fāsī's quotation, «شيخنا سيدي المهدي الفاسي» is al-Fāsī's shaykh. A half-clause ("in al-Zabīdī's own voice") would prevent misreading.
- **B4 (suggestion).** Give the name as "al-Shihāb al-Khafājī" and support the identification. Cite the SlH entry, which in the same article cites «الشهاب… شرح الشفاء», or cite intro vol. 1 p. 9. At present the reader sees only a date attached to a bare "al-Khafājī".
- **B5 (suggestion).** The heading "Two voices on one line" undersells the section, which is about three or more voices (Qāmūs, al-Zabīdī, al-Fāsī, quoted authorities).
- **B6 (suggestion).** At 1,094 words (validator) the essay is at the top of the range. Trimming B2 would help.

There is no padding, ranking or generic praise. Translations are labelled ("translations from Arabic here are our own"; "translation for this guide"). Every root mention is linked. No forced "original root meaning" narrative.

## URL check

Every source URL opened and is the stated work:

- **shamela 7030:** the Kuwait edition card. /7030/3326 is vol. 6 p. 547, the start of صلح.
- **shamela 11998/802:** Jabartī vol. 2 p. 104 (Dār al-Jīl), inside the cited pp. 103–113.
- **archive ZUB1965AR:** the Kuwait edition, 40 vols. Vol. 1 is credited to Farrāj, 1965.
- **archive anarabicenglish03lanegoog:** Lane, 1863, Williams and Norgate, with the Preface.
- **archive in.gov.ignca.12555:** Haywood, Brill 1960.
- **AUB bitstream:** Baalbaki, JAS 6 (2019) 185–208.
- **hawramani category page:** opens.
- **shamela author/711:** al-Shihāb al-Khafājī, 977–1069 / 1569–1659.
- **IslamWeb bk_no=123:** Qāmūs author's introduction, with the page marker [ص: 40].

No source is listed without being used. Locator note: the lane-preface citation (pp. xviii–xx) would need p. xxii/xxiii if the C39 fix quotes "mainly composing".

## Validator

`node scripts/validate-dictionary-guides.mjs taj-al-arus` → **ok**:
- 10 root links
- 4 excerpts
- 1,094 words
- 1/1 guides pass

## Site-data issues

1. **Stored death year 1790 is wrong for the recorded death date.** Al-Jabartī (vol. 2 p. 112, in the 1205 section) puts the death in Shaʿbān 1205, which is April 1791. Lane (Preface p. xviii) gives 1791. 1790 appears to be the Gregorian year in which 1205 AH began (hawramani and Baalbaki give 1205/1790). Suggest storing 1791.
2. **Title form.** The dictionary slug and the hawramani title read "fī Jawāhir al-Qāmūs". The author's own title (intro vol. 1 p. 11) is "min Jawāhir al-Qāmūs". The displayed short name "Tāj al-ʿArūs" is fine.
3. **Stored-text defects.** dyn has the wrong text after its first definition. 56 entries contain (سقط: …) gap notes. About 33% of entries (531/1,600 by heuristic) lack the round brackets that separate the Qāmūs from the commentary.
