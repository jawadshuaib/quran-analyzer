# Verification round 2: al-muhit-fi-l-lugha

Verifier: independent fact-check (round 2), 2026-09-26.
Page checked: `roots/frontend/src/content/dictionary-guides/guides/al-muhit-fi-l-lugha.ts` (current file, 1,122 words lede + body).
I did not open research-notes.md or any revision-*.md file. I read verification-r1.md only for the list of prior flags. Every source was re-opened by me in this round, and every example entry was re-read from `_dict_guide_tool.py`.

## Sources consulted in this round

| id | URL | Opens? | What I checked |
|---|---|---|---|
| iranica | https://www.iranicaonline.org/articles/ebn-abbad-esmail-al-saheb-kafi/ | Yes in the browser pane. curl/WebFetch get 403 (Cloudflare) | Pomerantz, published 1 Jan 2000, updated 19 Jun 2017. It gives "(938-95), vizier and belletrist"; "protégé" of Abu'l-Fażl b. al-ʿAmid; letters "composed when the vizier was a scribe for Ebn al-ʿAmid"; vizier to Moʾayyad-al-Dawla (Isfahan), then under Faḵr-al-Dawla at Rayy; "died on 30 March 995 in Rayy"; "a distinctive predilection for rare linguistic usage (Ar. ḡarib)"; he was "the author of … the comprehensive dictionary al-Moḥiṭ fi'l-loḡa" |
| ibn-khallikan | https://shamela.ws/book/1000/222 (ids 222–226) | Yes | Book card: "المحقق: إحسان عباس، الناشر: دار صادر - بيروت". id 222 = p. 228 (أخذ الأدب عن أبي الحسين أحمد بن فارس); id 223 = p. 229 (Muʾayyad al-Dawla, then Fakhr al-Dawla); id 224 = p. 230 (كثر فيه الألفاظ وقلل الشواهد); id 226 = p. 232, where the entry ends |
| haywood | archive.org …JohnA.Haywood, Binder2_djvu.txt | Yes | pp. 62–64: "(326/938-385/995)"; vizier to Muʾayyad and Fakhr al-Dawla "in Isfahan and Rai"; "he preferred al-Khalil's method to that used by his master in the 'Mujmal' and the 'Maqayis'—that is, the modern dictionary arrangement" (p. 63); "employs the anagrammatical method of al-ʿAin"; "The accusation of lack of examples is justified, but the author's aim was apparently to give an exhaustive vocabulary in a small space" (p. 64). It also gives al-Azharī (d. 370/981) |
| muhit-ed | https://shamela.ws/book/83 | Yes | Card: Āl Yāsīn, ʿĀlam al-Kutub, Beirut, 1414/1994, 11 vols, "ترقيم الكتاب موافق للمطبوع". Pages read: 1:57–61 (ids 40–44), 2:170 (id 616), 5:67 (id 1963), 5:373 (id 2264), 6:250–251 (ids 2625–2626), 10:32 (id 4159) |
| al-yasin | https://shamela.ws/book/83/2 | Yes | Editor's introduction 1:9–34 (ids 2–27), read in full for pp. 9, 15–16 and 22–34 |
| jubouri | https://www.alukah.net/library/0/148209/ | Yes | Al-Jubūrī's introduction, table of contents and conclusions |
| hayyali | qindeel.ae product page | Yes (HTTP 200) | "بلغ عدد ما جمعته منها 636 نصًّا، 580 نصًّا منها وجدتها في (المحيط في اللغة)"; author "أ.د. عامر باهر اسمير الحيالي" |
| shamela-old | https://old.shamela.ws/epubs/000/83.epub | Yes (2.9 MB) | info.xhtml: "[الكتاب مرقم آليا غير موافق للمطبوع]". The text matches our stored entries: Efw "عفو وعفى عفى أهمله الخليل"; zwr with the stray "وال! زور"; grf "قال الصاحب …"; Zlm "وظلمت الشيء: نقصته، من قوله عز وجل"; and the رذق notice printed under the heading "رفق" |
| muhit-scan | https://archive.org/details/lis01996 (10_djvu.txt) | Yes | Vol. 10 OCR of the Zlm page, with the same footnotes 19–23 as Shamela 10:32, reads "وظلمت الشيء: [نقصته] من قوله عز وجل: ولم تظلم منه شيئا". The printed page has the phrase that the current Shamela page drops, so the stored text agrees with the print |

