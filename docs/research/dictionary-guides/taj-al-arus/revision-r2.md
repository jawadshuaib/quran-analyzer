# Tāj al-ʿArūs guide: revision after verification round 2

**File revised:** `roots/frontend/src/content/dictionary-guides/guides/taj-al-arus.ts`
**Date:** 2026-09-26
**Validator:** `node scripts/validate-dictionary-guides.mjs taj-al-arus` gives **ok**, with no ✗ errors and no ! warnings. It reports 11 root links, 4 excerpts and 1,130 words (it was 1,100 before this revision). `tsc` reports no errors for the file.

## Sources I opened for this revision

I opened all of these myself this round. They are fetched copies, kept only in the session scratchpad.

- **Tāj introduction** (Kuwait edition as paginated in Shamela): https://shamela.ws/book/7030/5, /9, /10 and /11, all HTTP 200.
- **Ibn Manẓūr, *Lisān al-ʿArab*, introduction**, vol. 1 p. 8: https://shamela.ws/book/1687/8 (HTTP 200). I also opened p. 9 at /1687/9.
  - Book card: https://shamela.ws/book/1687, which reads «الناشر: دار صادر - بيروت؛ الطبعة: الثالثة - ١٤١٤ هـ؛ عدد الأجزاء: ١٥؛ [ترقيم الكتاب موافق للمطبوع]».
- **Kuwait edition, vol. 1, editor's introduction by ʿAbd al-Sattār Aḥmad Farrāj.** I used the archive.org OCR file "1 - تاج العروس_djvu.txt" from https://archive.org/details/ZUB1965AR (HTTP 200).

## Flagged claims

### C31 (NQ, and must-fix brief issue B1): the modesty quotation presented as al-Zabīdī's own self-portrait

**Fixed.** The quotation is now introduced as borrowed.

New text: "Even his introduction needs this care. After his list of sources come twenty-eight lines that, the Kuwait editor points out, are taken almost word for word, without acknowledgement, from Ibn Manẓūr's introduction to the *Lisān*.[^kuwait-ed][^lisan-intro|vol. 1, p. 8] In them al-Zabīdī praises the work, disclaims any merit of his own and makes the original authors answerable for whatever in it is right or wrong:"

- **Attribution line.** It now reads: "— al-Zabīdī, introduction to the *Tāj*, adapting Ibn Manẓūr's introduction to the *Lisān* (translation for this guide)".
- **New sentence after the quotation.** "Ibn Manẓūr had written "this book", and credited al-Azharī and Ibn Sīda where al-Zabīdī credits "our shaykh":[^lisan-intro|vol. 1, p. 8] the modest self-portrait is borrowed. In practice he weighs and corrects, even his teacher." This leads into the ر ح م passage, so the section now turns the borrowing into its lesson about checking voices.
- **Later sentence removed.** "The Kuwait editor notes that al-Zabīdī also copied twenty-eight lines…", from the fsd/Lane paragraph, is gone. Its content now sits at the quotation.
- **New source.** `lisan-intro` is added (see New claims).

Evidence:

- **Tāj p. 10** (7030/10): «…فجاءَ بِحَمْد الله تَعَالَى وَفْقَ البُغْيَة، وَفَوق المُنْيَة، بديعَ الإتقان، صحيحَ الْأَركان… حَللْتُ بِوَضْعِهِ ذِرْوَة الحُفّاظ… فكلُّ هَذِه الدَّعاوَى لم يَترك فِيهَا شيخُنا لقائلٍ مقَالا… وَلَيْسَ لي فِي هَذَا الشَّرْح فضيلةٌ أَمُتُّ بهَا، وَلَا وَسِيلَة أَتمسّك بهَا، سوى أنني جمعتُ فِيهِ مَا تفرّق فِي تِلْكَ الكُتب… فعُهدتُه على المصنِّف الأول»
- **Lisān p. 8** (1687/8): «فجَاء بِحَمْد الله وفْق البُغية وَفَوق المُنية، بديع الإتقان، صَحِيح الْأَركان… حللت بِوَضْعِهِ ذرْوَة الْحفاظ… فَكل هَذِه الدَّعَاوَى لم يتْرك فِيهَا الْأَزْهَرِي وَابْن سَيّده لقائلٍ مقَالا… وَلَيْسَ لي فِي هَذَا الْكتاب فَضِيلَة أمتُّ بهَا، وَلَا وَسِيلَة أتمسك بِسَبَبِهَا، سوى أَنِّي جمعت فِيهِ مَا تفرَّق فِي تِلْكَ الْكتب… فعهدته على المصنِّف الأوّل»
- **Kuwait editor** (OCR, section on al-Zabīdī and the Lisān): «بل إنه في مقدمته التي ستراها في التاج نقل ثمانية وعشرين سطرا من مقدمة ابن منظور في كتابه اللسان، دون أن يشير إلى ذلك، وغيّر بعض الألفاظ القليلة التي فيها أسماء الكتب، وأضاف بضعة ألفاظ». He gives the range as «فجاء بحمد الله تعالى هذا الشرح واضح المنهج… إلى وسميته تاج العروس» and places it: «انظر هذا النص بعد تعداده للكتب التي رجع إليها، قبل قوله: المقدمة وهي مشتملة على عشرة مقاصد».
- **Position of the passage.** Tāj p. 9 confirms it: the source list ends «…ويصعب على العادّ إحصاؤها», then comes one sentence on concision, then «فجاءَ بِحَمْد الله تَعَالَى هَذَا الشرحُ واضحَ المَنهج…».
- **What the passage does not include.** The editor's stated range ends at «وسميته» on p. 11. I do not say the introduction *ends* with the passage: p. 11 continues after the title with a further paragraph («وكأني بالعالم المنصف…») and a closing prayer. That is why the guide says "After his list of sources" and not "His introduction ends with".

