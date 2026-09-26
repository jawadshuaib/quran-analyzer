# Maqāyīs al-Lugha: verification, round 4

Independent fact-check of `roots/frontend/src/content/dictionary-guides/guides/maqayis-al-lugha.ts` (checked 2026-09-26).

**What I read:**
- I did not open research-notes.md or any revision file.
- I read verification-r3.md only for the list of earlier flags. None of its verdicts counts as evidence here. Every verdict below comes from a source I opened this round.

## Sources checked directly this round

- **Hārūn's edition on Shamela (book 21710).** I downloaded each page with curl and read its volume and page number from the page title.
  - Book card: "تحقيق وضبط: عبد السلام محمد هارون"; al-Bābī al-Ḥalabī; 2nd ed. 1389–92 AH / 1969–72; 6 vols; "ترقيم الكتاب موافق للمطبوع".
  - Editor's introduction:
    - p. 5 (/3), p. 6 (/4), p. 9 (/7), p. 10 (/8), p. 23 (/21);
    - p. 39 (/37), p. 40 (/38), p. 42 (/40), p. 43 (/41), p. 44 (/42), p. 46 (/44).
  - Author's preface: vol. 1 pp. 3–5 (/47–/49).
  - Entries:
    - vol. 1 pp. 328–29 (/372–/373);
    - vol. 2 p. 381 (/941), p. 386 (/946), p. 509 (/1069);
    - vol. 4 p. 205 (/1746);
    - vol. 5 p. 191 (/2243), p. 193 (/2245).
- **al-Ṣāḥibī on Shamela (book 9977):**
  - book card (Muḥammad ʿAlī Bayḍūn, 1st ed. 1418/1997, page-matched);
  - pp. 44 (/50) and 45 (/51).
