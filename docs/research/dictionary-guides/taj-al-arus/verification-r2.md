# Tāj al-ʿArūs guide: verification, round 2

**Page checked:** `roots/frontend/src/content/dictionary-guides/guides/taj-al-arus.ts` (the post-revision-r1 text)

**Date:** 2026-09-26

**Independence:** I did not open research-notes.md or revision-r1.md. I read verification-r1.md only to find the points flagged in round 1. Every claim below was checked again from sources I opened myself.

## Sources opened for this round

- **Tāj, author's introduction.** Kuwait edition as paginated in al-Maktaba al-Shāmila, https://shamela.ws/book/7030/1 to /14 (vol. 1, pp. 1–14). The book card at https://shamela.ws/book/7030 says: Kuwait, 40 vols, 1385–1422 AH / 1965–2001, «ترقيم الكتاب موافق للمطبوع».
- **Ibn Manẓūr, *Lisān al-ʿArab*, author's introduction.** Shamela book 1687, vol. 1, p. 8: https://shamela.ws/book/1687/8. I opened it to test whether the introduction lines the guide quotes are al-Zabīdī's own.
- **al-Jabartī, *ʿAjāʾib al-Āthār*, vol. 2.** Pages 103–105 and 111–113: https://shamela.ws/book/11998/801 to /803 and /809 to /811.
- **Kuwait edition, vol. 1 (1965), editor's front matter by ʿAbd al-Sattār Aḥmad Farrāj.** I used the archive.org OCR, "1 - تاج العروس_djvu.txt", from https://archive.org/details/ZUB1965AR. The relevant sections are «طريقة تاج العروس», «احتفال الزبيدي بإنجاز التاج», «صلة الزبيدي بالقاموس» and «التعريف بالزبيدي».
- **Lane, *Lexicon*, Book I (Williams and Norgate, 1863), Preface.** I used the full OCR of https://archive.org/details/arabicenglishlex0001edwa and checked page headers against its page_numbers.json. Leaf n24 is p. xix.
- **Haywood, *Arabic Lexicography* (Brill, 1960), pp. 86–90.** OCR of https://archive.org/details/in.gov.ignca.12555.
- **Baalbaki, "The Notion of gharīb in Arabic Lexica," JAS 6 (2019).** The PDF at the cited AUB URL, p. 203 and n. 85.
- **al-Naṣṣ, "Bishr ibn Abī Khāzim al-Asadī," *al-Mawsūʿa al-ʿArabiyya*.** https://arab-ency.com.sy/details/4285
- **al-Shihāb al-Khafājī's author page on Shamela.** https://shamela.ws/author/711
- **al-Qāmūs, author's introduction on IslamWeb.** The URL cited in the guide.
- **hawramani category page.** The URL cited in the guide.
- **Stored entries**, read with `_dict_guide_tool.py entry`:
  - Tāj: fsd (2385), rHm (13), Slw (1396), SlH (690), kfr (159), xlq (49), dyn (1388)
  - Qāmūs: fsd (2390)
  - Lisān: fsd (2384)
  - Lane: nhy
- **Read-only SQL over all 1,600 displayed Tāj entries.**

## Claims table