### C15 (NQ): the motive, "preserving a language on which… the rulings of the Qur'an and the Sunna depend"

**Deleted.** The first paragraph now ends with the audience sentence (p. 4), which is al-Zabīdī's own and was left unchanged.

Evidence that the motive is borrowed:
- Tāj p. 11 has «فإنني لم أقصد سوى حِفظِ هَذِه اللُّغَة الشَّرِيفَة، إِذْ عَلَيْهَا مَدار أَحكامِ الْكتاب الْعَزِيز والسُّنّة النبويّة».
- Lisān p. 8 has «فإنني لم أقصد سوى حفظ أصُول هَذِه اللُّغَة النَّبَوِيَّة وَضبط فَضلهَا، إِذْ عَلَيْهَا مدَار أَحْكَام الْكتاب الْعَزِيز وَالسّنة النَّبَوِيَّة».
- Both fall inside the editor's range.

I deleted the clause rather than qualifying it for two reasons. The borrowing is now explained once, where the quotation stands. And the word budget did not allow a second "in words borrowed from Ibn Manẓūr".

### C58 (NQ): "Al-Zabīdī says he makes no claim to have heard words face to face or travelled for them; his evidence comes from books"

**Rephrased.** New text: "In the borrowed passage, al-Zabīdī disclaims having heard words face to face or travelled for them;[^zabidi-intro|vol. 1, p. 10] introducing his own list of sources, he says he quoted the books directly, "not through intermediaries".[^zabidi-intro|vol. 1, p. 5]"

Evidence:
- **Tāj p. 10:** «لَا أَدّعي فِيهِ دَعْوَى فأَقول: شافَهْتُ، أَو سَمِعت، أَو شَددْتُ، أَو رحَلت».
- **Lisān p. 8:** «لَا أدّعي فِيهِ دَعْوَى فَأَقُول شافهتُ أَو سمعتُ، أَو فعلتُ أَو صنعتُ، أَو شددتُ أَو رحلتُ».
- **Tāj p. 5,** the sentence that introduces the source list («فأَوّل هَذِه المصنفات…» follows): «مستمدًّا ذَلِك من الْكتب الَّتِي يَسّر الله تَعَالَى بفضلِه وُقُوفِي عَلَيْهَا… ونقلْتُ بِالْمُبَاشرَةِ لَا بالوسائط عَنْهَا».
- **Removed:** "his evidence comes from books", replaced by the directly quoted p. 5 statement.

### C17 (NQ): Bilgram

**Qualified.** New text: "Al-Zabīdī was born in 1145 AH (1732–33); later sources say he was born in Bilgram, India, but the Kuwait editor finds nothing clear in al-Zabīdī's own writings that places him in India.[^kuwait-ed|vol. 1, editor's introduction]"

- **Removed:** the parenthesis "(his student al-Jabartī does not name the town)". It is true, but the sentence did not need it once the editor's doubt was stated.
- **Birth year:** unchanged. It is in the Kuwait editor («ولد سنة خمس وأربعين ومائة وألف») and in Jabartī p. 104, which is cited in the next sentence.

Evidence (Kuwait editor, «التعريف بالزبيدي», OCR):
- The later sources: «أما كتاب أبجد العلوم وكتاب نشر العرف وكتاب فهرس الفهارس وطابعو تاج العروس الطبعة الثانية فقد ذكروا أنه ولد ببلد هندي هو بلجرام».
- The editor's doubt: «فنحن لا نجد نصا واضحا في كلامه يدل على أنه من الهند، وإن صح أنه ولد هناك فإن بقاءه فيها كان لفترة وجيزة».
- His verdict on the Bilgram evidence: «وهذا ليس بدليل على ولادته هناك».
- Al-Zabīdī's own signature, which the editor quotes: «…الحسيني الواسطي العراقي الأصل الزبيدي نزيل مصر».

## Brief issues

