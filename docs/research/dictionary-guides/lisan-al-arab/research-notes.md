# Lisān al-ʿArab (Ibn Manẓūr) — research notes

Guide: `roots/frontend/src/content/dictionary-guides/guides/lisan-al-arab.ts`
Site dictionary slug: `ibn-manzur-lisan-al-arab` (1,452 displayed roots; stored date 1311)
Compiled 2026-09-26 by the drafting agent. Every claim in the guide is listed below with
its source, URL and the passage that supports it. Translations of Arabic are mine
(made for this guide) unless stated.

---

## 0. Sources actually opened

| id in guide | Source | URL | What I read |
|---|---|---|---|
| `lisan-ds` | Ibn Manẓūr, *Lisān al-ʿArab*, 3rd ed., 15 vols, Beirut: Dār Ṣādir, 1414 AH, "مذيل بحواشي اليازجي وجماعة من اللغويين" (Shamela card). Page numbers = print ("ترقيم الكتاب موافق للمطبوع"). | https://shamela.ws/book/1687 (pages /3 … /13; /1320–1321; /2001–2005) | Publisher's preface (vol. 1 p. 3); biographies reproduced from Ibn Ḥajar and al-Suyūṭī (p. 4); preface of the first (Būlāq) edition by Aḥmad Fāris [al-Shidyāq] (pp. 5–6); the AUTHOR'S INTRODUCTION (pp. 7–9); ḥurūf muqaṭṭaʿa chapter (pp. 10–12); letters chapter (p. 13); entry صلح (vol. 2 pp. 516–517); entry بحر (vol. 4 pp. 41–44+) |
| `durar` | Ibn Ḥajar, *al-Durar al-kāmina* + al-Suyūṭī, *Bughyat al-wuʿāt*, biographies of Ibn Manẓūr, as reproduced in the Dār Ṣādir ed., vol. 1, pp. 4–5 | https://shamela.ws/book/1687/4 | full text of both notices |
| `haywood` | John A. Haywood, *Arabic Lexicography: Its History, and Its Place in the General History of Lexicography* (Leiden: Brill, 1960), ch. 7 "Later dictionaries in the rhyme arrangement", pp. 77–82; ch. 6 p. 71 | Read in the full-text scan https://archive.org/details/ArabicLexicographyItsHistoryAndItsPlaceInTheGeneralHistoryOfLexicography-JohnA.Haywood (Binder2_djvu.txt); the guide links the Internet Archive library copy of the same 1960 Brill edition https://archive.org/details/arabiclexicograp0000hayw (opened, HTTP 200; borrowable) | pp. 68–72 (al-Jawharī's rhyme order), 77–82 (Lisān), 89 (Lane on Tāj) |
| `baalbaki-2019` | Ramzi Baalbaki, "The Notion of gharīb in Arabic Lexica", *Journal of Abbasid Studies* 6 (2019) 185–208, doi:10.1163/22142371-12340050 | https://scholarworks.aub.edu.lb/server/api/core/bitstreams/425764aa-f823-42e2-a34d-2c19e4178713/content | whole article; pp. 186 n. 1, 202, 203 + n. 84 |
| `lane` | E. W. Lane, *An Arabic-English Lexicon*, Book I, Part 1 (London: Williams and Norgate, 1863), Preface | https://archive.org/details/anarabicenglish03lanegoog | Preface pp. xvi, xviii, xx (this Google scan lacks the odd preface pages xiii–xxv; page numbers read from the running heads of scan leaves 18–20) |
| `nihaya` | Ibn al-Athīr (Majd al-Dīn), *al-Nihāya fī gharīb al-ḥadīth wa-l-athar*, ed. Ṭāhir Aḥmad al-Zāwī & Maḥmūd Muḥammad al-Ṭanāḥī, 5 vols (Beirut: al-Maktaba al-ʿIlmiyya, 1399/1979) | https://shamela.ws/book/23691/97 (vol. 1 p. 99) and /98 (p. 100) | entry بحر |
| `hawramani` | "Ibn Manẓūr, Lisān al-ʿArab", The Arabic Lexicon | https://arabiclexicon.hawramani.com/ibn-manzur-lisan-al-arab/ ; also /about/ and root pages صرط، بحر، ضيع، سلم، قبل، دعو، دعا، صلو، صلا، زكو، زكا | intro blurb + contents list |

Consulted but NOT cited in the guide:
- Zeinab A. Taha, review of Baalbaki, *The Arabic Lexicographical Tradition* (2014), *JALT* 13 (2015) 62–66 — https://sites.lsa.umich.edu/jalt/wp-content/uploads/sites/1121/2023/07/TahaJalt134.pdf . Only a two-sentence summary of Baalbaki's Lisān section (five sources; complaint about jamʿ vs waḍʿ). Baalbaki's 2014 book itself could not be accessed legitimately (only pirated copies turned up) → evidence gap.
- Wikipedia (en/ar) "Lisan al-Arab", "Ibn Manzur" — leads only (e.g. "completed 1290/689" — NOT used: no primary support found).
- Encyclopaedia of Islam² "Ibn Manẓūr" (J. W. Fück) — Brill pages return 403; not consulted → gap.
- islamweb.net Lisān text for سلم (search result) — used only to confirm that the printed Lisān has an article سلم (notes §6).

---

## 1. Identity of the work and author

