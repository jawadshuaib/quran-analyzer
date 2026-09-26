# Maqāyīs al-Lugha: verification, round 1

Independent fact-check of `roots/frontend/src/content/dictionary-guides/guides/maqayis-al-lugha.ts` (checked 2026-09-26). I did not open research-notes.md or any revision file.

Sources checked directly:
- **Hārūn ed. on Shamela** (book 21710; the book card confirms 2nd ed., al-Bābī al-Ḥalabī, 1969–72, 6 vols, page-matched). Shamela page ids map as follows. Introduction p. N = id N−2 (e.g. p. 23 = /21). Vol. 1 p. 3 = /47. Vol. 1 p. 328 = /372. Vol. 4 p. 205 = /1746. Vol. 5 p. 191 = /2243, p. 193 = /2245. Vol. 6 p. 150 = /2683.
- **Baalbaki 2014**, Google Books preview. I read pp. 349, 350, 351, 355 and 356 on screen. Pp. 352–53 are not in the preview.
- **al-Ṣāḥibī on Shamela** (book 9977): /50 = p. 44, /51 = p. 45.
- **hawramani page** for the dictionary.
- **Local displayed entries** via `_dict_guide_tool.py`: mjs 16616, kfr 163, qbl 536, Ebd 519, fqh 4838, jvm 9425, and the ʿAyn entry for Ebd, 372.
- **Qur'an morphology table** in quran.db.

Verdicts: S = supported, NQ = needs qualification, U = unsupported.

