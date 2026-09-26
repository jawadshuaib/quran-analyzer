# Maqāyīs al-Lugha (Ibn Fāris) — research notes

Guide: `roots/frontend/src/content/dictionary-guides/guides/maqayis-al-lugha.ts`
Site dictionary slug: `ibn-faris-maqayis-al-lugha` (site label: "Maqāyīs al-Lugha" | مقاييس اللغة | "Ibn Fāris" | stored date 1004 | ar | 1,323 displayed roots)
Written 2026-09-26. Validator: passes, 0 errors, 0 warnings; 1,100 words (lede + body, excluding excerpts).

---

## 1. Sources actually consulted

| id | source | how consulted | URL |
|---|---|---|---|
| harun-ed | Ibn Fāris, *Muʿjam Maqāyīs al-Lugha*, ed. ʿAbd al-Salām Muḥammad Hārūn, 2nd ed., 6 vols, Muṣṭafā al-Bābī al-Ḥalabī (Egypt), 1389–1392 AH / 1969–1972 CE (Shamela book card; "ترقيم الكتاب موافق للمطبوع" = pagination matches print; reprinted Dār al-Jīl / Dār al-Fikr, Beirut) | read pages on Shamela (downloaded HTML, extracted text) | https://shamela.ws/book/21710 (book card); pages cited below by Shamela page id |
| baalbaki | Ramzi Baalbaki, *The Arabic Lexicographical Tradition* (Brill, 2014), §3.3 on *al-Maqāyīs* and *al-Muǧmal*, pp. 348–356 | Google Books preview, full-page view of pp. 348, 349, 350, 351, 354, 355, 356 (pp. 352–353 NOT shown in preview); snippet view for pp. 52, 398 | https://books.google.ca/books?id=cme7AwAAQBAJ&pg=PA349 |
| sahibi | Ibn Fāris, *al-Ṣāḥibī fī Fiqh al-Lugha al-ʿArabiyya…*, Muḥammad ʿAlī Bayḍūn, 1st ed. 1418/1997 (Shamela card), pp. 44–45 "باب الأسباب الإسلامية" | Shamela pages 50–51 | https://shamela.ws/book/9977/51 (p. 45); https://shamela.ws/book/9977/50 (p. 44) |
| hawramani | The Arabic Lexicon, "Ibn Fāris, Maqāyīs al-Lugha" landing page + root pages كفر, أمن | fetched HTML | https://arabiclexicon.hawramani.com/ibn-faris-maqayis-al-lugha/ ; https://arabiclexicon.hawramani.com/كفر/ |
| (not cited) | Anas A. Elgmati et al., "The dictionary Maqāyīs al-Luġah… a book review", *Al-Qanatir* 32/1 (2023) | read PDF | http://al-qanatir.com/aq/article/download/604/474/3086 — weak secondary; used only as a lead (mentions other editions: Shams al-Dīn 1999; al-Dāya 2020). Not cited. |
| (not cited) | Encyclopaedia Iranica | searched; no dedicated "Ebn Fāres" article found (search results only mention him in the Hamadānī article: "Ebn Fāres (d. 395/1004)"). | https://www.iranicaonline.org/?s=Ebn+F%C4%81res |

Not consulted (could not access): EI2/EI3 "Ibn Fāris"; Haywood, *Arabic Lexicography* (1960); Jabal (2003) and the Arabic monographs Baalbaki cites (Ṣāliḥ 1970, Ḥamzāwī 1991/1998).

---

## 2. Claim-by-claim support (reader-facing text)

### Header fields
- **title / titleAr** مقاييس اللغة — Ibn Fāris's own preface opens "هذا كتاب المقاييس فى اللغة" (harun-ed vol. 1 p. 3, Shamela /47); Yāqūt calls it «كتاب مقاييس اللغة» (quoted by Hārūn, editor's intro p. 39, Shamela /37). Printed edition title adds *Muʿjam* (Baalbaki p. 52 snippet notes the two titles *Maqāyīs al-luġa* and *Muʿǧam Maqāyīs al-luġa*).
- **titleGloss "The Measures of Language"** — maqāyīs = pl. of miqyās; Baalbaki p. 351: "The term maqāyīs (cf. the book's title) is also used to refer to the norms that govern a certain type of words". My rendering; "Standards" would also be defensible.
- **authorFull** Abū l-Ḥusayn Aḥmad ibn Fāris ibn Zakariyyāʾ — Shamela card "أبو الحسين أحمد بن فارس بن زكريا (ت ٣٩٥ هـ)"; Hārūn intro p. 3 (Shamela /1) "أبى الحسين أحمد بن فارس بن زكريا بن حبيب الرازى", and fn 1 notes Ibn Fāris names his father "فارس بن زكريا" in the Maqāyīs preface.
- **period** d. 395 AH / 1004–5 CE (other dates reported) — Hārūn intro pp. 9–10 (Shamela /7–/8): "ولكنهم يختلفون فى تاريخ وفاته على أقوال خمسة" — 360, 369, 375, 390, 395; "وأصح الأقوال وأولاها بالصواب أن وفاته كانت سنة (٣٩٥)". Yāqūt's note (Hārūn p. 4, Shamela /2): died Ṣafar 395 in Rayy. Conversion: 1 Muḥarram 395 ≈ 18 Oct 1004 (Julian, tabular); Ṣafar 395 ≈ Nov–Dec 1004; year ends ≈ Oct 1005. Hence "1004–5".

