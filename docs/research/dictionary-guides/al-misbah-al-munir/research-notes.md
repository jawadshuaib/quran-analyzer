# al-Miṣbāḥ al-Munīr (al-Fayyūmī) — research notes

Guide: `roots/frontend/src/content/dictionary-guides/guides/al-misbah-al-munir.ts`
Site dictionary slug: `al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir`
Drafted 2026-09-26. All counts below are my own, run against the local DB / `_dict_guide_tool.py` (displayed entries only unless stated).

---

## 1. What al-nuqta actually displays

- `dicts`: "al-Miṣbāḥ al-Munīr | المصباح المنير | al-Fayyūmī (site date 1368) | lang=ar | displayed entries=901".
- DB row status counts for this slug: approved+visible 901; **deferred 526**; pending 1 (total 1,428 stored). The 526 deferred entries are real Miṣbāḥ entries (e.g. زبد، خيط، خفت، أخبت، خذل، وثن، وتر …) held back by `_dict_defer_redundant.py` (one-slot-per-root policy for the general dictionaries). So a root page without a Miṣbāḥ entry does **not** mean the work lacks that root.
- All 901 displayed roots have Qur'an frequency > 0 (site shows Qur'anic roots only). All 28 initial letters are represented (ا 46 … ظ 4 … ي 9). Entry length: min 80 chars, median 791, max 6,861.
- Headword format in stored text: spaced root letters + colon, e.g. `ح ج ج :` (the Beirut print has `(ح ج ج) :`). Qur'an quotations appear in braces followed by a bracketed sūra name + verse number, e.g. `{يَوْمًا لا تَجْزِي نَفْسٌ عَنْ نَفْسٍ شَيْئًا} [البقرة: 48]` (jzy). The printing's footnotes are NOT in the stored text.
- Frequency of features in the 901 displayed entries (regex over unvowelled text, `grep`):
  - `من باب|من بابي` (model-verb class): **600** entries (≈ two-thirds).
  - `وزان|مثل:` (model words for noun patterns): 336.
  - Qur'an bracket refs `[sura: n]`: 207; `التنزيل|قوله تعالى|القرآن|{`: 219 → "about two hundred".
  - `الأزهري` named: **133** (`قال الأزهري` alone: 96).
  - `قال ابن فارس` 53; `قال ابن السكيت` 47; `قال أبو زيد` 42; `قال الفارابي` 32; `قال الجوهري` 20.
  - Poetry (generous regex: قال الشاعر / named poets / قال الراجز / وأنشد / قال الآخر …): **72** entries, with some false positives (e.g. personal names); narrow regex (قال الشاعر + 7 pre-Islamic poets + الراجز + وأنشد): 46. Essay says "far fewer … by a generous count about seventy".
  - `الشرع` 23 entries; `الفقهاء` 43; `عامي|لحن|الصواب|غلط|خطأ` 73; `عامي` 8.
  - `شيخنا` 1 entry (fDl — Abū Ḥayyān).

