# Verification round 1 — Mukhtār al-Ṣiḥāḥ

Guide: `roots/frontend/src/content/dictionary-guides/guides/mukhtar-al-sihah.ts`
Verifier: independent fact-check (research-notes.md and revision files NOT opened).
Date: 2026-09-26

## Method

- Opened every cited URL myself (curl or WebFetch), and read the Arabic text.
  - al-Ziriklī, *al-Aʿlām*, Shamela 12286/5120 and 5121 (both marked vol. 6 p. 55).
  - *Kashf al-ẓunūn*, Shamela 2118/1144–1145 (vol. 2 pp. 1072–73), plus the book card for the edition.
  - Arabic Wikisource transcription of the 1911 Cairo title page.
  - *Mukhtār al-Ṣiḥāḥ*, 1999 Beirut ed. The book card is Shamela 23193. The introduction pp. 7–10 came through the Shamela ajax page endpoint, pages 2–5. I also read the entries ع ذ ب (p. 203) and ي د ي (pp. 348–49).
  - Khāṭir's 1916 arranged edition on Internet Archive (RZY1916AR): the title page image (n4), the preface p. (د) image (n9), and the djvu OCR text.
  - Haywood, *Arabic Lexicography* (archive.org in.gov.ignca.12555): the djvu OCR text, pp. 67–69 and 75–76.
  - The ALECSO/IMA note, and hawramani's dictionary page and About page.