### Lede
- "A typical entry opens with a verdict… one aṣl, or two, or three" — Baalbaki p. 349: "He begins by determining whether the root has no aṣl (see below), one aṣl, or more. He then justifies the lack of an aṣl or specifies the basic meaning of each proposed one. Each aṣl is then exemplified by one or more lexical items, often supported by attested usage (šawāhid), particularly in poetry…". Site data: 1,308 of 1,323 stored entries open by naming the letters (regex over stored text).
- "tenth-century philologist" — died 395/1004–5; career in Hamadhān/Rayy in the 4th/10th c. (Hārūn pp. 5–10).
- "persuasive in places, strained in others" — my characterisation; grounded in the Hārūn vs Baalbaki disagreement cited in the body (see §2 "Judgements").

### "A thesis in the preface"
- "worked mostly in Hamadhān and later at the Buyid court in Rayy, where he died" — Hārūn intro p. 5 (Shamela /3): "ولكن المقام استقر به فى معظم الأمر بمدينة همذان"; p. 6 (/4): "استدعى منها إلى بلاط آل بويه بمدينة الري، ليقرأ عليه أبو طالب بن فخر الدولة"; p. 9 (/7): "لم يختلف المؤرخون في أن ابن فارس قد قضى نحبه في مدينة الرى".
- "lists five dates before settling on 395" — see header.
- Preface quotation (vol. 1 p. 3, Shamela /47), verbatim: «إِنَّ لِلُغةِ العرب مقاييسَ صحيحةً، وأصولاً تتفرّع منها فروع. وقد ألَّف النَّاسُ فى جوامع اللغة ما ألَّفوا، ولم يُعربوا فى شئٍ من ذلك عن مقياس من تلك المقاييس، ولا أصل من الأصول.» Guide quotes the first sentence (my translation: "The language of the Arabs has sound measures, and roots from which branches grow.") and paraphrases the second ("Earlier compilers, he complains, never set out a single one of these measures").
- "He has headed each section, he says, with the aṣl from which its details branch, so that a short statement covers the whole family" — same page: «وقد صدَّرْنَا كلَّ فصلٍ بأصله الذى يتفرّع منه مسائلُه، حتّى تكونَ الجملةُ الموجَزةُ شاملةً للتَّفصيل، ويكونَ المجيبُ عما يُسألُ عنه مجيِباً عن الباب المبسوطِ بأوجزِ لفظٍ وأقربِه.»
- Five books (vol. 1 pp. 3–5, Shamela /47–/49): «فأعلاها وأشرفُهَا كتابُ أبى عبد الرحمن الخليل بن أحمد، المسمَّى (كتابَ العين)» … «ومنها كتابا أبى عُبيدٍ فى (غريب الحدِيث)، و (مصنَّف الغريب)» … «ومنها (كتاب المنطق)» [Ibn al-Sikkīt] … «ومنها كتاب أبى بكر بن دريد المسمَّى (الجمهرة)» … «فهذِه الكتبُ الخمسةُ معتمَدُنَا فيما استنبَطناه من مقاييس اللغة، وما بعدَ هذِه الكتبِ فمحمولٌ عليها، وراجعٌ إليها؛ حتى إذا وقع الشئُ النادر نَصَصْناه إلى قائله». Guide: "which he ranks highest and noblest" (paraphrase of فأعلاها وأشرفها); "Everything else rests on these, and a rare item is credited to whoever reported it" (paraphrase). Baalbaki p. 349 confirms: "he primarily depends on five works which include, in addition to K. al-ʿAyn and al-Ǧamhara, three mubawwab ones, namely, Abū ʿUbayd's … Ġarīb al-Ḥadīṯ and Muṣannaf al-ġarīb … and Ibn al-Sikkīt's … al-Manṭiq (i.e. Iṣlāḥ al-manṭiq)"; p. 348: "In the introduction of al-Maqāyīs, Ibn Fāris expresses his great admiration of Ḫalīl's K. al-ʿAyn, and attributes to it the highest status among his sources."
- "The words are inherited; the analysis is his." — my summary of the preface + Baalbaki pp. 349–50.
- "Nor did he aim to be complete… keeps the items that demonstrate an aṣl and cuts down what he takes from al-Khalīl and Ibn Durayd" — Baalbaki pp. 349–350: "Unlike some of his contemporaries, such as Azharī … and al-Ṣāḥib b. ʿAbbād …, Ibn Fāris was not interested in authoring an exhaustive lexicon and satisfied himself with the lexical items that prove the correctness of his uṣūl (or the absence of an aṣl in the first place) and illustrate the existence or absence of naḥt. In fact, quotations from the lemmata of his two main sources, the lexica of Ḫalīl and Ibn Durayd, are normally abbreviated, and lexical items cited therein are often ignored."

