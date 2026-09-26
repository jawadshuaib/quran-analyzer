# Verification round 1: al-misbah-al-munir

Independent fact-check of `roots/frontend/src/content/dictionary-guides/guides/al-misbah-al-munir.ts`.
I did not open research-notes.md or any revision file. Every source was opened directly (curl, WebFetch or the Wayback copy), and every example entry was read with `_dict_guide_tool.py entry` and in the DB.

Sources opened and what they are:

- **DURAR**: Ibn Ḥajar, *al-Durar al-Kāmina*, Shamela book 6674, page 371. The page header reads ج1 ص372, entry no. ٧٨٧. The book card gives the 2nd Hyderabad ed., 6 vols, 1392–96 H / 1972–76.
- **ENCY**: arab-ency.com.sy/details/8678, by Sakīna Mawʿid. Vol. 15 (2006), p. 90.
- **INTRO**: Wikisource مقدمة. Checked against Shamela 12145 pp. 1–2 of the separately numbered المقدمة. The texts are identical.
- **KHATIMA**: Shamela 12145.
  - The khātima starts at ج2 ص684 (Shamela page 3503).
  - p. 711 is Shamela page 3531.
  - p. 712 is Shamela page 3532, where the book ends.
- **SH-CARD**: the Shamela 12145 book card, "المكتبة العلمية - بيروت، عدد الأجزاء ٢ (متسلسلة الترقيم)".
- **LANE**: Lane's Preface at laneslexicon.github.io.
  - Source list: "[The "Miṣbáḥ" of El-Feiyoomee …] Notwithstanding its title, it comprises a very large collection of classical words and phrases and significations of frequent occurrence".
  - Abbreviations: "Mṣb".
  - Chronology: "Aboo-Ḥeiyán: born in 654: died in 745", and "El-Feiyoomee (author of the "Miṣbáh," which he finished in 734)".
- **HAYWOOD**: archive.org djvu text. The text says "al-Fayyumi (died 766/1364)", and the index gives "al-Fayyumi, 108". Leiden: Brill, copyright 1960.
- **HALLAQ**: Iranica. Live URL returns Cloudflare 403 to bots, so I read the Wayback copy of iranicaonline.org/articles/gazali-v-as-a-faqih/, 2026-04-07. Header: "Vol. X, Fasc. 4, pp. 372-374". It says al-Wasīṭ was "later abridged as al-Wajīz" and that "ʿAbd-al-Karīm Rāfeʿī (d. 623/1226) … wrote a commentary on al-Wājīz, entitled Fatḥ al-ʿazīz".
- **WALTERS**: W.590 description. It says: "originally written as a gloss on the commentary of ʿAbd al-Karīm al-Rāfiʿī (d. 623 AH / 1226 CE) on al-Wajīz … entitled Fatḥ al-ʿazīz". It also gives "copied … in 1083 AH / 1673 CE".
- **HAWRAMANI**: the index page names no edition. Its root page روي contains the Miṣbāḥ's ر و ي entry, which is where "وَرَأَيْتُ الشَّيْءَ رُؤْيَةً أَبْصَرْتُهُ" appears.
- **NLI**: National Library of Israel catalogue. It lists *Tuḥfat al-arīb bi-mā fī al-Qurʾān min al-gharīb* under Abū Ḥayyān (1256–1344).

Counts described as "by our count" were reproduced over the 901 displayed entries with `_dict_guide_tool.py grep`:

| Pattern | Entries | Share |
|---|---|---|
| من باب | 601 | 67% |
| الأزهري | 133 | |
| `{…}` Qur'an quotations | 208 | |
| التنزيل | 64 | |
| poetry markers (`...`, الشاعر, الراجز, أنشد, named poets) | 60 | |
| hadith `«…»` | 99 | |
| الشرع | 23 | |
| شرعا / شرعي | 13 | |
| اصطلاح | 12 | |
| الفقهاء | 43 | |
| Lane entries citing Msb | 1,261 of 1,410 | |