- Checked site data with `_dict_guide_tool.py entry …`, and with direct SQL that uses the tool's own "displayed" filter. Counts were recomputed independently in a scratch script.
- Ran the validator.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Mukhtār al-Ṣiḥāḥ* / مختار الصحاح (title, titleAr) | S | Shamela 23193 book card. 1916 title page (IA RZY1916AR n4). Intro p. 7: وسميته (مختار الصحاح) |
| C2 | titleGloss "Selections from al-Ṣiḥāḥ" | S | Intro p. 7: هذا مختصر … جمعته من كتاب الصحاح. *mukhtār* = "selected" |
| C3 | Author Zayn al-Dīn Abū ʿAbd Allāh Muḥammad b. Abī Bakr b. ʿAbd al-Qādir al-Rāzī; زين الدين الرازي | S | Shamela 23193 card: زين الدين أبو عبد الله محمد بن أبي بكر بن عبد القادر الحنفي الرازي. Ziriklī vol. 6 p. 55 |
| C4 | Completed 660 AH / 1262 (period) | S | Kashf vol. 2 p. 1073: وافق فراغه عشية يوم الخميس غرة شهر رمضان … سنة ٦٦٠. Ziriklī: فرغ من تأليفه أول رمضان سنة ٦٦٠ |
| C5 | "a later date also circulates" (period) | S | 1911 Cairo title page (Wikisource) quotes Kashf with سنة ستين وسبعمائة |
| C6 | d. after 666 AH / 1268 (period) | S | Ziriklī: (٠٠٠ - بعد ٦٦٦ هـ = ٠٠٠ - بعد ١٢٦٨ م). IMA page title: (ت بعد 666هـ) |
| C7 | kind "Abridgment of al-Ṣiḥāḥ" | S | Intro p. 7 (مختصر … من كتاب الصحاح) |
| C8 | Thirteenth-century (summary) | S | As C4/C6 |
| C9 | Commoner and Qur'anic vocabulary kept (summary, lede) | S | Intro p. 7: لكثرة استعماله وجريانه على الألسن … خصوصا ألفاظ القرآن العزيز والأحاديث النبوية |
| C10 | Most poetry dropped (summary) | S | Own count, see C26–C27 |
| C11 | Verb vowelling fixed by model verbs (summary) | S | Intro pp. 7–9 |
| C12 | Abridger's notes flagged قلت (summary, lede) | S | Intro p. 7: فكل موضع مكتوب فيه (قلت) فإنه من الفوائد التي زدتها على الأصل |
| C13 | Most of the text is someone else's, al-Jawharī's (lede) | S | Intro p. 7. Entry comparisons (Alh 556/109, ydy 1173/1178, hdy 591/533) |
| C14 | Lede quotation "especially the words of the Mighty Qur'an and the Prophetic ḥadīth" | S | Intro p. 7 |
| C15 | Compiler is not Fakhr al-Dīn al-Rāzī | S | Different name and dates in Ziriklī vol. 6 p. 55 (Muḥammad b. Abī Bakr b. ʿAbd al-Qādir, fl. 660–666) |
| C16 | Ziriklī: Ḥanafī jurist, originally from Rayy, knew tafsīr and adab, visited Egypt and Syria, in Konya 666 and last heard of there | S | Ziriklī vol. 6 p. 55: وهو من فقهاء الحنفية، وله علم بالتفسير والأدب. أصله من الري. زار مصر والشام، وكان في قونية سنة ٦٦٦ وهو آخر العهد به |
| C17 | His other books include Q&A on puzzling Qur'anic verses | S | Ziriklī: (أنموذج جليل في أسئلة وأجوبة من غرائب آي التنزيل - ط) |
| C18 | Istanbul ed. of Kashf quotes closing note dated 1 Ramaḍān 660 (July 1262), vol. 2 p. 1073 | S | Shamela 2118/1145, title "ج2 - ص1073". Edition per Shamela card (Yaltkaya & Bilge, Istanbul 1941–43) |
| C19 | 1911 Cairo printing quotes year 760 (1359) | S | Wikisource: وفي آخره وافق فراغه عشية يوم الجمعة سنة ستين وسبعمائة; الطبعة الاولى بالمطبعة الكلية … سنة ١٣٢٩ |
| C20 | Ziriklī cites ʿAbd Allāh Mukhliṣ's treatise refuting the 8th-century view (n. 1) | S | Ziriklī fn. (1) on Shamela 12286/5121 (still marked p. 55): عبد الله مخلص في رسالة سماها (صاحب مختار الصحاح - ط) حقق فيها خطأ القول بأنه توفي سنة ٧٦١هـ أو أنه كان من رجال القرن الثامن |
| C21 | Arabic intro quotation, p. 7 | S | Matches Shamela p. 7 verbatim. The ellipsis omits لكثرة استعماله … فالأهم |
| C22 | Translation of the intro quotation | S | Accurate. Minor nuance: عالم فقيه may be read "learned jurist". The rendering "every scholar — jurist, …" is defensible |
| C23 | He chose al-Jawharī as best arranged, best refined, easiest to consult, most widely used (p. 7) | S | Intro p. 7: أحسن أصول اللغة ترتيبا وأوفرها تهذيبا وأسهلها تناولا وأكثرها تداولا |
| C24 | 856 roots displayed in both works | S | SQL: Razi 877, Jawharī 866, intersection 856 |
| C25 | Link [[guide:al-sihah]] | S | Validator passes |
| C26 | al-Jawharī quotes verse in about 4 of 5 of those entries | S | Own count: 669–704 of 856 (78–82%), depending on the detection pattern |
| C27 | al-Rāzī quotes verse "in at most one in twenty" | **NQ** | Own count: 40 of 856 (4.7%) by markers only (… / الشاعر / أنشد / الراجز). **55 of 856 (6.4%, about 1 in 16)** once "قال/قول + poet" is added. The extra hits are real verse lines (fyA, mkn, Ebd, xbv, ndd, Sdr, nwq, ESr, nfl) |
| C28 | al-Rāzī's text is about two-fifths as long | S | Own count: character ratio 0.41 over the 856 shared roots (vowel marks stripped) |
| C29 | "Every place in which qultu is written …" and the notes' sources (al-Azharī's Tahdhīb, other trusted sources, "what God opened to me"), p. 7 | S | Intro p. 7: وضممت إليه فوائد كثيرة من تهذيب الأزهري وغيره من أصول اللغة الموثوق بها ومما فتح الله تعالى به علي |
| C30 | About a hundred of 877 entries contain such a note | S | 104 entries contain vowelled قُلْتُ (the unvowelled string also catches *qulta* "you say") |
| C31 | At least a quarter of those concern a Qur'anic verse | S | About 36 of 104 have a Qur'anic quotation or reference within the note (heuristic) |
| C32 | The source named most often is al-Azharī | S | al-Azharī is named in 28 note windows. Next: Abū ʿUbayd 6, al-Farrāʾ 6 |
| C33 | The vowel/pattern specifications are also his, without a flag | S | Intro p. 7 (كل ما أهمله الجوهري … ذكرته). The formula is absent from al-Jawharī's entries (C49) |
| C34 | The rest is al-Jawharī's substance, trimmed and reworded, including his "I" | S | Alh 556 vs 109 (سمعت أبا علي / أنشدني أبو علي in both) |
| C35 | *anshadanī Abū ʿAlī* in Alh is al-Jawharī speaking | S | Entry 109 (al-Ṣiḥāḥ): وأنشدني أبو علي |
| C36 | In the notes checked, "he, God have mercy on him" = al-Jawharī | S | Notes in kwn, Ebd, bny, brr, bky. Hml names الجوهري رحمه الله explicitly. (Outside notes, Eql uses it for Abū Ḥanīfa and Ibn Abī Laylā; the claim is restricted to the notes, so it holds) |
| C37 | A note's end is marked less reliably (qāla sometimes resumes, sometimes not); our English does not always show the seam | S | hdy 591: قال: وهدى واهتدى. ydy 1173: continues unmarked. The harmonized English of hdy puts "He notes hadā and ihtadā…" inside "The author's own note" |
| C38 | ydy excerpt, Arabic | S | Entry 1173. Validator passes |
| C39 | ydy excerpt, translation | S | Checked clause by clause. "also" in "Al-yad also means" is an acceptable addition |
| C40 | Up to "I say" is al-Jawharī: his entry lists strength among the senses of *yad* and cites Q 51:47 | S | Entry 1178: واليدُ: القوَّةُ. وأيَّدَهُ، أي قوَّاه … قال تعالى: (والسماءَ بَنيناها بأيْدٍ) |
| C41 | Rāzī's أ ي د defines *al-ayd* as strength | S | Entry 6722: و(الأيد) و(الآد) بالمد القوة |
| C42 | His evidence is al-Azharī plus the absence of agreement, and the second argument reports the limits of his reading | S | Entry 1173 text. The characterisation is the essayist's reasonable interpretation |
| C43 | The Q 9:29 sentence after the note is al-Jawharī's, unmarked | S | Entry 1178: وقوله تعالى: (حتَّى يُعْطوا الجزيةَ عن يَد) أي عن ذِلَّةٍ واستسلام |
| C44 | "The chapter of dāl" is a relic of the rhyme order. Al-Rāzī kept al-Jawharī's rhyme arrangement, which files roots by last letter [haywood p. 68][ima] | **NQ** (citation) | The claim is true. IMA: اتبع الترتيب المعجمي وفق نظام القافية. Khāṭir preface p. (د): أن الإمام الرازي جرى على أسلوب الجوهري في إيراد الكلم باعتبار أواخرها. Also Razi's own cross-reference "باب الألف اللينة" (Ebd note; intro p. 9). **But Haywood p. 68 only defines the rhyme order and credits it to al-Jawharī. Haywood mentions *Mukhtār* on pp. 75–76 and does not say what order it follows** |
| C45 | Some printings re-sort by first letter, including the 1999 Beirut edition our text matches | S | Shamela 23193 table of contents: حرف الهمزة، باب الباء … باب الياء (first-letter order). ع ذ ب sits early in باب العين (p. 203) |
| C46 | Khāṭir's edition was for Egypt's government schools, commissioned 1904 | S | 1916 title page (n4): قررت وزارة المعارف العمومية في ٢٥ شعبان سنة ١٣٢٢ (٣ نوفمبر سنة ١٩٠٤) طبع هذا الكتاب على نفقتها واستعماله بالمدارس الأميرية; عُني بترتيبه محمود خاطر بك; الطبعة الخامسة … ١٣٣٤–١٩١٦ |
| C47 | Khāṭir's preface: it dropped what "should not reach the ears of the young" (p. د) | S | Preface page headed (د) (IA n9): مع حذف ما لا ينبغي أن يطرق مسامع النشء بشرط المحافظة على أصل الكتاب |
| C48 | *wa-bābuhu* + model verb in "some 520 of the 877 entries" | **NQ** | Literal وبابه / وبابهما is in about 305–330 entries. About 520–545 entries contain *any* bāb model formula (وبابه, وبابهما, من باب نصر, etc.). The number is right only if "min bāb X" is included |
| C49 | …and in none of al-Jawharī's | S | The only وباب hits in al-Jawharī are *bāb* "door" (ErD, ftH, Enq, rfq, Ejm) |
| C50 | Twenty models in five classes, rare sixth class stated case by case (pp. 7–8) | S | Intro pp. 7–8: 7+5+2+4+2 = 20. الباب السادس … قليل لم نذكر له ميزانا … ننص على وزانه |
| C51 | "Its class is naṣara" = like naṣara, yanṣuru, naṣran in past, present and verbal noun (p. 9) | S | Intro p. 9: موازنا له في حركات ماضيه ومضارعه ومصدره |
| C52 | أ ي د: *āda … wa-bābuhu bāʿa* → āda, yaʾīdu, aydan | S | Entry 6722: (آد) الرجل … وبابه باع. Intro p. 8: باع يبيع بيعا. يئيد is given in ydy 1173 |
| C53 | Stated reason: copyists garble vowel marks, so he fixed forms in words (p. 10) | S | Intro p. 10: ألا يتطرق إليه بمرور الأيام تحريف النساخ … ضبطها بالشكل الذي يعكسه التبديل والتحريف عن قريب |
| C54 | He added nothing by analogy alone and left unstated what he could not find (p. 7) | S | Intro p. 7: إلا ما لم أجده … فإني قفوت أثره … لئلا أكون زائدا على الأصل شيئا بطريق القياس |
| C55 | hdy: Razi sheds verses of Zuhayr, Imruʾ al-Qays, al-Aʿshā and others, and rarer senses (bride-leading, swaying walk); keeps guidance, hady, conduct, gift | S | Entries 533 vs 591 (هداء the bride, تهادى gait, Zuhayr/Imruʾ al-Qays/al-Aʿshā/Ṭarafa/Mutalammis/Dhū l-Rumma present only in 533) |
| C56 | hdy excerpt Arabic and translation, including Q 1:6, 7:43, [38:22] | S | Entry 591. Q 38:22 is the correct locus of واهدنا إلى سواء الصراط (the reference is not in the Arabic; the essay brackets it) |
| C57 | "hadā and ihtadā have one meaning" is al-Jawharī's and directly follows the Ḥijāzī remark | S | Entry 533: … إلى الدار، حكاها الاخفش. وهدى واهتدى بمعنًى |
| C58 | ع ذ ب: our copy records only sweet water; al-Jawharī also has *al-ʿadhāb* "punishment"; not checked against a manuscript | S | Entries 580 and 238. Note: the printed 1999 ed. (Shamela p. 203) also has only: (العذب) الماء الطيب وبابه سهل |
| C59 | al-Jawharī often quotes earlier scholars such as al-Farrāʾ | S | Entry 533 (قال الفراء …), carried over into 591 |
| C60 | onOurSite: 877 roots displayed; more held but not shown | S | SQL: approved/displayed 877; deferred 607; pending 2 |
| C61 | hawramani pages name no edition | S | WebFetch of the dictionary page and the About page: no edition, editor or year named |
| C62 | Wording matches the 1999 Beirut ed. (5th printing) in every entry compared | S | ي د ي (Shamela pp. 348–49) and ع ذ ب (p. 203) match the stored text word for word |
| C63 | Formatting: fully vowelled; spaced root letters; headwords in parentheses; Qur'an in braces with [sūra: verse]; no page numbers; some one-line entries | S | Entries 1173, 591, 580. The Shamela page marker ⦗٣٤٩⦘ is absent from our stored ydy |
| C64 | Ḥājjī Khalīfa's bibliography is seventeenth-century | S | Shamela card: ت ١٠٦٧ هـ |

