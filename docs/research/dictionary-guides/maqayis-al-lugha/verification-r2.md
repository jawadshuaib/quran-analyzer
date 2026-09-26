# Maqāyīs al-Lugha: verification, round 2

Independent fact-check of `roots/frontend/src/content/dictionary-guides/guides/maqayis-al-lugha.ts` (checked 2026-09-26). I did not open research-notes.md or any revision file. I read verification-r1.md, but I re-checked every point myself and did not count r1's findings as evidence.

## Sources checked directly

- **Hārūn ed. on Shamela (book 21710)**
  - The book card confirms: 2nd ed., al-Bābī al-Ḥalabī, 1389–92 AH / 1969–72, 6 vols, page-matched.
  - Every page below was fetched and its volume and page read from the page title.
  - Editor's introduction: pp. 5–10 (/3–/8), p. 23 (/21), pp. 39–45 (/37–/43).
  - Preface: vol. 1 pp. 3–5 (/47–/49).
  - Entries: vol. 1 p. 52 (أتى, /96); p. 134 (أمن, /178); p. 169 (end of the hamza book, /213); pp. 325–29 (/369–/373); p. 403 (/446); vol. 2 p. 372 (/932); p. 386 (/946); p. 509 (/1069); vol. 3 pp. 183–84 (/1251–2); vol. 4 pp. 205–6 (/1746–7); vol. 5 pp. 192–93 (/2244–5); vol. 6 p. 71 (/2605); p. 150 (/2683); pp. 158–60 (/2691–3).
  - To test "most letters", I scanned the closing pages of all 28 letter books for the longer-words chapter.
- **al-Ṣāḥibī on Shamela (book 9977):** pp. 44 (/50) and 45 (/51). The card confirms Bayḍūn, 1st ed., 1418/1997, page-matched.
- **Baalbaki 2014, Google Books preview**
  - I read p. 349 on screen: the method paragraph, the five works with "(i.e. *Iṣlāḥ al-manṭiq*)", and the start of the "not interested in authoring an exhaustive lexicon" sentence.
  - Pp. 350, 351, 355 and 356 would not load. Google then served a reCAPTCHA to both browsers and to curl/WebFetch. I did not attempt it.
  - p. 351's "frequently arbitrary and unconvincing" is confirmed independently in the *Journal of Abbasid Studies* 5 (2018), "Meaning and Captivity in Classical Arabic Philology" (brill.com/view/journals/jas/5/1-2/article-p177_7.xml), fn 21: "Baalbaki, *Arabic Lexicographical Tradition*, 351".
- **hawramani**
  - The dictionary page: opens, and names no edition or editor.
  - The root pages /ردد/ (no Maqāyīs section) and /رد/ (has the Maqāyīs *radd* entry).
- **Displayed entries** via `_dict_guide_tool.py`:
  - Maqāyīs: kfr 163, mjs 16616, qbl 536, Ebd 519, fqh 4838, jvm 9425.
  - *Kitāb al-ʿAyn*: Ebd 372.
  - Greps across all 1,323 Maqāyīs entries.
  - Greps of the Lisān and Tāj entries for "ابن فارس".
- **quran.db:** the `morphology` and `dictionary_entries` tables.

Verdicts: S = supported, NQ = needs qualification, U = unsupported.

