# al-Ṣiḥāḥ: independent verification, round 4 (2026-09-26)

Checked: `roots/frontend/src/content/dictionary-guides/guides/al-sihah.ts`, the version after the final revision.
I did not open `research-notes.md` or any `revision-*.md`. I read `verification-r3.md` only to see what round 3 flagged. Then I re-checked the whole essay from the sources.

**Method.**
- Shamela: I fetched every cited page with curl and read its printed-page header (ج/ص). That covers the preface, the ʿAṭṭār essay, the kfr/rkE/Alh pages, Muzhir, Yāqūt, Dhahabī and the Lisān introduction. I also read the five book cards.
- Haywood: I downloaded the archive.org OCR text (`12555_djvu.txt`) and read chapter 6 in full. I placed page breaks by the printed numbers 69–75.
- Baalbaki: I downloaded the AUB PDF and ran `pdftotext` on each page.
- Other sources: I fetched both Iranica Wayback copies, al-Mawsūʿa and the Hawramani collection page.
- Our entries: I read the stored entries with `_dict_guide_tool.py entry` and scanned the displayed Ṣiḥāḥ entries with a read-only SQLite query.
- Edition match: I diffed the stored kfr, rkE and Alh texts against ʿAṭṭār's Shamela text. I used difflib after normalising vowel marks and hamza seats.
- Qur'an references: I checked each one against the local verse API.

**Totals: 78 claims. 78 supported, 0 need qualification, 0 unsupported.** The validator passes.

## The round-3 flag

| Item | Now reads | Verdict |
|---|---|---|
| C69 (r3), "word for word" | "…match ʿAṭṭār's edition as digitised on al-Maktaba al-Shāmila almost word for word, including that digital text's asterisks but not the editor's footnotes." | **Fixed and supported.** My diff against 23235/1597–1600 (kfr), /2418 (rkE) and /4401–4404 (Alh) shows only insertions on the Shamela side: neighbouring entries, the footnotes and one "زيادة من نسخة" note. There is one exception. In Alh, our "فك م" stands against Shamela's "فكأنهم" (/4404, vol. 6 p. 2224). kfr and rkE are exact, asterisks included. "Almost word for word" is accurate. |
| Brief: 1,101 words | unchanged | Still 1,101 per the validator. This remains a suggestion (see below). |

No new claims were introduced in this revision.

## Sources opened (round 4)

