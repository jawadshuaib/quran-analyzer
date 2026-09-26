# Maqāyīs al-Lugha: revision, round 2

Reviser's log for `roots/frontend/src/content/dictionary-guides/guides/maqayis-al-lugha.ts`, answering `verification-r2.md` (2026-09-26).

Validator after revision: `1/1 guides pass`, 0 errors. Words (lede + body, excluding excerpts): 1,085 (was 1,099). There are 13 root links (9 distinct pairs) and 3 excerpts. The three `!` warnings are the intended `[[root:…|none|…]]` links (rdd twice, rbb once). Each one sits in a sentence saying our copy has no entry for it.

## Access to Baalbaki this round

- I tried to reopen Baalbaki pp. 350, 351 and 355–56.
  - curl to books.google.ca returned HTTP 429 and a redirect to google.com/sorry (a reCAPTCHA).
  - The connected Chrome browser, at books.google.com `…&pg=PA350`, showed the same "I'm not a robot" reCAPTCHA page.
  - I did not attempt the CAPTCHA.
  - archive.org has no copy of the book (advanced search, 0 hits).
  - The session's web-search budget was used up, so I could not look for other copies.
- As a result, **none of the p. 350 / 351 / 355–56 content was re-verified by me.** Round 1's transcription in research-notes.md was not treated as evidence. Every claim that rested only on those pages was cut. The one exception is the p. 351 phrase, which an independent published source confirms (see C32a).

## Changes, by flag

### C18: "The verdict is typically…" (NQ), fixed
- Now reads: "A common verdict is *aṣl ṣaḥīḥ yadullu ʿalā…*, 'a sound root pointing to…', but not every root gets a sense."
- My own recount agrees with the verifier: "أصل صحيح يدل" appears in 200 of the 1,323 displayed entries, "أصل (واحد )?صحيح" in 317, and "أصل واحد" in 400 (`_dict_guide_tool.py grep`).

### C19: Baalbaki's counts 1,808 / 4,631 / 2,346 / 477 (NQ), deleted
- p. 350 was unreachable (CAPTCHA) and I found no second source.
- The counts are reportedly Jabal's (2003: 47). The project holds a 2010 scan of Jabal, but it has no text layer or public link, and citing it would add a new source just to save one sentence, so I did not pursue it.
- The point that not every root gets a sense stands on the displayed mjs entry, which the next sentence quotes.

### C17: Baalbaki on abridging al-Khalīl and Ibn Durayd (NQ), abridgement clause deleted
- Now reads: "Nor did he aim at an exhaustive lexicon, as Ramzi Baalbaki notes.[^baalbaki|p. 349]"
- The locator narrows from pp. 349–50 to p. 349.
- Support: verification-r2 read p. 349 on screen: "Ibn Fāris was not interested in authoring an exhaustive lexicon…". I could not reopen p. 349 myself (CAPTCHA), so the sentence rests on the verifier's reading of the page. The next verifier should confirm it if Google Books becomes reachable.

### C32b: "Ibn Fāris said he disliked far-fetched connections" (NQ), deleted
- Now reads, as the verifier proposed: "Baalbaki, by contrast, finds his proposed *uṣūl* 'frequently arbitrary and unconvincing'.[^baalbaki|p. 351]"
- **C32a check (kept).** I opened David Larsen, "Meaning and Captivity in Classical Arabic Philology", *Journal of Abbasid Studies* 5/1–2 (2018), p. 177ff (brill.com/view/journals/jas/5/1-2/article-p177_7.xml; the page metadata marks it open access, and I fetched it with curl).
  - Text: "Indeed, for modern authorities he often goes too far. Jaakko Hämeen-Anttila calls his etymologies 'fantastic'; 'frequently arbitrary and unconvincing,' says Ramzi Baalbaki."
  - n. 21: "Hämeen-Anttila, review of Zammit, *Comparative Lexical Study*, 296, n4; Baalbaki, *Arabic Lexicographical Tradition*, 351."
  - This confirms the phrase and the page. Larsen applies it to Ibn Fāris's etymological proposals. The guide's object, "his proposed *uṣūl*", fits a page inside Baalbaki's Maqāyīs section (pp. 348–56, per verification-r2, C61).
- Not used: round-1 notes point to Ibn Fāris's own words at Hārūn vol. 3 p. 275 (root ص ف ف), "غيرَ أنَّا نكره القياسَ المتمَحَّل المستَكْرَه". That root is not displayed in the Maqāyīs on al-nuqta, and the qbl excerpt already shows his reluctance to force a measure (يُتَمَحَّل). I added no new claim here.

### C51: Baalbaki's reception survey, pp. 355–56 (NQ), deleted and replaced with evidence I checked myself
- **Deleted:**
  - "Baalbaki's later survey finds it used, if narrowly: Ibn Manẓūr's *Lisān al-ʿArab* never quotes its *uṣūl*, but al-Ṣaghānī often cites them, and some of his quotations passed into al-Zabīdī's *Tāj al-ʿArūs*.[^baalbaki|pp. 355–56]"
  - The `[[guide:lisan-al-arab|…]]` link goes with it.