- **hawramani** (https://arabiclexicon.hawramani.com/ibn-faris-maqayis-al-lugha/)
  - It returns 200.
  - It names the five source books.
  - It names no editor or edition: "Hārūn", "هارون" and "تحقيق" are all absent.
- **Displayed entries**, read with `_dict_guide_tool.py entry` and read-only queries on `quran.db`:
  - Maqāyīs: mjs 16616, kfr 163, qbl 536, Ebd 519, fqh 4838, dlk 17840, jvm 9425.
  - *ʿAyn*: Ebd 372.
  - *Tāj*: dlk 17838, plus a grep of all displayed *Tāj* entries for المقاييس.
  - Counts across all 1,323 displayed Maqāyīs entries.
  - `morphology` for Q 22:17, 57:20, 43:81 and for root qbl.
- **Local API.**
  - `/api/root/Ebd/dictionaries` lists the *ʿAyn* and the Maqāyīs.
  - `/api/root/dlk/dictionaries` lists the Maqāyīs and the *Tāj*.
- **Poets' dates.** en.wikipedia.org "Tarafa" (c. 543–c. 569, "pre-Islamic") and "Al-Nabigha" (c. 535–c. 604, "one of the last pre-Islamic Arabian poets").
  - These are general reference only.
  - The essay makes only the uncontroversial claim that both are pre-Islamic.
  - Britannica returned 403.

Verdicts: S = supported, NQ = needs qualification, U = unsupported.

## Claims table

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Maqāyīs al-Lugha* / مقاييس اللغة | S | Shamela card "معجم مقاييس اللغة"; preface vol. 1 p. 3 "هذا كتاب المقاييس فى اللغة" |
| C2 | titleGloss "The Measures of Language" | S | Plain rendering; preface "إن للغة العرب مقاييس صحيحة" |
| C3 | Ibn Fāris / Abū l-Ḥusayn Aḥmad ibn Fāris ibn Zakariyyāʾ / ابن فارس | S | Shamela card "أبو الحسين أحمد بن فارس بن زكريا (ت ٣٩٥ هـ)"; intro p. 5 (Thaʿālibī quoted) |
| C4 | period "d. 395 AH / 1004–5 CE (other dates reported)" | S | Intro p. 9 "يختلفون فى تاريخ وفاته على أقوال خمسة" (360, 369, 375, 390); p. 10 "وأصح الأقوال … سنة (٣٩٥)" |
| C5 | kind "Root-meaning dictionary" | S | Preface p. 3 (مقاييس / أصول); entries |
| C6 | summary: names core sense(s), supports them with poetry, the Qur'an and earlier lexicons, sets aside misfits; the senses are his proposals | S | Preface pp. 3–5 ("فيما استنبطناه"); kfr, qbl, Ebd, mjs; "قال الخليل" (Ebd), "قال ابن دريد" (qbl) |
| C7 | lede: a typical entry opens with a verdict of one, two or three *aṣl* | S | My count: 1,033 of 1,323 displayed entries have أصل/أصول in the first 200 characters. أصلان appears in 170. ثلاثة أصول appears in 35 (e.g. Sbr, ArD, lqy) |
| C8 | lede: a tenth-century philologist; persuasive in places, strained in others; frank about misfits | S | Intro pp. 5–10; qbl "يتمحل"; mjs; the shadhdha formula. Evaluation is framed as the essay's own |
| C9 | Worked mostly in Hamadhān, later at the Buyid court in Rayy, where he died | S | p. 5 "استقر به فى معظم الأمر بمدينة همذان"; p. 6 "استدعى منها إلى بلاط آل بويه بمدينة الري"; p. 9 "قضى نحبه في مدينة الرى، أو المحمدية" (n. 1: a quarter of Rayy) |
| C10 | Hārūn lists five dates before settling on 395 [intro pp. 5–10] | S | pp. 9–10. The five reported dates include 395; see suggestion S4 on wording |
| C11 | Preface quotation إنّ للغة العرب مقاييسَ صحيحةً، وأصولاً تتفرّع منها فروع and translation | S | vol. 1 p. 3 (/47), verbatim; the translation is accurate |
| C12 | Earlier compilers never set out a single one of these measures | S | p. 3 "ولم يعربوا فى شئ من ذلك عن مقياس من تلك المقاييس، ولا أصل من الأصول" |
| C13 | Each section headed with its *aṣl*, so that a short statement covers the family | S | p. 3 "وقد صدرنا كل فصل بأصله الذى يتفرع منه مسائله، حتى تكون الجملة الموجزة شاملة للتفصيل" |
| C14 | Five books: *ʿAyn* ranked highest and noblest, two by Abū ʿUbayd, one by Ibn al-Sikkīt, the *Jamhara* | S | p. 3 "فأعلاها وأشرفها كتاب … الخليل … (كتاب العين)"; p. 4 "كتابا أبى عبيد فى (غريب الحديث)، و(مصنف الغريب)"; p. 5 "(كتاب المنطق) … عن ابن السكيت"; "(الجمهرة)"; "فهذه الكتب الخمسة معتمدنا" |
| C15 | Everything else rests on these | S | p. 5 "وما بعد هذه الكتب فمحمول عليها، وراجع إليها" |
| C16 | "The words are inherited; the analysis is his." | S | Interpretation of p. 5 "معتمدنا فيما استنبطناه من مقاييس اللغة", with p. 3's complaint that no predecessor stated any measure |
| C17 | A common verdict is *aṣl ṣaḥīḥ yadullu ʿalā…* | S | "أصل صحيح يدل" in 200 of 1,323 displayed entries |
| C18 | mjs: "a word for which we know no measure; I think it is Persian"; *al-majūs* Q 22:17 | S | Entry 16616 "كلمة ما نعرف لها قياسا، وأظنها فارسية"; morphology مَجُوسَ at 22:17 (the root's only occurrence) |
| C19 | kfr excerpt and translation, [Q 57:20] | S | Entry 163 (validator passes); Hārūn vol. 5 p. 191 has the same text. Translation accurate; كُفَّارَ at 57:20 |
| C20 | kfr: concrete uses first (armour, ashes, the sun "casts its hand into *kāfir*"); two glosses (sunset/sea) without choosing | S | Entry 163: "لمن غطى درعه بثوب"; "فيقال إن الكافر مغيب الشمس. ويقال بل الكافر البحر", with no preference; "ألقت ذكاء يمينها في كافر"; "رماد مكفور: سفت الريح التراب عليه". *kufr* follows all of these |
| C21 | The Qur'an is cited for farmers, not for belief | S | 57:20 is the entry's only Qur'an citation |
| C22 | The *kufr*/covering link is in his own voice ("so called because") | S | "والكفر ضد الإيمان، سمي لأنه تغطية الحق", unattributed |
| C23 | *kafirāt* "perhaps" (*laʿalla*) because the high peaks seem to hide them | S | "ولعلها سميت كفرات لأنها متطامنة، كأن الجبال الشوامخ قد سترتها" |
| C24 | *al-Ṣāḥibī*: words moved "from their places to other places"; the Arabs knew of *kufr* only covering and concealment [pp. 44–45] | S | p. 44 "ونقلت من اللغة ألفاظ من مواضع إلى مواضع أخر"; p. 45 "وكذلك كانت لا تعرف من الكفر إلا الغطاء والستر" |
| C25 | That "unbelief" grew out of "covering" is Ibn Fāris's reconstruction | S | Framed as his proposal. The essay does not endorse it |
| C26 | Recurring formula *wa-mimmā shadhdha ʿan hādhā l-bāb*; "chapter" = the root's family | S | "ومما شذ عن هذا الباب" in 29 displayed entries (hdy, qtl …) |
| C27 | qbl excerpt and translation | S | Entry 536 matches. "يتمحل" is rendered "a strained case can be made"; "إلى الشذوذ أقرب" is rendered "nearer to being an outlier". Accurate |
| C28 | *qabl*, the form the Qur'an uses most, placed tentatively outside the family | S | morphology: lemma *qabol* 242 occurrences; next highest 10. "يمكن أن يكون شاذا" matches "tentatively" |
| C29 | Hārūn: Ibn Fāris hardly ever failed to find the shared sense [intro p. 23] | S | p. 23 "يرد مفردات كل مادة … إلى أصولها المعنوية المشتركة فلا يكاد يخطئه التوفيق". See S3 on balance |
| C30 | Under each first letter: doubled roots, then three-letter roots, in an order of his own; most letters end with a longer-words chapter [intro pp. 42–44] | S | p. 42 "سلك طريقا خاصا به"; p. 43 "قسم كل كتاب إلى أبواب ثلاثة أولها باب الثنائى المضاعف والمطابق، وثانيها أبواب الثلاثى … وثالثها باب ما جاء على أكثر من ثلاثة أحرف"; p. 44 details the order ("وهو بدع") |
| C31 | Doubled roots such as rdd (none-link), "a section missing from our copy" | S | Hārūn vol. 2 p. 386 "[رد] الراء والدال أصل واحد مطرد منقاس", among two-letter headings ([رخ], [رد]); `root rdd` lists no Maqāyīs entry |
| C32 | "Most of what you see" is carved (*manḥūt*): two words taken, a new one carved keeping a share of each [vol. 1 pp. 328–29] | S | p. 328 "أن أكثر ما تراه منه منحوت. ومعنى النحت أن تؤخذ كلمتان وتنحت منهما"; p. 329 "كلمة تكون آخذة منهما جميعا بحظ" |
| C33 | The rest were "set down" with no room for measure | S | p. 329 "والضرب الآخر [الموضوع] وضعا لا مجال له فى طرق القياس" |
| C34 | *karbala* from *rabl* (flabby flesh) and *kabl* (fetter) | S | vol. 5 p. 193; displayed inside kfr 163: "منحوتة من كلمتين: من ربل وكبل. أما ربل فاسترخاء اللحم … وأما الكبل فالقيد" |
| C35 | Elsewhere he names a third kind, three-letter words with letters added [vol. 2 p. 509] | S | p. 509 "والذى جاء منه فمنحوت أو مزيد فيه"; displayed jvm 9425 lists three kinds: "ما نحت من كلمتين … ما أصله كلمة واحدة وقد ألحق بالرباعي والخماسي بزيادة تدخله … ما يوضع كذا وضعا" |
| C36 | *kanfalīla* (bushy beard) = *kafl* (gathering), enlarged | S | p. 193 / kfr 163: "اللحية الضخمة. وهذا مما زيدت فيه النون … وهو من الكفل، وهو جمع الشيء" |
| C37 | *kibrīt* "is not Arabic"; "I do not know how the scholars accept this and its like" | S | kfr 163: "(الكبريت): ليس بعربي"; "وما أدري كيف يقبل العلماء هذا وأشباهه" |
| C38 | Ebd excerpt and translation; "(The bracketed word is the editor's.)" | S | Entry 519 matches. Hārūn vol. 4 p. 205 "و [الأول] من ذينك (٢)", n. 2: ms "ذلك". Intro p. 46: supplements go "بين معكفى الزيادة". Translation accurate |
| C39 | First *aṣl*: *ʿabd* and the well-trodden road. Second: thick strong cloth and *ʿabad* (indignant disdain) | S | Entry 519: "فالأول العبد، وهو المملوك"; "الطريق المعبد، وهو المسلوك المذلل"; "ثوب له عبدة، إذا كان صفيقا قويا"; "العبد، مثل الأنف والحمية" |
| C40 | "al-Khalīl said" introduces the *ʿibād* / *ʿabīd* distinction | S | "قال الخليل: إلا أن العامة اجتمعوا على تفرقة ما بين عباد الله والعبيد المملوكين" |
| C41 | Quotation end unmarked. "We have not heard …" reads "I have not heard" in the *ʿAyn*, where much of the rest appears, often closely worded, with no shared-sense statement | S | Maqāyīs "ولم نسمعهم يشتقون منه فعلا". *ʿAyn* 372 "ولم أسمعهم يشتقون منه فعلاً". The *ʿAyn* shares the tar-smeared camel, Ṭarafa's hemistich, the road, *ʿabad*, 43:81 and ʿAlī's saying. It has no aṣl statement |
| C42 | Q 43:81 filed under the second sense with *wa-fussira*: "the first to be angered by this and to disdain it" | S | "وفسر قوله تعالى … أي أول من غضب عن هذا وأنف من قوله"; عَٰبِدِينَ at 43:81 |
| C43 | The *ʿAyn* gives that reading and adds one where *ʿābidīn* = worshippers | S | *ʿAyn* 372: "أي: الأنفين من هذا القول … فلست بأوّل من عَبَدَ الله مِنْ أهلِ مكّة" |
| C44 | The *Maqāyīs* gives only the reading that serves its second *aṣl* | S | Entry 519 gives one reading only |
| C45 | An *aṣl* is his inference; Qur'anic citations chosen for his scheme; weigh context | S | Interpretation consistent with "استنبطناه" (p. 5) and the entries above |
| C46 | Older material: pre-Islamic poets such as Ṭarafa and al-Nābigha; philologists of the 8th–10th c. | S | Displayed entries: "قال طرفة" in rsl and Ebd; "قال النابغة" in Amn, Aty and others. The five sources run from al-Khalīl to Ibn Durayd (d. 321/933; intro p. 23 n. 1). Poets' dates: Wikipedia (general reference) |
| C47 | fqh: "every knowledge of a thing", "then" reserved for the religious law | S | Entry 4838 "وكل علم بشيء فهو فقه … ثم اختص بذلك علم الشريعة" |
| C48 | Hārūn edited from the single manuscript he could find; no one but Yāqūt mentions the book; noticed only recently [intro pp. 39–40] | S | p. 39 "ولم أجد أحدا غير ياقوت يذكر هذا الكتاب لابن فارس"; p. 40 "لم يسترع انتباه العلماء إلا منذ عهد قريب … لم أجد أمامى منه إلا نسخة واحدة" |
| C49 | "It had been read, though." In several displayed entries the *Tāj* cites "Ibn Fāris in the *Maqāyīs*" | S | *Tāj* grep, six displayed entries: Sdq, slT, xDE, $gl and dlk ("ابن فارس في المقاييس"); bhl ("المجمل والمقاييس"). See S2 on al-Ṣaghānī |
| C50 | Under dlk the *Tāj* repeats almost word for word the reflection closing the Maqāyīs entry: dāl + lām + a third letter points to movement, coming and going | S | Maqāyīs 17840 "قال أحمد بن فارس: إن لله تعالى في كل شيء سرا ولطيفة … إلا وهي تدل على حركة ومجيء، وذهاب وزوال". *Tāj* 17838 has the same, adding "يعني باب الدال مع اللام". Both displayed (API) |
| C51 | onOurSite: stored text follows Hārūn's edition, with his corrections and square-bracketed supplements | S | Ebd has ذينك (Hārūn's correction, p. 205 n. 2); kfr has "فتذكرا ثقلا رثيدا" (Hārūn's correction of ms "فيذكر أهلا", vol. 5 p. 191 n. 4); [الأول] and qbl [فإن كانت] are present. One minor variant: stored "ويقال للزارع", Shamela "ويقال الزارع". See S5 |
| C52 | His footnotes identifying unnamed poets not included | S | vol. 5 p. 191 nn. 2, 3, 5 (Labīd, Thaʿlaba b. Ṣuʿayr, Manẓūr b. Marthad) are absent from stored entry 163 |
| C53 | Full vowels, bracketed verse references and the vowelled heading (كَفَرَ) are not in Shamela's text | S | Shamela p. 191: heading "[كفر]", partial vowels ("أصلٌ صحيحٌ يدلُّ"), "﴿أعجب الكفار نباته﴾" with no reference. Stored text has "(كَفَرَ)", full vowels and "[الحديد: 20]" |
| C54 | 1,323 roots, covering every letter | S | 1,323 displayed; 28 distinct first letters |
| C55 | Doubled-root section missing; no entry for rbb or rdd, though the book treats both [vol. 2 pp. 381, 386] | S | The only displayed root with 2nd = 3rd radical is Ayy. `root rbb` / `root rdd` list no Maqāyīs entry. p. 381 "[رب] الراء والباء يدل على أصول"; p. 386 "[رد]" |
| C56 | Entries run from a single line to over a thousand words | S | qvA 7 words, Hsd 8; Elq 1,081, Elw 1,127, jvm 1,209, Eqb 1,277 |
| C57 | In several letters the source copy runs the closing chapter into the root printed just before it | S | Six displayed entries contain it: kfr, SrT, jvm, r*l, nml, srd |
| C58 | End of kfr, from *kanfalīla* on, belongs to that chapter | S | Hārūn vol. 5 p. 193 opens "[باب ما جاء من كلام العرب على أكثر من ثلاثة أحرف أوله كاف] من ذلك (الكنفليلة)" |
| C59 | Most of jvm; heading surfaces mid-verse; list breaks off | S | jvm 9425: 30 words of root material, then 1,179 words of the chapter. "قال: باب ما جاء من كلام العرب على أكثر من ثلاثة أحرف أوله جيم بنانتين وجذمورا …". Ends "ومما وضع وضعا ولم أعرف له اشتقاقا:" |
| C60 | Source harun-ed (2nd ed., 6 vols, Cairo: al-Bābī al-Ḥalabī, 1969–72; Shamela page-matched) | S | Shamela card as above |
| C61 | Source sahibi (Bayḍūn 1997, "Bāb al-asbāb al-islāmiyya", pp. 44–45) | S | Shamela card and page titles ("باب الأسباب الإسلامية", ص44–45) |
| C62 | Source hawramani: source of our text; names no edition | S | Page opens (200); no editor or edition named; source_url of every checked entry points there |
| C63 | Every root and guide link resolves and supports its sentence (mjs, kfr ×2, qbl, Ebd ×2 incl. *ʿAyn*, fqh, dlk ×2 incl. *Tāj*, jvm; guide links kitab-al-ayn, taj-al-arus); none-links explained | S | Validator: 13 root links, 9 pairs, all resolve. Registry has both guide slugs. The rdd (body) and rbb/rdd (onOurSite) none-links are explained in their sentences |

**Totals:** 63 claims: 63 supported, 0 need qualification, 0 unsupported.

## Previously flagged points (r3), re-checked

- **C17 (r3): Baalbaki p. 349, "Nor did he aim at an exhaustive lexicon".** Deleted. The paragraph now ends "The words are inherited; the analysis is his." (C16, supported). Resolved.
- **C31 (r3): Baalbaki p. 351, "frequently arbitrary and unconvincing".** Deleted. The replacement is "Hārūn thought Ibn Fāris hardly ever failed to find the shared sense; entries like this one let a reader test that judgment."
  - Its factual half is C29 (supported, p. 23).
  - The second half is reading advice and states no fact.
  - Resolved.
- **C64 (r3): Baalbaki source entry.** Removed.
  - Nothing cites `baalbaki`: a grep for baalbaki, larsen and google finds nothing.
  - The only citation ids used are harun-ed (11 citations), sahibi (1) and hawramani (1).
  - Resolved.
- **r3 must-fix B1 (don't mark verified until Baalbaki is settled).** No Baalbaki citation remains, so nothing in the text now blocks `lastVerified`.
- **r3 suggestions S1–S3.** Not applied; they remain suggestions (below).

No new factual claims were introduced in the revision. I checked the one changed sentence (C29 plus the reading-advice clause) above.

## Flagged items and fixes

None. No claim needs qualification or is unsupported.

## Brief issues

- **S1 (suggestion, carried over): onOurSite length.** It is about 196 words (raw split) against FORMAT's ≈60–150. Possible trims:
  - Drop "Entries run from a single line to over a thousand words."
  - Compress the Shamela formatting sentence.
- **S2 (suggestion, carried over): the *Tāj* citations may be second-hand.**
  - In slT, "Ibn Fāris in the Maqāyīs" sits beside "وقد نبه عليه الصاغاني في العباب". In xDE it sits beside "قال الصاغاني".
  - "It had been read, though" is still true (by al-Ṣaghānī or by al-Zabīdī).
  - "Later lexicographers did cite it, though" avoids implying that al-Zabīdī had the book in hand.
- **S3 (suggestion, carried over): balance for Hārūn's praise.** Hārūn himself says, intro p. 39, "وابن فارس لا يعتمد اطراد القياس في جميع مواد اللغة، بل هو ينبه على كثير من المواد التى لا يطرد فيها القياس".
  - A clause would round out "hardly ever failed".
  - This is optional: the essay already shows the misfits (mjs, qbl, the foreign words).
- **S4 (suggestion): five dates.** "lists five dates before settling on 395" can be read as five dates plus 395. Hārūn's five opinions include 395. Clearer: "weighs five reported dates and prefers 395 AH (1004–5 CE)."
- **S5 (suggestion): the stored wording is not strictly identical.** Stored kfr reads "ويقال للزارع", where Shamela's Hārūn reads "ويقال الزارع".
  - "In the entries we compared, the wording is his" is essentially right.
  - "The wording is his, apart from small variants" would be exact.
- **S6 (suggestion): no modern scholarship beyond Hārūn.** With the Baalbaki citations gone, the page cites no modern scholarly assessment of Ibn Fāris's method besides Hārūn's introduction. That is acceptable, since nothing is overstated. A later round could add a checked academic source, for example Baalbaki 2014 opened in an ordinary browser.
- **Tone, labels and layout: no problems.**
  - No generic praise or rankings, and the site's default-open choice is not mentioned as a ranking.
  - Translations are labelled ("translation for this guide", "our translation", excerpts).
  - Every root mention is a root link.
  - Several kinds of entry are shown: no aṣl (mjs), one aṣl (kfr, qbl), two (Ebd), outliers, *naḥt* and foreign words. There is no forced single-origin narrative.
  - Summary 41 words, lede 82 words, lede + body 1,072 words: within limits.

## URL check

| URL | Result |
|---|---|
| https://shamela.ws/book/21710 | 200. Hārūn, 2nd ed., al-Bābī al-Ḥalabī 1969–72, page-matched. OK |
| https://shamela.ws/book/9977/50 | 200. *al-Ṣāḥibī* p. 44, "باب الأسباب الإسلامية". OK |
| https://arabiclexicon.hawramani.com/ibn-faris-maqayis-al-lugha/ | 200. Correct page; no edition named. OK |

All three listed sources are cited in the text, and none is listed but unused.

## Validator

`node scripts/validate-dictionary-guides.mjs maqayis-al-lugha` passes ("1/1 guides pass"):
- 13 root links (9 pairs);
- 3 excerpts, all valid;
- 1,072 words;
- example roots: mjs, kfr, qbl, Ebd, fqh, dlk, jvm.

It prints 3 warnings, one for each `none` link (rdd in the body; rbb and rdd in onOurSite). Each is explained in its sentence.

## Site-data issues (unchanged from r3; the database was not touched)

1. **Doubled roots never collected.**
   - No displayed Maqāyīs root is a doubled root; the only one with 2nd = 3rd radical is the weak root Ayy.
   - hawramani's contents page lists them (أَبَّ …).
   - This removes the Maqāyīs entries for rabb, radd and others (Hārūn vol. 2 pp. 381, 386).
2. **Longer-words chapters merged into the preceding root** in six displayed entries: kfr, SrT, jvm, r*l, nml, srd.
   - The kfr English renderings mislabel this material as filed "under k-f". It belongs to the chapter for the whole letter kāf (Hārūn vol. 5 p. 193).
3. **Stored label and date are correct.** Author "Ibn Fāris" and date 1004 fit 395 AH ≈ 1004–5 CE.