S = supported. NQ = needs qualification. U = unsupported.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Tāj al-ʿArūs*, titleAr تاج العروس من جواهر القاموس | S | Intro vol. 1 p. 11: «وسميته (تاج العروس من جواهر القاموس)» |
| C2 | titleGloss "The Bride's Crown, from the Jewels of al-Qāmūs" | S | A fair rendering of C1 |
| C3 | author / authorAr Murtaḍā al-Zabīdī | S | Jabartī vol. 2 p. 104: «الشهير بمرتضى الحسيني الزبيدي» |
| C4 | authorFull Abū l-Fayḍ Muḥammad ibn Muḥammad al-Ḥusaynī al-Zabīdī, known as Murtaḍā | S | Jabartī p. 104 has the name chain. p. 105: «وكناه… بابي الفيض». The Kuwait editor, «التعريف بالزبيدي», agrees |
| C5 | period d. 1205 AH / 1791 CE | S | Jabartī p. 112 (plague, Shaʿbān), in the section for 1205. Shaʿbān 1205 ≈ April 1791. Lane p. xviii: "died A.D. 1791 (in the year of the Flight 1205)" |
| C6 | kind: commentary on al-Qāmūs | S | Intro p. 4: «وضع شرح عليه، ممزوج العبارة» |
| C7 | Summary: an 18th-century commentary wrapping the Qāmūs in quotations, Qur'anic and poetic evidence, disputes, corrections and additions | S | Lane p. xviii ("interwoven commentary… corrections of mistakes… examples in prose and verse… additional words"); the entries fsd, Slw and SlH |
| C8 | Summary: useful for finding who recorded a meaning and on what evidence | S | Interpretation; the fsd and Slw entries bear it out |
| C9 | Lede: working in Cairo in the 1760s and 1770s | S | Lane p. xviii ("commenced, in Cairo… fourteen years"); Kuwait editor: colophons 1187–1188, last Rajab 1188 |
| C10 | Lede: running commentary that names sources, adds verse/poem, reports disputes, corrects, supplies missing words | S | Entries fsd, rHm, SlH, kfr. Kuwait editor, «طريقة تاج العروس»: «ينسب كثيرا من التفسير اللغوي إلى قائليه… يستدرك ما نقص» |
| C11 | The Qāmūs was prized for concision and so attracted commentators | S | Intro p. 2: «أوجز لفظه وأشبع معناه… ولما كان إبرازه في غاية الإيجاز… تصدى لكشف غوامضه… رجال» |
| C12 | His teacher al-Fāsī wrote one of the fullest commentaries; al-Zabīdī calls him "my mainstay in this discipline" | S | Intro p. 3: «ومن أجمع ما كتب عليه… شرح شيخنا… محمد بن الطيب… الفاسي… وهو عمدتي في هذا الفن» |
| C13 | His plan: *mamzūj al-ʿibāra*, noting where copies differ, quoting sources explicitly, gathering verses as evidence | S | Intro p. 4: «ممزوج العبارة… واف ببيان ما اختلف من نسخه». p. 5: «بصريح النقول، والتقاط أبيات الشواهد» |
| C14 | He wrote for scholars, especially teachers of *gharīb al-ḥadīth* and the major works on Arabic | S | Intro p. 4: «فاقة الأفاضل… ولا سيما من انتدب منهم لتدريس علم غريب الحديث، وإقراء الكتب الكبار من قوانين العربية» |
| C15 | "gives his motive as preserving a language on which, he says, the rulings of the Qur'an and the Sunna depend" | **NQ** | The words are on intro p. 11: «فإنني لم أقصد سوى حفظ هذه اللغة الشريفة، إذ عليها مدار أحكام الكتاب العزيز والسنة النبوية». But they are adapted from Ibn Manẓūr's introduction to the Lisān (vol. 1 p. 8): «فإنني لم أقصد سوى حفظ أصول هذه اللغة النبوية… إذ عليها مدار أحكام الكتاب العزيز والسنة النبوية». They fall inside the 28 lines that the Kuwait editor says al-Zabīdī copied from Ibn Manẓūr without acknowledgement: «من… فجاء بحمد الله تعالى هذا الشرح واضح المنهج… إلى وسميته تاج العروس». The guide presents them as al-Zabīdī's own statement of motive |
| C16 | Born 1145 AH (1732–33) | S | Jabartī p. 104: «ولد سنة خمس واربعين ومائة وألف كما سمعته من لفظه»; Kuwait editor, same |
| C17 | "in Bilgram in India according to later sources (his student al-Jabartī does not name the town)" | **NQ** | Partly supported. The Kuwait editor, the only source cited, lists the later sources (*Abjad al-ʿUlūm*, *Nashr al-ʿArf*, *Fihris al-Fahāris*, the second printing of the Tāj) and confirms Jabartī's silence. But the editor disputes the attribution. He says: «فنحن لا نجد نصا واضحا في كلامه يدل على أنه من الهند». He calls the Bilgram evidence «ليس بدليل على ولادته هناك». He notes that al-Zabīdī signs himself «الواسطي العراقي الأصل». The guide mentions only Jabartī's silence, not the editor's doubt |
| C18 | Studied in the Hijaz and Yemen | S | Jabartī p. 104: «حج مرارا… بمكة… نزل بالطائف بعد ذهابه إلى اليمن» |
| C19 | Reached Cairo in 1167 AH (1753) | S | Jabartī p. 104: «ورد إلى مصر في تاسع صفر سنة سبع وستين ومائة وألف» (≈ Dec. 1753) |
| C20 | Died in Cairo, Shaʿbān 1205, spring 1791 | S | Jabartī p. 112: «وأصيب بالطاعون في شهر شعبان… وتوفي يوم الأحد». p. 113: buried near al-Sayyida Ruqayya |
| C21 | In Cairo's libraries he found many of the 100+ works his introduction lists: lexicons including the Lisān, and works on history and medicine | S | Intro pp. 5–9: the Lisān on p. 5, *Taʾrīkh Dimashq* on p. 8, Dāwūd al-Anṭākī's *Tadhkira* on p. 9; the Cairo *khizāna*s of Azbak, Ṣarghatmish, al-Muʾayyad and Qāytbāy are named. Lane p. xviii: "more than a hundred are enumerated". Kuwait editor: «ظفر في مصر بأمهات الكتب… وجده بالقاهرة» |
| C22 | Al-Jabartī dates the completion banquet to 1181 AH (1767–68) | S | Jabartī p. 105: «ولما أكمله أولم وليمة حافلة… في سنة احدى وثمانين ومائة وألف» |
| C23 | The Kuwait editor, from dates in the text, puts the end in Rajab 1188 (1774), the banquet marking the first part | S | Editor: «وآخر الكتاب في رجب سنة 1188»; «تكون الوليمة… مناسبة إنجازه الجزء الأول» |
| C24 | Autograph: a line over the Qāmūs words. Students' copies: red. Printed editions: round brackets. Otherwise hard to tell the voices apart | S | Kuwait editor, «طريقة تاج العروس»: «يضع كلمة القاموس وفوقها خط… باللون الأحمر… بين قوسين… لو أزيلت الحدود… لكان من الصعب». Haywood p. 89: "put the contents of the 'Qamus' in brackets" |
| C25 | On our site, bracketed words are usually al-Fīrūzābādī's | S | Tāj fsd (2385) against Qāmūs fsd (2390); Slw; SlH |
| C26 | In his own voice, *al-muṣannif* alone = al-Fīrūzābādī | S | Intro p. 7: *al-Baṣāʾir*, *al-Bulgha* and others, «الأربعة للمصنف». fsd: «ونقل المصنف في البصائر» |
| C27 | In his own voice, *shaykhunā* = al-Fāsī | S | Intro p. 3: «شرح شيخنا… الفاسي»; p. 4: «وقد تكفل شيخنا بالرد عليه». Correctly scoped ("in al-Zabīdī's own voice") |
| C28 | *qultu* introduces his own view, as in the rHm passage | S | rHm (13): «انتهى سياق شيخنا. قلت: …». kfr (159): «قاله شيخنا. قلت: لا غلط…» |
| C29 | *intahā* closes a quotation, as Lane notes under nhy | S | Lane nhy: "اِنْتَهَى… a word put to mark the end of a quotation" |
| C30 | *wa-mimmā yustadrak ʿalayh* opens the supplement at the end of an entry (as in SlH), adding what the Qāmūs lacks | S | SlH (690): «ومما يستدرك عليه: قوم صلوح…». Kuwait editor: «وبعد انتهاء المادة… يستدرك ما نقص» |
| C31 | "Amid high praise for the work, he plays down his own share and makes the original authors answerable for whatever in it is right or wrong", followed by the quotation attributed to "al-Zabīdī, introduction" | **NQ** | Every element is on intro p. 10, including «بديع الإتقان… ذروة الحفاظ», «وليس لي في هذا الشرح فضيلة…» and «فعهدته على المصنف الأول». But the whole passage is Ibn Manẓūr's, reused nearly word for word. Lisān intro vol. 1 p. 8 has «فجاء بحمد الله وفق البغية وفوق المنية، بديع الإتقان، صحيح الأركان… حللت بوضعه ذروة الحفاظ… وليس لي في هذا الكتاب فضيلة أمت بها… فعهدته على المصنف الأول». These are the 28 lines the Kuwait editor identifies as copied without acknowledgement. In the quoted self-assessment, al-Zabīdī made two changes: الكتاب became الشرح, and «الأزهري وابن سيده» became «شيخنا». The guide presents this as his personal self-presentation. Four paragraphs later it reports the unacknowledged copying, without telling the reader that these are the copied lines |
| C32 | Arabic quotation «وليس لي في هذا الشرح فضيلة أمت بها … سوى أنني جمعت فيه ما تفرق في تلك الكتب» and its translation | S (text) | Verbatim, intro p. 10, and the translation is accurate. The attribution problem is under C31 |
| C33 | In practice he weighs and corrects, even his teacher | S | rHm (13) objects to al-Fāsī's al-ʿUbāb citation. kfr (159): «قلت: لا غلط، والصواب ما ذهب إليه الجوهري» against al-Fāsī |
| C34 | In rHm, al-Fāsī cites al-Ṣaghānī's *al-ʿUbāb* against a usage, and three markers appear together | S | rHm: «ونقل شيخنا عن العباب للصاغاني أن ترحمت عليه لحن… انتهى سياق شيخنا. قلت:» |
| C35 | rHm excerpt and translation | S | Matches entry 13; the translation is accurate |
| C36 | Qāmūs fsd excerpt, translation, "bare equivalents" | S | Entry 2390: «والفَسادُ: أخْذُ المالِ ظُلْماً، والجَدْبُ.» |
| C37 | In the Tāj the same words are in round brackets | S | Entry 2385: «(والفَسَادُ: أَخْذُ المالِ ظُلْماً)… (الجَدْبُ)» |
| C38 | Tāj fsd excerpt and translation | S | Matches entry 2385; the translation is accurate (including "dearth at sea… towns on the rivers") |
| C39 | The two Qāmūs senses are tied to named authorities' readings of Q 28:83 and Q 30:41 | S | Entry 2385: «هكذا فسر مسلم البطين» (28:83); «وهذا قول الزجاج» (30:41) |
| C40 | "In our view… one of the Tāj's most useful habits…" | S (labelled opinion) | Framed as the guide's own view |
| C41 | The rest of the entry adds grammar, poetry, a report, a hadith, and al-Fāsī's note (*baṭala* vs *taghayyara*), with most reading Q 21:22 the first way | S | Entry 2385: Sībawayh; verses; the ʿAbd al-Malik *khabar*; the *ghīla* hadith; «قال شيخنا… بطل واضمحل، ويكون بمعنى تغير، ومن الأول عند الأكثر: لو كان فيهما…». In the entry the teacher's note comes before the excerpt, not after it ("the rest" is loose, but not wrong) |
| C42 | Much of this is in the Lisān, including Q 30:41 credited to "al-Zajjājī"; Muslim al-Baṭīn and al-Fāsī's note are not | S | Lisān fsd (2384): «هذا قول الزجاجِيِّ». Sībawayh, verses, *khabar* and hadith are present. No Muslim al-Baṭīn, no شيخنا |
| C43 | Lane: the Tāj was "the medium through which I have drawn most of the contents of my lexicon" (p. xix) | S | Lane 1863 scan, OCR line under header "PREFACE. xix" and before "xX": "As the Taj el-'Aroos is the medium through which I have drawn most of the contents of my lexicon…". Leaf n24 = p. xix (page_numbers.json: leaf 31 = xxv). Round-1 C39 is resolved |
| C44 | Lane found its quotations faithfully transcribed | S | Lane p. xx: "in every instance I found that they had been faithfully transcribed" |
| C45 | In most articles Lane compared, 3/4 to 9/10 of the additions to the Qāmūs stood verbatim in the Lisān, and he faulted al-Zabīdī for not saying so | S | Lane p. xx, verbatim ("want of candour… by not stating…") |
| C46 | The Kuwait editor: 28 lines of Ibn Manẓūr's introduction were copied without acknowledgement | S | Editor: «نقل ثمانية وعشرين سطرا من مقدمة ابن منظور… دون أن يشير إلى ذلك» |
| C47 | Baalbaki counts the Lisān among his major sources | S | Baalbaki p. 203: "in spite of utilizing the Lisān as one of his major sources in Tāj al-ʿarūs" |
| C48 | Slw: the bracketed Qāmūs gives five senses of *ṣalāt* | S | Entry 1396: (الدعاء), (الرحمة), (الاستغفار), (حسن الثناء من الله… على رسوله…), (عبادة فيها ركوع وسجود) |
| C49 | Supplication called "the root of its meanings", with Q 9:103 and al-Aʿshā's wine-jar verse | S | Entry 1396: «وهو أصل معانيها… وصل عليهم… قول الأعشى: وصلى على دنها وارتسم أي دعا لها أن لا تحمض» |
| C50 | Slw excerpt and translation | S | Matches entry 1396. The translation is accurate, and «وفي الكل نظر، انتهى» is correctly inside al-Fāsī's quotation |
| C51 | Further authorities, from Ibn al-Athīr to al-Rāzī, on new coinage vs old word extended; the entry does not decide | S | Entry 1396: Ibn al-Athīr; *al-Miṣbāḥ* (*naql* vs *majāz*); al-Rāghib; al-Munāwī quoting al-Rāzī (Muʿtazila «أسماء شرعية» vs «المجازات المشهورة»). It then passes to *al-Ṣiḥāḥ* without a verdict |
| C52 | SlH: *ṣilāḥ* "reconciliation" is attested in a verse by Bishr ibn Abī Khāzim | S | Entry 690: «(وصالحه مصالحة، وصلاحا)… قال بشر بن أبي خازم: يسومون الصلاح بذات كهف…». The attribution is the Tāj's |
| C53 | Bishr was a pre-Islamic poet of the late 6th century | S | arab-ency 4285 (al-Naṣṣ, vol. 5, 2002, p. 119): «(… ـ نحو 598م)… من فحول شعراء الجاهلية… عاش في أواخر القرن السادس الميلادي» |
| C54 | Near the end, the supplement defines *iṣṭilāḥ* as "the agreement of a particular group on a particular matter", citing al-Khafājī | S | Entry 690, after «ومما يستدرك عليه»: «والاصطلاح: اتفاق طائفة مخصوصة على أمر مخصوص؛ قاله الخفاجي». The translation is accurate |
| C55 | Most likely al-Shihāb al-Khafājī (d. 1069 AH / 1659 CE), whose works al-Zabīdī lists among his sources | S (hedged) | Intro p. 9: «وشرح الشفاء، للشهاب الخفاجي. وشفاء الغليل، له أيضا». p. 4: «وللشهاب الخفاجي في العناية…». SlH itself: «ونقله الشهاب… (شرح الشفاء)». Shamela author 711: «الشهاب الخفاجي (٩٧٧ - ١٠٦٩ هـ = ١٥٦٩ - ١٦٥٩ م)» |
| C56 | "Some ten centuries separate the two; the page does not say so" | S | Arithmetic: c. 598 CE to 1659 CE ≈ 10.6 centuries. The entry gives no dates |
| C57 | The Tāj maps who said what; it cannot tell you a word's meaning in a particular verse or date a usage; each item is as old as its source | S (interpretation) | The guide's own judgement; consistent with C39 and C51 |
| C58 | "Al-Zabīdī says he makes no claim to have heard words face to face or travelled for them; his evidence comes from books" | **NQ** | Intro p. 10: «لا أدعي فيه دعوى فأقول: شافهت، أو سمعت، أو شددت، أو رحلت». This is Ibn Manẓūr's formula, from Lisān intro p. 8: «لا أدعي فيه دعوى فأقول شافهت أو سمعت… أو شددت أو رحلت». It lies within the same 28 copied lines. "His evidence comes from books" is independently supported by intro p. 5, in al-Zabīdī's own list: «ونقلت بالمباشرة لا بالوسائط عنها» |
| C59 | onOurSite: 1,600 entries from hawramani, which names no source | S | `dicts`/SQL: 1,600. The hawramani page gives only a description (d. 1790 / 1205), with no edition named |
| C60 | Matches the Shamela Kuwait text word for word, gaps and misprints included | S | SlH (690) against shamela 7030/3326–3330: «(سقط: لم يستكن لتهدد وتنمر», «من سجات الأساس», the Bishr verse and «قاله الخفاجي» all identical. Book card identifies the Kuwait ed., 1965–2001 |
| C61 | In roughly a third of entries (e.g. kfr, xlq) the Qāmūs's words are not bracketed | S | My SQL: 521/1,600 (33%) have no «(و)» marker and 490/1,600 (31%) have neither «(و)» nor an early bracket. kfr and xlq are in both sets. kfr and xlq open unbracketed |
| C62 | Round brackets also enclose verse; curly brackets mostly Qur'an; stray { } ! marks | S | kfr: poetry in (… ... …). fsd: {Qur'an}. Slw: «{الصَّلاَ», «إِنَّ! الصَّلاةَ» |
| C63 | (سقط: …) notes mark gaps | S | SlH (690); 56 displayed entries contain سقط |
| C64 | dyn is defective and runs into another root's text | S | Entry 1388: after «(وما لا أجل له فقرض)» it continues «التدهقن: التكيس… دهقن» |
| C65 | Qāmūs abbreviations: ج, ة, ع, د, م | S | Qāmūs intro, after [ص: 40]: «مكتفيا بكتابة ع، د، ة، ج، م، عن قولي: موضع، وبلد، وقرية، والجمع، ومعروف». Also in the Tāj, e.g. SlH «(والصالحية: ة قرب الرهى)» |
| C66 | "Already mentioned" and "will come" refer to the book's order by the root's last letter | S | Haywood p. 88: the Qāmūs's deliberate rhyme order, which the commentary follows. Slw: «وقد ذكرنا شيئا من ذلك في حرف الثاء» |

**Totals: 66 claims. 62 supported, 4 need qualification (C15, C17, C31, C58), 0 unsupported.**

## Round-1 flags: status

- **C39 (Lane, "most of the contents")**: resolved, now C43.
  - The full sentence is quoted exactly and sits on p. xix of the 1863 scan.
  - The new URL opens at leaf n24, which is p. xix.
  - p. xx carries "faithfully transcribed" and the 3/4–9/10 passage, so "pp. xix–xx" is correct.
- **C28 (*qultu* and *wa-mimmā yustadrak ʿalayh*)**: resolved, now C28 and C30. Both markers are now shown through stored entries (rHm, SlH), and [^kuwait-ed] supports only the supplement statement.
- **C30 ("presents his role modestly")**: reworded, but a deeper problem remains; see C31. The passage, including both the praise and the modesty, is Ibn Manẓūr's. So the revised framing still attributes a borrowed self-portrait to al-Zabīdī.

## Flagged items and fixes

### C31 + C15 + C58 (NQ): the introduction lines quoted and paraphrased as al-Zabīdī's own self-presentation are copied from Ibn Manẓūr

**Evidence:**
- Tāj intro vol. 1 pp. 9–11 (Shamela 7030/9–11) runs from «فجاء بحمد الله تعالى هذا الشرح واضح المنهج» to «وسميته (تاج العروس…)».
- That stretch is, almost word for word, Ibn Manẓūr's introduction to the *Lisān* (Shamela 1687/8, vol. 1 p. 8).
- The Kuwait editor names exactly this stretch as the 28 lines copied without acknowledgement: «من مقدمة ابن منظور… دون أن يشير إلى ذلك… فجاء بحمد الله تعالى هذا الشرح واضح المنهج… إلى وسميته تاج العروس».
- The stretch contains all of the following:
  - the praise («بديع الإتقان… ذروة الحفاظ»)
  - the modesty («وليس لي في هذا الشرح فضيلة…»)
  - the shifting of responsibility («فعهدته على المصنف الأول»)
  - the disclaimer of fieldwork («شافهت… رحلت»)
  - the motive («لم أقصد سوى حفظ هذه اللغة… مدار أحكام الكتاب العزيز والسنة النبوية»)
- Al-Zabīdī's changes are small: الكتاب became الشرح; «الأزهري وابن سيده» became «شيخنا»; «أصول هذه اللغة النبوية» became «هذه اللغة الشريفة».

**Fix (must-fix):** keep the quotation if wanted, but say whose words they are.

- **The modesty passage.** For example: "His introduction ends with a passage taken over, almost word for word and without acknowledgement, from Ibn Manẓūr's introduction to the *Lisān*. These are the twenty-eight lines the Kuwait editor identifies [^kuwait-ed]. In it he praises the work, disclaims any merit of his own, and makes the original authors answerable for what is right or wrong:" Then change the quote's attribution line to "— al-Zabīdī, introduction to the *Tāj*, adapting Ibn Manẓūr's introduction to the *Lisān* (translation for this guide)". Add a source for the Lisān introduction, e.g. Shamela book 1687, vol. 1 p. 8.
- **The motive (C15).** Either drop the p. 11 motive sentence or add "in words borrowed from Ibn Manẓūr". The audience sentence (p. 4) is his own and can stay.
- **C58.** Rephrase to: "Borrowing Ibn Manẓūr's words again, he disclaims having heard words face to face or travelled for them. His own list of sources says he quoted the books directly, 'not through intermediaries' [^zabidi-intro|vol. 1, p. 5]."
- **Move the later sentence.** "The Kuwait editor notes that al-Zabīdī also copied twenty-eight lines…" can then move up or be cut, since the point is made where it matters.

### C17 (NQ): Bilgram

**Evidence:** the cited Kuwait editor lists the later sources that place his birth in Bilgram, but rejects their evidence:
- «فنحن لا نجد نصا واضحا في كلامه يدل على أنه من الهند»
- «وهذا ليس بدليل على ولادته هناك»
- He cites al-Zabīdī's own signature: «الواسطي العراقي الأصل… نزيل مصر».

**Fix:** "in Bilgram in India according to later sources, though the Kuwait editor finds nothing in al-Zabīdī's own writings to confirm it [^kuwait-ed|vol. 1, editor's introduction]". Alternatively, "his birthplace is uncertain: later sources name Bilgram in India; al-Jabartī names no town".

## Brief issues

- **B1 (must-fix, ties to C31).** The essay's section on voices exists to separate al-Zabīdī's voice from those he quotes. At present its one block quotation from the introduction is unmarked borrowing, so the section undercuts its own aim. Correct it as above. Handled well, this is a strong teaching example of why voices must be checked.
- **B2 (suggestion).** "Lane, for whom the *Tāj* was 'the medium through which I have drawn most of the contents of my lexicon'" puts Lane's first-person "I" inside a third-person frame. Suggest: "Lane, who called the *Tāj* 'the medium through which I have drawn most of the contents of my lexicon', found its quotations faithfully transcribed but…"
- **B3 (suggestion).** At 1,100 words (validator) the essay sits at the ceiling, and the C31 and C17 fixes add words. Trim elsewhere to compensate:
  - Merge the banquet and colophon sentence into one clause, e.g. "completed, by the dates in its colophons, in 1774".
  - Or cut the now-redundant later "twenty-eight lines" sentence once the point is made at the quotation.
- **B4 (suggestion).** "The rest of the entry adds … al-Fāsī's note…": in the stored fsd entry that note comes before the excerpted lines. "The entry also gives…" would be exact.
- **B5 (suggestion).** "*ṣilāḥ*… is attested in a verse by Bishr": add "that the entry attributes to Bishr". The attribution is the Tāj's; the date is the encyclopedia's.

No padding, rankings or generic praise remain; "In our view…" is labelled as opinion. Translations are labelled. Every root mention is linked, and each link leads to a displayed entry that supports what the guide says. No forced "original root meaning" narrative.

## Source URLs

| id | URL | Status |
|---|---|---|
| zabidi-intro | https://shamela.ws/book/7030 | 200. Kuwait ed. card; pp. 1–14 opened |
| jabarti | https://shamela.ws/book/11998/802 | 200. Vol. 2 p. 104, in the 1205 section (Dār al-Jīl) |
| kuwait-ed | https://archive.org/details/ZUB1965AR | 200. 40 vols; vol. 1 by ʿAbd al-Sattār Farrāj, 1965 (metadata and OCR «كتبه: عبد الستار احمد فراج») |
| lane-preface | https://archive.org/details/arabicenglishlex0001edwa/page/n24/mode/1up | 200. 1863 Williams and Norgate; leaf n24 = p. xix |
| haywood | https://archive.org/details/in.gov.ignca.12555 | 200. Haywood 1960, Brill; pp. 88–89 used |
| baalbaki | AUB bitstream | 200. PDF, JAS 6 (2019) 185–208; p. 203 |
| hawramani | category page | 200 |
| shamela-ed | https://shamela.ws/book/7030/3326 | 200. Vol. 6 p. 547, start of صلح; /3327–3330 continue the entry |
| bishr | https://arab-ency.com.sy/details/4285 | 200. Author Iḥsān al-Naṣṣ; vol. 5, 2002, p. 119 |
| khafaji | https://shamela.ws/author/711 | 200. «الشهاب الخفاجي (٩٧٧ - ١٠٦٩ هـ = ١٥٦٩ - ١٦٥٩ م)» |
| qamus-intro | IslamWeb bk_no=123 | 200. Page marker [ص: 40] precedes the abbreviation sentence |

Every listed source is used and says what it is cited for. The exception is the C31/C15/C58 attribution, which needs an added Lisān-introduction source.

## Validator

`node scripts/validate-dictionary-guides.mjs taj-al-arus` gives **ok**:
- 11 root links (10 distinct pairs)
- 4 excerpts
- 1,100 words
- example roots SlH, rHm, fsd, Slw, kfr, xlq, dyn
- 1/1 guides pass

## Site-data issues

1. **Stored death year 1790.** Al-Jabartī (vol. 2 p. 112, in the 1205 section) puts his death in Shaʿbān 1205 ≈ April 1791, and Lane (Preface p. xviii) gives 1791. The year 1790 matches only the Gregorian year in which 1205 AH began; hawramani and Baalbaki give "1205/1790". Suggest storing 1791. This does not change the panel order.
2. **Title form.** The slug and hawramani title read "fī Jawāhir al-Qāmūs"; the author's own title (intro p. 11) is "min Jawāhir al-Qāmūs".
3. **Stored-text defects.**
   - dyn (1388) carries دهقن text after its first definition.
   - 56 entries contain (سقط: …) gap notes.
   - About a third of entries (490–521 of 1,600 by heuristic) lack the round brackets that separate the Qāmūs from the commentary.