## Claims table

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Maqāyīs al-Lugha* / مقاييس اللغة | S | Shamela card "معجم مقاييس اللغة"; preface opens "هذا كتاب المقاييس فى اللغة" (vol. 1 p. 3) |
| C2 | titleGloss "The Measures of Language" | S | Rendering of *maqāyīs*; Baalbaki p. 351 discusses *qiyās*/*maqāyīs* as norms/measures |
| C3 | author Ibn Fāris; authorFull Abū l-Ḥusayn Aḥmad ibn Fāris ibn Zakariyyāʾ; authorAr | S | Shamela card: "أبو الحسين أحمد بن فارس بن زكريا (ت ٣٩٥ هـ)" |
| C4 | period d. 395 AH / 1004–5 CE, other dates reported | S | Hārūn intro pp. 9–10 (/7–/8): five reported dates (360, 369, 375, 390, 395), 395 judged most sound |
| C5 | kind "Root-meaning dictionary" | S | Preface p. 3; Baalbaki p. 349 |
| C6 | summary: names core sense(s), supports with poetry, the Qur'an and earlier lexicons, sets aside misfits; senses are his proposals | S | Baalbaki p. 349 ("He begins by determining whether the root has no aṣl, one aṣl, or more … supported by attested usage (šawāhid), particularly in poetry"); entries kfr, qbl |
| C7 | lede: a typical entry opens with a verdict (one, two, three *aṣl*) and then brings the evidence | S | Baalbaki p. 349; entries kfr, Ebd, qbl |
| C8 | lede: "tenth-century philologist"; persuasive in places, strained in others | S | d. 395/1004. Baalbaki p. 351 ("frequently arbitrary and unconvincing"). Ibn Fāris's own *yutamaḥḥal* in qbl |
| C9 | Worked mostly in Hamadhān, later at the Buyid court in Rayy, where he died | S | Hārūn intro p. 5 (/3: "استقر به فى معظم الأمر بمدينة همذان"), p. 6 (/4: called to the Buyid court at Rayy), p. 9 (/7: died at Rayy) |
| C10 | Hārūn lists five dates and settles on 395 AH | S | Intro p. 9 "يختلفون فى تاريخ وفاته على أقوال خمسة"; p. 10 "وأصح الأقوال … سنة (٣٩٥)" |
| C11 | Preface quotation "إنّ للغة العرب مقاييسَ صحيحةً، وأصولاً تتفرّع منها فروع" and its translation | S | Vol. 1 p. 3 (/47), verbatim; translation accurate |
| C12 | Earlier compilers never set out one of these measures | S | p. 3: "ولم يُعربوا فى شئٍ من ذلك عن مقياس من تلك المقاييس، ولا أصل من الأصول" |
| C13 | Each section headed with its *aṣl*, so a short statement covers the family | S | p. 3: "وقد صدَّرْنَا كلَّ فصلٍ بأصله … حتّى تكونَ الجملةُ الموجَزةُ شاملةً للتَّفصيل" |
| C14 | The five books: *ʿAyn* ranked highest and noblest; Abū ʿUbayd's two books; Ibn al-Sikkīt's *Kitāb al-Manṭiq*; Ibn Durayd's *Jamhara* | S | pp. 3–5 (/47–/49): "فأعلاها وأشرفُهَا كتاب … الخليل"; "فهذِه الكتبُ الخمسةُ معتمَدُنَا" |
| C15 | Everything else rests on these; a rare item is credited to its reporter | S | p. 5: "وما بعدَ هذِه الكتبِ فمحمولٌ عليها … حتى إذا وقع الشئُ النادر نَصَصْناه إلى قائله" |
| C16 | "The words are inherited; the analysis is his." | S | Interpretation consistent with p. 5 "معتمدنا فيما استنبطناه" and Baalbaki p. 349 |
| C17 | Baalbaki: keeps the items that demonstrate an *aṣl*; cuts down what he takes from al-Khalīl and Ibn Durayd | S | Baalbaki pp. 349–50: "satisfied himself with the lexical items that prove the correctness of his uṣūl … quotations from the lemmata of his two main sources … are normally abbreviated" |
| C18 | Almost every entry opens with the letters and a verdict, typically *aṣl ṣaḥīḥ yadullu ʿalā* | S | Baalbaki p. 349. grep: 200 displayed entries contain "أصل صحيح يدل" |
| C19 | 1,808 of 4,631 roots have no *aṣl*; 2,346 have one; 477 more than one | S | Baalbaki p. 350, verbatim figures |
| C20 | mjs: "a word for which we know no measure; I think it is Persian"; *al-majūs* at Q 22:17 | S | Entry 16616: "كَلِمَةٌ مَا نَعْرِفُ لَهَا قِيَاسًا، وَأَظُنُّهَا فَارِسِيَّةٌ". Morphology: majuws at 22:17 |
| C21 | kfr excerpt (Arabic) and its translation; [Q 57:20] | S | Entry 163 text matches (validator ok); Hārūn vol. 5 pp. 191–92 (/2243–/2244); al-Ḥadīd = sura 57 |
| C22 | kfr: coat of mail, ashes buried by dust, the sun "casts its hand into *kāfir*", two glosses (sunset/sea) reported without choosing | S | Entry 163: "فيقال إن الكافر مغيب الشمس. ويقال بل الكافر البحر"; second verse "ألقت ذكاء يمينها في كافر" |
| C23 | The Qur'an is cited for farmers, not for belief | S | 57:20 is the only Qur'an citation in the entry |
| C24 | The *kufr*–covering link is in his own voice, unattributed | S | "والكفر ضد الإيمان، سمي لأنه تغطية الحق" with no attribution |
| C25 | *kafirāt* "perhaps" (*laʿalla*) so called because high peaks seem to hide them | S | "ولعلها سميت كفرات لأنها متطامنة، كأن الجبال الشوامخ قد سترتها" |
| C26 | *al-Ṣāḥibī*: with Islam words moved "from their places to other places"; the Arabs knew of *kufr* only covering; the *aṣl* of *ṣalāt* was *duʿāʾ*; pp. 44–45 | S | Shamela 9977 p. 44 (/50): "ونُقِلت من اللغة ألفاظ من مواضعَ إِلَى مواضع أخَر"; p. 45 (/51): "كَانَتْ لا تعرف من الكُفر إِلاَّ الغِطاء والسِّتْر … الصلاة وأصله فِي لغتهم: الدُّعاء" |
| C27 | That "unbelief" grew out of "covering" is Ibn Fāris's reconstruction | S | Correctly labelled as interpretation (C24, C26) |
| C28 | Recurring formula *wa-mimmā shadhdha ʿan hādhā l-bāb* | S | grep: 29 displayed entries (e.g. qtl, hdy) |
| C29 | qbl excerpt and its translation | S | Entry 536; Hārūn vol. 5 (/2104–5), same wording incl. "[فإن كانت]" |
| C30 | *qabl* is the form of the root the Qur'an uses most | S | Morphology: qabol 242 occurrences; next lemma 10 |
| C31 | Hārūn: Ibn Fāris hardly ever failed to find the shared sense | S | Intro p. 23 (/21): "فلا يكاد يخطئه التوفيق" |
| C32 | Baalbaki: he said he disliked far-fetched connections, yet his *uṣūl* are "frequently arbitrary and unconvincing" | S | Baalbaki p. 351, verbatim ("he detests farfetchedness … frequently arbitrary and unconvincing") |
| C33 | Longer words get a chapter of their own "at the end of each letter" | **NQ** | Most letters have one, e.g. bāʾ vol. 1 p. 328 (/372), kāf vol. 5 p. 193 (/2245), ẓāʾ vol. 3 p. 478. But the hamza book ends at "أيى" with "تم كتاب الهمزة" (/213). The wāw book ends at "وهن" (/2683), and Hārūn's note there says Ibn Fāris omitted such a chapter. |
| C34 | "Most of what you see of them" is carved (*manḥūt*); others are three-letter words with added letters; some "set down" with no measure; cited vol. 1 pp. 328–29 | **NQ** | pp. 328–29 support the quotation and the definition of *naḥt*, but they name only **two** kinds: "على ضربين: أحدهما المنحوت … والضرب الآخر [الموضوع] وضعاً". The added-letter class is stated in the jīm chapter introduction (stored in jvm: "ومنه ما أصله كلمة واحدة وقد ألحق بالرباعي والخماسي بزيادة تدخله") and appears in practice (بلعوم, p. 329). |
| C35 | *karbala* is carved from *rabl* and *kabl* | S | Entry 163 / Hārūn vol. 5 p. 193: "منحوتة من كلمتين: من ربل وكبل" |
| C36 | *kibrīt* "is not Arabic"; "I do not know how the scholars accept this and its like" | S | Entry 163 (kāf longer-words chapter): "(الكبريت) ليس بعربي"; "وما أدري كيف يقبل العلماء هذا وأشباهه" |
| C37 | Ebd excerpt, its translation, and "(The bracketed word is the editor's.)" | S | Entry 519; Hārūn vol. 4 p. 205 (/1746) prints "و [الأول] من ذينك" |
| C38 | First *aṣl*: *ʿabd* and the trodden road; second: thick strong cloth and *ʿabad* (disdain) | S | Entry 519 |
| C39 | "Quoted voices are marked": "al-Khalīl said" introduces the *ʿibād*/*ʿabīd* distinction | **NQ** | The instance is correct. But the generalisation is overstated: much unmarked text in the same entry is al-Khalīl's. ʿAyn (entry 372) reads "ولم أسمعهم يشتقون منه فعلاً"; the Maqāyīs gives it without attribution as "ولم نسمعهم يشتقون منه فعلاً". The *muʿabbad* camel, the road and *ʿabad* also match ʿAyn wording. |
| C40 | Much of the rest also appears in ʿAyn, listed there with no statement of a shared sense | S | Entry 372: lists *ʿabd*, *muʿabbad*, road, *ʿabad* with no *aṣl* statement |
| C41 | Q 43:81 is filed under the second sense with *wa-fussira*: "the first to be angered by this and to disdain it" | S | Entry 519: "وفسر قوله تعالى … أي أول من غضب عن هذا وأنف من قوله" |
| C42 | ʿAyn gives that reading and adds one where *ʿābidīn* = worshippers | S | Entry 372: "أي الأنفين … ويقال … فلست بأول من عبد الله من أهل مكة" |
| C43 | "The Maqāyīs reports only the reading that fits its scheme, as other people's interpretation" | **NQ** | Only one reading is given, and it is introduced with the passive *fussira*. But the worship reading would equally fit his first *aṣl*, so "fits its scheme" suggests a selectivity the entry does not show. What it shows is that he cites the verse only as evidence for the second *aṣl*. |
| C44 | An *aṣl* is his inference; his Qur'anic citations are evidence chosen for his scheme | S | Interpretation; consistent with Baalbaki p. 349 |
| C45 | Older material: pre-Islamic poets such as Ṭarafa and al-Nābigha; philologists of the 8th–10th c. | S | Ṭarafa in Ebd (Hārūn fn: his Muʿallaqa); al-Nābigha in Amn, Aty; five sources (al-Khalīl to Ibn Durayd) |
| C46 | fqh: "every knowledge of a thing", "then" reserved for knowledge of the religious law | S | Entry 4838: "وكل علم بشيء فهو فقه … ثم اختص بذلك علم الشريعة" |
| C47 | "The book drew little attention before modern times. Hārūn found only one medieval author, Yāqūt, who mentions it, and edited it from a single manuscript." | **NQ** | Hārūn does say this (intro p. 39, /37: "ولم أجد أحداً غير ياقوت يذكر هذا الكتاب"; p. 40, /38: single copy in Dār al-Kutub). But Baalbaki pp. 355–56 shows more medieval use: Yāqūt reports Bū Jaʿfarak drew on it, and al-Ṣaghānī "quotes Ibn Fāris very frequently". Set side by side unreconciled, as now, the two statements read as a contradiction. |
| C48 | Baalbaki: its *uṣūl* rarely quoted later; never in *Lisān*; often in al-Ṣaghānī; some passed to *Tāj* [p. 356] | **NQ** (locator) | Substance supported. The "not frequently quoted in subsequent lexica" sentence is on p. 355; *Lisān*, Ṣaghānī and Zabīdī are on p. 356. |
| C49 | Stored text follows Hārūn, incl. his corrections and square-bracketed words | S | Ebd compared with vol. 4 pp. 205–6: stored ذينك, المهنوء, صفيقا, يعبد match Hārūn's corrections of the ms (his fns); [الأول], [فإن كانت] present |
| C50 | Hārūn's footnotes identify many unnamed poets; not included | S | Hārūn fns name Labīd, Thaʿlaba b. Ṣuʿayr (kfr) and al-Farazdaq (Ebd); stored text has no footnotes. Baalbaki p. 349: verses "mostly not ascribed" |
| C51 | Full vowels, bracketed verse refs and vowelled root heading are not in Shamela's text | S | Shamela: partial vowels, ﴿…﴾ with no [sura: verse], heading "[عبد]" |
| C52 | 1,323 roots, covering every letter | S | Tool: 1,323 displayed; 28 distinct first letters |
| C53 | Entries run from one line to over a thousand words | S | Hsd = one line; Eqb = 1,277 words |
| C54 | In several letters the source copy runs the closing chapter into the preceding root | S | grep: kfr, jvm, SrT, r*l, nml, srd |
| C55 | End of kfr, from *kanfalīla* on, belongs to that chapter | S | Hārūn vol. 5 p. 193 (/2245): chapter heading, then "من ذلك (الكنفليلة)" |
| C56 | Most of jvm: the heading surfaces mid-verse and the list breaks off | S | Entry 9425: "قال: باب ما جاء … أوله جيم بنانتين وجذمورا"; ends "ومما وضع وضعا ولم أعرف له اشتقاقا:" |
| C57 | harun-ed citation (2nd ed., 6 vols, al-Bābī al-Ḥalabī, 1969–72) | S | Shamela book card |
| C58 | Baalbaki citation (Brill 2014, pp. 348–56) | S | Google Books preview opens; pp. 349–51, 355–56 read |
| C59 | Ṣāḥibī citation (Bayḍūn 1997, pp. 44–45) | S | Shamela 9977 card: "محمد علي بيضون، الطبعة الأولى ١٤١٨هـ-١٩٩٧م"; pages confirmed |
| C60 | hawramani does not name the edition | S | hawramani dictionary page: no edition or editor named |
| C61 | Excerpts are copied from the stored original | S | Validator: 3 excerpts pass |

