# Verification round 2: Mukhtār al-Ṣiḥāḥ

Guide: `roots/frontend/src/content/dictionary-guides/guides/mukhtar-al-sihah.ts`
Verifier: independent fact-check, round 2. I did not open research-notes.md or any revision-*.md. I read verification-r1.md only for its list of flagged points.
Date: 2026-09-26

## Method

I opened every source myself with curl, and read page images where OCR was unreliable.

- **al-Ziriklī, *al-Aʿlām*** (Shamela 12286/5120 and 5121; both are headed ج6 ص55). I also checked the edition on the book card: Dār al-ʿIlm lil-Malāyīn, 15th ed., May 2002.
- ***Kashf al-ẓunūn*** (Shamela 2118/1144–1145; pp. 1072–73). I also checked the book card: Yaltkaya and Bilge, Istanbul 1941–43, and the author's death date (ت ١٠٦٧).
- **Arabic Wikisource, 1911 Cairo title page.** I read the rendered transcription.
- ***Mukhtār al-Ṣiḥāḥ*, 1999 Beirut edition** (Shamela 23193).
  - Book card and introduction: page ids 1–5, print pp. 7–10.
  - Entries: ع ذ ب (id 2175, p. 203), ي د ي (id 3753, p. 348), ع م ل (id 2284, p. 218).
  - Neighbouring page titles, to check the order of roots.
- **Khāṭir's 1916 edition** (IA RZY1916AR). I viewed the page images n4 (title page) and n9 (preface page headed (د)), and read the djvu OCR.
- **Haywood, *Arabic Lexicography*** (IA in.gov.ignca.12555). I read the djvu text for pp. 68–69 and 75–76.
- **ALECSO/IMA news note** (malecso.org), and the hawramani dictionary page and About page.

For site data I used `_dict_guide_tool.py entry …`. I also ran my own read-only SQL over quran.db, using the tool's display filter (approved, not hidden, harmonized_en non-empty). The scratch script recomputed every "(our count)" statistic.