| Claim in guide | Source | Passage |
|---|---|---|
| Title *Lisān al-ʿArab* given by the author | `lisan-ds` vol. 1 p. 8 | "…وسميته [لسان العرب]" |
| Author's self-designation in the book: "ʿAbd Allāh Muḥammad ibn al-Mukarram…" | `lisan-ds` vol. 1 p. 7 | "قال عبد الله محمد بن المكرم بن أبي الحسن بن أحمد الأنصاري الخزرجي، عفا الله عنه بكرمه" |
| Full name (authorFull) Jamāl al-Dīn Abū l-Faḍl Muḥammad ibn Mukarram ibn ʿAlī al-Anṣārī al-Ifrīqī al-Miṣrī | `durar` (Ibn Ḥajar), `haywood` p. 77 | Ibn Ḥajar: "هو محمد بن مكرم بن علي بن أحمد الأنصاري الإفريقي ثم المصري جمال الدين أبو الفضل"; Haywood: "Muhammad ibn Mukarram ibn ʿAli Ridwan … ibn Manzur al-Ansari al-Ifriqi al-Misri Jamal al-Din Abu l-Fadl" |
| Born Muḥarram 630, died Shaʿbān 711 | `durar` (Ibn Ḥajar, Suyūṭī); `haywood` p. 77 "(630/1232–711/1311)"; Dār Ṣādir footnote to the Būlāq preface, vol. 1 p. 5 n. 1 (corrects the Būlāq preface's 690/771 to 630/711 citing al-Ṣafadī, Ibn Ḥajar, Ibn Taghrībirdī, al-Suyūṭī) | "ولد سنة ٦٣٠ في المحرم … ومات في شعبان سنة ٧١١" |
| CE conversion | my computation (tabular calendar): 1 Shaʿbān 711 = 13 Dec 1311 (Julian); 29 Shaʿbān 711 = 10 Jan 1312. 1 Muḥarram 630 = 18 Oct 1232 | → period "630–711 AH / 1232–1311 or 1312 CE" |
| Served in the chancery (dīwān al-inshāʾ) all his life; judge of Tripoli | `durar` (Ibn Ḥajar) | "وخدم في ديوان الإنشاء طول عمره وولي قضاء طرابلس" |
| "secretariat of the Mamluk rulers of Egypt … afterwards judge of Libyan Tripoli" | `haywood` pp. 77–78 | quoted |
| Al-Ṣafadī (quoted by Ibn Ḥajar): knew of hardly a long book he had not abridged; left 500 volumes in his hand | `durar` | "قال الصفدي: لا أعرف في الأدب وغيره كتابا مطولا إلا وقد اختصره، قال: وأخبرني ولده قطب الدين أنه ترك بخطه خمسمائة مجلدة" |

Disagreements recorded (not all used in the guide):
- **Birthplace**: Dār Ṣādir's own biographical note: "ولد ابن منظور في القاهرة، وقيل في طرابلس" (vol. 1, publisher's biography page, shamela /2); Haywood p. 77: "born in Tunis". Not mentioned in the guide (irrelevant to reading the dictionary, and unresolved).
- **Name**: Suyūṭī gives "محمد بن مكرم بن علي وقيل رضوان"; the author writes "محمد بن المكرم". Guide uses "Muḥammad ibn Mukarram" for the header and quotes his self-label "Muḥammad ibn al-Mukarram" in the entries.
- **Sources list**: the author's introduction names five works (below). Ibn Ḥajar ("جمع فيه بين التهذيب والمحكم والصحاح والجمهرة والنهاية وحاشية الصحاح"), al-Suyūṭī ("…والصحاح وحواشيه والجمهرة والنهاية") and the Būlāq preface by Aḥmad Fāris (vol. 1 p. 6: "…والجمهرة لابن دريد، والنهاية لابن الأثير، وغير ذلك") add Ibn Durayd's *Jamhara*. Recorded in the guide in one sentence.
- **Completion date** (689/1290 in Wikipedia and web pages): no primary or scholarly source seen → not used.
- **Ibn al-Athīr's identity/date**: hawramani's blurb says "Ibn al-Athīr (d. 1233 CE / 630 H)" — that is the historian ʿIzz al-Dīn; the *Nihāya* is by Majd al-Dīn Abū l-Saʿādāt al-Mubārak (d. 606/1210): the author's own intro names "أبا السعادات المبارك بن محمد بن الأثير الجزري" (vol. 1 p. 8); Baalbaki 2019 p. 202 "Ibn al-Athīr (d. 606/1210) in al-Nihāya"; Shamela card of the Nihāya "(ت ٦٠٦هـ)". Guide avoids the error (names "Ibn al-Athīr's *al-Nihāya*" and gives d. 606/1210).

## 2. The author's introduction (all `lisan-ds`, vol. 1)

