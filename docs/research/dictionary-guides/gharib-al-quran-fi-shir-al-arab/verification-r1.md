# Verification round 1 — gharib-al-quran-fi-shir-al-arab

Independent check of `roots/frontend/src/content/dictionary-guides/guides/gharib-al-quran-fi-shir-al-arab.ts` (2026-09-26). research-notes.md and revision files were NOT opened. Every source below was opened by the verifier; Shamela page numbers were read from each page's `data-page-num` (print pagination) and its volume selector.

Sources opened:
- ed1993 — https://shamela.ws/book/23622 (book card: غريب القرآن في شعر العرب ((مسائل نافع بن الأزرق…)), "ترقيم الكتاب موافق للمطبوع"); pages /4–/23, /44, /51, /54, /60, /247. Bibliographic data (eds. محمد عبد الرحيم وأحمد نصر الله, مؤسسة الكتب الثقافية, بيروت, ط1 1413/1993) is NOT on the Shamela card; corroborated by a bibliographic citation seen in search results (x.com/TurkiAldakhil/status/1820387508582048135) and the ketabpedia listing title "…ل احمد نصر الله"; p. 21 is signed "المحققان".
- itqan — https://shamela.ws/book/11728/449 (card: ed. Abū l-Faḍl Ibrāhīm, al-Hayʾa al-Miṣriyya, 1394/1974, 4 vols; breadcrumb "المجلد الثاني › النوع السادس والثلاثون"); pages /449–451 (pp. 67–69), /458–460 (pp. 76–78), /487–490 (pp. 105–108).
- bint — https://shamela.ws/book/12759/272 (card: al-Iʿjāz al-bayānī… wa-masāʾil Ibn al-Azraq, Dār al-Maʿārif, 3rd edn); pages /272–/288 (pp. 289–305).
- tarikh-baghdad — https://shamela.ws/book/736/6998 (card: Bashshār ʿAwwād Maʿrūf, Dār al-Gharb al-Islāmī 2002; volume selector = 12); pages /6998–/7002 (pp. 468–472), entry ٥٧٩٨.
- goldziher — https://archive.org/details/MN41643ucmf_1 (metadata: Goldziher, Die Richtungen der islamischen Koranauslegung, 1920); full text (djvu.txt) pp. 69–71.
- wansbrough — no URL in guide; full text consulted at archive.org (…/QuranicStudiesSourcesAndMethodsOfScripturalInterpretationByJohnWansbrough… _djvu.txt), pp. 216–218.
- samarrai — no URL in guide; found at https://archive.org/details/lis_ak87 (file lis_ak8709; OCR title page "مستل من مجلة رسالة الإسلام، العددان الخامس والسادس، السنة الثانية — مطبعة المعارف بغداد"). Read via OCR text/XML only; printed page numbers could not be read with certainty.
- hawramani — https://arabiclexicon.hawramani.com/abdullah-ibn-abbas-gharib-al-quran-fi-shir-al-arab/ (opens; describes "a 250-entry dictionary … question-and-answer format", also known as Masāʾil Nāfiʿ b. al-Azraq; does NOT name the printed edition it reproduces).
- Local data: `_dict_guide_tool.py entry` for kbd, mrD, bwr, qbs, xbt, snh (this dictionary) and kbd (ibn-manzur-lisan-al-arab); full dump of all 49 displayed entries (SQLite, same SHOWN filter).