**Edition check.** I compared 37 stored entries (root letter ر) with the Shamela text of the ʿIlmiyya printing:

- 36 match at a vowel-stripped similarity of 0.97 or higher.
- 1 (رغب) is at 0.969.
- ح ج ج is identical letter for letter.

## Claims table

S = SUPPORTED, NQ = NEEDS QUALIFICATION, U = UNSUPPORTED

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Title al-Miṣbāḥ al-Munīr, titleAr المصباح المنير في غريب الشرح الكبير | S | INTRO: "وَسَمَّيْتُهُ بِالْمِصْبَاحِ الْمُنِيرِ فِي غَرِيبِ الشَّرْحِ الْكَبِيرِ" |
| C2 | titleGloss "The Light-Giving Lamp, on the Unusual Words of the Great Commentary" | S | A fair rendering of the title (*gharīb* = unusual words) |
| C3 | author al-Fayyūmī / الفيومي | S | DURAR, ENCY, INTRO |
| C4 | authorFull Abū l-ʿAbbās Aḥmad b. Muḥammad b. ʿAlī al-Fayyūmī, later of Ḥamāh | S | INTRO "أبو العباس أحمد بن محمد بن علي الفيومي المقري"; ENCY "ثم الحموي، أبو العباس"; DURAR "الفيومي ثم الحموي" |
| C5 | Period: finished 734 / 1334; d. c. 770 / 1368 (uncertain) | S | KHATIMA p. 712 colophon; DURAR; ENCY |
| C6 | kind "Lexicon for a law book" | S | INTRO; WALTERS |
| C7 | Summary: 14th-c. dictionary for the difficult words of a Shāfiʿī law book | S | INTRO "غريب شرح الوجيز للإمام الرافعي"; SH-CARD "شرح فيه ألفاظ الفقه على المذهب الشافعي" |
| C8 | Summary/lede: fixes voweling, conjugation, plurals | S | INTRO "وَقَيَّدْتُ مَا يَحْتَاجُ إلَى تَقْيِيدٍ…"; entries Hjj/bxl/jzy give plurals "مثل سدرة وسدر" etc. |
| C9 | Summary "marks where a legal sense narrows ordinary usage"; lede "says plainly when a word's meaning in … al-sharʿ has narrowed from its meaning in the language" | **NQ** | He does this in examples (Hjj 3297 "قُصِرَ اسْتِعْمَالُهُ فِي الشَّرْعِ", bxl 6283, wly "خص في الشرع", Hyy, fqh). But explicit sharʿ/term markers appear in only ~25–45 of 901 displayed entries. "says plainly when" reads as systematic. Secondary support is only general: SH-CARD "أبرز المعاني الفقهية إلى جانب المعاني اللغوية"; ENCY "عني فيه بالمعاني الفقهية"; HAYWOOD "full of technical terms of jurisprudence" |
| C10 | Summary: weighs jurists' Arabic against earlier lexicographers | S | jzy 1201; bny ("فقول الفقهاء بنو اللبون مخرج…"); ktb ("وقول الفقهاء باب الكتابة فيه تسامح") |
| C11 | Lede: title promises the words of al-Rāfiʿī's Great Commentary; compact teaching lexicon | S | INTRO (abridgment "اختصاره"); KHATIMA p. 711 "مسالك التعليم للمبتدئ" |
| C12 | Grew up in al-Fayyūm, Egypt | S | DURAR "نشأ بالفيوم"; ENCY "بالفيوم بمصر" |
| C13 | Studied Arabic with Abū Ḥayyān | S | DURAR "وجمع في العربية عند أبي حيان" |
| C14 | Abū Ḥayyān is the author of Tuḥfat al-Arīb | S | NLI catalogue record |
| C15 | Settled in Ḥamāh; al-Malik al-Muʾayyad Ismāʿīl made him preacher (*khaṭīb*) of the Dahsha mosque he built | S | DURAR "ارتحل إلى حماة فقطنها ولما بنى الملك المؤيد إسماعيل جامع الدهشة قرره في خطابتها" |
| C16 | Ibn Ḥajar calls him learned in language and law (vol. 1, p. 372) | S | DURAR "وكان فاضلا عارفا باللغة والفقه", p. 372 confirmed |
| C17 | Death: after 770 (1368–9) by Ibn Ḥajar's guess | S | DURAR "وكأنه عاش إلى بعد سنة ٧٧٠" |
| C18 | Death c. 760 per a manuscript note reported by al-Ziriklī | S | ENCY, quoting al-Ziriklī: a note by Muḥammad b. al-Sābiq al-Ḥamawī on a manuscript of *al-Durar* says "في حدود 760". This is a secondary relay |
| C19 | 766 in Haywood, p. 108 | S | HAYWOOD "(died 766/1364)"; index "al-Fayyumi, 108" |
| C20 | Finished late Shaʿbān 734, spring 1334 (vol. 2, p. 712) | S | KHATIMA p. 712 "فِي الْعَشْرِ الْأَوَاخِرِ مِنْ شَعْبَانَ … سَنَةَ أَرْبَعٍ وَثَلَاثِينَ وَسَبْعِمِائَةٍ". Late Shaʿbān 734 ≈ late April / early May 1334 |
| C21 | The law book is al-Rāfiʿī's (d. 623/1226) commentary on al-Wajīz, the "Great Commentary" | S | INTRO; WALTERS; HALLAQ |
| C22 | al-Wajīz is al-Ghazālī's abridged manual of Shāfiʿī law | S | HALLAQ "later abridged as al-Wajīz" |
| C23 | He first compiled a longer book on the commentary's *gharīb*, with extra material on inflection, confusable words and cited examples | S | INTRO "أَوْسَعْتُ فِيهِ مِنْ تَصَارِيفِ الْكَلِمَةِ … الْأَلْفَاظِ الْمُشْتَبِهَاتِ وَالْمُتَمَاثِلَاتِ وَمِنْ إعْرَابِ الشَّوَاهِدِ وَبَيَانِ مَعَانِيهَا". "Cited examples" is loose (see brief issues) |
| C24 | The earlier book was arranged by word shape, so a root's material was scattered; the Miṣbāḥ abridges it, regathered by root (first letter, then second) | S | INTRO "قَسَمْتُ كُلَّ حَرْفٍ مِنْهُ بِاعْتِبَارِ اللَّفْظِ … غَيْرَ أَنَّهُ افْتَرَقَتْ بِالْمَادَّةِ الْوَاحِدَةِ أَبْوَابُهُ … فَأَحْبَبْتُ اخْتِصَارَهُ … مُعْتَبِرًا فِيهِ الْأُصُولَ مُقَدِّمًا الْفَاءَ ثُمَّ الْعَيْنَ" |
| C25 | Does not promise to cover what the commentary itself makes clear | S | INTRO "لَمْ أَلْتَزِمْ ذِكْرَ مَا وَقَعَ فِي الشَّرْحِ وَاضِحًا وَمُفَسَّرًا" |
| C26 | Lane: despite its title, a large stock of ordinary classical words and senses | S | LANE "Notwithstanding its title, it comprises a very large collection of classical words … of frequent occurrence" |
| C27 | A grammatical section closes the book; at its end he says he kept to "what concerns the jurists' vocabulary", teaching "the beginner" and bringing things "within reach of the intermediate student" (vol. 2, p. 711) | S | KHATIMA p. 711 "وَقَدْ اقْتَصَرْتُ فِي هَذَا الْفَرْعِ أَيْضًا عَلَى مَا يَتَعَلَّقُ بِأَلْفَاظِ الْفُقَهَاءِ وَسَلَكْتُ فِي كَثِيرٍ مِنْهُ مَسَالِكَ التَّعْلِيمِ لِلْمُبْتَدِئِ وَالتَّقْرِيبِ عَلَى الْمُتَوَسِّطِ"; section pp. 684–712 |
| C28 | Intro quotation "وَقَيَّدْتُ … مِنْ بَابِ قَتَلَ" and its translation | S | Matches INTRO verbatim (ellipsis skips "وقفل وأقفال وهمل وإهمال ونحو ذلك"); translation accurate |
| C29 | *min bāb* formulas in about two-thirds of the entries shown | S | 601/901 |
| C30 | *min bāb qatala* = conjugates like *qatala, yaqtulu* | S | INTRO; entries |
| C31 | *bi-l-alif* marks form IV; *bi-l-tashdīd* marks form II | S | bxl "وأبخلته بالألف"; zkw "زكى … بالتشديد"; Hjj "أحججت الرجل بالألف" |
| C32 | *lugha* flags a variant | S | fDl "وفي لغة"; Hjj "والفتح لغة" |
| C33 | *ʿāmmī* marks a rejected popular form, sometimes paired with *al-ṣawāb*; zkw: *zakātiyya* is *ʿāmmī*, correct is *zakawiyya* | S | zkw: "وَقَوْلُهُمْ زَكَاتِيَّةٌ عَامِّيٌّ وَالصَّوَابُ زَكَوِيَّةٌ" |
| C34 | The original drew on some seventy books, beginning with al-Azharī's *Tahdhīb* (vol. 2, pp. 711–712) | S | KHATIMA p. 711 "مِنْ نَحْوِ سَبْعِينَ مُصَنَّفًا … فَمِنْ ذَلِكَ التَّهْذِيبُ لِلْأَزْهَرِيِّ" |
| C35 | He usually names his authority "where a judgement rests on it" | S | KHATIMA p. 712 "وَسَمَّيْتُهُ غَالِبًا فِي مَوَاضِعِهِ حَيْثُ يُبْنَى عَلَيْهِ حُكْمٌ" |
| C36 | al-Azharī is named in about 130 entries shown | S | 133 |
| C37 | "al-Fārābī" is the author of *Dīwān al-Adab*, judging from the same list | S | KHATIMA pp. 711–712 "وَدِيوَانُ الْأَدَبِ لِلْفَارَابِيِّ" |
| C38 | Hjj excerpt copied from the stored text | S | Entry 3297; validator passes |
| C39 | Hjj translation | S | Accurate (قصد = headed for; النسك = devotional rites) |
| C40 | *al-ḥijj* is the noun of the act, the form in Q 3:97 | S | 3297 "وَالِاسْمُ الْحِجُّ بِالْكَسْرِ"; Q 3:97 (Ḥafṣ) حِجُّ الْبَيْتِ |
| C41 | *ḥijja* "a single occasion", with Thaʿlab's remark | S | 3297 "قَالَ ثَعْلَبٌ قِيَاسُهُ الْفَتْحُ وَلَمْ يُسْمَعْ مِنْ الْعَرَبِ" |
| C42 | *ḥujja* proof; *ḥājjahu* (Q 2:258); eye-bone; beaten road; plurals by model words | S | 3297; Q 2:258 حَاجَّ إِبْرَاهِيمَ |
| C43 | No evidence given for the older sense; "proof" and eye-bone are not derived from it; senses stand side by side | S | Reading of 3297 |
| C44 | al-Jawharī's *Ṣiḥāḥ* is among al-Fayyūmī's listed sources | S | KHATIMA p. 712 "وَالصِّحَاحُ لِلْجَوْهَرِيِّ" |
| C45 | *Ṣiḥāḥ* Hjj: same two-step story; quote; line by al-Mukhabbal; "convention" | S | Displayed Ṣiḥāḥ Hjj: "قال المخبل … هذا الأصلُ، ثم تُعورِفَ استعماله في القصد إلى مكة للنُسك" |
| C46 | "The label names a register, not a date"; Q 2:196 | S | Guide's own interpretation, fairly framed; Q 2:196 "وَأَتِمُّوا الْحَجَّ وَالْعُمْرَةَ لِلَّهِ" |
| C47 | bxl excerpt and translation | S | Entry 6283; accurate |
| C48 | Neither definition comes with evidence; Qur'anic *bukhl* verses Q 3:180, 47:38 | S | 6283; Q 3:180 يَبْخَلُونَ; Q 47:38 يَبْخَلُ |
| C49 | jzy: matches *jazā* with *qaḍā*, cites Q 2:48, later turns to jurists' *ajzā* | S | Entry 1201 |
| C50 | jzy excerpt and translation | S | 1201; accurate |
| C51 | The "I" is al-Azharī; *hādhā lafẓuhu* closes the quote; *wa-fīhi naẓar* is al-Fayyūmī | S | Structure of 1201; Lisān جزي corroborates al-Azharī on jurists' أجزى ("قال الأزهري: وبعض الفقهاء يقول أجزى") |
| C52 | Objection: softening is regular (*akhṭaʾtu/akhṭaytu*, *tawaḍḍaʾtu/tawaḍḍaytu*); al-Akhfash: *jazā* Ḥijāz, *ajzaʾa* Tamīm | S | 1201 |
| C53 | Jurists' Arabic defended by analogy and by report against a lexicographer | S | 1201 (qiyāsī softening + al-Akhfash's transmission) |
| C54 | fDl: idiom *lā yamliku dirhaman faḍlan ʿan dīnārin*; "our shaykh Abū Ḥayyān … may God preserve him" found no text showing it is Arab speech | S | fDl entry "وَقَالَ شَيْخُنَا أَبُو حَيَّانَ … أَبْقَاهُ اللَّهُ تَعَالَى وَلَمْ أَظْفَرْ بِنَصٍّ…" |
| C55 | A blessing for the living; Abū Ḥayyān d. 745 | S | LANE chronology "died in 745"; consistent with the book finished in 734 |
| C56 | "The Miṣbāḥ is strongest on form and on marking where the sharʿ narrowed a word" | **NQ** | "Form" is well supported (C29–C31). Sharʿ-narrowing is explicit in only a few dozen entries; "strongest" is an unattributed evaluation |
| C57 | Quotes the Qur'an (with formulas like *wa-fī l-tanzīl*) in roughly 200 entries shown | S | 208 entries with {…}; التنزيل in 64 |
| C58 | "its evidence is mostly earlier scholars, and verse appears in only about seventy entries" | **NQ** | Poetry about 60 by strict markers, so "about seventy, generous" is acceptable. But hadith («…») appear in 99 entries, more than poetry, and the essay never mentions hadith as evidence. SH-CARD: "أكثر فيه من الاستشهاد بالأحاديث النبوية". "Verse" is ambiguous next to Qur'anic verses |
| C59 | Its labels are a 14th-c. teacher's classifications, not a history | S | Interpretation consistent with KHATIMA (teaching aim) |
| C60 | Lane cites it as "Msb" in most of his entries on our site | S | 1,261/1,410 displayed Lane entries; LANE abbreviation "Mṣb" |
| C61 | Tāj quotes "the Miṣbāḥ" by name; its smw entry takes Ibn al-Anbārī's remark on the gender of *samāʾ* from al-Fayyūmī | S | Displayed Tāj smw: "فِي المِصْباح: قالَ ابنُ الأنْبارِي: السَّماءُ يُذَكَّرُ ويُوءَنَّثُ"; Miṣbāḥ smw has the same |
| C62 | Ibn Ḥajar: his son copied most of it into a book of his own | S | DURAR "وقد نقل غالبه ولده في كتاب تهذيب المطالع" |
| C63 | Text from hawramani, which names no edition | S | HAWRAMANI index page |
| C64 | Agrees almost letter for letter with the ʿIlmiyya printing on Shamela (896/901), without its footnotes | S (sampled) | 36/37 sampled entries match at ≥0.97, Hjj identical; exact 896 not re-counted. Stored text keeps footnote markers "(1)", "(3)" in 12 entries (see brief issues) |
| C65 | 901 roots shown | S | `dicts`: 901 displayed |
| C66 | Some entries held back where another dictionary fills the place | S | DB: 526 Miṣbāḥ rows `deferred`; `_dict_defer_redundant.py` policy (one general-dictionary slot per root) |
| C67 | Introduction and closing grammatical section not shown | S | Entries are per-root; no khātima text in displayed rows |
| C68 | "he files a hamza in the middle of a root under the letter it softens to" | **NQ** | INTRO: after kasra → under ي; after ḍamma → under و; after fatḥa → under و, "لِأَنَّهَا تُسَهَّلُ إلَى الْأَلِفِ وَالْأَلِفُ الْمَجْهُولَةُ كَوَاوٍ كَالْفَأْسِ وَالرَّأْسِ". For *saʾala* (fatḥa) the hamza softens to alif but is filed under wāw, so the stated rule is wrong for the very case cited |
| C69 | *saʾala* is on the س و ل page | S | Entry 10115 "س و ل : … وَسَأَلْتُ اللَّهَ الْعَافِيَةَ…" |
| C70 | The ر أ ي page shows only *al-riʾa*; *raʾā* sits in an entry our copy lacks | S | Entry 275 (lung only); HAWRAMANI روي has the Miṣbāḥ's ر و ي entry with "وَرَأَيْتُ الشَّيْءَ رُؤْيَةً"; no DB row for it |
| C71 | Source durar: 2nd ed., 6 vols, Hyderabad 1972–76, vol. 1 p. 372 no. 787 | S | Shamela 6674 card and page |
| C72 | Source arabency: Sakīna Mawʿid, vol. 15, 2006, p. 90 | S | ENCY page footer |
| C73 | Source haywood: Brill 1960 | S | archive.org title page and copyright |
| C74 | Source misbah-ed: ʿIlmiyya, 2 vols continuous; intro pp. 1–2; khātima vol. 2 pp. 684–712 | S | SH-CARD; Shamela pages 1–2, 3503 (p. 684), 3532 (p. 712) |
| C75 | Source hallaq: Iranica X/4, 2000, pp. 372–374 | S | Wayback copy header |
| C76 | Source walters: W.590, dated 1083/1673 | S | WALTERS |
| C77 | Source wikisource: intro | S | Opened; identical to Shamela |
| C78 | Source lane: Preface (sources, abbreviations, chronology) | S | Opened |
| C79 | Source hawramani | S | Opened |