### "How an entry works"
- "Almost every entry opens by naming the letters and giving a verdict, typically aṣl ṣaḥīḥ yadullu ʿalā…" — site data: 1,308/1,323 stored entries open with "(root) الـX والـY والـZ"; "أصل صحيح|أصل واحد" occurs in 679 entries, "أصلان" in 170, "ثلاثة أصول" in 12, "كلمة واحدة" in 94 (regex over displayed entries).
- Counts "1,808 of 4,631 roots said to have no aṣl, 2,346 one, 477 more" — Baalbaki p. 350: "Out of 4,631 roots in the lexicon, 1,808 are said not to have an aṣl, whereas out of the remaining 2,823 roots, 2,346 have one aṣl and only 477 more than one." (fn 429: Ǧabal 2003: 47). Attributed in the guide ("By a count Baalbaki reports").
- مجس — stored entry (displayed): «(مَجَسَ) الْمِيمُ وَالْجِيمُ وَالسِّينُ كَلِمَةٌ مَا نَعْرِفُ لَهَا قِيَاسًا، وَأَظُنُّهَا فَارِسِيَّةٌ، وَهِيَ قَوْلُنَا هَؤُلَاءِ الْمَجُوسُ. يُقَالُ: تَمَجَّسَ الرَّجُلُ، إِذَا صَارَ مِنْهُمْ.» Guide translation: "a word for which we know no measure; I think it is Persian". Q 22:17 contains وَالْمَجُوسَ. Baalbaki p. 351 fn 439 confirms the general practice: "words which he identifies as Arabized (muʿarrab) are excluded from the proposed uṣūl" (his example is KNR).

### Close reading: ك ف ر (kfr), entry_id 163
Stored original (verbatim, relevant parts): «(كَفَرَ) الْكَافُ وَالْفَاءُ وَالرَّاءُ أَصْلٌ صَحِيحٌ يَدُلُّ عَلَى مَعْنًى وَاحِدٍ، وَهُوَ السَّتْرُ وَالتَّغْطِيَةُ. يُقَالُ لِمَنْ غَطَّى دِرْعَهُ بِثَوْبٍ: قَدْ كَفَرَ دِرْعَهُ. وَالْمُكَفِّرُ: الرَّجُلُ الْمُتَغَطِّي بِسِلَاحِهِ. فَأَمَّا قَوْلُهُ: حَتَّى إِذَا أَلْقَتْ يَدًا فِي كَافِرٍ ... فَيُقَالُ: إِنَّ الْكَافِرَ: مَغِيبُ الشَّمْسِ. وَيُقَالُ: بَلِ الْكَافِرُ: الْبَحْرُ. وَكَذَلِكَ فُسِّرَ قَوْلُ الْآخَرِ: … أَلْقَتْ ذُكَاءُ يَمِينَهَا فِي كَافِرِ … وَيُقَالُ لِلزَّارِعِ كَافِرٌ، لِأَنَّهُ يُغَطِّي الْحَبَّ بِتُرَابِ الْأَرْضِ. قَالَ اللَّهُ تَعَالَى: {أَعْجَبَ الْكُفَّارَ نَبَاتُهُ} [الحديد: 20] . وَرَمَادٌ مَكْفُورٌ: سَفَتِ الرِّيحُ التُّرَابَ عَلَيْهِ حَتَّى غَطَّتْهُ … وَالْكُفْرُ: ضِدُّ الْإِيمَانِ، سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ. وَكَذَلِكَ كُفْرَانُ النِّعْمَةِ: جُحُودُهَا وَسَتْرُهَا … فَأَمَّا الْكَفِرَاتُ وَالْكَفَرُ فَالثَّنَايَا مِنَ الْجِبَالِ، وَلَعَلَّهَا سُمِّيَتْ كَفِرَاتٍ، لِأَنَّهَا مُتَطَامِنَةٌ، كَأَنَّ الْجِبَالَ الشَّوَامِخَ قَدْ سَتَرَتْهَا.»
- Same wording in Hārūn vol. 5 pp. 191–192 (Shamela /2243–/2244); his fn identify the first verse as Labīd's (Muʿallaqa) and the second as Thaʿlaba b. Ṣuʿayr al-Māzinī; fn 4 records his emendation of the manuscript's «فيذكر أهلا» to «فتذكرا ثقلا» — our stored text has the emended reading; «فهم أهل الكفور» is his correction of «فهو» — stored text agrees.
- Guide claims: concrete uses first (order checked); two glosses for kāfir "sunset or the sea" reported with يقال … ويقال بل, no choice made; Q 57:20 is the entry's only Qur'an citation and is used for الزارع (sower); kufr's link to covering is stated in his own voice ("سُمِّيَ لِأَنَّهُ") with no attribution; "perhaps" = لعلها for kafirāt.
- My translation in the excerpt: "a sound root pointing to a single meaning: concealing and covering… The sower is called kāfir because he covers the seed with the soil of the earth. God, exalted, said: 'its growth delights the kuffār'… Kufr, the opposite of īmān, is so called because it is a covering of the truth."
- What it shows: single aṣl; concrete senses ordered before the religious one; poetry + Qur'an as evidence; reported alternatives left unresolved; hedging (لعل). Uncertainty: the derivation of kufr "unbelief" from "covering" is his proposal (see al-Ṣāḥibī below), not established fact.
- **al-Ṣāḥibī** (sahibi pp. 44–45, Shamela 9977 /50–/51): «كَانَتْ العربُ فِي جاهليتها عَلَى إرثٍ من إرث آبائهم فِي لُغاتهم … فلما جاءَ الله جلّ ثناؤه بالإسلام حالت أحوالٌ … ونُقِلت من اللغة ألفاظ من مواضعَ إِلَى مواضع أخَر بزيادات زيدت» (p. 44); «وكذلك كَانَتْ لا تعرف من الكُفر إِلاَّ الغِطاء والسِّتْر» and «ومما جاء فِي الشرع الصلاة وأصله فِي لغتهم: الدُّعاء» (p. 45). Guide paraphrases/translates these, labelled "(our translation)".