## Claims table

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Maqāyīs al-Lugha* / مقاييس اللغة | S | Shamela card "معجم مقاييس اللغة"; preface "هذا كتاب المقاييس فى اللغة" (vol. 1 p. 3, /47) |
| C2 | titleGloss "The Measures of Language" | S | Plain rendering of *maqāyīs*; preface "مقاييس صحيحة" |
| C3 | author Ibn Fāris; authorFull Abū l-Ḥusayn Aḥmad ibn Fāris ibn Zakariyyāʾ; ابن فارس | S | Shamela card "أبو الحسين أحمد بن فارس بن زكريا (ت ٣٩٥ هـ)" |
| C4 | period "d. 395 AH / 1004–5 CE (other dates reported)" | S | Hārūn intro p. 9 (/7) "يختلفون فى تاريخ وفاته على أقوال خمسة"; p. 10 (/8) "وأصح الأقوال … سنة (٣٩٥)" |
| C5 | kind "Root-meaning dictionary" | S | Preface p. 3; Baalbaki p. 349 |
| C6 | summary: names core sense(s); supports them with poetry, the Qur'an and earlier lexicons; sets aside misfits; the senses are his proposals | S | Preface p. 3; entries kfr, qbl, Ebd; Baalbaki p. 349 ("determining whether the root has no aṣl, one aṣl, or more … attested usage (šawāhid), particularly in poetry") |
| C7 | lede: a typical entry opens with a verdict (one, two or three *aṣl*), then the evidence | S | Of 1,323 displayed entries, 988 name an *aṣl* in their first ~160 characters and 35 name three *uṣūl* (my count) |
| C8 | lede: "tenth-century philologist"; persuasive in places, strained in others; frank about misfits | S | d. 395/1004; qbl "يتمحل"; the shadhdha formula (C28) |
| C9 | Worked mostly in Hamadhān, later at the Buyid court in Rayy, where he died | S | Intro p. 5 (/3) "استقر به فى معظم الأمر بمدينة همذان"; p. 6 (/4) "استدعى منها إلى بلاط آل بويه بمدينة الري"; p. 9 (/7) "قضى نحبه في مدينة الرى" |
| C10 | Hārūn lists five dates and settles on 395 [intro pp. 5–10] | S | As C4; the locator covers pp. 5–10 |
| C11 | Preface quotation "إنّ للغة العرب مقاييسَ صحيحةً، وأصولاً تتفرّع منها فروع" and its translation | S | vol. 1 p. 3 (/47), verbatim; translation accurate |
| C12 | Earlier compilers never set out one of these measures | S | p. 3 "ولم يُعربوا فى شئٍ من ذلك عن مقياس من تلك المقاييس، ولا أصل من الأصول" |
| C13 | Each section headed with its *aṣl*, so a short statement covers the family | S | p. 3 "وقد صدَّرْنَا كلَّ فصلٍ بأصله … حتّى تكونَ الجملةُ الموجَزةُ شاملةً للتَّفصيل" |
| C14 | Five books: *ʿAyn*, ranked highest and noblest; two by Abū ʿUbayd; one by Ibn al-Sikkīt; Ibn Durayd's *Jamhara* | S | pp. 3–5 (/47–/49): "فأعلاها وأشرفُهَا كتاب … الخليل"; "كتابا أبى عبيد"; "(كتاب المنطق) … عن ابن السكيت"; "(الجمهرة)"; "فهذه الكتب الخمسة معتمدنا" |
| C15 | Everything else rests on these | S | p. 5 "وما بعدَ هذِه الكتبِ فمحمولٌ عليها، وراجعٌ إليها" |
| C16 | "The words are inherited; the analysis is his." | S | Interpretation, consistent with p. 5 "معتمدنا فيما استنبطناه من مقاييس اللغة" |
| C17 | Baalbaki: not aiming at completeness; keeps what demonstrates an *aṣl*; abridges what he takes from al-Khalīl and Ibn Durayd [pp. 349–50] | **NQ** | p. 349 (seen): "Ibn Fāris was not interested in authoring an exhaustive lexicon and satisfied himself with the lexical…"; the sentence runs onto p. 350, which I could not open. The abridgement half is **unconfirmed this round**. |
| C18 | "The verdict is typically *aṣl ṣaḥīḥ yadullu ʿalā…*" | **NQ** | Displayed entries: the full formula "أصل صحيح يدل" in 200 of 1,323 (15%); "أصل صحيح" in 281 opening passages; "يدل" in 708. The formula is common, not typical. |
| C19 | By Baalbaki's count, 1,808 of 4,631 roots have no *aṣl*, 2,346 have one, 477 more [p. 350] | **NQ** | p. 350 not reachable (CAPTCHA); **unconfirmed this round**. No second source found. |
| C20 | mjs: "a word for which we know no measure; I think it is Persian"; *al-majūs* at Q 22:17 | S | Entry 16616 "كلمة ما نعرف لها قياسا، وأظنها فارسية"; morphology: مَجُوسَ at 22:17 |
| C21 | kfr excerpt and its translation, [Q 57:20] | S | Entry 163; Hārūn vol. 5 pp. 191–92; كُفَّارَ at 57:20; translation accurate |
| C22 | kfr: concrete uses first (armour, ashes under dust, the sun casting its hand into *kāfir*); two glosses (sunset/sea) without choosing | S | Entry 163: "يقال إن الكافر مغيب الشمس. ويقال بل الكافر البحر", with no preference stated |
| C23 | The Qur'an is cited for farmers, not for belief | S | 57:20 is the entry's only Qur'an citation |
| C24 | The *kufr*–covering link is in his own voice ("so called because") | S | "والكفر ضد الإيمان، سمي لأنه تغطية الحق", unattributed |
| C25 | *kafirāt* "perhaps" (*laʿalla*): high peaks seem to hide them | S | "ولعلها سميت كفرات لأنها متطامنة، كأن الجبال الشوامخ قد سترتها" |
| C26 | *al-Ṣāḥibī*: words moved "from their places to other places"; the Arabs knew of *kufr* only covering and concealment [pp. 44–45] | S | p. 44 (/50) "ونُقِلت من اللغة ألفاظ من مواضعَ إِلَى مواضع أخَر"; p. 45 (/51) "كَانَتْ لا تعرف من الكُفر إِلاَّ الغِطاء والسِّتْر" |
| C27 | That "unbelief" grew out of "covering" is Ibn Fāris's reconstruction | S | Correctly labelled as interpretation |
| C28 | Recurring formula *wa-mimmā shadhdha ʿan hādhā l-bāb* | S | 29 displayed entries (e.g. hdy, lqH, hmd, fyl) |
| C29 | qbl excerpt and its translation | S | Entry 536; translation accurate, "yutamaḥḥal" rendered as "a strained case can be made" |
| C30 | *qabl*, the form the Qur'an uses most, is left outside the family | S | Morphology: *qabl* 242 occurrences, next lemma 10. Ibn Fāris says "nearer to being an outlier", and the excerpt above shows that hedge (see brief suggestion). |
| C31 | Hārūn: Ibn Fāris hardly ever failed to find the shared sense [intro p. 23] | S | p. 23 (/21) "فلا يكاد يخطئه التوفيق" |
| C32a | Baalbaki finds the *uṣūl* "frequently arbitrary and unconvincing" [p. 351] | S | *JAS* 5 (2018), fn 21, cites "Baalbaki, *Arabic Lexicographical Tradition*, 351" for this exact phrase |
| C32b | "Baalbaki … notes that Ibn Fāris said he disliked far-fetched connections" [p. 351] | **NQ** | p. 351 not reachable; **unconfirmed this round**. No such statement found in the displayed entries (greps for تكلف, تعسف, بعيد…القياس). |
| C33 | Under each first letter: doubled roots such as *radd*, then three-letter roots, in an order of Ibn Fāris's own [intro pp. 42–44] | S | Intro p. 42 (/40) "سلك طريقاً خاصَّا به"; p. 43 (/41) "قسم كل كتاب إلى أبواب ثلاثة أولها باب الثنائى المضاعف والمطابق، وثانيها أبواب الثلاثى … وثالثها بابُ ما جاء على أكثر من ثلاثة أحرفٍ"; *radd* at vol. 2 p. 386 (/946) in "باب الراء وما معها فى الثنائى والمطابق" (p. 372, /932). NB: our site does not display this entry (brief issue B1). |
| C34 | Most letters end with a chapter on longer words | S | My scan of all 28 books found the chapter in 25 (e.g. bāʾ vol. 1 p. 328, thāʾ p. 403, rāʾ vol. 2 p. 509, kāf vol. 5 p. 193, hāʾ vol. 6 p. 71). Hamza ends "تم كتاب الهمزة" (/213). Wāw ends "تم كتاب الواو" (/2683). Yāʾ has only a short paragraph "فأما ما زاد على الثلاثة فى هذا الباب" (vol. 6 p. 160). |
| C35 | "Most of what you see" is carved (*manḥūt*): two words taken, a new one carved keeping a share of each [vol. 1 pp. 328–29] | S | p. 328 (/372) "وذلك أنّ أكثر ما تراه منه منحوتٌ. ومعنى النَّحت أن تُؤخَذَ كلمتان وتُنْحَتَ منهما"; p. 329 (/373) "كلمةٌ تكون آخذةً منهما جميعاً بحَظٍّ" |
| C36 | "The rest were 'set down' with no room for measure" | S | p. 329 "على ضربين: أحدهما المنحوت … والضَّرْب الآخر [الموضوع] وضعاً لا مجالَ له فى طُرق القياس" (the word الموضوع is Hārūn's supplement; وضعاً is original) |
| C37 | *karbala* (slack-footed gait) carved from *rabl* (flabby flesh) and *kabl* (fetter) | S | Entry 163 = vol. 5 p. 193: "رخاوة في القدمين … منحوتة من كلمتين: من ربل وكبل. أما ربل فاسترخاء اللحم … وأما الكبل فالقيد" |
| C38 | In practice he adds a third kind, three-letter words with letters added: *kanfalīla* (bushy beard) = *kafl* (gathering) enlarged | S | Entry 163: "(الكنفليلة): اللحية الضخمة. وهذا مما زيدت فيه النون … وهو من الكفل، وهو جمع الشيء". He also states the class outright, not only in practice: jvm entry 9425 (jīm chapter intro) "ومنه ما أصله كلمة واحدة وقد ألحق بالرباعي والخماسي بزيادة تدخله"; rāʾ chapter vol. 2 p. 509 "فمنحوت أو مزيد فيه" (suggestion B3). |
| C39 | *kibrīt* "is not Arabic"; "I do not know how the scholars accept this and its like" | S | Entry 163: "(الكبريت): ليس بعربي"; on *kundush*: "وما أدري كيف يقبل العلماء هذا وأشباهه" |
| C40 | Ebd excerpt and its translation; "(The bracketed word is the editor's.)" | S | Entry 519; Hārūn vol. 4 p. 205 (/1746) prints "و [الأول] من ذينك" |
| C41 | First *aṣl*: *ʿabd* and the trodden road; second: thick strong cloth and *ʿabad* (disdain) | S | Entry 519: "الطريق المعبد … المسلوك المذلل"; "ثوب له عبدة، إذا كان صفيقا قويا"; "العبد، مثل الأنف والحمية" |
| C42 | Some quoted voices are marked: "al-Khalīl said" introduces the *ʿibād* / *ʿabīd* distinction | S | Entry 519 "قال الخليل: إلا أن العامة اجتمعوا على تفرقة ما بين عباد الله والعبيد المملوكين" |
| C43 | Where a quotation ends is not marked. "We have not heard them derive a verb" reads "I have not heard" in the *ʿAyn* entry, where much of the rest also appears, often closely worded, with no statement of a shared sense. | S | Maqāyīs "ولم نسمعهم يشتقون منه فعلا"; ʿAyn 372 "ولم أسمعهم يشتقون منه فعلاً". The ʿAyn also has *muʿabbad* "مهنوء بالقطران", the road, "العبد: الأنفة والحمية", Q 43:81, and ʿAlī's "عبدت فصمت". It has no *aṣl* statement. |
| C44 | Q 43:81 filed under the second sense with *wa-fussira*: "the first to be angered by this and to disdain it" | S | Entry 519 "وفسر قوله تعالى … أي أول من غضب عن هذا وأنف من قوله"; عَٰبِدِينَ at 43:81 |
| C45 | The *ʿAyn* on al-nuqta gives that reading and adds one where *ʿābidīn* = worshippers | S | ʿAyn 372 "أي الأنفين … ويقال … فلست بأوّل من عَبَدَ الله من أهل مكة" |
| C46 | The *Maqāyīs* gives only the reading that serves its second *aṣl* | S | Entry 519 gives one reading only |
| C47 | An *aṣl* is his inference; his Qur'anic citations are evidence chosen for his scheme; weigh context and other dictionaries | S | Interpretation, consistent with the preface ("استنبطناه") and the entries |
| C48 | Older material: pre-Islamic poets such as Ṭarafa and al-Nābigha; philologists of the 8th–10th c. | S | Ṭarafa in Ebd (Hārūn fn "من معلقته"). al-Nābigha in Amn (Hārūn fn "ديوان النابغة ٧٨") and Aty (his Muʿallaqa verse). The five sources run from al-Khalīl (8th c.) to Ibn Durayd (d. 321/933). |
| C49 | fqh: *fiqh* is "every knowledge of a thing", "then" reserved for knowledge of the religious law | S | Entry 4838 "وكل علم بشيء فهو فقه … ثم اختص بذلك علم الشريعة" |
| C50 | Hārūn edited from the single manuscript he could find; knew only Yāqūt as a medieval author mentioning it; wrote that scholars noticed it only recently [intro pp. 39–40] | S | p. 39 (/37) "ولم أجدْ أحداً غير ياقوت يذكر هذا الكتاب"; p. 40 (/38) "لم يسترع انتباه العُلماء إلا منذ عهد قريب … لم أجِد أمامى منه إلا نُسخة واحِدة" |
| C51 | Baalbaki's survey: used, if narrowly; *Lisān* never quotes its *uṣūl*; al-Ṣaghānī often cites them; some of his quotations passed into *Tāj* [pp. 355–56] | **NQ** | pp. 355–56 not reachable; **unconfirmed this round**. Partial corroboration from our displayed data: *Lisān* has 6 hits for "ابن فارس", none quoting an *aṣl* (e.g. TEm "أخذه من كتاب ابن فارس", Abl "ابن فارس في المجمل"). *Tāj* quotes Maqāyīs-style reasoning (zhq "من الأصل الذي ذكرنا"; xbT "وقال ابن فارس: الأصل فيه"). The al-Ṣaghānī link itself is not verified. |
| C52 | Stored text follows Hārūn, including his corrections to the manuscript and his square-bracketed words | S | Ebd: stored ذينك, المهنوء, صفيقا match Hārūn's corrections (his fns: ms ذلك, المهناء, ضعيفا). kfr stored فهم = Hārūn's correction of ms فهو (vol. 5 p. 192 fn 4). [الأول], [فإن كانت] present. |
| C53 | Hārūn's footnotes identify many poets quoted without names; not included | S | Hārūn intro p. 45 (/43) "عُنيت أيضا بنسبة الأشعار والأرجاز المهملة إلى قائليها"; kfr fns (al-ʿAjjāj, al-Numayrī); stored text has no footnotes. Baalbaki p. 349: verses "mostly not ascribed" |
| C54 | Full vowels, bracketed verse references and the vowelled root heading are not in Shamela's text | S | Shamela: partial vowels, ﴿…﴾ with no [sura: verse], headings like "[عبد]" |
| C55 | 1,323 roots shown, covering every letter | S | Tool: 1,323 displayed; 28 distinct first letters. But see B1: the whole doubled-root section is absent. |
| C56 | Entries run from a single line to over a thousand words | S | Hsd = 8 words; Eqb = 1,277 words |
| C57 | In several letters the source copy runs the closing chapter into the preceding root | S | kfr, jvm, nml, srd, SrT carry appended "مما زيدت فيه…" material |
| C58 | End of kfr, from *kanfalīla* on, belongs to that chapter | S | Hārūn vol. 5 p. 193 (/2245): chapter heading, then "من ذلك (الكنفليلة)" |
| C59 | Most of jvm: the heading surfaces mid-verse; the list breaks off | S | Entry 9425 "قال: باب ما جاء … أوله جيم بنانتين وجذمورا"; ends "ومما وضع وضعا ولم أعرف له اشتقاقا:" |
| C60 | harun-ed citation | S | Shamela card |
| C61 | Baalbaki citation (Brill 2014, pp. 348–56) | S | Book exists; p. 349 seen; section confirmed |
| C62 | Ṣāḥibī citation (Bayḍūn 1997, "Bāb al-asbāb al-islāmiyya", pp. 44–45) | S | Shamela card and page titles |
| C63 | hawramani: the source of our text; names no edition | S | Page opens; no editor or edition named |
| C64 | Excerpts copied from the stored originals | S | Validator: 3 excerpts valid |

Totals: 65 rows (C32 split into a and b). 60 supported, 5 need qualification (C17, C18, C19, C32b, C51), 0 unsupported.

## Flagged items and fixes

- **C18 "The verdict is typically *aṣl ṣaḥīḥ yadullu ʿalā…*"**
  - Overgeneralised: the exact formula appears in 200 of 1,323 displayed entries.
  - Fix: change "The verdict is typically…" to "A common verdict is *aṣl ṣaḥīḥ yadullu ʿalā…*".
- **C19 Baalbaki's counts (1,808 / 4,631 / 2,346 / 477, p. 350)**
  - I could not open p. 350 (Google CAPTCHA), and the reviser also reports being unable to reopen Baalbaki.
  - Fix: before publishing, confirm the four figures and the page against the Google Books preview in an ordinary browser. If they cannot be confirmed, delete the sentence.
  - The point that not every root gets a sense stands without them: mjs, and 124 displayed entries opening with "ليس بأصل", "كلمة واحدة", "ما نعرف" and similar.
- **C17 Baalbaki on abridging al-Khalīl and Ibn Durayd (pp. 349–50)**
  - I confirmed only p. 349: "not interested in authoring an exhaustive lexicon and satisfied himself with the lexical…".
  - Fix: confirm the p. 350 continuation. If unconfirmable, keep only "Nor did he aim to be complete [^baalbaki|p. 349]" and drop the abridgement clause.
- **C32b "Ibn Fāris said he disliked far-fetched connections" (p. 351)**
  - Unconfirmed; p. 351 is only corroborated for "frequently arbitrary and unconvincing".
  - Fix: confirm on p. 351. If unconfirmable, write "Baalbaki, by contrast, finds his proposed *uṣūl* 'frequently arbitrary and unconvincing'.[^baalbaki|p. 351]"
- **C51 Baalbaki pp. 355–56 on Lisān, al-Ṣaghānī and Tāj**
  - Unconfirmed this round.
  - Fix: confirm pp. 355–56 before publishing. If unconfirmable, cut to what can be shown: Hārūn's statement (C50) and, optionally, "the *Tāj* entries on al-nuqta sometimes quote Ibn Fāris's root reasoning, e.g. [[root:zhq|murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus|ز ه ق]]" (Tāj zhq "وقال ابن فارس: … من الأصل الذي ذكرنا").
  - Also make "some of his quotations" unambiguous: al-Ṣaghānī's, not Ibn Fāris's.

## Brief issues

- **B1 (must-fix): tell readers the doubled-root section is missing.**
  - Our copy has no Maqāyīs entry for any doubled root. Of the 153 Qur'anic roots whose 2nd and 3rd radicals are identical (rbb, Hqq, Znn, Hbb, mdd, dll, Emm, rdd …), none has a Maqāyīs row in `dictionary_entries`, in any review status.
  - Cause: hawramani files these under two-letter pages. /رد/ carries the Maqāyīs *radd* entry; /ردد/ has no Maqāyīs section.
  - So the first of the three sections in every letter (C33) is absent from our site.
  - onOurSite should say so, e.g. "The opening section of each letter, on doubled roots such as *radd* or *rabb*, is not in our copy."
  - The body's "doubled roots such as *radd*" names a root the site does not show in this dictionary. Per FORMAT it should be marked `[[root:rdd|none|ر د د]]` with the limitation stated, or be covered by the onOurSite note.
- **B2 (suggestion): hedge on *qabl*.** "the form the Qur'an uses most is left outside the family" is firmer than Ibn Fāris's "nearer to being an outlier". Consider "is placed, tentatively, outside the family".
- **B3 (suggestion): the third kind is not only practice.** He names three kinds himself in the jīm chapter's introduction (visible inside [[root:jvm|…]]), and the rāʾ chapter heading reads "فمنحوت أو مزيد فيه". Consider "Elsewhere he names a third kind…" instead of "In practice he adds…".
- **B4 (suggestion): word count.** Lede + body is 1,099 words. The C18/C32b fixes are neutral or shorter, and B1 belongs in onOurSite, so no trim is needed if applied as proposed.
- **Tone and labels.**
  - No generic praise or ranking was found. The Hārūn/Baalbaki contrast is balanced, and the essay repeatedly says the *uṣūl* are proposals.
  - It does not force a single-origin narrative: it shows no-*aṣl*, one-*aṣl*, two-*aṣl* and outlier cases.
  - Translations are labelled.
  - Every root mention except *radd* is a root link.

## URL check

- https://shamela.ws/book/21710: opens; Hārūn 2nd ed., page-matched. OK.
- https://books.google.ca/books?id=cme7AwAAQBAJ&pg=PA349: opens in a normal browser and shows p. 349. Later pages would not load in my session, and Google then served a reCAPTCHA. The URL is usable for ordinary readers, but the p. 350/351/355–56 claims remain unconfirmed by me.
- https://shamela.ws/book/9977/50: opens *al-Ṣāḥibī* p. 44, where the chapter begins. OK.
- https://arabiclexicon.hawramani.com/ibn-faris-maqayis-al-lugha/: opens; right page; no edition named. OK.
- All four sources are cited in the text. None is listed but unused.

## Validator

`node scripts/validate-dictionary-guides.mjs maqayis-al-lugha` passed ("1/1 guides pass"):
- 8 root links (7 distinct pairs);
- 3 excerpts;
- 1,099 words (lede + body, excluding excerpts).

## Site-data issues

1. **Doubled roots never collected (B1).** No Maqāyīs entry exists for any doubled root (0 of 153 Qur'anic doubled roots). hawramani keeps them on two-letter pages (e.g. /رد/), which the scrape did not fetch. This removes, among others, Maqāyīs entries for rabb, ḥaqq, ẓann, ḥubb and madd.
2. **Longer-words chapters merged into the preceding root.** kfr, jvm, nml, srd and SrT carry a letter's closing chapter.
   - The kfr harmonized English still calls the appended words "augmented and quadriliteral words Ibn Fāris files under k-f". The faithful translation says "falling under the k-f section".
   - Both are wrong: the material belongs to the chapter for the whole letter kāf (Hārūn vol. 5 p. 193).
3. **Stored labels are correct.** Author "Ibn Fāris" and date 1004 (395 AH ≈ 1004–5 CE) are right.