| id | What I saw | OK? |
|---|---|---|
| jawhari-preface | shamela.ws/book/23235/50, header "ج1 - ص33 … مقدمة المؤلف". Full preface: "أودعت هذا الكتاب ما صح عندي من هذه اللغة، التى شرف الله منزلتها … على ترتيب لم أسبق إليه، وتهذيب لم أغلب عليه، في ثمانية وعشرين بابا، وكل باب منها ثمانية وعشرون فصلا … بعد تحصيلها بالعراق رواية، وإتقانها دراية، ومشافهتي بها العرب العاربة، في ديارهم بالبادية". | yes |
| muzhir | 6936/68–72 = vol. 1 pp. 74–78. Card: al-Suyūṭī (d. 911), ed. Fuʾād ʿAlī Manṣūr, DKI, 1st ed. 1418/1998. | yes |
| iranica-farab | Wayback 20260923051656. "Article by Clifford Edmund Bosworth … Vol. IX, Fasc. 2, p. 208 Published December 15, 1999". It has "The lexicographer Abū Naṣr Ḥammād Jawharī (d. 393/1003?) … was born in Fārāb" and "on the middle Syr Darya … in Transoxania". | yes |
| yaqut | 9788/656–659 = vol. 2 pp. 656–659. Card: ed. Iḥsān ʿAbbās, Dār al-Gharb al-Islāmī, 1st ed. 1414/1993. | yes |
| dhahabi | 10906/10491–10493 = vol. 17 pp. 80–82. Card: vol. 17 ed. al-ʿIrqsūsī; al-Risāla, 3rd ed. 1405/1985. p. 82: "قال جمال الدين علي بن يوسف القفطي: مات الجوهري … في سنة ثلاث وتسعين وثلاث مائة. ثم قال: وقيل: مات في حدود سنة أربع مائة". | yes |
| haywood | archive.org in.gov.ignca.12555 (metadata: "Arabic lexicography", Haywood, John A., 1960). Ch. 6 "The Rhyme Arrangement: the 'Sahah' of al-Jauhari", pp. 68–76. | yes |
| baalbaki-2019 | AUB PDF, header "Journal of Abbasid Studies 6 (2019) 185-208". PDF page 2 (printed p. 186) has, in the continuation of n. 1: "al-Jawharī's (d. ca. 400/1010) al-Ṣiḥāḥ". | yes |
| attar-ed | 23235 card: ed. ʿAṭṭār, Dār al-ʿIlm lil-Malāyīn, 4th printing 1407/1987, 6 vols, "ترقيم الكتاب موافق للمطبوع". Page headers: kfr ج2 ص807–808 (section labels باب الراء, فصل الكاف); rkE ج3 ص1222 (باب العين, فصل الراء); Alh ج6 ص2223–2224 (باب الهاء, فصل الالف). | yes |
| attar-essay | 23235/12 has the heading "[الجوهري مبتكر منهج الصحاح:]". /20–22 have "وإن كان مسبوقا في الزمن والتأليف من قبل البندنيجي أو الفارابي"; "أما دعواه في نفي الابتكار عن الجوهري أن البندنيجي سبقه فمردودة"; "ونحن لا نشك في أن الفارابي يعد واضع بعض أساس منهج الصحاح"; and "فالامام الجوهري مبتكر منهجه ابتكارا … وإن ظهر … أن «كتاب التقفية» تقدم معجم الصحاح بزمن غير يسير". | yes |
| lisan-intro | 1687/7–8; card Dār Ṣādir, 3rd printing 1414. p. 7: "فتداولوه وتناقلوه … قد صحّف وحرّف … فأتيح له الشيخ أبو محمد بن بري فتتبع ما فيه … ورتبته ترتيب [الصحاح] في الأبواب والفصول". p. 8: "هذه الأصول الخمسة". | yes |
| iranica-dict | Wayback 20260629143409. "Vol. VII, Fasc. 4, pp. 387-397 Published December 15, 1995". Part i is signed (ʿALĪ AŠRAF ṢĀDEQĪ): "Moḥammad Naḵjavānī's Ṣehāḥ al-fors (2,300 entries, comp. 728/1328) … arranged on the model of the Arabic Ṣeḥāḥ al-loḡa by Jawharī Fārābī". | yes |
| mawsua | arab-ency.com.sy/details/5188. Signed شوقي المعري; "المجلد السابع، طبعة 2003 … رقم الصفحة ضمن المجلد: 822". It has "وفي سنة وفاته خلاف، لكنّ معظم المصادر تشير إلى أنّ الجوهري مات نحو سنة 400هـ"; "وهذا الخبر يناقض … كما يستدل منه على أن وفاة الجوهري كانت بعد سنة 396هـ"; "حواشي عبد الله بن برّي (ت582هـ)"; and "مختار الصحاح". | yes |
| hawramani | Collection page loads. Title "Ismāʿīl bin Ḥammād al-Jawharī, Tāj al-Lugha wa Ṣiḥāḥ al-ʿArabīya". It has "Al-Jawharī (d. 1003 CE / 393 AH)". It names no edition: no match for edition, عطار, تحقيق or طبعة. | yes |