### 1a. Which printed text the stored copy follows (established)
- hawramani pages (e.g. https://arabiclexicon.hawramani.com/حجج/) and the hawramani work page (https://arabiclexicon.hawramani.com/al-fayyumi-al-misbah-al-munir-fi-gharib-al-sharh-al-kabir/) say nothing about the edition. The work page describes the Miṣbāḥ as explaining technical terms of al-Rāfiʿī's al-Sharḥ al-Kabīr (commentary on al-Ghazālī's al-Wajīz), "d. 1368 CE / 770 AH". No edition statement. (hawramani about page: also no edition statement.)
- I downloaded every page of the al-Maktaba al-Shāmila digitisation (book 12145: "الناشر: المكتبة العلمية - بيروت، عدد الأجزاء: ٢ (متسلسلة الترقيم) [ترقيم الكتاب موافق للمطبوع]") via `https://shamela.ws/ajax/pageContent/12145/<id>` and compared each displayed entry with the Shamela entry of the same heading (character-level match on unvowelled letters):
  - **896 of 901 match at ≥ 99 %**; 1 at ≥ 95 %; brq 0.84 (stored text appends the separate *istabraq* sub-entry); swy 0.61 (stored text longer: includes an appended passage on *siyyamā*); fTr and HDD heading-format mismatches only.
  - Word-level diff for jzy: identical except that Shamela carries the edition's footnotes ("(١)…" apparatus: note on Q 2:48, note on *majzaʾ* vocalisation citing the Qāmūs and Asās) which the stored text lacks.
  - Conclusion used in `onOurSite`: stored text = the Beirut al-Maktaba al-ʿIlmiyya printing as digitised on Shāmila, minus footnotes. (Whether hawramani took it from Shāmila directly is not stated anywhere — I only say "agrees with".)
- Pages in that printing for the examples: Hjj vol. 1 p. 121 (Shamela id 624); jzy vol. 1 p. 100 (524); bxl vol. 1 p. 37 (184); zkw vol. 1 p. 254 (1307); swl vol. 1 p. 297 (1515); rAy (رء ي) vol. 1 p. 249 (1263); (ر وي) containing "seeing" vol. 1 p. 246 (1253); fDl vol. 2 p. 475 (2345); smw — not needed. Introduction pp. 1–2 (separately numbered). Khātima vol. 2 pp. 684–712 (source list pp. 711–712, colophon p. 712).

### 1b. Filing of hamzated roots — consequences on our site (established)
- Introduction (see §3, claim I-6) says a medial hamza after *fatḥa* is filed where the wāw would go (examples الفأس، الرأس), after *ḍamma* also wāw (البؤس), after *kasra* yāʾ (البير، الذيب).
- Shamela confirms: `(رء س)` sits between `(ر ود)` and `(ر وض)` (ids 1246–1248, vol. 1 p. 245).
- **سأل "to ask"** is treated inside the Miṣbāḥ's `س و ل` entry (stored & displayed on `/root/swl`): "سَوَّلْتُ لَهُ الشَّيْءَ … وَسَأَلْتُ اللَّهَ الْعَافِيَةَ طَلَبْتُهَا سُؤَالًا وَمَسْأَلَةً …". There is no Miṣbāḥ entry on the سأل root page (`sAl`).
- **رأى "to see"**: the Miṣbāḥ treats رأيت الشيء رؤية inside its `(ر وي)` entry (Shamela id 1253, vol. 1 p. 246: "ورأيت الشيء رؤية أبصرته بحاسة البصر ومنه الرياء…"). That entry is not stored in our DB at all (no Miṣbāḥ entry contains "بحاسة البصر"). The `rAy` root page shows only the separate `(رء ي)` entry on الرِّئَة "the lung" (451 chars). → site data issue + onOurSite note.

### 1c. Entries read in full (with notes)
- **Hjj** (id 3297) — chosen, close reading. Text: "حَجَّ حَجًّا مِنْ بَابِ قَتَلَ قَصَدَ فَهُوَ حَاجٌّ هَذَا أَصْلُهُ ثُمَّ قُصِرَ اسْتِعْمَالُهُ فِي الشَّرْعِ عَلَى قَصْدِ الْكَعْبَةِ لِلْحَجِّ أَوْ الْعُمْرَةِ وَمِنْهُ يُقَالُ مَا حَجَّ وَلَكِنْ دَجَّ فَالْحَجُّ الْقَصْدُ لِلنُّسُكِ وَالدَّجُّ الْقَصْدُ لِلتِّجَارَةِ وَالِاسْمُ الْحِجُّ بِالْكَسْرِ وَالْحِجَّةُ الْمَرَّةُ بِالْكَسْرِ عَلَى غَيْرِ قِيَاسٍ وَالْجَمْعُ حِجَجٌ مِثْلُ: سِدْرَةٍ وَسِدَرٍ قَالَ ثَعْلَبٌ قِيَاسُهُ الْفَتْحُ وَلَمْ يُسْمَعْ مِنْ الْعَرَبِ … وَالْحِجَّةُ أَيْضًا السَّنَةُ … وَالْحُجَّةُ الدَّلِيلُ وَالْبُرْهَانُ وَالْجَمْعُ حُجَجٌ مِثْلُ: غُرْفَةٍ وَغُرَفٍ وَحَاجَّهُ مُحَاجَّةً فَحَجَّهُ يَحُجُّهُ مِنْ بَابِ قَتَلَ إذَا غَلَبَهُ فِي الْحُجَّةِ. وَحِجَاجُ الْعَيْنِ … الْعَظْمُ الْمُسْتَدِيرُ حَوْلَهَا … وَالْمَحَجَّةُ … جَادَّةُ الطَّرِيقِ."
  - Method points visible: model verb (bāb qatala); aṣl → sharʿ narrowing stated with *thumma*; proverb glossed; Thaʿlab: analogy (qiyās) vs what was heard (samāʿ); plurals via model words; the senses "proof", "bone round the eye", "main road" are LISTED with no attempt to connect them to "head for" (true of THIS entry; not generalised).
  - No Qur'an citation, no verse of poetry in this entry.
  - Qur'an cross-refs I add (my own, verified in site text): Q 2:196 "وَأَتِمُّوا الْحَجَّ وَالْعُمْرَةَ لِلَّهِ"; Q 3:97 "وَلِلَّهِ عَلَى النَّاسِ حِجُّ الْبَيْتِ" (ḥijj with kasra = the entry's "والاسم الحج بالكسر"); Q 2:258 "أَلَمْ تَرَ إِلَى الَّذِي حَاجَّ إِبْرَاهِيمَ".
  - Site English check: faithful translation keeps "This is its original sense; then its usage was restricted, in the legal/religious usage (fī al-sharʿ)…". Harmonized says "in **later** legal/religious usage" — "later" is not in the original (thumma = "then"). Minor; reported.
  - Comparison: al-Ṣiḥāḥ displays Hjj (entry 3295): "الحَجُّ: القصد … وقد حَجَّ بنو فُلانٍ فلاناً، إذا أطالوا الاختلاف إليه. قال المخبل: وأشهد من عوف حلولا كثيرة * يحجون سب الزبرقان المزعفرا قال ابن السكيت: يقول يكثرون الاختلاف إليه. هذا الأصلُ، ثم تُعورِفَ استعماله في القصد إلى مكة للنُسك." Whether "هذا الأصل…" is al-Jawharī's or continues Ibn al-Sikkīt's remark is ambiguous → in the guide I attribute it to "the entry", not to a person. al-Fayyūmī lists al-Ṣiḥāḥ among his sources (khātima, vol. 2 p. 711) — I do NOT claim he took this sentence from al-Jawharī.
- **bxl** (id 6283) — chosen, short. "بَخِلَ بَخَلًا وَبُخْلًا مِنْ بَابَيْ تَعِبَ وَقَرُبَ وَالِاسْمُ الْبُخْلُ وِزَانُ فَلْسٍ … وَالْبُخْلُ فِي الشَّرْعِ مَنْعُ الْوَاجِبِ وَعِنْدَ الْعَرَبِ مَنْعُ السَّائِلِ مِمَّا يَفْضُلُ عِنْدَهُ وَأَبْخَلْته بِالْأَلِفِ وَجَدْته بَخِيلًا." Explicit contrast sharʿ vs ʿinda l-ʿArab; no evidence for either; no Qur'an citation. Qur'an refs I add: Q 3:180, Q 47:38 (both verified: يبخلون / يبخل).
  - Side observation (NOT used): stored vowelling "الْبُخْلُ" conflicts with the model word "وزان فلس" (which implies *bakhl*); cannot establish whether printer's vowelling or author's intent → omitted.
  - Site translation: "تَعِبَ (tuʿiba…)" mis-transliterates *taʿiba* — reported.