- **B1 (must-fix).** Fixed as described under C31.
- **B2 (Lane's first person).** Adopted: "[[guide:lane-lexicon|Lane]], who called the *Tāj* "the medium through which I have drawn most of the contents of my lexicon", found its quotations faithfully transcribed, but also found…". The quotation and page are unchanged.
- **B3 (word budget).** Trimmed as follows. The result is 1,130 words: slightly above the 1,100 ceiling of the target range and well below the validator's 1,200 warning.
  - **The later "twenty-eight lines" sentence:** cut. Its content moved to the quotation.
  - **The banquet and colophon sentence:** merged to one clause. It now reads: "The Kuwait editor, from dates recorded in the text, puts the *Tāj*'s completion in Rajab 1188 AH (1774)." That completion date was verified in round 2 as C23; the editor's text reads «وآخر الكتاب في رجب سنة 1188». Al-Jabartī's banquet date (1181 AH) and the editor's view that the banquet marked the first part are removed.
  - **The Cairo-libraries sentence:** tightened to "from lexicons such as Ibn Manẓūr's *Lisān al-ʿArab* to works on history and medicine". Its content is unchanged.
- **B4.** "The rest of the entry adds…" became "The entry also gives…".
- **B5.** "attested in a verse by Bishr ibn Abī Khāzim" became "attested in a verse the entry attributes to Bishr ibn Abī Khāzim". The attribution is the Tāj's own (entry 690: «قال بشر بن أبي خازم»). The date comes from the encyclopedia and is unchanged.
- **Consistency.** *Lisān* is now italicised in the Lane paragraph.

## Removed claims

1. The motive clause: "gives his motive as preserving a language on which, he says, the rulings of the Qur'an and the Sunna depend" [p. 11] (C15).
2. "his student al-Jabartī does not name the town" (from C17).
3. The framing of the quotation as al-Zabīdī's own self-presentation: "Amid high praise for the work, he plays down his own share…" (C31).
4. "his evidence comes from books", replaced by the quoted p. 5 statement (C58).
5. "Al-Jabartī dates a banquet for the *Tāj*'s completion to 1181 AH (1767–68)", with the Jabartī vol. 2 p. 105 citation, and "the banquet marking the first part" (B3 trim; both were supported, cut only for length).
6. The stand-alone later sentence "The Kuwait editor notes that al-Zabīdī also copied twenty-eight lines of Ibn Manẓūr's introduction without acknowledgement". It is not really removed: the claim now stands at the quotation.

## New claims

1. **Where the borrowed passage sits.** "After his list of sources come twenty-eight lines… taken almost word for word, without acknowledgement, from Ibn Manẓūr's introduction to the *Lisān*."
   - The number, the lack of acknowledgement and the "few words changed" are the Kuwait editor's: «نقل ثمانية وعشرين سطرا… دون أن يشير إلى ذلك، وغيّر بعض الألفاظ القليلة… وأضاف بضعة ألفاظ».
   - The position is the editor's too: «بعد تعداده للكتب التي رجع إليها».
   - "Almost word for word" matches my own comparison of Tāj pp. 9–11 with Lisān p. 8, quoted above.
2. **The quoted sentence lies inside that passage.** Tāj p. 10 against Lisān p. 8, quoted above.
3. **Ibn Manẓūr's wording.** Ibn Manẓūr wrote "this book" (هذا الكتاب) where al-Zabīdī has "this commentary" (هذا الشرح). He credited al-Azharī and Ibn Sīda («لم يترك فيها الأزهري وابن سيده لقائل مقالا») where al-Zabīdī credits «شيخنا» («لم يترك فيها شيخنا لقائل مقالا»).
   - Sources: Lisān p. 8 and Tāj p. 10.
4. **The fieldwork disclaimer lies inside the borrowed passage.** Tāj p. 10 against Lisān p. 8 (see C58).
5. **"Not through intermediaries."** "Introducing his own list of sources, he says he quoted the books directly, 'not through intermediaries'." Tāj p. 5 (see C58); the translation was made for this guide.
6. **The Kuwait editor's doubt about Bilgram.** He "finds nothing clear in al-Zabīdī's own writings that places him in India." Source: the Kuwait editor, «فنحن لا نجد نصا واضحا في كلامه يدل على أنه من الهند».
7. **New source `lisan-intro`.** Ibn Manẓūr, *Lisān al-ʿArab*, author's introduction, vol. 1, p. 8 (Beirut: Dār Ṣādir, 3rd ed., 1414 AH; as paginated in al-Maktaba al-Shāmila, book 1687). URL: https://shamela.ws/book/1687/8 (HTTP 200).
   - The publisher, edition, volume count and "pagination matches print" note all come from the book card at https://shamela.ws/book/1687.

## Disputed

None. I accepted all four flags and every brief issue.

## Not changed

- **Summary, lede, onOurSite, the other sources and all four excerpts:** unchanged.
- **lastVerified:** not set. The final verification round sets it.