**Totals: 64 claims — 61 supported, 3 need qualification, 0 unsupported.**

## Flagged items and fixes

1. **C27, "al-Rāzī in at most one in twenty".**
   - Evidence: 55 of 856 shared entries (6.4%) quote verse once named-poet citations are counted. Examples: fyA, mkn, Ebd, xbv, ndd, Sdr, nwq, ESr, nfl.
   - Fix: change to "al-Rāzī in about one in sixteen", or "in fewer than one in ten". Or drop "at most" and say "in roughly one in twenty".
2. **C44, rhyme arrangement citation.**
   - Evidence: Haywood p. 68 supports only the definition of al-Jawharī's rhyme order. His only mention of *Mukhtār* (pp. 75–76) says nothing about its arrangement.
   - Fix: keep `[^ima]`. Replace or add a citation for the claim that al-Rāzī kept the order: `[^khatir-1916|preface, p. د]`, which says الرازي جرى على أسلوب الجوهري في إيراد الكلم باعتبار أواخرها. Keep `[^haywood|p. 68]` only for "files roots by their last letter".
3. **C48, "some 520 … wa-bābuhu".**
   - Evidence: the literal *wa-bābuhu / wa-bābuhumā* appears in about 320 entries. About 520–545 contain any *bāb* model formula (including *min bāb naṣara*).
   - Fix: "…runs through some 520 of the 877 entries we display…: *wa-bābuhu* ('and its class is') or *min bāb …* ('of the class of'), followed by a model verb."

