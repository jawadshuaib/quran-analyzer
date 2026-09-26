# Verification round 2 — gharib-al-quran-fi-shir-al-arab

Independent check of `roots/frontend/src/content/dictionary-guides/guides/gharib-al-quran-fi-shir-al-arab.ts` (2026-09-26). research-notes.md and revision-r1.md were NOT opened. verification-r1.md was read for the list of earlier flags only; every claim below was re-checked against sources opened in this round.

## How sources were checked

- **ed1993** — all 275 text pages of Shamela book 23622 downloaded through `https://shamela.ws/ajax/pageContent/23622/<id>`; print page = the returned `pageNum` (card: "ترقيم الكتاب موافق للمطبوع"). Pages read: 12–13, 17, 19–21, 25–27, 33, 50–52, 54, 61, 64, 70, 97, 116, 169, 175, 179, 183–184, 200, 207–208, 217–218, 257, 277, 280, 283. Bibliographic data: editors Muḥammad ʿAbd al-Raḥīm and Aḥmad Naṣr Allāh confirmed on archive.org/details/20191024_20191024_1900; publisher Muʾassasat al-Kutub al-Thaqāfiyya on books.rafed.net (b_id 4297); 1413/1993 from a catalogue snippet in search results; p. 21 signed "المحققان".
- **itqan** — Shamela 11728 (card: ed. Muḥammad Abū l-Faḍl Ibrāhīm, al-Hayʾa al-Miṣriyya al-ʿĀmma li-l-Kitāb, 1394/1974, 4 vols); page ids 449–450, 458–460, 487–490 = vol. 2 ("ج2" on page 449), pp. 67–68, 76–78, 105–108.
- **bint** — Shamela 12759 (card: Dār al-Maʿārif, 3rd edn, print pagination); page ids 272–288 = pp. 289–305.
- **tarikh-baghdad** — Shamela 736 (card: Bashshār ʿAwwād Maʿrūf, Dār al-Gharb al-Islāmī, 1422/2002; al-Khaṭīb 392–463 AH); page ids 6998–7002 = vol. 12 ("ج12"), pp. 468–472, entry ٥٧٩٨.
- **goldziher** — archive.org MN41643ucmf_1 (metadata: Goldziher, *Die Richtungen der islamischen Koranauslegung*, 1920), djvu.txt, pp. 69–71.
- **wansbrough** — archive.org full text (QuranicStudiesSourcesAndMethodsOfScripturalInterpretationByJohnWansbrough … _djvu.txt), pp. 216–218.
- **samarrai** — `https://archive.org/download/lis_ak87/lis_ak8709.pdf`, rendered with pdftoppm. PDF page 6 prints "- ٥ -" (the مقدمة, with "ذلك ان ابن عباس قد اعتمد فيها منهجا لم يسبق اليه"); PDF page 7 prints "- ٦ -" (the Dār al-Kutub MS 116 majāmīʿ, used via a photocopy in the Iraqi Academy); PDF page 8 prints "- ٧ -" ("وهي بالقلم النسخي الجميل ويبدو أن خطها حديث وقد خلت من تاريخ يشير الى النسخ"). Title page OCR: "مستل من مجلة رسالة الإسلام، العددان الخامس والسادس، السنة الثانية … مطبعة المعارف بغداد". Year 1968 from Goodreads (book/show/60688897, "Published January 1, 1968").
- **hawramani** — contents page opens; it says "a 250-entry dictionary … (also known as Masāʾil Nāfiʿ b. al-Azraq)" and names no printed edition.
- **Local data** — `_dict_guide_tool.py entry` for all 49 displayed roots of this dictionary, plus kbd in ibn-manzur-lisan-al-arab; `/api/root/kbd/dictionaries` for the stored label.
- **Collation** — all 50 displayed exchanges were compared, after removing vowel marks and punctuation, with the ed1993 text minus its footnote markers: 50/50 identical, headings included.

