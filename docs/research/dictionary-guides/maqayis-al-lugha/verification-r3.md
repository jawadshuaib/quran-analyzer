# Maqāyīs al-Lugha: verification, round 3

Independent fact-check of `roots/frontend/src/content/dictionary-guides/guides/maqayis-al-lugha.ts` (checked 2026-09-26).

**What I read:**
- I did not open research-notes.md or any revision file.
- I read verification-r2.md for the list of prior flags only. None of its verdicts is counted as evidence here.

## Sources checked directly this round

- **Hārūn ed. on Shamela (book 21710)**
  - Book card: 2nd ed., al-Bābī al-Ḥalabī, 1389–92 AH / 1969–72, 6 vols, "ترقيم الكتاب موافق للمطبوع". Author "أبو الحسين أحمد بن فارس بن زكريا (ت ٣٩٥ هـ)".
  - I downloaded each page below with curl and read its volume and page from the page title.
  - Editor's introduction: pp. 5, 6, 9, 10, 23, 39, 40, 41, 42, 43, 44, 46 (/3, /4, /7, /8, /21, /37, /38, /39, /40, /41, /42, /44).
  - Author's preface: vol. 1 pp. 3–5 (/47–/49).
  - Entries:
    - vol. 1 pp. 328–29 (/372–/373)
    - vol. 2 p. 372 (/932), p. 381 (/941), p. 386 (/946), p. 509 (/1069)
    - vol. 4 p. 205 (/1746)
    - vol. 5 pp. 191–93 (/2243–/2245)
- **al-Ṣāḥibī on Shamela (book 9977):** pp. 44 (/50) and 45 (/51). Card: Bayḍūn, 1st ed. 1418/1997, page-matched.
- **Baalbaki 2014**
  - Google Books: both the browser pane and curl/WebFetch got Google's reCAPTCHA ("unusual traffic"). I did not attempt it. **I could not see any page of the book.**
  - Brill title page https://brill.com/display/title/25514 opens. It confirms the book (Brill, 2014; ISBN 978-90-04-27401-3). Chapter 3, "Muǧannas (Semasiological) Lexica", runs pp. 279–401, so pp. 348–56 fall inside it. The section's exact page range is not visible there.
  - Larsen, "Meaning and Captivity in Classical Arabic Philology", *Journal of Abbasid Studies* 5 (2018), https://brill.com/view/journals/jas/5/1-2/article-p177_7.xml. It opens and is open access. Its text reads: *Jaakko Hämeen-Anttila calls his etymologies "fantastic"; "frequently arbitrary and unconvincing," says Ramzi Baalbaki.* Footnote 21 cites "Baalbaki, *Arabic Lexicographical Tradition*, 351".