Totals: 61 claims. 55 supported, 6 need qualification, 0 unsupported.

## Flagged items and fixes

- **C33** "Longer words get a chapter of their own at the end of each letter."
  - Fix: change to "at the end of most letters".
  - Hārūn's text has no such chapter for hamza (/213) or wāw (/2683, where his note says Ibn Fāris left it out).
- **C34** The three kinds, cited to vol. 1 pp. 328–29.
  - Fix: keep the "Most of what you see…" quotation and the definition at [^harun-ed|vol. 1, pp. 328–29].
  - Then say that there he names two kinds, carved and "set down" (*mawḍūʿ*) with no room for measure.
  - Attribute the added-letter class separately: it is announced in the jīm chapter's introduction, which the site shows inside [[root:jvm|…]]. Alternatively, present it as what the entries do (e.g. *kanfalīla*: "a nūn has been added").
- **C39** "Quoted voices are marked."
  - Fix: "Some quoted voices are marked: 'al-Khalīl said' introduces…"
  - Then add: "but not all. 'We have not heard them derive a verb from it' is al-Khalīl's 'I have not heard' in *Kitāb al-ʿAyn*, taken over unmarked."
  - This also serves the brief's question on telling the compiler's voice from his sources.
- **C43** "reports only the reading that fits its scheme."
  - Fix: "The *Maqāyīs* gives only the reading that serves its second *aṣl*, and marks it as an interpretation (*fussira*), not its own."
  - Or simply drop "that fits its scheme".