### Outliers: ق ب ل (qbl), entry_id 536
Stored original: «(قَبَلَ) الْقَافُ وَالْبَاءُ وَاللَّامُ أَصْلٌ وَاحِدٌ صَحِيحٌ تَدُلُّ كَلِمُهُ كُلُّهَا عَلَى مُوَاجَهَةِ الشَّيْءِ لِلشَّيْءِ، وَيَتَفَرَّعُ بَعْدَ ذَلِكَ … فَأَمَّا قَبْلُ الَّذِي هُوَ خِلَافُ بَعْدَ، فَيُمْكِنُ أَنْ يَكُونَ شَاذًّا عَنِ الْأَصْلِ الَّذِي ذَكَرْنَاهُ، وَقَدْ يُتَمَحَّلُ لَهُ بِأَنْ يُقَالَ هُوَ مُقْبِلٌ عَلَى الزَّمَانِ. وَهُوَ عِنْدَنَا إِلَى الشُّذُوذِ أَقْرَبُ.» (end of entry)
- "the form the Qur'an uses most" — site morphology table: lemma قَبْل = 242 of the root's 294 tokens (next: تَقَبَّلَ 10).
- Formula «ومما شذ عن هذا الباب/الأصل» — site data: 186 displayed entries contain شذ/شاذ in a sense other than "لا يشذ" (regex). Examples seen: سمع (السمع: ولد الذئب من الضبع), بعض (البعوضة), غفر, شهد, فتن.
- Other displayed hedged cases (not used): قتل «ومما شذ عن هذا الباب ويمكن أن يقاس عليه بلطف نظر»; خشي «وقد يمكن الجمع بينهما على بعد»; عزل; ضيف «ويمكن أن يتمحل له»; طوق «وقد يمكن أن يتمحل فيقاس على الأول، لكنه يبعد».

### Judgements of the method
- Hārūn, editor's intro p. 23 (Shamela /21): «إذ يردُّ مفرداتِ كلِّ مادة من مواد اللغة إلى أصولها المعنوية المشتركة فلا يكاد يخطئه التوفيق» → "hardly ever failed to find the shared sense".
- Baalbaki p. 351: "It is obvious moreover that Ibn Fāris was mindful of the fact that the identification of semantic relationships often leads to farfetched interpretations. On one occasion he declares that he detests farfetchedness in seeking to demonstrate how a lexical item can be related to a specific aṣl.[fn 437: III, 275] How much he abided by this maxim, however, is certainly open to question given that the uṣūl which he proposes are frequently arbitrary and unconvincing." I read III, 275 on Shamela (/1343, root صف): «ومما شذَّ عن الباب، وقد يمكن أن يُتطَلَّب له فى القياس وجهٌ، غيرَ أنَّا نكره القياسَ المتمَحَّل المستَكْرَه». (صفف is NOT displayed in Maqāyīs on our site, so not linked.)

### Longer words / naḥt
- Vol. 1 pp. 328–329 (Shamela /372–/373), start of «باب ما جاء من كلام العرب على أكثر من ثلاثة أحرف أوله باء»: «اعلم أنّ للرُّباعىّ والخُماسىِّ مذهباً فى القياس، يَستنبِطه النَّظرُ الدَّقيق. وذلك أنّ أكثر ما تراه منه منحوتٌ. ومعنى النَّحت أن تُؤخَذَ كلمتان وتُنْحَتَ منهما كلمةٌ تكون آخذةً منهما جميعاً بحَظٍّ. والأصل فى ذلك ما ذكره الخليل من قولهم حَيْعَل الرَّجُل، إِذا قالَ حَىَّ عَلَى … فنقول: إنَّ ذلك على ضربين: أحدهما المنحوت الذى ذكرناه، والضَّرْب الآخر [الموضوع] وضعاً لا مجالَ له فى طُرق القياس.» p. 329 also: «(البلْعُوم) … مأخوذٌ من بَلِعَ، إلاّ أنّه زِيد عليه ما زِيدَ» (augmented type).
- Three-way classification also in the jīm chapter, vol. 1 p. 505 (Shamela /548) and visible in the stored جثم entry: «فَمِنْهُ مَا نُحِتَ مِنْ كَلِمَتَيْنِ … وَمِنْهُ مَا أَصْلُهُ كَلِمَةٌ وَاحِدَةٌ وَقَدْ أُلْحِقُ بِالرُّبَاعِيِّ وَالْخُمَاسِيِّ بِزِيَادَةٍ تَدْخُلُهُ. وَمِنْهُ مَا يُوضَعُ كَذَا وَضْعًا».
- Baalbaki p. 349: "In roots that have more than three radicals, the main focus is on naḥt, and no attempt is made at assigning uṣūl." p. 354: of 404 manḥūt examples, 267 blends of two or more items, 137 blends of item + affix; example kanfalīla < kafl + n + l + long vowel (not used in guide).
- karbala — stored kfr entry (appended chapter): «(الْكَرْبَلَةُ) : وَهِيَ رَخَاوَةٌ فِي الْقَدَمَيْنِ … وَهَذِهِ مَنْحُوتَةٌ مِنْ كَلِمَتَيْنِ: مِنْ رَبَلٍ وَكَبَلٍ. أَمَّا رَبْلٌ فَاسْتِرْخَاءُ اللَّحْمِ … وَأَمَّا الْكَِبْلُ فَالْقَيْدُ». Hārūn vol. 5 p. 193.
- kibrīt / kundush — stored kfr entry: «وَ (الْكِبْرِيتُ) : لَيْسَ بِعَرَبِيٍّ» ; «وَقَالُوا: (الْكُنْدُشُ) : الْعَقْعَقُ … وَمَا أَدْرِي كَيْفَ يَقْبَلُ الْعُلَمَاءُ هَذَا وَأَشْبَاهَهُ.»

