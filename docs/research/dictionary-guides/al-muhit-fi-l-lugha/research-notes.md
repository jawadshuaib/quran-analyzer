# al-Muḥīṭ fī l-Lugha (al-Ṣāḥib ibn ʿAbbād) — research notes

Guide: `roots/frontend/src/content/dictionary-guides/guides/al-muhit-fi-l-lugha.ts`
Site dictionary slug: `al-sahib-bin-abbad-al-muhit-fi-l-lugha` (836 displayed roots; stored date 995; label "al-Ṣāḥib b. ʿAbbād").
Compiled 2026-09-26. Everything below was opened and read by the drafting agent; page images were viewed where stated.

---

## 1. What al-nuqta displays

- `_dict_guide_tool.py dicts` → "al-Muḥīṭ fī l-Lugha | المحيط في اللغة | al-Ṣāḥib b. ʿAbbād (site date 995) | lang=ar | displayed entries=836".
- Entries read in full with `entry`: كفر (kfr), رزق (rzq), ظلم (Zlm), عذب (E*b), علم (Elm), عفو (Efw), غرف (grf), زور (zwr), رفق (rfq), سبل (sbl); al-ʿAyn entries for rzq, Zlm, E*b, Elm; Lisān and Muḥkam for kfr.
- Peculiarities of the stored text:
  - Every entry begins with the bare root letters run into the text ("كفر الكُفْرُ: …", "رزق الرِّزْقُ: …").
  - Stray characters / misplaced vowels: zwr "وال! زوَرُ"; sbl "وااسابِلةُ"; kfr "ألْجَاتَ" (print: ألْجَأْتَ), "تُشْكَر ُنِعَمُه".
  - No editor's footnotes; no bāb headings of the phonetic arrangement (e.g. print's "[الكاف والراء والفاء]" before كرف/كفر/فكر/فرك is absent).
  - Very short entries exist: rzq = 5 short clauses, "الرِّزْقُ: مَعروفٌ" ("well known") and nothing more on rizq.
  - Efw: stored "عفو وعفى عفى أُهْمَلَه الخَليلُ. وحَكاه الخارْزَنْجِيُّ." Print (vol. 2, p. 170): "عفو عفى: «عفى» أهمله الخليل وحكاه الخارزنجي." The quotation marks limiting the note to the spelling «عفى» are lost; our faithful translation and harmonized English both say al-Khalīl omitted *this root* (wrong — the ʿAyn has ʿ-f-w and we display it).
  - rfq: stored entry opens "رفق مُهْمَلٌ عنده. الخارزنجي: الرَّوَاذق: …". Print (vol. 5, p. 373) has this note under **رذق**: "رذق: مُهْمَلٌ عنده (٨). الخارزنجيُّ (٩): الرَّوَاذِقُ …". Mis-headed on hawramani; our harmonized English says "the root رفق was left untreated by al-Khalīl" (wrong).
- Rough counts (my regex counts on displayed originals, vowel-insensitive):
  - Full verse lines (hemistich separator "..."): 21 of 836 al-Muḥīṭ entries (cf. 356 of 505 Kitāb al-ʿAyn entries; ʿAyn entries each cover several permutation-roots, so not like-for-like — not used in the essay).
  - Qur'an markers (عز وجل|تعالى|قوله جل|القرآن|التنزيل): 156 of 836 (not used in essay).
  - "الخارزنجي" in 6 displayed entries; "الخليل" in 8.
  - Author's own voice: "قال الصاحب" (grf; also qEd "وقال الصاحب: قال الخليل…"); "عندي" judgements (zwr "وهو تصحيف عندي"; mrd "وهذا عندي موضعه المعتل").
  - Tāj al-ʿArūs entries naming Ibn ʿAbbād with a verb of citation `(عن|قال|قاله|ذكره|أورده|اورده|نقله) ابن عباد(?![ةه])`: 269 displayed entries (essay: "more than 250"). 22 say explicitly "نقله الصاغاني عن ابن عباد" or "في العباب عن ابن عباد" (e.g. nws, rfE, qrD, bT$, nqD, xms, bDE).

### Which text is it? (onOurSite)

