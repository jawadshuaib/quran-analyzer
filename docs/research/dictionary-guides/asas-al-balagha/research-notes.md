# Research notes — Asās al-Balāgha (guide slug `asas-al-balagha`)

Dictionary slug on site: `al-zamakhshari-asas-al-balagha` · site label "Asās al-Balāgha | أساس البلاغة | al-Zamakhsharī | stored date 1143 | ar | 1505 displayed entries".

Drafted 2026-09-26. Everything below was opened and read during drafting; URLs were fetched (curl or WebFetch) and returned HTTP 200.

---

## 1. What al-nuqta displays

Tool: `python3 roots/backend/_dict_guide_tool.py …` (read-only; displayed entries only).

- `dicts`: 1,505 displayed entries. `roots … --limit 2000` shows every displayed root has `quran_freq ≥ 1` (tail of the frequency sort is freq = 1), i.e. only roots that occur in the Qur'an are shown.
- Headword count in hawramani's copy: the Asās landing page https://arabiclexicon.hawramani.com/al-zamakhshari-asas-al-balagha/ lists the contents under all 28 letters (ا … ي); I counted 3,729 multi-letter headings in that list (script over the fetched HTML). So al-nuqta shows roughly 40% of the headings hawramani holds. (Headings ≠ roots exactly; say "about 3,700 headings".)
- hawramani states NO edition/source for its Asās text. The landing page gives only a blurb ("dictionary and phrasebook concerned with balāgha…", d. 1143 CE / 538 AH). The per-root page (خلق) shows the section credit "Al-Zamakhsharī, Asās al-Balāgha (d. 1143 CE) أساس البلاغة للزمخشري" and the text, nothing else. The "About" page yielded nothing on editions.
- **Which text our copy represents (inference, strong):** I compared five stored entries with the al-Maktaba al-Shāmila digital text of the ʿUyūn al-Sūd edition (book 21568; card: "تحقيق: محمد باسل عيون السود — الناشر: دار الكتب العلمية، بيروت — الطبعة الأولى ١٤١٩ هـ - ١٩٩٨ م — [ترقيم الكتاب موافق للمطبوع]"). All five match word for word, including the same slips:
  - كفر — Shāmila vol. 2 pp. 140–141 (https://shamela.ws/book/21568/838 and /839): identical, incl. "وفيث الحديث" (for وفي الحديث) and ending "وكفّر الله عنك خطاياك."
  - أله — vol. 1 p. 33 (https://shamela.ws/book/21568/19): "[أل هـ] فلان يتأله: يتعبد. وهو عابد متأله." — the whole entry; our stored entry is identical (41 chars).
  - خلق — vol. 1 p. 264 (https://shamela.ws/book/21568/247): identical incl. "خلفاء جبهته" (apparently for خلقاء).
  - ضلل — vol. 1 pp. 585–586 (https://shamela.ws/book/21568/566): identical.
  - جيء — vol. 1 p. 162 (https://shamela.ws/book/21568/145): identical incl. "وما اء بك؟" (for وما جاء بك).
  → Say in onOurSite: matches this digital text "in every entry we compared"; hawramani does not name its source. Do NOT say hawramani took it from Shāmila (not established).
- Peculiarities of the stored text:
  - Each entry opens with the root letters spaced (e.g. "خ ل ق") — the edition's bracketed heading "[خ ل ق]" without brackets.
  - Largely unvowelled; occasional shadda and a few vowel marks.
  - Qur'anic phrases in quotation marks, no verse numbers (e.g. ضلل: " أئذا ضللنا في الأرض "; ربط: " لولا أن ربطنا على قلبها ").
  - Poetry hemistichs separated by "...".
  - Typos inherited from the digital text (above).
  - Markers (grep over displayed originals): "ومن المجاز" in 1,037 of 1,505 entries; "ومن الكناية" in 11; "ومن المستعار" in 23 (almost all ʿayn roots: عند، عرف، عدد، عصي، عجب، عجز، عوذ، عطو، عذر، عون، عوم …); "وأصله" in 45; "والأصل" in 13.
  - Entry length: 28 characters (شمز, وطر) to 3,039 (ربع); e.g. أله = a single line.
  - كفر has no "ومن المجاز" section in this edition, although it includes denial and "ascribing kufr" — a reminder that not every entry is split.

Entries read in full (original + site translations): كفر (kfr), خلق (xlq), ضلل (Dll), جيء (jyA), أله (Alh), ربط (rbT), زود (zwd), عوم (Ewm, start). Source URLs opened on hawramani: خلق page (https://arabiclexicon.hawramani.com/خلق/), Asās landing page.

---

## 2. Claims and their sources

### Identity, author, dates

| Claim | Source | Passage |
|---|---|---|
| Title أساس البلاغة; author Abū l-Qāsim (Jār Allāh) Maḥmūd b. ʿUmar al-Zamakhsharī, d. 538 AH | Shāmila card for the ʿUyūn al-Sūd ed. https://shamela.ws/book/21568 | "الكتاب: أساس البلاغة — المؤلف: أبو القاسم جار الله محمود بن عمر بن أحمد الزمخشري (ت ٥٣٨ هـ)" |
| Grandfather's name differs: "بن أحمد" (Shāmila card) vs "بن محمد" (al-Dhahabī) | Siyar vol. 20 p. 151 | "أَبُو الْقَاسِمِ مَحْمُودُ بْنُ عُمَرَ بْنِ مُحَمَّدٍ" → authorFull uses only "Maḥmūd ibn ʿUmar" |
| Born Rajab 467 in Zamakhshar, a village of Khwārazm | al-Dhahabī, *Siyar aʿlām al-nubalāʾ* vol. 20 p. 154 (IslamWeb digital text) https://www.islamweb.net/ar/library/content/60/5086/%D8%A7%D9%84%D8%B2%D9%85%D8%AE%D8%B4%D8%B1%D9%8A | "وكان مولده بزمخشر -قرية من عمل خوارزم- في رجب سنة سبع وستين وأربعمائة" |
| Died on the eve of ʿArafa 538 (al-Samʿānī via al-Dhahabī) | Siyar vol. 20 p. 155 | "مات ليلة عرفة سنة ثمان وثلاثين وخمس مائة" |
| Resided (in Mecca) "until the winds of the desert blew upon his speech" (al-Samʿānī, quoted by al-Dhahabī) | Siyar vol. 20 p. 155; "وحج، وجاور" p. 153 | "جاور مدة حتى هبت على كلامه رياح البادية" |
| An active Muʿtazilī | Siyar vol. 20 p. 151 ("كبير المعتزلة"), p. 156 ("وكان داعية إلى الاعتزال"); Haywood p. 104 ("he held unorthodox views, being a Mu'tazilite") |
| Dates 467/1075–538/1144; born Zamakhshar near Khwarizm; settled in Mecca some years, nicknamed Jarallah "neighbour of God"; died in his native land | J. A. Haywood, *Arabic Lexicography* (Leiden: Brill, 1960), p. 104. Full text: https://archive.org/details/in.gov.ignca.12555 (djvu text read) | "(467/1075-538/1144) … bom in the village of Zamakhshar near Khwarizm … went to Mecca, where he settled some years and acquired the nickname 'Jarallah' (neighbour of God). He died, however, in his native land." |
| Wrote the Kashshāf (Qur'an commentary) and al-Mufaṣṣal (grammar) | Siyar p. 152 ("صاحب الكشاف والمفصل"); Haywood p. 105 |

**Date conversion (my own arithmetic, tabular Islamic calendar):** 1 Muḥarram 538 = 16 July 1143 (Julian); 9 Dhū l-Ḥijja 538 (day of ʿArafa; its eve = the night before) ≈ 13 June 1144. So death = June 1144 CE. Rajab 467 ≈ Feb–Mar 1075.

**Disagreement on the CE year:** our DB stores 1143; hawramani says "d. 1143 CE / 538 AH"; English Wikipedia (Al-Zamakhshari, opened 2026-09-26) gives "12 July 1143 AD (Monday, eve of 8th Dhu AlHijjah, 538 AH)" — internally inconsistent (8/9 Dhū l-Ḥijja 538 fell in June 1144; 12 July 1143 is before 1 Muḥarram 538). Haywood gives 538/1144. → Guide uses "d. 538 AH / 1144 CE"; **siteDataIssue**: stored 1143 should be 1144 (ordering in the panel is unaffected: neighbours are 1109 and 1268). Wikipedia also says the Asās was "first published in 1998" — wrong (Haywood cites a Cairo 1953 edition; the Shāmila card, quoting al-Warrāq, lists Cairo 1299 AH, 1327 AH, Dār al-Kutub 1341/1922) — Wikipedia not used as support for anything.

### The author's introduction (primary; read in Arabic)

Edition: al-Zamakhsharī, *Asās al-Balāgha*, ed. Muḥammad Bāsil ʿUyūn al-Sūd, 2 vols (Beirut: Dār al-Kutub al-ʿIlmiyya, 1998), vol. 1 pp. 15–16; Shāmila text "numbering matches the print". p. 15 = https://shamela.ws/book/21568/1 ; p. 16 = https://shamela.ws/book/21568/2 (the first fetch of /2 returned a different book due to a site glitch; re-fetched and got "ج1 - ص16 - كتاب أساس البلاغة - مقدمة المؤلف").

1. **Qur'anic motivation (p. 15)** — "هذا، ولما أنزل الله تعالى كتابه مختصاً من بين الكتب السماوية بصفة البلاغة … كان الموفق من العلماء الأعلام … من كانت مطامح نظره، ومطارح فكره، الجهات التي توصل إلى تبين مراسم البلغاء، والعثور على مناظم الفصحاء، والمخايرة بين متداولات ألفاظهم … والمغايرة بين ما انتقوا منها وانتخلوا، وما انتفوا عنه فلم يتقبلوا … والنظر فيما كان الناظر فيه على وجوه الإعجاز أوقف … وإلى هذا الصوب ذهب عبد الله الفقير إليه محمود بن عمر الزمخشري … في تصنيف كتاب أساس البلاغة".
   Paraphrase used: because God singled out His book by eloquence, the well-guided scholar is the one who studies the ways of eloquent speakers — weighing the words they chose against those they rejected — since that brings one closest to the aspects of the Qur'an's inimitability (iʿjāz); "in this direction" he composed the Asās.
2. **Material (p. 15)** — "فليت له العربية وما فصح من لغاتها، وملح من بلاغاتها، وما سمع من الأعراب في بواديها، ومن خطباء الحلل في نواديها، ومن قراضبة نجد في أكلائها ومراتعها، ومن سماسرة تهامة في أسواقها ومجمعها، وما تراجزت به السقاة … وتساجعت به الرعاة … وما تقارضته شعراء قيس وتميم … وما تزاملت به سفراء ثقيف وهذيل … وما طولع في بطون الكتب ومتون الدفاتر". (Shāmila has "قراضبة تجد" — obvious misprint for نجد, as the al-Warrāq quotation on the card has "نجد".) Paraphrase used: he says he combed Arabic for it — its eloquent dialects, what was heard from Bedouin in their deserts, orators, poets of Qays and Tamīm, and what he read in books. (I mention Bedouin, orators, poets, books — all in the passage.)
3. **Feature 1 (p. 15)** — "ومن خصائص هذا الكتاب تخير ما وقع في عبارات المبدعين وانطوى تحت استعمالات المفلقين، أو ما جاز وقوعه فيها، وانطواؤه تحتها، من التراكيب التي تملح وتحسن". My translation: "Among the features of this book is the selection of pleasing, graceful constructions that occur in the expressions of masterful stylists and fall within the usage of brilliant speakers — or that could admissibly occur in them and fall within that usage."
   → KEY for evidence: he includes what "could admissibly occur" (ما جاز وقوعه), not only attested phrases.
4. **Feature 2 (p. 16)** — "ومنها التوقيف على مناهج التركيب والتأليف … بسوق الكلمات متناسقة لا مرسلة بدداً" (showing how words are combined, presenting them in ordered sequences, not scattered). Not quoted in the guide except by implication ("phrases rather than definitions").
5. **Feature 3 (p. 16)** — "ومنها تأسيس قوانين فصل الخطاب والكلام الفصيح، بإفراد المجاز عن الحقيقة والكناية عن التصريح". My translation: "And among them: laying down the rules of decisive and eloquent speech, by setting the figurative (majāz) apart from the literal (ḥaqīqa), and indirect expression (kināya) apart from plain statement." (Quoted in the guide.)
6. **Audience (p. 16)** — "فمن حصل هذه الخصائص وكان له حظ من الإعراب … وأصاب ذرواً من علم المعاني، وحظي برش من علم البيان، وكانت له قبل ذلك كله قريحة صحيحة وسليقة سليمة، فحل نثره، وجزل شعره، ولم يطل عليه أن يناهز المقدمين". Paraphrase used: whoever masters these features, with some grammar, rhetoric and natural talent, will find his prose potent and his poetry grand and will soon rival the foremost. → intended reader = the aspiring writer/poet (plus the scholar of iʿjāz, item 1).
7. **Arrangement (p. 16)** — "وقد رتب الكتاب على أشهر ترتيب متداولاً، وأسهله متناولاً … من غير أن يحتاج … إلى النظر فيما لا يوصل إلا بإعمال الفكر إليه، وفيما دقق النظر فيه الخليل وسيبويه". He calls it the best-known and easiest order, not requiring what al-Khalīl and Sībawayh examined minutely. I do NOT interpret this as an allusion to the ʿAyn's phonetic order in the guide (plausible, but I have no scholarly source for it in hand).

### Scholarship

**Haywood, *Arabic Lexicography* (1960)** — https://archive.org/details/in.gov.ignca.12555 (full text read; page headers visible in OCR).
- p. 104: dates, Mu'tazilite, Hejaz "studying the speech of the pure Arabs", Mecca, Jarallah.
- p. 106: "With the Asas al-Balagha, however, al-Zamakhshari introduced the modern dictionary order in its entirety, listing words under their roots according to the alphabetical order of all their component letters from the first to the last. He compiled this dictionary with a special aim—to distinguish between the literal use of words and the metaphorical (haqiqa and majaz). He lived in an age when rhetoric was seriously studied by every man claiming to be cultured, the time of ornate rhymed prose… In the 'Asas', each entry is divided into two parts. The first gives ordinary meanings; the second, introduced by the formula wa min al-majaz (and metaphorically). There are examples from the Quran, the Hadith, poetry, and proverbs… Al-Zamakhshari tells us in his introduction that he is interested in how words are used by men of genius. He was interested in words as parts of constructions, not as isolated units of meaning… In order to achieve his purpose without prolixity, al-Zamakhshari adopted two courses. Firstly, he made no attempt to give a comprehensive account of the various derivations of any particular root. Secondly, he omitted rare roots: quadriliterals and quinquiliterals are hardly [found] at all."
- p. 107: "For this reason, the 'Asas' would not be a satisfactory aid to the understanding of Arabic poetry—particularly that of the Jahiliya and the Omayyad period… The author almost saw words as living organisms… So he made a point of quoting late authors, including those of his own time."
- Haywood's footnote gives the edition he used: Cairo 1953, ed. Amīn al-Khūlī (not consulted by me).
- Claim of priority ("introduced the modern dictionary order in its entirety") — I do NOT repeat it (priority claims are contested; see Lane below and the Arabic encyclopedia note on Shāmila "من السابقين إلى هذا الترتيب إن لم يكن الأول"). Guide says only that the printed text is in alphabetical order of all root letters, citing Haywood's description.

**Lane, *An Arabic-English Lexicon*, Book I Part 1 (London, 1863), Preface** — https://archive.org/details/arabicenglishlex0001edwa (djvu text read; page headers "PREFACE. xv", "PREFACE. xxv").
- p. xv: "[The 'Asás' of Ez-Zamakhsheree, who was born in the year of the Flight 467, and died in 538 [OCR '588']. This lexicon is a very excellent repertory of choice and chaste words and phrases; and especially and peculiarly valuable as comprising a very large collection of tropical significations, distinguished as such, which has greatly contributed, by indirectly illustrating proper significations as well as otherwise, to the value of my own lexicon, as my numerous citations of it will show, although I have generally been obliged to draw from it through the medium of the Taj el-'Aroos, which often does not name it in quoting it. Its order is the same as that of the Mujmal, apparently in most copies: but some, which are said to be abridged, follow the order of the Sihah.]"
- p. xxv: "Whenever I have found it possible to do so, I have distinguished (by the mark †) what is affirmed to be tropical from what is proper; generally on the authority of the Asás."
- Abbreviation list (same preface): "A — The 'Asás' of Ez-Zamakhsheree"; "Tropical, مجاز and مجازيّ" (page number not secure in OCR; not cited with a page).
- **Disagreement on arrangement:** Haywood (printed text) = strict alphabetical by all radicals; Lane = "the same as that of the Mujmal, apparently in most copies", some copies in Ṣiḥāḥ order. The Shāmila/ʿUyūn al-Sūd text and hawramani's list are in strict alphabetical order (e.g. ك أب، ك أد، ك أس، ك ب ب …). Mentioned briefly in the guide.

**Primary: al-Kashshāf on Q 89:22** — https://tafsir.app/kashaf/89/22 (fetched; passage located in HTML): "فإن قلت: ما معنى إسناد المجيء إلى الله، والحركة والانتقال إنما يجوزان على من كان في جهة؟ قلت: هو تمثيل لظهور آيات اقتداره وتبين آثار قهره وسلطانه". My translation: "If you ask: what is meant by ascribing 'coming' to God, when motion and moving from place to place are possible only for what is located somewhere? I say: it is a figurative representation (tamthīl) of the appearing of the signs of His power and the evidences of His might and dominion."

### Displayed evidence of reception (on al-nuqta itself)

- Tāj al-ʿArūs, root خلق (displayed): "…وَفِي الأساسِ: وَمن المَجازِ: خَلَقَ اللهُ الخَلْقَ: أَوْجَدَهُ على تَقْدِيرٍ أَوْجَبَتْهُ الحِكْمَةُ." Also "وَفِي الأساسِ: رَجُلٌ مخْتَلَقٌ: حَسَنُ الخِلْقَةِ… وَهُوَ مَجازٌ". The phrase "في الأساس" occurs in 656 displayed TA entries (grep) — not used as a number in the guide.
- Lane, root خلق (displayed original, English): "Accord. to the A , خَلَقَ اللّٰهُ الخَلْقَ is a tropical phrase, meaning ( tropical :) God brought into existence the creation, or created beings, or mankind, according to a predetermination (تَقْدِير) required by wisdom. ( TA .)" — shows the chain Asās → TA → Lane, as Lane's preface says.
- Ibn Fāris, Maqāyīs, root خلق (displayed): "الْخَاءُ وَاللَّامُ وَالْقَافُ أَصْلَانِ: أَحَدُهُمَا تَقْدِيرُ الشَّيْءِ، وَالْآخَرُ مَلَاسَةُ الشَّيْءِ … وَمِنْ ذَلِكَ الْخُلُقِ، وَهِيَ السَّجِيَّةُ، لِأَنَّ صَاحِبَهُ قَدْ قُدِّرُ عَلَيْهِ". No literal/figurative sorting; no mention of God's creating in the displayed entry. My translation of the reason clause: "because its possessor has been measured out upon it".

---

## 3. Root examples considered

| Root | Displayed? | Used? | Why |
|---|---|---|---|
| خلق xlq | yes (entry 51); also shown in Ibn Fāris, TA, Lane | **CLOSE READING** | Literal = the leather-worker/tailor measuring before cutting ("قدّره قبل القطع"); figurative section opens with God's creating "أوجده على تقدير أوجبته الحكمة" — same idea of measure (taqdīr) reused (my observation). Also khuluq, khalīq "كأنما خلق له وطبع عليه", fabricating a lie "خلق الإفك واختلقه", an unattributed maxim "وخالق الناس ولا تخالفهم". Reception visible in TA and Lane. Comparison with Ibn Fāris (two aṣl, reasons given). |
| ضلل Dll | yes (entry 641) | **YES** | Literal: straying from the road/intended course; ḍalaltu vs aḍlaltu a camel (hobbled vs loose); losing a ring. "ومن المجاز: ضل في الدين" — religious straying classed as figurative. Figurative part also: water vanishing in milk "إذا خفي فيه وغاب", then the Qur'anic " أئذا ضللنا في الأرض " (Q 32:10), then burial "وأضل الميت: دفن" with a line by al-Mukhabbal. |
| جيء jyA | yes (entry 361) | **YES (short)** | "ومن المجاز: جاء ربك" — first item of the figurative list, no comment (cf. Q 89:22 "وجاء ربك والملك صفا صفا"). Kashshāf explains it as tamthīl because motion belongs only to what is located. Shows the label can carry a theological judgment. Literal part also has a dialect note from Abū Zayd (dropping the hamza). |
| ربط rbT | yes | no (kept for notes) | Very good: literal tying of a beast; explicit derivation "ورابط الجيش: أقام في الثغر والأصل أن يربط هؤلاء وهؤلاء خيلهم، ثم سمي الإقامة في الثغر مرابطةً ورباطاً"; figurative "ربط الله على قلبه: صبره " لولا أن ربطنا على قلبها "" (Q 28:10). Dropped only to stay within 2–3 examples. Note: includes the later formula "اللهم انصر جيوش المسلمين ومرابطاتهم" and a rhymed model sentence "لولا رجاحة رأيه ورباطة جأشه…". |
| كفر kfr | yes | rejected | No "ومن المجاز" marker at all in this edition; would mislead as an illustration of the literal/figurative split. |
| أله Alh | yes | rejected | One line only ("فلان يتأله: يتعبد. وهو عابد متأله.") — noted as a data point (short entries), not as an example. |
| زود zwd | yes | rejected | Short; Haywood's own example (التقوى خير زاد under majāz) — nice but duplicative. |
| عوم Ewm | yes | rejected | Uses "ومن المستعار" and "المجاز المرشح" — too technical for this essay. |

---

## 4. Open questions / evidence gaps

- Baalbaki, *The Arabic Lexicographical Tradition* (2014): not accessible to me in a legitimate open copy (Brill, paywalled; only pirate uploads found — not used). Encyclopaedia of Islam (Versteegh, "al-Zamakhsharī") — 403 from Brill; not consulted. Encyclopaedia Iranica — site returned 403; no Iranica article on the Asās found. So the scholarly account rests on Haywood (1960) and Lane's preface (1863), plus primary sources (introduction, Kashshāf, Siyar).
- Date of composition of the Asās: not established (Haywood: order of composition of the Fāʾiq and the Asās unknown).
- Which printed edition hawramani used: not stated by hawramani; our stored text matches the Shāmila digital text of the ʿUyūn al-Sūd edition in 5/5 compared entries (inference, not proof of provenance).
- Lane vs Haywood on arrangement in manuscripts — unresolved; I report both.
- Whether al-Zamakhsharī's majāz classifications are systematically shaped by Muʿtazilī theology: only one case shown (جاء ربك + Kashshāf on 89:22). The guide claims no more than that case.
- Ibn Ḥajar's abridgment *Ghirās al-Asās* (reported on the Shāmila card via al-Warrāq to keep only what al-Zamakhsharī marked as majāz): the only scan I found had unreadable OCR; not cited.
- The meaning of "فلم يهتد لمكانه" in the ضلل camel distinction: the subject shifts person (ضللت … فلم يهتد); I translate "he could not find his way to where it was" (the owner), in line with the parallel "ولم تدر أين أخذ".

## 5. Site data issues

- Stored date 1143 → should be 1144 (death on the eve of ʿArafa 538 AH ≈ 13 June 1144 CE; Haywood 538/1144). hawramani and Wikipedia also give 1143; Wikipedia's day/month is inconsistent with its own Hijri date.
- Author label "al-Zamakhsharī" is correct. Title correct.
- Inherited typos in stored text (وفيث for وفي in كفر; وما اء بك for وما جاء بك in جيء; خلفاء for خلقاء in خلق) — from the digital text, not introduced by al-nuqta.

---

## 6. Guide-text decisions (draft 1, 2026-09-26)

- Validator: passes, no warnings; lede + body = 1,100 words; 3 excerpts; root links xlq (Asās, Ibn Fāris, TA, Lane), Dll, jyA.
- Label for jyA written ج ي أ (the site spells the root جيا; the Asās heading is "ج ي ء") to match the root page.
- Statements explicitly marked as the guide's own interpretation: "figurative marks a position on his map, not a verdict" ("In our reading"); the reuse of *taqdīr* in the خلق glosses ("our observation; the entry gives no reason"); "the label carries a theological judgment" (jyA) — the Kashshāf passage is the evidence, the inference is ours.
- Count claims in the essay/onOurSite, all from `_dict_guide_tool.py grep` over displayed originals: ~90 entries naming al-Aṣmaʿī/Abū Zayd/Ibn al-Aʿrābī/Abū ʿUbayda/al-Farrāʾ/Sībawayh/al-Khalīl/Abū ʿAmr/al-Liḥyānī/Ibn al-Sikkīt/al-Kisāʾī (regex union = 90); 1,037 with ومن المجاز; 11 ومن الكناية; 23 ومن المستعار; وأصله 45 + والأصل 13 (supports "entries seldom say how one use grew from another").
- Lane's "tropical" = majāz: from the abbreviation list in the Preface (page not secured from OCR, so cited without locator); "generally on the authority of the Asás" p. xxv; "through the medium of the Taj el-'Aroos, which often does not name it" p. xv.
- "Lane believed most copies followed the order of … *Mujmal*" — Lane: "Its order is the same as that of the Mujmal, apparently in most copies" (p. xv).
- Haywood p. 107 "not a satisfactory aid to … poetry … of the Jahiliya and the Omayyad period" is attributed to Haywood by name.

---

## 7. Addendum (revision r1, 2026-09-26)

Details are in `revision-r1.md`. Evidence added in this round:

- **Lane, Preface p. xxix** (archive.org `arabicenglishlex0001edwa`, page image leaf n34): Table II lists "Tropical, مَجَازٌ and مَجَازِيٌّ". The key at the foot of the page reads "‡ means asserted to be tropical / ‡‡ asserted to be doubly tropical / † supposed by me to be tropical". (Correction to §2: p. xxv uses ‡ for "affirmed to be tropical … generally on the authority of the Asás" and † for Lane's own supposition. The OCR had swapped the glyphs.)
- **Stored Lane labels vs print:** p. 11 (أبو) † = stored "(assumed tropical :)" in six cases. p. 83 (أله) ‡ = stored "( tropical :)" for لله درك (A), but ‡ is also stored as "(assumed tropical :)" for لله درّه (Ḥar p. 11). The mapping is generally reliable but not always.
- **DB recounts** (displayed originals, vowels stripped): ومن المجاز 1,037; ومن المستعار 23 (none also with ومن المجاز); ومن الكناية 11 (7 without ومن المجاز); 438 entries with none of the three. Named philologists: union of about 106 entries (some noise). A speaker is named in about 1,000 entries, mostly poets (ذو الرمة 186 mentions, الراعي 73, النابغة 69, الأعشى 69 …); a bare قال: occurs in 632. Hadith introduced by (و)في الحديث open with a quotation mark in 135 of 144 cases; في المثل in 10 of 11. استعير/مستعار من occurs in 27 entries (e.g. HbT).
- **Shamela intro re-read** (21568/1, /2): p. 15 addresses the scholar of iʿjāz; p. 16 addresses the would-be writer and closes "والله تعالى الموفق إلى إفادة أفاضل المسلمين".

---

## 8. Addendum (revision r2, 2026-09-26)

Details are in `revision-r2.md`. Recounts over the displayed entries (SHOWN filter, vowels stripped):

- Markers: 1,505 in total. 1,037 contain ومن المجاز. 23 contain ومن المستعار without ومن المجاز. 7 contain ومن الكناية without either: Axr, swA, H*r, zyl, brz, Sdf, xDE. 438 contain none of the three, counted directly.
- *Kināya* is not *majāz* for al-Zamakhsharī. His introduction (p. 16) pairs المجاز/الحقيقة and الكناية/التصريح as two separate distinctions. xDE heads a section "ومن الكناية والمجاز". Several kināya sections are euphemisms: brz "خرج إلى البراز", swA "بدت سوءته", bDE "ملك بضعها".
- Reason clauses: 256 of 1,505 entries contain لأن anywhere. 478 contain any of لأن, استعير, وأصله, والأصل, كأنما or كأنه. In the figurative part of the 1,037 ومن المجاز entries, 135 contain لأن by my regex (the verifier counted 98 with a narrower one).
- القصد in the Asās: qSd (id 8389), in its figurative part, reads "وهو على القصد، وعلى قصد السبيل إذا كان راشداً", the right course. I used this for the Dll translation "from the right course".
