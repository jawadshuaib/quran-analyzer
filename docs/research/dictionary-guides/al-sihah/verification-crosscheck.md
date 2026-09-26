# al-Ṣiḥāḥ: verification of the cross-check revision (round 99)

Independent check of the three changes listed for this revision. I did not read research-notes.md or revision-*.md. Sources were opened directly (Shāmila pages fetched and read as Arabic text; printed page numbers read from each page's page field).

## 1. Body, "After al-Jawharī": two-thirds vs. half

Claim A: al-Suyūṭī's text of the Qāmūs preface reads "two-thirds of the language or more".
- Opened al-Muzhir, Shāmila 6936/71 (printed p. 77) and 6936/72 (printed p. 78). Page 77 ends «ولما رأيت إقبال الناس على صحاح الجوهري وهو جدير بذلك غيرَ أنه فاته»; page 78 begins «ثلثا اللغة أو أكثر إما بإهمال المادة أو بترك المعاني الغريبة النادّة». Page 78 continues with «لتداوله واشتهاره بخصوصه واعتماد المدرسين على نقوله ونصوصه», which supports the rest of the sentence ("widely used, teachers relied on it"). **Supported.** The locator [^muzhir|vol. 1, pp. 77–78] is correct.

Claim B: the printed Qāmūs reads "half".
- Opened Shāmila 7283/3. The page field reads 27. The book card (Shāmila 7283) gives: ed. Maktab Taḥqīq al-Turāth fī Muʾassasat al-Risāla, supervised by Muḥammad Naʿīm al-ʿArqsūsī; Muʾassasat al-Risāla, Beirut; 8th ed., 1426/2005; «ترقيم الكتاب موافق للمطبوع». Text: «غَيْرَ أَنَّهُ فَاتَهُ نِصْفُ اللُّغَةِ أَوْ أَكْثَرُ، إِمَّا بِإِهْمَالِ الْمَادَّةِ، أَوْ بِتَرْكِ الْمَعَانِي الْغَرِيبَةِ النَّادَّةِ». The source entry `qamus-preface` (citation, page and URL) is accurate, and the URL returns 200.
- Qualification: the reading is not uniform across copies. Al-Zabīdī, *Tāj al-ʿArūs* (Shāmila 7030/76, page field 76), commenting on this sentence of the preface, says «نصف اللغة» is found "in a Meccan copy" and that "in the Nāṣiriyya copy, as is said", it reads «ثلثا اللغة». So "the printed *Qāmūs* reads 'half'" generalises from one edition to a text whose manuscripts vary. **Needs qualification. Fixed:** the wording is now "a modern edition of the *Qāmūs* reads "half"", which matches exactly what the citation shows. I did not add al-Zabīdī's note to the page, because that would be new material. It remains available if a later revision wants to explain the variant.
- Framing check: "(so al-Suyūṭī quotes his preface; …)" does not accuse al-Suyūṭī of misquoting. Given al-Zabīdī's note, that restraint is appropriate.

## 2. Lede: "The title promises soundness, as one scholar judged it, not completeness."

The sentence is the guide's own interpretation and is presented without attribution to anyone, which is appropriate. It rests on:
- The preface, «أودعت هذا الكتاب ما صح عندي من هذه اللغة». Re-opened on Shāmila 23235/50, page field 33. Supported.
- Al-Suyūṭī, Muzhir 1:74 (Shāmila 6936/68): «وأول من التزم الصحيح مقتصرا عليه … الجوهري ولهذا سمى كتابه بالصحاح». Supported. The body cites it as pp. 74–75.
- "Not completeness" is backed on the page by the later critiques (Ṣaghānī's *Takmila*; Fīrūzābādī's "half/two-thirds … or more"). **Supported as interpretation.**

## 3. Sources

`qamus-preface` was added with kind primary. The citation details match the Shāmila book card, and p. 27 was seen. **Supported.**

## Validator

`node scripts/validate-dictionary-guides.mjs al-sihah`: ok, 1/1 pass, with 12 root links, 7 excerpts and 1,110 words (lede + body). That is the upper edge of the 700–1,100 target. It is a note, not an error.

## Result (final state)

- Claims checked: 5 (Muzhir "two-thirds" reading; the teachers/circulation clause in the same sentence; the Qāmūs "half" reading; the qamus-preface citation; the lede interpretation).
- Supported: 4. Needed qualification: 1, fixed in the guide ("the printed" became "a modern edition of the"). Unsupported: 0.