## Claims table

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Gharīb al-Qurʾān fī Shiʿr al-ʿArab* / غريب القرآن في شعر العرب (title, titleAr) | SUPPORTED | Shamela card 23622; ed1993 p. 20 |
| C2 | titleGloss "The Qurʾan's Unfamiliar Words in the Poetry of the Arabs" | SUPPORTED | fair rendering of the Arabic |
| C3 | author "Attributed to ʿAbdullāh ibn ʿAbbās", عبد الله بن عباس | SUPPORTED | Shamela card: "عن الصحابي عبد الله بن عباس"; attribution disputed (Goldziher 70–71, Wansbrough 216–17) |
| C4 | period: d. 68 AH / 687–8; recorded versions late 9th–10th c. CE | SUPPORTED | ed1993 p. 12 n. 1 (d. 68/687 at al-Ṭāʾif); chain dated 288 and 344 AH (ed1993 p. 25); al-Mubarrad d. 285, Ibn al-Anbārī d. 328, al-Ṭabarānī d. 360 (bint pp. 289–292) |
| C5 | kind "Question-and-answer glossary" | SUPPORTED | all 50 displayed exchanges are Q&A |
| C6 | summary: questioner named as Nāfiʿ; brief gloss, then poetry as proof | SUPPORTED | ed1993 pp. 26–27 frame; entries |
| C7 | lede: frame story names Khārijite leader Nāfiʿ ibn al-Azraq | SUPPORTED | ed1993 p. 17 n. 11 ("رأس الأزارقة"), p. 26 |
| C8 | lede: he presses "Do the Arabs know that?"; answer always a line of poetry | SUPPORTED | 50/50 displayed exchanges contain تعرف العرب ذلك and أما سمعت + verse |
| C9 | lede: text attributed to Ibn ʿAbbās, shaped by transmitters, not a lexicon he wrote | SUPPORTED (interpretation) | variant routes/counts (bint pp. 289–304); Goldziher 70–71; Wansbrough 216–17 |
| C10 | The 1993 editors added the title so readers grasp the subject (p. 20) | SUPPORTED | ed1993 p. 20: "أضفنا إلى العنوان الرئيسي عنوانا جديدا وضروريا وهو: غريب القرآن في شعر العرب كي … يتفهم المراد منه" |
| C11 | Two editors, Beirut, 1993 (+ source citation: M. ʿAbd al-Raḥīm & A. Naṣr Allāh, Muʾassasat al-Kutub al-Thaqāfiyya) | SUPPORTED | ed1993 p. 21 signed "المحققان"; bibliographic citation (see above) |
| C12 | Earlier writers call it the *Masāʾil* of Nāfiʿ (Itqān 2:67) | SUPPORTED | Itqān 2:67: "أوعب ما رويناه عنه مسائل نافع بن الأزرق" |
| C13 | *gharīb* = rare or opaque words | SUPPORTED | standard sense; ed1993 p. 20 "الحرف الغريب" |
| C14 | Frame at the Kaʿba; Nāfiʿ and Najda accuse him; ask for *miṣdāq* from the speech of the Arabs, since Qurʾan came in clear Arabic (pp. 26–27) | SUPPORTED | ed1993 p. 26 "بفناء الكعبة"; p. 27 "وتأتينا بمصداقه من كلام العرب، فإن الله … أنزل القرآن بلسان عربي مبين" |
| C15 | Every displayed entry: phrase, gloss, وهل تعرف العرب ذلك؟, أما سمعت + verse | SUPPORTED | 44 وهل / 6 فهل; 50 أما سمعت; qbs has a narrative gloss and fwm extra witnesses, but the pattern holds |
| C16 | Our copy omits the frame; unnamed قال alternates | SUPPORTED (minor caveat) | true of the frame; note the fwm entry keeps "يا ابن أم الأزرق" |
| C17 | Ibn ʿAbbās the Prophet's cousin; died at al-Ṭāʾif 68 AH (pp. 12–13) | SUPPORTED | ed1993 p. 12 n. 1; p. 13 "ابن عمه" |
| C18 | Nāfiʿ head of the Azāriqa, killed 65/685 (p. 17 n. 11) | SUPPORTED | ed1993 p. 17 n. 11: "قتل نافع يوم دولاب … سنة (٦٥) هـ الموافق (٦٨٥) م" |
| C19 | Later reports praise him for teaching old poetry and battle-days alongside religion and law (Goldziher p. 71) | SUPPORTED | Goldziher p. 71: "Man rühmt von ihm, dass er ausser den religiösen und gesetzlichen Kenntnissen auch Belehrungen über … ajjām al-ʿarab, über alte Poesie … geboten habe" |
| C20 | Panel date 687 is his death, not the text's date | SUPPORTED | C4 |
| C21 | Ibn al-Ṭastī taught it in his mosque in 344 AH (955 CE) | SUPPORTED | ed1993 p. 25 "في مسجده بدرب رباح … سنة أربع وأربعين وثلاثمائة" |
| C22 | received from al-Sarī ibn Sahl at Jundīsābūr, 288 AH (~900) | SUPPORTED | ed1993 p. 25 |
| C23 | chain runs back through ʿĪsā ibn Daʾb (pp. 25–26) | SUPPORTED | ed1993 p. 26 "حدثنا عيسى بن دأب" |
| C24 | al-Khaṭīb (d. 1071): Ibn Daʾb transmitter of Arab lore, genealogy, tribal history; "was said to add to reports what was not in them" (vol. 12 p. 468) | SUPPORTED | TB 12:468 "راوية عن العرب … عالما بالنسب، عارفا بأيام الناس … وقيل: إنه كان يزيد في الأحاديث ما ليس منها" |
| C25 | Khalaf al-Aḥmar's charge of fabrication (p. 472) | SUPPORTED | TB 12:471–472 "كان خلف الأحمر ينسب ابن داب إلى الكذب"; "ابن داب يضع الحديث بالمدينة" |
| C26 | Other routes carry other selections | SUPPORTED | bint pp. 289–304 |
| C27 | Counts per Bint al-Shāṭiʾ: al-Mubarrad a handful, Ibn al-Anbārī 50, al-Ṭabarānī 31, al-Suyūṭī 190, two undated Cairo MSS 255 (pp. 289–303) | SUPPORTED | p. 289 (Mubarrad 3 + "بضع مسائل دون العشر"); p. 291 (50); p. 292 (31); p. 295 (190); p. 302 ("عاريتان … من … تاريخ نسخ"); p. 303 (255) |
| C28 | al-Suyūṭī d. 911/1505 | SUPPORTED | Itqān card; ed1993 p. 20 |
| C29 | al-Suyūṭī says he left out a dozen or so (2:105) | SUPPORTED | Itqān 2:105 "حذفت منها يسيرا نحو بضعة عشر سؤالا" |
| C30 | 1993 edition rests on one Cairo MS and numbers 250 questions (p. 20) | NEEDS QUALIFICATION | p. 20 names the single Dār al-Kutub MS (١١٦ مجاميع م, undated); the count 250 is not on p. 20 — it comes from the edition's numbering (contents run to (٢٥٠), no. 23 absent from the Shamela contents list) |
| C31 | al-Sāmarrāʾī thought its handwriting looked recent (samarrai p. 7) | NEEDS QUALIFICATION | wording confirmed in OCR: "ويبدو أن خطها حديث وقد خلت من تاريخ"; same Dār al-Kutub majāmīʿ MS (OCR "١١7"). Page number unconfirmed: page-foot numerals in the OCR ("-١١-" on leaf 10, "…١6" on leaf 15) suggest this passage is on p. 8, not 7 |
| C32 | Bint al-Shāṭiʾ: Cairo copies likely descend from a 10th-c. original (p. 302) | SUPPORTED | p. 302 "منقولتان من أصل واحد من القرن الرابع للهجرة" (4th c. AH ≈ 10th c. CE) |
| C33 | qbs entry tells of Moses on a rainy night; al-Suyūṭī's version only "a flame of fire from which they kindle" (Itqān 2:77); Q 27:7 | SUPPORTED | entry 11487 ("وطشت السماء"); Itqān 2:77 "شعلة من نار يقتبسون منه"; ed1993 p. 70 n. 1 al-Naml 7 |
| C34 | Modern Arab editors present the questions as Ibn ʿAbbās's own pioneering method (samarrai p. 5; ed1993 p. 19) | NEEDS QUALIFICATION | content confirmed: Sāmarrāʾī "اعتمد فيها منهجا لم يسبق اليه"; ed1993 p. 19 "كان له طريقة مميزة في التفسير". Sāmarrāʾī page unconfirmed (OCR pagination suggests p. 6) |
| C35 | Goldziher: *lehrreiche Schullegende*; tribute from later philologists to the "father of tafsīr" and his philological method (pp. 70–71) | SUPPORTED | pp. 70–71: "eine lehrreiche Schullegende … eine Huldigung der philologischen Nachwelt an den eine philologische Methode der Koranerklärung fördernden Vater des Tafsīr" |
| C36 | Wansbrough: method "considerably posterior"; "an ancient and honourable pedigree" (pp. 216–17) | SUPPORTED | pp. 216–217, verbatim |
| C37 | Wansbrough: regular poetic evidence in a commentary first with al-Farrāʾ (d. 822) (p. 218) | SUPPORTED | p. 218 "The earliest exegetical composition in which poetic shawahid were regularly employed is the Maʿani 'l-Qurʾan of Farraʾ (d. 207/822)" |
| C38 | Ibn al-Anbārī, as al-Zarkashī reports, saw in it proof against objectors (bint p. 293) | SUPPORTED | bint p. 293 quoting al-Burhān |
| C39 | al-Suyūṭī introduces it with Ibn al-Anbārī's reply: poetry not a foundation, only clarifies the rare word (2:67) | SUPPORTED | Itqān 2:67 |
| C40 | kbd excerpt (Arabic) and translation; Q 90:4 | SUPPORTED | entry 16979 matches; translation accurate; ed1993 p. 33 n. 1 al-Balad 4 |
| C41 | "The gloss is two nouns and nothing more" | SUPPORTED | في اعتدال واستقامة |
| C42 | Lisān "reports both readings of the verse" and glosses Labīd's line the other way | NEEDS QUALIFICATION | entry 16990: Lisān gives at least five readings (al-Farrāʾ upright/balanced; struggling with this world and the next; hardship; walking erect; birth position; also Abū Ṭālib: الاستواء والاستقامة). The line is glossed "أي في شدة وعناء" — that part is correct |
| C43 | Lisān excerpt (Arabic) and translation | SUPPORTED | entry 16990; ellipses mark omitted readings; translation accurate |
| C44 | 1993 editors' footnotes gloss *kabad* as hardship; variants "the enemy", "the women" (p. 33 nn. 2, 4) | SUPPORTED | ed1993 p. 33 n. 2 "الكبد: المشقة"; n. 4 "قام العدوّ" (Kāmil), "قام النّساء" (Ibn Hishām) |
| C45 | mrD excerpt (two exchanges) and translation | SUPPORTED | entry 4276; ed1993 nos. 32 (p. 61) and 224 (p. 257) |
| C46 | Q 33:32 addressed to the Prophet's wives; Q 2:10 is the edition's identification, about people claiming belief they do not hold | SUPPORTED | ed1993 p. 61 n. 1 (al-Aḥzāb 32), p. 257 n. 1 (al-Baqara 10); Q 33:32 "يا نساء النبي"; Q 2:8–10 |
| C47 | Editors note the al-Aʿshā line is not in his dīwān (p. 61 n. 3) | SUPPORTED | "وليس البيت في (ديوان الأعشى)" |
| C48 | bwr excerpt and translation; Q 48:12 | SUPPORTED | entry 9529; وكنتم قوما بورا = 48:12 |
| C49 | al-Suyūṭī drew five such labels from the collection for his chapter on non-Ḥijāzī words (2:106–108) | SUPPORTED | Itqān ch. 37 begins 2:106; the five "في مسائل نافع … وفيها" items (Hawāzin, ʿUmān, Yemen, ʿAbs, Hudhayl) on pp. 107–108 |
| C50 | The line shows *kufr* used for failing to repay a favour | SUPPORTED (interpretation of the quoted line) | "فلا تكفروا ما قد صنعنا إليكم وكافوا به" |
| C51 | Labīd and Abū Miḥjan, both quoted in our copy, lived into Islam (pp. 33, 54) | SUPPORTED | p. 33 n. 3 "أدرك الإسلام"; p. 54 n. 2 "أسلم سنة (٩) هـ"; both quoted in displayed entries (kbd, Amr, nHb; fwm) |
| C52 | 19 of the 50 displayed exchanges credit only "the poet" | SUPPORTED | count of الشاعر in all displayed originals = 19; exchanges = 50 |
| C53 | Wansbrough: "Jahili or Mukhadrami poets (many anonymous)" (p. 217) | SUPPORTED | p. 217 verbatim |
| C54 | onOurSite: text follows the 1993 Beirut edition "as reproduced on arabiclexicon.hawramani.com", same wording/headings, without numbers and footnotes | NEEDS QUALIFICATION | Verifier's collation confirms identical wording and headings (kbd = p. 33; mrD = nos. 32 + 224; shwb الغاق = p. 64; qbs incl. [آنَسْتُ] = p. 70), but hawramani's page does not name its source edition, so the [^hawramani] citation does not support the identification |
| C55 | Entries open with root letters and bracketed Qurʾanic word; other brackets mark editorial insertions | SUPPORTED | all 49 headings; [آنَسْتُ] in qbs; ed1993 uses [] for insertions (e.g. p. 25 [المكي]) |
| C56 | Arabic gives no verse numbers; some English versions supply them | SUPPORTED | no digits in any displayed original; kbd/qbs translations add Q refs |
| C57 | 49 roots ≈ a fifth of 250; the two maraḍ exchanges share one entry | SUPPORTED | 50 exchanges / 250 |
| C58 | *khabat* (Q 17:97) appears under خ ب ت | SUPPORTED | entry 11147 (heading خ ب و, stored under xbt); Q 17:97 |
| C59 | الغاق where al-Suyūṭī has الغساق (2:76) | SUPPORTED | entry $wb and ed1993 p. 64 "الغاق"; Itqān 2:76 "الخلط الحميم والغساق" |
| C60 | Source data: Itqān edition (Ibrāhīm, 1974, 4 vols) | SUPPORTED | Shamela card 11728 |
| C61 | Source data: Tārīkh Baghdād (Bashshār, 2002), vol. 12, entry 5798 | SUPPORTED | Shamela 736 card; volume selector 12; entry ٥٧٩٨ |
| C62 | Source data: Bint al-Shāṭiʾ, 3rd edn, Dār al-Maʿārif | SUPPORTED | Shamela 12759 card |
| C63 | Source data: al-Sāmarrāʾī, Baghdad, Maṭbaʿat al-Maʿārif, 1968, offprint from *Risālat al-Islām* 2, nos. 5–6 | SUPPORTED | OCR title page (lis_ak87): "مستل من مجلة رسالة الإسلام، العددان الخامس والسادس، السنة الثانية … مطبعة المعارف بغداد"; 1968 per library listings (Goodreads/ketabpedia) |

