# Mukhtār al-Ṣiḥāḥ — research notes (drafting agent, 2026-09-26)

Guide: `roots/frontend/src/content/dictionary-guides/guides/mukhtar-al-sihah.ts`
Site dictionary slug: `zayn-al-din-al-razi-mukhtar-al-sihah` (877 displayed roots; site date 1268; author label "Zayn al-Dīn al-Rāzī").

All Arabic below was copied from the pages named. Translations are mine unless stated.

---

## 1. What the site displays

- `_dict_guide_tool.py dicts` → "Mukhtār al-Ṣiḥāḥ | مختار الصحاح | Zayn al-Dīn al-Rāzī (site date 1268) | lang=ar | displayed entries=877".
- Read-only DB count (sqlite3 -readonly): approved+shown 877; `deferred` 607; `pending` 2 (total 1,486 collected). The 607 were deferred by the site's own selection pass (`roots/backend/_dict_defer_redundant.py`, docstring: Mukhtār ranked last among general dictionaries "because it is a pure abridgment of al-Sihah"). So a root with no Mukhtār panel entry may still have an entry in the book. Guide says only: "more of his entries are held in our data but not yet shown".
- Stored-text peculiarities (observed in `entry` output):
  - Root heading = spaced letters + colon: `ي د ي :`, `ع ذ ب :`.
  - Fully vowelled; headwords/forms being defined in parentheses: `(الْيَدُ)`, `(أَيَّدَهُ)`.
  - Qur'an quotations in braces `{…}` followed by `[sura-name: n]` in Western digits (Shamela has Arabic-Indic digits). One verse reference present in Shamela is absent in ours: hdy `{وَاهْدِنَا إِلَى سَوَاءِ الصِّرَاطِ}` has `[ص: ٢٢]` on Shamela, none in our copy.
  - No page numbers (Shamela shows ⦗n⦘ page markers; stored text has none — grep for ⦗ returned 0).
  - Very short entries: e.g. E*b 57 chars, trf 46, *qn 50, SrT 61. Very long: ErD 4,920 chars, Hml 4,026.
  - `قُلْتُ:` (vocalised, damma on tāʾ) occurs 116 times in 101 of the 877 displayed entries; `قُلْتَ` ("you say", fatha) 46 times — the vowelling distinguishes them. Check: for every `قُلْتُ:` occurrence, the next 18 unvowelled letters were searched in the al-Ṣiḥāḥ entry for the same root; 0 matches → none of these notes is al-Jawharī's text.
  - Of those 101 entries, 25 have a Qur'anic quotation `{` within 200 characters after `قُلْتُ:` (heuristic; lower bound) → "at least a quarter".
  - Sources named within 400 chars after `قُلْتُ:`: al-Azharī/al-Tahdhīb 36; al-Jawharī / "raḥimahu llāh" 9; Sībawayh 2; Thaʿlab/al-Faṣīḥ 2; al-Zamakhsharī/al-Mufaṣṣal 2; Dīwān al-Adab 1; al-Mujmal 1 → "the source his notes name most often is al-Azharī".
- Comparison stats (roots displayed in BOTH Mukhtār and al-Ṣiḥāḥ: 856):
  - Entries with verse markers: al-Ṣiḥāḥ 678 (regex `\*|الشاعر|أنشد|الراجز`, ≈79%); Mukhtār 46 (regex `\.\.\.|الشاعر|أنشد|الراجز`, ≈5%, an upper bound — e.g. `$Er` matches the word الشاعر "poet" in a definition). → "about four entries in five" vs "about one in twenty".
  - Total unvowelled characters: Mukhtār 432,751 vs al-Ṣiḥāḥ 1,062,123 → ratio 0.41 → "about two-fifths the length".