| Claim | Location | Arabic (Dār Ṣādir text, vowels simplified) | My translation / paraphrase |
|---|---|---|---|
| Two kinds of lexicographers | p. 7 | "ورأيت علماءها بين رجلين: أما من أحسن جمعه فإنه لم يحسن وضعه، وأما من أجاد وضعه فإنه لم يجد جمعه" | "one who gathered well but did not arrange well; one who arranged well but did not gather well" (paraphrased in guide) |
| Tahdhīb (al-Azharī) and Muḥkam (Ibn Sīda) the fullest | p. 7 | "ولم أجد في كتب اللغة أجمل من تهذيب اللغة لأبي منصور محمد بن أحمد الأزهري، ولا أكمل من المحكم لأبي الحسن علي بن إسماعيل بن سيده الأندلسي" | paraphrase. Also establishes **Abū Manṣūr = al-Azharī** (used in the guide) |
| …but badly arranged, so people neglected them | p. 7 | "غير أن كلا منهما مطلب عسر المهلك … فأهمل الناس أمرهما، وانصرفوا عنهما … وليس لذلك سبب إلا سوء الترتيب" | paraphrase |
| al-Jawharī: well arranged, but "a drop in its sea"; errors; Ibn Barrī tracked them | p. 7 | "ورأيت أبا نصر إسماعيل بن حماد الجوهري قد أحسن ترتيب مختصره … غير أنه في جو اللغة كالذرة، وفي بحرها كالقطرة … وهو مع ذلك قد صحف وحرف … فأتيح له الشيخ أبو محمد بن بري فتتبع ما فيه، وأملى عليه أماليه، مخرجا لسقطاته، مؤرخا لغلطاته" | paraphrase ("a drop in the sea of the language") |
| Did not go beyond these sources; arranged as the Ṣiḥāḥ | p. 7 | "ولم أخرج فيه عما في هذه الأصول، ورتبته ترتيب [الصحاح] في الأبواب والفصول" | used |
| Wanted hadith/athar; took Ibn al-Athīr's *Nihāya*, re-filed words under proper roots | p. 8 | "وقصدت توشيحه بجليل الأخبار، وجميل الآثار … فرأيت أبا السعادات المبارك بن محمد بن الأثير الجزري قد جاء في ذلك بالنهاية … غير أنه لم يضع الكلمات في محلها، ولا راعى زائد حروفها من أصلها، فوضعت كلا منها في مكانه" | paraphrase ("re-filing its words under their proper roots") |
| No fieldwork claims | p. 8 | "وأنا مع ذلك لا أدعي فيه دعوى فأقول شافهت أو سمعت … أو نقلت عن العرب العرباء" | (not used in final text; Haywood p. 79 paraphrases it) |
| **"No merit … except that I gathered"** (quoted in guide) | p. 8 | "وليس لي في هذا الكتاب فضيلة أمتّ بها، ولا وسيلة أتمسك بسببها، سوى أني جمعت فيه ما تفرّق في تلك الكتب من العلوم" | "I have in this book no merit to plead and no claim to hold on to, except that I gathered in it the learning scattered through those books." |
| Credit/blame belongs to the first author; changed nothing | p. 8 | "فمن وقف فيه على صواب أو زلل، أو صحة أو خلل، فعهدته على المصنف الأول، وحمده وذمه لأصله الذي عليه المعول. لأنني نقلت من كل أصل مضمونه، ولم أبدل منه شيئا … وما تصرفت فيه بكلام غير ما فيها من النص" | paraphrase |
| Quoting the Lisān = quoting the five | p. 8 | "فليعتد من ينقل عن كتابي هذا أنه ينقل عن هذه الأصول الخمسة" | paraphrase |
| Purpose: preserve the language on which Qur'an/Sunna rulings turn | p. 8 | "فإنني لم أقصد سوى حفظ أصول هذه اللغة النبوية وضبط فضلها، إذ عليها مدار أحكام الكتاب العزيز والسنة النبوية" | paraphrase |
| Complaint: speaking Arabic counted a fault; rivalry in translations into foreign tongues; Noah's ark | p. 8 | "وصار النطق بالعربية من المعايب معدودا. وتنافس الناس في تصانيف الترجمانات في اللغة الأعجمية … وصنعته كما صنع نوح الفلك وقومه منه يسخرون" | paraphrase (Haywood p. 79 paraphrases the same) |
| Moved al-Azharī's section on the disconnected letters to the front | p. 9 | "شرطنا في هذا الكتاب المبارك أن نرتبه كما رتب الجوهري صحاحه … إلا أن الأزهري ذكر، في أواخر كتابه، فصلا جمع فيه تفسير الحروف المقطعة … وقدمتها في صدر كتابي" | used in onOurSite? — NO (cut for length); kept here |
| Author signs digressions "beyond my condition" with his name | p. 13 | "قال عبد الله محمد بن المكرم: هذا الباب أيضا ليس من شرطنا …" | supports "his own voice is signed" |

## 3. Arrangement

