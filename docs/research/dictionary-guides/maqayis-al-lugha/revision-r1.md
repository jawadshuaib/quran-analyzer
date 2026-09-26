# Maqāyīs al-Lugha: revision, round 1

Reviser's log for `roots/frontend/src/content/dictionary-guides/guides/maqayis-al-lugha.ts`, answering `verification-r1.md` (2026-09-26).

Validator after revision: `node scripts/validate-dictionary-guides.mjs maqayis-al-lugha` → "1/1 guides pass", 0 errors, 0 warnings. 8 root links (7 distinct pairs), 3 excerpts valid, **1,099 words** (lede + body, excluding excerpts; was 1,100). The page was also checked in the local browser: the new guide link resolves to `/classical-dictionaries/kitab-al-ayn`, the ʿAyn root link to `/root/Ebd#dict-al-khalil-b-ahmad-al-farahidi-kitab-al-ain`, and the al-Ṣāḥibī source link to `/9977/50`.

Sources re-opened for this round (Shamela HTML downloaded and read; Hārūn ed. = shamela.ws/book/21710, page id = print page + offset):
- Hārūn, editor's introduction pp. 39–44 (/37–/42)
- Author's preface vol. 1 pp. 3–5 (/47–/49)
- Vol. 1 pp. 169 (/213), 328–29 (/372–/373)
- Vol. 2 pp. 372, 386 (/932, /946)
- Vol. 4 p. 205 (/1746)
- Vol. 6 pp. 72–73 (/2606–/2607), 150–51 (/2683–/2684)
- *al-Ṣāḥibī* p. 44 (shamela.ws/book/9977/50)
- Displayed entries via `_dict_guide_tool.py`: Ebd (Maqāyīs 519; ʿAyn 372), jvm (9425) and kfr (163)