## Brief issues (non-factual)

- **suggestion.** C58 ع ذ ب: add that the printed 1999 edition (p. 203) also has only the one line. That rules out a copying loss on our side. The open question is then only al-Rāzī versus the manuscript tradition.
- **suggestion.** "The note shows what the book offers a Qur'an reader: which constructions the Qur'an itself uses, and where" generalises from one note. Soften to "Notes like this show…".
- **suggestion.** Several "(our count)" statistics sit close together in "Who made it" and "Hearing the two voices", and they read a little like a data sheet. Consider keeping two of them and letting the examples carry the rest.
- **suggestion (site approach).** Al-Rāzī was a Ḥanafī jurist (Ziriklī), and at least one note comments on jurists' technical usage. In عمل, *qultu*: وقول الفقهاء ماء (مستعمل) قياس على هذا. One sentence noting that some notes record later scholarly and legal usage would help readers, but only if the root is linked and the note quoted accurately.
- The word count (1,096) is at the top of the range but not padded. No generic praise or ranking was found. The one value judgment ("best arranged…") is correctly attributed to al-Rāzī. Root mentions are all linked. Translations are labelled.

## URL check

| Source | Opens | Is the stated work | Supports cited locator |
|---|---|---|---|
| zirikli (shamela 12286/5120) | yes | yes, *al-Aʿlām*, 15th ed. 2002 | yes, vol. 6 p. 55. Footnote n. 1 is on Shamela page 5121, which is also labelled p. 55 |
| kashf (shamela 2118/1145) | yes | yes, Istanbul ed. | yes, p. 1073 |
| cairo-1911 (Wikisource) | yes | yes, title-page transcription | yes |
| razi-1999 (shamela 23193) | yes | yes, ed. Yūsuf al-Shaykh Muḥammad, 5th printing 1420/1999 | yes, pp. 7–10 |
| haywood (archive.org) | yes | yes, Haywood 1960 | p. 68 is only partial (see flag 2) |
| ima (malecso.org) | yes | yes, "1- مختار الصحاح لزين الدين الرازي (ت بعد 666هـ)", 10 March 2024 | yes |
| khatir-1916 (archive.org RZY1916AR) | yes | yes, arranged by Maḥmūd Khāṭir, 5th printing, Amīriyya 1334/1916 | yes, title page and p. (د) |
| hawramani | yes | yes | yes |

All listed sources were consulted, and none is unusable.

## Validator

`node scripts/validate-dictionary-guides.mjs mukhtar-al-sihah` passes (1/1). It found 10 root links (9 distinct pairs), 2 excerpts and 1,096 words.

## Site-data issues

- The stored year 1268 is a *terminus post quem* (he was alive in Konya in 666 AH / 1267–68 per Ziriklī), not a known death year. It is fine for ordering, but anywhere the UI labels it "d." it should read "d. after 1268" or similar. Shamela's card gives "ت ٦٦٦هـ", which likely rests on the same datum.
- The author label "Zayn al-Dīn al-Rāzī" is correct.
- hawramani's own blurb calls the source "Tāj al-Lugha" and al-Jawharī "the Persian philologist". This does not affect our stored data.