- Haywood p. 71 (on al-Jawharī): "Al-Jauhari arranged his roots according to their final radicals in the first instance … Within each chapter, roots are entered according to the first, and then the intermediate radicals." Haywood p. 80: "Ibn Manzur retained al-Jauhari's arrangement as being the handiest."
- Dār Ṣādir publisher, vol. 1 p. 3: kept the order ("ترتيب الأبواب على الحرف الأخير") and speculates it helps poets with rhyme ("ولعله أحد المقاصد"). Haywood p. 71 is sceptical of the "rhymes for poets" explanation ("It has been all too readily assumed…"). Guide does not give a reason.
- بحر sits in vol. 4 (the rāʾ chapter), "فصل الباء الموحدة", starting p. 41 (Shamela /2001 title "ج4 - ص41 … فصل الباء الموحدة"; the entry's Suhaylī passage p. 42; the Q 30:41 passage p. 44).

## 4. How voices are marked (evidence from stored entries; grep via `_dict_guide_tool.py grep`)

Counts in the 1,452 displayed entries (vowels ignored): "الأزهري" 783; "قال أبو منصور" 316; "التهذيب" 684; "ابن سيده" 864; "المحكم" 285; "الجوهري" 802; "الصحاح" 418; "ابن بري" 791; "ابن الأثير" 596; "وفي الحديث" 1,059; **"محمد بن المكرم" 21** (nfs, $rk, jzy, Hmd, dwr, bHr, vql, Emr, $kk, fqr, jld, jdd, nqD, brd, gwr, sll, bhm, wqb, njd, gwl, Smt).

Examples of the compiler's own signed remarks (stored text):
- Hmd — changes a source's wording out of reverence (quoted in guide; see §5.3).
- bHr — "شرطي في هذا الكتاب…" (quoted in guide; §5.1).
- wqb — corrects al-Jawharī: "قال محمد بن المكرم: في قول الجوهري دخلت موضعها، تجوز في اللفظ، فإنها لا موضع لها تدخله." (not used; candidate).
- Emr — objects to al-Azharī's phrasing about ʿUmar (not used).
- $kk — "نقلت هذا الكلام على نصه وفي قلمي نبوة عن قوله وأنا دونه" (not used; shows verbatim transmission with a separate signed reservation).

Verdicts inside labelled passages belong to the source:
- byn: "وكان أبو حاتم ينكر هذه القراءة … قال أبو منصور: وهذا الذي قاله أبو حاتم خطأ" (on Q 6:94 "لقد تقطع بينكم") — al-Azharī's verdict. Used in guide.
- bHr: "قال الأزهري: والقول هو الأول لما جاء في حديث أبي الأحوص الجشمي" — al-Azharī's preference among baḥīra definitions. Used.

Nested citation: Baalbaki 2019 p. 203 n. 84: "Note also that among the works cited by Ibn Manẓūr — obviously on the authority of his five sources — are several works on gharīb al-Ḥadīth …" (quoted, <15 words).

Haywood p. 81: "Ibn Manzur is content to repeat verbatim what previous lexicographers have written in their dictionaries; where two of them disagree, he tends merely to repeat what both have said, even at the risk of appearing to contradict himself." (quoted: "tends merely to repeat what both have said").

## 5. Root examples

### 5.1 بحر — bHr (CLOSE READING) — chosen
Displayed in Lisān (entry_id 2760; source_url https://arabiclexicon.hawramani.com/بحر/#c66c692138e8a64688944b89d05ea3b1 ; deep link /root/bHr#dict-ibn-manzur-lisan-al-arab). Also displayed in al-Muḥkam (entry 2756) and al-Ṣiḥāḥ (entry 2755). Printed: Dār Ṣādir vol. 4 pp. 41 ff.

What I checked (stored original vs displayed Muḥkam/Ṣiḥāḥ):
- Opening, unlabelled: "البحر: الماء الكثير، ملحا كان أو عذبا … قد غلب على الملح حتى قل في العذب، وجمعه أبحر وبحور وبحار. وماء بحر: ملح، قل أو كثر" = Muḥkam's opening ("البحر: الماء الكثير، ملحا كان أو عذبا وقد غلب على الملح حتى قل في العذب. وجمعه أبحر، وبحور، وبحار. وماء بحر: ملح، قل أو كثر"). Interleaved: "وهو خلاف البر، سمي بذلك لعمقه واتساعه" = Ṣiḥāḥ ("البحر: خلاف البر. يقال: سمي بحرا لعمقه واتساعه"). Neither named. ✔
- Naming explanations: (a) "قال ابن بري: هذا القول هو قول الأموي لأنه كان يجعل البحر من الماء الملح فقط. قال: وسمي بحرا لملوحته"; (b) "وأما غيره فقال: إنما سمي البحر بحرا لسعته وانبساطه"; also "وسمي البحر بحرا لاستبحاره، وهو انبساطه وسعته"; (c) "ويقال: إنما سمي البحر بحرا لأنه شق في الأرض شقا … والبحر في كلام العرب: الشق". No verdict by Ibn Manẓūr. ✔
- al-baḥīra (Q 5:103 "ما جعل الله من بحيرة ولا سائبة ولا وصيلة ولا حام" — quoted in the entry): Ibn Sīda: ear split after ten births, flesh forbidden to women, lawful to men; variants (lengthwise; left without herdsman; the abundant milker); Abū Isḥāq via al-Azharī: after five births with the last a male; "وقيل: البحيرة الشاة…" (ewe); al-Azharī: "والقول هو الأول لما جاء في حديث أبي الأحوص الجشمي"; al-Farrāʾ: daughter of the sāʾiba; Ibn ʿArafa via al-Azharī: five births, fifth male slaughtered/eaten, female → ear slit, forbidden to women; hadith material: a male calf (saqb) whose ear was slit. → "a string of accounts that disagree about how many births, which animal and what was forbidden; al-Azharī prefers one on the strength of a hadith". ✔
- **Q 30:41** (excerpt quoted in guide, stored text verbatim): "والبحر: الريف، وبه فسر أبو علي قوله عز وجل: ظهر الفساد في البر والبحر؛ لأن البحر الذي هو الماء لا يظهر فيه فساد ولا صلاح؛ وقال الأزهري: معنى هذه الآية أجدب البر وانقطعت مادة البحر بذنوبهم، كان ذلك ليذوقوا الشدة بذنوبهم في العاجل؛ وقال الزجاج: معناه ظهر الجدب في البر والقحط في مدن البحر التي على الأنهار". The first sentence (unlabelled in Lisān) = Muḥkam as displayed: "والبحر: الريف، وبه فسر أبو علي قوله تعالى: (ظهر الفساد في البر والبحر) لأن البحر الذي هو الماء لا يظهر فيه فساد ولا صلاح." ✔ Same passage in Dār Ṣādir vol. 4 p. 44 ✔. Verse checked: Q 30:41 contains بَرّ and بَحْر (local API /api/verse/30:41).
  - Translation for guide: "*Al-baḥr* is also *al-rīf*, cultivated, well-watered country; that is how Abū ʿAlī explained His words 'Corruption has appeared on land and *baḥr*', because the *baḥr* that is water shows neither corruption nor soundness. Al-Azharī said: the meaning of this verse is that the land became barren and the supply of the sea was cut off because of their sins — that came about so that they would taste hardship for their sins here and now. Al-Zajjāj said: it means drought appeared on land, and dearth in the towns of the *baḥr* that lie on rivers."
  - Uncertainty: I do not identify "Abū ʿAlī" further (the entry does not; likely al-Fārisī but unsourced here). Al-Zajjāj's gloss may itself reach the Lisān through al-Azharī's *Tahdhīb* (not verifiable: the Tahdhīb is not displayed on our site and I did not check a print copy) — the guide does not claim either way.
- **Compiler's signed intervention** (excerpt): stored "قال عبدا محمد بن المكرم: شرطي في هذا الكتاب أن أذكر ما قاله مصنفو الكتب الخمسة الذين عينتهم في خطبته، لكن هذه نكتة لم يسعني إهمالها." Dār Ṣādir vol. 4 p. 42 reads "قال عبد الله محمد بن المكرم" → "عبدا" is a digitization slip in the stored text; the excerpt starts after it with "…". Then "قال السهيلي … زعم ابن سيده في كتاب المحكم أن العرب تنسب إلى البحر بحراني … وما قاله سيبويه قط …" and closes "هذا آخر ما رأيته منقولا عن السهيلي". Translation: "…Muḥammad ibn al-Mukarram [said]: My rule in this book is to set down what the authors of the five books I named in its preface said; but this is a fine point I could not let pass."
  - Visibility: the site's harmonized English condenses the Suhaylī passage (item 21: "al-Suhaylī's long correction is recorded … condensed here") and the faithful translation brackets it ("apparatus omitted"); the compiler's sentence is visible only under "Original Text". The guide says so.
- **Hadith material = Nihāya, unnamed**: Lisān bHr has no occurrence of "ابن الأثير" (checked). Passages matching the Nihāya (`nihaya` vol. 1 pp. 99–100) nearly verbatim: horse Mandūb "إني وجدته بحرا" (Nihāya: "إن وجدناه لبحرا … أي واسع الجري"); "أبى ذلك البحر ابن عباس؛ سمي بحرا لسعة علمه وكثرته" (identical gloss); "وفي حديث عبد المطلب: وحفر زمزم ثم بحرها … أي شقها ووسعها حتى لا تنزف" (identical gloss); "وفي حديث القسامة … البحرة: البلدة"; "وفي حديث عبد الله بن أبي … البحيرة: مدينة … وهي تصغير البحرة، وقد جاء في رواية مكبرا … والعرب تسمي المدن والقرى: البحار"; "وكتب لهم ببحرهم"; "ورد ذكر البحيرة في غير موضع: كانوا إذا ولدت إبلهم سقبا بحروا أذنه…"; plural بحر "جمع غريب في المؤنث … وحكى الزمخشري بحيرة وبحر وصريمة وصرم" (Nihāya identical, incl. "وحكى الزمخشري"); "وفي حديث مازن … باحر … ويروى بالجيم"; "دم بحراني … وزادوه في النسب ألفا ونونا للمبالغة"; "بحران … سرية عبد الله بن جحش". ✔ → guide: "the hadith … matches the Nihāya almost word for word, yet Ibn al-Athīr's name never appears; one line even reports what 'al-Zamakhsharī related' — a citation that is already in Ibn al-Athīr's text".
- **al-yamm (Q 28:7)**: "وقد أجمع أهل اللغة أن اليم هو البحر. وجاء في الكتاب العزيز: فألقيه في اليم؛ قال أهل التفسير: هو نيل مصر" ✔ (verse 28:7 contains "فألقيه في اليم" — local API shows أَلْقَىٰ in 28:7).
- **muwallad flag**: "الجوهري: … والأطباء يسمون التغير الذي يحدث للعليل دفعة في الأمراض الحادة: بحرانا … وجميع ذلك مولد؛ قال ابن بري عند قول الجوهري: إنه مولد…" ✔; Ṣiḥāḥ displayed has "وجميع ذلك مولد" ✔.
- Poets cited in bHr include Nuṣayb, Ibn Muqbil, Jarīr, ʿAdī ibn Zayd, al-Kumayt, al-Ṭirimmāḥ, al-Namir ibn Tawlab, al-Farazdaq, al-Muthaqqib al-ʿAbdī, al-Shammākh — guide does NOT date them (no source opened for their dates).
- Editor's note (for onOurSite): stored "(* قوله «وغور مائها وأنه إلخ» كذا بالأصل المنسوب للمؤلف وهو غير تام)"; Dār Ṣādir vol. 4 p. 44 n. 1: "قوله [وغور مائها وأنه إلخ] كذا بالأصل المنسوب للمؤلف وهو غير تام" ✔ identical.

Why chosen: Qur'anic (Q 30:41, 5:103, 28:7), shows (i) unlabelled splicing of two sources, (ii) competing explanations left side by side, (iii) a labelled verdict belonging to a source, (iv) the compiler's rare signed voice, (v) unnamed Nihāya material with a nested citation, (vi) a muwallad flag. Uncertainty stated in guide: the entry does not choose among readings.

### 5.2 صلح — SlH (comparison; seams) — chosen
Displayed in Lisān (entry 696), al-Ṣiḥāḥ (692), al-Muḥkam (697) — `python3 _dict_guide_tool.py root SlH`. Printed Dār Ṣādir vol. 2 pp. 516–517 (Shamela /1320–1321): same text, incl. the ending "والصلح: نهر بميسان"; print reads "والمصلحة واحدة المصالح" where the stored text has the slip "والمَصعلَحة".
Seams (stored texts compared):
- Lisān "الصلاح: ضد الفساد" = Ṣiḥāḥ "الصلاح: ضد الفساد" (Muḥkam has "ضد الطلاح"). ✔
- Lisān "صلح يصلح ويصلح صلاحا وصلوحا" = Muḥkam (Ṣiḥāḥ has only "صلح … يصلح صلوحا"). ✔
- Lisān "وهو صالح وصليح، الأخيرة عن ابن الأعرابي، والجمع صلحاء وصلوح؛ وصلح: كصلح، قال ابن دريد: وليس صلح بثبت" = Muḥkam. ✔
- Lisān "وربما كنوا بالصالح عن الشيء الذي هو إلى الكثرة كقول يعقوب … وكقول بعض النحويين، كأنه ابن جني" = Muḥkam ("أراه ابن جني"). ✔
- Lisān "وهذا الشيء يصلح لك أي هو من بابتك. والإصلاح: نقيض الإفساد … والاستصلاح: نقيض الاستفساد" = Ṣiḥāḥ. ✔
- Lisān "وصلاح وصلاح: من أسماء مكة، شرفها الله تعالى، يجوز أن يكون من الصلح لقوله عز وجل: حرما آمنا؛ ويجوز أن يكون من الصلاح" = Muḥkam (minus "شرفها الله تعالى"). ✔ → "almost word for word".
- Labelled sources in the entry: only "وفي التهذيب" and "قال ابن بري" (other names — Abū Zayd, Ibn al-Aʿrābī, Ibn Durayd, Yaʿqūb, Ibn Jinnī, Bishr — are cited authorities, not the Lisān's source labels). ✔
- Absent: Muḥkam's Qur'anic comments (Q "ونبيا من الصالحين" with al-Zajjāj: "الصالح: الذي يؤدي إلى الله عز وجل ما افترض عليه، ويؤدي إلى الناس حقوقهم"; "إنما نحن مصلحون"; "إنا لا نضيع أجر المصلحين"; the Iblīs/Ḥawwāʾ story) are not in the Lisān's صلح — checked in both the stored text and Dār Ṣādir pp. 516–517 (no "الصالحين", no "ونبيا"). Cause unknown (Ibn Manẓūr's Muḥkam copy vs omission; modern Muḥkam edition could differ) → guide states the absence and that the entry does not say why.
- Site English: harmonized_en item 6 says "Ibn Manẓūr suggests it may come from ṣulḥ … or from ṣalāḥ" — but the words are Ibn Sīda's (Muḥkam, displayed). Guide points this out. Also reported in siteDataIssues.
Why chosen: very common Qur'anic root; the comparison is verifiable on one root page by any reader; it demonstrates the unlabelled mosaic concretely.

### 5.3 حمد — Hmd (compiler's own voice) — chosen
Displayed (entry 61). Stored: "والحميد: من صفات الله تعالى وتقدس بمعنى المحمود على كل حال، وهو من الأسماء الحسنى فعيل بمعنى محمود؛ قال محمد بن المكرم: هذه اللفظة في الأصول فعيل بمعنى مفعول ولفظة مفعول في هذا المكان ينبو عنها طبع الإيمان، فعدلت عنها وقلت حميد بمعنى محمود، وإن كان المعنى واحدا، لكن التفاصح في التفعيل هنا لا يطابق محض التنزيه والتقديس لله عز وجل". Excerpt stops at "واحداً" (the last clause's idiom "التفاصح في التفعيل" is harder to render and not needed).
Translation: "Muḥammad ibn al-Mukarram said: In the source texts this word is [described as] 'faʿīl in the sense of mafʿūl'; but the word mafʿūl ['acted upon', the grammarians' term for the passive] is one the temper of faith shrinks from in this place, so I turned from it and said 'ḥamīd in the sense of maḥmūd [praised]', even though the meaning is the same."
"al-uṣūl" = his source texts (cf. intro p. 7 "ولم أخرج فيه عما في هذه الأصول").
Visible in site English: harmonized item 5 ("Ibn Manẓūr notes it is grammatically faʿīl-for-passive … avoided the word 'mafʿūl' …") ✔.
What it shows: (1) an admitted departure from verbatim transmission, signed; (2) the motive is theological reverence, not a lexical finding ("the meaning is the same"); (3) the sentence the reader sees before it ("faʿīl bi-maʿnā maḥmūd") is Ibn Manẓūr's re-wording, not his source's.

### 5.4 Candidates examined and rejected
- صرط SrT (306 chars): short; shows al-Azharī on the readings of ṣirāṭ with ṣād/sīn. Rejected: too thin for method; mostly readings.
- وقب wqb: compiler corrects al-Jawharī ("تجوز في اللفظ"), Q 113:3. Rejected for space; Hmd is more central (divine name, frequent root) and shows a different kind of intervention.
- علم Elm: entry opens with the divine attributes (العليم، العالم، العلام) — matches Haywood p. 82 n. 20. Not used (space).
- شكك $kk: "نقلت هذا الكلام على نصه وفي قلمي نبوة" — theological reservation about a hadith explanation; rejected as sensitive and less about language.
- عمر Emr: objection to al-Azharī's phrasing about ʿUmar — rejected (not about Qur'anic vocabulary).
- ضيع DyE: stored entry is a fragment → site-data issue, not an example.

## 6. What al-nuqta displays (onOurSite)

- 1,452 displayed roots (`_dict_guide_tool.py dicts`); status counts: 1,452 approved, 1 pending, 5 rejected/hidden.
- Stored text length 205–54,605 characters (mean ≈ 7,100). Longest: عرض ErD 54,605; shortest: سوح swH 205 (a complete short article: headword, definition, plurals, al-Jawharī's remark).
- Every displayed entry but two begins "<root>: …" (headword + colon). Exceptions: اذن A*n begins "تفسير إذ وإذا وإذن" (the Lisān's special section); ضيع DyE is a 245-character fragment beginning mid-word "لأثير في ترجمة ضيع: وفي الحديث تعين ضائعا…" — hawramani's own ضيع page has only this fragment under Lisān (checked https://arabiclexicon.hawramani.com/ضيع/ ).
- 831 of 1,452 displayed entries contain inline "(* …)" notes. These correspond to the printed edition's footnotes: e.g. bHr note = Dār Ṣādir vol. 4 p. 44 n. 1 (identical). Dār Ṣādir publisher's preface (vol. 1 p. 3): "ورأينا أن نثبت تحقيقات مصحح الطبعة الأولى الواردة في الهوامش بنصها" (they kept verbatim the first edition's corrector's notes). The first edition = Būlāq, preface by Aḥmad Fāris dated 17 Rajab 1300 (vol. 1 p. 6), which mentions finding "نسخة منسوبة للمؤلف" (a copy ascribed to the author) — the note's "كذا بالأصل المنسوب للمؤلف". Haywood p. 81 n. 15: Būlāq edition 1300–1308 AH, 20 vols. Shamela card: Dār Ṣādir footnotes include al-Yāzijī's and other linguists' notes → the guide says "editors' notes" (not specifically the Būlāq corrector for all of them).
- hawramani's Lisān page gives no edition statement ("In print the dictionary is 15 or 18 volumes, depending on the edition") ✔; root pages likewise. The stored text matched Dār Ṣādir wording in the two entries compared (بحر passage + note; صلح whole entry), apart from typing slips → guide says "in the entries we checked".
- Typing slips found: "قال عبدا محمد بن المكرم" (print: عبد الله) in bHr; "والمَصعلَحة" (print: والمصلحة) in SlH; also in bHr "المسأبة" (for المسألة?) and "وجَمْهُها" (for وجمعها?) and "أبصرب" (for أبصرت?) — the last three not checked against print → not cited in guide.
- Missing roots: 191 Qur'anic roots (of 1,643 in the morphology table) have no displayed Lisān entry, incl. Ayy, smw 381, qbl 294, wly 232, dEw 212, Hyy 184, lqy 146, slm 140, dnw, Abw, Edw, dyn 101, Slw 99, Axw, bgy, njw, swy, gny, rDw, Elw, skn, Eyn, jry, tlw, zyd, fry, nsw, zkw, qry, ndw, qdm, nsy, HfZ, qwy, blw, ftH, hwy… None of them has any Lisān row in the DB (not rejected — never scraped). Two causes found:
  1. hawramani's Lisān contents list lacks some articles entirely (سلم، قبل، دين، سكن، عين، زيد، قدم، حفظ، فتح absent from https://arabiclexicon.hawramani.com/ibn-manzur-lisan-al-arab/ contents; their root pages have no Lisān section). The printed Lisān does have them (e.g. سلم: islamweb.net Lisān text "سلم: السلام والسلامة: البراءة", search result https://www.islamweb.net/ar/library/content/122/3952/%D8%B3%D9%84%D9%85).
  2. Weak-final roots: hawramani files the Lisān article under the alif-final headword on a separate page (دعا، صلا، زكا have a Lisān section; دعو، صلو، زكو do not) — the scrape read only the و/ي spelling.
- Not displayed at all: the author's introduction, the opening chapters (disconnected letters; letters' names/properties).

## 7. Later use of the Lisān (guide)
- Lane, Preface p. xviii: Tāj al-ʿArūs — "though I believe that it was mainly derived in the first instance from the Lisán el-ʿArab"; p. xx: "in most of the articles in the former, from three-fourths to about nine-tenths of the additions to the text of the Ḳámoos, and in many articles the whole of those additions, existed verbatim in the Lisán el-ʿArab"; "This circumstance has induced me very often to compose articles of my lexicon principally from the Lisán el-ʿArab in preference to the Táj el-ʿAroos". Lane p. xvi: his copy was the 28-volume Ashrafiyya manuscript (Cairo).
- Baalbaki 2019 p. 203: "al-Zabīdī (d. 1205/1790), in spite of utilizing the Lisān as one of his major sources in Tāj al-ʿarūs, refers independently to Ibn al-Athīr's al-Nihāya…"; same page: "Ibn Manẓūr's (d. 711/1311) Lisān al-ʿArab combines five books, one of which is … Ibn al-Athīr's al-Nihāya fī gharīb al-Ḥadīth".
- Haywood p. 89 repeats Lane's finding.

## 8. Dates of the sources (guide)
Baalbaki 2019 p. 202: "Al-Azharī's (d. 370/981) Tahdhīb al-lugha"; "Ibn al-Athīr (d. 606/1210) in al-Nihāya"; "Ibn Sīda's (d. 458/1066) al-Muḥkam". p. 186 n. 1: "al-Jawharī's (d. ca. 400/1010) al-Ṣiḥāḥ and Ibn Manẓūr's (d. 711/1311) Lisān al-ʿArab". (Ibn Barrī's date not found in a consulted scholarly source → not given.)

## 9. Open questions / evidence gaps
- Baalbaki's *The Arabic Lexicographical Tradition* (2014) chapter on the Lisān and EI² "Ibn Manẓūr" not accessed.
- No source seen for the completion date of the Lisān (689/1290 is widely repeated online).
- Birthplace disputed (Cairo / Tripoli per Dār Ṣādir note; Tunis per Haywood) — unresolved; left out of the guide.
- Which printed edition hawramani digitised is not stated by hawramani; matching wording and notes point to the Būlāq→Dār Ṣādir text, checked in two entries only.
- Whether Ibn Manẓūr's hadith material always comes from the Nihāya, and his general ordering of sources inside entries, was checked only for بحر/صلح; the guide presents these as observations on those entries.
- The absence of Ibn Sīda's Qur'anic comments from the Lisān's صلح: cause unknown.
- "Abū ʿAlī" in the Q 30:41 passage is not further identified.

## 10. Additional checks made while finalising the guide

- Inline "(* …)" notes: 1,937 notes in 831 displayed entries. Openings: "قوله" ≈1,700; others "في ديوان زهير…", "وفي رواية أخرى…", "كذا بالأصل ونسخة من التهذيب", "في الصفحة السابقة…" (a cross-reference to the printed page), "لبيد في معلقته", "البيت لحسان بن ثابت…". All are editorial (variants, doubtful readings, poet identifications, cross-references) → guide: "they flag doubtful readings, give variants or name a verse's poet; they are editors' notes".
- Intro wording refined: "أجمل" (Tahdhīb) vs "أكمل" (Muḥkam) → guide says "nothing finer than … Tahdhīb … or more complete than … Muḥkam" (Haywood p. 78: "none more attractive … none more complete"). "لم يجد جمعه" → "gathered poorly".
- "Early on" (not "midway"): the signed remark in بحر sits about 2,300 characters into a 15,589-character entry (print vol. 4 p. 42 of an entry starting p. 41).
- baḥīra: guide says "a beast whose ear was slit" because the accounts vary between she-camel, ewe and male calf.
- Q 30:41 first sentence vs Muḥkam: Lisān "قوله عز وجل" / Muḥkam "قوله تعالى" → "almost word for word".
- Source URLs re-opened 2026-09-26, all HTTP 200: shamela 1687, 1687/4, 23691/97; archive.org arabiclexicograp0000hayw and anarabicenglish03lanegoog; AUB bitstream; hawramani Lisān page.
- Validator: `node scripts/validate-dictionary-guides.mjs lisan-al-arab` → ok, 0 errors; 1,101 words (lede + body, excl. excerpts); warnings only for the two deliberate `none` links (slm, Slw) in onOurSite, which the sentence explains ("have no Lisān entry on our site although the printed work treats them").

## 11. Site-data issues found (reported to orchestrator, not fixed)

1. **Missing Lisān entries for 191 Qur'anic roots** (e.g. smw, qbl, wly, dEw, Hyy, lqy, slm, dyn, Slw, zkw, HfZ, ftH). Causes: (a) hawramani's Lisān lacks some articles altogether (سلم، قبل، دين، سكن، عين، زيد، قدم، حفظ، فتح are not in its contents list); (b) for weak-final roots hawramani files the Lisān text on the alif-final headword page (دعا، صلا، زكا), which the scraper did not read (it read دعو، صلو، زكو). (b) is recoverable by scraping the alif-final pages.
2. **DyE (ضيع)**: the displayed Lisān "entry" is a 245-character fragment starting mid-word ("لأثير في ترجمة ضيع…"); it is not the Lisān article ضيع. Same fragment on hawramani's page. Consider hiding it.
3. **Harmonized English misattribution (SlH)**: item 6 says "Ibn Manẓūr suggests it may come from ṣulḥ … or from ṣalāḥ"; the sentence is Ibn Sīda's (al-Muḥkam, displayed on the same page). Likely a systematic tendency of the English renderings to credit unlabelled source text to "Ibn Manẓūr".
4. **Typing slips in stored text** (inherited from hawramani): "قال عبدا محمد بن المكرم" (print عبد الله) in bHr; "والمَصعلَحة" (print والمصلحة) in SlH.
5. Stored date 1311: acceptable (death Shaʿbān 711 = 13 Dec 1311 – 10 Jan 1312 Julian); no change needed. Author label "Ibn Manẓūr" correct.
6. hawramani's blurb dates the *Nihāya*'s author as "Ibn al-Athīr (d. 1233 CE / 630 H)" — that is the historian ʿIzz al-Dīn; the *Nihāya* is by Majd al-Dīn (d. 606/1210). Not on our site, but worth knowing if the blurb is ever reused.

## 12. Revision round 1 (2026-09-26): additional checks by the reviser

- **Baalbaki 2019 n. 84**: re-read in the AUB PDF (the page headed 203 is PDF p. 19). Full note: "Note also that among the works cited by Ibn Manẓūr — obviously on the authority of his five sources — are several works on gharīb al-Ḥadīth, only one on gharīb al-Qurʾān, and one which combines both types; see the indices of Abū l-Hayjāʾ and ʿAmāyira, Fahāris Lisān al-ʿArab, II, 385-386." The phrase applies to *works cited*. The guide now uses it that way (C30).
- **Intro p. 7** (Shamela 1687/7, label "ج1 - ص7"): "ولم أخرج فيه عما في هذه الأصول، ورتبته ترتيب [الصحاح] في الأبواب والفصول". This supports "by his own account he kept within his five books".
- **Signature count**: `grep ibn-manzur-lisan-al-arab 'المكرم'` gives 33 hits. Removing the المكرم "honoured" false hits (Ebd, qrb, Hbb, krm, Avr, Ewn, Dyf, wfd, dss) leaves **24** signed entries: the 21 listed in §4 plus Amm ("محمد ابن المكرم"), Trq ("ابن المكرم") and fyA ("عبدالله بن المكرم"). Variants inside the 21: bHr "عبدا محمد", fqr and jdd "عبد الله محمد". Signed departures from the five sources: bHr (al-Suhaylī), brd (Ibn Khallikān), dwr and sll (marginal notes "حاشية … في بعض الأصول").
- **Durar/Bughya**: both notices are complete on vol. 1 p. 4 (Shamela 1687/4), each ending "مات في شعبان سنة ٧١١". Vol. 1 p. 5 begins "مقدمة الطبعة الأولى". The locator is corrected to p. 4.
- **Dār Ṣādir notes**: Shamela card "الحواشي: لليازجي وجماعة من اللغويين". Publisher's preface p. 3: kept "تحقيقات مصحح الطبعة الأولى الواردة في الهوامش بنصها" and corrected errors "مستعينين بنخبة من علماء اللغة المتخصصين".
- **Haywood open copy**: https://archive.org/details/in.gov.ignca.12555. Per the metadata API: "Arabic lexicography", Haywood, John A., 1960, not access-restricted. The djvu text is downloadable. Passages located by running heads: p. 71 "final radicals in the first instance"; p. 78 "Tripoli for some time"; p. 80 "retained al-Jauhari's arrangement as being the handiest"; p. 81 "where two of them disagree, he tends merely to repeat what both have said" plus the Būlāq-edition footnote. The guide now links this copy.
- **SlH labels re-checked** (entry 696): التهذيب ×1, ابن بري ×2; الجوهري, ابن سيده, المحكم, الصحاح, ابن الأثير, النهاية ×0 → "of his five sources, only the *Tahdhīb* and Ibn Barrī are named".

## 13. Revision round 2 (2026-09-26): additional checks by the reviser

- **Unsigned al-Suhaylī in جمع (jmE).** Displayed entry (`_dict_guide_tool.py entry jmE ibn-manzur-lisan-al-arab`): "وزعم ثعلب أَن أَوّل من سماه به كعبُ بن لؤيّ … وذكر السهيلي في الرَّوْض الأُنُف أَنَّ كعب بن لؤيّ أَوّلُ من جَمَّع يوم العَرُوبةِ، ولم تسمَّ العَروبةُ الجُمعة إِلا مُذ جاء الإِسلام …". No "قال محمد بن المكرم" and no closing formula around it. Print check: Shamela 1687/3906, page selector "ج: 8", `data-page-num` 58 = Dār Ṣādir vol. 8 p. 58, same wording ("وَذَكَرَ السُّهَيْلِيُّ فِي الرَّوْض الأُنُف أَنَّ كَعْبَ بْنَ لُؤَيٍّ أَوّلُ مَنْ جَمَّع يَوْمَ العَرُوبةِ …"), so the lack of a signature is not a digitisation artefact. The site's English rendering also carries it ("al-Suhaylī (in al-Rawḍ al-Unuf): Kaʿb was the first to 'gather' …").
- **Route not established.** Verifier r2 found the passage absent from the Nihāya's جمع article (vol. 1 pp. 295–296). I did not re-check that and do not use it in the guide. As I recall, al-Suhaylī (d. 581) and Ibn Barrī (d. 582) were contemporaries. I have not checked those dates in a source, and the guide does not use them. If they are right, a route through Ibn Barrī's notes cannot be ruled out from what I have seen. The guide therefore says only that the quotation is unsigned and that the entry does not say how it arrived. It does not say that Ibn Manẓūr added it himself.
- **Haywood p. 81 n. 15.** The djvu OCR is garbled here ("The Baliii Edition of 1306^1303 A.H, is in 20 vols."). The verifier read "1300-1308" from the page image. I moved the existing citation and did not re-read the image.
