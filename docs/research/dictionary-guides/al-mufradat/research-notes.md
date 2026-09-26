# al-Mufradāt (al-Rāghib al-Iṣfahānī) — research notes

Guide: `roots/frontend/src/content/dictionary-guides/guides/al-mufradat.ts`
Site dictionary slug: `al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran`
Prepared 2026-09-26. Every claim in the guide is listed below with its source and the
passage that supports it. Translations of Arabic are my own unless stated.

---

## 0. Sources actually opened

| id in guide | source | URL opened | how accessed |
|---|---|---|---|
| `raghib-intro` | al-Rāghib's own introduction (*muqaddimat al-muʾallif*), Dāwūdī ed. pp. 53–56 | https://shamela.ws/book/23636/35 … /38 (cited URL: /36) | curl; Shamela card says "ترقيم الكتاب موافق للمطبوع" (pagination matches print) |
| `dawudi` | Ṣafwān ʿAdnān Dāwūdī, editor's introduction to the same edition, pp. 5–38 | https://shamela.ws/book/23636/1 (pp. 5–38 = Shamela pages 1–34) | curl |
| `iranica` | G. J. van Gelder, "RĀḠEB EṢFAHĀNI", *Encyclopaedia Iranica* (pub. 1 Jan 2000, updated 8 Nov 2012) | https://www.iranicaonline.org/articles/rageb-esfahani/ | browser pane (curl blocked by Cloudflare) — full text read |
| `key` | Alexander Key, *Language Between God and the Poets: Maʿnā in the Eleventh Century* (University of California Press, 2018; open access, DOI 10.1525/luminos.54) | https://www.academia.edu/40442079/Language_Between_God_and_the_Poets | browser pane; full text rendered on the page with page markers (luminosoa.org returned 403) |
| `zarkashi-gharib` | al-Zarkashī, *al-Burhān fī ʿulūm al-Qurʾān*, ch. 18 "maʿrifat gharībih" | https://www.islamweb.net/ar/library/content/67/120/ (full URL in guide) | curl |
| `zarkashi-tafsir` | al-Zarkashī, *al-Burhān*, section on tafsīr (two kinds of Qur'anic passage) | https://www.islamicbook.ws/qbook/alom/albrhan-004.html | curl |
| `hawramani` | arabiclexicon.hawramani.com, the al-Mufradāt dictionary page | https://arabiclexicon.hawramani.com/al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran/ | curl |

Leads only (not cited): en.wikipedia "Al-Raghib al-Isfahani", "Al-Mufradat fi Gharib al-Quran" (surfaced in search; not relied on).
Not accessible: Baalbaki, *The Arabic Lexicographical Tradition* (2014) — no open copy found (academia.edu item is not the full text; Google Books API quota exhausted). EI² "al-Rāghib al-Iṣfahānī" (Rowson) — paywalled, not seen. Madelung 1974, al-Jawharjī 1986, Key's 2012 dissertation — known only through van Gelder, Dāwūdī and Key; not cited directly.

---

## 1. What al-nuqta displays (tool output, 2026-09-26)

- `dicts`: `al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran` — title "al-Mufradāt fī Gharīb al-Qurʾān", المفردات في غريب القرآن, author "al-Rāghib al-Iṣfahānī", **site date 1109**, lang ar, **1,267 displayed entries**. All 1,267 rows in `dictionary_entries` for this slug are approved/visible.
- API `/api/root/kfr/dictionaries` returns `author_death_year: 1109`, `is_quran_specific: true`.
- Entries by first letter (my count): ا46 ب68 ت13 ث16 ج50 ح72 خ58 د32 ذ14 ر72 ز23 س82 ش50 ص47 ض16 ط31 ظ6 ع82 غ35 ف61 ق65 ك43 ل39 م50 ن93 ه27 و68 ي8 — every letter present.
- Lengths: mean ≈ 886 characters; shortest ذعن (61 chars: "مُذْعِنِينَ أي: منقادين، يقال: ناقة مِذْعَان، أي: منقادة."), longest هدى (10,976 chars), كتب, قوم, سوا, كفر (6,600), كبر …
- Recurring features (my regex counts over the 1,267 stored originals, vowel marks stripped):
  - bracketed verse reference of the form `[السورة/ n]`: **1,250 / 1,267** entries
  - `قيل` ("it has been said"): 646 entries
  - `أصل` (origin): 308
  - borrowing vocabulary (استعير / مستعار / يستعار / استعارة): 179
  - `قال الشاعر`: 182
  - `روي` / `الحديث`: 170
  - `متعارف` (customary/established usage): 18 (e.g. kfr, kbr "والكبيرة متعارفة في كل ذنب تعظم عقوبته", byt "صار أهل البيت متعارفا في آل النبي")
  - "in the sharīʿa / in the Law" markers (في الشرع / في الشريعة): 18 entries (sjd, Swm, twb, slm, rbw, srq, Ekf, Ewd, Emr …)
- Later dictionaries on our site that quote him by name (tool `grep`):
  - Tāj al-ʿArūs (`murtada-al-zabidi-…`): regex `(قال|وقال|ذكره|قاله) (الإمام )?الراغب` → **282 displayed entries**; `الراغب في المفردات|مفردات الراغب` → 26 (e.g. ذكر: "وقال الراغب في المفردات، وتبعه المصنف في البصائر").
  - Lane (`william-edward-lane-arabic-english-lexicon`): `Er-R[aá]ghib` → **265 displayed entries**; sample امن "( Er-Rághib , TA .)" i.e. often via the Tāj.
  - Lisān al-ʿArab, Tuḥfat al-Arīb, al-Miṣbāḥ, al-Qāmūs: no named citations in displayed text (Lisān's one hit is the ordinary word الراغب).

### 1a. Which printed text the stored copy represents
- hawramani's dictionary page gives no edition/source statement. Its text: "The Mufradāt of al-Isfahānī is perhaps the most widely used dictionary of the Quran … (d. c. 1109 CE / 502 AH) … Not much is known about al-Isfahānī, not even his proper first name." (No source named.) → cited as `hawramani` only for "does not name its source".
- I compared three stored entries word for word with Shamela book 23636, whose card reads: "المحقق: صفوان عدنان الداودي — الناشر: دار القلم، الدار الشامية - دمشق بيروت — الطبعة: الأولى - ١٤١٢ هـ [ترقيم الكتاب موافق للمطبوع] — عدد الصفحات: ٩٠١".
  - كفر (Shamela p. 714): identical wording, same vowelling (الكُفْرُ … بِالْكَافِرِ …), same bracketed refs `[الأنبياء/ ٩٤]`; Shamela adds poem numbers "٣٨٧-", "٣٨٨-" and footnotes (poet = Thaʿlaba b. Ṣuʿayr al-Māzinī; rajaz of al-ʿAjjāj) that are absent from ours.
  - سرح (Shamela p. 406): identical.
  - حمد (Shamela p. 256): identical; our text has "محمودا ، وقوله" where Shamela has "محمودا «٢» ، وقوله" — the stray space before the comma is where the footnote marker was removed.
  - فجج (Shamela p. 626-ish, page 607-610 range): Shamela continues "وجمعه فِجَاجٌ. قال: مِنْ كُلِّ فَجٍّ عَمِيقٍ [الحج/ ٢٧] …" — **our copy stops at "وجمعه"** (truncated).
  - Key cites the same edition's pages for entries he discusses (e.g. sarḥ at "1992, 406") — consistent with Shamela p. 406.
  - Conclusion stated in guide as observation, not as a source statement: "matches, in the entries we compared, Dāwūdī's edition … without the editor's footnotes".
- Dāwūdī p. 5 (editor's method, item 3): "تخريج الآيات القرآنية، وذكر أرقامها وسورها. وجعلناها في المتن تخفيفاً للحواشي" = he identified the Qur'anic verses, gave their numbers and suras, "and put them in the main text to lighten the footnotes" → the `[sura/ n]` brackets in our text are the editor's.
- Edition date: Shamela card "الأولى - ١٤١٢ هـ" (1991–92); Key's bibliography "1992. Mufradāt Alfāẓ al-Qurʾān al-Karīm. Ed. Ṣafwān ʿAdnān Dāwūdī. Beirut/Damascus: Dār al-Qalam / Dār aš-Šāmīyah"; van Gelder's bibliography "Mofradāt alfāẓ al-Qorʾān, ed. Ṣafwān ʿAdnān Dāwudi, Damascus and Beirut, 1997" (probably a later printing). Title on the Shamela card is المفردات في غريب القرآن; Key and van Gelder give the title as *Mufradāt alfāẓ al-Qurʾān*. Guide cites "1412/1992" per the Shamela card + Key.
- Dāwūdī signed his introduction "المدينة المنورة - شعبان ١٤٠٨ هـ" (p. 6).

### 1b. Gaps and artifacts in our copy (for onOurSite / siteDataIssues)
- 376 roots in our morphology table have no al-Mufradāt entry on the site (1,643 roots total). Some are genuine omissions of the book (Dāwūdī p. 28, quoting al-Samīn al-Ḥalabī: غوط، زبن، قريش، كلح، قدو، نضخ; and himself: فني، خردل).
- **But many common roots are missing only because of how the source site files them.** hawramani's table of contents for al-Mufradāt lists headwords such as حق، رب، حب، جن، ضل، صلا، زكا، دعا، سما، دنا، كان; hawramani's page for حق and رب and صلا each contain an al-Mufradāt entry (checked: `https://arabiclexicon.hawramani.com/حق/` has "al-Mufradāt fī Gharīb" 1×, `/رب/` 1×, `/صلا/` 1×; `/حقق/`, `/ربب/`, `/صلو/` 0×). Our roots Hqq, rbb, Hbb, jnn, Dll, Slw, zkw, dEw, smw, dnw, kwn show no al-Mufradāt entry. Dāwūdī's text has the حق entry at p. 246 ("أصل الحَقّ: المطابقة والموافقة …").
- **Mis-mapping:** our root `swA` is س و ء (lemmas suw', sayyi'a, sawʾ — "evil"). The al-Mufradāt entry displayed there (entry id from source_url `…/سوا/#d4a4b7c4…`) begins "سوا الْمُسَاوَاةُ: المعادلة المعتبرة بالذّرع والوزن…" — his article on *equality* (root س و ي). His سوأ (evil) article (in hawramani's contents as سوأ) is not displayed; root `swy` has no al-Mufradāt entry. `root_arabic` stored for swA is "سوا". The same mapping appears for other dictionaries on swA (Kitāb al-ʿAyn, Lisān … all labelled سوا) — outside this guide's scope, reported.
- Truncation: فجج ends "وجمعه" (see above). يوم runs on into the following يس article ("… يس يس قيل معناه يا إنسان، والصحيح أنّ يس هو من حروف التّهجّي …,"). نأى ends with the chapter markers "تمّ كتاب النون كتاب الهاء". ربح keeps an editor's poem number "177-".
- Line breaks of the print (poetry on separate lines) are flattened: half-lines of verse run on into prose (e.g. كفر "… لمّا سمع: ألقت ذكاء يمينها في كافر والْكَافُورُ …").
- Each stored entry begins with the book's headword (e.g. "هدى الهداية دلالة بلطف …"; hawramani puts the headword above the entry).

---

## 2. Author, date, title — claims and support

**C1. Almost nothing is known of his life.**
- van Gelder (`iranica`): "Next to nothing is known about his life, since he is hardly mentioned in major biographical dictionaries … neither do his own works … offer significant clues about him."
- Dāwūdī p. 7: sources say nothing of his teachers or students ("لم تذكر المصادر المتوفرة بأيدينا شيئاً عمّن تلقّى عنه الراغب علومه …").

**C2. Name.** van Gelder: "Abul’l-Qāsem Ḥosayn b. Moḥammad b Mofażżal"; Key p. 11: "Abū al-Qāsim al-Ḥusayn b. Muḥammad b. al-Mufaḍḍal ar-Rāġib al-Iṣfahānī"; the book itself (Dāwūdī p. 53): "قال الشيخ أبو القاسم الحسين بن محمد بن المفضل الراغب". Dāwūdī p. 7: name disputed because he was known by his laqab; "الأشهر أنّ اسمه الحسين" (variants: al-Ḥusayn b. Mufaḍḍal b. Muḥammad; al-Ḥusayn b. al-Faḍl; al-Mufaḍḍal b. Muḥammad [Suyūṭī]). → guide `authorFull`.

**C3. Isfahan by nisba; place of work unknown.** van Gelder: "One may assume on the evidence of Rāḡeb’s nesba that he was born in Isfahan. It is said, again without any supporting evidence, that he lived in Baghdad … it is not known if he was active elsewhere."

**C4. Death date disputed; 502/1108 lacks evidence; early 5th/11th c.**
- van Gelder: headword "(d. early 5th/11th cent.)"; "It is often stated, without any clear evidence, that he died in 502/1108 (e.g., Ḥāji Ḵalifa …) … but Wilferd Madelung’s study has confirmed that Rāḡeb lived 'in the first part of the fifth century' (Soyuṭi, II, p. 297). Nevertheless, the later date still persists in many modern publications." Evidence: verses in his *Muḥāḍarāt* addressed to Abū l-Qāsim b. Abī l-ʿAlāʾ, identified by Madelung as a poet of the circle of al-Ṣāḥib b. ʿAbbād (d. 385/995); the anthology quotes that period and circle, later poets (e.g. al-Maʿarrī) absent.
- Key p. 11: "From the twelfth to the twentieth century, notices … have provided a variety of incorrect death dates … it is only through recent research (including my own) that we have been able to ascertain from the oldest manuscript witness to his Quranic glossary that ar-Rāġib was alive in or before 1018." fn 11 → ms "409/1018. Mufradāt Ġarīb al-Qurʾān al-Karīm … Library of Muḥammad Luṭfī al-Ḫaṭīb, London. [Private collection.]" (bibliography p. 263). Key (chapter 1, "Contexts"; page not pinned, NOT cited with a page): "the glossary of the Quran written by ar-Rāġib at the start of the 1000s". Key p. 90: "ar-Rāġib’s Quranic glossary, or the dictionary of his contemporary Ibn Fāris" (page marker "90 The Lexicon" verified).
- Dāwūdī pp. 37–38: lists the disagreement — Suyūṭī: early 5th century; Dhahabī placed him in the 42nd ṭabaqa (deaths 440–470); Ḥājjī Khalīfa 502 (followed by Brockelmann); Hadiyyat al-ʿārifīn 500; Taymūriyya catalogue 503; Ziriklī and Kaḥḥāla 502; Kurd ʿAlī 402 and later 503; MMIA 452. ʿAdnān al-Jawharjī reported a rare manuscript of the Mufradāt in the library of Muḥammad Luṭfī al-Khaṭīb **in Damascus** (Key says London), copied in 409 AH, with a marginal note (in the hand of an "Abū l-Saʿādāt") saying it is in al-Rāghib's hand, born Rajab 343, died 412. Dāwūdī concludes: "إن الأرجح أنّ وفاته في حوالي سنة ٤٢٥ هـ" (most likely c. 425 AH ≈ 1033–34 CE), arguing from his quotations of al-Jabbān's *al-Shāmil* (taught in Isfahan in 416), al-Sharīf al-Raḍī (d. 406), Miskawayh (d. 421) etc.
- Discrepancy recorded: manuscript location Damascus (Dāwūdī, reporting al-Jawharjī 1986) vs London (Key's bibliography). Not in guide.
- **Guide wording:** later works often give 502/1108, repeated without clear evidence (van Gelder); modern scholarship places him in the early 5th/11th c. (van Gelder, Madelung via van Gelder); Key: oldest ms dated 409/1018, so alive/active by 1018; Dāwūdī: c. 425/1034. "Either way" → early 11th century, roughly contemporary with Ibn Fāris (Key p. 90 calls Ibn Fāris "his contemporary").
- → **siteDataIssue**: stored `author_death_year` 1109 (= 502 AH) is the doubted date; places him after Ibn Sīda (1066) in the panel.

**C5. Title variants.** van Gelder: "The first, more often entitled Mofradāt alfāẓ al-Qorʾān, is a very useful alphabetical dictionary of Qorʾanic Arabic"; bibliography: *al-Mofradāt fi ḡarib al-Qorʾān*, ed. Kaylānī (Cairo 1961), ed. Khalaf-Allāh (Cairo 1970); *Mofradāt alfāẓ al-Qorʾān*, ed. Dāwūdī. The introduction (p. 55) describes the book as "كتاب مستوف فيه مفردات ألفاظ القرآن".

**C6. His other interests: ethics, exegesis, theology, anthology; approach "invariably linguistic".** van Gelder: "scholar, littérateur, and author of works on Islamic ethics, Qurʾanic exegesis, Islamic theology, and Arabic philology, as well as anthologies." Key p. 11: "a thinker whose approach to problems of theology, ethics, politics, and poetry was invariably linguistic." Used in paraphrase.

**C7. His own mix of positions seeps into the glossary.** Key p. 13: "Ar-Rāġib then allowed this combination to seep, however subtly, into his glossary of the Quran" (combination = traditionist piety, "Sufism", Aristotelian/Neoplatonic ethics; his own label "traditionists, senior sufis, and wise philosophers"). van Gelder: Suyūṭī thought him a Muʿtazilite until he found Fakhr al-Dīn al-Rāzī pairing him with al-Ghazālī as a Sunni authority. Dāwūdī p. 27: sees Muʿtazilī influence in places (e.g. زمل) and suspects Abū Muslim al-Iṣfahānī's tafsīr as the channel. → Guide quotes Key's "however subtly" (4 words) and paraphrases the rest.

---

## 3. Purpose, audience, arrangement — the author's introduction (Dāwūdī ed. pp. 53–56)

**C8. Words first; the brick simile.** p. 54: "وذكرت أنّ أول ما يحتاج أن يشتغل به من علوم القرآن العلوم اللفظية، ومن العلوم اللفظية تحقيق الألفاظ المفردة، فتحصيل معاني مفردات ألفاظ القرآن في كونه من أوائل المعاون لمن يريد أن يدرك معانيه، كتحصيل اللّبن في كونه من أول المعاون في بناء ما يريد أن يبنيه، وليس ذلك نافعا في علم القرآن فقط، بل هو نافع في كلّ علم من علوم الشرع".
My translation: "I have mentioned that the first of the Qur'anic sciences one needs to take up is the verbal sciences, and among the verbal sciences the precise determination of single words. So acquiring the meanings of the single words of the Qur'an is among the first aids for anyone who wants to grasp its meanings, as acquiring bricks is among the first aids for building what one wants to build. And that is useful not only in the study of the Qur'an but in every one of the sciences of the religious Law."
- اللّبن here = *labin*, unfired (mud) bricks — required by "بناء" (building). (A search-engine summary rendered it "milk" — wrong.)
- Zarkashī reproduces the same sentence, unattributed, in *al-Burhān* ("فتحصيل معاني المفردات من ألفاظ القرآن من أوائل المعادن لمن يريد أن يدرك معانيه وهو كتحصيل اللبن …", islamicbook.ws p. 004) — not used in guide.
- "وذكرت" = he had said this earlier (in *al-Risāla al-munabbiha ʿalā fawāʾid al-Qurʾān* / *al-Dharīʿa*, pp. 53–54) — the Mufradāt is the first step of a programme. Not in guide beyond "states his purpose".

**C9. Qur'an's words as the core of Arabic.** p. 55: "فألفاظ القرآن هي لبّ كلام العرب وزبدته، وواسطته وكرائمه، وعليها اعتماد الفقهاء والحكماء في أحكامهم وحكمهم، وإليها مفزع حذّاق الشعراء والبلغاء …" (the Qur'an's words are the kernel and cream of the Arabs' speech; jurists and sages rely on them; skilled poets and orators resort to them). Used only lightly (not quoted) — possibly omitted for length.

**C10. Plan and arrangement.** p. 55: "وقد استخرت الله تعالى في إملاء كتاب مستوف فيه مفردات ألفاظ القرآن على حروف التهجي، فنقدّم ما أوله الألف، ثم الباء على ترتيب حروف المعجم، معتبرا فيه أوائل حروفه الأصلية دون الزوائد، والإشارة فيه إلى المناسبات التي بين الألفاظ المستعارات منها والمشتقات حسبما يحتمل التوسع في هذا الكتاب، وأحيل بالقوانين الدالة على تحقيق مناسبات الألفاظ على «الرسالة» التي عملتها مختصّة بهذا الباب."
Translation: "I have sought God's guidance in dictating a book that covers the single words of the Qur'an in alphabetical order — putting first what begins with alif, then bāʾ, in the order of the letters — taking account of their first root letters, not the added ones; and pointing out in it the relations (*munāsabāt*) between words, those borrowed and those derived, as far as the scope of this book allows; for the rules that establish these relations I refer [the reader] to the treatise I wrote specifically on that subject." (Dāwūdī fn: the treatise is *Taḥqīq munāsabāt al-alfāẓ*.)
- Dāwūdī p. 28 (remark 9): he did not observe the order of the third letter (e.g. أبا before أبّ) — not used.

**C11. Planned sequel on near-synonyms; the ḥamd/shukr complaint.** pp. 55–56: "وأتبع هذا الكتاب- إن شاء الله تعالى ونسأ في الأجل- بكتاب ينبئ عن تحقيق «الألفاظ المترادفة على المعنى الواحد، وما بينها من الفروق الغامضة» ، فبذلك يعرف اختصاص كل خبر بلفظ من الألفاظ المترادفة دون غيره من أخواته، نحو ذكر القلب مرّة والفؤاد مرة والصدر مرّة، … ونحو ذلك ممّا يعدّه من لا يحقّ الحقّ ويبطل الباطل أنّه باب واحد، فيقدّر أنه إذا فسّر: الْحَمْدُ لِلَّهِ بقوله: الشكر لله، و لا رَيْبَ فِيهِ ب: لا شك فيه، فقد فسّر القرآن ووفّاه التبيان."
Translation (sense): he will follow this book, God willing, with one on words that are synonymous for a single meaning "and the subtle differences between them", showing why a statement uses one of the synonyms and not its sisters — e.g. *qalb* (heart) in one place, *fuʾād* in another, *ṣadr* in another; and the different verse-endings "for people who believe / reflect / know / understand …" — things that someone who does not establish truth from falsehood counts as one category, supposing that if he glosses *al-ḥamdu li-llāh* as *al-shukru li-llāh* and *lā rayba fīhi* as *lā shakka fīhi*, he has explained the Qur'an and given it its full due.
- Dāwūdī p. 55 fn 2: "لم نجد هذا الكتاب" (we did not find this book).
- van Gelder: cites Zarkashī's praise for fine nuances; the examples he gives (qalb vs ṣadr; "mouth" with speaking implies lying) — the فوه entry on our site has: "وكل موضع علق الله تعالى حكم القول بالفم فإشارة إلى الكذب، وتنبيه أن الاعتقاد لا يطابقه" (not used in guide).

**C12. Audience.** Only what the introduction states: "anyone who wants to grasp [the Qur'an's] meanings" and useful to "every one of the sciences of the religious Law". No further claim about audience made.

---

## 4. Method and evidence — claims and support

**C13. Pattern: literal sense → derivatives → figurative senses and their link.** Dāwūdī p. 19: "فنجده أولا يذكر المادة بمعناها الحقيقي، ثم يتبعها بما اشتقّ منها، ثم يذكر المعاني المجازية للمادة، ويبيّن مدى ارتباطها بالمعنى الحقيقي" — the editor's characterisation, illustrated by إبل، بور، خبت، مرد. Evidence cited "from the Qur'an first, then hadith, then Arab poetry and sayings"; "he explains the Qur'an by the Qur'an a great deal". Used as the editor's view.

**C14. Borrowing (istiʿāra) as his account of change; herding metaphors.** Key p. 107: "Ar-Rāġib remarked on this process of language evolution at multiple points in his Quranic glossary, using the word for 'metaphor' (istiʿārah …). His dictionary sought to read God as having taken phrases from a nomadic lifestyle and turned them into language for a new community." Examples: rawāḥ (Dāwūdī p. 371), midrār (p. 310), sarḥ/tasrīḥ (p. 406: "وقوله: وسرّحوهنّ سراحاً جميلاً مستعار من تسريح الإبل، كالطّلاق في كونه مستعارا من إطلاق الإبل"). Guide paraphrases "a herding way of life" with [^key|p. 107]. My count: 179 of 1,267 entries use borrowing vocabulary (not used in guide).
Key p. 106–107 also quotes al-Rāghib's *Muqaddimat jāmiʿ al-tafāsīr* (1984, p. 33) that specialists transfer words to new meanings, with revelation words such as *ṣalāt* and *zakāt* as examples — **not used** (from a different work; could be added if wanted).

**C15. Zarkashī: meanings from context.**
- `zarkashi-gharib` (islamweb, ch. 18, marked [ص: 393–394] in that edition): "ومن أحسنها كتاب " المفردات " للراغب . وهو يتصيد المعاني من السياق ; لأن مدلولات الألفاظ خاصة" — "…and he hunts out meanings from the context, because the significations of words are specific." The "من أحسنها" ranking is **deliberately omitted** from the guide (house rule: no ranking).
- `zarkashi-tafsir` (islamicbook.ws 004): "الثاني: ما لم يرد فيه نقل عن المفسرين وهو قليل وطريق التوصل إلى فهمه النظر إلى مفردات الألفاظ من لغة العرب ومدلولاتها واستعمالها بحسب السياق وهذا يعتني به الراغب كثيرا في كتاب المفردات فيذكر قيدا زائدا على أهل اللغة في تفسير مدلول اللفظ لأنه اقتنصه من السياق".
My translation of the last clause: "…al-Rāghib attends to this a great deal in the Mufradāt: he adds a qualification beyond [what] the philologists [give] in explaining a word's meaning, because he has caught it from the context."
- Zarkashī's dates: d. 794/1392 (van Gelder). Guide says "fourteenth-century".
- My interpretive caution in the guide (labelled as such by phrasing "That is also what to watch"): a qualification caught from Qur'anic context is a reading of that context, not independent outside evidence. This is my interpretation, not Zarkashī's.

**C16. Poetry sparse; poets unnamed.** Dāwūdī p. 25: al-Zamakhsharī's *Asās* "يمتاز بكثرة الشواهد الشعرية التي يزيد عددها على ٦٠٠٠ بيت، بينما كتاب الراغب لا يتجاوز ٥٠٠ بيت" → guide: "fewer than 500 lines of verse in the whole book" (no comparison with Asās, to avoid ranking). On our site: "قال الشاعر" in 182 entries; attributions are in Dāwūdī's footnotes (e.g. كفر fn: Thaʿlaba b. Ṣuʿayr; al-ʿAjjāj), which our copy lacks.

**C17. Readings and hadith: editor's warnings.** Dāwūdī p. 26: (1) "أنه لم يميّز بين القراءات المتواترة والشاذة، بل يكتفي أن يقول: وقرئ كذا"; (2) "قلّة بضاعته في علم الحديث الشريف … نسبته بعض الأقوال إلى الرسول، وليست هي من قوله" (e.g. جبر "لا جبر ولا تفويض" — words of theologians, not the Prophet), and some fabricated hadith (ورث). p. 27: misattributions of scholars' views (روى: Abū ʿAlī; فتن: al-Akhfash/al-Farrāʾ swapped). → Guide: "he cites variant readings with a bare *wa-quriʾa* … without saying which are accepted or irregular, and some sayings he attributes to the Prophet are not hadith."

**C18. Sources used silently; Ibn Fāris's al-Mujmal.** Dāwūdī p. 21: "اعتمد الراغب على مؤلّفات العلماء قبله، فبحث فيها، وناقش أصحابها، وارتضى أقوالا، وردّ أخرى"; first: "كتاب «المجمل في اللغة» لابن فارس. ويبدو أنّ الراغب قد اعتمد عليه كثيرا، مع أنه لم يذكره باسمه، ويتضح ذلك من نفس ترتيب الكتاب، والتشابه الكبير في العبارة، وربما ينقل عنه حرفيا، والموافقة في الأبيات الشعرية" (examples أبّ، أسّ، جنف، خصف، ركز، سجل، صفد; "except that al-Rāghib abridged and reduced the verses"). Also named/traced: al-Jabbān's *al-Shāmil* (named in دلى), Ibn al-Sikkīt, Abū ʿAlī al-Fārisī, al-Farrāʾ, Ibn Durayd, al-Zajjāj, al-Khalīl's *ʿAyn* (named in مكّ، قول، ظلم، ضعف، أوّل), Abū Muslim al-Iṣfahānī, Abū ʿUbayda, al-Akhfash, Ibn Qutayba, Sībawayh, Abū ʿUbayd, Thaʿlab (pp. 21–23). "يبدو" = "it appears" → guide says Dāwūdī "argues" / "traces".
- Note: the *Mujmal* is not the *Maqāyīs* displayed on al-nuqta; guide says so explicitly.
- van Gelder on al-Dharīʿa: "he virtually never quotes or refers to earlier authors" — about the Dharīʿa, NOT the Mufradāt; not transferred.

**C19. Later users.** Dāwūdī p. 24: Fīrūzābādī "عكف على كتاب الراغب، واختصره، وزاد فيه أشياء" in *Baṣāʾir dhawī al-tamyīz*, often copying whole passages; al-Samīn al-Ḥalabī "جعل كتاب الراغب لبّ كتابه" in *ʿUmdat al-ḥuffāẓ*; also Zarkashī, Suyūṭī, al-Rāzī's tafsīr, al-Baghdādī, **al-Zabīdī in Tāj al-ʿArūs** (رجع، ربع، أبد، أمد، عود), Ibn Ḥajar, al-Ālūsī. On-site counts (sect. 1) confirm Tāj and Lane quote him. Tāj's ذكر entry: "وقال الراغب في المفردات، وتبعه المصنف في البصائر" (Zabīdī himself notes Fīrūzābādī followed him in the Baṣāʾir).
- Dāwūdī p. 25 also suggests ("لعلّ") al-Zamakhsharī's *Asās al-Balāgha* followed al-Rāghib's literal→figurative approach — **not used** (hedged editor's suggestion; comparative).

**C20. Text stable.** Key p. 12: "Today, almost every Arabic library in the world has a copy of ar-Rāġib’s glossary of the Quran, and the text is virtually unchanged from its earliest manuscript witness." → not used in guide (kept for notes).

---

## 5. Root examples examined

Selection criteria: displayed on site (tool `entry`), shows method clearly, matters to a Qur'an reader, and what I say is visible in the stored original AND in the site's English renderings.

### CHOSEN 1 — كفر `kfr` (close reading) — entry_id 157, Dāwūdī pp. 714–716
Stored original (key sentences, in order):
1. "الكُفْرُ في اللّغة: ستر الشيء، ووصف الليل بِالْكَافِرِ لستره الأشخاص، والزّرّاع لستره البذر في الأرض، وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع: ألقت ذكاء يمينها في كافر"
   → covering; night and sower "described" as kāfir; "that is not a name for them, as some philologists said on hearing [the half-line] 'the sun cast its right hand into a kāfir'". (He rejects treating kāfir as a lexicalised name for night etc.)
2. "وكُفْرُ النّعمة وكُفْرَانُهَا: سترها بترك أداء شكرها، قال تعالى: فَلا كُفْرانَ لِسَعْيِهِ [الأنبياء/ 94]" — ingratitude = covering a blessing by not giving thanks (Q 21:94).
3. "وأعظم الكُفْرِ: جحود الوحدانيّة أو الشريعة أو النّبوّة، والكُفْرَانُ في جحود النّعمة أكثر استعمالا، والكُفْرُ في الدّين أكثر، والكُفُورُ فيهما جميعا" (Q 17:99; 25:50) — frequency distinctions between forms.
4. Verses pairing kufr with shukr: Q 27:40; 2:152; 26:19; 14:7.
5. "ولمّا كان الكفران يقتضي جحود النّعمة صار يستعمل في الجحود، قال: وَلا تَكُونُوا أَوَّلَ كافِرٍ بِهِ [البقرة/ 41] أي: جاحد له وساتر" — his explicit reasoning for the extension to denial.
6. "والكَافِرُ على الإطلاق متعارف فيمن يجحد الوحدانيّة، أو النّبوّة، أو الشريعة، أو ثلاثتها" — *mutaʿāraf* = the established/customary usage.
7. Q 24:55: "عني بالكافر السّاتر للحقّ" — also "concealer of the truth".
8. "ولمّا جعل كلّ فعل محمود من الإيمان جعل كلّ فعل مذموم من الكفر" (sorcery Q 2:102, usury Q 2:275–276, pilgrimage Q 3:97) — theological extension (not used in guide for length).
9. Plurals: "والكُفَّارُ في جمع الكافر المضادّ للإيمان أكثر استعمالا … والكَفَرَةُ في جمع كافر النّعمة أشدّ استعمالا … أُولئِكَ هُمُ الْكَفَرَةُ الْفَجَرَةُ [عبس/ 42]".
10. Q 4:137: several "قيل" views; then "وقد بيّنته في كتاب «الذّريعة إلى مكارم الشّريعة»" — self-reference to his ethics book.
11. Q 57:20: "قيل: عنى بالكفّار الزّرّاع … بدلالة قوله: يُعْجِبُ الزُّرَّاعَ لِيَغِيظَ بِهِمُ الْكُفَّارَ [الفتح/ 29] ولأنّ الكافر لا اختصاص له بذلك. وقيل: بل عنى الكفار، وخصّهم بكونهم معجبين بالدّنيا" — both views reported, each introduced with قيل.
12. Legal: "والْكَفَّارَةُ: ما يغطّي الإثم، ومنه: كَفَّارَةُ اليمين … ككفارة القتل والظّهار" (Q 5:89).
- Site English (harmonized) visibly includes: core sense covering; ingratitude; "Because ingratitude entails denying a blessing, the word extended to outright denial"; kufrān/kufr/kufūr distinction; "Absolute al-kāfir conventionally means …"; Q 4:137 readings + "referring the reader to his own book al-Dharīʿa"; Q 57:20 two views; kaffāra. ✔
- **What it shows:** starts "in the language" with a concrete image; builds the religious sense through ingratitude, reading kufr against its Qur'anic opposite shukr; notes which forms the Qur'an uses for which sense (tendencies: "أكثر استعمالا"); flags customary usage with *mutaʿāraf*; reports rival readings with *qīla*; sends reader to his own ethics book.
- **Uncertainty:** the ordering covering→ingratitude→denial is his reasoned reconstruction ("ولمّا كان … صار"), not a documented history; Ibn Fāris orders it differently.

**Comparison — Ibn Fāris, Maqāyīs, كفر `kfr` (entry_id 163, displayed):**
"الْكَافُ وَالْفَاءُ وَالرَّاءُ أَصْلٌ صَحِيحٌ يَدُلُّ عَلَى مَعْنًى وَاحِدٍ، وَهُوَ السَّتْرُ وَالتَّغْطِيَةُ. يُقَالُ لِمَنْ غَطَّى دِرْعَهُ بِثَوْبٍ: قَدْ كَفَرَ دِرْعَهُ … فَيُقَالُ: إِنَّ الْكَافِرَ: مَغِيبُ الشَّمْسِ. وَيُقَالُ: بَلِ الْكَافِرُ: الْبَحْرُ … وَيُقَالُ لِلزَّارِعِ كَافِرٌ، لِأَنَّهُ يُغَطِّي الْحَبَّ بِتُرَابِ الْأَرْضِ … وَرَمَادٌ مَكْفُورٌ: سَفَتِ الرِّيحُ التُّرَابَ عَلَيْهِ حَتَّى غَطَّتْهُ … وَالْكُفْرُ: ضِدُّ الْإِيمَانِ، سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ. وَكَذَلِكَ كُفْرَانُ النِّعْمَةِ: جُحُودُهَا وَسَتْرُهَا."
My translation of the key line: "Kufr is the opposite of faith; it is so called because it is a covering of the truth. Likewise kufrān of a blessing: denying and concealing it."
- Difference: Ibn Fāris reaches the religious sense in one step (covering the truth) and treats ingratitude as a parallel ("likewise"); his evidence is Arab usage/poetry (armour covered with a garment; sea; buried ash). Al-Rāghib runs the religious sense through ingratitude, grounding it in the Qur'an's kufr/shukr pairing. Al-Rāghib *also* uses "concealer of the truth" at Q 24:55 — so the guide says his path "runs first" through ingratitude, not that he lacks the truth-covering idea.
- Also: Ibn Fāris reports "it is said kāfir [in the line] = sunset / the sea"; al-Rāghib says kāfir there is a description, not a name — noted in notes, not in the guide (too fine).
- Dāwūdī says al-Rāghib drew on Ibn Fāris's *Mujmal* (not the Maqāyīs). I do not claim he used the Maqāyīs.

### CHOSEN 2 — سجد `sjd` — displayed (freq 92)
Stored original: "السُّجُودُ أصله: التّطامن والتّذلّل، وجعل ذلك عبارة عن التّذلّل لله وعبادته، وهو عامّ في الإنسان، والحيوانات، والجمادات، وذلك ضربان: سجود باختيار، وليس ذلك إلا للإنسان … وسجود تسخير، وهو للإنسان، والحيوانات، والنّبات … [الرعد/ 15] … [النحل/ 48] فهذا سجود تسخير، وهو الدّلالة الصامتة الناطقة المنبّهة على كونها مخلوقة … وَالنَّجْمُ وَالشَّجَرُ يَسْجُدانِ [الرحمن/ 6]، فذلك على سبيل التّسخير … ادْخُلُوا الْبابَ سُجَّداً [النساء/ 154] ، أي: متذلّلين منقادين، وخصّ السّجود في الشريعة بالرّكن المعروف من الصلاة، وما يجري مجرى ذلك من سجود القرآن، وسجود الشّكر … اسْجُدُوا لِآدَمَ [البقرة/ 34] ، قيل: أمروا بأن يتّخذوه قبلة، وقيل: أمروا بالتّذلّل له … وَخَرُّوا لَهُ سُجَّداً [يوسف/ 100] ، أي: متذلّلين …"
- Translation for guide: "Sujūd: its origin is lowering oneself and self-abasement, and this was made an expression for abasing oneself before God and worshipping Him … In the religious Law, sujūd was restricted to the well-known pillar of the prayer."
- Harmonized English shows: underlying sense bowing low/self-abasement; two kinds (choice / subjection); 4:154 "humbly and submissively"; "a specialized legal usage: in the sharīʿa, sujūd came to denote the well-known bodily posture within the ritual prayer" ✔.
- **What it shows:** three layers kept apart — base sense, religious application, and a legal specialisation he labels "in the sharīʿa"; some verses glossed without the posture (4:154, 12:100 "متذلّلين"). The two-kinds (choice/taskhīr) scheme is his analytical frame. This is the example that most directly helps a reader see "later technical usage" — and al-Rāghib himself marks it (18 entries use such a marker; list above).
- **Uncertainty:** "restricted in the sharīʿa" says nothing about *when*; I do not claim it is post-Qur'anic. Guide wording: "keeps … apart", "labels".

### CHOSEN 3 — حمد `Hmd` (brief) — displayed; Dāwūdī p. 256
Stored original: "الحَمْدُ لله تعالى: الثناء عليه بالفضيلة، وهو أخصّ من المدح وأعمّ من الشكر، فإنّ المدح يقال فيما يكون من الإنسان باختياره، ومما يقال منه وفيه بالتسخير، فقد يمدح الإنسان بطول قامته وصباحة وجهه، كما يمدح ببذل ماله وسخائه وعلمه، والحمد يكون في الثاني دون الأول، والشّكر لا يقال إلا في مقابلة نعمة، فكلّ شكر حمد، وليس كل حمد شكرا، وكل حمد مدح وليس كل مدح حمدا".
- Translation: "Ḥamd of God Most High: praising Him for excellence. It is narrower than *madḥ* and broader than *shukr*." Then: madḥ may be for what a person does by choice and for what is in him by nature (tall stature, handsome face) as well as for spending wealth, generosity, knowledge; ḥamd only the second [the chosen]; shukr only in return for a favour; so every shukr is ḥamd but not every ḥamd shukr; every ḥamd madḥ but not every madḥ ḥamd.
- Careful reading of "والحمد يكون في الثاني دون الأول": the "first" = qualities by taskhīr (stature, face)? The sentence lists "فيما يكون من الإنسان باختياره، ومما يقال منه وفيه بالتسخير" then examples "بطول قامته وصباحة وجهه [taskhīr], كما يمدح ببذل ماله وسخائه وعلمه [choice]" — "the second" = the second-mentioned examples (generosity etc., by choice). The harmonized English reads it the same way ("Ḥamd applies only to the chosen/acquired qualities"). Guide follows that.
- **Why chosen:** it is the practice behind the introduction's complaint about glossing *al-ḥamdu li-llāh* as "thanks be to God" (C11).

### Considered and rejected
- هدى `hdy` (longest entry; four ordered kinds of divine guidance; "الهدى والهداية في موضوع اللغة واحد لكن قد خصّ الله عزّ وجلّ لفظة الهدى بما تولّاه"; objection–answer "إن قيل … قيل" on Q 37:23 as irony). Excellent for theology-in-the-lexicon, but a fourth example would overrun the word budget; the point is made with سجد + Key p. 13 + the Dharīʿa reference in كفر. Possible substitute.
- سرح `srH` (short, clean borrowing chain: sarḥ tree → pasturing camels → tasrīḥ in divorce "مستعار من تسريح الإبل، كالطّلاق في كونه مستعارا من إطلاق الإبل"; discussed by Key p. 107). Rejected only for length; the borrowing theme is conveyed via Key's summary without naming the root.
- روح `rwH` (singular rīḥ = punishment, plural riyāḥ = mercy, with a counter-case resolved by a variant reading "وقرئ بلفظ الجمع، وهو أصحّ") — interesting but requires explaining qirāʾāt; rejected.
- فوه `fwh` (mouth + speech implies lying) — mentioned by van Gelder; small entry; rejected.
- صلو / زكو / حقق / ربب — not displayed on site (see 1b); cannot be used.
- ذعن, عرجن (61–86 chars) — show terse gharīb glosses; not needed.

---

## 6. Statements in the guide that are my interpretation (not a source's)
- "lexicon and commentary share the same page, and a careful reader learns to tell them apart" (lede).
- "Neither account is a record of the word's history; each is an explanation of how its senses hang together."
- "When an entry sorts a word into kinds (*awjuh*, *ḍarbān*), you are reading al-Rāghib's analysis …"
- The caution that a qualification caught from Qur'anic context is a reading of that context, not independent evidence from outside it.
- "when a definition appears in more than one dictionary on our site, it may be one witness quoted twice" (supported by the on-site citation counts, but the inference is mine).
All are phrased as advice/interpretation, not attributed to al-Rāghib or a scholar.

## 7. Open questions / evidence gaps
- Exact death date: unresolved (502/1108 doubted; c. 425/1034 Dāwūdī; ms of 409/1018 per al-Jawharjī/Key; ms location Damascus vs London disagrees between Dāwūdī and Key).
- hawramani's source text is not stated; the Dāwūdī identification rests on my word-for-word comparison of 4 entries (kfr, srH, Hmd, fjj) and on Key's page numbers matching Shamela's pagination.
- Baalbaki (2014) and EI² (Rowson) not consulted — could not access.
- The treatise on *munāsabāt* and the planned synonyms book are unlocated (Dāwūdī) — nothing said about their content beyond the introduction.
- I did not verify Dāwūdī's claim of dependence on Ibn Fāris's *Mujmal* against the *Mujmal* itself; it is reported as his argument.
- The count of Qur'anic roots lacking an entry (376) mixes genuine omissions and mapping losses; I could not separate them fully.
- Whether al-Rāghib's "في الشريعة" specialisations (sjd etc.) reflect usage later than the Qur'an is not something the entries state; the guide says only that he labels them.

## 8. Site data issues (for the return value)
1. Stored death year 1109 (502 AH) — doubted by modern scholarship (van Gelder: "often stated, without any clear evidence"; Key: oldest ms 409/1018; Dāwūdī: c. 425/1034). Suggest early 11th c. (e.g. ~1025 for ordering, or 1018 as terminus). Effect: the panel places him after Ibn Sīda (1066) instead of near Ibn Fāris (1004).
2. Root `swA` (س و ء, "evil") shows al-Rāghib's سوا (musāwāt, equality — root س و ي) entry; stored root_arabic "سوا". His سوأ (evil) article is not displayed; `swy` has none. The same سوا page mapping likely affects the other dictionaries on swA.
3. Entries the book files under two-letter/alif-final headwords (حق، رب، حب، جن، ضل، صلا، زكا، دعا، سما، دنا، كان …) exist on hawramani but were not mapped to our roots (Hqq, rbb, Hbb, jnn, Dll, Slw, zkw, dEw, smw, dnw, kwn) — high-frequency Qur'anic roots lack an al-Mufradāt entry.
4. Truncation/artifacts: فجج truncated after "وجمعه"; يوم absorbs the following يس article; نأى ends "تمّ كتاب النون كتاب الهاء"; ربح retains poem number "177-".

---

## 9. Final guide text: claim → support map (as published in al-mufradat.ts, 2026-09-26)

Header
- title / titleAr المفردات في غريب القرآن — site label; also the title of the Kaylānī (Cairo 1961) and Khalaf-Allāh (1970) editions per van Gelder's bibliography, and of Shamela's Dāwūdī card. titleGloss is my rendering.
- authorFull "Abū l-Qāsim al-Ḥusayn ibn Muḥammad ibn al-Mufaḍḍal" — the book's own line (Dāwūdī p. 53), van Gelder, Key p. 11 (C2).
- period "early 11th century CE (death date disputed)"; sortYear 1020 (my approximation for ordering only) (C4).

Lede — summary of the essay; each element supported below (plain physical sense → Dāwūdī p. 19 characterisation + kfr/sjd; borrowing → intro p. 55, Key p. 107; narrowing → sjd "خُصّ في الشريعة"; near neighbours → Hmd, intro pp. 55–56). "lexicon and commentary share the page" = my interpretation.

"Bricks for a building"
- verbal sciences first; brick simile; quotation + translation → intro p. 54 (C8).
- "covers" (*mustawfin*), alphabetical by first root letter, *munāsabāt* between borrowed and derived words → intro p. 55 (C10).
- Key: repeatedly explains Qur'anic words as metaphors borrowed from nomadic life → Key p. 107 (C14).
- sequel on synonyms, qalb/fuʾād/ṣadr; dismisses glossing al-ḥamdu li-llāh as "thanks be to God" as explaining the Qur'an → intro pp. 55–56 (C11). Editor could not find it → Dāwūdī p. 55 fn 2.
- Hmd excerpt + paraphrase (handsome face vs generosity; shukr only for a favour) → stored entry; Dāwūdī p. 256.
- life: name → Isfahan; books on ethics, exegesis, theology → van Gelder (C1, C3, C6).
- 502/1108 repeated without clear evidence; early 11th c. → van Gelder (C4).
- Key: oldest ms dated 409/1018; alive in or before 1018 → Key p. 11 (+ bibliography p. 263).
- Dāwūdī: death c. 425 AH (1033–34) → Dāwūdī pp. 37–38.
- "some four centuries after the Qur'an" — arithmetic (Qur'an early 7th c.; al-Rāghib early 11th c.). "contemporary of Ibn Fāris" → Key p. 90.

"Reading an entry" (kfr) — all from stored entry 157 (sect. 5, CHOSEN 1); Dāwūdī pp. 714–717.
- "two half-lines from unnamed poets": ألقت ذكاء يمينها في كافر (introduced via "بعض أهل اللغة لمّا سمع") and كالكرم إذ نادى من الكافور ("قال الشاعر").
- verses setting kufr against shukr: Q 14:7, 27:40 (also 2:152, 76:3 in entry).
- denial grows out of ingratitude: "ولمّا كان الكفران يقتضي جحود النّعمة صار يستعمل في الجحود" + Q 2:41.
- "used more for which sense": "أكثر استعمالا … أكثر … فيهما جميعا"; plurals "أكثر استعمالا / أشدّ استعمالا".
- mutaʿāraf: "والكَافِرُ على الإطلاق متعارف فيمن يجحد …".
- qīla at Q 57:20: two views, each "قيل".
- reference to his own ethical treatise: "وقد بيّنته في كتاب «الذّريعة إلى مكارم الشّريعة»"; Dharīʿa = ethics per van Gelder.
- Ibn Fāris comparison: stored Maqāyīs entry 163 (sect. 5). "a man covers his coat of mail with a garment" = "يُقَالُ لِمَنْ غَطَّى دِرْعَهُ بِثَوْبٍ: قَدْ كَفَرَ دِرْعَهُ". "is so called because it is a covering of the truth" = "سُمِّيَ لِأَنَّهُ تَغْطِيَةُ الْحَقِّ"; "likewise" = "وَكَذَلِكَ كُفْرَانُ النِّعْمَةِ". Al-Rāghib Q 24:55 "عني بالكافر السّاتر للحقّ". Closing sentence = my interpretation.

"Where the lexicon becomes interpretation" (sjd) — stored entry (sect. 5, CHOSEN 2); Dāwūdī pp. 396–397.
- shadows (Q 13:15) and trees (Q 55:6 "وَالنَّجْمُ وَالشَّجَرُ يَسْجُدانِ") perform sujūd; I avoided rendering *al-najm* (stars or stemless plants — ambiguous) by naming only "shadows and trees".
- Q 4:154 "أي: متذلّلين منقادين".
- "in the religious Law" label: "وخصّ السّجود في الشريعة"; same for fasting (صوم: "والصوم في الشرع: إمساك المكلف بالنية …"), repentance (توب: "والتوبة في الشرع: ترك الذنب لقبحه …"), usury (ربو: "لكن خص في الشرع بالزيادة على وجه دون وجه").
- two kinds, choice/taskhīr; "الدّلالة الصامتة الناطقة المنبّهة على كونها مخلوقة، وأنّها خلق فاعل حكيم" → "a silent yet speaking sign that they were made by a wise Maker" (compressed).
- Key "however subtly" → Key p. 13 (C7). Blend = "traditionist piety, Sufism and philosophical ethics" paraphrases Key pp. 12–13 ("traditionists, senior sufis, and wise philosophers"; "the Aristotelian and Neoplatonic ethical heritage"). Page cited: 13.
- ḍarbān / awjuh "kinds": ḍarbān in sjd; awjuh in hdy, qwl etc. (67 entries use أوجه/أضرب/ضربان). Advice = my interpretation.

"Evidence and its limits"
- verses in all but a handful: 1,250/1,267 bracketed refs (my count).
- poetry "no more than 500 lines" → Dāwūdī p. 25 ("لا يتجاوز ٥٠٠ بيت"); "usually anonymous" = my observation ("قال الشاعر" in 182 entries).
- readings without separating mutawātir/shādhdh; sayings wrongly attributed to the Prophet → Dāwūdī p. 26 (C17).
- names earlier philologists in about 60 entries: my regex count = 61 displayed entries matching الخليل|الفراء|الأخفش|أبو عبيدة|ابن دريد|الزجاج|الفارسي|أبو علي|الأصمعي|ابن الأعرابي|سيبويه|أبو زيد|ثعلب|المبرد|الكسائي|ابن السكيت|الجبان|أبو عبيد.
- silent use of Ibn Fāris's *al-Mujmal* → Dāwūdī p. 21 (C18); "not the Maqāyīs" = clarification.
- qīla in about half: 646/1,267 (my count).
- "His own voice is in the definitions, the 'since … it came to be used' reasoning, and first-person asides" — my reading, supported by kfr ("ولمّا كان … صار", "وقد بيّنته").
- al-Fīrūzābādī, al-Samīn al-Ḥalabī reworked it → Dāwūdī p. 24 (C19).
- Tāj ≈280, Lane ≈265 → my tool counts (sect. 1). "one witness repeated" = my inference.
- Zarkashī quotes → zarkashi-gharib, zarkashi-tafsir (C15). "fourteenth-century" → d. 794/1392 (van Gelder).
- "explanations offered in the early eleventh century, not records of usage"; "Test them against the verses …" = my interpretation/advice.

onOurSite — sect. 1a/1b. "some frequent roots show no entry from this work" (حقّ، ربّ، صلا، كان) → hawramani contents + page checks. fjj truncation → stored vs Shamela. Death date 1109 → dicts output.

Removed during drafting (length): hdy and srH examples; title-variant sentence (van Gelder "more often entitled Mofradāt alfāẓ al-Qorʾān"); editor's warning wording "wa-quriʾa".

---

## 10. Revision round 1 (2026-09-26): extra checks made while applying verification-r1

- **Tāj al-ʿArūs count (C56).** Python over displayed Tāj entries, vowel marks stripped (`original_text_ar`, SHOWN filter): 340 contain الراغب. 312 have an explicit "قال/وقال/قاله الراغب", "مفردات" or "الراغب:"; I read the other 28 in context. 27 of them are the scholar ("نقله الراغب", "قيده الراغب", "أشار إليه الراغب", "صرح به الراغب"…). One, `wsl`, is the ordinary word: "الواسل: (الراغب إلى الله تعالى)". So 339 entries cite him. The guide says "some 340".
- **Anonymous poetry.** In displayed Mufradāt entries I count 297 anonymous introductions ("قال الشاعر", "قول الشاعر", "قال الآخر"…) across 239 entries, against 16 introductions that name one of about 40 common poets. Dāwūdī p. 5, method item 6: "نسبة الأبيات الشعرية لقائليها، وبيان محلها في كتب اللغة والتفسير" (Shamela 23636/1).
- **Near-synonym comparisons.** `grep … '(أخص|أعم|أبلغ) من'` gives 61 displayed entries, hence "a few dozen". "الفرق" is unusable as a marker because it also matches the root فرق.
- **The introduction's framing (pp. 53–54, Shamela ids 35–36).** p. 53: "كنت قد ذكرت في «الرسالة المنبهة على فوائد القرآن»". p. 54: "وأشرت في كتاب «الذريعة إلى مكارم الشريعة»", then "وذكرت أنه…" and "ودلّلت في تلك الرسالة", where Dāwūdī's n. 3 reads "أي: الذريعة". The bricks passage follows as "وذكرت أنّ أول ما يحتاج…". Which earlier work the bricks passage restates is therefore ambiguous (the *Risāla munabbiha* or the *Dharīʿa*). The guide says only "recalling his earlier writings".
- **kfr, poetry.** The first half-line (ألقت ذكاء يمينها في كافر) appears twice in entry 157. At the start it is quoted to reject a philologist's inference: "وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع". Near the end it is ordinary evidence: "ويقال الْكَافِرُ للسّحاب الذي يغطّي الشمس والليل، قال الشاعر: ألقت ذكاء…". The second half-line (كالكرم إذ نادى من الكافور) is also quoted twice.
- **Key URL.** doi.org/10.1525/luminos.54 redirects to luminosoa.org, which returns 403 both to curl and in the browser pane. library.oapen.org returns 403 to curl and the browser pane could not open it. The UC Press book page https://www.ucpress.edu/books/language-between-god-and-the-poets/paper returns 200, labels the book "Open Access" and offers "Read Book / Download EPUB / PDF", so it is the new URL. I re-checked the page numbers against the archive.org copy of the OAPEN PDF (archive.org/details/oapen-20.500.12657-29479; printed page = PDF page − 17): p. 11 "ar-Rāġib was alive in or before 1018"; p. 13 "combination to seep, however subtly, into his glossary of the Quran"; p. 90 "the dictionary of his contemporary Ibn Fāris"; p. 107 "using the word for 'metaphor' (istiʿārah…) … from a nomadic lifestyle".
- **Iranica** (Wayback snapshot of the article URL): "The first, more often entitled Mofradāt alfāẓ al-Qorʾān, is a very useful alphabetical dictionary of Qorʾanic Arabic". This supports the alternative-title sentence.
- **Ordering against Ibn Sīda.** `dicts` gives Ibn Sīda 1066 and al-Rāghib 1109, so the panel puts al-Rāghib after Ibn Sīda. I did not write "not after Ibn Sīda". Dāwūdī p. 37 reports that al-Dhahabī put him in the 42nd *ṭabaqa* (deaths 440–470 AH), which overlaps Ibn Sīda's d. 458. Only "contemporary of Ibn Fāris" (Key p. 90) is used.

---

## 11. Revision round 2 (2026-09-26): checks made while applying verification-r2

- **Poets named in al-Rāghib's own text (C58).** `_dict_guide_tool.py grep al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran` over "قال/قول" plus 14 common poet names finds 12 displayed entries:
  - bEd and AHd: النابغة
  - Hkm and HSr: لبيد
  - brj and xbl: زهير
  - gbr: طرفة
  - x*l: الأعشى
  - krs: العجاج
  - nhr: أبو ذؤيب
  - $rb and sbE: الهذلي

  So the text *sometimes* names poets; the guide now says "most attributions in the printed edition come from the editor's notes".
- **Dāwūdī p. 5 (Shamela 23636/1, fld_goto_top = 5), method item 6, re-read:** "نسبة الأبيات الشعرية لقائليها، وبيان محلها في كتب اللغة والتفسير، وضبط الأبيات، إذ قلّ ما وجدناه منها صحيحاً".
- **Dāwūdī p. 21 (Shamela 23636/17, fld_goto_top = 21), re-read:** "كتاب «المجمل في اللغة» لابن فارس. ويبدو أنّ الراغب قد اعتمد عليه كثيرا، مع أنه لم يذكره باسمه … وربما ينقل عنه حرفيا". The Mujmal locator is narrowed to p. 21.
- **Entry 157 (kfr), order re-checked.** The thanks verses (Q 27:40, 2:152, 26:19, 14:7) and the Q 2:41 denial step come before "[النور/ 55] عني بالكافر السّاتر للحقّ". This supports "he gets there via the Qur'an's pairing of *kufr* with thanks".