Every listed source was consulted and supports at least one claim. No listed source went unused.

## Claim table

S = supported, NQ = needs qualification, U = unsupported. The "Previously" column marks claims that round 1 flagged or that the reviser introduced.

| # | Claim | Previously | Verdict | Evidence |
|---|---|---|---|---|
| C1 | Title al-Muḥīṭ fī l-Lugha / المحيط في اللغة | | S | Shamela 83 card; Ibn Khallikān 1:230 "سماه المحيط"; Iranica |
| C2 | titleGloss "The Comprehensive Book on Language" | | S | An interpretive gloss. Haywood (pp. 64 and later) reads *muḥīṭ* as "all-embracing" but calls the meaning "doubtful" (ocean vs all-embracing). Acceptable as a gloss |
| C3 | author al-Ṣāḥib ibn ʿAbbād / الصاحب بن عباد | | S | Ibn Khallikān 1:228; Shamela card |
| C4 | authorFull Abū l-Qāsim Ismāʿīl ibn ʿAbbād | | S | Ibn Khallikān 1:228 "الصاحب أبو القاسم إسماعيل بن أبي الحسن عباد"; Haywood p. 62 |
| C5 | period 326–385 AH / 938–995 CE | | S | Haywood pp. 62–63; Iranica (born 14 Sep 938, died 30 Mar 995) |
| C6 | kind "Dictionary in al-Khalīl's order" | | S | Āl Yāsīn 1:15 "سار فيه مؤلفه على منهج الخليل في العين"; Jubouri |
| C7 | Summary: fills the *ʿAyn*'s framework with many more words | | S | Jubouri: 8,117 roots against 5,800 in the *ʿAyn* |
| C8 | Summary/lede: terse glosses, little quoted evidence | | S | Ibn Khallikān 1:230; Jubouri "انماز … بقلة شواهده … مختصرًا في توضيح معانيها"; Āl Yāsīn 1:16 "بعض الشواهد الشعرية ولكنها قليلة" |
| C9 | Summary advice: useful for recorded range of senses; check against works that show evidence | | S | Interpretive advice that follows from C7–C8 |
| C10 | Lede: its compiler was a Buyid vizier | | S | Iranica; Haywood p. 63 |
| C11 | Lede: kept the *ʿAyn*'s sound-based order and much of its wording | | S | Āl Yāsīn 1:15; Jubouri "يذكر ما ورد في كتاب العين"; entries 287 (ʿAyn) and 593 (Muḥīṭ) Zlm |
| C12 | Lede: added words from later collectors, above all al-Khārzanjī | | S | Jubouri "معتمدًا أولًا على تكملة العين للخارزنجي … مصادره الأخرى"; Āl Yāsīn 1:22 |
| C13 | Lede: sharply cut back the poetry the *ʿAyn* used as evidence | | S | Jubouri. Site data: verse separators appear in 356 of 505 displayed *ʿAyn* entries and in 21 of 836 displayed Muḥīṭ entries |
| C14 | Lede: usually silent about where each sense came from | | S | Jubouri "لم يكن يصرح بأسمائهم، بل إنه كثيرًا ما كان يغفل ذكرها" |
| C15 | Titled *al-Ṣāḥib*; a career official | | S | Ibn Khallikān 1:229; Iranica |
| C16 | Secretary to the vizier Ibn al-ʿAmīd | | S | Iranica "protégé" and "when the vizier was a scribe for Ebn al-ʿAmid"; Ibn Khallikān 1:229 "يصحب أبا الفضل ابن العميد" |
| C17 | Then vizier to two Buyid emirs at Isfahan and Rayy | revised (names dropped) | S | Iranica; Haywood p. 63; Ibn Khallikān 1:229 |
| C18 | Died at Rayy in 995 | | S | Iranica "died on 30 March 995 in Rayy" |
| C19 | A letter-writer with a taste for rare words | | S | Iranica "predilection for rare linguistic usage (Ar. ḡarib)" |
| C20 | Ibn Khallikān names Ibn Fāris among his teachers (1:228) | | S | 1:228 "أخذ الأدب عن أبي الحسين أحمد بن فارس اللغوي" |
| C21 | As Haywood observed, he passed over his teacher's alphabetical arrangement for al-Khalīl's (p. 63) | | S | Haywood p. 63 (quoted above). The claim is correctly attributed to Haywood |
| C22 | The introduction says nothing about why he wrote or for whom | | S | Muḥīṭ 1:57–61, read in full: word structure, the letter order, and replies to objections. No statement of purpose or audience. The text proper begins at 1:63 |
| C23 | The introduction explains al-Khalīl's system and defends it against objections from Sībawayh and al-Mubarrad (1:57–61) | | S | 1:58 (Sībawayh, "أقل ما تكون عليه الكلمة حرف واحد"); 1:60 (Sībawayh on the points of articulation); 1:61 (al-Mubarrad, then "ونحن نقول") |
| C24 | Arabic quotation "واعلم: أن الخليل لمّا هَمَّ … ويدير عليه أبوابه" (1:59) | | S | Verbatim at 1:59 |
| C25 | Its translation | | S | Accurate |
| C26 | Ibn Khallikān (d. 1282): *kaththara fīhi l-alfāẓ wa-qallala l-shawāhid* (1:230) | | S | 1:230 verbatim; Ibn Khallikān d. 681/1282 |
| C27 | Haywood thought the charge fair; the aim was "an exhaustive vocabulary in a small space" (p. 64) | | S | Haywood p. 64, verbatim |
| C28 | Letters ordered by point of articulation, from the throat outward (1:59–60) | new locator | S | 1:59 "ووجد مخرج الكلام كله من الحَلْق، فصيَّر أولاها بالابتداء أدخل حرف منها في الحلق"; 1:60 table from ع ح هـ خ غ "حلقية" to ف ب م "شفوية" |
| C29 | Within each letter: doubled, then sound and weak three-letter roots, then longer words (1:15) | locator tightened | S | 1:15 "ابتداءً بباب المضاعف الثنائي، ثم باب الثلاثي الصحيح، ثم باب الثلاثي المعتل، ثم باب اللفيف، ثم باب الرباعي، ثم باب الخماسي" |
| C30 | All orderings of the same consonants are handled together (Haywood p. 64) | | S | Haywood p. 64 "anagrammatical method". Confirmed in print: in vol. 10, لمظ comes immediately before ظلم in one section, followed by "[الظاء والنون]" |
| C31 | He treats the *ʿAyn* as al-Khalīl's own; his contemporary al-Azharī credited its contents to al-Layth | shortened name | S | Jubouri "معتقدًا أن العين هو للخليل لا لغيره … الأزهري الذي كان ينسب كلَّ ما ورد في هذا الكتاب إلى الليث بن المظفر". Contemporary: Haywood gives al-Azharī (d. 370/981) |
| C32 | He reports the *ʿAyn*, names al-Khalīl where it left a word out, and fills gaps first from al-Khārzanjī, then from sources he seldom names | | S | Jubouri (same passage, "لا يصرح بأسمائها غالبًا"); Āl Yāsīn 1:22 "وبخاصةٍ في ما أهمله الخليل" |
| C33 | The *Takmila* of al-Khārzanjī (d. 348/959) appears to be lost (1:23–24) | | S | 1:23 "توفي في رجب سنة ثمان وأربعين وثلاثمائة"; 1:24 "مفقوداً في أغلب الظن" |
| C34 | Most of what survives of it survives here: one collector found 580 of his 636 fragments in al-Muḥīṭ | | S | Qindeel: 636 texts, 580 of them found in al-Muḥīṭ. The rest are in al-ʿUbāb, al-Ṣaghānī's Takmila, Muʿjam al-buldān, the Tāj and others |
| C35 | Al-Azharī attacked al-Khārzanjī for taking words from written copies he had never heard read aloud, and so misreading them | | S | Āl Yāsīn 1:24–27, quoting the Tahdhīb ("صحفي، والصحفي … يصحّف فيكثر، وذلك انه يخبر عن كتبٍ لم يسمعها") |
| C36 | Āl Yāsīn calls the attack unfair (1:24–31) | | S | 1:28 "لم يستطع أنْ يكون علمياً وموضوعياً"; 1:29 "حملة ظالمة"; 1:31 summary (not infallible either) |
| C37 | "A rare word known only through al-Khārzanjī deserves a second look." | | S | Advice supported by 1:31 ("لم يكن معصوماً من … التصحيف") and the zwr entry, where Ibn ʿAbbād himself calls a Khārzanjī word a miscopying |
| C38 | Zlm: shared wording (*ẓulm* definition; *ẓalīm* = male ostrich; *ẓulima fa-ẓẓalama*; "wronged" ground) | | S | Entries 287 and 593 |
| C39 | In the *ʿAyn* three senses come with a poet (Kaʿb, Zuhayr, al-Nābigha), and *ẓulm* = *shirk* comes with its verse | | S | Entry 287. There is also an unnamed line for the teeth sense, but the claim counts named poets |
| C40 | *ʿAyn* excerpt and its translation (Q 31:13) | | S | Validator OK; the translation is accurate (*nuʾy* = the trench) |
| C41 | "Ibn ʿAbbād keeps most of these senses but drops every poet, and that verse as well" | R1 NQ, revised | S | Entry 593 has no poet and no Q 31:13. It lacks the *ʿAyn*'s ليلة ظلماء "very evil", أظلم فلان علينا البيت, and the generous-man sense, so "most" is accurate |
| C42 | Muḥīṭ Zlm excerpt and its translation | | S | Entry 593 = print 10:32 (scan). The translation is accurate |
| C43 | His additions are mostly more senses: a torrent "wronging" a valley, a "wronged" waterskin | | S | Both are in 593 and absent from 287 |
| C44 | The one general statement ("putting a thing out of its place") has no source or argument, and the entry does not use it to explain other senses | | S | Entry 593 original. The only other explanation in it is local (سميت لإظلامها for the three nights) |
| C45 | "Our English version groups several senses under that idea; the 'Original Text' view shows he does not." | NEW | S | Entry 593, harmonized: heading "'OUT OF PLACE' — CONCRETE EXTENSIONS OF ẒULM" over the waterskin, ground, torrent and donkey senses. The original is a flat sequence |
| C46 | Q 18:33 is quoted for *ẓalama* = "to diminish" | | S | Entry 593 "وظلمت الشيء: نقصته، من قوله عز وجل: ولم تظلم منه شيئا". The scan of vol. 10 has the phrase. The current Shamela 10:32 drops "وظلمت الشيء: نقصته من قوله عز وجل" but gives n. 23 "سورة الكهف آية 33" |
| C47 | A study of the whole book: quotations cut to the point, half-lines outnumber whole lines, sometimes a bare reference | | S | Jubouri: "يقتطع من الآية أو الحديث … عدد الأشطر الشعرية هو أكثر قياسًا بعدد الأبيات الكاملة … يشير إلى الآية … دون ذكرها" |
| C48 | "By our rough count" a full line of verse appears in about 20 of 836 entries | | S | 21 displayed entries contain "...". A few are prose (SlH, Eyr), so about 17–19 are verse. Labelled as a rough count |
| C49 | "Many statements are impersonal, introduced by 'it is said' (*wa-qīla*) or 'they say', and his sources usually go unnamed" | R1 NQ, revised | S | Jubouri "كثرت عنده عبارات مثل: (قال، قيل، قالوا، يقولون)" and "لم يكن يصرح بأسمائهم". Site: وقيل in 293 and يقولون in 189 of 836 entries |
| C50 | grf excerpt "قال الصاحب … بخطه" and its translation | | S | Entry 8051; print 5:67 |
| C51 | The grf remark is on the tree *gharaf*; the entry does not say which Abū Ḥanīfa | NEW | S | Entry 8051 "والغرف - على وزن مطر -: شجر القسي"; print 5:67 nn. 31–35 give no identification. The site's harmonized English adds "Abū Ḥanīfa [al-Dīnawarī]" (see site-data issues) |
| C52 | zwr: a word from al-Khārzanjī called "a miscopying in my view" (*taṣḥīf ʿindī*), the true word having *r* for *z* | | S | Entry 8248 "وحكى الخارزنجي: الزائرة … وهو تصحيف عندي؛ لأنه هو الرائرة - بالراء دون الزاي -" |
| C53 | Such remarks are rare in the entries we display, but a full study gives a whole section to his linguistic criticism, including of al-Khalīl and al-Khārzanjī | R1 NQ, revised, NEW | S | Site: "قال الصاحب" occurs only in grf and qEd. Other "عندي" hits are ordinary usage, apart from zwr. Jubouri ToC "النقد اللغوي 233-257 … نقد الصاحب للخليل 249-252 … نقد الصاحب للخارزنجي 252-255"; conclusions "نقده لأصحاب المعجمات كالخليل والخارزنجي" |
| C54 | kfr opens with *kufr* as the opposite of *īmān* and as ingratitude (opposite of *shukr*), then gives a classification | | S | Entry 568. "Disobedience and refusal" and *kufr ʿalā kufr* come in between, which is acceptable for "opens with" |
| C55 | kfr excerpt and its translation | | S | Entry 568 = print 6:250–251. The translation is accurate |
| C56 | "In our reading" the four kinds sort a religious concept; the entry gives them no source | | S | Labelled as interpretation. Entry 568 cites no source |
| C57 | The Lisān gives nearly the same scheme, credited to "some of the learned" (*baʿḍ ahl al-ʿilm*): Ibn ʿAbbād's first three kinds, plus *inkār*, explained as unbelief "with his heart and his tongue" | R1 NQ, revised, NEW | S | Displayed Lisān kfr (entry 158): "قال بعض أهل العلم: الكفر على أربعة أنحاء: كفر إنكار … وكفر جحود، وكفر معاندة، وكفر نفاق … فأما كفر الإنكار فهو أن يكفر بقلبه ولسانه" |
| C58 | "Much of the rest is concrete: the night is *kāfir*; so is a valley that 'has covered everything along its sides'" | R1 NQ, revised | S | Entry 568 "والكافر: الليل … ووادٍ كافر: غطى كل ما على جوانبه". "Much" is correct, since *kaffāra*, the *kāfūr* spring in Paradise and *takfīr* are not concrete |
| C59 | He ties several senses to covering but never says that covering unites them; "our English version, again, says it does" | NEW | S | Original: "لأنه يغطيها", "لبسها مغطاة", "ملبس تراباً", "غطى كل ما على جوانبه", "الغطاء", with no unifying statement. Harmonized: "whose unifying thread is covering/concealing" |
| C60 | *kufr ʿalā kufr* = "hatred upon hatred" (*bughḍ*); other dictionaries read *kafr ʿalā kafr*, "one upon another" (*baʿḍ*) (6:250 n. 17), as our al-Muḥkam does | | S | 6:250 n. 17 "هكذا ضُبطت الجملة في الأصول، وفي المحكم واللسان والتاج: كَفْر على كَفْرٍ أي بَعْض على بَعْض". Displayed Muḥkam kfr "كَفْر على كَفْر: أَي بعض على بعض". The displayed Lisān and Tāj agree |
| C61 | The two words differ by one dot | | S | بغض / بعض |
| C62 | It shows how far recorded uses reached: diminishing *ẓalama* (Q 18:33), the night and the covering valley beside *kufr* | | S | Entries 593 and 568 |
| C63 | It rarely says which sense a verse intends, and it cannot date a usage | | S | Only 139 of 836 displayed entries contain a Qur'an-citation formula (عز وجل / تعالى). There are no dates. This is interpretation, and fair |
| C64 | Finished by 995; material from the eighth-century *ʿAyn* through al-Khārzanjī's tenth-century gleanings to unnamed sources | | S | Death date (C18); C32–C33; Jubouri |
| C65 | Without the poetry you usually cannot see who used a word, or when | | S | Follows from C13 and C47 |
| C66 | The order of senses is not a history: the kufr entry puts the religious senses first | | S | Entry 568. Jubouri also notes no fixed order of forms within an entry ("لا يسير على ترتيب معين") |
| C67 | Al-Ṣaghānī's al-ʿUbāb and the Tāj quote it very often (1:9 n. 2, 33) | | S | 1:9 n. 2 (al-ʿUbāb 1:8; Tāj 1:39 "وفي كثير من صفحاته"); 1:33 "ما جاء في العباب وتاج العروس منقولاً عن المحيط وهو كثير جداً" |
| C68 | On our site the Tāj cites "Ibn ʿAbbād" by name in more than 250 entries | | S | 285 displayed Tāj entries contain ابن عباد (not ابن عبادة). Almost all are in citation form: عن 294, وقال 156, قال 74, نقله 64 … |
| C69 | onOurSite: our stored text, taken from arabiclexicon.hawramani.com, matches (apart from small slips) the older Shamela digital text of Āl Yāsīn's edition | | S | source_url in every entry points to hawramani. The EPUB matches the stored text in Efw, zwr (including "وال! زور"), grf, Zlm and rfq (including the misplaced "رفق" heading). The EPUB does not name its edition; the identification rests on its agreement with the Āl Yāsīn print (C70) and the same Shamela book id 83 |
| C70 | Where checked against the printed pages it matches them (scan 10:32) | | S | Scan vol. 10 OCR: "وظلمت الشيء: [نقصته] من قوله عز وجل"; the same footnotes 19–23 as Shamela 10:32 |
| C71 | The editor's footnotes and al-Khalīl-order chapter headings are not included | | S | Entries 593, 568, 9061 and 3183 against print 10:32, 6:250–251, 5:373 and 2:170. The EPUB has headings such as "الزاي والراء و. ا. ي", and our entries do not |
| C72 | We display 836 roots | | S | `_dict_guide_tool.py dicts` |
| C73 | Root letters run into the text; stray characters; misplaced vowels; many short entries | | S | "ظلم: لقيته…", "غرف الغرف…", "وال! زوَرُ", "أُهْمَلَه" (Efw); many entries are a few lines long |
| C74 | onOurSite: the default English view at present files several Zlm senses under an "out of place" heading and gives the kfr senses a "unifying thread" of covering; use "Original Text" for his own order and wording | NEW | S | Harmonized entries 593 and 568 (quoted in C45 and C59) |
| C75 | Efw: in print "al-Khalīl left it out" refers only to the spelling عفى (2:170) | | S | 2:170 "عفو عفى: «عفى» أهْمَلَه الخَليلُ وحَكاه الخارْزَنْجِيّ". Stored: "عفو وعفى عفى أُهْمَلَه الخَليلُ" |
| C76 | rfq opens with a note on *al-rawādhiq*, meat cooked with seasonings, which the edition places under that word's root; our copy has no entry for that root (5:373) | NEW | S | Entry 9061 "رفق مُهْمَلٌ عنده. الخارزنجي: الرَّوَاذق: ما طُبخَ من لَحْمٍ وخُلِطَ بأخْلاطِه"; print 5:373 heading "رذق: مُهْمَلٌ عنده"; `find-root رذق` gives "No match" |
| C77 | Source note: the older Shamela EPUB is "numbered automatically, not matching the printed edition" | | S | EPUB info.xhtml "[الكتاب مرقم آليا غير موافق للمطبوع]" |