**Totals:**

- 79 claims.
- 75 supported.
- 4 need qualification (C9, C56, C58, C68).
- 0 unsupported.

## Flagged items and fixes

**C9: summary and lede overstate the sharʿ-narrowing marking**

The entry examples are real (Hjj, bxl; also wly, Hyy, fqh, jdl, sHr). But only about 25–45 of the 901 displayed entries carry an explicit sharʿ, sharʿan or iṣṭilāḥ note.

Fix:
- Lede: change "and says plainly when a word's meaning in the religious law, *al-sharʿ*, has narrowed…" to "and, in a number of entries, says plainly that a word's meaning in the religious law, *al-sharʿ*, has narrowed…".
- Summary: change "marks where a legal sense narrows ordinary usage" to "sometimes notes where a legal sense narrows ordinary usage".

**C56: "strongest on form and on marking where the sharʿ narrowed a word"**

This is an unattributed evaluation, and the second half is a minority feature.

Fix: "The *Miṣbāḥ* is most useful on form, and, where it notes one, on the gap between a word's legal and ordinary sense."

**C58: evidence profile omits hadith; "verse" is ambiguous**

Hadith quotations appear in about 99 displayed entries (e.g. jzy's Abū Burda hadith), more than poetry. The Shamela description notes the book "أكثر فيه من الاستشهاد بالأحاديث النبوية".

Fix: "Its evidence is mostly earlier scholars, with hadith in about a hundred entries and poetry in only about sixty or seventy, by a generous count."

- Replace "verse" with "poetry".
- Optionally cite the jzy hadith as the instance.

**C68: medial-hamza filing rule misstated**

INTRO: a medial hamza after kasra is filed under yāʾ; after ḍamma or fatḥa it is filed under wāw. After fatḥa this is because it softens to alif and an alif of unknown origin is treated as wāw.

Fix: "Because he files a medial hamza under a weak letter (after *a* or *u*, under *wāw*)[^misbah-ed|introduction], his treatment of *saʾala* … is on the س و ل page …"

- Optionally add that *raʾā* is in his ر و ي entry, a root our site does not list.

## Brief issues (non-factual)

- **must-fix:** "verse appears in only about seventy entries" sits next to a sentence about Qur'an quotations. A reader will take "verse" as Qur'anic verse and see a contradiction (200 vs 70). Say "poetry" (merged into the C58 fix).
- **suggestion:** C23 "cited examples" undersells *iʿrāb al-shawāhid wa-bayān maʿānīhā*. Use "the grammar and meaning of the evidentiary quotations".
- **suggestion:** Body says "Msb", the source list says "Mṣb". The site's Lane text shows "Msb", so keep "Msb" but make the two consistent, or say "(Mṣb, shown on our site as Msb)".
- **suggestion:** onOurSite could warn that 12 stored entries keep the printing's footnote numbers, e.g. "(1)", "(3)" in اتي, اخر, اذن, without the notes.
- **suggestion:** C18: say "a note on a manuscript of Ibn Ḥajar's *Durar*" so readers don't read it as a Miṣbāḥ manuscript.
- **suggestion:** "Reading an entry" packs several conventions into one paragraph and is close to a list. It is acceptable, but could be lightened.
- **Otherwise:** word count 1,099 is at the top of the range and not padded. There is no generic praise or ranking, and no forced "original root meaning" narrative. All root mentions are linked, and translations are labelled.

## URL check

| Source | URL result |
|---|---|
| durar | https://shamela.ws/book/6674/371 opens; shows ج1 ص372, entry 787 |
| arabency | https://arab-ency.com.sy/details/8678 opens |
| haywood | archive.org item opens; djvu text available |
| misbah-ed | https://shamela.ws/book/12145 opens; ʿIlmiyya, Beirut |
| hallaq | https://www.iranicaonline.org/articles/gazali/gazali-v-as-a-faqih/ gives Cloudflare 403 to automated fetch but is indexed by search engines under this URL. Content verified via Wayback (iranicaonline.org/articles/gazali-v-as-a-faqih/) |
| walters | Opens; correct manuscript |
| wikisource | Opens; correct text |
| lane | Opens; contains the cited material |
| hawramani | Opens |

Every listed source is cited in the text.

## Validator

`node scripts/validate-dictionary-guides.mjs al-misbah-al-munir` passed with 0 errors and 0 warnings ("1/1 guides pass"):

- root links: 10
- excerpts: 3
- words (lede + body): 1,099

## Site-data issues

- The stored date 1368 (≈ 770 AH) matches the common "c. 770" but is uncertain: after 770 (Ibn Ḥajar), c. 760 (al-Ziriklī's report), 766 (Haywood). No change needed, since the guide states the uncertainty.
- The stored author ("al-Fayyūmī") and title labels are correct.
- The Miṣbāḥ's account of رأى sits in its ر و ي entry. The site has no rwy root, so that entry was never collected. This is not an error, but it means the site cannot show al-Fayyūmī on "to see".