I ran the validator.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Mukhtār al-Ṣiḥāḥ* / مختار الصحاح | S | Shamela 23193 card. Intro p. 7: وَسَمَّيْتُهُ (مُخْتَارَ الصِّحَاحِ). 1916 title page (n4) |
| C2 | titleGloss "Selections from al-Ṣiḥāḥ" | S | Intro p. 7: هَذَا مُخْتَصَرٌ … جَمَعْتُهُ مِنْ كِتَابِ الصِّحَاحِ; *mukhtār* = "selected" |
| C3 | Author: Zayn al-Dīn Abū ʿAbd Allāh Muḥammad b. Abī Bakr b. ʿAbd al-Qādir al-Rāzī, زين الدين الرازي | S | Shamela 23193 card: زين الدين أبو عبد الله محمد بن أبي بكر بن عبد القادر الحنفي الرازي. Ziriklī vol. 6 p. 55. Intro p. 7 gives the name in his own words |
| C4 | Period: completed 660 AH / 1262 CE | S | Kashf vol. 2 p. 1073: وافق فراغه عشية يوم الخميس غرة شهر رمضان ليلة الجمعة سنة ٦٦٠. Ziriklī: فرغ من تأليفه أول رمضان سنة ٦٦٠ |
| C5 | "a later date also circulates" | S | 1911 title page (Wikisource): وفي آخره وافق فراغه عشية يوم الجمعة سنة ستين وسبعمائة |
| C6 | d. after 666 AH / 1268 CE | S | Ziriklī: (٠٠٠ - بعد ٦٦٦ هـ = ٠٠٠ - بعد ١٢٦٨ م). IMA title: (ت بعد 666هـ) |
| C7 | kind "Abridgment of al-Ṣiḥāḥ" | S | Intro p. 7 (مختصر … من كتاب الصحاح) |
| C8 | Thirteenth century; commoner and Qur'anic vocabulary kept (summary, lede) | S | Intro p. 7: لِكَثْرَةِ اسْتِعْمَالِهِ وَجَرَيَانِهِ عَلَى الْأَلْسُنِ … خُصُوصًا أَلْفَاظَ الْقُرْآنِ الْعَزِيزِ وَالْأَحَادِيثِ النَّبَوِيَّةِ |
| C9 | Most poetry dropped (summary) | S | Own count (C27, C28) |
| C10 | Verb vowelling fixed by model verbs (summary) | S | Intro pp. 7–9 |
| C11 | Abridger's notes flagged "I say" (summary, lede) | S | Intro p. 7: فَكُلُّ مَوْضِعٍ مَكْتُوبٍ فِيهِ (قُلْتُ) فَإِنَّهُ مِنَ الْفَوَائِدِ الَّتِي زِدْتُهَا عَلَى الْأَصْلِ |
| C12 | Most of the text comes from someone other than the named author (lede) | S | Intro p. 7. Entry pairs Alh 556/109, ydy 1173/1178 and hdy 591/533 run in parallel |
| C13 | Lede quotation "especially the words of the Mighty Qur'an and the Prophetic ḥadīth" | S | Intro p. 7 |
| C14 | "…and cut the rest" (lede) | S | Intro p. 7: وَاجْتَنَبْتُ فِيهِ عَوِيصَ اللُّغَةِ وَغَرِيبَهَا طَلَبًا لِلِاخْتِصَارِ |
| C15 | The compiler is not Fakhr al-Dīn al-Rāzī | S | Different name (Muḥammad b. Abī Bakr b. ʿAbd al-Qādir) and different dates (fl. 660–666) in Ziriklī vol. 6 p. 55 |
| C16 | Ziriklī: Ḥanafī jurist, originally from Rayy, knew tafsīr and literature, last heard of in Konya in 666 (1267–68) | S | Ziriklī vol. 6 p. 55: وهو من فقهاء الحنفية، وله علم بالتفسير والأدب. أصله من الري … وكان في قونية سنة ٦٦٦ وهو آخر العهد به |
| C17 | His other books include Q&A on puzzling Qur'anic verses | S | Ziriklī: (أنموذج جليل في أسئلة وأجوبة من غرائب آي التنزيل - ط) |
| C18 | "The book's date is disputed" | S | C19–C21 together: 660 vs 760, and a published refutation of the eighth-century view |
| C19 | The Istanbul edition of Ḥājjī Khalīfa's 17th-century bibliography quotes the closing note as 1 Ramaḍān 660 (July 1262), vol. 2 p. 1073 | S | Shamela 2118/1145, headed ج2 - ص1073: وقال في آخره وافق فراغه … غرة شهر رمضان … سنة ٦٦٠. Card: Istanbul 1941–43; author d. 1067. 1 Ramaḍān 660 ≈ 19 July 1262 |
| C20 | The 1911 Cairo printing quotes the same work (Kashf) with 760 (1359) | S | Wikisource: قال في كشف الظنون … وفي آخره وافق فراغه عشية يوم الجمعة سنة ستين وسبعمائة; الطبعه الاولى بالمطبعة الكلية … سنة ١٣٢٩. 760 AH = Dec 1358 – Nov 1359, so "1359" is acceptable |
| C21 | Ziriklī cites ʿAbd Allāh Mukhliṣ's treatise refuting the eighth-century view (n. 1) | S | Shamela 12286/5121 (also headed p. 55), fn (1): عَبْد الله مُخْلِص في رسالة سماها (صاحب مختار الصحاح - ط) حقق فيها خطأ القول بأنه توفي سنة ٧٦١هـ أو أنه كان من رجال القرن الثامن |
| C22 | Arabic intro quotation (p. 7) | S | Verbatim against Shamela p. 7. The ellipsis omits لِكَثْرَةِ اسْتِعْمَالِهِ … فَالْأَهَمُّ. The 1916 OCR has the same text |
| C23 | Translation of the intro quotation, labelled "translation for this guide" | S | Accurate. "every scholar — jurist, ḥāfiẓ, …" is a defensible reading of لِكُلِّ عَالِمٍ فَقِيهٍ أَوْ حَافِظٍ … |
| C24 | Chose al-Jawharī as best arranged, best refined, easiest to consult, most widely used; framed as his judgment | S | p. 7: أَحْسَنَ أُصُولِ اللُّغَةِ تَرْتِيبًا وَأَوْفَرَهَا تَهْذِيبًا وَأَسْهَلَهَا تَنَاوُلًا وَأَكْثَرَهَا تَدَاوُلًا |
| C25 | Link to the al-Ṣiḥāḥ guide | S | Validator passes |
| C26 | 856 roots shown in both works | S | Own SQL: Rāzī 877, Jawharī 866, intersection 856 |
| C27 | Al-Jawharī quotes verse in about four in five | S | Own count: 699/856 = 82% (verse-marker plus named-poet heuristic) |
| C28 | **(r1 flag)** Al-Rāzī quotes verse in "fewer than one in ten" | S | Own count with the same heuristic: 57/856 = 6.7%. Round 1 found 40–55. Every method lands between 4.7% and 6.7%, so "fewer than one in ten" is safe |
| C29 | Al-Rāzī's text is about two-fifths as long | S | Own count: character ratio 0.41 over the 856 roots, vowel marks stripped |
| C30 | "Every place in which qultu is written …" and the notes' sources (Tahdhīb, other trusted sources, "what God opened to me") | S | p. 7: وَضَمَمْتُ إِلَيْهِ فَوَائِدَ كَثِيرَةً مِنْ تَهْذِيبِ الْأَزْهَرِيِّ، وَغَيْرِهِ مِنْ أُصُولِ اللُّغَةِ الْمَوْثُوقِ بِهَا وَمِمَّا فَتَحَ اللَّهُ تَعَالَى بِهِ عَلَيَّ |
| C31 | About a hundred of 877 entries contain such a note | S | 104 entries contain vowelled قُلْتُ. The unvowelled string gives 134, because it also catches *qulta* |
| C32 | At least a quarter of those notes concern a Qur'anic verse | S | 34 of 104 (33%) have a braced Qur'an quotation or تعالى within the note window (heuristic) |
| C33 | **(NEW)** ع م ل: the jurists' *māʾ mustaʿmal* "used water" can be justified only by analogy with al-Azharī's *istaʿmala al-labin* "he built with the bricks" | S | Entry 581, displayed: قُلْتُ: قَالَ الْأَزْهَرِيُّ: يُقَالُ: (اسْتَعْمَلَ) فُلَانٌ اللَّبِنَ إِذَا بَنَى بِهِ بِنَاءً. قُلْتُ: وَقَوْلُ الْفُقَهَاءِ مَاءٌ (مُسْتَعْمَلٌ) قِيَاسٌ عَلَى هَذَا وَإِلَّا فَلَا وَجْهَ لِصِحَّتِهِ غَيْرُ هَذَا الْقِيَاسِ. The stored text is identical to Shamela 23193/2284 (p. 218) once vowels and punctuation are ignored (327/327 letters) |
| C34 | **(NEW)** "One shows the jurist in him" | S | Light interpretation resting on Ziriklī (وهو من فقهاء الحنفية) and on a note about jurists' usage. Acceptable as framed |
| C35 | **(NEW)** "For him the legal term extends attested usage; it is not an instance of it" | S | A fair paraphrase of قِيَاسٌ عَلَى هَذَا وَإِلَّا فَلَا وَجْهَ لِصِحَّتِهِ غَيْرُ هَذَا الْقِيَاسِ. It is the essay's interpretation of a quoted note (see the plain-English suggestion below) |
| C36 | The vowel and pattern specifications are also his, unflagged | S | p. 7: وَكُلُّ مَا أَهْمَلَهُ الْجَوْهَرِيُّ … فَإِنِّي ذَكَرْتُهُ. The formulas appear without قلت, e.g. E*b 580: وَبَابُهُ سَهُلَ. Absent from al-Jawharī (C52) |
| C37 | The rest is al-Jawharī's substance, trimmed and sometimes reworded, including his "I" | S | Alh 556 vs 109: وَسَمِعْتُ أَبَا عَلِيٍّ النَّحْوِيَّ and وَأَنْشَدَنِي أَبُو عَلِيٍّ are in both |
| C38 | In إ ل ه, *anshadanī Abū ʿAlī* is al-Jawharī, as his own entry shows | S | Entry 109: وأنشدني أبو علي: تروحنا من اللعباء قصرا … |
| C39 | In the notes checked, "he, God have mercy on him" = al-Jawharī | S | grep: kwn, Ebd, bny, brr, bky (inside قلت notes, referring to al-Jawharī's own text); Hml names الجوهري رحمه الله. Eql (Abū Ḥanīfa, Ibn Abī Laylā) sits outside a note, so the restriction to notes holds |
| C40 | A note's end is marked less reliably than its start; *qāla* sometimes resumes, sometimes the text just carries on; al-Jawharī's entry is the surest check | S | hdy 591: … قَالَ: وَهَدَى وَ(اهْتَدَى) بِمَعْنًى. ydy 1173: وَقَوْلُهُ تَعَالَى {حَتَّى يُعْطُوا …} follows unmarked. 1999 ed. p. 11 (id 6): قُلْتُ: … قَالَ: وَهِيَ ضَرْبَانِ |
| C41 | ydy excerpt, Arabic | S | Entry 1173. Validator passes. Stored text identical to Shamela 23193/3753 (p. 348; 866/866 letters) |
| C42 | ydy excerpt, translation | S | Checked clause by clause. Accurate. "also" in "Al-yad also means" is a harmless addition given the ellipsis |
| C43 | Up to "I say" this is al-Jawharī: his entry lists "strength" among the senses of *yad* and cites the verse for it | S | Entry 1178: واليدُ: القوَّةُ. وأيَّدَهُ، أي قوَّاه. ومالى بفلان يدان، أي طاقةٌ. قال تعالى: (والسماءَ بَنيناها بأيْدٍ) |
| C44 | Al-Rāzī keeps the meaning but disputes the origin; his أ ي د defines *al-ayd* as strength | S | ydy 1173 note. Ayd 6722: وَ(الْأَيْدُ) وَ(الْآدُ) بِالْمَدِّ الْقُوَّةُ |
| C45 | His evidence is al-Azharī plus the absence of agreement; the second reports only the limits of his reading | S | Entry 1173: وَقَدْ نَصَّ الْأَزْهَرِيُّ … وَلَا أَعْرِفُ أَحَدًا …. The characterisation is a reasonable interpretation |
| C46 | The Q 9:29 sentence after the note is al-Jawharī's, unmarked | S | Entry 1178: وقوله تعالى: (حتَّى يُعْطوا الجزيةَ عن يَد) أي عن ذِلَّةٍ واستسلام، ويقال: نَقداً لا نسيئةً (al-Rāzī rewords the second gloss as وقيل) |
| C47 | **(r1 flag)** "The chapter of dāl" is a relic; al-Rāzī kept al-Jawharī's rhyme arrangement [ima][khatir-1916 preface p. د] | S | IMA: وسار فيه على منوال صاحب الأصل … فاتبع الترتيب المعجمي وفق نظام القافية. Khāṭir preface, page image n9 headed (د): وجلي أن الإمام الرازي جرى على أسلوب الجوهري في إيراد الكلم باعتبار أواخرها. Citations now placed correctly |
| C48 | Rhyme order files roots by their last letter [haywood p. 68] | S | Haywood p. 68: "the rhyme arrangement, by which roots were listed according to their final radicals"; credit for it "usually given to al-Jauhari" |
| C49 | The 1999 Beirut edition, which our text matches, re-sorts by first letter [razi-1999] | S | Shamela sequence: ع د ا (id 2174), ع ذ ب (2175), ع ذ ر (2176), all p. 203. باب الياء at p. 348 (id 3748) opens with ي ب س, ي ت م, ي د ي. First-letter order |
| C50 | Khāṭir's edition for government schools (commissioned 1904); preface says it dropped what "should not reach the ears of the young" | S | Title page n4: عُني بترتيبه محمود خاطر بك; قررت وزارة المعارف العمومية في ٢٥ شعبان سنة ١٣٢٢ (٣ نوفمبر سنة ١٩٠٤) طبع هذا الكتاب على نفقتها واستعماله بالمدارس الأميرية; الطبعة الخامسة … ١٣٣٤–١٩١٦. Preface p. (د): على اعتبار الحرف الأول والثاني … مع حذف ما لا ينبغي أن يطرق مسامع النشء |
| C51 | **(r1 flag)** "Some 520 of the 877 entries": *wa-bābuhu* or *min bāb* plus a model verb | S | Own count: 303 entries have وبابه/-هما/-ها/-هن; 284 have من باب; 526 have either. Restricted to a following model verb (ضرب، نصر، طرب، دخل، قطع، قال، رد، باع، ظرف، فهم، وعد، رمى، جلس، خضع، سلم، صدي، عدا، سهل، سما، كتب …), 518. So "some 520" holds |
| C52 | …and through none of al-Jawharī's | S | 0 of 866 al-Jawharī entries have وبابه or من باب followed by a model verb |
| C53 | Wherever al-Jawharī had not said how a triliteral verb or its maṣdar is vowelled, al-Rāzī supplied it, by naming vowels or by one of twenty models in five classes (pp. 7–8) | S | pp. 7–8: 7 + 5 + 2 + 4 + 2 = 20 models in classes 1–5. The sixth class has no model (هُوَ قَلِيلٌ لَمْ نَذْكُرْ لَهُ مِيزَانًا). "Wherever" is qualified two sentences later (C57), as the intro itself qualifies it |
| C54 | "Its class is naṣara" = like naṣara, yanṣuru, naṣran in past, present and verbal noun (p. 9) | S | p. 9: مُوَازِنًا لَهُ فِي حَرَكَاتِ مَاضِيهِ وَمُضَارِعِهِ وَمَصْدَرِهِ; p. 7: نَصَرَ يَنْصُرُ نَصْرًا |
| C55 | أ ي د: *āda … wa-bābuhu bāʿa* → āda, yaʾīdu, aydan, like bāʿa, yabīʿu, bayʿan | S | Entry 6722: (آدَ) الرَّجُلُ اشْتَدَّ وَقَوِيَ وَبَابُهُ بَاعَ. p. 8: بَاعَ يَبِيعُ بَيْعًا. ydy 1173: آدَ يَئِيدُ |
| C56 | Stated reason: copyists soon garble vowel marks, so he fixed forms in words (p. 10) | S | p. 10: وَأَلَّا يَتَطَرَّقَ إِلَيْهِ بِمُرُورِ الْأَيَّامِ تَحْرِيفُ النُّسَّاخِ … بِالشَّكْلِ الَّذِي يَعْكِسُهُ التَّبْدِيلُ وَالتَّحْرِيفُ عَنْ قَرِيبٍ |
| C57 | Nothing added by analogy alone; what he could not find he left unstated, as al-Jawharī had (p. 7) | S | p. 7: إِلَّا مَا لَمْ أَجِدْهُ … فَإِنِّي قَفَوْتُ أَثَرَهُ … لِئَلَّا أَكُونَ زَائِدًا عَلَى الْأَصْلِ شَيْئًا بِطَرِيقِ الْقِيَاسِ |
| C58 | ه د ي: al-Rāzī sheds verses by Zuhayr, Imruʾ al-Qays, al-Aʿshā and others, and the senses of bride-leading and swaying walk; keeps guidance, *hady*, conduct, *hadiyya* | S | Entry 533 has هِداء (Zuhayr), الهاديات (Imruʾ al-Qays), تهادى (al-Aʿshā; also Ṭarafa, al-Mutalammis, Dhū l-Rumma). Entry 591 has none of them, and keeps الهدى، الهدي، هديته (سيرته)، الهدية، التهادي |
| C59 | hdy excerpt, Arabic | S | Entry 591. Validator passes |
| C60 | hdy excerpt, translation, including Q 1:6, 7:43, [38:22] | S | Accurate. مُعَدًّى بِنَفْسِهِ = "taking its object directly". Q 38:22 is the correct place for وَاهْدِنَا إِلَى سَوَاءِ الصِّرَاطِ. The bracket shows the reference is not in the Arabic |
| C61 | "hadā and ihtadā have one meaning" is al-Jawharī's and follows the remark on Ḥijāzī usage | S | Entry 533: هذه لغة أهل الحجاز، وغيرهم يقول: هديته إلى الطريق وإلى الدار، حكاها الاخفش. وهدى واهتدى بمعنًى |
| C62 | **(NEW in part)** ع ذ ب: our copy has only sweet water, as does the 1999 edition (p. 203); al-Jawharī also has *al-ʿadhāb* "punishment"; not checked against a manuscript | S | Entry 580: ع ذ ب : (الْعَذْبُ) الْمَاءُ الطَّيِّبُ وَبَابُهُ سَهُلَ. Shamela 23193/2175, headed ص203 – ع ذ ب: identical single line. Entry 238: والعذاب: العقوبة |
| C63 | Much is al-Jawharī quoting still earlier scholars such as al-Farrāʾ; the book's date is not the date of its evidence | S | Entry 533: قال الفراء: يريد لا يهتدي. Carried into 591: قَالَ الْفَرَّاءُ: مَعْنَاهُ لَا يَهْتَدِي |
| C64 | onOurSite: 877 roots displayed; more entries held but not shown | S | SQL: approved/displayed 877, deferred 607, pending 2 |
| C65 | hawramani pages name no edition | S | Dictionary page and About page (curl): no editor, publisher, year or edition named |
| C66 | Wording matches the 1999 Beirut ed. (5th printing, ed. Yūsuf al-Shaykh Muḥammad) in every entry compared | S | I compared ydy (866/866 letters), Eml (327/327) and E*b (one line). All are identical once vowels and punctuation are ignored. The card: المحقق يوسف الشيخ محمد … الطبعة الخامسة ١٤٢٠هـ/١٩٩٩م |
| C67 | Formatting: fully vowelled; root letters spaced; headwords in parentheses; Qur'an in braces, usually with [sūra: verse]; no page numbers; some one-line entries | S | Entries 1173, 591, 580. The Shamela page marker ⦗٣٤٩⦘ is absent from the stored ydy. hdy's {وَاهْدِنَا إِلَى سَوَاءِ الصِّرَاطِ} has no bracket, so "usually" is right |
| C68 | Al-Rāzī's notes begin with قُلْتُ; in the English versions, check the Arabic for where a note ends | S | Intro p. 7. The harmonised English of hdy folds the resumed al-Jawharī sentence into the note |

**Totals: 68 claims. 68 supported, 0 need qualification, 0 unsupported.**

## Round-1 flags: status

1. **C27 → C28, verse share.** Fixed. The essay now says "fewer than one in ten". My count is 6.7%.
2. **C44 → C47/C48, rhyme-order citation.** Fixed. `[^ima][^khatir-1916|preface, p. د]` now carries "kept the arrangement". `[^haywood|p. 68]` carries only the definition, which p. 68 does state.
3. **C48 → C51, bāb formula.** Fixed. *min bāb* is now included. My count is 518–526.

## New claims introduced in revision: status

- **ع ذ ب, 1999 ed. p. 203, one line.** Confirmed on Shamela 23193/2175.
- **ع م ل qultu note on *māʾ mustaʿmal*.** Confirmed on displayed entry 581 and on the 1999 ed. p. 218 (identical). The quotation and gloss are accurate.
- **"One shows the jurist in him".** Rests on Ziriklī, confirmed.
- **"extends attested usage; not an instance of it".** A fair interpretation of the note.
- **Bāb count 522.** Confirmed at 518–526.
- **Khāṭir preface p. (د).** Confirmed on page image n9, which carries the (د) header.
- **`[^razi-1999]` for first-letter order.** Confirmed from page sequence and titles.

## Flagged items and fixes

None. Every claim is supported.

## Brief issues (non-factual)

- **suggestion. Date consistency.** `period` says "d. after 666 AH / 1268 CE", while the body says "666 AH (1267–68 CE)". Both are defensible: Ziriklī prints ١٢٦٨, and 666 AH spans Sept 1267 – Sept 1268. Consider "1267–68" in `period` so the header and body agree.
- **suggestion. The abstract sentence in ع م ل.** "For him the legal term extends attested usage; it is not an instance of it" is correct but abstract for a general reader. A plainer version: "In other words, he treats the jurists' phrase as an extension by analogy, not as something the Arabs were recorded saying about water."
- **suggestion, optional. Manuscript.** The IMA note reports an author's copy (نسخة المؤلف) at Murad Molla, Istanbul, no. 1816, 404 folios. The ع ذ ب limitation sentence could say that this copy exists but was not consulted, so the question is checkable in principle. The sentence is accurate as it stands. Only add this if space allows; lede plus body is exactly 1,100 words.
- **Word count and statistics.** Lede plus body is 1,100 words, the top of the range. Nothing should be added without a matching cut. The statistics paragraph in "Who made it" is still dense, but acceptable now that the "Hearing the two voices" statistics are trimmed.
- **No must-fix issues.**
  - No generic praise or ranking. "best arranged…" is attributed to al-Rāzī and marked "his judgment, not ours".
  - Every root mention is linked. Comparisons link both dictionaries (ydy, hdy, E*b, Alh).
  - Translations are labelled.
  - The page does not force an "original root meaning" narrative.
  - Nothing is promised that the site doesn't show.

## URL check

| Source | Opens | Is the stated work | Supports cited locator |
|---|---|---|---|
| zirikli (shamela 12286/5120) | yes | yes, *al-Aʿlām*, 15th ed., May 2002 | yes, vol. 6 p. 55. n. 1 is on Shamela 5121, also headed p. 55 |
| kashf (shamela 2118/1145) | yes | yes, Istanbul ed. (Yaltkaya & Bilge, 1941–43) | yes, p. 1073 (the entry starts at p. 1072, id 1144) |
| cairo-1911 (Wikisource) | yes (HTTP 200) | yes, title-page transcription, al-Maṭbaʿa al-Kulliyya 1329 | yes |
| razi-1999 (shamela 23193) | yes | yes, ed. Yūsuf al-Shaykh Muḥammad, 5th printing 1420/1999 | yes: pp. 7–10 (ids 2–5), p. 203 (id 2175), p. 218 (id 2284), p. 348 (id 3753) |
| haywood (archive.org in.gov.ignca.12555) | yes | yes, Haywood, *Arabic Lexicography*, 1960 | yes, p. 68 for the definition of the rhyme order |
| ima (malecso.org) | yes (200) | yes, "1- مختار الصحاح لزين الدين الرازي (ت بعد 666هـ)", 10 March 2024 | yes (نظام القافية) |
| khatir-1916 (archive.org RZY1916AR) | yes | yes, arranged by Maḥmūd Khāṭir, 5th printing, Amīriyya 1334/1916 | yes, title page (n4) and p. (د) (n9) |
| hawramani | yes (200) | yes | yes |

All listed sources were consulted. None is unusable.

## Validator

`node scripts/validate-dictionary-guides.mjs mukhtar-al-sihah` gives **ok (1/1 guides pass)**. It found 11 root links (10 distinct root/dictionary pairs) and 2 excerpts. Lede plus body is 1,100 words. Example roots: Eml, Alh, ydy, Ayd, hdy, E*b.

## Site-data issues

- **Stored year 1268.** This is a *terminus post quem* (alive in Konya in 666 AH per Ziriklī), not a death year. The work itself was completed in 660/1262. The panel shows "1268 CE" with no "d.", so nothing is mislabelled. It is fine for ordering, but should not be read as a death date.
- **Author label.** "Zayn al-Dīn al-Rāzī" is correct.
- **Unrelated data gap.** Al-Jawharī's displayed أ ي د entry (id 6727) is a fragment: `[أيد] أبو زيد:` with nothing after it. This guide does not link it.