**Totals: 77 claims. 77 supported, 0 need qualification, 0 unsupported.**

## Round-1 flags: status

| R1 flag | Fix applied? | Round-2 verdict |
|---|---|---|
| C38 "keeps the senses" | Yes, now "keeps most of these senses but drops every poet, and that verse as well" | S (C41) |
| C45 "Most entries speak impersonally" | Yes, now "Many statements are impersonal…" | S (C49) |
| C48 "Such remarks are rare; … checking copies" | Yes. Rarity is limited to the displayed entries, and Jubouri's section is cited | S (C53); Jubouri ToC pp. 233–257 verified |
| C52 Lisān "with different members" | Yes, rewritten | S (C57); matches entry 158 exactly |
| C53 "The rest of the entry is concrete" | Yes, now "Much of the rest is concrete" | S (C58) |
| Brief must-fix: English view contradicts the method points | Yes, in the body (twice) and in onOurSite | Resolved; see the suggestion below on redundancy |

## Flagged items

None. No claim in this round needs qualification or is unsupported.

## Brief issues (not factual)

- **suggestion: length.** Lede + body is now 1,122 words (validator). Round 1 had 1,097, and the target is roughly 700–1,100. The caveat about the English view now appears three times: the Zlm parenthetical, the kfr clause, and onOurSite. Keeping it in onOurSite (where it belongs, as a note on the stored text) and cutting the two body parentheticals to a few words, or removing them, would bring the page under 1,100 without losing substance.
- **suggestion: statements that can go stale.** The body parentheticals describe the *current* harmonized English ("Our English version groups…", "our English version, again, says it does"). If the site-data issue below is fixed, these sentences become false. Only onOurSite says "at present". Better: fix the harmonized entries and then drop the caveats. Failing that, keep the caveat only in onOurSite with "at present".
- **suggestion: grf.** The default English view of grf says "Abū Ḥanīfa [al-Dīnawarī]", and the essay says "the entry does not say which Abū Ḥanīfa". Both are true (the English bracket is an editorial addition), but a reader who clicks through may see a clash. Optionally add "(our English version supplies al-Dīnawarī; the original does not)". Also, the editor notes that one manuscript (ت) lacks the whole "قال الصاحب … والواحدة غرفة" passage (print 5:67 n. 34). This is not required, but it matters if the essay leans on this remark as the author's own voice.
- No generic praise, no rankings, no forced "original root meaning" narrative (the essay explicitly declines to read *aṣl* as a unifying theory). Every root mention is linked, and each link resolves to a displayed entry. Translations are labelled, and interpretation is flagged ("In our reading", "By our rough count"). The essay tone is good.