- **hawramani:** https://arabiclexicon.hawramani.com/ibn-faris-maqayis-al-lugha/ returns 200. It names no edition or editor. Its contents list includes doubled roots (أَبَّ, أَتَّ, أَثَّ …), which the site has but we did not scrape.
- **Displayed entries**, via `_dict_guide_tool.py` and `quran.db`:
  - Maqāyīs: kfr 163, mjs 16616, qbl 536, Ebd 519, fqh 4838, jvm 9425, dlk 17840, Ejz 4076, Ajr 1294.
  - *ʿAyn*: Ebd 372.
  - *Tāj*: dlk 17838.
  - Greps across all 1,323 displayed Maqāyīs entries and across the *Tāj*.
  - `morphology` (Qur'an forms), `dictionary_entries` and `dictionaries`.
- **Local API:** `/api/root/dlk/dictionaries` lists both the Maqāyīs and the *Tāj* for dlk.

Verdicts: S = supported, NQ = needs qualification, U = unsupported.

## Claims table

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Maqāyīs al-Lugha* / مقاييس اللغة | S | Shamela card "معجم مقاييس اللغة"; preface vol. 1 p. 3 "هذا كتاب المقاييس فى اللغة" |
| C2 | titleGloss "The Measures of Language" | S | Plain rendering; preface "إن للغة العرب مقاييس صحيحة" |
| C3 | Ibn Fāris; Abū l-Ḥusayn Aḥmad ibn Fāris ibn Zakariyyāʾ; ابن فارس | S | Shamela card; intro p. 5 "أبو الحسين أحمد بن فارس بن زكريا" |
| C4 | period "d. 395 AH / 1004–5 CE (other dates reported)" | S | Intro p. 9 "يختلفون فى تاريخ وفاته على أقوال خمسة" (360, 369, 375, 390); p. 10 "وأصح الأقوال … سنة (٣٩٥)" |
| C5 | kind "Root-meaning dictionary" | S | Preface p. 3 (مقاييس / أصول) |
| C6 | summary: names core sense(s), supports them with poetry, the Qur'an and earlier lexicons, sets aside misfits; the senses are his proposals | S | Preface pp. 3–5 ("استنبطناه"); entries kfr, qbl, Ebd; shadhdha formula (C27) |
| C7 | lede: a typical entry opens with a verdict of one, two or three *aṣl*, then evidence | S | My count: 1,033 of 1,323 displayed entries have أصل/أصول in the first 200 characters; أصلان in 170; three *uṣūl* in 35 |
| C8 | lede: a tenth-century philologist; persuasive in places, strained in others; frank about misfits | S | d. 395/1004–5, career mainly 4th/10th c. (intro pp. 5–10); qbl "يتمحل"; misfit formula. Evaluative, and framed as such |
| C9 | Worked mostly in Hamadhān, later at the Buyid court in Rayy, where he died | S | Intro p. 5 "استقر به فى معظم الأمر بمدينة همذان"; p. 6 "استدعى منها إلى بلاط آل بويه بمدينة الري"; p. 9 "قضى نحبه في مدينة الرى، أو المحمدية" (a quarter of Rayy, n. 1) |
| C10 | Hārūn lists five dates before settling on 395 [intro pp. 5–10] | S | As C4 |
| C11 | Preface quotation "إنّ للغة العرب مقاييسَ صحيحةً، وأصولاً تتفرّع منها فروع" and its translation | S | vol. 1 p. 3 (/47), verbatim; the translation is accurate |
| C12 | Earlier compilers never set out a single measure | S | p. 3 "ولم يُعربوا فى شئٍ من ذلك عن مقياس من تلك المقاييس، ولا أصل من الأصول" |
| C13 | Each section headed with its *aṣl*, so that a short statement covers the family | S | p. 3 "وقد صدَّرْنَا كلَّ فصلٍ بأصله الذى يتفرّع منه مسائلُه، حتّى تكونَ الجملةُ الموجَزةُ شاملةً للتَّفصيل" |
| C14 | Five books: *ʿAyn* ranked highest and noblest, two by Abū ʿUbayd, one by Ibn al-Sikkīt, the *Jamhara* | S | pp. 3–5: "فأعلاها وأشرفُهَا كتاب … الخليل"; "كتابا أبى عبيد … (غريب الحديث) و(مصنف الغريب)"; "(كتاب المنطق) … عن ابن السكيت"; "(الجمهرة)"; "فهذه الكتب الخمسة معتمدنا" |
| C15 | Everything else rests on these | S | p. 5 "وما بعدَ هذِه الكتبِ فمحمولٌ عليها، وراجعٌ إليها" |
| C16 | "The words are inherited; the analysis is his." | S | Interpretation of p. 5 "معتمَدُنَا فيما استنبَطناه من مقاييس اللغة" |
| C17 | "Nor did he aim at an exhaustive lexicon, as Ramzi Baalbaki notes." [p. 349] | **NQ** | **Not seen this round:** Google Books serves a reCAPTCHA, and I found no second copy or quotation. The idea itself has primary support in displayed entries. Ejz 4076: "وما تركنا في هذا كراهة التكرار راجع إلى الأصلين اللذين ذكرناهما". Ajr 1294: "وإنما لم نذكرها في قياس الباب لما قلناه أنها ليست من كلام البادية". The Baalbaki page attribution remains unconfirmed by me. |
| C18 | "A common verdict is *aṣl ṣaḥīḥ yadullu ʿalā…*" | S | Full formula "أصل صحيح يدل" in 200 of 1,323 displayed entries, so "common" is fair |
| C19 | Not every root gets a sense. mjs: "a word for which we know no measure; I think it is Persian". *al-majūs* at Q 22:17 | S | Entry 16616 "كلمة ما نعرف لها قياسا، وأظنها فارسية"; morphology مَجُوسَ at 22:17 |
| C20 | kfr excerpt and its translation, with [Q 57:20] | S | Entry 163 matches (validator). Hārūn vol. 5 p. 191 has the same text. Translation accurate. كُفَّارَ at 57:20 |
| C21 | kfr: concrete uses first (armour, ashes under dust, the sun casting its hand into *kāfir*); two glosses (sunset/sea) without choosing | S | Entry 163: "يقال لمن غطى درعه بثوب"; "رماد مكفور"; "فيقال إن الكافر مغيب الشمس. ويقال بل الكافر البحر", with no preference given; "ألقت ذكاء يمينها في كافر" |
| C22 | The Qur'an is cited for farmers, not for belief | S | 57:20 is the entry's only Qur'an citation |
| C23 | The *kufr*/covering link is in his own voice ("so called because") | S | "والكفر ضد الإيمان، سمي لأنه تغطية الحق", unattributed |
| C24 | *kafirāt* "perhaps" (*laʿalla*) | S | "ولعلها سميت كفرات لأنها متطامنة، كأن الجبال الشوامخ قد سترتها" |
| C25 | *al-Ṣāḥibī*: words moved "from their places to other places"; the Arabs knew of *kufr* only covering and concealment [pp. 44–45] | S | p. 44 (/50) "ونُقِلت من اللغة ألفاظ من مواضعَ إِلَى مواضع أخَر"; p. 45 (/51) "كَانَتْ لا تعرف من الكُفر إِلاَّ الغِطاء والسِّتْر" |
| C26 | That "unbelief" grew out of "covering" is Ibn Fāris's reconstruction | S | Correctly framed as his proposal |
| C27 | Recurring formula *wa-mimmā shadhdha ʿan hādhā l-bāb*, the "chapter" being the root's family | S | 29 displayed entries (e.g. hdy, qtl) |
| C28 | qbl excerpt and its translation | S | Entry 536 matches; "يتمحل" rendered "a strained case can be made"; "إلى الشذوذ أقرب" rendered "nearer to being an outlier". Accurate |
| C29 | *qabl*, the form the Qur'an uses most, is placed, tentatively, outside the family | S | Morphology: lemma *qabl* 242 occurrences; next highest 10. The hedge now matches the Arabic |
| C30 | Hārūn: Ibn Fāris hardly ever failed to find the shared sense [intro p. 23] | S | p. 23 (/21) "يردُّ مفرداتِ كلِّ مادة … إلى أصولها المعنوية المشتركة فلا يكاد يخطئه التوفيق" |
| C31 | "Baalbaki, by contrast, finds his proposed *uṣūl* 'frequently arbitrary and unconvincing'." [p. 351] | **NQ** | The phrase, the author and p. 351 are confirmed through Larsen, *JAS* 5 (2018), n. 21. Larsen applies the phrase to Ibn Fāris's **etymologies** generally. Whether Baalbaki says it of the *uṣūl* themselves, the derivations from them, or the *naḥt* analyses cannot be checked without p. 351. The object "his proposed *uṣūl*" is therefore an unverified narrowing. |
| C32 | Under each first letter: doubled roots, then three-letter roots, in an order of his own; most letters end with a longer-words chapter [intro pp. 42–44] | S | p. 42 "سلك طريقاً خاصَّا به"; p. 43 "قسم كل كتاب إلى أبواب ثلاثة أولها باب الثنائى المضاعف والمطابق، وثانيها أبواب الثلاثى … وثالثها بابُ ما جاء على أكثر من ثلاثة أحرفٍ"; p. 44 details the order. "Most letters" is more cautious than Hārūn's "every book", which is acceptable. |
| C33 | "doubled roots such as [[root:rdd\|none]] (a section missing from our copy)" | S | Hārūn vol. 2 p. 386 (/946) "[رد] الراء والدال أصلٌ واحدٌ مطّردٌ منقاس", within "باب الراء وما معها فى الثنائى والمطابق" (p. 372, /932); `root rdd` shows no Maqāyīs entry |
| C34 | "Most of what you see" is carved (*manḥūt*): two words taken, a new one carved keeping a share of each [vol. 1 pp. 328–29] | S | p. 328 "أنّ أكثر ما تراه منه منحوتٌ. ومعنى النَّحت أن تُؤخَذَ كلمتان وتُنْحَتَ منهما"; p. 329 "كلمةٌ تكون آخذةً منهما جميعاً بحَظٍّ" |
| C35 | The rest were "set down" with no room for measure | S | p. 329 "على ضربين: أحدهما المنحوت … والضَّرْب الآخر [الموضوع] وضعاً لا مجالَ له فى طُرق القياس" |
| C36 | *karbala* (slack-footed gait) carved from *rabl* (flabby flesh) and *kabl* (fetter) | S | vol. 5 p. 193 (/2245), and displayed inside kfr 163: "رخاوة في القدمين … منحوتة من كلمتين: من ربل وكبل. أما ربل فاسترخاء اللحم … وأما الكبل فالقيد" |
| C37 | Elsewhere he names a third kind, three-letter words with letters added [vol. 2 p. 509] | S | p. 509 (/1069) "وهذا شئ يقِلُّ فى كتاب الراء، والذى جاء منه فمنحوتٌ أو مزيدٌ فيه"; also jvm 9425 "ومنه ما أصله كلمة واحدة وقد ألحق بالرباعي والخماسي بزيادة تدخله" |
| C38 | *kanfalīla* (bushy beard) = *kafl* (gathering), enlarged | S | vol. 5 p. 193 / kfr 163: "اللحية الضخمة. وهذا مما زيدت فيه النون … وهو من الكفل، وهو جمع الشيء" |
| C39 | *kibrīt* "is not Arabic"; "I do not know how the scholars accept this and its like" | S | kfr 163 (kāf longer-words chapter): "(الكبريت): ليس بعربي"; after *kundush*: "وما أدري كيف يقبل العلماء هذا وأشباهه" |
| C40 | Ebd excerpt and its translation; "(The bracketed word is the editor's.)" | S | Entry 519 matches. Hārūn vol. 4 p. 205 (/1746) "و [الأول] من ذينك". Intro p. 46 (/44): he puts his supplements "بين معكفى الزيادة". Translation accurate |
| C41 | First *aṣl*: *ʿabd* and the well-trodden road; second: thick strong cloth and *ʿabad* (indignant disdain) | S | Entry 519: "الطريق المعبد، وهو المسلوك المذلل"; "ثوب له عبدة، إذا كان صفيقا قويا"; "العبد، مثل الأنف والحمية" |
| C42 | "al-Khalīl said" introduces the *ʿibād* / *ʿabīd* distinction | S | Entry 519 "قال الخليل: إلا أن العامة اجتمعوا على تفرقة ما بين عباد الله والعبيد المملوكين" |
| C43 | Where a quotation ends is not marked. "We have not heard…" reads "I have not heard" in the *ʿAyn*, which has much of the rest, often closely worded, and no shared-sense statement | S | Maqāyīs "ولم نسمعهم يشتقون منه فعلا". *ʿAyn* 372 "ولم أسمعهم يشتقون منه فعلاً"; it shares *muʿabbad*/tar, Ṭarafa's hemistich, the road, *ʿabad*, 43:81 and ʿAlī's saying, and has no *aṣl* statement |
| C44 | Q 43:81 filed under the second sense with *wa-fussira*: "the first to be angered by this and to disdain it" | S | Entry 519 "وفسر قوله تعالى … أي أول من غضب عن هذا وأنف من قوله"; عَٰبِدِينَ at 43:81 |
| C45 | The *ʿAyn* gives that reading and adds one where *ʿābidīn* = worshippers | S | *ʿAyn* 372 "أي: الأنفين من هذا القول … ويقال … فلست بأوّل من عَبَدَ الله مِنْ أهلِ مكّة" |
| C46 | The *Maqāyīs* gives only the reading that serves its second *aṣl* | S | Entry 519 has one reading only |
| C47 | An *aṣl* is his inference; his Qur'anic citations are chosen for his scheme; weigh context | S | Interpretation, consistent with "استنبطناه" (p. 5) and the entries |
| C48 | Older material: pre-Islamic poets such as Ṭarafa and al-Nābigha; philologists of the 8th–10th c. | S | Ṭarafa in Ebd and rsl; al-Nābigha in Amn, Aty, Ahl, Edw ("قال النابغة"). The five sources run from al-Khalīl to Ibn Durayd (d. 321/933; intro p. 23 n. 1) |
| C49 | fqh: "every knowledge of a thing", "then" reserved for knowledge of the religious law | S | Entry 4838 "وكل علم بشيء فهو فقه … ثم اختص بذلك علم الشريعة" |
| C50 | Hārūn edited from the single manuscript he could find; found no one besides Yāqūt who mentions the book; scholars noticed it only recently [intro pp. 39–40] | S | p. 39 (/37) "ولم أجدْ أحداً غير ياقوت يذكر هذا الكتاب لابن فارس"; p. 40 (/38) "لم يسترع انتباه العُلماء إلا منذ عهد قريب … لم أجِد أمامى منه إلا نُسخة واحِدة" |
| C51 | In several displayed entries, the *Tāj* cites "Ibn Fāris in the *Maqāyīs*" | S | *Tāj* grep: Sdq "وأنشد ابن فارس في المقاييس"; slT "وتابعه ابن فارس في المقاييس"; xDE "وابن فارس في المقاييس"; $gl "وقال ابن فارس في المقاييس"; dlk "قال ابن فارس في المقاييس"; bhl "كذا في المجمل والمقاييس" |
| C52 | Under dlk the *Tāj* repeats, almost word for word, the reflection closing the Maqāyīs entry: wherever dāl and lām are joined by a third letter, the word points to movement, coming and going | S | Maqāyīs 17840: "قال أحمد بن فارس: إن لله تعالى في كل شيء سرا ولطيفة. وقد تأملت في هذا الباب … إلا وهي تدل على حركة ومجيء، وذهاب وزوال من مكان إلى مكان". *Tāj* 17838: the same text, without تعالى and with "يعني باب الدال مع اللام" added. Both displayed (API) |
| C53 | "It had been read, though." | S | Inference from C51–C52; al-Zabīdī (or a source he copies) quotes it. See suggestion S2 on the al-Ṣaghānī context |
| C54 | Stored text follows Hārūn's edition, including his corrections and square-bracketed words | S | Ebd stored ذينك (Hārūn p. 205 n. 2: ms ذلك); kfr stored فهم (Hārūn vol. 5 p. 192 n. 4: ms فهو); [الأول], [فإن كانت] present; intro p. 46 on brackets |
| C55 | His footnotes identifying unnamed poets are not included | S | Intro p. 45 "عُنيت أيضا بنسبة الأشعار والأرجاز المهملة إلى قائليها"; kfr footnotes (Labīd, Thaʿlaba b. Ṣuʿayr, al-ʿAjjāj) are absent from stored entry 163 |
| C56 | Full vowels, bracketed verse references and the vowelled heading (كَفَرَ) are not in Shamela's text | S | Shamela vol. 5 p. 191: heading "[كفر]", partial vowels, "﴿أَعْجَبَ اَلْكُفّارَ نَباتُهُ﴾" with no reference; stored entry has "(كَفَرَ)", full vowels and "[الحديد: 20]" |
| C57 | 1,323 roots, covering every letter | S | 1,323 displayed; 28 distinct first letters |
| C58 | The doubled-root section opening each letter is missing; no entry for rbb or rdd, though the book treats both [vol. 2 pp. 381, 386] | S | Of the displayed roots, the only one with 2nd = 3rd radical is Ayy (a weak root), plus one quadriliteral, zxrf. `root rbb` / `root rdd`: no Maqāyīs. Hārūn vol. 2 p. 381 "[رب] الراء والباء يدلُّ على أُصولٍ"; p. 386 "[رد]" |
| C59 | Entries run from a single line to over a thousand words | S | qvA 7 words, Hsd 8; Elw 1,127, jvm 1,209, Eqb 1,277 |
| C60 | In several letters the source copy runs the closing chapter into the preceding root | S | Six entries: kfr, jvm, SrT, r*l, nml, srd (grep "مما زيدت فيه / أكثر من ثلاثة أحرف") |
| C61 | The end of kfr, from *kanfalīla* on, belongs to that chapter | S | Hārūn vol. 5 p. 193 opens "[باب ما جاء من كلام العرب على أكثر من ثلاثة أحرف أوله كاف] من ذلك (الكنفليلة)" |
| C62 | Most of jvm; the heading surfaces mid-verse; the list breaks off | S | Entry 9425 "قال: باب ما جاء من كلام العرب على أكثر من ثلاثة أحرف أوله جيم بنانتين وجذمورا…"; ends "ومما وضع وضعا ولم أعرف له اشتقاقا:" |
| C63 | Source harun-ed (2nd ed., 6 vols, Cairo: al-Bābī al-Ḥalabī, 1969–72; Shamela) | S | Shamela card |
| C64 | Source baalbaki: "pp. 348–56 (section on *al-Maqāyīs* and *al-Mujmal*); consulted in the Google Books preview", URL books.google.ca id cme7AwAAQBAJ | **NQ** | The book is real (Brill title page 25514: 2014, ch. 3 pp. 279–401). The 348–56 range, the section title and the Google Books id could not be opened (CAPTCHA). Only pp. 349 and 351 are cited now, and p. 351 is confirmed only through Larsen. |
| C65 | Source sahibi (Bayḍūn 1997, "Bāb al-asbāb al-islāmiyya", pp. 44–45) | S | Shamela card and page titles |
| C66 | Source hawramani: the source of our text; names no edition | S | Page opens (200); no editor or edition named |
| C67 | Every root link leads to a displayed entry that supports the sentence (mjs, kfr, qbl, Ebd ×2, fqh, dlk ×2, jvm); the none-links are explained | S | Validator: 13 links (9 pairs), all resolve. Entries read above. The rbb and rdd none-links are explained in the same sentence |

**Totals:** 67 claims: 64 supported, 3 need qualification (C17, C31, C64), 0 unsupported.

## Previously flagged points (r2), re-checked

- **C18 "typically" → "A common verdict".** Fixed. Supported by the count above.
- **C19 Baalbaki counts (p. 350).** Deleted. It does not reappear anywhere.
- **C17 abridgement clause.** Deleted. The remaining sentence is my C17. It is still unverified by me.
- **C32b "disliked far-fetched connections".** Deleted. The remaining phrase is my C31. The phrase and page are confirmed, but the object needs qualification.
- **C51 Baalbaki pp. 355–56.** Deleted. The new *Tāj* passage (C51–C53) and the Hārūn rewording (C50) are verified from displayed entries and Shamela.
- **B1 doubled roots.** Fixed in the body (C33) and in onOurSite (C58). Verified.
- **B2 *qabl* hedge.** Fixed (C29).
- **B3 "Elsewhere he names a third kind".** Fixed (C37); vol. 2 p. 509 was checked.

## Flagged items and fixes

- **C17 "Nor did he aim at an exhaustive lexicon, as Ramzi Baalbaki notes. [^baalbaki|p. 349]"**
  - I could not open p. 349 (reCAPTCHA) and found no other copy.
  - Fix, either of:
    - (a) Keep it only after a person confirms p. 349 in an ordinary browser.
    - (b) Replace it with primary evidence the site displays. Suggested wording: "Nor did he try to record everything: under [[root:Ejz|ibn-faris-maqayis-al-lugha|ع ج ز]] he says he has left words out 'for fear of repetition' (our translation)." Ejz 4076 reads "وما تركنا في هذا كراهة التكرار".
  - Either way, drop the Baalbaki attribution unless p. 349 is confirmed.
- **C31 "finds his proposed *uṣūl* 'frequently arbitrary and unconvincing' [^baalbaki|p. 351]"**
  - The only evidence I could open (Larsen 2018, n. 21) applies the phrase to Ibn Fāris's etymologies generally.
  - Fix: "Baalbaki, by contrast, calls his derivations 'frequently arbitrary and unconvincing'.[^baalbaki|p. 351]"
  - Unless a person confirms that p. 351 says it of the *uṣūl*, also add Larsen as a source through which the quotation was checked. Suggested entry:
    - id `larsen`, kind scholarship.
    - Citation: "David Larsen, 'Meaning and Captivity in Classical Arabic Philology', *Journal of Abbasid Studies* 5 (2018), 177–228, n. 21 (quoting Baalbaki, p. 351)."
    - URL: https://brill.com/view/journals/jas/5/1-2/article-p177_7.xml
  - The page span 177–228 is from the article page's citation metadata (citation_firstpage / citation_lastpage).
- **C64 Baalbaki source entry**
  - The page range 348–56, the section title and "consulted in the Google Books preview" cannot be confirmed this round.
  - Fix: narrow the citation to the pages actually cited: "pp. 349, 351".
  - Use the publisher's page https://brill.com/display/title/25514 as the URL. It opens and confirms the book. The Google Books link serves a CAPTCHA to automated checks and could not be tied to this book this round.
  - If C17 is replaced as in (b), and C31 is sourced through Larsen, reword the entry to reflect how the book was actually consulted.

## Brief issues

- **B1 (must-fix, carried over): do not mark the page verified until the last Baalbaki item is settled.** No round has independently re-opened p. 349. Either a person confirms it, or apply fix C17(b).
- **S1 (suggestion): onOurSite length.** It is 192 words against FORMAT's ≈60–150. Possible trims:
  - "Entries run from a single line to over a thousand words" could go.
  - The Shamela formatting sentence could be shortened, e.g. "Vowel marks, verse references and the vowelled heading such as (كَفَرَ) were added by the source site."
- **S2 (suggestion): *Tāj* citations may be second-hand.** In two of the six *Tāj* passages, al-Ṣaghānī is named beside the Maqāyīs citation:
  - slT: "نبه عليه الصاغاني في العباب";
  - xDE: "قال الصاغاني".
  - "It had been read, though" is still true. If the author wants precision, "Later lexicographers did cite it, though" avoids implying that al-Zabīdī had the book in hand.
- **S3 (suggestion): Hārūn and Baalbaki are not simply opposed.** Hārūn himself notes, intro p. 39, that Ibn Fāris "لا يعتمد اطراد القياس في جميع مواد اللغة، بل هو ينبه على كثير من المواد التى لا يطرد فيها القياس". A clause could round out the "hardly ever failed" quotation, but the essay already shows misfits, so this is optional.
- **Tone, labels and layout**
  - No generic praise, ranking or "most important" claims. The site's default-open choice is not presented as a ranking.
  - Translations are labelled.
  - Every root mention is a root link.
  - No forced single-origin narrative: no-*aṣl*, one-*aṣl*, two-*aṣl*, outlier and foreign-word cases are all shown.
  - Lede 82 words, summary 41 words, lede + body 1,085 words: within limits.

## URL check

| URL | Result |
|---|---|
| https://shamela.ws/book/21710 | Opens. Hārūn 2nd ed., page-matched. OK |
| https://books.google.ca/books?id=cme7AwAAQBAJ&pg=PA349 | Redirects to google.com/sorry (reCAPTCHA) for the browser pane, curl and WebFetch. **Could not confirm it is Baalbaki's book or that p. 349 is previewable.** Replace with or add https://brill.com/display/title/25514 (opens; Brill 2014) |
| https://shamela.ws/book/9977/50 | Opens *al-Ṣāḥibī* p. 44, where the chapter begins. OK |
| https://arabiclexicon.hawramani.com/ibn-faris-maqayis-al-lugha/ | 200; correct page; no edition named. OK |

All four listed sources are cited in the text. None is listed but unused.

## Validator

`node scripts/validate-dictionary-guides.mjs maqayis-al-lugha` passed ("1/1 guides pass"):
- 13 root links (9 distinct root/dictionary pairs);
- 3 excerpts, all valid;
- 1,085 words (lede + body, excluding excerpts);
- example roots: mjs, kfr, qbl, Ebd, fqh, dlk, jvm.

It printed 3 warnings, one for each `none` link (rdd in the body; rbb and rdd in onOurSite). Each is explained in its sentence, as FORMAT requires.

## Site-data issues

1. **Doubled roots never collected.**
   - Of the displayed Maqāyīs roots, none is a doubled (2nd = 3rd radical) root, apart from the weak root Ayy.
   - hawramani's own contents page lists them (أَبَّ, أَتَّ, أَثَّ …) on two-letter pages that the scrape did not fetch.
   - This removes Maqāyīs entries for rabb, radd, ḥaqq, ẓann, ḥubb, madd and others.
2. **Longer-words chapters merged into the preceding root.**
   - Six displayed entries carry a letter's closing chapter: kfr, jvm, SrT, r*l, nml, srd.
   - The kfr English renderings mislabel this material:
     - faithful translation, line 28: "falling under the k-f section";
     - harmonized text: "files under k-f".
   - It belongs to the chapter for the whole letter kāf (Hārūn vol. 5 p. 193).
3. **Stored labels are correct.** Author "Ibn Fāris" and death year 1004 match (395 AH ≈ 1004–5 CE).