- hawramani page for the work (https://arabiclexicon.hawramani.com/al-sahib-bin-abbad-al-muhit-fi-l-lugha/): "Al-Ṣāḥib bin ʿAbbād (d. c. 995 CE / 385 AH) was a Persian Shiite scholar … His Muḥīṭ … is meant as a complete dictionary of Standard Arabic, comprising 1300 pages. The entries are arranged in the manner of al-Khalīl's Kitāb al-ʿAin." **No edition named.** hawramani /about/ page: no edition statements. (Note: hawramani's "Shiite" is contradicted by Iranica, "Although not himself a Shiʿite…"; not used.)
- Old Shamela EPUB (https://old.shamela.ws/epubs/000/83.epub), info page: "[الكتاب مرقم آليا غير موافق للمطبوع]". I compared 15 stored entries (kfr, Zlm, E*b, Elm, rzq, grf, zwr, Efw, sbl, qwm, nwr, xlf, Hkm, bSr, rHm) in 40-character normalized chunks against the EPUB: 94–100 % of chunks found verbatim (misses at root headings / stray characters). → "matches, apart from small slips, the older digital text".
- New Shamela (https://shamela.ws/book/83; card: ed. Muḥammad Ḥasan Āl Yāsīn, ʿĀlam al-Kutub, Beirut, 1st ed. 1414/1994, 11 vols) is page-aligned with the print and has footnotes, but in Zlm it **drops** words the stored text has: new Shamela "و {وَلَمْ تَظْلِمْ مِنْهُ شَيْئاً}" and "و {فَإِذا هُمْ مُظْلِمُونَ}" vs stored "وظَلَمْتُ الشَّيْءَ: نَقَصْتُه، من قَوْلِه عَزَّ وجَلَّ: " ولم تَظْلِمْ منه شَيْئاً "" and "والمُظْلِمَةُ: المَرْأةُ التي قد أظْلَمَ عليها، ومنه قَوْلُه عَزَّ وجَلَّ".
- Print scan (https://archive.org/details/lis01996, file 10.pdf, PDF p. 32 = printed vol. 10, p. 32; viewed as image): reads "وظَلَمْتُ الشَّيْءَ: نَقَصْتُه، من قَوْلِـه عَـزَّ وجَـلَّ: ﴿ولم تـظْلِمْ منـه شَيْئاً﴾ (٢٣)". → stored text agrees with the print; the new Shamela digitisation is the one that lost words. Cover of 01.pdf viewed: "المحيط في اللغة / تأليف كافي الكفاة الصاحب إسماعيل بن عباد ٣٢٦–٣٨٥هـ / تحقيق الشيخ محمد حسن آل ياسين / عالم الكتب".
- Edition history (al-Jubūrī summary, alukah): Āl Yāsīn edited three parts printed by the (Iraqi) Ministry of Culture and Information 1978–1982; publication stopped; complete in 11 parts by ʿĀlam al-Kutub 1994. Quote: "إذ قام الشيخ محمد حسن آل ياسين بتحقيق ثلاثة أجزاء منه، طبعتها وزارة الثقافة والإعلام بين الأعوام (1978-1982)، وتوقف عن الصدور إلى أنْ دفعه محققه إلى مؤسسة عالم الكتب لتقوم بطباعته كاملًا عام 1994م في أحد عشر جزءًا." (Not used in the guide.)

---

## 2. Claim-by-claim support

| # | Claim in guide | Source | Passage / location |
|---|---|---|---|
| 1 | Ismāʿīl ibn ʿAbbād, title al-Ṣāḥib; secretary to Ibn al-ʿAmīd; vizier to Buyid emirs Muʾayyad al-Dawla and Fakhr al-Dawla at Isfahan and Rayy; died 995 in Rayy | Iranica (Pomerantz), https://www.iranicaonline.org/articles/ebn-abbad-esmail-al-saheb-kafi/ (read in browser; curl gets 403) | "ṢĀḤEB EBN ʿABBĀD, Esmāʿil Kāfi-al-Kofat (938-95), vizier and belletrist." "became the protégé of … Abu'l-Fażl b. al-ʿAmid"; "An earlier collection of letters, composed when the vizier was a scribe for Ebn al-ʿAmid"; "In 966, Moʾayyad-al-Dawla became the ruler of Isfahan and Abu'l-Fażl appointed Ebn ʿAbbād as his vizier"; "Ebn ʿAbbād became vizier on behalf of Moʾayyad-al-Dawla in 976"; "arranged for [Faḵr-al-Dawla's] installation as the new emir in Rayy"; "Ebn ʿAbbād died on 30 March 995 in Rayy." Also Āl Yāsīn pp. 10–12 ("فأصبح ابن عباد كاتباً لابن العميد", p. 11). |
| 2 | Letter-writer with a taste for rare words; patron of a famous library | Iranica | "Their style is marked by a frequent use of rhymed prose (Ar. sajʿ) and a distinctive predilection for rare linguistic usage (Ar. ḡarib) reflecting Ebn ʿAbbād's interest in lexicography"; "In Rayy, Ebn ʿAbbād encouraged the construction of a library that was among the largest collections of books in the Islamic world at the time". |
| 3 | Ibn Khallikān names Ibn Fāris among his teachers | Ibn Khallikān, Wafayāt, ed. ʿAbbās, vol. 1, p. 228 (https://shamela.ws/book/1000/222) | "أخذ الأدب عن أبي الحسين أحمد بن فارس اللغوي صاحب كتاب " المجمل " في اللغة، وأخذ عن ابي الفضل ابن العميد". Also Āl Yāsīn p. 21. |
| 4 | Haywood: he did not adopt his teacher's alphabetical arrangement; went back to al-Khalīl's | Haywood 1960, p. 63 (archive.org djvu text) | "We are told that he studied under the lexicographer Ibn Faris … But when he came to compile a dictionary, he preferred al-Khalil's method to that used by his master in the "Mujmal" and the "Maqayis" — that is, the modern dictionary arrangement." |
| 5 | His introduction says nothing about why/for whom; explains al-Khalīl's system; objections from Sībawayh and al-Mubarrad | al-Muḥīṭ, ed. Āl Yāsīn, vol. 1, pp. 57–61 (https://shamela.ws/book/83/40 … /44) — read in full | Opens "كلام العرب مبنيٌّ على أربعة أنحاء: الثُّنائيّ، والثلاثيّ، والرباعي، والخماسي" (p. 57); "فإِنْ قال قائل: لِمَ ابتدأ الخليل عند ذكر الأبنية بالثنائي؛ وقد قال سيبويه…" (p. 58); letter table by articulation (p. 60); "فقد قرأتُ لشيخنا أبي العباس المبرّد…" (p. 61); ends "قال الخليل: وإِنما بدأنا [الأبنية] بالمضاعَف لأنه أخفُّ على اللسان…" (p. 61). p. 63 begins [حرف العين]. No statement of purpose, audience or sources. |
| 6 | Quoted sentence + translation | same, vol. 1, p. 59 | "واعلم: أن الخليل لمّا هَمَّ بجمع كلام العرب أجال فكره فيما يبني عليه كتابه ويدير عليه أبوابه، فنظر في الحروف كلِّها…" Translation (mine): "Know that when al-Khalīl resolved to gather the speech of the Arabs, he turned over in his mind what to build his book upon and around what to turn its chapters." |
| 7 | Ibn Khallikān: "made the words many and the evidence few" | Ibn Khallikān vol. 1, p. 230 (https://shamela.ws/book/1000/224) | "وصنف في اللغة كتاباً سماه المحيط وهو في سبع مجلدات، رتبه على حروف المعجم، كثر فيه الألفاظ وقلل الشواهد فاشتمل من اللغة على جزء متوفر". (Ibn Khallikān d. 681/1282 per Shamela card.) |
| 8 | Haywood: charge fair; aim "an exhaustive vocabulary in a small space" | Haywood p. 64 | "All agreed that it contained an exceedingly large vocabulary not supported by sufficient examples." … "The accusation of lack of examples is justified, but the author's aim was apparently to give an exhaustive vocabulary in a small space." |
| 9 | Arrangement: articulation order from throat; doubled roots, sound and weak triliterals, longer words | Āl Yāsīn, editor's intro, vol. 1, pp. 15–16 (https://shamela.ws/book/83/8) | "وقد سار فيه مؤلفه على منهج الخليل في العين؛ سواءاً فيما يتعلق بتسلسل الحروف مقسمة على مخارجها الصوتية؛ أو بترتيب الأبواب داخل كل حرف، ابتداءً بباب المضاعف الثنائي، ثم باب الثلاثي الصحيح، ثم باب الثلاثي المعتل، ثم باب اللفيف، ثم باب الرباعي، ثم باب الخماسي." p. 16: "وفي الكتاب بعض الشواهد الشعرية ولكنها قليلة." Author's intro p. 57–60 confirms throat-first order. |
| 10 | All orderings of same consonants handled together | Haywood p. 64; edition vol. 6 pp. 250–52 | Haywood: "Ibn ʿAbbad employs the anagrammatical method of al-Khalil, with exactly the same phonetic alphabet." Edition: "[الكاف والراء والفاء] كرف … كفر … فكر … فرك" on consecutive pages. |
| 11 | He treats the ʿAyn as al-Khalīl's; al-Azharī credited its contents to al-Layth | al-Jubūrī summary (https://www.alukah.net/library/0/148209/) | "ثم يشير إلى ما أهمله الخليل مصرحًا باسمه، معتقدًا أن العين هو للخليل لا لغيره، مثلما فعل الأزهري الذي كان ينسب كلَّ ما ورد في هذا الكتاب إلى الليث بن المظفر." NB the Arabic "مثلما فعل الأزهري" is literally "as al-Azharī did", but the relative clause says al-Azharī attributed it to al-Layth — i.e. a contrast. My rendering "whereas" follows the sense. Verifier may wish to recheck. |
| 12 | Reports what the ʿAyn contains, names al-Khalīl where it left a word out, fills first from al-Khārzanjī's Takmila, then from sources he seldom names | al-Jubūrī summary | "وكان الصاحب في كل ذلك يذكر ما ورد في كتاب العين الذي كان نصب عينيه، ثم يشير إلى ما أهمله الخليل مصرحًا باسمه … وأما ما لم يجده في العين، فإنه يأخذه مما استدرك عليه، معتمدًا أولًا على تكملة العين للخارزنجي … هذا فضلًا عما كان يأخذه من مصادره الأخرى، التي لا يصرح بأسمائها غالبًا." Edition instances: vol. 1 p. 66 "عه: أهمله الخليل. وحكى الخارزنجي…", p. 106 "[قهع]: أهمله الخليل. وحكى الخارزنجي…". |
| 13 | al-Khārzanjī d. 348/959; Takmila appears lost | Āl Yāsīn pp. 23–24 | quoting al-Samʿānī: "وتوفي في رجب سنة ثمان وأربعين وثلاثمائة" (p. 23); "ولمّا كان كتابه «التكملة» مفقوداً في أغلب الظن" (p. 24); "وروى عنه الصاحب بن عباد في المحيط فأكثر" (p. 24); p. 22: "الخارزنجي البشتي الذي تردد اسمه كثيراً في «المحيط» وتكرَّر النقل عنه وبخاصةٍ في ما أهمله الخليل." |
| 14 | One collector found 580 of his 636 fragments in al-Muḥīṭ | al-Ḥayyālī, publisher's description (qindeel.ae) | "وقد بلغ عدد ما جمعته منها 636 نصًّا،580 نصًّا منها وجدتها في )المحيط في اللغة( للصاحب بن عباد385 هـ وبهذه المثابة يكون المصدر الأول الذي ضم بين دفتيه نصوصًا من التكملة؛ وتبين انه قد نقلها من التكملة مباشرة." Also "جمع نصوص هذا الكتاب المفقود". Only the description was consulted, not the book. |
| 15 | Al-Azharī attacked al-Khārzanjī (copying from unheard written copies → misreadings); Āl Yāsīn calls the attack unfair | Āl Yāsīn pp. 24–31 (quoting Tahdhīb 1/32–40, 52–53) | al-Azharī: "قد اعترف البشتي بأنه لا سماع له في شيءٍ من هذه الكتب، وانه نقل ما نقل إلى كتابه من صُحفهم … لأنه اعترف بأنه صحفي، والصحفي إِذا كان رأس ماله صحفاً قرأها فإِنه يصحّف فيكثر" (p. 26); "فالواجب على طلبة هذا العلم ألاّ يغتروا بما اودع كتابه" (p. 27). Āl Yāsīn: "لم يستطع أنْ يكون علمياً وموضوعياً في نقده وطعنه بهذا الرجل" (p. 28); "وانها لحملة ظالمة ليس لها أي مسوِّغ مقبول" (pp. 29–30); conclusion p. 31. |
| 16 | ظ ل م comparison (shared wording; ʿAyn's poets Kaʿb, Zuhayr, al-Nābigha; Q 31:13; Muḥīṭ drops poets and verse) | Displayed entries Zlm in both dictionaries | ʿAyn: "والظَّلْمُ: الثَّلْجُ … قال كعْب: تَجْلُو عوارِضَ ذي ظَلْمٍ إذا ابتَسَمَتْ"; "قال زهير: ...... ويُظْلَمُ أحياناً فيَظَّلِمُ"; "وظُلِمَت الأرض: لم تُحْفَر قطُّ ثم حُفِرَتْ، قال النابغة: والنُّؤيُ كالحَوْض في المظلومة الجَلَدِ"; "والظُّلْمُ: الشِّرْك، قال الله- عز وجل-: إِنَّ الشِّرْكَ لَظُلْمٌ عَظِيمٌ". (The ʿAyn also has an anonymous line "إذا ما رنا الرائي…" for the teeth sense — so "three senses come with a poet" is true; four lines in all.) Muḥīṭ has the same senses (الظَّلْمُ: الثَّلْجُ، وماءُ الأسْنَانِ وشِدَّةُ ضَوْئها; ظُلِمَ فاظَّلَمَ: أي احْتَمَلَ الظُّلْمَ; الأرْضُ المَظْلُوْمَةُ; الظُّلْمُ: الشِّرْكُ بالله; الظَّلِيْمُ: الذَّكَرُ من النَّعَام; الظُّلاَمَةُ) and no verse of poetry (only proverbs). Print: vol. 10, pp. 31–33. |
| 17 | Muḥīṭ additions: torrent fills valley; waterskin drunk before matured; aṣl = putting a thing out of its place, without source; Q 18:33 for ẓalama = diminish | Displayed Muḥīṭ Zlm | "وظَلَمَ السَّيْلُ الأرْضَ والوادِي: إذا مَلأَه"; "وسِقَاءٌ مَظْلُوْمٌ: شُرِبَ ما فيه قَبْلَ إدْرَاكِه"; "وأصْلُه: وَضْعُ الشَّيْءِ في غير مَوْضِعِه"; "وظَلَمْتُ الشَّيْءَ: نَقَصْتُه، من قَوْلِه عَزَّ وجَلَّ: " ولم تَظْلِمْ منه شَيْئاً "" (= Q 18:33, editor n. 23). None of these in the displayed ʿAyn entry. |
| 18 | Study of the whole book: quotations cut to the point; half-lines more than whole lines; sometimes bare reference | al-Jubūrī summary | "فهو يقتطع من الآية أو الحديث أو المَثَل أو القول ما يجد فيه شاهده، وكذلك الحال في الشعر، ومن هنا كان عدد الأشطر الشعرية هو أكثر قياسًا بعدد الأبيات الكاملة، وتعزيزًا لمنهجه في الاختصار وجدناه يشير إلى الآية أو الحديث أو أي نوع من الشواهد النثرية والشعرية دون ذكرها". |
| 19 | About twenty of 836 entries have a full verse line | my count (§1) | 21 entries with "..." hemistich separator. Labelled "by our rough count". |
| 20 | Entries impersonal ("it is said", "they say"); sources usually unnamed | al-Jubūrī summary | "تبيَّن لنا أن الصاحب عندما كان يعتمد على أقوال اللغويين والشيوخ لم يكن يصرح بأسمائهم … ولذا كثرت عنده عبارات مثل: (قال، قيل، قالوا، يقولون)". |
| 21 | غ ر ف: "قال الصاحب…" autograph of Abū Ḥanīfa | Displayed grf; print vol. 5, p. 67 | "قال الصاحِبُ: الصَّحيحُ في الغَرَفِ فَتْحُ الراء، كذا وَجَدْتُه في أصْل أبي حَنِيفَةَ بخَطِّه، والواحِدَةُ غَرَفَةٌ." Editor n. 34: passage missing in MS ت. Abū Ḥanīfa NOT identified in the guide (our site's faithful translation adds "[al-Dīnawarī]"; plausible but not verified from a source I consulted). |
| 22 | ز و ر: al-Khārzanjī's word judged "taṣḥīf ʿindī"; true word with r | Displayed zwr; print vol. 9, p. 83 | "وحَكَى الخارزنجيُّ: الزائرَةُ: الشحْمَةُ التي تكونُ حَوْلَ الداغِصَةِ من الدابةِ السمِيْنَةِ. وهو تَصْحِيْفٌ عندي؛ لأنَّه هو الرّائرَةُ - بالراء دُوْنَ الزاي -." |
| 23 | ك ف ر opens with kufr ≠ īmān, ingratitude ≠ shukr, then the four-kinds classification; night, valley; sun's setting-place "because it covers it" | Displayed kfr; print vol. 6, pp. 250–52 | "الكُفْرُ: نَقِيْضُ الإِيمان. وهو - أيضاً -: العِصْيَانُ والامْتِناعُ. وقَوْلُ العَرَبِ: كُفْرٌ على كُفْرٍ … والكُفْرُ: كُفْرَانُ النَعْمَةِ وهو نَقِيْضُ الشكْرِ. والكُفْرُ باللهِ على أرْبَعَةِ أصْنَافٍ…"; "والكافِرُ: اللَّيْلُ"; "ووادٍ كافِرٌ: غَطى كُلَّ ما على جَوَانِبِه"; "ومَغِيْبُ الشَّمْس: كافِرُ الشَّمْس لأنَه يُغَطِّيْها". Covering-linked senses: sun (يغطيها), mail-coat worn مغطاة, valley غطى, ashes ملبس ترابا, al-kafr = al-ghiṭāʾ. No statement that covering unites the entry. |
| 24 | Four kinds = scheme sorting a religious concept, no source given | my interpretation, labelled "In our reading" | Entry gives no attribution. |
| 25 | Lisān: similar four-part scheme, different members, credited to "some of the learned" | Displayed Lisān kfr | "قال بعض أهل العلم: الكفر على أربعة أنحاء: كفر إنكار بأن لا يعرف الله أصلا ولا يعترف به، وكفر جحود، وكفر معاندة، وكفر نفاق" (continues "وفي التهذيب…", i.e. via al-Azharī). Members differ: inkār vs Muḥīṭ's "القلب واللسان". |
| 26 | Poet al-Mutalammis named for river al-Kāfir without quotation; editor supplies line | Displayed kfr; print vol. 6, p. 251, n. 23 | "والكافِرُ: نَهرٌ معروفٌ فيه ماءٌ غَمْرٌ في قَوْلِ المُتَلَمِّسِ". n. 23: "ورد في ديوانه:٦٥، ونصُّ البيت فيه: وألْقَيتها في الثِّنيِ من جنب كافرٍ …". |
| 27 | kufr ʿalā kufr glossed bughḍ; other dictionaries read kafr ʿalā kafr = baʿḍ ʿalā baʿḍ; our Muḥkam shows it | print vol. 6, p. 250, n. 17; displayed Muḥkam kfr | n. 17: "هكذا ضُبطت الجملة في الأصول، وفي المحكم واللسان والتاج: كَفْر على كَفْرٍ أي بَعْض على بَعْض." Muḥkam displayed: "وقول العرب: كفر على كفر: أي بعض على بعض." (Tāj displayed has the same.) بغض / بعض differ by the dot on غ. |
| 28 | Material from the 8th-c. ʿAyn, al-Khārzanjī's 10th-c. gleanings, unnamed sources | claims 12–14, 20 | — |
| 29 | al-Ṣaghānī's al-ʿUbāb and Tāj al-ʿArūs quote it very often | Āl Yāsīn p. 9 n. 2; p. 33 | n. 2 lists users: "كفقه اللغة للثعالبي … والعباب والتكملة والذيل والصلة للصغاني … والقاموس المحيط للفيروزابادي … وتاج العروس للزبيدي … وفي كثير من صفحاته"; p. 33: "وإِلى ما جاء في العباب وتاج العروس منقولاً عن المحيط وهو كثير جداً". |
| 30 | On our site Tāj cites "Ibn ʿAbbād" in >250 entries | my count (§1) | 269. |
| 31 | onOurSite: Efw note refers only to «عفى» | print vol. 2, p. 170 | "عفو عفى: «عفى» أهْمَلَه الخَليلُ وحَكاه الخارْزَنْجِيّ." |
| 32 | onOurSite: rfq opens with note placed under another root | print vol. 5, p. 373 | "رذق: مُهْمَلٌ عنده (٨). الخارزنجيُّ (٩): الرَّوَاذِقُ: ما طُبِخَ من لَحْمٍ …" |
| 33 | Period 326–385 AH / 938–995 CE | Āl Yāsīn p. 10; Iranica | Āl Yāsīn: "المولود في اليوم السادس عشر من شهر ذي القعدة الحرام سنة ٣٢٦ هـ‍ في أصح الروايات، والمتوفى عام ٣٨٥ هـ‍"; Iranica: born 14 Sept 938, died 30 March 995. Ibn Khallikān p. 231: born 326, died 24 Ṣafar 385 at Rayy. |

---

## 3. Examples considered

- **ظ ل م (Zlm)** — CHOSEN, close reading + comparison with Kitāb al-ʿAyn (both display it). Shows: shared wording with the ʿAyn; poets and Q 31:13 dropped; added senses; unsourced "aṣl" formula; Qur'an cited only as evidence of a particular sense (Q 18:33). Qur'an frequency 315.
- **ك ف ر (kfr)** — CHOSEN. Shows unattributed theological classification (compare Lisān, which attributes a similar scheme), a poet named but not quoted, a textual crux (bughḍ/baʿḍ) visible against al-Muḥkam. Not displayed in Kitāb al-ʿAyn. Frequency 525.
- **غ ر ف (grf)** — CHOSEN (short): the explicit "قال الصاحب" voice, checking Abū Ḥanīfa's autograph.
- **ز و ر (zwr)** — CHOSEN (one sentence): "تصحيف عندي" against al-Khārzanjī.
- **ع ف و (Efw)** — used only in onOurSite (note on the lost quotation marks). Would otherwise be a good Qur'anic example (al-ʿafwa = al-faḍl "surplus" beside Q 2:219), but the entry's opening note is misleading as stored, so not used as a method example.
- **ع ذ ب (E*b)** — considered for the ʿAyn comparison: the Muḥīṭ keeps ʿAyn's senses (ʿādhib/ʿadhūb, "neither fasting nor breaking fast", "nothing between him and the sky", ʿadhabat al-sawṭ, al-ʿUdhayb) without its five verse citations (ʿAbīd, Ḥumayd, anonymous, al-Nābigha al-Jaʿdī, anonymous) and adds many senses. Rejected as redundant with Zlm. Noted: neither displayed entry glosses ʿadhāb "punishment"; also Muḥīṭ "المعذب … نعتاً للفاسق" vs ʿAyn "للعاشق" (variant, unexplained).
- **ر ز ق (rzq)** — rejected as main example: rizq glossed only "maʿrūf" (well known). Could illustrate terseness.
- **س ب ل (sbl)** — Tāj: "والسبل: الأنف، يقال: أرغم الله سبله، والجمع سبال، كما في المحيط" matches our Muḥīṭ entry; but Tāj "والسبل: السب والشتم، يقال: بيني وبينه سبل، كما في المحيط" vs our Muḥīṭ "وبَيْني وبَيْنَه سَبَلٌ: أي سَبَبٌ" (another variant). Rejected for word budget.
- **ر ف ق (rfq)** — site-data issue only.

---

## 4. Site data issues found

1. **rfq** (entry_id 9061): opening note "رفق مُهْمَلٌ عنده. الخارزنجي: الرَّوَاذق…" belongs to root **رذق** (edition vol. 5, p. 373). Harmonized English says al-Khalīl left رفق untreated — false.
2. **Efw** (entry_id 3183): "أهمله الخليل" applies only to «عفى» (edition vol. 2, p. 170). Faithful translation and harmonized English say al-Khalīl omitted the root — false (the ʿAyn entry for ʿ-f-w is displayed on our site).
3. **kfr** (entry_id 568) harmonized English opens "whose unifying thread is covering/concealing" — the author does not say this; he links only some senses to covering.
4. Stored date 995 and label "al-Ṣāḥib b. ʿAbbād" are correct (death 385 AH / 995 CE).
5. hawramani's intro to the work calls him "a Persian Shiite scholar"; Iranica says "Although not himself a Shiʿite…" (not displayed on our site as far as I know; FYI only).

---

## 5. Open questions / evidence gaps

- Not consulted (inaccessible here): Baalbaki, *The Arabic Lexicographical Tradition* (2014) — Google Books search returned nothing usable; EI² "Ibn ʿAbbād" (Cahen & Pellat); Pellat in *Abbasid Belles-Lettres* (1990); Āl Yāsīn, *al-Ṣāḥib b. ʿAbbād* (1957); Ḥusayn Naṣṣār, *al-Muʿjam al-ʿArabī*. The guide leans on Āl Yāsīn's introduction, the al-Jubūrī thesis summary, Haywood, Iranica and Ibn Khallikān.
- al-Jubūrī: the alukah page labels the study "Masters resume" but the text calls it a doctoral thesis ("موضوع دراستي للدكتوراه", "أطروحة للدكتوراه"). Guide says "doctoral thesis". Only the published summary was read.
- al-Ḥayyālī: only the publisher's description; no year/ISBN visible.
- Birthplace disputed: Iranica "Ṭalaqānča … 20 miles south of Isfahan"; Ibn Khallikān "بإصطخر، وقيل: بالطالقان". Omitted from the guide.
- Size: Ibn Khallikān "seven volumes"; Haywood reports al-Suyūṭī "ten". Omitted.
- Ibn Khallikān says it was arranged "على حروف المعجم"; Haywood calls this "ambiguous, if not misleading" — the actual order is phonetic. Omitted.
- al-Jubūrī counts 8,117 roots in al-Muḥīṭ vs 5,800 in al-ʿAyn (his count). Omitted.
- The author's intro says "قرأتُ لشيخنا أبي العباس المبرّد" though al-Mubarrad died (286/899) before Ibn ʿAbbād's birth; unexplained. Omitted.
- The source of the four-kinds-of-kufr scheme in al-Muḥīṭ is unknown.
- Identity of "Abū Ḥanīfa" in grf not established from a consulted source (likely al-Dīnawarī; not asserted).
- My counts (verse lines, Qur'an markers, Tāj citations) are regex-based and approximate.
- Whether hawramani took its text directly from the old Shamela file or from a common source cannot be proven; only textual identity was shown.

---

## 6. Addendum (revision round 1, 2026-09-26)

- **al-Jubūrī on criticism** (alukah, re-downloaded): conclusions say "كان مهتمًّا بالنقد اللغوي في المجال الدلالي والمجال الصرفي والمجال النحوي … فيما يتعلق بالتصحيف، وكذلك تقويم اللغات والمفاضلة بينها، هذا فضلًا عن نقده لأصحاب المعجمات كالخليل والخارزنجي". ToC: النقد اللغوي pp. 233–257; نقد أصحاب المعجمات pp. 249–257 (نقد الصاحب للخليل 249–252; للخارزنجي 252–255; نقد الخارزنجي للخليل 255–257). So first-person/critical remarks are "rare" only in our 836 displayed entries.
- **First-person remarks in displayed entries** (grep): قال الصاحب in qEd, grf; عندي as a judgement in zwr, mrd; unattributed correction in qTr ("والصحيح أنه غير مهموز").
- **Abū Ḥanīfa in grf**: print vol. 5, p. 67 (Shamela 83/1963), editor's n. 34 only notes the passage is missing in MS ت; no identification. Āl Yāsīn's intro (vol. 1, pp. 9–35) and al-Jubūrī's summary never mention Abū Ḥanīfa/al-Dīnawarī. Lisān/Muḥkam/Tāj grf quote "أبو حنيفة" on the plant but never with a nisba. Identification with al-Dīnawarī remains unsourced; not asserted.
- **Letter order**: Āl Yāsīn vol. 1, p. 15 has the bāb sequence and "مقسمة على مخارجها الصوتية"; the throat-first order itself is in the author's intro, vol. 1, pp. 59–60 ("ووجد مخرج الكلام كله من الحلق…"; letter table ع ح هـ خ غ حلقية … ف ب م شفوية).
- **رذق**: no root page on the site (find-root "No match"; /api/root/r*q → 404), so it cannot be linked even with `none`.
- **Harmonized English**: Muḥīṭ Zlm heading "'OUT OF PLACE' — CONCRETE EXTENSIONS OF ẒULM"; kfr "whose unifying thread is covering/concealing". Neither is in the original; the guide now warns readers.
- **Lisān kfr four kinds** (entry 158): inkār (defined "أن يكفر بقلبه ولسانه ولا يعرف ما يذكر له من التوحيد"), juḥūd, muʿānada, nifāq — i.e. the Muḥīṭ's first three plus inkār (≈ the Muḥīṭ's "heart and tongue").