## URL problems

- Iranica returns 403 to scripted fetches (Cloudflare) and opens normally in a browser. It is fine for readers.
- jubouri (the author's own summary on alukah) and hayyali (the publisher's description) are summaries, not the full works. Both are adequate for the narrow claims attached to them.
- No broken or mis-identified URLs. All nine sources opened and are the stated works.

## Validator

`node scripts/validate-dictionary-guides.mjs al-muhit-fi-l-lugha` passes: "=== al-muhit-fi-l-lugha — ok"; 11 root links (9 distinct root/dictionary pairs), 4 excerpts, 1,122 words, example roots Zlm, grf, zwr, kfr, Efw, rfq; "1/1 guides pass". The API returns 200 for /api/root/{Zlm,grf,zwr,kfr,Efw,rfq}/dictionaries.

## Site-data issues

1. The harmonized English (the default view) adds semantic unifications the author does not make. For Muḥīṭ Zlm (entry 593) it adds the heading "'OUT OF PLACE' — CONCRETE EXTENSIONS OF ẒULM". For Muḥīṭ kfr (entry 568) it opens "whose unifying thread is covering/concealing". Both are still present in this round. They are worth correcting at the data level, and the essay's caveats could then be removed.
2. The harmonized English for Muḥīṭ grf (entry 8051) identifies "Abū Ḥanīfa [al-Dīnawarī]". The original and the Āl Yāsīn print (5:67) do not name him.
3. The stored rfq entry (9061) begins with the رذق notice ("رفق مُهْمَلٌ عنده. الخارزنجي: الرواذق…"). The print places it under the heading "رذق" (5:373). The error comes from the older Shamela EPUB, which has the same misplaced "رفق" heading.
4. The stored label (al-Ṣāḥib b. ʿAbbād) and date (995) are correct. He died on 30 March 995 in Rayy (Iranica).