## Claims table

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *Gharīb al-Qurʾān fī Shiʿr al-ʿArab* / غريب القرآن في شعر العرب (title, titleAr) | SUPPORTED | Shamela 23622 card; ed1993 p. 20 |
| C2 | titleGloss "The Qurʾan's Unfamiliar Words in the Poetry of the Arabs" | SUPPORTED | fair rendering |
| C3 | author "Attributed to ʿAbdullāh ibn ʿAbbās" | SUPPORTED | Shamela card "[عبد الله بن عباس]"; attribution disputed (Goldziher 70–71; Wansbrough 216–17) |
| C4 | authorAr عبد الله بن عباس | SUPPORTED | ed1993 p. 12 n. 1 |
| C5 | period: d. 68 AH / 687–8 CE; recorded versions late 9th–10th c. CE | SUPPORTED | ed1993 p. 12 n. 1 (68/687); chain dated 288 and 344 AH (p. 25); al-Mubarrad d. 285, Ibn al-Anbārī d. 328, al-Ṭabarānī d. 360 (bint pp. 289–291) |
| C6 | kind "Question-and-answer glossary" | SUPPORTED | all 50 displayed exchanges are Q&A |
| C7 | summary: questioner named as Nāfiʿ; brief gloss, then a line of poetry as proof; attributed rather than authored | SUPPORTED | ed1993 pp. 26–27; entries; Goldziher/Wansbrough |
| C8 | lede: in the frame story the questioner is the Khārijite leader Nāfiʿ ibn al-Azraq | SUPPORTED | ed1993 p. 17 n. 11 ("رأس الأزارقة"), pp. 26–27 |
| C9 | lede: he presses "Do the Arabs know that?"; the answer is always a line of poetry | SUPPORTED | all 50 exchanges contain تعرف العرب and أما سمعت + verse |
| C10 | lede: text attributed to Ibn ʿAbbās and shaped by transmitters, not a lexicon he wrote | SUPPORTED (interpretation) | differing routes and counts (bint pp. 289–303); Goldziher 70–71; Wansbrough 216–17 |
| C11 | full name is recent; the editors say they added it to make the subject clear (p. 20) | SUPPORTED | p. 20: "أضفنا إلى العنوان الرئيسي عنوانا جديدا وضروريا وهو: غريب القرآن في شعر العرب كي يقع هذا العنوان على نظر القارئ ويتفهم المراد منه" |
| C12 | two editors, Beirut, 1993 | SUPPORTED | p. 21 "المحققان"; archive.org item names both; rafed lists Muʾassasat al-Kutub al-Thaqāfiyya; 1413/1993 in catalogue listing |
| C13 | earlier writers call it the *Masāʾil* of Nāfiʿ (Itqān 2:67) | SUPPORTED | Itqān 2:67 "وأوعب ما رويناه عنه مسائل نافع بن الأزرق"; also al-Zarkashī "ومسائل نافع له" (bint p. 293) |
| C14 | *gharīb* = rare or opaque words | SUPPORTED | ed1993 p. 20 "الحرف الغريب"; standard sense |
| C15 | frame at the Kaʿba; Nāfiʿ and Najda accuse him of presuming to interpret; ask for *miṣdāq* "from the speech of the Arabs", since the Qurʾan came in clear Arabic (pp. 26–27) | SUPPORTED | p. 26 "بفناء الكعبة"; p. 27 "فقاما إليه فقالا … ما يحملك على تفسير القرآن"; "وتأتينا بمصداقه من كلام العرب، فإن الله … أنزل القرآن بلسان عربي مبين" |
| C16 | every displayed entry: phrase, gloss, the challenge, أما سمعت + verse | SUPPORTED | 50/50 (6 have فهل rather than وهل; the pattern holds) |
| C17 | our copy leaves out the frame; the unnamed قال alternates | SUPPORTED | grep of displayed entries for الكعبة/نجدة/حدثنا/الطس: 0 matches |
| C18 | NEW: once, Ibn ʿAbbās calls the questioner "son of Umm al-Azraq" | SUPPORTED | fwm entry 17535 "قال: يا ابن أم الأزرق ومن قرأها على قراءة عبد الله بن مسعود (الثوم)"; the only displayed entry containing الأزرق; = ed1993 p. 54 |
| C19 | Ibn ʿAbbās the Prophet's cousin, died at al-Ṭāʾif 68 AH (pp. 12–13) | SUPPORTED | p. 12 n. 1 "فسكن الطائف وتوفي بها سنة (٦٨) هـ"; p. 13 "فهو ابن عمه" |
| C20 | Nāfiʿ head of the Azāriqa, killed 65/685 (p. 17 n. 11) | SUPPORTED | "رأس الأزارقة … وقتل نافع يوم دولاب … سنة (٦٥) هـ الموافق (٦٨٥) م" |
| C21 | later reports praise Ibn ʿAbbās for teaching old poetry and battle-days alongside religion and law (Goldziher p. 71) | SUPPORTED | p. 71 "Man rühmt von ihm, dass er ausser den religiösen und gesetzlichen Kenntnissen auch Belehrungen über … ajjām al-ʿarab, über alte Poesie … geboten habe" |
| C22 | the panel's 687 is his death, not the text's date | SUPPORTED | C5; stored author_death_year 687 |
| C23 | Ibn al-Ṭastī taught it in AH 344 (955 CE) | SUPPORTED | p. 25 "قراءة عليه … سنة أربع وأربعين وثلاثمائة (٣٤٤ هـ)" (Rabīʿ II 344 = 955) |
| C24 | received from al-Sarī ibn Sahl in AH 288 (about 900 CE) | SUPPORTED | p. 25 "قراءة عليه سنة ثمان وثمانين ومائتين" |
| C25 | the chain runs back through ʿĪsā ibn Daʾb (pp. 25–26) | SUPPORTED | p. 26 "حدثنا عيسى بن دأب"; bint p. 304 identifies him as ʿĪsā ibn Yazīd ibn Bakr |
| C26 | al-Khaṭīb (d. 1071): Ibn Daʾb a transmitter of Arab lore, genealogy, tribal history; "was said to add to reports what was not in them" (vol. 12, p. 468) | SUPPORTED | TB 12:468 "راوية عن العرب، وافر الأدب، عالما بالنسب، عارفا بأيام الناس … وقيل: إنه كان يزيد في الأحاديث ما ليس منها"; card: d. 463 AH (= 1071) |
| C27 | Khalaf al-Aḥmar's charge that he fabricated reports (p. 472) | SUPPORTED | TB 12:471–472 "كان خلف الأحمر ينسب ابن داب إلى الكذب"; p. 472 "ابن داب، يضع الحديث بالمدينة" |
| C28 | other routes carry other selections | SUPPORTED | bint pp. 289–304 |
| C29 | per Bint al-Shāṭiʾ: al-Mubarrad a handful, Ibn al-Anbārī fifty, al-Suyūṭī 190, two undated Cairo MSS 255 (pp. 289–303) | SUPPORTED | p. 289 (3 + "بضع مسائل دون العشر"); p. 291 "خمسون مسألة"; p. 295 "مائة وتسعون مسألة"; p. 302 "عاريتان … من تقييد سماع أو توقيع ناسخ وتاريخ نسخ"; p. 303 "مائتين وخمسا وخمسين مسألة" |
| C30 | al-Suyūṭī d. 911/1505 | SUPPORTED | ed1993 p. 20 "المتوفى سنة (٩١١ هـ)"; Itqān card |
| C31 | R1-FLAG FIXED: the 1993 edition rests on one Cairo MS (p. 20) | SUPPORTED | p. 20 "عمدنا إلى نشر هذه المسائل كما وردت في الأصل المخطوط المحفوظ في دار الكتب المصرية تحت رقم ١١٦ مجاميع م" |
| C32 | R1-FLAG FIXED / NEW locator: numbers its questions to 250 (no. 250, p. 283) | SUPPORTED | Shamela page 273 = print p. 283: "(٢٥٠) خ ف ي [أخفيها]"; contents run (١)–(٢٥٠); no. 23 (أي د) is present on p. 51 although the Shamela contents list skips it |
| C33 | R1-FLAG RESOLVED: al-Sāmarrāʾī thought its handwriting looked recent (p. 7) | SUPPORTED | scan PDF page 8, printed "- ٧ -": "ويبدو أن خطها حديث"; he describes the same Dār al-Kutub MS 116 majāmīʿ (printed p. 6). R1's OCR-based "p. 8" was wrong; the reviser's dispute is correct |
| C34 | Bint al-Shāṭiʾ: Cairo copies likely descend from a tenth-century original (p. 302) | SUPPORTED | p. 302 "فالراجح أنهما منقولتان من أصل واحد من القرن الرابع للهجرة" (4th c. AH ≈ 10th c. CE) |
| C35 | qbs entry tells of Moses on a rainy night; al-Suyūṭī's version gives only "a flame of fire from which they kindle" (2:77); Q 27:7 | SUPPORTED | entry 11487 "وذلك في ليلة مظلمة، وطشت السماء" (= ed1993 p. 70, n. 1 al-Naml 7); Itqān 2:77 "شعلة من نار يقتبسون منه" |
| C36 | R1-FLAG RESOLVED: modern Arab editors present the questions as Ibn ʿAbbās's own pioneering method (samarrai p. 5; ed1993 p. 19) | SUPPORTED | scan printed "- ٥ -": "ذلك ان ابن عباس قد اعتمد فيها منهجا لم يسبق اليه وهو شرح الفاظ القرآن والاستدلال عليها بما جاء في شعر العرب"; ed1993 p. 19 "كان له طريقة مميزة في التفسير، فكان كثيرا ما يرجع إلى الشعر الجاهلي إذا سئل عن غريب القرآن" |
| C37 | Goldziher: *lehrreiche Schullegende*; tribute from later philologists to the "father of tafsīr" and his philological method (pp. 70–71) | SUPPORTED | pp. 70–71 "eine lehrreiche Schullegende … eine Huldigung der philologischen Nachwelt an den eine philologische Methode der Koranerklärung fördernden Vater des Tafsīr" |
| C38 | Wansbrough: method "considerably posterior"; asked whether the aim was "an ancient and honourable pedigree" (pp. 216–17) | SUPPORTED | p. 216 "exhibits an exegetical method considerably posterior to the activity of Ibn ʿAbbas"; p. 217 "provoke the question whether the real purpose of the work was not to furnish an ancient and honourable pedigree" |
| C39 | Wansbrough: regular poetic evidence in a commentary first with al-Farrāʾ (d. 822) (p. 218) | SUPPORTED | p. 218 "The earliest exegetical composition in which poetic shawahid were regularly employed is the Maʿani 'l-Qurʾan of Farraʾ (d. 207/822)" |
| C40 | Ibn al-Anbārī, as al-Zarkashī reports, saw in it proof against objectors (bint p. 293) | SUPPORTED | p. 293 "ذكرها الأنباري في كتاب (الوقف والابتداء) بإسناده، وقال: فيه دلالة على بطلان قول من أنكر على النحويين احتجاجهم على القرآن بالشعر" |
| C41 | al-Suyūṭī introduces it with Ibn al-Anbārī's reply: poetry is not a foundation; it clarifies the rare word (2:67) | SUPPORTED | 2:67 "ليس الأمر كما زعموه من أنا جعلنا الشعر أصلا للقرآن بل أردنا تبيين الحرف الغريب من القرآن بالشعر" |
| C42 | kbd excerpt Arabic; Q 90:4 | SUPPORTED | entry 16979 matches (validator ok); ed1993 p. 33 n. 1 al-Balad 4 |
| C43 | kbd translation | SUPPORTED | accurate |
| C44 | "The gloss is two nouns"; the witness does not by itself fix the sense | SUPPORTED (interpretation) | في اعتدال واستقامة; Lisān reads the same line otherwise (C45) |
| C45 | R1-FLAG FIXED: Lisān "reports several readings of the verse, balance and hardship among them, and quotes the same line, glossed the other way" | SUPPORTED | entry 16990: al-Farrāʾ منتصباً معتدلاً; يعالج ويكابد; في شدة ومشقة; walking erect; birth position; Abū Ṭālib الاستواء والاستقامة; Labīd's line glossed "أي في شدة وعناء" |
| C46 | Lisān excerpt Arabic + translation | SUPPORTED | entry 16990; ellipses mark omitted readings; translation accurate |
| C47 | 1993 footnotes gloss *kabad* as hardship; line variants "the enemy", "the women" (p. 33 nn. 2, 4) | SUPPORTED | n. 2 "الكبد: المشقة"; n. 4 "قمنا وقام العدوّ" (Kāmil), "قمنا وقام النّساء" (Ibn Hishām) |
| C48 | the maraḍ entry holds two exchanges; the same phrase gets different answers | SUPPORTED | entry 4276 = ed1993 no. 32 (p. 61) + no. 224 (p. 257) |
| C49 | mrD excerpt Arabic + translation | SUPPORTED | entry 4276; translation accurate |
| C50 | Q 33:32 addressed to the Prophet's wives; Q 2:10 is the edition's identification, about people claiming belief they do not hold | SUPPORTED | p. 61 n. 1 al-Aḥzāb 32; p. 257 n. 1 al-Baqara 10; Q 33:32 "يا نساء النبي"; Q 2:8–10 |
| C51 | "on our reading" each witness is chosen to fit | SUPPORTED (labelled interpretation) | the lines themselves |
| C52 | editors note the al-Aʿshā line is not in his dīwān (p. 61 n. 3) | SUPPORTED | "وليس البيت في (ديوان الأعشى)" |
| C53 | bwr excerpt + translation; Q 48:12 | SUPPORTED | entry 9529 = ed1993 p. 200; translation accurate |
| C54 | some answers tag a word with a region's speech | SUPPORTED | bwr (ʿUmān), nqb (Yemen) |
| C55 | al-Suyūṭī drew five such labels from this collection for his chapter on non-Ḥijāzī words (2:106–108) | SUPPORTED | ch. 37 heading 2:106; "وفي مسائل نافع بن الأزرق" items: Hawāzin (p. 107); ʿUmān, Yemen, ʿAbs, Hudhayl (p. 108) |
| C56 | the line shows *kufr* used for failing to repay a favour | SUPPORTED (interpretation of quoted line) | "فلا تكفروا ما قد صنعنا إليكم وكافوا به" |
| C57 | Labīd and Abū Miḥjan, both quoted in our copy, lived into Islam (pp. 33, 54) | SUPPORTED | p. 33 n. 3 "أدرك الإسلام … توفي عام (٤١) هـ"; p. 54 n. 2 "أسلم سنة (٩) هـ"; Labīd in kbd, Amr, nHb; Abū Miḥjan in fwm |
| C58 | 19 of the 50 displayed exchanges credit only "the poet" | SUPPORTED | own count of الشاعر across 50 exchanges = 19 |
| C59 | Wansbrough: "Jahili or Mukhadrami poets (many anonymous)" (p. 217) | SUPPORTED | p. 217 verbatim |
| C60 | NEW: the 1993 editors name a few of these poets, among them Dhū l-Rumma for the rikz line (Q 19:98) (p. 208 n. 2) | SUPPORTED | p. 208 "(١٧٧) ر ك ز [ركزا]"; n. 1 "سورة مريم الآية: ٩٨"; n. 2 "الشاعر: ذو الرمة: وهو غيلان بن عقبة". Own check of all 19: named only at p. 64 (Umayya), p. 184 (Abū Zubayd), p. 208 (Dhū l-Rumma), p. 277 (ʿAdī ibn Zayd); the other 15 footnotes (pp. 32, 42, 69, 85, 97, 116, 169, 175, 179, 200, 207, 217, 218, 257, 280) name no poet. 4 of 19 = "a few" |
| C61 | NEW: Dhū l-Rumma died 117/735, nearly fifty years after Ibn ʿAbbās | SUPPORTED | p. 208 n. 2 "توفي بأصبهان سنة (١١٧) هـ الموافق (٧٣٥) م"; 117 − 68 = 49 AH years |
| C62 | it cannot settle a meaning alone: attribution disputed, versions differ, witnesses anonymous or missing from the dīwān | SUPPORTED | C29, C35, C37–38, C52, C58 |
| C63 | onOurSite (R1-FLAG FIXED): our text comes from hawramani, which does not name its source | SUPPORTED | source_url of every entry is arabiclexicon.hawramani.com; hawramani contents page names no edition |
| C64 | in every entry compared it matches the 1993 edition word for word, headings included, without numbers and footnotes | SUPPORTED | own collation 50/50 exchanges identical to ed1993 text; headings identical minus "(n)" |
| C65 | entries open with root letters and the bracketed Qurʾanic word; other brackets mark editorial insertions | SUPPORTED | all 49 headings; [آنَسْتُ] in qbs = ed1993 p. 70 n. 7 (MS has [أرى]) |
| C66 | the Arabic gives no verse numbers; some English versions supply them | SUPPORTED | no digits in any displayed original; kbd/qbs/rkz translations add Q refs |
| C67 | 49 roots ≈ a fifth of 250; the two maraḍ exchanges share one entry | SUPPORTED | 50 exchanges in 49 entries |
| C68 | a few entries sit on a neighbouring root's page: *khabat* (Q 17:97) under خ ب ت | SUPPORTED | xbt entry 11147 heading خ ب و; also snh entry 15503 heading س ن و. Two such entries in all |
| C69 | الغاق where al-Suyūṭī has الغساق (2:76) | SUPPORTED | $wb entry = ed1993 p. 64 "والحميم: الغاق"; Itqān 2:76 "الخلط الحميم والغساق" |
| C70 | source: ed1993 citation and Shamela URL | SUPPORTED | see "How sources were checked" |
| C71 | source: Itqān (Ibrāhīm, Cairo 1974, 4 vols; vol. 2 chs 36–37) | SUPPORTED | Shamela 11728 card; ch. 36 at 2:67, ch. 37 at 2:106 |
| C72 | source: Goldziher 1920 | SUPPORTED | archive.org metadata |
| C73 | source: Tārīkh Baghdād (Bashshār, 2002), vol. 12, entry 5798 | SUPPORTED | Shamela 736 card; "ج12"; entry ٥٧٩٨ |
| C74 | source: Bint al-Shāṭiʾ, 3rd edn, Dār al-Maʿārif | SUPPORTED | Shamela 12759 card |
| C75 | source: al-Sāmarrāʾī (Baghdad, Maṭbaʿat al-Maʿārif, 1968; offprint from *Risālat al-Islām* 2, nos. 5–6); scan shows printed page numbers | SUPPORTED | scan title page; Goodreads 1968; printed page-foot numerals visible |
| C76 | source: Wansbrough (OUP, 1977, London Oriental Series 31) | SUPPORTED | archive.org text |
| C77 | source: hawramani contents page | SUPPORTED | opens; describes the work |