Totals: 63 claims — 58 supported, 5 needs qualification, 0 unsupported.

## Flagged items and fixes

- **C30** — "rests on one Cairo manuscript and numbers 250 questions;[^ed1993|p. 20]". Fix: keep p. 20 for the manuscript; source the count to the edition's numbering, e.g. "…rests on one Cairo manuscript,[^ed1993|p. 20] and numbers its questions to 250;[^ed1993|contents]" (or cite [^hawramani], which states 250 entries).
- **C31** — Sāmarrāʾī "handwriting looked recent" [^samarrai|p. 7]. Wording confirmed; page not. Fix: check the scan at https://archive.org/details/lis_ak87 and correct the locator (OCR suggests p. 8), or drop the page number; add that URL to the samarrai source.
- **C34** — Sāmarrāʾī "pioneering method" [^samarrai|p. 5]. Same fix (OCR suggests p. 6).
- **C42** — "The entry in Lisān al-ʿArab reports both readings of the verse". Fix: "reports several readings of the verse, among them both of these, and quotes the same line, glossed the other way".
- **C54** — "Our text follows the 1993 Beirut edition, as reproduced on arabiclexicon.hawramani.com". Fix: "Our text, taken from arabiclexicon.hawramani.com (which does not name its source), matches the 1993 Beirut edition word for word, headings included, without the editors' question numbers and footnotes.[^ed1993][^hawramani]"