- **Hārūn's sentence reworded to match his words.** It used to say he "knew of only one medieval author who mentions the book, Yāqūt". "Medieval" is not his word. Hārūn, editor's intro p. 39 (Shamela /37, page title "المقدمة - ص39"): "ولم أجدْ أحداً غير ياقوت يذكر هذا الكتاب لابن فارس". The guide now says: "he had found no one besides Yāqūt who mentions the book, and he wrote that scholars had noticed it only recently." The second half is p. 40 (/38): "وهذا الكتاب لم يسترع انتباه العُلماء إلا منذ عهد قريب". The single manuscript is also p. 40: "فإنى لم أجِد أمامى منه إلا نُسخة واحِدة مودعة بِدار الكتب المصرية".
- **Added (new claims N1–N2 below):** "It had been read, though…", with the Tāj evidence and dlk linked in both dictionaries. This follows the verifier's optional suggestion, using dlk rather than zhq because the dlk quotation names the book and is nearly verbatim. Without it, the page would imply that nobody but Yāqūt took notice of the book. The Tāj text displayed on al-nuqta shows otherwise.

### B1 (must-fix): the doubled-root section is missing, fixed in body and onOurSite
- **Body:** "doubled roots such as *radd*" became "doubled roots such as [[root:rdd|none|ر د د]] (a section missing from our copy)".
- **onOurSite:** "The 1,323 roots shown cover every letter, but not every section. The section that opens each letter, on doubled roots, is missing, so there is no entry here for [[root:rbb|none|ر ب ب]] or [[root:rdd|none|ر د د]], though the book treats both.[^harun-ed|vol. 2, pp. 381, 386]"
- Evidence: see N3.

### B2 (suggestion): qbl hedge, applied
"is left outside the family" became "is placed, tentatively, outside the family". This matches the excerpt's "nearer to being an outlier" (إلى الشذوذ أقرب).

### B3 (suggestion): the third kind of longer word, applied
- "In practice he adds a third kind…" became "Elsewhere he names a third kind, three-letter words with letters added.[^harun-ed|vol. 2, p. 509] *Kanfalīla*, a bushy beard, is one: *kafl* (gathering), enlarged."
- Evidence: see N4.

### B4 (word count)
Now 1,085. Nothing was padded.

### B5 (must-fix): the Baalbaki passages on pp. 350, 351 (first half) and 355–56
All were cut as proposed. The only Baalbaki claims left are:
- p. 349, "not … an exhaustive lexicon" (read on screen by verification-r2);
- p. 351, "frequently arbitrary and unconvincing" (confirmed independently by Larsen 2018, n. 21).

## Removed claims

1. Baalbaki p. 350: 1,808 of 4,631 roots have no *aṣl*, 2,346 have one, 477 have more.
2. Baalbaki pp. 349–50: Ibn Fāris keeps what demonstrates an *aṣl* and abridges what he takes from al-Khalīl and Ibn Durayd.
3. Baalbaki p. 351: Ibn Fāris said he disliked far-fetched connections.
4. Baalbaki pp. 355–56: *Lisān al-ʿArab* never quotes the *uṣūl*; al-Ṣaghānī often cites them; some of al-Ṣaghānī's quotations passed into *Tāj al-ʿArūs*.
5. "The verdict is typically…". Replaced by "A common verdict…".
6. "In practice he adds a third kind". Replaced by "Elsewhere he names a third kind" (N4).
7. The qualifier "only one *medieval* author". Replaced by Hārūn's own "no one besides Yāqūt".

## New claims (each checked by me in a source I opened)

**N1. "In several entries al-nuqta shows, al-Zabīdī's Tāj al-ʿArūs cites 'Ibn Fāris in the *Maqāyīs*'."**
- `_dict_guide_tool.py grep murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus "المقاييس|مقاييس"` finds 7 displayed entries. Six of them name the book:
  - Sdq: "وأنشد ابن فارس في المقاييس"
  - slT: "وتابعه ابن فارس في المقاييس، والصواب: ما قاله الجوهري، وقد نبه عليه الصاغاني في العباب"
  - xDE: "وابن فارس في المقاييس"
  - $gl: "وقال ابن فارس في المقاييس: قد جاء عنهم: اشتغل فلان بالشيء"
  - dlk: "قال ابن فارس في المقاييس في هذا التركيب"
  - bhl: "كذا في المجمل والمقاييس"
  - The seventh, zyl, uses مقاييسه for grammar and is irrelevant.
- Cross-check: the Sdq verse "فلا زلن حسرى ظلعا…" and the $gl sentence "وقد جاء عنهم: اشتغل فلان بالشيء" both appear in the displayed Maqāyīs entries for those roots.
- The claim is limited to the displayed text. It does not say whether al-Zabīdī read the *Maqāyīs* directly or through al-Ṣaghānī.