- **C47** Hārūn's "only Yāqūt".
  - Fix: "When Hārūn edited it, from the single manuscript he could find, he knew of only one medieval author, Yāqūt, who mentioned it.[^harun-ed|editor's introduction, pp. 39–40]"
  - Follow with: "Baalbaki has since shown more use: al-Ṣaghānī quoted it often…"
  - Soften "drew little attention before modern times" to Baalbaki's framing: the method was not frequently quoted in later lexica, and fuller recognition waited until the twentieth century.
- **C48** Locator.
  - Change [^baalbaki|p. 356] to [^baalbaki|pp. 355–56].

## Brief issues

- **Suggestion: arrangement.** The essay never tells the reader how the book is arranged. The brief asks for it, and the task lists it. One sentence would do, and would explain why "chapters at the end of each letter" exist:
  - books by first letter;
  - within a letter, a sequence peculiar to Ibn Fāris (Hārūn, intro p. 42 ff.; Baalbaki p. 349, "a special type of taqālīb").
- **Suggestion: Ibn al-Sikkīt's book.** "Kitāb al-Manṭiq" is Ibn Fāris's own name for it. Add "(i.e. *Iṣlāḥ al-Manṭiq*)" as Baalbaki p. 349 glosses it; otherwise readers will not recognise the book.
- **Suggestion: word count.** Lede + body is exactly 1,100 words, the upper limit. Any added qualification needs a matching trim, e.g. the list of five books could be compressed.
- **Suggestion: guide link.** Consider a [[guide:…]] link at the first mention of *Kitāb al-ʿAyn*, since the essay compares against it.
- **Tone.** No generic praise or ranking was found. The Hārūn/Baalbaki contrast is balanced, and the essay says repeatedly that the *uṣūl* are proposals. It does not force a single-origin narrative: it shows outliers, two-*aṣl* roots and no-*aṣl* roots.
- **Labels.** The translations are labelled ("our translation", excerpt captions).