Totals: 77 claims — 77 supported, 0 needs qualification, 0 unsupported.

## Round-1 flags: resolution

- C30 (manuscript + 250) — fixed. Separate citations; p. 20 and no. 250 p. 283 both verified.
- C31 (Sāmarrāʾī p. 7) — the reviser's dispute is correct. Printed "- ٧ -" on the scan page that carries "ويبدو أن خطها حديث". Round 1 was wrong.
- C34 (Sāmarrāʾī p. 5) — the reviser's dispute is correct. Printed "- ٥ -".
- C42 (Lisān readings) — fixed.
- C54 (onOurSite) — fixed. The own-collation claim is now verified for all 50 exchanges.

Round 1 also suggested that Wansbrough (p. 218) records *Kitāb gharīb al-Qurʾān* as an older title for this collection. That is a misreading. On p. 216 Wansbrough lists *Kitāb gharīb al-Qurʾān*, *Kitāb Bayān lughat al-Qurʾān* and *Masāʾil Nāfiʿ b. Azraq* as three titles associated with Ibn ʿAbbās, which match three different blocks in Itqān chapter 36. The reviser was right not to add it.

## Flagged items

None.

## Brief issues (non-factual)

- suggestion — onOurSite "A few entries sit on a neighbouring root's page": there are exactly two (xbt holds خ ب و *khabat*; snh holds سِنَة Q 2:255, heading س ن و). "Two entries" would be more exact. It could also name the second one, since a reader of سنه "year" will meet a question on drowsiness.
- suggestion — Dhū l-Rumma: "nearly fifty years after Ibn ʿAbbās" is accurate but understates the point. Standard references give his birth as c. 77/696, after Ibn ʿAbbās's death. If that is added, cite a source that states it (the 1993 note does not give a birth year).
- suggestion — Lede + body is 1,099 words, 1 under the ceiling. Any further addition needs a matching cut.
- The Lisān excerpt joins "في شدّة ومشقة … وقال لبيد". In Lisān, Labīd's line follows al-Layth's remark on *yukābidu l-layl*, not the verse. The essay says only that Lisān "quotes the same line, glossed the other way", which is accurate, and the ellipsis marks the gap. No change needed.
- No bare root mentions. Translations are labelled ("translations on this page are ours"). No ranking or generic praise, no forced "original root meaning" story, and nothing promised that the site does not show.