- **jzy** (id 1201) — chosen, voice-separation reading. Key passage: "قَالَ الْأَزْهَرِيُّ وَالْفُقَهَاءُ يَقُولُونَ فِيهِ أَجْزَى مِنْ غَيْرِ هَمْزٍ وَلَمْ أَجِدْهُ لِأَحَدٍ مِنْ أَئِمَّةِ اللُّغَةِ وَلَكِنْ إنْ هُمِزَ أَجْزَأَ فَهُوَ بِمَعْنَى كَفَى هَذَا لَفْظُهُ وَفِيهِ نَظَرٌ لِأَنَّهُ إنْ أَرَادَ امْتِنَاعَ التَّسْهِيلِ … فَإِنَّ تَسْهِيلَ هَمْزَةِ الطَّرَفِ فِي الْفِعْلِ الْمَزِيدِ وَتَسْهِيلَ الْهَمْزَةِ السَّاكِنَةِ قِيَاسِيٌّ فَيُقَالُ أَرْجَأْتُ الْأَمْرَ وَأَرْجَيْتُهُ … وَأَخْطَأْتُ وَأَخْطَيْتُ … وَتَوَضَّأْتُ وَتَوَضَّيْتُ … فَالْفُقَهَاءُ جَرَى عَلَى أَلْسِنَتِهِمْ التَّخْفِيفُ وَإِنْ أَرَادَ الِامْتِنَاعَ مِنْ وُقُوعِ أَجْزَأَ مَوْقِعَ جَزَى فَقَدْ نَقَلَهُمَا الْأَخْفَشُ لُغَتَيْنِ …". Earlier in entry: "جَزَى الْأَمْرُ يَجْزِي جَزَاءً مِثْلُ: قَضَى يَقْضِي قَضَاءً وَزْنًا وَمَعْنًى وَفِي التَّنْزِيلِ {يَوْمًا لا تَجْزِي نَفْسٌ عَنْ نَفْسٍ شَيْئًا} [البقرة: 48]" and "نَقَلَهُمَا الْأَخْفَشُ بِمَعْنًى وَاحِدٍ فَقَالَ الثُّلَاثِيُّ مِنْ غَيْرِ هَمْزٍ لُغَةُ الْحِجَازِ وَالرُّبَاعِيُّ الْمَهْمُوزُ لُغَةُ تَمِيمٍ".
  - Voices: "ولم أجده" = al-Azharī (inside the quotation, which "هذا لفظه" closes); "وفيه نظر" onward = al-Fayyūmī. Site translation & harmonized English both keep this distinction correctly.
  - Site translation: renders بالألف as "with the connective alif" — wrong term (it is the Form-IV prefix, not hamzat al-waṣl); reported.
- **fDl** (id for fDl) — used briefly. "…وَقَوْلُهُمْ لَا يَمْلِكُ دِرْهَمًا فَضْلًا عَنْ دِينَارٍ … قَالَ قُطْبُ الدِّينِ الشِّيرَازِيُّ فِي شَرْحِ الْمِفْتَاحِ … وَقَالَ شَيْخُنَا أَبُو حَيَّانَ الْأَنْدَلُسِيُّ نَزِيلُ مِصْرَ الْمَحْرُوسَةِ أَبْقَاهُ اللَّهُ تَعَالَى وَلَمْ أَظْفَرْ بِنَصٍّ عَلَى أَنَّ مِثْلَ هَذَا التَّرْكِيبِ مِنْ كَلَامِ الْعَرَبِ وَبَسَطَ الْقَوْلَ فِي هَذِهِ الْمَسْأَلَةِ وَهُوَ قَرِيبٌ مِمَّا تَقَدَّمَ." "لم أظفر" read as Abū Ḥayyān's words (followed by "وبسط القول" = "and he [Abū Ḥayyān] expanded…"); site translation reads it the same way. Slight residual ambiguity (the quotation opens with "و") — I phrase it as "he reports that…".
  - "أبقاه الله" = a blessing used of the living → consistent with composition (734) before Abū Ḥayyān's death (745, per Lane's chronological list). Interpretation, labelled as such.
- **zkw** (id 2180) — used only to illustrate the ʿāmmī/al-ṣawāb convention: "وَقَوْلُهُمْ زَكَاتِيَّةٌ عَامِّيٌّ وَالصَّوَابُ زَكَوِيَّةٌ"; also shows "مِنْ بَابِ قَعَدَ", "بِالْأَلِفِ", "بِالتَّشْدِيدِ", and a reason for a name: "وَسُمِّيَ الْقَدْرُ الْمُخْرَجُ مِنْ الْمَالِ زَكَاةً لِأَنَّهُ سَبَبٌ يُرْجَى بِهِ الزَّكَاءُ". Harmonized English adds "purify" (not in original) — reported.
- **swl**, **rAy** — used in onOurSite (filing of hamzated roots), see §1b.
- **Swm** (id 5681) — examined, rejected as a main example: the lugha→sharʿ statement is introduced by قِيلَ ("it is said"), not asserted in his own voice; Abū ʿUbayda's broad sense + "خيل صيام" half-verse, poet unnamed in the entry. Good material but voice is reported, and Hjj/bxl make the point more cleanly. Harmonized English wrongly presents the qīla line as "al-Fayyūmī's own note" — reported.
- **qbl** (qābūl) — examined: "والقابول هو الساباط هكذا استعمله الغزالي وتبعه الرافعي ولم أظفر بنقل فيه" — shows him checking the jurists' words against lexical transmission. Rejected for space (qābūl is not Qur'anic; entry is 3,688 chars).
- **wsT** — examined: "وَقَوْلُهُمْ الْعَشْرُ الْأَوْسَطُ عَامِّيٌّ وَلَا عِبْرَةَ بِمَا فَشَا عَلَى أَلْسِنَةِ الْعَوَامّ مُخَالِفًا لِمَا نَقَلَهُ أَئِمَّةُ اللُّغَةِ فَقَدْ قَالَ أَبُو سُلَيْمَانَ الْخَطَّابِيُّ وَجَمَاعَةٌ إنَّ لَفْظَ الْحَدِيثِ تَنَاقَلَتْهُ أَيْدِي الْعَجَمِ …" Rejected: where al-Khaṭṭābī's quotation ends is unclear; would need too much space.
- Other *sharʿ* labels seen (not used): Hyy "ثم استعمله الشرع في دعاء مخصوص"; rkE "ثم استعملت في الشرع في هيئة مخصوصة"; ymm "حتى صار التيمم في عرف الشرع…"; wly "لكنه خص في الشرع بولاء العتق"; fqh "والفقه على لسان حملة الشرع علم خاص".