**Not re-opened: Baalbaki.** Google Books returned a reCAPTCHA wall to every route (curl, browser pane, the user's Chrome, WebFetch), and the Books API quota was exhausted. I did not try to get past the CAPTCHA and did not use pirated copies. No new Baalbaki claim was added. The two Baalbaki sentences I touched keep the substance the verifier confirmed (C17, C48), with the locator corrected as the verifier asked. The research notes' verbatim p. 356 transcription agrees.

---

## Changes by flagged claim

### C33 [NQ] "a chapter of their own at the end of each letter" → fixed
New: "…most letters end with a chapter on longer words.[^harun-ed|editor's introduction, pp. 42–44]"
- Hamza has no such chapter. Vol. 1 p. 169 (/213) ends أيى, then "تم كتاب الهمزة ويتلوه كتاب الباء".
- Wāw has none either. Vol. 6 p. 150 (/2683) ends وهن, then "تم كتاب الواو واللّه أعلم بالصواب". The next page, /2684, is "كتاب الياء".
- The bāʾ chapter is on vol. 1 p. 328 (/372). The hāʾ chapter is on vol. 6 pp. 72–73 (/2606–/2607) and ends "تم كتاب الهاء".
- Hārūn on the plan of each book, intro p. 43 (/41): "ثم قسم كل كتاب إلى أبواب ثلاثة أولها باب الثنائى المضاعف والمطابق، وثانيها أبواب الثلاثى الأصول من المواد، وثالثها بابُ ما جاء على أكثر من ثلاثة أحرفٍ أصلية".
- The same sentence also answers the verifier's "arrangement" suggestion (see New claims 1).
- A side note, not used in the essay: Hārūn's footnote 3 at /2683 reads "أغفل ابن فارس أن يورد بعد هذا (باب ما جاء من كلام العرب على ثلاثة أحرف أوله هاء)". Its examples (الهذربة، الهرجاب…) begin with hāʾ, yet the hāʾ book does have such a chapter (/2606–7). The note as Shamela gives it looks garbled. So the guide rests "most letters" on the two books that visibly end without the chapter, not on this note.

### C34 [NQ] three kinds cited to vol. 1 pp. 328–29 → fixed
- Now: "Of these, 'most of what you see,' he says, is carved (*manḥūt*): two words are taken and a new one is carved from them, keeping a share of each. The rest were 'set down' with no room for measure (our translation).[^harun-ed|vol. 1, pp. 328–29]"
- Evidence, p. 328 (/372): "وذلك أنّ أكثر ما تراه منه منحوتٌ. ومعنى النَّحت أن تُؤخَذَ كلمتان وتُنْحَتَ منهما كلمةٌ تكون آخذةً منهما جميعاً بحَظٍّ".
- Evidence, p. 329 (/373): "إنَّ ذلك على ضربين: أحدهما المنحوت الذى ذكرناه، والضَّرْب الآخر [الموضوع] وضعاً لا مجالَ له فى طُرق القياس".
- The third class is now presented separately, as what the entries do: "In practice he adds a third kind, three-letter words with letters added: *kanfalīla*, a bushy beard, is *kafl* (gathering) enlarged."
- Evidence, displayed kfr entry 163 (the appended kāf chapter): "(الكنفليلة) : اللحية الضخمة. وهذا مما زيدت فيه النون مع الزيادة في حروفه، وهو من الكفل، وهو جمع الشيء، وقد ذكرناه".
- The same practice appears on p. 329 itself: "(البلْعُوم) … مأخوذٌ من بَلِعَ، إلاّ أنّه زِيد عليه ما زِيدَ".
- The jīm chapter's introduction names all three kinds. It is visible in the displayed jvm entry 9425: "فمنه ما نحت من كلمتين… ومنه ما أصله كلمة واحدة وقد ألحق بالرباعي والخماسي بزيادة تدخله. ومنه ما يوضع كذا وضعا". "In practice" is therefore understated, not overstated. I did not name the jīm introduction in the body because the word budget had no room.

### C39 [NQ] "Quoted voices are marked" → fixed (wording more cautious than the verifier's; see Disputed)
- Now: "Some quoted voices are marked: 'al-Khalīl said' introduces the distinction between God's servants (*ʿibād*) and owned slaves (*ʿabīd*). Where a quotation ends is not. Soon after, 'we have not heard them derive a verb from it' reads 'I have not heard' in [the Kitāb al-ʿAyn entry for this root], where much of the rest also appears, often closely worded, but with no statement of a shared sense."
- Maqāyīs, displayed entry 519: "قَالَ الْخَلِيلُ: إِلَّا أَنَّ الْعَامَّةَ اجْتَمَعُوا عَلَى تَفْرِقَةِ مَا بَيْنَ عِبَادِ اللَّهِ وَالْعَبِيدِ الْمَمْلُوكِينَ. يُقَالُ هَذَا عَبْدٌ بَيِّنُ الْعُبُودَةِ. وَلَمْ نَسْمَعْهُمْ يَشْتَقُّونَ مِنْهُ فِعْلًا".
- Hārūn vol. 4 p. 205 (/1746) has the same "ولم نسمَعْهم", so this is the edition's reading, not a hawramani variant.
- *Kitāb al-ʿAyn*, displayed entry 372: "إنّ العامّة اجتمعوا على تفرقة ما بين عباد الله، والعبيد المملوكين. وعبدٌ بيّن العبودة، وأقرّ بالعبوديّة، ولم أسمعهم يشتقون منه فعلاً".
- "Often closely worded", compared in the same two entries:
  - ʿAyn: "وبعيرٌ مُعَبَّدٌ: مهنوء بالقَطِران". Maqāyīs: "الْبَعِيرُ الْمُعَبَّدُ، أَيِ الْمَهْنُوءُ بِالْقَطْرَانِ".
  - ʿAyn: "والعَبَدُ: الأنفة والحميّة". Maqāyīs: "الْعَبَدُ، مِثْلُ الْأَنَفِ وَالْحَمِيَّةِ".
  - The Nimr b. Saʿd verse and "تعبّد فلان فلاناً… وإن كان حراً" appear in both.

### C43 [NQ] "reports only the reading that fits its scheme, as other people's interpretation" → fixed
- Now: "The *Maqāyīs* gives only the reading that serves its second *aṣl*." This is the verifier's wording.
- "As other people's interpretation" was dropped as a separate clause. The sentence just before already gives the passive "has been interpreted" (*wa-fussira*).
- Evidence, entry 519: "وَفُسِّرَ قَوْلُهُ … أَيْ أَوَّلُ مَنْ غَضِبَ عَنْ هَذَا وَأَنِفَ مِنْ قَوْلِهِ", filed under "وَالْأَصْلُ الْآخَرُ".

### C47 [NQ] + must-fix brief issue (unreconciled Hārūn vs Baalbaki) → fixed
- Removed the narrator's own claim, "The book drew little attention before modern times."
- Now: "When Hārūn edited it, from the single manuscript he could find, he knew of only one medieval author who mentions the book, Yāqūt, and wrote that scholars had noticed it only recently.[^harun-ed|editor's introduction, pp. 39–40] Baalbaki's later survey finds it used, if narrowly: Ibn Manẓūr's Lisān al-ʿArab never quotes its *uṣūl*, but al-Ṣaghānī often cites them, and some of his quotations passed into al-Zabīdī's Tāj al-ʿArūs.[^baalbaki|pp. 355–56]"
- Hārūn p. 39 (/37): "ولم أجدْ أحداً غير ياقوت يذكر هذا الكتاب لابن فارس".
- Hārūn p. 40 (/38): "وهذا الكتاب لم يسترع انتباه العُلماء إلا منذ عهد قريب … فإنى لم أجِد أمامى منه إلا نُسخة واحِدة مودعة بِدار الكتب المصرية".
- The locator changed from pp. 39–41 to pp. 39–40, because nothing now cited is on p. 41.
- How the reconciliation works: Hārūn's statement is framed as what he knew when he edited the book. Baalbaki's evidence is introduced as later and as showing narrow use, so the two no longer read as a contradiction.
- I did **not** add the verifier's other Baalbaki points (Bū Jaʿfarak via Yāqūt; "fuller recognition waited until the twentieth century"), because I could not open Baalbaki this round.

### C48 [NQ locator] → fixed
The locator changed from `[^baalbaki|p. 356]` to `[^baalbaki|pp. 355–56]`, following the verifier's reading of the pages. The substance ("does not mention a single view of Ibn Fāris's on the uṣūl"; al-Ṣaghānī "often cites … the basic meanings that he assigns to the roots"; quotations passed to al-Zabīdī) matches research-notes §2 "Reception" (p. 356).

## Brief issues

- **[must-fix] Hārūn/Baalbaki contradiction:** fixed (see C47).
- **[suggestion] Arrangement:** added one sentence, sourced to Hārūn's intro pp. 42–44 (see New claims 1). I did not use Baalbaki p. 349 ("a special type of taqālīb") because I could not re-open it.
- **[suggestion] *Kitāb al-Manṭiq*:** resolved by compressing the source list to "two by Abū ʿUbayd, one by Ibn al-Sikkīt, and Ibn Durayd's *Jamhara*". The unrecognisable title is gone, and so is any need for the Baalbaki gloss I could not re-check. Hārūn's footnotes to the preface (/49) do not identify the book, so no Hārūn source was available for the gloss.
- **[suggestion] Word count:** trimmed to 1,099. Cuts made to fit the qualifications:
  - The source list was compressed.
  - "and a rare item is credited to whoever reported it" was cut.
  - "Almost every entry opens by naming the letters and giving a verdict" became "The verdict is typically…"; the lede still says a typical entry opens with a verdict.
  - The al-Ṣāḥibī clause on *ṣalāt* = *duʿāʾ* was cut. It was supported (C26) and was dropped only for length; the *kufr* half, the one that bears on the example, stays.
  - "not attributed to anyone" was cut as redundant.
  - "he has just described", "Q 43:81 shows what the sorting does" (now "Take Q 43:81") and "of another word he writes" (now "of another") were shortened.
  - "coat of mail" became "armour" (درع).
- **[suggestion] Guide link:** added `[[guide:kitab-al-ayn|Kitāb al-ʿAyn]]` at the first mention. The slug comes from registry.ts: `'al-khalil-b-ahmad-al-farahidi-kitab-al-ain': 'kitab-al-ayn'`.
- **[suggestion] al-Ṣāḥibī URL:** changed to `https://shamela.ws/book/9977/50`. It opens p. 44, "[باب الأسباب الإسلامية]", including "ونُقِلت من اللغة ألفاظ من مواضعَ إِلَى مواضع أخَر".

## Removed claims
1. "The book drew little attention before modern times." (narrator's voice; now attributed to Hārūn as what he wrote, p. 40)
2. "Others are three-letter words with letters added", as part of the classification cited to vol. 1 pp. 328–29. It is now presented as his practice (kanfalīla).
3. "Quoted voices are marked" as a generalisation. It is now "Some quoted voices are marked".
4. "…reports only the reading that fits its scheme, as other people's interpretation" (rephrased per C43)
5. "Hārūn found only one medieval author…" as an unqualified fact. It is now framed as what Hārūn knew when editing.
6. Removed only for length; the verifier marked all of these supported:
   - the *ṣalāt* = *duʿāʾ* clause from al-Ṣāḥibī
   - "a rare item is credited to whoever reported it"
   - "Almost every entry opens by naming the letters"
   - the titles of Abū ʿUbayd's two books and Ibn al-Sikkīt's *Kitāb al-Manṭiq*
   - "not attributed to anyone"

## New claims (each with its evidence)
1. **Arrangement.** "Under each first letter come doubled roots such as *radd*, then three-letter roots, in an order of Ibn Fāris's own; most letters end with a chapter on longer words." [harun-ed, editor's introduction, pp. 42–44]
   - Hārūn p. 42 (/40): "جرى ابن فارس على طريقة فاذَّةٍ بين مؤلفى المعاجم … سلك طريقاً خاصَّا به" and "فهو قد قسم مواد اللغة أوَّلاً إلى كتب، تبدأ بكتاب الهمزة وتنتهى بكتاب الياء".
   - p. 43 (/41): the three parts, quoted under C33, and "أن كل قسم من القسمين الأولين قد التُزم فيه ترتيب خاص، هو ألا يبدأ بعد الحرفِ الأوَّل إلا بالذى يليه".
   - p. 44 (/42): "هذا هو الترتيب الذي التزمه ابن فارس في كتابيه «المجمل» و «المقاييس»".
   - *radd* is a doubled root in the rāʾ book. Vol. 2 p. 372 (/932) opens "كتاب الرّاء[باب الراء وما معها فى الثنائى والمطابق][رز]…", and vol. 2 p. 386 (/946) has "[رد]الراء والدال أصلٌ واحدٌ مطّردٌ منقاس، وهو رَجْع الشَّئ". The rāʾ book begins at رز and reaches رد only after wrapping round, which illustrates the order.
   - "most letters": see C33.
2. **"The rest were 'set down' with no room for measure."** Vol. 1 p. 329 (/373), quoted under C34.
3. **Third kind in practice; *kanfalīla* = *kafl* (gathering) enlarged.** Displayed kfr entry 163, quoted under C34.
4. **"Where a quotation ends is not [marked]"; "we have not heard" = ʿAyn's "I have not heard"; the rest often closely worded.** Entries 519 and 372 and Hārūn vol. 4 p. 205, quoted under C39.
5. **Hārūn "wrote that scholars had noticed it only recently."** Intro p. 40 (/38): "وهذا الكتاب لم يسترع انتباه العُلماء إلا منذ عهد قريب".
6. **"Baalbaki's later survey finds it used, if narrowly".** This is my summary, not a new fact. It summarises the same p. 356 content the guide already carried (al-Ṣaghānī "quotes Ibn Fāris very frequently … often cites … the basic meanings that he assigns to the roots but stops short of following his method"; Lisān never cites his uṣūl), as transcribed in research-notes §2 and confirmed by verifier C48. "Later" is by date: Baalbaki 2014, Hārūn's 2nd ed. 1969–72.
7. **"His material comes from five books: … two by Abū ʿUbayd, one by Ibn al-Sikkīt…".** Preface vol. 1 pp. 4–5 (/48–/49): "ومنها كتابا أبى عُبيدٍ فى (غريب الحدِيث)، و (مصنَّف الغريب)"; "ومنها (كتاب المنطق) … عن ابن السكِّيتِ"; "فهذِه الكتبُ الخمسةُ معتمَدُنَا".

## Disputed
- **C39, partly.** The verifier proposed saying that "we have not heard them derive a verb from it" is al-Khalīl's remark "taken over unmarked". In the Maqāyīs the sentence comes two sentences after "قال الخليل". Arabic prose has no closing quotation mark, so it may be read as still inside al-Khalīl's quotation, now voiced as "we", or as Ibn Fāris's own. The guide therefore says only what the texts show: the quotation's end is not marked, and the *ʿAyn* has the same remark with "I". This is narrower than the verifier's wording, not a rejection of the finding.
- No other disagreements. Every NQ was applied as far as the evidence I could open allows.