### Two senses: ع ب د (Ebd), entry_id 519, compared with Kitāb al-ʿAyn (entry_id 372)
Maqāyīs stored original (quoted parts): «(عَبَدَ) الْعَيْنُ وَالْبَاءُ وَالدَّالُ أَصْلَانِ صَحِيحَانِ، كَأَنَّهُمَا مُتَضَادَّانِ، وَ [الْأَوَّلُ] مِنْ ذَيْنِكَ الْأَصْلَيْنِ يَدُلُّ عَلَى لِينٍ وَذُلٍّ، وَالْآخَرُ عَلَى شِدَّةٍ وَغِلَظٍ. … قَالَ الْخَلِيلُ: إِلَّا أَنَّ الْعَامَّةَ اجْتَمَعُوا عَلَى تَفْرِقَةِ مَا بَيْنَ عِبَادِ اللَّهِ وَالْعَبِيدِ الْمَمْلُوكِينَ … وَمِنَ الْبَابِ الْبَعِيرُ الْمُعَبَّدُ، أَيِ الْمَهْنُوءُ بِالْقَطْرَانِ. وَهَذَا أَيْضًا يَدُلُّ عَلَى مَا قُلْنَاهُ لِأَنَّ ذَلِكَ يُذِلُّهُ وَيَخْفِضُ مِنْهُ … وَمِنَ الْبَابِ: الطَّرِيقُ الْمُعَبَّدُ … وَالْأَصْلُ الْآخَرُ الْعَبَدَةُ، وَهِيَ الْقُوَّةُ وَالصَّلَابَةُ; يُقَالُ هَذَا ثَوْبٌ لَهُ عَبْدَةٌ، إِذَا كَانَ صَفِيقًا قَوِيًّا … وَمِنْ هَذَا الْقِيَاسِ الْعَبَدُ، مِثْلُ الْأَنَفِ وَالْحَمِيَّةِ … وَفُسِّرَ قَوْلُهُ - تَعَالَى -: {قُلْ إِنْ كَانَ لِلرَّحْمَنِ وَلَدٌ فَأَنَا أَوَّلُ الْعَابِدِينَ} [الزخرف: 81] ، أَيْ أَوَّلُ مَنْ غَضِبَ عَنْ هَذَا وَأَنِفَ مِنْ قَوْلِهِ.»
- «قال الخليل» occurs exactly twice (the ʿibād/ʿabīd distinction; al-ʿibiddāʾ). The ʿibāda remark follows «قال:» continuing the quotation — guide cites only the ʿibād/ʿabīd case for "al-Khalīl said".
- "[الأول]" = editor's supplement: Hārūn vol. 4 p. 205 (Shamela /1746) prints «و [الأول] من ذينك (٢) الأصلين» with fn «فى الأصل: ذلك». Editor's method (intro p. 46, Shamela /44): «أو أتمها بدون تنبيه إلا بوضعها بين معكفى الزيادة إن لم أجد لها سندا إلا ضرورة الكلام».
- Hārūn's text for عبد (vol. 4 pp. 205–207, Shamela /1746–/1748) matches the stored text incl. emendations «صفيقا قويا» (MS «ضعيفا قويا»), «المهنوء» (MS «المهناء»), «ويعبد الجاهل» (MS «ونعبد»). Hārūn fn traces «وأعبد أن تهجى كليب بدارم» to al-Farazdaq via Iṣlāḥ al-Manṭiq 58–59 (i.e. one of Ibn Fāris's five sources) — not used in guide.
- Kitāb al-ʿAyn stored entry (displayed) contains: «إنّ العامّة اجتمعوا على تفرقة ما بين عباد الله، والعبيد المملوكين»; «وأمّا عبَد يعبُد عِبادة فلا يقال إلا لمن يعبد الله»; «وبعيرٌ مُعَبَّدٌ: مهنوء بالقَطِران … وأُفْرِدْتُ إفرادَ البعيرِ المعبّد»; «والمعبّد: كلّ طريق يكثر فيه المختلفة، المسلوك»; «والعَبَدُ: الأنفة والحميّة … ومنه: فَأَنَا أَوَّلُ الْعابِدِينَ أي: الأنفين من هذا القول … ويقال: فَأَنَا أَوَّلُ الْعابِدِينَ أي: كما أنه ليس للرحمن ولد فلست بأوّل من عَبَدَ الله مِنْ أهلِ مكّة»; «عَبِدْتُ فَصَمَتُّ»; the verse «ويَعْبَدُ الجاهل الجافي بحقّهم». No statement of a shared/underlying sense. It does NOT contain «ثوب له عبدة» (thick cloth).
- Guide claims checked: Maqāyīs gives one reading of Q 43:81 (passive وفُسِّر); the ʿAyn text on al-nuqta gives that reading plus a second where ʿābidīn = worshippers. Caveat: our ʿAyn text is a modern edition, not necessarily the copy Ibn Fāris read (he says he read it with ʿAlī b. Ibrāhīm al-Qaṭṭān — preface vol. 1 p. 3). The guide says "The ʿAyn text on al-nuqta", not "al-Khalīl's original".