Every listed source is cited in the essay, and every URL opens the stated work.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Field | Claim | V | Evidence |
|---|---|---|---|---|
| C1 | title/titleAr | al-Ṣiḥāḥ / الصحاح | S | Shamela 23235 card; Muzhir 1:74 "سمّى كتابه بالصحاح" |
| C2 | titleGloss | Full title Tāj al-Lugha wa-Ṣiḥāḥ al-ʿArabiyya, glossed "The Crown of Language and the Sound Words of Arabic" | S | Preface heading 23235/50; Haywood p. 69 ("The crown of language and the correct of Arabic"); Muzhir 1:75 (ṣiḥāḥ as plural of ṣaḥīḥ) |
| C3 | author/authorFull/authorAr | Abū Naṣr Ismāʿīl ibn Ḥammād al-Jawharī / الجوهري | S | Preface "قال الشيخ أبو نصر إسماعيل بن حماد الجوهري" |
| C4 | period | d. 393 AH (1002–3) or c. 400 (c. 1010); disputed | S | Dhahabī 17:82; Baalbaki p. 186 n. 1; Mawsūʿa "في سنة وفاته خلاف" |
| C5 | kind/sortYear | Rhyme-ordered general dictionary; 1003 | S | Haywood ch. 6 title; Baalbaki n. 1 "general lexica, such as al-Jawharī's" |
| C6 | summary | Compact general dictionary from about 1000, filed by each root's last letter | S | Preface; Haywood pp. 71, 74 ("succinct definitions") |
| C7 | summary | Set out to include only what he judged sound | S | Preface "ما صح عندي" |
| C8 | summary | Definitions, named authorities and grammatical arguments were absorbed and corrected by later dictionaries such as Lisān | S | Lisān intro 1:7–8; Lisān Alh (id 111, Ibn Barrī's rebuttal) and kfr (id 158, "قال الجوهري") |
| C9 | lede | The preface is only a few lines long | S | 23235/50 is one paragraph; Haywood p. 71 "remarkably short" |
| C10 | lede | Two claims define it: sound "in my judgement", and a new arrangement | S | Preface; Haywood p. 71 "makes two claims: to have included only correct words, and to have initiated a new arrangement" |
| C11 | lede | Entries name authorities, show a grammarian's interest in how words are built, and leave much out | S | Entries 155 and 109; Haywood p. 74 ("deep interest in grammar, syntax, and derivation"), p. 75 ("had omitted much") |
| C12 | lede | Read it as one scholar's selection, not a record of everything the Arabs said | S | Interpretation resting on C7, C10, C11 and Muzhir 1:77–78 |
| C13 | body | Preface quotation (Arabic) | S | Matches 23235/50; the ellipses mark omitted text |
| C14 | body | Translation of the preface quotation | S | Accurate; labelled as made for this guide |
| C15 | body | "The standard is personal: ʿindī" | S | Reading of "ما صح عندي", framed as interpretation |
| C16 | body | Al-Suyūṭī (d. 911/1505): first to confine himself to sound material, "and for this he named his book al-Ṣiḥāḥ" | S | Muzhir 1:74 "وأولُ مِن التزمَ الصحيح مقتصرا عليه … الجَوْهَري ولهذا سمَّى كتابه بالصحاح" |
| C17 | body | Also voiced al-Ṣaḥāḥ | S | Muzhir 1:75 (al-Tibrīzī: "ويقال: الصَّحاح بالفتح") |
| C18 | body | Not to be confused with al-Zabīdī's much later Tāj al-ʿArūs | S | Different title; al-Zabīdī stored 1790; separate guide |
| C19 | body | Born in Fārāb in Transoxiana | S | Iranica "Fārāb" ("was born in Fārāb", "in Transoxania"); Haywood p. 69 |
| C20 | body | Studied Arabic in Iraq with Abū ʿAlī al-Fārisī and Abū Saʿīd al-Sīrāfī | S | Yāqūt 2:656 "دخل العراق فقرأ علم العربية على … أبي علي الفارسي وأبي سعيد السيرافي" |
| C21 | body | Travelled among the tribes of Rabīʿa and Muḍar | S | Yāqūt 2:656 "طوّف بلاد ربيعة ومضر"; Mawsūʿa ("قبائل"); Haywood p. 69 ("the lands of the Mudar and Rabi'a tribes") |
| C22 | body | Settled in Nishapur, teaching and copying books | S | Yāqūt 2:656 "مقيما بها على التدريس والتأليف وتعليم الخط وكتابة المصاحف والدفاتر" |
| C23 | body | Died in 393 (1002–3) or around 400 (c. 1010) | S | Dhahabī 17:82 (al-Qifṭī, then "وقيل … في حدود سنة أربع مائة"); Baalbaki p. 186 n. 1 |
| C24 | body | Yāqūt quotes al-Mujāshiʿī: al-Jawharī died when al-Bīshakī, for whom he wrote the book, had heard it only as far as ḍād | S | Yāqūt 2:658 "صنف «كتاب الصحاح» للأستاذ أبي منصور … البيشكي، وسمعه منه إلى باب الضاد المعجمة … فوقع فمات" |
| C25 | body | A pupil fair-copied the rest and "made gross errors in several places" | S | Yāqūt 2:658 "فبيّضه أبو إسحاق إبراهيم بن صالح الوراق تلميذ الجوهري بعد موته، فغلط فيه في عدة مواضع غلطا فاحشا" |
| C26 | body | Haywood: "a pinch of salt" | S | Haywood p. 69 |
| C27 | body | Yāqūt saw a copy in al-Jawharī's hand dated 396 (1005–6) | S | Yāqūt 2:658–659 "وقفت على نسخة بالصحاح بخطّ الجوهري بدمشق … وقد كتبها في سنة ست وتسعين وثلاثمائة" |
| C28 | body | A modern reference: this contradicts the story and puts his death after 396 | S | Mawsūʿa p. 822 (quoted above) |
| C29 | body | Al-Tibrīzī: some taṣḥīf is the author's own | S | Muzhir 1:75 "فيه تصحيفٌ لا يُشَكُّ في أنه من المصنِّف لا من الناسخ" |
| C30 | body | Filed by last letter, in 28 chapters (bāb) | S | Preface "في ثمانية وعشرين بابا"; Haywood p. 71 ("according to their final radicals") |
| C31 | body | Sections (faṣl) by first letter | S | Preface ("ثمانية وعشرون فصلا"); Haywood p. 71 ("according to the first, and then the intermediate radicals") |
| C32 | body | Kufr sits in bāb al-rāʾ, faṣl al-kāf (vol. 2 p. 807) | S | 23235/1598: header ج2 ص807, labels "باب الراء" and "فصل الكاف" |
| C33 | body | The novelty is disputed; his maternal uncle al-Fārābī used final-letter order inside the subsections of Dīwān al-Adab | S | Haywood p. 69 ("the rhyme order was only used in subsections"); Yāqūt 2:656 "ابن أخت أبي إسحاق الفارابي صاحب «ديوان الأدب»" |
| C34 | body | ʿAṭṭār grants the uncle "part of the foundation" and the priority of al-Bandanījī's rhyme book, still calls al-Jawharī the originator, and rejects al-Jāsir | S | attar-essay 23235/20–22 (quoted above) |
| C35 | body | Lisān arranged "in the order of the Ṣiḥāḥ" | S | Lisān intro 1:7 "ورتبته ترتيب [الصحاح] في الأبواب والفصول" |
| C36 | body | A 14th-century Persian dictionary was modelled on it | S | Iranica "Dictionaries i": Ṣehāḥ al-fors, 728/1328 |
| C37 | body | On our site each entry stands alone, so the arrangement is invisible | S | Site behaviour (one entry per root page) |
| C38 | body | Vowels spelled out (bi-l-fatḥ, bi-l-kasr) or shown by a model word after mithl | S | Haywood p. 74 ("to indicate vowels … in full wording … and to use familiar words as models"); entry 155 "بالفتح", "بالكسر", "مثل جائع وجياع" |
| C39 | body | A named authority marks a report; unattributed sentences are presented as his own | S | Reading advice consistent with entries 155 and 109; qualified in the next sentence by Haywood |
| C40 | body | Haywood: his definitions often coincide with al-ʿAyn's | S | Haywood p. 74 "(often coinciding with those of the 'Ain')" |
| C41 | body | The kfr entry opens with the religious senses, then turns to covering | S | Entry 155 |
| C42 | body | kfr excerpt 1: Arabic and translation | S | Entry 155; identical to Shamela 2:807 |
| C43 | body | "Denial" is illustrated by Q 28:48 and Q 17:99 | S | Entry 155. Verse API: 28:48 "إنا بكل كافرون"; 17:99 "فأبى الظالمون إلا كفورا" |
| C44 | body | "Covering" is illustrated by a line recited by al-Aṣmaʿī | S | Entry 155 "وأنشد الاصمعي … غير رماد مكفور" |
| C45 | body | Further senses: village, grave, dark of night, sea, great river, the farmer "because he covers the seed with soil" | S | Entry 155 |
| C46 | body | Partway through, the link between the two groups appears in Ibn al-Sikkīt's name | S | Entry 155 "قال ابن السكيت: ومنه سمي الكافر" |
| C47 | body | kfr excerpt 2: Arabic and translation | S | Entry 155 |
| C48 | body | Ibn Fāris's excerpt and translation; covering as the governing principle, in his own voice | S | Entry 163 (Maqāyīs kfr) |
| C49 | body | Ibn Fāris unifies (the truth is covered); al-Jawharī lists, and Ibn al-Sikkīt derives the word from covering God's favour | S | Entries 163 and 155 |
| C50 | body | Ibn Fāris cites Q 57:20 for kuffār = farmers; al-Jawharī gives the sense without the verse | S | Entry 163 "{أعجب الكفار نباته} [الحديد: 20]"; entry 155 "والكفار: الزراع" (no verse) |
| C51 | body | A dictionary shows a sense existed; whether a verse uses it depends on context | S | Methodological framing, consistent with the brief |
| C52 | body | The poetry line gets two readings: the sea / sunset, or the night | S | Entry 155 "يعني الشمس أنها بدأت في المغيب. ويحتمل أن يكون أراد الليلَ" |
| C53 | body | Law and doctrine terms near the end: the qibla maxim; kaffāra (Q 5:89); takfīr of sins likened to iḥbāṭ; no witness quoted, nothing dated | S | Entry 155; Q 5:89 "فكفارته … ذلك كفارة أيمانكم" |
| C54 | body | Ibn Barrī d. 582 AH | S | Mawsūʿa "(ت582هـ)" |
| C55 | body | Ibn Barrī wrote corrective notes on the book | S | Muzhir 1:76 "الحواشي على الصحاح"; Lisān 1:7 "فتتبع ما فيه … مخرّجا لسقطاته" |
| C56 | body | Ibn Barrī: "the most grammatical of the lexicographers" | S | Muzhir 1:75 "الجوهري أَنْحَى اللغويين" |
| C57 | body | Alh: alaha = worshipped; Ibn ʿAbbās's reading "and your worship" at Q 7:127 | S | Entry 109; Q 7:127 "ويذرك وءالهتك" |
| C58 | body | Alh excerpt 1: Arabic and translation | S | Entry 109 = Shamela 6:2223 |
| C59 | body | He states his view, reports Abū ʿAlī's opposite view (heard in person) at length without reply, and adds Sībawayh's alternative; nothing is resolved | S | Entry 109 "وسمعت أبا على النحوي يقول … وجوز سيبويه أن يكون أصله لاها على ما نذكره من بعد" |
| C60 | body | Ibn Barrī's reply survives in Lisān's Alh entry; excerpt and translation | S | Lisān Alh, entry 111 (displayed): "قال ابن بري عند قول الجوهري … هذا رد على أبي علي الفارسي … ولا يلزمه ما ذكره الجوهري …" |
| C61 | body | "Idols" excerpt and translation | S | Entry 109 = Shamela 6:2224 |
| C62 | body | The rkE excerpt is the whole entry; no witness and no verse | S | Entry 5785 = Shamela 3:1222, exact |
| C63 | body | Ritual bowing appears as one use of an ordinary word for bending | S | Entry 5785 "ومنه ركوع الصلاة" |
| C64 | body | Ibn Manẓūr: "passed it from hand to hand"; it had misreadings that Ibn Barrī traced | S | Lisān intro 1:7 |
| C65 | body | Al-Ṣaghānī's Takmila, a completion of what it missed | S | Muzhir 1:76 "التكملة على الصحاح ذكر فيها ما فاته من اللغة" |
| C66 | body | Fīrūzābādī: "two-thirds of the language or more"; he singled it out because it was widely used and teachers relied on it | S | Muzhir 1:77–78 "فاته ثلثا اللغة أو أكثر … لِتَدَاوُله واشتهارِه … واعتماد المدرسين على نُقُوله" |
| C67 | body | Lisān used it, with Ibn Barrī's notes, as a source | S | Lisān intro 1:7–8 |
| C68 | body | On our site al-Jawharī is often named inside Lisān and Tāj | S | My count: "الجوهري" appears in 801 of 1,452 displayed Lisān entries and 377 of 1,600 displayed Tāj entries |
| C69 | body | Lisān kfr repeats "or he may have meant the night" and credits al-Jawharī | S | Lisān kfr (id 158) "قال الجوهري: ويحتمل أن يكون أراد الليل" |
| C70 | body | Mukhtār al-Ṣiḥāḥ is an abridgement | S | Haywood p. 75; Mawsūʿa |
| C71 | body | The date belongs to the compilation, not the usages; silence proves nothing; the verse must be weighed | S | Methodological framing |
| C72 | onOurSite | 866 roots displayed | S | Scan: 866 displayed entries, 866 distinct roots |
| C73 | onOurSite | Hawramani names no edition | S | Collection page |
| C74 | onOurSite | Compared entries match ʿAṭṭār's Shamela text almost word for word, with its asterisks and without the footnotes | S | Diff: kfr and rkE exact; Alh has one garble ("فك م" / "فكأنهم", 23235/4404); asterisks at the same places |
| C75 | onOurSite | Hamza often unwritten; vowel marks partial | S | Stored "لانه", "الاله", "الاصمعي", "الشئ" |
| C76 | onOurSite | 17 hamza-final roots open with the weak-letter root's entry; qrA opens with qarw, a wooden bowl | S | Scan: jyA, swA, nbA, qrA, mrA, brA, n$A, xTA, bwA, bdA, DwA, *rA, xsA, hyA, hnA, SbA, $TA; qrA "[قرا] القَرْوُ: قدحٌ من خشب" |
| C77 | onOurSite | Nine repeat their heading over a similar-looking root's passage (nZr opens with nāṭūr); one root is in both groups | S | Scan: nZr (نطر), xlf (خطف), jbl (جيل), rjf (رخف), lHq (لخقوق), brq (يرقان), xsA (حسا), Hlq (حلقن), Anf (أثف); xsA is in both groups |
| C78 | onOurSite | A few are cut short (Ayd is two words); our English summary for kufr calls covering "the root sense", but al-Jawharī does not | S | Ayd "[أيد] أبو زيد:"; kfr harmonized_en §3 "Kafr as covering — the root sense", which is not in entry 155 |

The bibliographic details in `sources` also match the book cards, the page headers and the article headers listed above.

## Flagged items and fixes

None. The single round-3 flag (the "word for word" wording in `onOurSite`) is fixed, and I found no new problem.

## Brief issues (not factual)

- **Suggestion: length.** The validator still counts 1,101 words for the lede and body, one over the "roughly 700–1,100" guide. This is acceptable as it stands. If a trim is wanted, "Brevity is the book's other face." → "Brevity is its other face." would do it.
- **Suggestion (optional).** "The same Ṣiḥāḥ entry makes a remark worth carrying to any dictionary" is mildly editorial. It is harmless, and the remark it introduces is al-Jawharī's own.
- I found no padding, rankings, generic praise, encyclopedia-style biography, forced "original root meaning" narrative, bare root mention or unlabelled translation.

## URL problems

None. Every URL opens the stated work. The Iranica links are Wayback copies and load.

## Validator

`node scripts/validate-dictionary-guides.mjs al-sihah` returns **ok**: 12 root links (9 distinct pairs), 7 excerpts, 1,101 words. 1/1 guides pass.

## Site-data issues

- **Date.** The stored death year 1003 (= 393 AH) follows al-Qifṭī (via al-Dhahabī), the Shamela card ("ت ٣٩٣هـ"), Iranica ("d. 393/1003?") and Hawramani. Other sources put it later:
  - Al-Mawsūʿa says most sources give about 400 AH, and infers a death after 396 from the autograph copy that Yāqūt saw.
  - Baalbaki gives "ca. 400/1010".
  - Haywood gives "not later than 398/1007".

  The stored year is defensible but is one side of a dispute. It matters only for panel order relative to Ibn Fāris (stored 1004).
- **Corrupted stored text.** Alh (entry 109) has "فك م" for "فكأنهم".
- **Merged and truncated entries.** `onOurSite` discloses them: 17 hamza merges and 9 repeated-heading merges, with xsA in both groups. Ayd is truncated.
