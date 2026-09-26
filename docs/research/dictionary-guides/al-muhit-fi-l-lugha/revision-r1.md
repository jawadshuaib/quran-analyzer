# Revision round 1: al-muhit-fi-l-lugha

Reviser, 2026-09-26. Input: `verification-r1.md` (70 claims: 65 S, 5 NQ, 0 U; 1 must-fix brief issue; 4 suggestions).
File edited: `roots/frontend/src/content/dictionary-guides/guides/al-muhit-fi-l-lugha.ts` (lede unchanged; body and onOurSite revised).
Validator after revision: `=== al-muhit-fi-l-lugha — ok`, 11 root links (9 distinct pairs), 4 excerpts, **1,122 words** (lede + body), no errors, no warnings.

Sources I opened again for this round: the alukah.net page for al-Jubūrī (downloaded in full), Shamela book 83 pages 2–45 (vol. 1 pp. 9–63: editor's introduction and author's introduction) and pages 1962–1964 (vol. 5 pp. 66–68, the غرف entry with the editor's notes). Displayed entries re-read with `_dict_guide_tool.py`: Muḥīṭ Zlm (593), kfr (568), grf (8051), rfq (9061); ʿAyn Zlm (287); Lisān kfr (158); Lisān, Muḥkam, Tāj grf. Local API checked for root `r*q`.

## Flagged claims

### C38 (NQ): "Ibn ʿAbbād keeps the senses and drops every poet, and the verse as well"
- **Now:** "Ibn ʿAbbād keeps most of these senses but drops every poet, and that verse as well:"
- Evidence re-checked: ʿAyn entry 287 has "وليلةٌ ظَلْماءُ [ويَومٌ مظلم]: شديد الشَّرِّ. وأَظْلَمَ فلانٌ علينا البيت: إذا أسمَعَك ما تكرَهْ", neither of which is in Muḥīṭ entry 593. "That verse" now points unambiguously to Q 31:13. The Muḥīṭ's own Qur'an quotations (Q 18:33, Q 36:37) do not conflict: the next paragraph already says Q 18:33 is quoted for a particular sense.

### C45 (NQ): "Most entries speak impersonally …"
- **Now:** "Many statements are impersonal, introduced by 'it is said' (*wa-qīla*) or 'they say', and his sources usually go unnamed.[^jubouri]"
- Evidence (alukah, al-Jubūrī conclusions): "وقد تبيَّن لنا أن الصاحب عندما كان يعتمد على أقوال اللغويين والشيوخ لم يكن يصرح بأسمائهم … ولذا كثرت عنده عبارات مثل: (قال، قيل، قالوا، يقولون)". That supports "many" and "usually unnamed", not "most entries".

### C48 (NQ): "Such remarks are rare; they show a compiler checking copies."
- **Now:** "Such remarks are rare in the entries we display, though a full study of the book gives a whole section to his linguistic criticism, including of al-Khalīl and al-Khārzanjī.[^jubouri]"
- "Rare" is limited to our copy. My own grep of the 836 displayed entries: "قال الصاحب" in 2 (qEd, grf); first-person judgement with عندي in 2 (zwr "وهو تصحيف عندي", mrd "وهذا عندي موضعه المعتل"); one more unattributed correction, qTr "والصحيح أنه غير مهموز". (Other عندي hits are ordinary example sentences.)
- Evidence for the new clause (alukah, same page):
  - Conclusions: "كما تبين لنا أن الصاحب كان مهتمًّا بالنقد اللغوي في المجال الدلالي والمجال الصرفي والمجال النحوي وغير ذلك فيما يتعلق بالتصحيف، وكذلك تقويم اللغات والمفاضلة بينها، هذا فضلًا عن نقده لأصحاب المعجمات كالخليل والخارزنجي".
  - Table of contents: "النقد اللغوي 233-257 … نقد أصحاب المعجمات 249-257: أولًا. نقد الصاحب للخليل 249-252؛ ثانيًا. نقد الصاحب للخارزنجي 252-255؛ ثالثًا. نقد الخارزنجي للخليل 255-257".
  - Chapter summary: "ثم ختمناه بالنقد اللغوي الذي اشتمل عليه هذا المعجم".
- I dropped "they show a compiler checking copies" to save words. The two examples show it on their own.

### C52 (NQ): Lisān "similar four-part scheme, with different members"
- **Now:** "The Lisān al-ʿArab gives nearly the same scheme, credited to 'some of the learned' (*baʿḍ ahl al-ʿilm*): Ibn ʿAbbād's first three kinds, plus *inkār*, explained as unbelief 'with his heart and his tongue'."
- Evidence (displayed Lisān kfr, entry 158): "قال بعض أهل العلم: الكفر على أربعة أنحاء: كفر إنكار بأن لا يعرف الله أصلا ولا يعترف به، وكفر جحود، وكفر معاندة، وكفر نفاق … فأما كفر الإنكار فهو أن يكفر بقلبه ولسانه ولا يعرف ما يذكر له من التوحيد". "His first three kinds" (juḥūd, muʿānada, nifāq) are the Lisān's second to fourth, so I wrote "Ibn ʿAbbād's first three kinds" to avoid implying the Lisān lists them first.

### C53 (NQ): "The rest of the entry is concrete"
- **Now:** "Much of the rest is concrete: …" (it now opens a new paragraph).
- Evidence: entry 568 also has "والكَفّارَةُ: ما يُكَفَرُ به الخَطِيْئَةُ والذَّنْبُ", "والتَكْفِيْرُ: إيْمَاءُ الذِّمَيّ برأسِه", "والكافُورُ … وعَيْنُ ماءٍ في الجَنَّةِ".

## Brief issues

### Must-fix: the default English view contradicts the essay's two method points
Re-checked: the harmonized English for Muḥīṭ Zlm (entry 593) has the heading "'OUT OF PLACE' — CONCRETE EXTENSIONS OF ẒULM" over items 11–13. For kfr (entry 568) it opens "This entry treats the root k-f-r, whose unifying thread is covering/concealing." The original text states neither.
Fixed in three places:
1. Body, Zlm paragraph, right after the point about *aṣl*: "(Our English version groups several senses under that idea; the 'Original Text' view shows he does not.)"
2. Body, kfr paragraph: "Ibn ʿAbbād ties several senses to covering but never says that covering unites them (our English version, again, says it does)."
3. onOurSite: "The default English view sometimes sorts an entry into groups the author does not make: at present it files several ظ ل م senses under an 'out of place' heading and gives the ك ف ر senses a 'unifying thread' of covering. For his own order and wording, use 'Original Text'."
"At present" is there because the site team may correct these renderings (see Site-data issues). If they do, delete the two body parentheticals and the onOurSite sentence.

### Suggestion: "Abū Ḥanīfa's original" (grf)
Partly adopted: the reader is told the word is a tree name and that the entry does not say which Abū Ḥanīfa is meant ("That is from غ ر ف, on the tree *gharaf*; the entry does not say which Abū Ḥanīfa."). I did **not** identify him as al-Dīnawarī. I looked for a source and found none that I could cite:
- The editor's notes on this passage (Shamela, vol. 5, p. 67, n. 34) only record that the passage is missing from MS ت: "(٣٤) من قوله: (قال الصاحب) إلى قوله هنا: (والواحدة غرفة) سقط من ت."
- Āl Yāsīn's introduction (vol. 1, pp. 9–35) and al-Jubūrī's summary never mention Abū Ḥanīfa or al-Dīnawarī.
- The displayed Lisān, Muḥkam and Tāj grf entries quote "Abū Ḥanīfa" repeatedly on the plant *gharaf*, but none names him in full.
"*gharaf* is the name of a tree" comes from the entry itself: "والغَرَفُ - على وَزْنِ مَطَرٍ -: شَجَرُ القِسِيِّ" and "قال الصاحب: الصحيح في الغرف فتح الراء … والواحدة غرفة".

### Suggestion: name the root of the rfq notice
Adopted in substance, not in the suggested form. A `[[root:…|none|…]]` link is impossible: the site has no root page for رذق. `find-root رذق` gives "No match", `_dict_guide_tool.py root 'r*q'` gives "no dictionary entries", and `/api/root/r*q` returns 404, so the validator would reject the link. Writing the letters out spaced would be a bare-root validation error. Instead, onOurSite now names the word the note is about: "The ر ف ق entry opens with a short note on *al-rawādhiq*, meat cooked with seasonings, which the edition places under the root of that word; our copy has no entry for that root." The gloss translates the stored note ("الرَّوَاذق: ما طُبخَ من لَحْمٍ وخُلِطَ بأخْلاطِه"). The placement comes from vol. 5, p. 373 ("رذق: مُهْمَلٌ عنده … الخارزنجيُّ: الرَّوَاذِقُ …"), already verified as C69.

### Suggestion: light trim
- Biography: dropped the emirs' names ("the Buyid emirs Muʾayyad al-Dawla and Fakhr al-Dawla" became "two Buyid emirs", still supported by Iranica, C14). Dropped "patron of a famous library", which is true (C17) but does not explain the dictionary. Tightened the Haywood clause ("he passed over his teacher's alphabetical arrangement for al-Khalīl's"; Haywood p. 63: "he preferred al-Khalil's method to that used by his master").
- Kufr paragraph: split in two (classification plus Lisān; then the concrete senses and the *bughḍ/baʿḍ* crux). Dropped the al-Mutalammis sentence (C55, supported but not essential). Its footnote citation 6:251 n. 23 went with it.
- Dropped "Its reliability was disputed early." (the next sentence carries the point) and "is a wide net" in the closing paragraph.
- Shortened the al-Azharī/al-Layth clause ("al-Layth ibn al-Muẓaffar" became "al-Layth"). The claim is unchanged.
- Net effect: the fixes add about 60 words and the trims remove about 35. The essay is now 1,122 words by the validator (1,097 before). I did not trim further: the remaining paragraphs each carry an example or a point the brief asks for.

### Suggestion: al-yasin locator
Adopted. "[^al-yasin|vol. 1, pp. 15–16]" is now "[^al-yasin|vol. 1, p. 15]". Vol. 1 p. 15 (Shamela page 8): "وقد سار فيه مؤلفه على منهج الخليل في العين؛ سواءاً فيما يتعلق بتسلسل الحروف مقسمة على مخارجها الصوتية؛ أو بترتيب الأبواب داخل كل حرف، ابتداءً بباب المضاعف الثنائي، ثم باب الثلاثي الصحيح، ثم باب الثلاثي المعتل، ثم باب اللفيف، ثم باب الرباعي، ثم باب الخماسي." p. 15 does not state "from the throat outward", so I added a citation to the author's introduction: "[^muhit-ed|vol. 1, pp. 59–60]". Vol. 1 p. 59: "ووجد مخرج الكلام كله من الحلق، فصير أولاها بالابتداء أدخل حرف منها في الحلق"; p. 60: "العين، فجعلها أول الكتاب، ثم ما قرب منها؛ الأرفع فالأرفع", with the letter table from ع ح هـ خ غ "حلقية" to ف ب م "شفوية". This source was already on the page and is already cited for vol. 1 p. 59.

## Removed claims
- "[He was] the patron of a famous library": trimmed for relevance. Supported (C17), not removed for accuracy.
- The emir names Muʾayyad al-Dawla and Fakhr al-Dawla: trimmed ("two Buyid emirs" kept).
- "He names the poet al-Mutalammis for a river called al-Kāfir without quoting him; the editor supplies the line (6:251 n. 23)": trimmed for density. Supported (C55).
- "Its reliability was disputed early.": a redundant lead-in.
- "The Lisān has a similar four-part scheme, with different members": replaced (C52). "With different members" was wrong.
- "Most entries speak impersonally": replaced (C45).
- "Such remarks are rare; they show a compiler checking copies": replaced (C48).
- "keeps the senses": replaced (C38).
- "The rest of the entry is concrete": replaced (C53).

## New claims
1. **The default English view files several Zlm senses under an "out of place" heading and gives the kfr senses a "unifying thread" of covering. The author does not.** Evidence: `_dict_guide_tool.py entry Zlm/kfr al-sahib-bin-abbad-al-muhit-fi-l-lugha`, HARMONIZED ENGLISH: "\"OUT OF PLACE\" — CONCRETE EXTENSIONS OF ẒULM"; "whose unifying thread is covering/concealing". ORIGINAL TEXT: no grouping and no unifying statement (see C41, C54).
2. **Al-Jubūrī's study gives a whole section to Ibn ʿAbbād's linguistic criticism, including of al-Khalīl and al-Khārzanjī.** Evidence: alukah.net/library/0/148209, ToC "النقد اللغوي 233-257 … نقد الصاحب للخليل 249-252 … نقد الصاحب للخارزنجي 252-255", and the conclusion quoted under C48.
3. **In the grf entry *gharaf* is a tree, and the entry does not identify Abū Ḥanīfa.** Evidence: displayed entry 8051 ("والغَرَفُ - على وَزْنِ مَطَرٍ -: شَجَرُ القِسِيِّ"; the remark names only "أبي حنيفة"). Print vol. 5, p. 67 and its notes 31–35 add no identification.
4. **The rfq note is about *al-rawādhiq*, "meat cooked with seasonings", and our copy has no entry for its root.** Evidence: displayed entry 9061 "الرَّوَاذق: ما طُبخَ من لَحْمٍ وخُلِطَ بأخْلاطِه"; print 5:373 heading "رذق"; site has no r*q root (find-root "No match", API 404).
5. **The letter order runs from the throat outward (author's introduction).** Evidence: Muḥīṭ vol. 1, pp. 59–60, quoted above. The claim itself is not new (C26); only the citation is.
6. **The Lisān's four kinds are Ibn ʿAbbād's first three plus *inkār*, explained as unbelief "with his heart and his tongue".** Evidence: Lisān entry 158, quoted under C52.

## Disputed
None. I accepted all five qualifications as the verifier worded them, with small wording changes explained above.

## Site-data issues (for the site team; not edited)
1. Harmonized English, Muḥīṭ Zlm (593): the heading "'OUT OF PLACE' — CONCRETE EXTENSIONS OF ẒULM" imposes a grouping the original does not make. Harmonized English, Muḥīṭ kfr (568): "whose unifying thread is covering/concealing" is not in the original. If these are corrected, remove the two body parentheticals ("Our English version groups…", "our English version, again, says it does") and the corresponding onOurSite sentence.
2. From research-notes §4 and still open: rfq (9061) carries a note that belongs under رذق, and Efw (3183) loses the quotation marks that limit "أهمله الخليل" to «عفى». The harmonized English for both says al-Khalīl omitted the whole root, which is wrong.