## Brief issues (non-factual)

- suggestion — "Our copy leaves out the frame, so the unnamed قال…": the fwm entry still addresses the questioner as "يا ابن أم الأزرق"; optionally add "(one entry still addresses him as 'son of Umm al-Azraq')".
- suggestion — The transmission paragraphs ("What can be dated…", "Other routes…") stack many numbers (344/955, 288/900, 50, 31, 190, 255, 250) and read a little like a list; consider trimming one route count if space is needed. Lede + body is 1,088 words, right at the ceiling; nothing is padding, but no room to add.
- suggestion — "nineteen … credit only 'the poet'": the 1993 editors' footnotes sometimes name the anonymous poet (e.g. p. 64 n. 2 names Umayya ibn Abī l-Ṣalt for the شوب line); a clause saying so would stop readers assuming these lines are untraceable.
- suggestion — Wansbrough (p. 218) records *Kitāb gharīb al-Qurʾān* as one older title for this collection; "The name on our panel … is recent" is right for the full title, but the essay could say that the longer phrase *fī shiʿr al-ʿArab* is what the editors added.
- No bare root mentions; every translation is labelled ("translations on this page are ours"); no ranking or generic praise; no "original root meaning" narrative forced; nothing promised that the site does not show.

## URLs

- All listed URLs open and are the stated works (see top). ed1993 URL is the Shamela reproduction; its card does not carry editor/publisher data.
- samarrai and wansbrough have no URL. Add https://archive.org/details/lis_ak87 for Sāmarrāʾī. Wansbrough is available on archive.org but its copyright status is unclear; leaving it without a link is acceptable.
- No source is listed but unused.