### ف ق ه (fqh), entry_id 4838
Stored: «الْفَاءُ وَالْقَافُ وَالْهَاءُ أَصْلٌ وَاحِدٌ صَحِيحٌ، يَدُلُّ عَلَى إِدْرَاكِ الشَّيْءِ وَالْعِلْمِ بِهِ … وَكُلُّ عِلْمٍ بِشَيْءٍ فَهُوَ فِقْهٌ … ثُمَّ اخْتُصَّ بِذَلِكَ عِلْمُ الشَّرِيعَةِ، فَقِيلَ لِكُلِّ عَالِمٍ بِالْحَلَالِ وَالْحَرَامِ: فَقِيهٌ.» Guide: "every knowledge of a thing", and only "then" (ثُمَّ) reserved for knowledge of the religious law.

### Dates / provenance
- Pre-Islamic poets in displayed entries: Ṭarafa (عبد: «قال طرفة: … إفراد البعير المعبد»); al-Nābigha (أمن: «قال النابغة: وكنت أمينه…»). Philologists of 8th–10th c.: al-Khalīl (d. c. 170s/780s–790s), Abū ʿUbayd (d. 224/838), Ibn al-Sikkīt (d. 244/858), Ibn Durayd (d. 321/933) — death dates as given by Baalbaki p. 349 / Hārūn p. 23 fn (Ibn Durayd b. 223 d. 321).

### Reception
- Hārūn intro p. 39 (Shamela /37): «ولم أجدْ أحداً غير ياقوت يذكر هذا الكتاب لابن فارس»; p. 40 (/38): «وهذا الكتاب لم يسترع انتباه العُلماء إلا منذ عهد قريب … فإنى لم أجِد أمامى منه إلا نُسخة واحِدة مودعة بِدار الكتب المصرية» (photographs of a MS in Persia); p. 41 (/39): the copy «يشيع فيها التحريف والاضطراب … الفجوات والأسقاط».
- Baalbaki p. 356: "Ibn Manẓūr …, whose Lisān al-ʿArab incorporates five major earlier lexica, does not mention a single view of Ibn Fāris's on the uṣūl of a root or the naḥt of a lexical item. … a notable exception is Ṣaġānī (d. 650/1252), who quotes Ibn Fāris very frequently in his al-ʿUbāb al-zāḫir and often cites, at the end of the relevant lemmata, the basic meanings that he assigns to the roots but stops short of following his method … Some of Ṣaġānī's quotations of Ibn Fāris were in turn quoted by Zabīdī (d. 1205/1790) in Tāǧ al-ʿarūs." Also p. 355: al-Mujmal "understandably gained more currency than al-Maqāyīs"; p. 356: 20th-c. al-ʿAlāyilī and the Cairo Academy's al-Muʿjam al-kabīr quote Maqāyīs uṣūl (not used).
- Dating relative to al-Mujmal (NOT in guide, word budget): Hārūn p. 41: «وأستَطيع أن أذهب أيضاً إلى أنه ألَّف «المقاييس» بعدَ تأليفه «المجمل»»; Baalbaki p. 354: "it was probably authored after it, although this cannot be ascertained in the absence of solid textual evidence."