---

## 2. Sources consulted (opened)

1. al-Fayyūmī, **introduction** — Arabic Wikisource, https://ar.wikisource.org/wiki/المصباح_المنير/مقدمة (raw text downloaded); cross-checked word-for-word against the Beirut printing on Shāmila, https://shamela.ws/book/12145/1 (intro pp. 1–2). Identical apart from (وبعد) vs أما بعد.
2. al-Fayyūmī, **khātima** — Wikisource https://ar.wikisource.org/wiki/المصباح_المنير/الخاتمة ; Shāmila ids 3503–3532 = vol. 2 pp. 684–712.
3. **Edition**: al-Fayyūmī, *al-Miṣbāḥ al-Munīr fī Gharīb al-Sharḥ al-Kabīr*, 2 vols, continuous pagination, Beirut: al-Maktaba al-ʿIlmiyya, n.d.; digitised https://shamela.ws/book/12145 (card: "ت نحو ٧٧٠ هـ"; "ترقيم الكتاب موافق للمطبوع").
4. **Ibn Ḥajar al-ʿAsqalānī**, *al-Durar al-Kāmina fī Aʿyān al-Miʾa al-Thāmina*, 2nd ed., Hyderabad: Dāʾirat al-Maʿārif al-ʿUthmāniyya, 1392–96/1972–76, vol. 1, p. 372, no. 787 — https://shamela.ws/book/6674/371.
5. **Sakīna Mawʿid**, "al-Fayyūmī (Aḥmad b. Muḥammad)", *al-Mawsūʿa al-ʿArabiyya*, vol. 15 (Damascus, 2006), p. 90 — https://arab-ency.com.sy/details/8678.
6. **J. A. Haywood**, *Arabic Lexicography: Its History, and Its Place in the General History of Lexicography* (Leiden: Brill, 1960), p. 108 — https://archive.org/details/ArabicLexicographyItsHistoryAndItsPlaceInTheGeneralHistoryOfLexicography-JohnA.Haywood (full text: …/Binder2_djvu.txt). Page: the passage follows the running page number "108" in the OCR; index lists "al-Fayyumi, 108" and "'al-Misbah al-Munir', 108".
7. **E. W. Lane**, *An Arabic-English Lexicon*, Book I, Part 1 (London, 1863), Preface — transcription https://laneslexicon.github.io/lexicon/site/lane/preface/ (page number of the Miṣbāḥ paragraph not securely determinable from the transcription's markers — xvi or xvii — so cited without page).
8. **Wael B. Hallaq**, "Ḡazālī, Abū Ḥāmed Moḥammad, v. As a faqīh", *Encyclopaedia Iranica* X/4 (2000), pp. 372–374 — https://www.iranicaonline.org/articles/gazali/gazali-v-as-a-faqih/ (read in browser; WebFetch gets 403).
9. **Walters Art Museum**, Ms. W.590, catalogue description — https://www.thedigitalwalters.org/Data/WaltersManuscripts/html/W590/description.html
10. Kazuo Morimoto, "Tadwin, al-", *Encyclopaedia Iranica* (2016) — https://www.iranicaonline.org/articles/tadwin-of-rafei/ — consulted for al-Rāfiʿī's dates (b. 555/1160, d. Qazvin 623/1226); **not cited** in the guide (Hallaq suffices for d. 623/1226).
11. hawramani work page + /حجج/ page + /about/ — consulted for edition statement (none found).
Leads only (not cited): Arabic Wikipedia, islamstory.com, tarajm.com.
Not accessible: Baalbaki, *The Arabic Lexicographical Tradition* (2014) — no open text found; Google Books API quota exhausted. EI2/EI3 — no accessible article found.

---

## 3. Claim-by-claim support