### Which edition does the stored text follow?
- hawramani pages checked: https://arabiclexicon.hawramani.com/عذب/ ; dictionary page https://arabiclexicon.hawramani.com/zayn-al-din-al-razi-mukhtar-al-sihah/ ; https://arabiclexicon.hawramani.com/about/ — no statement of edition or source text found. Hawramani labels the work "Zayn al-Dīn al-Razī, Mukhtār al-Ṣiḥāḥ (d. 1266 CE)".
- al-Maktaba al-Shāmila book 23193 (https://shamela.ws/book/23193): card = "المؤلف: زين الدين أبو عبد الله محمد بن أبي بكر بن عبد القادر الحنفي الرازي (ت ٦٦٦هـ) — المحقق: يوسف الشيخ محمد — الناشر: المكتبة العصرية - الدار النموذجية، بيروت - صيدا — الطبعة: الخامسة، ١٤٢٠هـ / ١٩٩٩م — عدد الصفحات: ٣٥٠ — [ترقيم الكتاب موافق للمطبوع]". Arranged by first letter (TOC: حرف الهمزة, باب الباء, … باب الياء).
- Word-for-word comparison (vowels included) of stored text vs Shamela for: ع ذ ب (Shamela 23193/2175, p. 203: "ع ذ ب: (الْعَذْبُ) الْمَاءُ الطَّيِّبُ وَبَابُهُ سَهُلَ." — identical one-line entry), ش ي أ (23193/1852, p. 171 — identical), ه د ي (23193/3482, p. 325 — identical except missing [ص: ٢٢]), أ م ر (23193/176, pp. 21–22 — identical; page break ⦗٢٢⦘ inside al-Rāzī's note), ي د ي (23193/3753, pp. 348–349 — identical; break ⦗٣٤٩⦘ before كَرَحَيَانِ).
- Conclusion for guide: stored text matches the Yūsuf al-Shaykh Muḥammad edition (5th printing 1999) as digitised on Shamela in every entry checked; hawramani names no source. NOT claimed: that hawramani took it from Shamela.
- Side observation: the 1999 edition contains cross-reference lines such as "يَرْبُوعٌ فِي ر ب ع" (Shamela 23193/3754, p. 349) — the kind of pointer Khāṭir's preface describes (see §4). Not used in guide.

---

## 2. Author and dates

| Claim | Source | Passage |
|---|---|---|
| Full name Zayn al-Dīn Muḥammad ibn Abī Bakr ibn ʿAbd al-Qādir al-Rāzī; author of Mukhtār al-Ṣiḥāḥ | al-Ziriklī, *al-Aʿlām*, 15th ed. (Dār al-ʿIlm lil-Malāyīn, 2002), vol. 6, p. 55 — https://shamela.ws/book/12286/5120 | "الرَّازي (٠٠٠ - بعد ٦٦٦ هـ = ٠٠٠ - بعد ١٢٦٨ م) محمد بن أبي بكر بن عبد القادر الرازيّ، زين الدين: صاحب (مختار الصحاح - ط) في اللغة" |
| Kunya Abū ʿAbd Allāh | Shamela card (above); Institute of Arabic Manuscripts note (below) | "زين الدين أبو عبد الله محمد بن أبي بكر…" |
| Ḥanafī jurist, knowledge of tafsīr and adab; origin Rayy; visited Egypt and Syria; in Konya in 666, last trace | al-Ziriklī vi, 55 | "وهو من فقهاء الحنفية، وله علم بالتفسير والأدب. أصله من الري. زار مصر والشام، وكان في قونية سنة ٦٦٦ وهو آخر العهد به" |
| Completed the Mukhtār 1 Ramaḍān 660 | al-Ziriklī vi, 55 | "فرغ من تأليفه أول رمضان سنة ٦٦٠ هـ" |
| Other works include a Q&A book on puzzling Qur'anic verses (*Anmūdhaj jalīl…*) | al-Ziriklī vi, 55 (continues to 5121); Shamela author page https://shamela.ws/author/896 lists the printed book | "و (أنموذج جليل في أسئلة وأجوبة من غرائب آي التنزيل - ط)" |
| Dating dispute: an 8th-century dating (d. 761) was refuted by ʿAbd Allāh Mukhliṣ | al-Ziriklī vi, 55 n. 1 (https://shamela.ws/book/12286/5121) | "(١) عَبْد الله مُخْلِص في رسالة سماها (صاحب مختار الصحاح - ط) حقق فيها خطأ القول بأنه توفي سنة ٧٦١هـ أو أنه كان من رجال القرن الثامن." |
| Kashf al-Ẓunūn (Istanbul ed.) reports the colophon: Thursday evening, 1 Ramaḍān, eve of Friday, 660 | Ḥājjī Khalīfa, *Kashf al-ẓunūn*, ed. Yaltkaya & Bilge (Istanbul 1941–43), vol. 2, pp. 1072–73 — https://shamela.ws/book/2118/1144 and /1145 | "واختصره الشيخ الإمام محمد بن أبي بكر بن عبد القادر الرازي المتوفى بعد سنة … وسماه مختار الصحاح واقتصر فيه على ما لا بد منه في الاستعمال وضم إليه كثيراً من تهذيب الأزهري وغيره وصدر فوائده بقلت … وقال في آخره وافق فراغه عشية يوم الخميس غرة شهر رمضان ليلة الجمعة سنة ٦٦٠ ستين وستمائة." |
| A 1911 Cairo printing quotes Kashf with 760 | *Mukhtār al-Ṣiḥāḥ* (Cairo: al-Maṭbaʿa al-Kulliyya, 1329/1911), title page, transcribed on Arabic Wikisource — https://ar.wikisource.org/wiki/مختار_الصحاح_(المطبعة_الكلية،_1911) ; same printing scanned: https://archive.org/details/mukhtrali00jawhuoft | "قال في كشف الظنون عند الكلام على صحاح الجوهري واختصره الشيخ الامام محمد بن ابى بكر بن عبد القادر الرازي و سماه مختار الصحاح وهو مشهور متداول بين الناس وفي آخره وافق فراغه عشية يوم الجمعة سنة ستين وسبعمائة" |
| Conversions: 1 Ramaḍān 660 ≈ 20 July 1262 (Julian); 666 AH = Sept 1267–Sept 1268; 760 AH ≈ 1359 | tabular Hijri calculation (my own) | — |
| Author's autograph copy: Murad Molla (Istanbul) 1816, 404 folios; headings and entries in red | Institute of Arabic Manuscripts (ALECSO), "1- مختار الصحاح لزين الدين الرازي (ت بعد 666هـ)", 10 March 2024 — https://www.malecso.org/2024/03/10/نشرة-1 | "وتحتفظ مكتبة مراد ملا (إستانبول) بنسخة المؤلف تحت رقم (1816)، وهي تقع في (404) ورقة … وقد كتبت عناوين الأبواب والفصول والمداخل بالحمرة." (Not used in guide.) |
| The Mukhtār followed al-Jawharī's rhyme (qāfiya) arrangement | same Institute note | "وسار فيه على منوال صاحب الأصل إسماعيل بن حماد الجوهري فاتبع الترتيب المعجمي وفق نظام القافية" |
| Al-Azharī (d. 370) author of Tahdhīb al-Lugha | same Institute note | "من (تهذيب اللغة) للأزهري (ت370هـ)" (date not used in guide) |

Not Fakhr al-Dīn al-Rāzī: established by the different full name in al-Ziriklī (Muḥammad b. Abī Bakr b. ʿAbd al-Qādir). Guide says only that he is "not the theologian Fakhr al-Dīn al-Rāzī" and that the nisba points to Rayy (al-Ziriklī: "أصله من الري"). Note: some online uploads misattribute the Mukhtār to Abū Bakr Muḥammad ibn Zakariyyāʾ al-Rāzī (e.g. archive.org items "elshandawily10310/10313") — evidence the confusion exists; not cited in guide.

Site date: the stored 1268 corresponds to al-Ziriklī's "after 666 AH = after 1268 CE" — a terminus post quem, not a death date. Hawramani's "d. 1266 CE" matches no source found. → siteDataIssues.

---

## 3. The author's introduction (primary source)

Edition: ed. Yūsuf al-Shaykh Muḥammad, 5th printing 1999, pp. 7–10, via Shamela 23193/2 (p. 7), /3 (p. 8), /4 (p. 9), /5 (p. 10). The same introduction is printed (OCR, lower quality) in the 1916 Khāṭir printing (archive.org RZY1916AR).

- p. 7, purpose and base text:
  "هَذَا مُخْتَصَرٌ فِي عِلْمِ اللُّغَةِ جَمَعْتُهُ مِنْ كِتَابِ الصِّحَاحِ لِلْإِمَامِ … أَبِي نَصْرٍ إِسْمَاعِيلَ بْنِ حَمَّادٍ الْجَوْهَرِيِّ …، لَمَّا رَأَيْتُهُ أَحْسَنَ أُصُولِ اللُّغَةِ تَرْتِيبًا وَأَوْفَرَهَا تَهْذِيبًا وَأَسْهَلَهَا تَنَاوُلًا وَأَكْثَرَهَا تَدَاوُلًا، وَسَمَّيْتُهُ (مُخْتَارَ الصِّحَاحِ)"
  → Translation: "This is an abridgment in the science of language which I gathered from the book *al-Ṣiḥāḥ* of … Abū Naṣr Ismāʿīl ibn Ḥammād al-Jawharī, since I saw it to be the best of the sources of the language in arrangement, the fullest in refinement, the easiest to consult and the most widely circulated; and I named it *Mukhtār al-Ṣiḥāḥ*."
- p. 7, audience and selection:
  "وَاقْتَصَرْتُ فِيهِ عَلَى مَا لَا بُدَّ لِكُلِّ عَالِمٍ فَقِيهٍ، أَوْ حَافِظٍ، أَوْ مُحَدِّثٍ، أَوْ أَدِيبٍ مِنْ مَعْرِفَتِهِ وَحِفْظِهِ: لِكَثْرَةِ اسْتِعْمَالِهِ وَجَرَيَانِهِ عَلَى الْأَلْسُنِ مِمَّا هُوَ الْأَهَمُّ فَالْأَهَمُّ خُصُوصًا أَلْفَاظَ الْقُرْآنِ الْعَزِيزِ وَالْأَحَادِيثِ النَّبَوِيَّةِ ; وَاجْتَنَبْتُ فِيهِ عَوِيصَ اللُّغَةِ وَغَرِيبَهَا طَلَبًا لِلِاخْتِصَارِ وَتَسْهِيلًا لِلْحِفْظِ."
  → Translation used in guide (quoted in the blockquote).
  Note: "حافظ" rendered "ḥāfiẓ (a memoriser of texts)" — the word is ambiguous (Qur'an memoriser / ḥadīth ḥāfiẓ); gloss kept general.
- p. 7, additions and the قلت convention:
  "وَضَمَمْتُ إِلَيْهِ فَوَائِدَ كَثِيرَةً مِنْ تَهْذِيبِ الْأَزْهَرِيِّ، وَغَيْرِهِ مِنْ أُصُولِ اللُّغَةِ الْمَوْثُوقِ بِهَا وَمِمَّا فَتَحَ اللَّهُ تَعَالَى بِهِ عَلَيَّ، فَكُلُّ مَوْضِعٍ مَكْتُوبٍ فِيهِ (قُلْتُ) فَإِنَّهُ مِنَ الْفَوَائِدِ الَّتِي زِدْتُهَا عَلَى الْأَصْلِ."
- p. 7, patterns supplied; no analogy:
  "وَكُلُّ مَا أَهْمَلَهُ الْجَوْهَرِيُّ مِنْ أَوْزَانِ مَصَادِرِ الْأَفْعَالِ الثُّلَاثِيَّةِ الَّتِي ذَكَرَ أَفْعَالَهَا وَمِنْ أَوْزَانِ الْأَفْعَالِ الثُّلَاثِيَّةِ الَّتِي ذَكَرَ مَصَادِرَهَا فَإِنِّي ذَكَرْتُهُ إِمَّا بِالنَّصِّ عَلَى حَرَكَاتِهِ أَوْ بَرَدِّهِ إِلَى وَاحِدٍ مِنَ الْمَوَازِينِ الْعِشْرِينَ … إِلَّا مَا لَمْ أَجِدْهُ مِنْ هَذَيْنِ النَّوْعَيْنِ فِي أُصُولِ اللُّغَةِ الْمَوْثُوقِ بِهَا …، فَإِنِّي قَفَوْتُ أَثَرَهُ … فِي ذِكْرِهِ مُهْمَلًا لِئَلَّا أَكُونَ زَائِدًا عَلَى الْأَصْلِ شَيْئًا بِطَرِيقِ الْقِيَاسِ، بَلْ كُلُّ مَا زِدْتُهُ فِيهِ نَقَلْتُهُ مِنْ أُصُولِ اللُّغَةِ الْمَوْثُوقِ بِهَا."
- pp. 7–8, the six verb classes and twenty models: Bāb 1 faʿala yafʿulu — نَصَرَ، دَخَلَ، كَتَبَ، رَدَّ، قَالَ، عَدَا، سَمَا (7); Bāb 2 faʿala yafʿilu — ضَرَبَ، جَلَسَ، بَاعَ، وَعَدَ، رَمَى (5); Bāb 3 faʿala yafʿalu — قَطَعَ، خَضَعَ (2); Bāb 4 faʿila yafʿalu — طَرِبَ، فَهِمَ، سَلِمَ، صَدِيَ (4); Bāb 5 faʿula yafʿulu — ظَرُفَ، سَهُلَ (2); Bāb 6 faʿila yafʿilu (وَثِقَ يَثِقُ) — "وَهُوَ قَلِيلٌ لَمْ نَذْكُرْ لَهُ مِيزَانًا … بَلْ حَيْثُ جَاءَ فِي الْكِتَابِ نَنُصُّ عَلَى وِزَانِهِ" (p. 8). Total 20 → "twenty model verbs in five classes, with a rare sixth class stated case by case".
- p. 9, meaning of "it is of the class of X":
  "وَالْتَزَمْنَا فِي الْمَوَازِينِ أَنَّا مَتَى قُلْنَا فِي فِعْلٍ مِنَ الْأَفْعَالِ إِنَّهُ مِنْ بَابِ ضَرَبَ أَوْ نَصَرَ … فَإِنَّهُ يَكُونُ مُوَازِنًا لَهُ فِي حَرَكَاتِ مَاضِيهِ وَمُضَارِعِهِ وَمَصْدَرِهِ أَيْضًا"
- p. 9–10, nouns: "وَأَمَّا الْأَسْمَاءُ فَإِنَّا ضَبَطْنَا كُلَّ اسْمٍ يُشْتَبَهُ … إِمَّا بِذِكْرِ مِثَالٍ مَشْهُورٍ عَقِيبَهُ، وَإِمَّا بِالنَّصِّ عَلَى حَرَكَاتِ حُرُوفِهِ … وَلِهَذَا أَهْمَلَهُ الْجَوْهَرِيُّ" → the "bi-wazn …" / "ka-…" formulas are al-Rāzī's additions (e.g. Ayd entry: "بِوَزْنِ جَيِّدٍ", "بِوَزْنِ مُخْرَجٍ").
- p. 10, why: "وَلَكِنَّا قَصَدْنَا بِزِيَادَةِ الضَّبْطِ بِالْمِيزَانِ أَوْ بِالنَّصِّ عُمُومَ الِانْتِفَاعِ بِهِ وَأَلَّا يَتَطَرَّقَ إِلَيْهِ بِمُرُورِ الْأَيَّامِ تَحْرِيفُ النُّسَّاخِ وَتَصْحِيفُهُمْ … قِلَّةُ الضَّبْطِ فِيهَا بِالْمَوَازِينِ الْمَشْهُورَةِ … اعْتِمَادًا مِنْ مُصَنِّفِيهَا عَلَى ضَبْطِهَا بِالشَّكْلِ الَّذِي يَعْكِسُهُ التَّبْدِيلُ وَالتَّحْرِيفُ عَنْ قَرِيبٍ" → copyists garble vowel marks (shakl); fixing forms by model words protects them.

Kashf al-Ẓunūn's summary (vol. 2, p. 1073) independently describes the same features: "وصدر فوائده بقلت وكل ما أهمله الجوهري من الأوزان ذكره بالنص على حركاته أو برده إلى واحد من الأوزان العشرين".

---

## 4. Later arrangement (Maḥmūd Khāṭir)

Source: *Mukhtār al-Ṣiḥāḥ*, "عُني بترتيبه محمود خاطر بك", 5th printing (Cairo: al-Maṭbaʿa al-Amīriyya, 1334/1916). archive.org item RZY1916AR (https://archive.org/details/RZY1916AR); page images viewed in browser: title page n4 (https://archive.org/download/RZY1916AR/page/n4.jpg), preface n8–n9.
- Title page (read from image): "مختار الصحاح للشيخ الإمام محمد بن أبي بكر بن عبد القادر الرازي رحمه الله تعالى — عُني بترتيبه محمود خاطر بك — قررت وزارة المعارف العمومية في ٢٥ شعبان سنة ١٣٢٢ (٣ نوفمبر سنة ١٩٠٤) طبع هذا الكتاب على نفقتها واستعماله بالمدارس الأميرية — (الطبعة الخامسة) بالمطبعة الأميرية بالقاهرة ١٣٣٤ — ١٩١٦".
- Preface p. (د) (image n9), signed محمود خاطر: "وجلي أن الإمام الرازي جرى على أسلوب الجوهري في إيراد الكلم باعتبار أواخرها وهو ما لا يخلو أيضا من الصعوبة … فرأى أن يكون على اعتبار الحرف الأول والثاني كما هو ترتيب المصباح للإمام الفيومي وأن ترد إلى كل مادة مشتقاتها التي يصعب على الطالب ردها إليها مع حذف ما لا ينبغي أن يطرق مسامع النشء بشرط المحافظة على أصل الكتاب" — (the proposal is attributed to the ministry's undersecretary, Yaʿqūb Artīn Pasha; correction and vowelling entrusted to Shaykh Ḥamza Fatḥ Allāh).
- Guide uses: al-Rāzī followed al-Jawharī's order by final letters; Khāṭir's edition for the Ministry of Education (decision of 1904) re-sorted it by first and second letters (as in al-Fayyūmī's *al-Miṣbāḥ*), pointed hard-to-trace derivatives to their roots, and dropped what "should not reach the ears of the young". Guide does NOT claim Khāṭir was the first to rearrange, nor that the 1999 edition is Khāṭir's text.
- Supporting (secondary, not cited): Youm7, 16 Dec 2020, on a Quṣūr al-Thaqāfa reprint: "قام محمود خاطر أحد موظفى مطبعة بولاق بترتيب الصحاح حسب ترتيب المعاجم الحديثة وطبع سنة 1907 بعد حذف منه بعض الألفاظ" — newspaper; date 1907 conflicts with 1904 decision/earlier printings; not used.
- The 1911 al-Maṭbaʿa al-Kulliyya printing (archive.org mukhtrali00jawhuoft, OCR) still follows the rhyme order: OCR shows headings like "فصل الباء # باب الواو والياء", "فصل الباء * باب العين".

## 5. Scholarship

- Haywood, *Arabic Lexicography* (Leiden: Brill, 1960), archive.org copy https://archive.org/details/in.gov.ignca.12555 (OCR text read; page numbers are the running heads):
  - p. 68: rhyme arrangement "by which roots were listed according to their final radicals"; credit usually given to al-Jawharī.
  - p. 69: al-Jawharī "studied under his maternal uncle, Abū Ibrāhīm Isḥāq ibn Ibrāhīm al-Fārābī (died 350/961)", who used the rhyme order "in a vocabulary entitled Dīwān al-Adab". (Used for identifying the Dīwān al-Adab that al-Rāzī cites in ش ي أ — only if that example is used; it was dropped from the final draft.)
  - p. 75: "Several mukhtasarat or abridgements of the Sahah were compiled. The most famous was al-Rāzī's Mukhtār al-Sahah, published in Bulaq in 1282/1865." (ranking — not repeated in guide)
  - p. 76: "Both he [al-Zinjānī] and al-Rāzī omitted most quadriliteral and quinqueliteral roots, besides pruning other entries to the very limit." → guide paraphrases, attributed.
- Baalbaki, *The Arabic Lexicographical Tradition* (Brill, 2014): NOT accessed (paywalled; only pirated copies found online — not used). Baalbaki's CV (https://www.aub.edu.lb/fas/arabic/Documents/C.V.-%20RB.pdf) lists "Ṣafw al-rāḥ min mukhtār al-Ṣiḥāḥ," al-Abḥāth 40 (1992), pp. 3–106 — not accessed; not cited.
- Encyclopaedia Iranica: no article on the Mukhtār; "Lexicography" is a pointer headword; "Dictionaries" (Persian) does not mention it. Not cited.
- EI2/EI3: not accessible; not cited.

---

## 6. Root examples examined

Chosen:
1. **ي د ي (ydy)** — CLOSE READING. Mukhtār entry (id 1173) quoted: "وَ (الْيَدُ) الْقُوَّةُ. وَ (أَيَّدَهُ) قَوَّاهُ … {وَالسَّمَاءَ بَنَيْنَاهَا بِأَيْدٍ} [الذاريات: 47] . قُلْتُ: … بِأَيْدٍ … أَيْ بِقُوَّةٍ وَهُوَ مَصْدَرُ آدَ يَئِيدُ إِذَا قَوِيَ، وَلَيْسَ جَمْعًا لِيَدٍ لِيُذْكَرَ هُنَا بَلْ مَوْضِعُهُ بَابُ الدَّالِ. وَقَدْ نَصَّ الْأَزْهَرِيُّ عَلَى هَذِهِ الْآيَةِ فِي الْأَيْدِ بِمَعْنَى الْمَصْدَرِ. وَلَا أَعْرِفُ أَحَدًا مِنْ أَئِمَّةِ اللُّغَةِ أَوِ التَّفْسِيرِ ذَهَبَ إِلَى مَا ذَهَبَ إِلَيْهِ الْجَوْهَرِيُّ مِنْ أَنَّهَا جَمْعُ يَدٍ." al-Ṣiḥāḥ ydy (id 1178, displayed) has the pre-قلت part verbatim in substance: "واليدُ: القوَّةُ. وأيَّدَهُ، أي قوَّاه. ومالى بفلان يدان، أي طاقةٌ. قال تعالى: (والسماءَ بَنيناها بأيْدٍ). وقوله تعالى: (حتَّى يُعْطوا الجزيةَ عن يَد) أي عن ذِلَّةٍ واستسلام، ويقال: نَقداً لا نسيئةً." → shows (a) al-Jawharī's text, (b) al-Rāzī's objection, (c) the Q 9:29 line after the note is al-Jawharī's again with no resumption marker. Both read the verse as "strength"; the dispute is derivation/placement. Uncertainty: al-Rāzī's "I know of no one…" is unverifiable from the entry; his report of al-Azharī was NOT checked against the *Tahdhīb* (evidence gap).
   - Linked companion: **أ ي د (Ayd)** Mukhtār entry (id 6722, displayed): "(آدَ) الرَّجُلُ اشْتَدَّ وَقَوِيَ وَبَابُهُ بَاعَ وَ (الْأَيْدُ) وَ (الْآدُ) بِالْمَدِّ الْقُوَّةُ" → supports "defines al-ayd as strength" and the bāb example (āda yaʾīdu aydan ~ bāʿa yabīʿu bayʿan). Note the Ayd entry does not itself cite Q 51:47 — guide doesn't say it does.
2. **ه د ي (hdy)** — addition + seam + cuts. Mukhtār (id 591) quoted: "قُلْتُ: قَدْ وَرَدَ (هَدَى) فِي الْكِتَابِ الْعَزِيزِ عَلَى ثَلَاثَةِ أَوْجُهٍ: مُعَدًّى بِنَفْسِهِ كَقَوْلِهِ - تَعَالَى -: {اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ} … وَمُعَدًّى بِاللَّامِ كَقَوْلِهِ - تَعَالَى -: {الْحَمْدُ لِلَّهِ الَّذِي هَدَانَا لِهَذَا} … وَمُعَدًّى بِإِلَى كَقَوْلِهِ - تَعَالَى -: {وَاهْدِنَا إِلَى سَوَاءِ الصِّرَاطِ} . قَالَ: وَهَدَى وَ (اهْتَدَى) بِمَعْنًى." al-Ṣiḥāḥ hdy (id 533): "وغيرهم يقول: هَدَيْتُهُ إلى الطريق وإلى الدار ، حكاها الاخفش. وهدى واهتدى بمعنًى." → the note is inserted between these; "قال:" resumes al-Jawharī. al-Ṣiḥāḥ's entry quotes Zuhayr (twice), al-Mutalammis, Ṭarafa, Imruʾ al-Qays, Dhū al-Rumma, al-Aʿshā; has هِداء (bride led to husband), يُهادي/تهادى (swaying walk), هادي السهم, الهادي = threshing bull, هوادي الخيل, مِهدى/مِهداء — none of these is in the Mukhtār's entry. The Mukhtār keeps: hudā; hadāhu li-l-dīn; hadaytuhu al-ṭarīq (Ḥijāzī) / ilā; hady (animal brought to the Ḥaram) + hadiyy; hadya/hidya = conduct; hādī = neck; hadiyya; tahādī. Verse refs: Q 1:6, 90:10, 7:43, 10:35, 38:22 (the last not given in our copy; Shamela gives [ص: ٢٢]).
   - Site rendering issue: harmonized English puts "He notes hadā and ihtadā carry the same sense" and al-Farrāʾ's reading under "3. The author's own note" — but that text is al-Jawharī's. → siteDataIssues (minor).
3. **إ ل ه (Alh)** — brief: "وَأَنْشَدَنِي أَبُو عَلِيٍّ: وَأَعْجَلْنَا الْإِلَاهَةَ أَنْ تَئُوبَا" in the Mukhtār; al-Ṣiḥāḥ Alh: "وأنشدني أبو علي: تروحنا من اللعباء قصرا * وأعجلنا الالاهة أن تؤوبا" → the first person is al-Jawharī's. (The Mukhtār keeps only the second hemistich.) Not an excerpt; the Arabic is visible in "Original Text" (the harmonized English does not render this line).
4. **ع ذ ب (E*b)** — brief, in the limits paragraph: Mukhtār (id 580) = "ع ذ ب : (الْعَذْبُ) الْمَاءُ الطَّيِّبُ وَبَابُهُ سَهُلَ." (entire entry; identical in 1999 ed. p. 203); al-Ṣiḥāḥ (id 238) includes "والعذاب: العقوبة، وقد عذبته تعذيبا." Whether al-Rāzī omitted عذاب or the printed tradition lost it: not established (OCR of 1885/1911/1916 printings too poor to locate the entry; autograph MS images not examined).

Examined and not used (or dropped for length):
- **أ م ر (Amr)** — excellent: al-Jawharī: "وقوله تعالى: (أَمَرْنا مُتْرَفيها)، أي أمرناهم بالطاعة فعصوا. وقد يكون من الامارة"; al-Rāzī: "قُلْتُ: لَمْ يُذْكَرْ فِي شَيْءٍ مِنْ أُصُولِ اللُّغَةِ وَالتَّفْسِيرِ أَنَّ أَمَرْنَا مُخَفَّفًا مُتَعَدِّيًا بِمَعْنَى جَعَلَهُمْ أُمَرَاءَ." Also "وَبَابُهُمَا نَصَرَ" (absent in al-Ṣiḥāḥ) and a second note on Q 65:6. Dropped: same kind of move as ydy; word budget.
- **ش ي أ ($yA)** — Mukhtār keeps only "(الْمَشِيئَةُ) الْإِرَادَةُ … قُلْتُ: وَفِي دِيوَانِ الْأَدَبِ: (الْمَشِيئَةُ) أَخَصُّ مِنَ الْإِرَادَةِ"; al-Ṣiḥāḥ's long debate on أشياء gone. Good illustration of cutting + outside source; dropped for length (hdy already shows cutting).
- **ح م ل (Hml)** — "فاستشهاد الجوهري رحمه الله تعالى بالآيتين فيه نظر" (Q 20:100–101, 7:189); long entry (4,026 chars); not used.
- **ب ر ر (brr)** — "لا أعلم أحدا ذكر (التبرر) بمعنى الطاعة غيره رحمه الله"; not Qur'an-central; not used.
- **ع ق ب (Eqb)**, **ظ ه ر (Zhr)** (al-Rāzī notes al-Jawharī omitted the canonical reading تظاهر), **ح ل ل (Hll)**, **ت و ب (twb)** — noted as further instances of al-Rāzī checking al-Jawharī; not used.
- **ص د د (Sdd)** — "وَقُلْتُ لِأَبِي عَلِيٍّ النَّحْوِيِّ" in the Mukhtār (no colon; al-Jawharī's voice) — could not find the line in our al-Ṣiḥāḥ ص د د entry (probably under another root there), so used إ ل ه instead.

## 7. Open questions / evidence gaps
- Exact date: 660 AH (Kashf Istanbul ed.; al-Ziriklī) vs 760 AH (Kashf as quoted on the 1911 Cairo title page). I did not see the colophon of the autograph (Murad Molla 1816) myself, nor ʿAbd Allāh Mukhliṣ's treatise. Death date unknown ("after 666").
- Whether the short entries (ع ذ ب etc.) reflect al-Rāzī's own selection or losses in the printed tradition.
- Whether the 1999 Beirut text descends from Khāṭir's rearranged/bowdlerised text (the presence of cross-reference lines suggests a first-letter tradition like his, but not proven).
- al-Rāzī's claim about al-Azharī on Q 51:47 not checked in the *Tahdhīb*.
- Baalbaki 2014 and EI not consulted (access).
- Which hawramani source text: unknown; matched to the 1999 edition by comparison only.

---

## 8. Additional counts and final-draft decisions (after drafting)

- Model-verb class formulas: regex `(وبابه|وبابهما|وبابها|وبابهن) + one of the 20 model verbs` or `من باب + model verb` (unvowelled). Mukhtār: 522 of 877 displayed entries; al-Ṣiḥāḥ: 0 of 866 → guide: "some 520 of the 877 entries we display, and none of al-Jawharī's".
- Final examples in the guide: ي د ي (close reading, with al-Ṣiḥāḥ comparison, both linked), ه د ي (addition + seam + cuts, both linked), plus brief linked mentions of أ ي د (Mukhtār; definition of al-ayd and "وَبَابُهُ بَاعَ"), إ ل ه (both; al-Jawharī's first person), ع ذ ب (both; silence of a selection).
- Dropped from the final draft for length: Haywood p. 76 (quadriliterals), ش ي أ, أ م ر.
- "Not the theologian Fakhr al-Dīn al-Rāzī": no source is cited for the negative; it rests on the different full name given by al-Ziriklī and the Shamela card. Fakhr al-Dīn's own dates are not stated in the guide.
- "last heard of in Konya in 666" = al-Ziriklī "وكان في قونية سنة ٦٦٦ وهو آخر العهد به".
- Inline quotations from the introduction in the lede and in "Hearing the two voices" are my translations; the blockquote label says so for all quotations from the introduction.
- Rendered page checked at http://localhost:4000/classical-dictionaries/mukhtar-al-sihah (text read back via the browser pane); validator: 0 errors, 0 warnings, 1,096–1,099 words.

---

## 9. Revision round 1 (reviser, 2026-09-26): added evidence

- **Verse in al-Rāzī, recounted over the 856 shared roots.**
  - Markers only: 46.
  - Markers + "قال/قول + named poet": 58 (6.8%).
  - Carry-over of al-Jawharī's poet-introduced lines, combined with the markers: 48.
  - An asterisk-based method overcounts: `*` also marks non-verse text in al-Jawharī.
  - All methods stay below 10%, so the guide now says "fewer than one in ten".
- **Bāb formulas, unvowelled.**
  - وباب(ه|هما|ها|هن) + model verb: 299 entries.
  - من باب + model verb: 280, of which 223 have no *wa-bābuhu*.
  - Either formula: 522/877. Al-Jawharī: 0/866.
- **Khāṭir 1916, preface p. (د).** Seen in the page image n9 and in the djvu OCR: "وجلي أن الإمام الرازي جرى على أسلوب الجوهري في إيراد الكلم باعتبار أواخرها". It is on the same page as "مع حذف ما لا ينبغي أن يطرق مسامع النشء".
- **1999 ed. (Shamela 23193/2175), p. 203.** The whole ع ذ ب entry is "ع ذ ب: (الْعَذْبُ) الْمَاءُ الطَّيِّبُ وَبَابُهُ سَهُلَ." The breadcrumb reads باب العين › ع ذ ب, which is first-letter order.
- **ع م ل (Eml, id 581), two *qultu* notes.** Al-Azharī: "استعمل فلان اللبن إذا بنى به بناء". Then: "قلت: وقول الفقهاء ماء (مستعمل) قياس على هذا وإلا فلا وجه لصحته غير هذا القياس". This is the only *qultu* note on jurists' usage among the displayed entries: Eql's Abū Ḥanīfa/Ibn Abī Laylā passage and Smm's "وذكر أبو عبيد أن الفقهاء يقولون" both sit outside *qultu* notes.