### onOurSite claims
- Text = Hārūn's edition: verified wording identity for عبد (vol. 4 pp. 205–207) and كفر (vol. 5 pp. 191–192), including Hārūn's emendations and bracketed supplement [الأول]. hawramani's Maqāyīs landing page names the five sources but no edition.
- Footnotes absent: Hārūn's fn (poet identifications, MS readings) not in stored text. "identify many of the poets Ibn Fāris quotes without naming" — Hārūn intro p. 45 (Shamela /43): «وعُنيت أيضا بنسبة الأشعار والأرجاز المهملة إلى قائليها»; Baalbaki p. 349: verses "mostly not ascribed to their renderers".
- Full vowelling, verse refs like [الحديد: 20], and heading (كَفَرَ): absent from Shamela's Hārūn text, which has partial vowelling, Qur'an in ﴿﴾ without reference, headings like [كفر] / [عبد].
- 1,323 roots; all 28 initial letters represented (counts per letter: ا 52 … ظ 5, ي 7); length 7 words (قثأ) to 1,277 words (عقب).
- Appended chapters: stored كفر ends with «من ذلك (الكنفليلة)…» to «والله أعلم بالصواب» = Hārūn vol. 5 p. 193ff «[باب ما جاء من كلام العرب على أكثر من ثلاثة أحرف أوله كاف]» (heading absent in stored text and on hawramani's كفر page). Stored جثم = Hārūn vol. 1 p. 505: جثم is the last jīm triliteral, followed by the jīm longer-words chapter; in stored text the heading «باب ما جاء … أوله جيم» appears after «قال:» inside the جذمور verse, and the text ends at «وَمِمَّا وُضِعَ وَضْعًا وَلَمْ أَعْرِفْ لَهُ اشْتِقَاقًا:». Other stored entries carrying such chapters (not named in guide): صرط, رذل, نمل, سرد.

---

## 3. Candidate roots examined

| root | decision | reason |
|---|---|---|
| كفر kfr | **chosen (close reading)** | single aṣl; concrete→religious ordering; Qur'an cited for a non-religious sense; reported alternatives; لعل hedge; ties to al-Ṣāḥibī theory; also carries the kāf longer-words chapter (naḥt examples, "not Arabic", "I do not know how the scholars accept this"). Displayed in 13 dictionaries. |
| عبد Ebd | **chosen (two uṣūl + comparison)** | explicit "two roots that seem opposite"; his own reasoning (وهذا أيضا يدل على ما قلناه); marked quotations of al-Khalīl; Q 43:81 reported in passive; displayed in Kitāb al-ʿAyn, whose text shows the same material without a stated shared sense and a second reading of 43:81. |
| قبل qbl | **chosen (outlier)** | "all its words" then admits qabl is nearer to an outlier; يُتمحّل; qabl = 242/294 Qur'anic tokens of the root. |
| مجس mjs | pointer only | "no measure; I think it is Persian" — loanword/no-aṣl case; Q 22:17. |
| فقه fqh | pointer only | he flags the later specialisation (ثم اختص بذلك علم الشريعة). |
| جثم jvm | onOurSite only | shows the appended jīm chapter, heading mid-verse, truncated; three-way classification of longer words. |
| أمن Amn | rejected | good (two close uṣūl; poetry; al-Khalīl), but site's harmonized English adds "later usage draws īmān from the second", which the original does not say — risk of confusing readers. |
| صلي Sly | rejected (word budget) | two uṣūl (fire; «جنس من العبادة»), ṣalāt = duʿāʾ with al-Aʿshā, then «والصلاة هي التي جاء بها الشرع من الركوع والسجود»; excellent but overlaps al-Ṣāḥibī point. Harmonized English adds "not perform ritual worship", not in original. |
| قدس qds | rejected (budget) | «وأظنه من الكلام الشرعي الإسلامي» — interesting self-flag; kept as backup. |
| تبع tbE | rejected | «لا يشذ عنه من الباب شيء» + «هذا من طريقة الفتيا» — good but less central. |
| صرط SrT | rejected | «من باب الإبدال، وقد ذكر في السين» — but س ر ط not displayed on our site; entry also contaminated by ṣād longer-words chapter. |
| صفف Sff | not usable | contains his explicit «نكره القياس المتمحل» (vol. 3 p. 275) but NOT displayed in Maqāyīs on al-nuqta. |
| قتل, خشي, عزل, ضيف, طوق | backups | hedged outlier formulas (بلطف نظر, على بعد, يتمحل). |

---

## 4. Site data issues found

1. **Appended chapters presented as part of a root.** In several letters the stored (and hawramani) text runs the closing «باب ما جاء من كلام العرب على أكثر من ثلاثة أحرف» chapter into the last triliteral root printed before it: كفر (kāf; heading dropped), جثم (jīm; heading embedded mid-verse; text truncated at «ومما وضع وضعا ولم أعرف له اشتقاقا:»), and at least صرط, رذل, نمل, سرد. The site's faithful translation for كفر says "[Ibn Fāris then lists augmented/quadriliteral words falling under the k-f section:]" and the harmonized English says "Appendix — augmented and quadriliteral words Ibn Fāris files under k-f"; for جثم the harmonized English says "under the same heading". In Hārūn's edition these are a separate chapter (vol. 5 p. 193; vol. 1 p. 505).
2. **Harmonized English adds interpretation** in some entries: أمن ("later usage draws īmān (faith) from the second" — not in the original); صلي ("not perform ritual worship" — not in the original).
3. **Stored date 1004**: consistent with 395 AH (Ṣafar 395 ≈ Nov–Dec 1004), but the death year is disputed (Hārūn lists 360, 369, 375, 390, 395). No change needed; guide says "other dates reported".
4. The edition is not named by the source site; our comparison shows the text is Hārūn's (without footnotes, with added full vowelling, verse references and parenthesised vowelled headings).

---

## 5. Open questions / evidence gaps

- EI2/EI3 "Ibn Fāris" and Haywood (1960) not consulted; Encyclopaedia Iranica appears to have no dedicated article.
- Baalbaki read only in Google Books preview (pp. 352–353 not visible; they may contain relevant discussion, e.g. on muʿarrab exclusions and qiyās).
- The 4,631 / 1,808 / 2,346 / 477 counts are Jabal (2003) as reported by Baalbaki; not independently checked. What "said not to have an aṣl" covers (e.g. «كلمة واحدة», «ليس بشيء», disparate words) is not fully clear from the visible pages.
- Composition date of the Maqāyīs is unknown; order after al-Mujmal is Hārūn's inference (Baalbaki: probable, unprovable). Not in guide.
- Which digital text the source site used (full vowelling, verse references) is not established; Hārūn 1st (1946–52?) vs 2nd (1969–72) edition not distinguished — compared only against the 2nd edition on Shamela. First-edition dates not verified from a catalogue record (NLI and Iranica fetches blocked).
- Ibn Fāris's intended audience: only the preface's "the one who is asked… can answer" is direct evidence; not elaborated in the guide.
- Hārūn's claim that Ibn Durayd's *Kitāb al-Ishtiqāq* inspired the Maqāyīs (intro pp. 23–24, «وأرى …») is his conjecture; not used.

---

## 6. Additions during revision r1 (2026-09-26)

Details and quotations are in `revision-r1.md`.

- **Arrangement** (Hārūn intro pp. 42–44, Shamela /40–/42):
  - The work is divided into books (كتب), from hamza to yāʾ.
  - Each book has three parts: the doubled two-letter roots (الثنائى المضاعف والمطابق), the triliterals, and "ما جاء على أكثر من ثلاثة أحرف أصلية".
  - In the first two parts, the letter after the first is taken from the one that follows it in the alphabet, running to the end and then wrapping round. The third letter is ordered the same way.
  - Hārūn calls the scheme unique ("طريقة فاذة").
  - Example: the rāʾ book opens at رز (vol. 2 p. 372, /932) and reaches رد only after wrapping round (vol. 2 p. 386, /946).
  - The same logic makes كفر the last kāf triliteral before the kāf longer-words chapter (vol. 5 p. 193).
- **Books without a longer-words chapter:**
  - hamza ends at أيى, "تم كتاب الهمزة ويتلوه كتاب الباء" (vol. 1 p. 169, /213)
  - wāw ends at وهن, "تم كتاب الواو" (vol. 6 p. 150, /2683)
  - The hāʾ book has one (vol. 6 pp. 72–73, /2606–/2607).
  - Hārūn's footnote 3 at /2683 says Ibn Fāris omitted a longer-words chapter, but names it "أوله هاء" and lists hāʾ words. That contradicts the hāʾ chapter's presence, so the note as Shamela gives it looks garbled. Don't rely on it.
- **Hārūn on reception**, intro p. 40 (/38): "وهذا الكتاب لم يسترع انتباه العُلماء إلا منذ عهد قريب". This is the source of the old sentence "drew little attention before modern times", which is now attributed to him.
  - Also p. 41 (/39): he attributes the book's obscurity ("خمول ذكر هذا الكتاب") to its being a late work.
- **"ولم نسمعهم يشتقون منه فعلا"** (Maqāyīs عبد) is also in Hārūn vol. 4 p. 205 (/1746). The ʿAyn entry reads "ولم أسمعهم".
- **Kitāb al-Manṭiq:** Hārūn's preface footnotes (/49) do not identify it. Only Baalbaki p. 349 glosses it as *Iṣlāḥ al-manṭiq*. The guide now avoids the title.
- **Baalbaki could not be re-opened in r1:** Google Books showed a CAPTCHA wall on every route, and the API quota was exhausted. No new Baalbaki claims were added.

---

## 7. Additions during revision r2 (2026-09-26)

Details and quotations are in `revision-r2.md`.

- **Baalbaki could not be reopened.** Google Books served a reCAPTCHA to curl (HTTP 429, google.com/sorry) and to the connected Chrome browser; I did not attempt it. archive.org has no copy. Every guide claim that rested only on pp. 350, 351 (first half) or 355–56 was cut. §2 above still records round 1's transcriptions of those pages, but they are unconfirmed.
- **Baalbaki p. 351 is confirmed independently.** David Larsen, "Meaning and Captivity in Classical Arabic Philology", *Journal of Abbasid Studies* 5 (2018), open access on brill.com. It says: "'frequently arbitrary and unconvincing,' says Ramzi Baalbaki", and n. 21 cites "Baalbaki, *Arabic Lexicographical Tradition*, 351". Larsen also cites Hämeen-Anttila calling Ibn Fāris's etymologies "fantastic". Not used.
- **Reception, from the Tāj on our site.**
  - Six displayed Tāj entries name "ابن فارس في المقاييس" or "المقاييس": Sdq, slT, xDE, $gl, dlk, bhl.
  - Under dlk the Tāj reproduces almost verbatim the closing reflection of the Maqāyīs dlk entry (entry 17840): that dāl and lām, joined by any third letter, point to movement, coming and going.
  - slT shows the Tāj faulting Ibn Fāris "in al-Maqāyīs" for following Ibn Durayd's *Jamhara* on *salīṭ*, citing al-Ṣaghānī's *al-ʿUbāb*. Not used; this is a backup example of the Maqāyīs following one of its five sources.
  - Hārūn's own words (intro p. 39, /37) are "ولم أجدْ أحداً غير ياقوت يذكر هذا الكتاب لابن فارس". The guide now uses them in place of "only one medieval author".
- **The doubled-root gap is confirmed.**
  - Hārūn's rāʾ book opens with "باب الراء وما معها فى الثنائى والمطابق" (vol. 2 p. 372). It includes [رب] at p. 381 (/941) and [رد] at p. 386 (/946).
  - Our database has no Maqāyīs row for rbb or rdd. hawramani /رد/ carries the *radd* entry; /ردد/, /رب/ and /ربب/ have none.
  - The only Maqāyīs row among roots whose second and third letters match is Ayy (أيى), a triliteral-section entry at the end of the hamza book.
- **The third kind of longer word.** The rāʾ chapter heading (vol. 2 p. 509, /1069) says the longer words there are "منحوتٌ أو مزيدٌ فيه". The jīm chapter introduction, stored inside the jvm entry, lists three kinds: carved, one word augmented, and set down.
- **Formula counts** (displayed Maqāyīs, vowel marks ignored): "أصل صحيح يدل" in 200 entries; "أصل (واحد )?صحيح" in 317; "أصل واحد" in 400.