## URLs

All eight listed URLs return 200 and are the stated works. The samarrai URL (`https://archive.org/details/lis_ak87/lis_ak8709.pdf`) opens the lis_ak87 item page. The file itself is at `/download/lis_ak87/lis_ak8709.pdf`. Either is usable. Wansbrough has no URL, which is acceptable. No source is listed but unused.

## Validator

`node scripts/validate-dictionary-guides.mjs gharib-al-quran-fi-shir-al-arab` → ok. 7 root links (7 distinct pairs), 4 excerpts, 1,099 words (lede + body). Example roots: qbs, kbd, mrD, bwr, rkz, xbt. 1/1 guides pass.

## Site-data issues

1. The stored author "ʿAbdullāh ibn ʿAbbās" (API `author`) presents a disputed attribution as authorship. Suggest "attributed to ʿAbdullāh ibn ʿAbbās".
2. The stored `author_death_year` 687 is Ibn ʿAbbās's death (68 AH = 687–8), not the date of the text. The earliest datable versions are late 9th–10th c. CE (al-Mubarrad d. 285/898; chain dated 288 and 344 AH). It sorts this work first in the panel.
3. Misfiled entries: snh (entry 15503) holds the question on سِنَةٌ "drowsiness" (Q 2:255, root و س ن; stored heading س ن و) on the page for سنه "year". xbt (entry 11147) holds the question on خَبَتْ, heading خ ب و. The guide mentions the second.
4. The title *Gharīb al-Qurʾān fī Shiʿr al-ʿArab* was added by the 1993 editors (ed1993 p. 20). The manuscript title is *Suʾālāt Nāfiʿ ibn al-Azraq*, and al-Suyūṭī's name for it is *Masāʾil Nāfiʿ ibn al-Azraq*. Suggest showing one of these as an alternative title.