## URL check

- **https://shamela.ws/book/21710:** opens; it is the Hārūn 2nd edition, page-matched. OK.
- **https://books.google.ca/books?id=cme7AwAAQBAJ&pg=PA349:** opens in a browser with preview pages visible. Pp. 352–53 are not in the preview, and the essay cites neither. Scripted requests get a Google CAPTCHA, but ordinary readers are unaffected. OK.
- **https://shamela.ws/book/9977/51:** opens *al-Ṣāḥibī* p. 45. The chapter and the "مواضع إلى مواضع أخر" sentence start on p. 44 = /9977/50. Suggestion: point the URL at /50.
- **https://arabiclexicon.hawramani.com/ibn-faris-maqayis-al-lugha/:** opens; it is the right page, and it names no edition. OK.
- All four sources are used in the text. None is listed but unused.

## Validator

`node scripts/validate-dictionary-guides.mjs maqayis-al-lugha` passed ("1/1 guides pass"):
- 8 root links (7 distinct);
- 3 excerpts valid;
- 1,100 words (lede + body, excluding excerpts).

## Site-data issues

- **Stored labels are correct.** Author "Ibn Fāris" and date 1004 match 395 AH (Ṣafar 395 ≈ Nov.–Dec. 1004).
- **Longer-words chapters merged into roots.** The source copy (hawramani) runs each letter's closing chapter on words of more than three letters into the root before it: kfr, jvm, SrT, r*l, nml, srd.
- **The kfr English version compounds this.** The site's harmonized English for kfr describes the appended material as "augmented and quadriliteral words Ibn Fāris files under k-f". That is wrong: they belong to the chapter for the whole letter kāf, not to k-f. The guide's onOurSite note handles this correctly. The harmonized English (and probably jvm's) should be corrected, or the appended chapters split off.