## Validator

`node scripts/validate-dictionary-guides.mjs gharib-al-quran-fi-shir-al-arab` → ok; 6 root links, 4 excerpts, 1,088 words; example roots qbs, kbd, mrD, bwr, xbt. 1/1 guides pass.

## Site-data issues

1. Stored author "ʿAbdullāh ibn ʿAbbās" presents a disputed attribution as authorship. The text is a transmitted question-and-answer exchange (chain via ʿĪsā ibn Daʾb, recorded 288/344 AH), and Goldziher and Wansbrough treat it as later. Suggest the label "attributed to ʿAbdullāh ibn ʿAbbās".
2. Stored date 687 is Ibn ʿAbbās's death (68 AH = 687–8 CE), not the date of the text; it sorts this work first in the panel. The earliest datable versions are late 9th–10th c. CE (al-Mubarrad d. 285/898; chain dated 288 and 344 AH). If the panel must stay sorted by death year, it should at least be shown as "attrib., d. 68/687–8".
3. Misfiled entry: snh (entry 15503) holds the question on سِنَةٌ "drowsiness" (Q 2:255), whose root is و س ن; the stored heading itself says س ن و. It sits on the page for سنه ("year"). Similarly xbt holds an entry headed خ ب و (khabat, Q 17:97). The essay already mentions the second case; the first should be refiled or noted.
4. The title *Gharīb al-Qurʾān fī Shiʿr al-ʿArab* is the 1993 editors' addition (ed1993 p. 20); the older name is *Masāʾil/Suʾālāt Nāfiʿ ibn al-Azraq*. Suggest showing it as an alternative title.