**N2. Under dlk, the Tāj "repeats, almost word for word, the reflection that closes his own entry: wherever dāl and lām are joined by a third letter, he finds, the word points to movement, to coming and going."**
- Maqāyīs dlk (entry 17840, displayed; its last words): "قَالَ أَحْمَدُ بْنُ فَارِسٍ: إِنَّ لِلَّهِ تَعَالَى فِي كُلِّ شَيْءٍ سِرًّا وَلَطِيفَةً. وَقَدْ تَأَمَّلْتَ فِي هَذَا الْبَابِ مِنْ أَوَّلِهِ إِلَى آخِرِهِ فَلَا تَرَى الدَّالَ مُؤْتَلِفَةً مَعَ اللَّامِ بِحَرْفٍ ثَالِثٍ إِلَّا وَهِيَ تَدُلُّ عَلَى حَرَكَةٍ وَمَجِيءٍ، وَذَهَابٍ وَزَوَالٍ مِنْ مَكَانٍ إِلَى مَكَانٍ، وَاللَّهُ أَعْلَمُ."
- Tāj dlk (entry 17838, displayed): "قال ابن فارس في المقاييس في هذا التركيب: إن لله في كل شيء سرا ولطيفة، وقد تأملت في هذا الباب يعني باب الدال مع اللام من أوله إلى آخره فلا ترى الدال مؤتلفة مع اللام بحرف ثالث إلا وهي تدل على حركة ومجيء وذهاب وزوال من مكان إلى مكان."
- Differences: the Tāj omits تعالى, adds the gloss "يعني باب الدال مع اللام", and omits "والله أعلم". Hence "almost word for word".
- The guide gives a paraphrase, not a quotation, and "he finds" marks it as his observation.
- Both dictionaries are linked: [[root:dlk|murtada-…|د ل ك]] and [[root:dlk|ibn-faris-maqayis-al-lugha|his own entry]].

**N3. Doubled-root section missing; no entry for rbb or rdd; the book treats both at vol. 2 pp. 381, 386.**
- **Hārūn on Shamela (book 21710):**
  - The rāʾ book's first section is "باب الراء وما معها فى الثنائى والمطابق" (table of contents on /932 = vol. 2 p. 372). Its bracketed two-letter headings run [رز], [رس] … [رأ], [رب] … [رد].
  - /941 (page title "ج2 - ص381"): "[رب] الراء والباء يدلُّ على أُصولٍ. فالأول إصلاح الشئِ والقيامُ عليه…"
  - /946 ("ج2 - ص386"): "[رد] الراء والدال أصلٌ واحدٌ مطّردٌ منقاس، وهو رَجْع الشَّئ…"
- **Our database** (`quran.db`, read-only):
  - No `ibn-faris-maqayis-al-lugha` row exists for rbb or rdd, in any status.
  - All Maqāyīs rows have three-letter ids apart from one four-letter id (zxrf). None has a source_url on a two-letter hawramani page.
- **hawramani:** /رد/ carries "Ibn Fāris, Maqāyīs al-Lugha … (رَدَّ) الرَّاءُ وَالدَّالُ أَصْلٌ وَاحِدٌ مُطَّرِدٌ مُنْقَاسٌ". /ردد/ has no Maqāyīs section.
- I did not find where hawramani files the Maqāyīs *rabb* entry (neither /رب/ nor /ربب/ has one). So the page does not state why the section is missing, only that it is.

**N4. "Elsewhere he names a third kind, three-letter words with letters added.[^harun-ed|vol. 2, p. 509]"**
- Shamela /1069 (page title "ج2 - ص509"): "[باب الراء وما بعدها مما هو أكثر من ثلاثة أحرف] وهذا شئ يقِلُّ فى كتاب الراء، والذى جاء منه فمنحوتٌ أو مزيدٌ فيه".
- The same three-way scheme appears in the displayed jvm entry (the jīm chapter's introduction): "وذلك على أضرب: فمنه ما نحت من كلمتين صحيحتي المعنى، مطردتي القياس. ومنه ما أصله كلمة واحدة وقد ألحق بالرباعي والخماسي بزيادة تدخله. ومنه ما يوضع كذا وضعا."
- The *kanfalīla* example itself is unchanged (verification-r2, C38).

## Disputed

None of the verifier's verdicts is disputed. One precision on B1's data:
- The verifier found no Maqāyīs row among the 153 roots whose second and third letters match. In fact one exists: **Ayy (أيى)**, entry 531, displayed.
- It is a weak root that the book files at the end of the hamza book, among the three-letter roots (verification-r2 saw "تم كتاب الهمزة" at /213). It is not a doubled-section entry, so the statement "the section on doubled roots is missing" stands.

## Site-data notes (no action taken)

- The doubled-root gap is a scrape gap. The Maqāyīs entries for doubled roots (for example *radd* at hawramani /رد/) were never collected. This removes, among others, *rabb* and *radd*.