**Author / life**
- C1. Aḥmad b. Muḥammad al-Fayyūmī, "then al-Ḥamawī"; grew up in al-Fayyūm; studied/excelled in Arabic with Abū Ḥayyān; moved to Ḥamāh and settled; when al-Malik al-Muʾayyad Ismāʿīl built the Dahsha mosque he appointed him to its preaching (khiṭāba); "learned in language and law"; wrote al-Miṣbāḥ; "كثير الفائدة حسن الإيراد"; his son copied most of it into *Tahdhīb al-Maṭāliʿ*; "seems to have lived past 770". — Ibn Ḥajar, *Durar* vol. 1 p. 372 no. 787: "أحمد بن محمد الفيومي ثم الحموي نشأ بالفيوم واشتغل ومهر وتميز وجمع في العربية عند أبي حيان ثم ارتحل إلى حماة فقطنها ولما بنى الملك المؤيد إسماعيل جامع الدهشة قرره في خطابتها وكان فاضلا عارفا باللغة والفقه صنف في ذلك كتابا سماه المصباح المنير في غريب الشرح الكبير وهو كثير الفائدة حسن الإيراد وقد نقل غالبه ولده في كتاب تهذيب المطالع وكأنه عاش إلى بعد سنة ٧٧٠".
- C2. Full name "أبو العباس أحمد بن محمد بن علي الفيومي المقري" — introduction (opening line), both Wikisource and Shāmila.
- C3. Biographies say little; al-Ziriklī reports a note by Muḥammad b. al-Sābiq al-Ḥamawī on a MS of al-Durar giving death c. 760 — al-Mawsūʿa al-ʿArabiyya: "وهو على شهرته ضنّت كتب التراجم بأخباره … قال الزركلي في الأعلام: «وعلّق محمد بن السّابق الحموي على إحدى النسخ المخطوطة من الدرر الكامنة بأنه توفي في حدود760هـ»". (I have NOT seen al-Ziriklī's *Aʿlām* myself → guide says "a note reported by al-Ziriklī", cited to the encyclopedia.)
- C4. Haywood: "the 'Misbah al-Munir' by the Egyptian al-Fayyumi (died 766/1364)" (p. 108, citing Darwīsh). → three different death dates in circulation; guide reports all three.
- C5. Abū Ḥayyān died 745 — Lane preface chronological list: "Aboo-Ḥeiyán: born in 654: died in 745".
- C6. "our shaykh Abū Ḥayyān … أبقاه الله" — displayed fDl entry (vol. 2 p. 475). "Blessing said of the living" = my interpretation (standard usage), labelled in guide.

**The book: date, purpose, audience, arrangement**
- I-1. Finished last ten days of Shaʿbān 734 — khātima colophon, vol. 2 p. 712: "وَكَانَ الْفَرَاغُ مِنْ تَعْلِيقِهِ عَلَى يَدِ مُؤَلِّفِهِ فِي الْعَشْرِ الْأَوَاخِرِ مِنْ شَعْبَانَ الْمُبَارَكِ سَنَةَ أَرْبَعٍ وَثَلَاثِينَ وَسَبْعِمِائَةٍ". Lane also: "Its author states in it that he finished its composition in the year of the Flight 734." Arab Encyclopedia: "انتهى منه في شعبان سنة734هـ". CE: 734 AH ≈ Sept 1333–Aug 1334; Shaʿbān 734 ≈ April 1334 → "spring 1334".
- I-2. Purpose/origin: "أَمَّا بَعْدُ فَإِنِّي كُنْتُ جَمَعْتُ كِتَابًا فِي غَرِيبِ شَرْحِ الْوَجِيزِ لِلْإِمَامِ الرَّافِعِيِّ وَأَوْسَعْتُ فِيهِ مِنْ تَصَارِيفِ الْكَلِمَةِ وَأَضَفْتُ إلَيْهِ زِيَادَاتٍ مِنْ لُغَةِ غَيْرِهِ وَمِنَ الْأَلْفَاظِ الْمُشْتَبِهَاتِ وَالْمُتَمَاثِلَاتِ وَمِنْ إعْرَابِ الشَّوَاهِدِ وَبَيَانِ مَعَانِيهَا وَغَيْرِ ذَلِكَ مِمَّا تَدْعُو إلَيْهِ حَاجَةُ الْأَدِيبِ الْمَاهِرِ." My translation: "I had compiled a book on the unusual vocabulary of the commentary on al-Wajīz by the imām al-Rāfiʿī; in it I dealt at length with the inflected forms of words, and added material from the language of other [texts], words that resemble and parallel one another, the grammatical analysis of quoted verses and the explanation of their meanings, and other things a skilled man of letters needs."
  - "مِنْ لُغَةِ غَيْرِهِ" — "from the vocabulary of [works] other than it" (i.e. beyond the commentary). Paraphrased as "words from outside the commentary".
- I-3. Earlier arrangement and reason for abridging: "قَسَمْتُ كُلَّ حَرْفٍ مِنْهُ بِاعْتِبَارِ اللَّفْظِ إلَى أَسْمَاءٍ مُنَوَّعَةٍ إلَى مَكْسُورِ الْأَوَّلِ وَمَضْمُومِ الْأَوَّلِ وَمَفْتُوحِ الْأَوَّلِ. وَإِلَى أَفَعَالٍ بِحَسَبِ أَوْزَانِهَا … غَيْرَ أَنَّهُ افْتَرَقَتْ بِالْمَادَّةِ الْوَاحِدَةِ أَبْوَابُهُ فَوَعَرَتْ عَلَى السَّالِكِ شِعَابُهُ … فَأَحْبَبْتُ اخْتِصَارَهُ عَلَى النَّهْجِ الْمَعْرُوفِ وَالسَّبِيلِ الْمَأْلُوفِ لِيَسْهُلَ تَنَاوُلُهُ بِضَمِّ مُنْتَشِرِهِ وَيُقْصَرُ تَطَاوُلُهُ بِنَظْمِ مُنْتَثِرِهِ." My reading: the EARLIER book was arranged by word-shape (nouns by first vowel; verbs by pattern), which scattered one root's material; so he abridged it "on the familiar method", gathering what was scattered. **Disagreement**: al-Mawsūʿa al-ʿArabiyya applies the word-shape division to the Miṣbāḥ itself ("وقد قسّم كلّ حرف منه بحسب اللفظ إلى مكسور الأول ومضمومه ومفتوحه"). The surviving Miṣbāḥ (Shāmila headings "الحاء مع الجيم وما يثلثهما", then (ح ج ب), (ح ج ج)…) is arranged by root, so the encyclopedia's sentence describes the earlier book. The guide follows the introduction.
- I-4. Root order: "مُعْتَبِرًا فِيهِ الْأُصُولَ مُقَدِّمًا الْفَاءَ ثُمَّ الْعَيْنَ" ("taking account of the root letters, placing the first radical first, then the second"). Shāmila section headings "X مع Y وما يثلثهما" confirm grouping by first + second radical. Haywood p. 108 places it among dictionaries that followed al-Zamakhsharī's (alphabetical) arrangement; Arab Encyclopedia: "مراعياً الحرف الأول فالثاني فالثالث، إذ سار على نهج الزمخشري … كما يقول كثير من الباحثين" (attributed to researchers). Guide: "regathered root by root, in alphabetical order of first and second letters" (intro) — no claim about following al-Zamakhsharī.
- I-5. Model words: "وَقَيَّدْتُ مَا يَحْتَاجُ إلَى تَقْيِيدٍ بِأَلْفَاظٍ مَشْهُورَةِ الْبِنَاءِ فَقُلْتُ مِثْلُ فَلْسٍ وَفُلُوسٍ وَقُفْلٍ وَأَقْفَالٍ وَهَمْلٍ وَإِهْمَالٍ وَنَحْوِ ذَلِكَ. وَفِي الْأَفْعَالِ مِثْلُ ضَرَبَ يَضْرِبُ أَوْ مِنْ بَابِ قَتَلَ وَشِبْهِ ذَلِكَ، لَكِنْ إنْ ذُكِرَ الْمَصْدَرُ مَعَ مِثَالٍ دَخَلَ فِي التَّمْثِيلِ وَإِلَّا فَلَا." Translation for guide (abridged with …).
  - Interpretation of "min bāb qatala" = conjugates like qatala/yaqtulu: standard; consistent with Hjj "فحجه يحجه من باب قتل" (yaḥujjuhu). "بابي تعب وقرب" = two patterns (bakhila/yabkhalu; bakhula/yabkhulu).
- I-6. Hamza filing rules (see §1b): "وَإِنْ وَقَعَتِ الْهَمْزَةُ عَيْنًا وَانْكَسَرَ مَا قَبْلَهَا جَعَلْتُهَا مَكَانَ الْيَاءِ نَحْوُ الْبِيرِ وَالذِّيبِ وَإِنِ انْضَمَّ مَا قَبْلَهَا جَعَلْتُهَا مَكَانَ الْوَاوِ لِأَنَّهَا تُسَهَّلُ إلَيْهَا نَحْوُ الْبُؤْسِ. وَكَذَا إنِ انْفَتَحَ مَا قَبْلَهَا لِأَنَّهَا تُسَهَّلُ إلَى الْأَلِفِ وَالْأَلِفُ الْمَجْهُولَةُ كَوَاوٍ كَالْفَأْسِ وَالرَّأْسِ".
- I-7. Did not cover what the Sharḥ already makes clear: "وَأَعْلَمُ أَنِّي لَمْ أَلْتَزِمْ ذِكْرَ مَا وَقَعَ فِي الشَّرْحِ وَاضِحًا وَمُفَسَّرًا".
- I-8. Title: "وَسَمَّيْتُهُ بِالْمِصْبَاحِ الْمُنِيرِ فِي غَرِيبِ الشَّرْحِ الْكَبِيرِ" → titleAr verified.
- I-9. al-Sharḥ al-Kabīr = al-Rāfiʿī's commentary on al-Ghazālī's al-Wajīz: intro "غريب شرح الوجيز للإمام الرافعي"; Walters W.590: "originally written as a gloss on the commentary of ʿAbd al-Karīm al-Rāfiʿī (d. 623 AH / 1226 CE) on al-Wajīz fī al-furūʿ by Abū Ḥāmid Muḥammad ibn Muḥammad al-Ghazzālī (d. 505 AH / 1111 CE), entitled Fatḥ al-ʿazīz ʿalá kitāb al-Wajīz"; Hallaq (Iranica): "Al-Wasīṭ … later abridged as al-Wajīz … ʿAbd-al-Karīm Rāfeʿī (d. 623/1226), another Shafiʿite author, wrote a commentary on al-Wājīz, entitled Fatḥ al-ʿazīz". Shāfiʿī: Hallaq ("another Shafiʿite author"; al-Wajīz among "the five most recognized works in the Shafiʿite school" per Nawawī). "Compact manual" = al-Wajīz is an abridgment (Hallaq) — OK.
- I-10. Khātima audience: vol. 2 p. 711: "وَقَدْ اقْتَصَرْتُ فِي هَذَا الْفَرْعِ أَيْضًا عَلَى مَا يَتَعَلَّقُ بِأَلْفَاظِ الْفُقَهَاءِ وَسَلَكْتُ فِي كَثِيرٍ مِنْهُ مَسَالِكَ التَّعْلِيمِ لِلْمُبْتَدِئِ وَالتَّقْرِيبِ عَلَى الْمُتَوَسِّطِ لِيَكُونَ لِكُلٍّ حَظٌّ حَتَّى فِي كِتَابَتِهِ." Translation: "In this part too I have kept to what concerns the jurists' vocabulary, and in much of it I have followed the ways of teaching the beginner and bringing things within reach of the intermediate student…". Khātima heading (Wikisource): "الخاتمة من الكتاب في مسائل مهمة"; topics (my survey of its paragraphs): hamzated and doubled verbs, transitivity, imperfect vowels, verbal-noun patterns, mafʿal nouns, plurals of paucity/abundance, feminine plurals, gender of body parts, numerals, nisba, names of race-horses, feminine agreement, the elative *afʿal*.
- I-11. ~70 sources and the named list: vol. 2 pp. 711–712: "وَهَذَا مَا وَقَعَ عَلَيْهِ الِاخْتِيَارُ مِنْ اخْتِصَارِ الْمُطَوَّلِ وَكُنْتُ جَمَعْتُ أَصْلَهُ مِنْ نَحْوِ سَبْعِينَ مُصَنَّفًا مَا بَيْنَ مُطَوَّلٍ وَمُخْتَصَرٍ فَمِنْ ذَلِكَ التَّهْذِيبُ لِلْأَزْهَرِيِّ … وَالْمُجْمَلِ لِابْنِ فَارِسٍ … وَإِصْلَاحُ الْمَنْطِقِ لِابْنِ السِّكِّيتِ … وَدِيوَانُ الْأَدَبِ لِلْفَارَابِيِّ وَالصِّحَاحُ لِلْجَوْهَرِيِّ وَالْفَصِيحُ لِثَعْلَبٍ … وَكِتَابُ الْأَفْعَالِ لِابْنِ الْقُوطِيَّةِ … وَأَفْعَالُ ابْنِ الْقَطَّاعِ وَأَسَاسُ الْبَلَاغَةِ لِلزَّمَخْشَرِيِّ وَالْمُغْرِبُ لِلْمُطَرِّزِيِّ …" Note: "this is what was chosen in abridging the long work" — confirms Miṣbāḥ = abridgment of his longer book.
  - "al-Fārābī" in entries = author of Dīwān al-Adab: inference from the source list ("ديوان الأدب للفارابي"); Haywood index "al-Farabi, Abu Ibrahim Ishaq". Guide says "to judge from his source list".
- I-12. Names his authority where a judgement rests on it: vol. 2 p. 712: "وَسَمَّيْتُهُ غَالِبًا فِي مَوَاضِعِهِ حَيْثُ يُبْنَى عَلَيْهِ حُكْمٌ" — "I have usually named it in its place where a judgement is built on it." (*ḥukm* could be a legal ruling or a linguistic judgement; translated neutrally.)
- I-13. Lane: "This is a lexicon similar to the Mughrib, above mentioned; but much more comprehensive … Notwithstanding its title, it comprises a very large collection of classical words and phrases and significations of frequent occurrence; in many instances with more clear and full explanations than I have found elsewhere. I have therefore constantly drawn from it in composing my own lexicon". Abbreviation list: "Mṣb 'The Miṣbáḥ' of El-Feiyoomee". Guide paraphrases; avoids "more clear … than elsewhere" (ranking).
- I-14. Lane's stored entries on our site: regex `\bMsb\b` matches **1,261 of 1,410** displayed Lane entries → "most of the Lane entries on our site".
- I-15. al-Zabīdī quotes it: displayed Tāj entry smw: "في المصباح: قال ابن الأنباري: السماء يذكر ويوءنث. وقال الفراء: التذكير قليل، وهو على معنى السقف…" ; Miṣbāḥ smw (displayed): "وَالسَّمَاءُ الْمُظِلَّةُ لِلْأَرْضِ قَالَ ابْنُ الْأَنْبَارِيِّ تُذَكَّرُ وَتُؤَنَّثُ وَقَالَ الْفَرَّاءُ التَّذْكِيرُ قَلِيلٌ وَهُوَ عَلَى مَعْنَى السَّقْفِ". Match confirmed. (Tāj also: "وفي المصباح: مؤنثة لأنها في معنى السحابة"; "وفي المصباح: الاسم همزته وصل…".)
- I-16. Walters MS copied in Iran 1083/1673 — not used in guide (space).

**Interpretive statements in the guide (mine, labelled or phrased as such)**
- "the two interests this book joins" (language + law) — interpretation of Ibn Ḥajar's description + the book's purpose.
- "His label names a register, not a date" — interpretation; basis: *thumma* orders without dating; Q 2:196 already uses ḥajj/ʿumra for the rites.
- "the senses sit side by side" in Hjj — description of that entry only; explicitly not generalised.
- "records an idiom current among scholars together with a doubt about its pedigree" (fDl) — description of the entry's content (Quṭb al-Dīn al-Shīrāzī explains usage; Abū Ḥayyān found no attestation).

---

## 4. Examples: chosen / rejected
| root | use | why |
|---|---|---|
| Hjj ح ج ج | close reading + comparison with al-Ṣiḥāḥ (both displayed) | clearest aṣl→sharʿ statement in his own voice; model-verb; Thaʿlab qiyās/samāʿ; Qur'anic ḥajj/ḥijj/ḥājja; al-Ṣiḥāḥ gives verse evidence the Miṣbāḥ lacks |
| bxl ب خ ل | short | explicit "fī l-sharʿ" vs "ʿinda l-ʿArab" contrast; Qur'anic bukhl |
| jzy ج ز ي | voice-separation reading | "hādhā lafẓuhu" + "wa-fīhi naẓar"; defends jurists' Arabic by qiyās and al-Akhfash's dialect report; cites Q 2:48 |
| fDl ف ض ل | one paragraph | "our shaykh Abū Ḥayyān" (biography + dating a construction) |
| zkw ز ك و | convention illustration only | ʿāmmī / al-ṣawāb |
| swl, rAy | onOurSite only | filing of hamzated roots; what is/isn't on our pages |
| smw (Tāj + Miṣbāḥ) | later use | al-Zabīdī quotes "al-Miṣbāḥ" |
| Swm, qbl, wsT, Hyy, rkE | rejected | see §1c |

## 5. Open questions / evidence gaps
- Death date unresolved: Ibn Ḥajar "after 770" (hedged: وكأنه); marginal note via al-Ziriklī c. 760 (not seen directly); Haywood 766/1364 (source: Darwīsh, not seen). Site stores 1368 (= c. 770) — defensible, but uncertain.
- Where the book was written (Ḥamāh or Egypt) is not stated in anything I read; colophon gives no place. Guide avoids saying.
- When he moved to Ḥamāh / date of the Dahsha appointment: not established.
- His son's *Tahdhīb al-Maṭāliʿ*: only Ibn Ḥajar's sentence; nothing further seen.
- No modern scholarly monograph or article on the Miṣbāḥ's method was accessible (Baalbaki 2014 not seen). Account of method rests on the author's introduction/khātima, the displayed entries, Haywood's paragraph and Lane's preface.
- Which manuscript(s)/earlier edition the Beirut al-Maktaba al-ʿIlmiyya printing reproduces: not established (no editor named on Shāmila card).
- Whether the full vowelling of the stored text is the author's or the printer's: not established (cf. bxl *al-bukhl* vs "wazān fals").

## 6. Site data issues (for the return value; nothing edited)
1. `rAy` (ر ء ي, 328 Qur'anic occurrences): the Miṣbāḥ panel shows only the `(رء ي)` sub-entry on *al-riʾa* "the lung". The work's treatment of *raʾā/ruʾya* "seeing" is inside its `(ر وي)` entry (ed. vol. 1 p. 246), which is not in the DB.
2. `sAl` (س ء ل): no Miṣbāḥ entry; his treatment of *saʾala* is inside the `س و ل` entry shown on `/root/swl`. A cross-reference would help.
3. `Swm` harmonized English presents the قِيلَ ("it is said") lugha→sharʿ line as "al-Fayyūmī's own note on sharʿ usage".
4. `zkw` harmonized English: "to make one's wealth grow/purify it" — "purify" is not in the original.
5. `bxl` faithful translation: "تَعِبَ (tuʿiba …)" should be *taʿiba*.
6. `jzy` faithful translation: "أَجْزَأَ, with the connective alif" — بالألف here means the Form-IV prefix, not hamzat al-waṣl.
7. `Hjj` harmonized English: "in **later** legal/religious usage" — "later" not in original.
8. Stored date 1368 (≈ 770 AH): consistent with Ibn Ḥajar's hedged "after 770", but the date is disputed (c. 760 per a marginal note reported by al-Ziriklī; 766/1364 in Haywood).
9. 526 Miṣbāḥ entries stored but deferred (not displayed) — not an error, but explains why the work "lacks" many Qur'anic roots on the site.

---

## 7. Addenda (after drafting)

- **Baalbaki 2014** (Google Books id `cme7AwAAQBAJ`, https://books.google.ca/books?id=cme7AwAAQBAJ): index (p. 484) lists "al-Miṣbāḥ al-munīr (Fayyūmī) 83" — a single mention. Page 83 is not viewable in the preview, so I could not read what Baalbaki says; **not cited**.
- **Khātima audience sentence** ("وَقَدْ اقْتَصَرْتُ فِي هَذَا الْفَرْعِ أَيْضًا عَلَى مَا يَتَعَلَّقُ بِأَلْفَاظِ الْفُقَهَاءِ …") stands at the end of the last *faṣl* (on the elative *afʿal*); "this branch too" may refer to that chapter or to the whole closing section. The guide therefore says "At the end of the grammatical section … al-Fayyūmī says he has kept to …" without claiming the restriction for every chapter.
- **Qur'an-citation formulas** in the 901 displayed entries: "قوله تعالى" 100 entries, "وفي التنزيل" 63, "قال تعالى" 33 → guide says "with formulas such as *wa-fī l-tanzīl*" (not "usually").
- **ʿāmmī + al-ṣawāb**: ʿāmmī in 8 displayed entries (Axr, Sdq, zkw, vwb, Ewm[nisba sense, not a verdict], HSr, wsT, Emm[nisba]); paired with الصواب only in zkw → guide says "sometimes paired".
- **Lane "Msb"**: `\bMsb\b` in 1,261 of 1,410 displayed Lane entries.
- Rendering checked at http://localhost:4000/classical-dictionaries/al-misbah-al-munir (header, blockquotes, excerpts, onOurSite, sources list render). Deep link `/root/jzy#dict-al-fayyumi-…` opens and scrolls to the Miṣbāḥ entry.
- Validator: 0 errors, 0 warnings; 1,099 words (lede + body, excluding excerpts); 10 root links (Hjj ×2 dictionaries, bxl, jzy, fDl, zkw, smw ×2 dictionaries, swl, rAy); 3 excerpts.

### Final list of what the guide asserts about each linked root
- Hjj (Miṣbāḥ): excerpt + nouns list (ḥijj; ḥijja + Thaʿlab; ḥujja; ḥājjahu; ḥijāj al-ʿayn; maḥajja; model-word plurals). No evidence for the aṣl sense; senses not derived from one another (this entry only).
- Hjj (al-Ṣiḥāḥ): "هذا الأصلُ، ثم تُعورِفَ استعماله في القصد إلى مكة للنُسك" + verse of al-Mukhabbal; attributed to "the same root in al-Jawharī's al-Ṣiḥāḥ" (the entry), not to a speaker.
- bxl: excerpt; no evidence; no Qur'an citation in the entry.
- jzy: jazā = qaḍā "wazn wa-maʿnā", Q 2:48 cited; al-Azharī quote closed by هذا لفظه; وفيه نظر = al-Fayyūmī; tashīl regular (أخطأت/أخطيت، توضأت/توضيت); "فالفقهاء جرى على ألسنتهم التخفيف"; al-Akhfash Ḥijāz/Tamīm.
- fDl: faḍlan ʿan idiom; "شيخنا أبو حيان … أبقاه الله تعالى"; Abū Ḥayyān found no text (لم أظفر بنص) that the construction is Arab speech.
- zkw: "وقولهم زكاتية عامي والصواب زكوية".
- smw (Tāj): "في المصباح: قال ابن الأنباري: السماء يذكر ويؤنث"; smw (Miṣbāḥ): "قال ابن الأنباري تذكر وتؤنث".
- swl: contains سأل ("وسألت الله العافية طلبتها سؤالا ومسألة …").
- rAy: only "(رء ي) الرئة …".

---

## 8. Revision round 1 addenda (reviser, 2026-09-26)

Re-counts over the 901 displayed entries (`_dict_guide_tool.py grep`, vowel marks ignored):
- `«` quotations 99 (overwhelmingly hadith; wider hadith-marker regex 143 incl. false positives); `وفي الحديث` 27; `الحديث` 58.
- Poetry: strict markers (قال الشاعر|الراجز|أنشد|قال الآخر + 12 named poets) 59; hemistich `...` 44; union 70.
- `الشرع|شرعا|شرعي|شرعية` 31 entries; with `اصطلاح` 42 (اصطلاح is mostly grammarians'/jurisprudents' technical usage, not a sharʿ-narrowing note).
- Footnote call-numbers "(n)" left in stored text without the notes: 12 entries (Aty ArD Ax* Axr Abw Ajr A*n Axw vny Aby Abl Abb). Shamela 12145 id 17 "(ء ت ي)" shows the matching footnote "(١) العَجَّاجُ." naming the poet.
- Medial-hamza filing (intro, Wikisource raw text): after kasra → yāʾ; after ḍamma → wāw; after fatḥa → also wāw ("لأنها تسهل إلى الألف والألف المجهولة كواو كالفأس والرأس"). Shamela id 1253 "(ر وي)" (vol. 1 pp. 246–247) contains "ورأيت الشيء رؤية أبصرته بحاسة البصر"; its section index puts "(رء س)" between "(ر ود)" and "(ر وض)".
- Arab Encyclopedia 8678 re-opened: the c. 760 date is Muḥammad b. al-Sābiq al-Ḥamawī's note on a manuscript of *al-Durar al-Kāmina*, as quoted from al-Ziriklī's *Aʿlām*.
- Lane preface abbreviation list: "†Mṣb" ; site Lane text uses "Msb" (1,261/1,410 entries), never "Mṣb".
