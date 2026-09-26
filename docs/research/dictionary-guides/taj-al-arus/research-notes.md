# Research notes — Tāj al-ʿArūs (guide slug `taj-al-arus`)

Dictionary slug on site: `murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus` · site label "Tāj al-ʿArūs | تاج العروس | Murtaḍā al-Zabīdī | stored date 1790 | ar | 1600 displayed entries".

Drafted 2026-09-26. Everything cited below was opened and read during drafting (curl or WebFetch; HTTP 200). Scratch copies of downloaded pages were kept in the session scratchpad only.

---

## 1. What al-nuqta displays

Tool: `python3 roots/backend/_dict_guide_tool.py …` (read-only; displayed entries only). DB queries read-only (`file:data/quran.db?mode=ro`).

- `dicts`: 1,600 displayed entries.
- Entries read in full or at length (original + site translation + harmonized): صلح SlH, فسد fsd, صلو Slw (first ~9,000 chars and all English), دين dyn, دسو dsw, سوح swH; key passages of رحم rHm, كفر kfr, فكر fkr, عرض ErD, نفس nfs, خلق xlq, قبل qbl.
- Length: median ≈ 7,460 characters; max عرض ErD 83,177; min دسو dsw 195. Very short ones are genuinely short Tāj entries (دسو, سوح), except دين (below).
- **Source text / edition.** hawramani names no edition for the Tāj. Its landing page (https://arabiclexicon.hawramani.com/murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus/) says only: "the largest dictionary of the Arabic language ever written, comprising 11,800 pages … a commentary on the 15th-century Qāmūs al-Muḥīṭ of Firuzabadi", author "d. 1790 CE / 1205 AH", "from Belgram in West Bengal, India" (sic; Bilgram is not in Bengal — see §3). Homepage (https://arabiclexicon.hawramani.com/) names sources only for Lane and Salmoné; for the rest: "All texts belong to the public domain." The section heading on root pages is "Murtaḍa al-Zabīdī, Tāj al-ʿArūs fī Jawāhir al-Qamūs (d. 1790 CE)".
- **Comparison with al-Maktaba al-Shāmila (book 7030).** Shāmila card: publisher Kuwait Ministry of Guidance and Information / National Council for Culture, Arts and Letters, 40 vols, 1385–1422 AH / 1965–2001; "ترقيم الكتاب موافق للمطبوع". I located صلح at Shāmila pages 3326–3330 = vol. 6, pp. 547–551 (https://shamela.ws/book/7030/3326 …/3330). Our stored entry is the same text word for word, flattened into one paragraph, INCLUDING: the lacuna marker "(سقط: لم يستكن لتهدد وتنمر", the misprint "من سَجَات الأَساس" (for سَجَعات), "وَسموا صلاخا" (for صلاحا), the loss of vowel marks from "(و) رأى الإمام (المصلحة)" onward, and the stray ")" after "وأتتنى صالحة من فلان.". Other Shāmila pages sampled (vol. 3 p. ~ /2786, vol. 6 /3100, vol. 30 /15587) show the same quirks as our text (stray "{" "}" before headwords; spellings هاكذا، ذالك، لاكن). Shāmila's copy ends "(سقط: من منتصف الصفحة (٥٧٢) حتى نهاية الكتاب.)" (https://shamela.ws/book/7030/21562).
  → Guide says: "Where we compared them, it matches word for word, gaps and misprints included, the digital text in al-Maktaba al-Shāmila, which that library identifies with the Kuwait edition (1965–2001)." Do NOT claim hawramani took it from Shāmila, or that it IS the printed Kuwait text (the digital text's lacunae and vowelling may differ from print; not checked against the printed volumes).
- **Bracket marking.** In the stored text the Qāmūs's words are in round brackets in about two thirds of entries. Heuristic count (bracket groups not containing "..." verse separators and not sura refs): 526 of 1,600 entries have fewer than 3 such groups, i.e. effectively NO Qāmūs marking; they cluster by final radical (ل 84, ر 70, ع 66, ق 54, ف 51, س 47, ط 29, ض 28 …), i.e. by volumes of the digital text. Examples: عرض ErD (0), خلف xlf, قبل qbl, نفس nfs, خلق xlq, كفر kfr (brackets only around verse lines). Shāmila vol. 30 (e.g. [عضل], /15587) is likewise unbracketed, so the loss is in the digital source, not our scrape. → guide: "roughly a third … by our count".
- Other features: curly braces {…} usually around Qur'an quotations, often with sura name and verse number in round brackets after them; stray "{", "}" and "!" before headwords (1,088 entries contain { or }, 653 contain !); poetry hemistichs joined by "..." inside round brackets (Kuwait layout flattened).
- **Lacuna markers** "(سقط: …)" in 19 displayed entries, e.g. كذب k*b, صلح SlH, قعد qEd, صنع SnE ("(سقط: الصفحة كاملة)"), نطق nTq ("(سقط: آخر الصفحة رقم (425) .)"), مزق mzq ("(سقط: من بداية الصفحة (390) حتى نهاية الصفحة (391) .)"), حصل HSl.
- **Defective entry دين (dyn), entry_id 1388.** Stored original = first line of the Tāj article (الدين: ما له أجل … قاله المناوي … وما لا أجل له فقرض) and then a passage belonging to دهقن (التدهقن: التكيس …). hawramani's own دين page has exactly this text (fetched https://arabiclexicon.hawramani.com/دين/ , anchor 081eb7a3a88cd208c681196bdd37a1cd) — so the defect is upstream. The site's translation and harmonized English both flag the intrusion. For Qur'an readers this means the Tāj's treatment of dīn (religion/judgement) is simply absent on our site.
- Recurring expressions (grep, vowels ignored): "ومما يستدرك" 1,404 entries; "قلت" 1,057 (incl. other uses; "قلت: " 927); "شيخنا" 833 ("قال شيخنا" 595); "المصنف" 750; "المجاز" 908; "الصحاح" 1,029; "الأساس" 782; "اللسان" 665; "التهذيب" 655; "المحكم" 651; "العباب" 414; "المصباح" 236; "البصائر" 158; "المفردات" 85.
- Abbreviations of the Qāmūs visible inside brackets, e.g. SlH "(والصالحية: ة قرب الرهى)" (ة = village), "(ج …)" for plural (1,321 entries match "ج ").
- Cross-references to the book's own order, e.g. SlH "والبابة: النوع، وقد تقدم" (the root ب و ب comes earlier in rhyme order); nfs "وسيأتي الكلام عليها قريبا".

---

## 2. Claims in the guide and their sources

### Title, author, dates

| Claim | Source | Passage |
|---|---|---|
| Title تاج العروس من جواهر القاموس (with *min*) | al-Zabīdī intro, Kuwait ed. vol. 1 p. 11 (Shāmila https://shamela.ws/book/7030/11) | "وسميته. (تَاج الْعَرُوس من جَوَاهِر الْقَامُوس) ." |
| Kunya Abū l-Fayḍ; name Muḥammad b. Muḥammad …, known as Murtaḍā, al-Ḥusaynī al-Zabīdī | al-Jabartī, ʿAjāʾib al-āthār (Dār al-Jīl), vol. 2 pp. 104–105 (Shāmila https://shamela.ws/book/11998/802 , /803) | "الشيخ أبو [الفيض — Shāmila prints القبض] السيد محمد بن محمد بن محمد بن عبد الرزاق الشهير بمرتضى الحسيني الزبيدي الحنفي"; p. 105: "وكناه سيدنا السيد أبو الأنوار بن وفا بابي الفيض … سنة اثنتين وثمانين ومائة وألف". NB Baalbaki 2019 bibliography has "Abū l-Faḍl Muḥammad Murtaḍā" — disagreement; guide follows al-Jabartī. |
| Born 1145 AH (= 24 Jun 1732 – 12 Jun 1733, tabular conversion) | al-Jabartī vol. 2 p. 104 | "ولد سنة خمس واربعين ومائة وألف كما سمعته من لفظه ورايته بخطه" |
| Birthplace Bilgram per later sources; al-Jabartī silent | Kuwait ed. vol. 1, Farrāj's introduction, section "التعريف بالزبيدي" (archive.org ZUB1965AR, file "1 - تاج العروس", OCR) | "وتلميذه الجبرتي الذي جالسه كثيرا لم يذكر لنا البلد الذي ولد فيه، أما كتاب أبجد العلوم وكتاب نشر العرف وكتاب فهرس الفهارس وطابعو تاج العروس الطبعة الثانية فقد ذكروا أنه ولد ببلد هندي هو بلجرام" (OCR normalised). Guide says "in India", not a region. |
| Travelled for study in the Hijaz and Yemen | al-Jabartī vol. 2 p. 104 | "ونشأ ببلاده وارتحل في طلب العلم وحج مرارا … ونزل بالطائف بعد ذهابه إلى اليمن ورجوعه في سنة ست وستين" |
| Reached Cairo 1167 AH (9 Ṣafar 1167 = 6 Dec 1753) | al-Jabartī vol. 2 p. 104; Lane Preface p. xviii ("came to Cairo A.D. 1753") | "ثم ورد إلى مصر في تاسع صفر سنة سبع وستين ومائة وألف" |
| al-Jabartī was his student | al-Jabartī vol. 2 p. 103 | "ومات شيخنا علم الأعلام …" |
| Died of plague in Shaʿbān 1205 (≈ 5 Apr – 3 May 1791, tabular conversion) in Cairo; buried beside his wife at the shrine of al-Sayyida Ruqayya | al-Jabartī vol. 2 pp. 112–113 (https://shamela.ws/book/11998/810 , /811); obituary is in the list "من مات في هذه السنة" of 1205 (p. 103) | "وأصيب بالطاعون في شهر شعبان وذلك أنه صلى الجمعة في مسجد الكردي المواجه لداره فطعن … وتوفي يوم الأحد"; Lane p. xviii: "died A.D. 1791 (in the year of the Flight 1205)". Farrāj (Kuwait vol. 1) repeats: "وتوفي يوم الأحد في شعبان سنة 1205". |
| Work took "fourteen years and some days" (his own note) | Lane, Preface p. xviii (archive.org anarabicenglish03lanegoog, djvu text line ~705) | "At the end of a copy of it in his own handwriting, he states that it occupied him fourteen years and some days." |
| Banquet for completion 1181 AH (1767–68) | al-Jabartī vol. 2 p. 105 | "وشرع في شرح القاموس حتى أتمه في عدة سنين في نحو أربعة عشر مجلدا وسماه تاج العروس ولما أكمله أولم وليمة حافلة … وذلك في سنة احدى وثمانين ومائة وألف" (Lane p. xviii follows: "finished the Táj el-'Aroos A.D. 1767 or 1768") |
| End of work Rajab 1188 (Sept–Oct 1774); banquet = completion of first part | Kuwait vol. 1, Farrāj's introduction, section "احتفال الزبيدي بإنجاز التاج" and the list of dated letter-endings | "إن المؤلف نفسه وهو الزبيدى نص على أنه أنجزه سنة ١١٨[٨] هجرية، وإذن تكون الوليمة … مناسبة إنجازه الجزء الأول"; "وإذا رجعنا إلى أواخر المواد في تاج العروس نجد أن آخر حرف الذال كان في ربيع الأول سنة 1187 [OCR] بخان الصاغة … وآخر الكتاب في رجب سنة 1188 بمنزله في عطفة الغسال". (OCR digits are unreliable in places — "١184" appears where 1188 is meant; the last line is legible as 1188.) Wikipedia (lead only) gives "begun 1760 … concluded … 8 September 1774", citing Reichmuth 2009 — consistent, not independently checked. |
| "1760s and 1770s" (lede) | Lane p. xviii ("commenced, in Cairo, soon after the middle of the last century"); Farrāj (end 1188/1774) | — |

**Date disagreement to report:** stored 1790 vs death Shaʿbān 1205 = spring 1791. Sources for 1791: al-Jabartī (month), Lane p. xviii, Reichmuth's book title "(1732–91)" (archive.org metadata, not read). Sources giving 1790: Baalbaki 2019 pp. 202–203 ("Zabīdī's (d. 1205/1790)"), hawramani, English Wikipedia. The 1790 figure is best explained as the CE year in which 1205 AH began (1 Muḥarram 1205 ≈ 10 Sept 1790). Guide uses "d. 1205 AH / 1791 CE".

### Purpose, plan, audience (al-Zabīdī's introduction, Kuwait ed. vol. 1, Shāmila pages 2–11 = printed pp. 2–11)

- p. 2: the Qāmūs admired for concision: "حَيْثُ أَوْجَزَ لفظَه وأشْبَعَ مَعْنَاهُ، وقَصَّرَ عِبارَته وَأطَال مَغْزاه"; describes its arrangement: "بَوَّبَه فأَورَد فِي كلِّ بابٍ من الحروفِ مَا فِي أوّله الْهَمْز، ثمَّ قَفَّى على أثرِه بِمَا فِي أَوّله الْبَاء …".
- pp. 2–3: "(وَلما) كَانَ إبرازُه فِي غَايَة الإيجاز … تَصدَّى لكشف غوامضه ودقائقه رجالٌ من أهل الْعلم" — then lists commentators.
- p. 3: teacher: "وَمن أَجمع مَا كُتِب عَلَيْهِ مِمَّا سمعتُ ورأيتُ شرحُ شَيخنَا الإِمَام اللغويّ أبي عبد الله مُحَمَّد بن الطّيِّب بن مُحَمَّد الفاسيّ، المتولّد بفاس سنة ١١١٠، والمتوفَّى بِالْمَدِينَةِ المنوَّرة سنة ١١٧٠، وَهُوَ عُمدتي فِي هَذَا الفنّ … وشَرحُه هَذَا عِنْدِي فِي مجلّدين ضخمين." → guide: "among the fullest … his teacher … 'my mainstay in this discipline'" (translation for the guide). (Guide originally said "valued most" — corrected to "among the fullest", matching من أجمع.)
- p. 4: "وَقد تكفل شيخُنا بالرّدّ عَلَيْهِ" and "ينْقل عَنْهَا شَيخنَا كثيرا" — "shaykhunā" in the intro = al-Fāsī.
- p. 4 (audience): "فَلَمَّا آنست من تَناهِي فاقَةِ الأفاضل إِلَى استكشافِ غوامِضه … وَلَا سيّما من انتدب مِنْهُم لتدريس علم غَرِيب الحَدِيث، وإقراء الكُتب الْكِبَار من قوانين الْعَرَبيَّة".
- pp. 4–5 (plan): "فِي وضع شرحٍ عَلَيْهِ، ممزوجِ الْعبارَة، جامعٍ لموادّه بالتصريح فِي بعضٍ وَفِي الْبَعْض بِالْإِشَارَةِ، وافٍ بِبَيَان مَا اختلَف من نُسخه، والتصويب لما صحّ مِنْهَا مِن صَحِيح الأُصول، حاوٍ لذِكْر نُكَتِه ونوادِره، والكشفِ عَن مَعَانِيه والإنباه عَن مَضارِبه ومآخذه بصرِيح النُّقول، والتقاطِ أبياتِ الشواهد لَهُ".
- p. 5: "ونقلْتُ بِالْمُبَاشرَةِ لَا بالوسائط عَنْهَا، لَكِن على نُقصانٍ فِي بَعْضهَا" (not used in the guide, recorded for the verifier: he claims direct quotation; Lane's collation qualifies this).
- pp. 5–9: the source list — Ṣiḥāḥ (Yāqūt's hand, Azbak library), Tahdhīb (16 vols), Muḥkam (8 vols), Ibn al-Qaṭṭāʿ, **Lisān al-ʿArab (28 vols)**, Tahdhīb al-Tahdhīb, al-Gharībayn, al-Nihāya, … al-ʿUbāb & al-Takmila (Ṣarghatmish library), al-Miṣbāḥ, Mukhtār al-Ṣiḥāḥ, Asās/Fāʾiq/Mustaqṣā, Jamhara, … al-Mufradāt of al-Rāghib, … Tārīkh Dimashq, Tārīkh Baghdād, genealogies (Jamharat al-ansāb of Ibn Ḥazm, etc.), medicine (al-Tadhkira fī l-ṭibb of Dāwūd al-Anṭākī), botany (Kitāb al-Nabāt of Abū Ḥanīfa al-Dīnawarī) … "وَغير ذَلِك من الْكتب … مِمَّا يطول على النَّاظر استقصاؤها". Count "more than a hundred": Lane p. xviii ("more than a hundred are enumerated"); Farrāj ("وهى أكثر من مائة"). Haywood p. 89 says he "lists about 500 authors" — a different count (authors, not works); not used.
- p. 7: "وبصائر ذَوي التَّمْيِيز … والبُلغة … وترقيق الأَسل … وَالرَّوْض المسلوف … والمثلثات، الأَربعة للْمُصَنف" — Baṣāʾir etc. are al-Fīrūzābādī's → *al-muṣannif* = al-Fīrūzābādī. (Also فسد entry: "ونقل المصنف في البصائر".)
- "In Cairo's libraries he found many of …": intro names Cairo mosque libraries (خزانة الأمير أزبك، خزانة الأمير صرغتمش، خزانة المؤيد، خزانة الملك الأشرف قايتباي); Farrāj: "وقد ظفر فى مصر بأمهات الكتب … ولا يعقل أنه استحضرها معه" (OCR partly garbled). Lane p. xviii–xix renders the libraries as those "of the collegiate mosque" of Azbak etc.
- p. 10 (modesty + disclaimers): "وَأَنا مَعَ ذَلِك لَا أَدّعي فِيهِ دَعْوَى فأَقول: شافَهْتُ، أَو سَمِعت، أَو شَددْتُ، أَو رحَلت، أَو أَخطأَ فلانٌ أَو أَصاب، أَو غَلِطَ القائلُ فِي الْخطاب، فكلُّ هَذِه الدَّعاوَى لم يَترك فِيهَا شيخُنا لقائلٍ مقَالا … وَلَيْسَ لي فِي هَذَا الشَّرْح فضيلةٌ أَمُتُّ بهَا، وَلَا وَسِيلَة أَتمسّك بهَا، سوى أنني جمعتُ فِيهِ مَا تفرّق فِي تِلْكَ الكُتب من مَنْطُوق وَمَفْهُوم … فعُهدتُه على المصنِّف الأول … لِأَنِّي عَن كلِّ كتابٍ نَقلتُ مَضمونه، فَلم أُبدِّل شَيْئا". Guide quotes the "no merit … except gathering" sentence (with an ellipsis) and paraphrases the disclaimer as "no claim to have heard words face to face or travelled for them (nor … to judge who erred …)". Interpretive note: شافهت/سمعت/شددت/رحلت are the classic claims of hearing Arabs directly and travelling to collect; he also disclaims "so-and-so erred or was right", saying his teacher left nothing to add — the guide notes that in practice he does judge (قلت in رحم, كفر).
- p. 11 (motive): "فإنني لم أقصد سوى حِفظِ هَذِه اللُّغَة الشَّرِيفَة، إِذْ عَلَيْهَا مَدار أَحكامِ الْكتاب الْعَزِيز والسُّنّة النبويّة".

### Two voices / conventions

- Autograph overline → red ink in students' copies → round brackets in print: Kuwait vol. 1, Farrāj, section "طريقة تاج العروس": "أما القاموس وشرحه تاج العروس فإنه لو أزيلت الحدود التى تفصل بين المتن والشرح لكان من الصعب معرفة ما لهذا أو ما لذاك … وفي النسخة التى بخط الزبيدى كان يضع كلمة القاموس وفوقها خط، فلما نسخه تلاميذه جعلوا كلمة القاموس باللون الأحمر وكلام الشارح الزبيدى باللون الأسود. وحينما طبع التاج رئي أن تكون كلمة صاحب القاموس بين قوسين والشرح مطلقا من الأقواس. وهذا ما سرنا عليه فى الطبعة الجديدة" (OCR normalised). Same section: "والزبيدى ينسب كثيرا من التفسير اللغوى إلى قائليه، إرجاعا لمتن القاموس إلى أصوله … وبعد انتهاء المادة … يستدرك ما نقص".
- Haywood, Arabic Lexicography (1960) p. 89: "The method of the author of the 'Taj' was to put the contents of the 'Qamus' in brackets, interpolating commentary material." (archive.org in.gov.ignca.12555, djvu text lines 5239–5241; page header "89".)
- انتهى = end of quotation: Lane's own entry نهي on our site (displayed, william-edward-lane…): "انتهى It is ended: a word put to mark the end of a quotation." Guide links [[root:nhy|william-edward-lane-arabic-english-lexicon|ن ه ي]].
- قلت = al-Zabīdī's own voice: observed (e.g. رحم, كفر, قبل, أيي). No external citation in the guide.

### Lane, the Lisān, and borrowing

- Lane, Preface (Book I Part 1, 1863), p. xviii: description of the Tāj ("a compilation from the best and most copious of the preceding Arabic lexicons … in the form of an interwoven commentary on the Ḳámoos … corrections of mistakes … examples in prose and verse; and a very large collection of additional words"); "though I believe that it was mainly derived in the first instance from the Lisán el-'Arab, more than a hundred are enumerated by the seyyid Murtaḍà in his preface".
- p. xix: "As the Táj el-'Aroos is the medium through which I have drawn most of the contents of my lexicon …" (page from the laneslexicon.github.io transcription https://laneslexicon.github.io/lexicon/site/lane/preface/ , where page marker "xix" precedes this paragraph; the archive.org Google scan omits p. xix).
- p. xx: "I was therefore obliged to make a most laborious collation of passages quoted in it with the same passages in the works quoted: and in every instance I found that they had been faithfully transcribed … in most of the articles in the former, from three-fourths to about nine-tenths of the additions to the text of the Ḳámoos, and in many articles the whole of those additions, existed verbatim in the Lisán el-'Arab. I cannot, therefore, acquit the seyyid Murtaḍà of a want of candour …" (archive.org scan lines 722–740, header "XX").
- Lane also: the rumour that someone else wrote the Tāj — "I did not find to be credited by any of the learned, nor do I myself believe it" (p. xix–xx). Not used in the guide (no evidence for it; mentioning would give it air). Recorded here for completeness.
- Lane (p. xviii–xix): copies of the Tāj often omit vowel signs ("syllabical signs, which are too often omitted in the copies of the Táj el-'Aroos"). Farrāj: earlier printings (5 parts, al-Maṭbaʿa al-Wahbiyya; then 10 parts) "خاليتان من الضبط", and "عدم الضبط يرجع إلى الزبيدى نفسه، فإن ما وجد من التاج بخطه غير مضبوط". Not used in the guide (word limit) — useful for the verifier: the vowel marks in our stored text are editorial/digital, not al-Zabīdī's.
- Farrāj: al-Zabīdī "في مقدمته … نقل ثمانية وعشرين سطرا من مقدمة ابن منظور فى كتابه اللسان، دون أن يشير إلى ذلك" (compares Lisān "فجاء هذا الكتاب بحمد الله واضح المنهج سهل السلوك …" with Tāj "فجاء بحمد الله تعالى هذا الشرح واضح المنهج كثير الفائدة سهل السلوك …"; I confirmed the Tāj wording on Shāmila p. 9).
- Baalbaki, "The Notion of gharīb in Arabic Lexica", JAS 6 (2019) p. 203: "al-Zabīdī (d. 1205/1790), in spite of utilizing the Lisān as one of his major sources in Tāj al-ʿarūs, refers independently to Ibn al-Athīr's al-Nihāya among the works which he directly consulted, rather than through secondary sources" (n. 85: Tāj I, 4–5, Khayriyya ed.). Guide: "Baalbaki counts the Lisān among his major sources."
- Haywood p. 89–90 quotes Lane's complaint and adds that the Tāj "has never replaced the 'Lisan' in Arab estimation" and is "comparatively deficient in its illustrative examples" (p. ~83) — evaluative; NOT used (no ranking).

### Arrangement (for onOurSite "already mentioned / will come")

- Haywood p. 88: "First we must accept that the choice of the rhyme order was deliberate and considered" (of the Qāmūs). Al-Zabīdī intro p. 2 describes the Qāmūs's arrangement. Shāmila headings in the Tāj: e.g. "(فصل الْفَاء) مَعَ الْحَاء الْمُهْملَة) [فتح]" (/3373) — i.e. chapter of final ḥāʾ, section of initial fāʾ.

### Abbreviations (onOurSite)

- al-Fīrūzābādī, introduction to al-Qāmūs (IslamWeb text, page marker [ص: 40]): "مكتفيا بكتابة ع، د، ة، ج، م، عن قولي: موضع، وبلد، وقرية، والجمع، ومعروف." URL https://islamweb.net/ar/library/index.php?page=bookcontents&idfrom=1&idto=1&bk_no=123&ID=2 (edition not named on the page; cited as "IslamWeb library text").

### al-Khafājī's dates

- al-Maktaba al-Shāmila author page https://shamela.ws/author/711 : "الشهاب الخفاجي (٩٧٧ - ١٠٦٩ هـ = ١٥٦٩ - ١٦٥٩ م) أحمد بن محمد بن عمر، شهاب الدين الخفاجي المصري • قاضي القضاة وصاحب التصانيف في الأدب واللغة". Identification of the Tāj's "الخفاجي" / "الشهاب" with him: Tāj intro p. 4 ("وللشهاب الخفاجي في العناية محاورات معه … ينقل عنها شيخنا كثيرا") and p. 9 ("وشرح الشفاء، للشهاب الخفاجي"). The SlH entry cites "(شرح الشفاء)" of "الشهاب" in its first lines.

---

## 3. Examples

### Chosen

1. **فسد fsd — close reading.** Displayed in Tāj (entry id via API), al-Qāmūs (firuzabadi-al-qamus-al-muhit) and Lisān (ibn-manzur-lisan-al-arab). All three linked.
   - Qāmūs stored: "فَسَدَ، كنَصَرَ وعَقضدَ وكَرُمَ، فَساداً وفُسوداً: ضِدُّ صَلُحَ، فهو فاسِدٌ وفَسيدٌ من فَسْدَى، ولم يُسْمَعْ: انْفَسَدَ. والفَسادُ: أخْذُ المالِ ظُلْماً، والجَدْبُ. والمَفْسَدَةُ: ضِدُّ المَصْلَحَةِ. …" (note typo عقضد in our Qāmūs copy — for the Qāmūs guide).
   - Tāj: every bracketed segment reassembles the Qāmūs line: (فَسَدَ) (كنَصَر، وعَقَدَ، وكَرُمَ) (فَساداً) (وفُسُوداً) (ضِدُّ صَلَحَ) (فَهُوَ فاسِدٌ وفَسِيدٌ) (مِن) (فَسْدَى) (وَلم يُسْمَع) (انْفَسَدَ) (والفَسَادُ: أَخْذُ المالِ ظُلْماً) (و) (الجَدْبُ) (والمَفْسَدةُ ضِدُّ المَصْلَحَةِ) (وفَسَّدَه تَفْسِيداً أَفْسَدَهُ) (وتفاسَدُوا: قَطَعُوا الأَرْحَامَ) (واسْتفْسَدَ) (ضِدُّ استصْلَحَ).
   - Commentary attributes "taking property wrongfully" to Muslim al-Baṭīn's interpretation of Q 28:83 ("هكاذا فسر مسلم البطين قوله تعالى …") and "drought" to al-Zajjāj's reading of Q 30:41 ("الفساد هنا: الجدب في البر، والقحط في البحر، أي في المدن التي على الأنهار، وهاذا قول الزجاج"). Teacher: "وقد اختلفت عباراتهم في معناه، فقيل: فسد الشيء: بطل واضمحل، ويكون بمعنى تغير، ومن الأول عند الأكثر: {لو كان فيهما آلهة إلا الله لفسدتا}". Also Sībawayh on فسدى; verses (إن الشباب والفراغ والجده …؛ Abū Jundab al-Hudhalī …؛ يمددن بالثدي …); ʿAbd al-Malik b. Marwān report; hadith "كره عشر خلال منها إفساد الصبي غير محرمه … أنه كرهه ولم يبلغ به حد التحريم"; "حرب الفساد … بين بني شك وغوث من طيئ"; Asās saying.
   - Lisān stored entry contains: Sībawayh (جمعوه جمع هلكى), the three verses, the ʿAbd al-Malik report, the hadith, and "وقوله عز وجل: ظهر الفساد في البر والبحر؛ الفساد هنا: الجدب في البر والقحط في البحر أي في المدن التي على الأنهار؛ هذا قول الزجاجي". It does NOT contain Muslim al-Baṭīn, the teacher's remarks, حرب الفساد, or the Asās saying. → one-entry illustration of Lane's finding; the guide says so and does not generalise.
   - Uncertainty: Lisān has "الزجاجي", Tāj "الزجاج" — noted in guide ("credited there to 'al-Zajjājī'"). Identity/date of Muslim al-Baṭīn not researched; guide names him only.
   - Site English (translation + harmonized) shows both attributions — reader can see them.
   - Why chosen: displayed in Qāmūs too, so the reader can literally see the Qāmūs text standing alone and then inside the Tāj; demonstrates the key reading lesson (a "meaning" = a named reading of one verse); Qur'anic root.

2. **صلو Slw — debate on ṣalāt.** Bracketed Qāmūs senses: (الدُّعاءُ) (الرحمة) (الاستغفار) (حسن الثناء من الله عز وجل على رسوله …) (عبادة فيها ركوع وسجود). Commentary: "وهو أصل معانيها، وبه صدر الجوهري الترجمة؛ ومنه قوله تعالى: {وصل عليهم} … ومنه قول الأعشى: وصلى على دنها وارتسم أي دعا لها أن لا تحمض ولا تفسد"; "(و) قال ابن الأعرابي: الصلاة من الله (الرحمة)"; "(و) قيل: الصلاة من الملائكة: (الاستغفار)". Teacher quotation (excerpted) ending "وفي الكل نظر، انتهى". Then Ibn al-Athīr, al-Miṣbāḥ, al-Rāghib, al-Miṣbāḥ on naql, "وقيل: … مشتركة", al-Munāwī quoting al-Rāzī (Muʿtazila vs "our companions").
   - Guide: "citing Q 9:103" (the Tāj gives the words {وصل عليهم} without a reference; identification ours).
   - Attribution point: "وفي الكل نظر" lies inside the teacher's quotation (closed by انتهى). The site's harmonized English says "al-Zabīdī says all these are open to question" — misattribution (reported below). The faithful translation keeps it with the teacher.
   - Why chosen: Qur'anic key term; shows the Tāj itself marking a sense as sharʿī and recording the debate about pre-Islamic attestation — directly relevant to the site's approach, stated without advocacy.

3. **صلح SlH — brief.** "وأغفل المصنف اللغة المشهورة، وهي صلح كنصر يصلح ويصلح … وقد ذكرها الجوهري والفيومي وابن القطاع والسرقسطي في الأفعال وغير واحد"; Bishr b. Abī Khāzim verse "يسومون الصلاح بذات كهف …" for ṣilāḥ = muṣālaḥa; mustadrak: "والاصطلاح: اتفاق طائفة مخصوصة على أمر مخصوص؛ قاله الخفاجي". Also "قال شيخنا: وخالف في ذلك السبكي …" (prophets described by ṣalāḥ), place names (Ṣāliḥān in Isfahan; al-Ṣāliḥiyya near al-Ruhā, in Baghdad, outside Damascus, in Egypt). NB the Tāj's statement that these Ṣāliḥiyyas are named after "al-Malik al-Ṣāliḥ Ṣalāḥ al-Dīn Yūsuf b. Ayyūb" looks historically confused (Saladin's title was al-Malik al-Nāṣir) — the guide avoids repeating it ("places in Isfahan, Iraq, Syria and Egypt" was cut in the final draft anyway).

### Supporting illustration (not a main example)

- **رحم rHm** — "انتهى سياق شيخنا. قلت: وفي نقله عن العباب نظر؛ لأن مصنفه وصل إلى تركيب "بكم" وبقي ما بعده ناقصا؛ لأنه اخترمته المنية" — shows انتهى, شيخنا, قلت together. Context: teacher cited al-ʿUbāb (al-Ṣaghānī) that "ترحمت عليه" is a solecism. Caveat noted in the guide wording: here مصنفه = "its author" (al-Ṣaghānī), hence "al-muṣannif … used on its own". Site English shows this passage ("Al-Zabīdī: I doubt the ascription to al-ʿUbāb …").

### Linked for onOurSite only

- كفر kfr and خلق xlq — entries without Qāmūs brackets (kfr opens "كفر الكُفْرُ، بالضَّمِّ: ضِدُّ الْإِيمَان، ويُفتَحُ …" — Qāmūs words unmarked; 18 "(" all verse lines). Also kfr has "قاله شيخنا. قلت: لا غلط، والصواب ما ذهب إليه الجوهري والأئمة …" (al-Zabīdī correcting his teacher) — an alternative illustration.
- دين dyn — defective entry.

### Considered and rejected

- كفر kfr as a main example: excellent قلت-vs-teacher passage, but no brackets in our copy, so it cannot show the matn/commentary split. Used only in onOurSite.
- اله Alh (freq 2,851): has "قلت: وهو قول كثير من العارفين. (واختلف فيه على عشرين قولا …" — theological; long and would need much context. Rejected.
- دين dyn: key Qur'anic root but defective on our site.
- امن Amn: "قلت: وقد يطلق الإيمان على الإقرار باللسان فقط" — theological/definitional; not needed given صلو.
- نظر, قبل, خلق: unbracketed or too long.

---

## 4. Other sources looked at

- English Wikipedia "Murtada al-Zabidi", "Taj al-'Arus min Jawahir al-Qamus" — leads only (birth Bilgram 1732; "1205 AH/1790 CE"; begun 1760, finished 8 Sept 1774 citing Reichmuth). Not cited.
- Reichmuth, *The World of Murtaḍā al-Zabīdī (1732–91)* (Gibb Memorial Trust, 2009) — archive.org copy is access-restricted; Google Books has no preview. NOT read; not cited. Its title gives 1791.
- Kuwait edition OCR (archive.org ZUB1965AR) — read vol. 1 editor's introduction (OCR is noisy; page numbers not recoverable, so cited by section).
- Khayriyya edition 1306 AH (archive.org ZUB1888ARAR, vol. 10 OCR) — tried to find the colophon; OCR unusable. Not cited.
- OAPEN "Global Arabic Literary Cultures" (Brill) — blocked by a bot-check; not read.
- Encyclopaedia of Islam / EI3 "al-Zabīdī" — not accessible; not cited.
- Baalbaki, *The Arabic Lexicographical Tradition* (2014) — not accessible; not cited (the 2019 article was used instead).

---

## 5. Site data issues (for the return value)

1. **Stored date 1790 should be 1791.** Died Shaʿbān 1205 AH (al-Jabartī vol. 2 p. 112) = April–May 1791; Lane p. xviii "died A.D. 1791 (in the year of the Flight 1205)". 1790 (hawramani, Baalbaki 2019, Wikipedia) is the CE year in which 1205 AH began. Panel ordering is unaffected.
2. **Full title**: dictionary slug and hawramani heading say "fī Jawāhir al-Qāmūs"; al-Zabīdī named it "Tāj al-ʿArūs min Jawāhir al-Qāmūs" (intro vol. 1 p. 11). The short label "Tāj al-ʿArūs" is fine.
3. **دين (dyn) entry defective** (entry_id 1388): stored text = first definition (debt) + intrusive passage from دهقن; the Tāj's treatment of dīn as religion/judgement is missing. Upstream (hawramani) defect. Consider hiding or adding a visible note.
4. **Harmonized English for صلو (Slw) misattributes** "وفي الكل نظر" to al-Zabīdī ("al-Zabīdī says all these are open to question"); in the Arabic it is the end of al-Fāsī's quotation (closed by انتهى).
5. **About a third of entries (526/1,600 by heuristic) lack the Qāmūs bracket marking** in the stored text (inherited from the digital source) — English renderings of those entries cannot separate al-Fīrūzābādī's words from al-Zabīdī's.
6. 19 entries contain "(سقط: …)" lacuna markers (list in §1).
7. (For the Qāmūs guide) stored Qāmūs فسد has a typo "عقضد" for عقد.
8. hawramani's blurb places Bilgram "in West Bengal" — wrong (Farrāj quotes it as near Qannauj beyond the Ganges; Bilgram is in Hardoi district, Uttar Pradesh per Wikipedia). Not displayed on al-nuqta; FYI only.

## 6. Open questions / evidence gaps

- Exact date of starting the Tāj (1174/1760 per Wikipedia→Reichmuth) not verified from a source I read; guide avoids it.
- Whether the Shāmila digital text reproduces the printed Kuwait volumes faithfully (lacunae, vowelling) — not checked against printed pages.
- Whether hawramani's text derives from Shāmila or from a common digital ancestor — unknown.
- Reichmuth (2009) and EI articles unread; Lane's figures (¾–9⁄10 from the Lisān) come from his own collation and have not been re-tested beyond the single فسد entry.
- Identity and date of Muslim al-Baṭīn not researched (named only).
- Kuwait intro page numbers unrecoverable from OCR (cited by section heading).

---

## 7. Revision round 1 (2026-09-26): additional evidence

- **Lane, Preface p. xix (verifier C39).** The Google scan `anarabicenglish03lanegoog` lacks p. xix: its OCR runs from "xviii PREFACE." straight to "XX". A complete 1863 Williams and Norgate scan is `https://archive.org/details/arabicenglishlex0001edwa`. On leaf n24, which I viewed as an image, the page is headed "PREFACE. xix" and reads: "As the Táj el-'Aroos is the medium through which I have drawn most of the contents of my lexicon, I must more fully state the grounds upon which I determined to make so great a use of it." In the same scan's OCR, "fourteen years and some days" falls on p. xviii (line 1068, before the xix header at line 1084), and "While mainly composing from the Táj el-'Aroos" falls on p. xxii (line 1301, after the "xxii PREFACE." header at line 1271).
- **Kuwait editor on the supplement.** In the section «طريقة تاج العروس», the editor writes: «وبعد انتهاء المادة التى ألفها الفيروزبادى وشرحها هو يستدرك ما نقص، جامعا ذلك من أشتات كتب اللغة وغيرها من الفنون». He does not name the phrases قلت or ومما يستدرك عليه.
- **SlH (entry 690).** The supplement is introduced by «ومما يستدرك عليه» after the Qāmūs's last bracketed item «(وصليحا، كزبير)», and it runs to the end of the entry. Near its end: «والاصطلاح: اتفاق طائفة مخصوصة على أمر مخصوص؛ قاله الخفاجي». Early in the entry, inside a quotation from al-Fāsī, it says «ونقله الشهاب في مواضع من (شرح الشفاء)».
- **al-Khafājī = al-Shihāb (inference).** The introduction lists his works: p. 9 «وشرح الشفاء، للشهاب الخفاجي. وشفاء الغليل، له أيضا», and p. 4 «وللشهاب الخفاجي في العناية». In 60 displayed Tāj entries, the bare «الخفاجي» is routinely tied to his works: العناية, شرح الشفاء, شفاء الغليل, الريحانة. The SlH line names no work, so the guide says "most likely".
- **Intro vol. 1 p. 10 in full context (verifier C30).** The page praises the work before the modest sentence: «بديع الإتقان، صحيح الأركان … حللت بوضعه ذروة الحفاظ» and «غني ما فيه عن غيره وافتقر غيره إليه». After it, he places responsibility on his sources: «فعهدته على المصنف الأول، وحمده وذمه لأصله الذي عليه المعول، لأني عن كل كتاب نقلت مضمونه، فلم أبدل شيئا».
- **Bishr ibn Abī Khāzim.** Iḥsān al-Naṣṣ, *al-Mawsūʿa al-ʿArabiyya* vol. 5 (Damascus 2002) p. 119, https://arab-ency.com.sy/details/4285: «(… ـ نحو 598م) … من فحول شعراء الجاهلية … عاش في أواخر القرن السادس الميلادي». Corroborated by *Muʿjam al-Shuʿarāʾ al-ʿArab* (Shamela 2114/999): «? – ٢٢ ق. هـ / ? – ٦٠١ م … شاعر جاهلي فحل».
- **Nested *shaykhunā* (rHm).** Inside al-Fāsī's quotation, which is closed by «انتهى سياق شيخنا», the text reads «نقل خلاصتها شيخنا سيدي المهدي الفاسي». Here "our shaykh" is not al-Fāsī. I did not research who this al-Mahdī al-Fāsī is, so the guide makes no claim about his identity. It says only "in al-Zabīdī's own voice".

---

## Addendum (revision r2, 2026-09-26): the borrowed passage in the introduction

- **Tāj intro pp. 9–11 against Lisān intro vol. 1 p. 8.** The Tāj pages are Shamela 7030/9–11. The Lisān page is Shamela 1687/8; its book card reads: Dār Ṣādir, Beirut, 3rd ed. 1414 AH, 15 vols, "ترقيم الكتاب موافق للمطبوع".
  - The stretch begins at «فجاء بحمد الله تعالى هذا الشرح واضح المنهج» (end of p. 9) and runs to «وسميته (تاج العروس…)» (p. 11). It is Ibn Manẓūr's text with small changes:
    - هذا الكتاب becomes هذا الشرح
    - «لم يترك فيها الأزهري وابن سيده» becomes «لم يترك فيها شيخنا»
    - «حفظ أصول هذه اللغة النبوية» becomes «حفظ هذه اللغة الشريفة»
    - after «شافهت… رحلت» al-Zabīdī adds «أو أخطأ فلان أو أصاب، أو غلط القائل في الخطاب»
  - It contains the praise, the "no merit" sentence, «فعهدته على المصنف الأول», the fieldwork disclaimer and the motive («مدار أحكام الكتاب العزيز والسنة النبوية»).
  - None of these may be presented as al-Zabīdī's own words without saying they are borrowed.
- **The Kuwait editor (Farrāj) on this passage,** from the archive.org OCR of vol. 1: «نقل ثمانية وعشرين سطرا من مقدمة ابن منظور في كتابه اللسان، دون أن يشير إلى ذلك، وغيّر بعض الألفاظ القليلة التي فيها أسماء الكتب، وأضاف بضعة ألفاظ». He places it «بعد تعداده للكتب التي رجع إليها، قبل قوله: المقدمة وهي مشتملة على عشرة مقاصد».
- **After the borrowed stretch.** Tāj p. 11 continues past «وسميته» with «وكأني بالعالم المنصف…» and a closing prayer. So the introduction does not *end* with the borrowed passage. I did not check whether that last paragraph has another source.
- **Statements that are al-Zabīdī's own** (outside the editor's range):
  - p. 2–3: the Qāmūs's concision and its commentators; al-Fāsī «عمدتي في هذا الفن».
  - p. 4: the audience and *mamzūj al-ʿibāra*.
  - p. 5: «ونقلت بالمباشرة لا بالوسائط عنها», which introduces the source list.
  - I have not tested whether any of these are themselves borrowed from elsewhere.
- **Bilgram.** The Kuwait editor, «التعريف بالزبيدي», disputes the later sources:
  - «فنحن لا نجد نصا واضحا في كلامه يدل على أنه من الهند، وإن صح أنه ولد هناك فإن بقاءه فيها كان لفترة وجيزة»
  - «وهذا ليس بدليل على ولادته هناك»
  - He quotes al-Zabīdī signing «الواسطي العراقي الأصل… نزيل مصر» (letter dated 1181).
  - He also reports searching the Tāj entries where Bilgram would be expected (بلجرم، بلكرم…) without finding it: «لم يذكرها الزبيدي في تاج العروس في المستدركات».
