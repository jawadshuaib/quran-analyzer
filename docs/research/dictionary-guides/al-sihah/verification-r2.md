# al-Ṣiḥāḥ — independent verification, round 2 (2026-09-26)

Checked: `roots/frontend/src/content/dictionary-guides/guides/al-sihah.ts` (the version after revision r1).
I did not open `research-notes.md` or `revision-r1.md`. I read `verification-r1.md` only to find the items flagged in round 1.
All sources below were opened again in this round. Shamela pages were fetched with curl, and each page header (ج/ص) was read to confirm the volume and page. Stored entries were read with `_dict_guide_tool.py entry` and through a direct read-only scan of `dictionary_entries`.

**Totals: 76 claims. 75 supported, 1 needs qualification, 0 unsupported.** The validator passes.

## Round-1 flags: status

| r1 item | Now reads | Verdict |
|---|---|---|
| C8 "makes two promises" | "Among its claims, two define the book …" [preface p. 33][Haywood p. 71] | Fixed. Haywood p. 71 reads: "Al-Jauhari's modest preface makes two claims: to have included only correct words, and to have initiated a new arrangement." |
| C9 "hence its short title" in the lede | Removed from the lede. The body credits the naming to al-Suyūṭī [Muzhir 1:74–75]. | Fixed. Muzhir 1:74: "وأول من التزم الصحيح مقتصرا عليه … الجوهري ولهذا سمى كتابه بالصحاح". |
| C29 ʿAṭṭār and the uncle | ʿAṭṭār grants that the uncle laid "part of the foundation" and that al-Bandanījī came first, yet calls al-Jawharī the originator and rejects al-Jāsir. | Fixed and supported. Shamela 23235/20 (digital header "ج1 - ص1"): "وإن كان مسبوقا في الزمن والتأليف من قبل البندنيجي أو الفارابي … أما دعواه … أن البندنيجي سبقه فمردودة". /21: "ونحن لا نشك في أن الفارابي يعد واضع بعض أساس منهج الصحاح" (ʿAṭṭār quoting his own *Muqaddimat al-Ṣiḥāḥ*, pp. 80–81). /22: "فالامام الجوهري مبتكر منهجه ابتكارا … وإن ظهر … أن «كتاب التقفية» تقدم معجم الصحاح بزمن غير يسير". |
| C33 reading convention under a Haywood citation | The rule is now the guide's own advice, with no citation. Haywood p. 74 is cited only for the overlap with al-ʿAyn. | Fixed. Haywood p. 74: "succinct definitions, (often coinciding with those of the 'Ain')". |
| C35 al-Akhfash | Dropped. "'Denial' is illustrated by two Qur'anic phrases (Q 28:48 and Q 17:99)". | Fixed. Entry 155; checked against the verse texts. |
| C43 "set against iḥbāṭ" | "likened to iḥbāṭ" | Fixed. Entry 155: "والتَكْفيرُ في المعاصي، كالإحباطِ في الثوابِ". |
| C65 "nine" | Kept, with the mechanism now named: "repeat their heading over a similar-looking root's passage". | **Supported. Round 1's count of 8 was wrong.** My own scan (below) finds 9. The ninth is xsA, whose second [خسا] block is the entry for حسا ("حسوت المرق حسوا …"). |
| Must-fix: unlabeled translations | The preface attribution now reads "(translation for this guide, like every translation from Arabic on this page)". | Fixed. The label comes before every inline rendering from al-Muzhir, Yāqūt, Ibn Barrī, the Lisān introduction, Fīrūzābādī and ʿAṭṭār. |

## Sources opened (round 2)

| id | What I saw | OK? |
|---|---|---|
| jawhari-preface | shamela.ws/book/23235/50. Header "ج1 - ص33 … مقدمة المؤلف". Full preface read. | yes |
| muzhir | shamela.ws/book/6936/68–72 = vol. 1, pp. 74–78. Book card: ed. Fuʾād ʿAlī Manṣūr, DKI, 1st ed. 1418/1998. Al-Suyūṭī d. 911. | yes |
| iranica-farab | Wayback copy, via curl. "Article by Clifford Edmund Bosworth … Vol. IX, Fasc. 2, p. 208 … Published December 15, 1999". Text: "The lexicographer Abū Naṣr Ḥammād Jawharī (d. 393/1003?) … was born in Fārāb", on "the middle Syr Darya … in Transoxania". | yes |
| yaqut | shamela.ws/book/9788/656–660 = vol. 2, pp. 656–660. Book card: ed. Iḥsān ʿAbbās, Dār al-Gharb al-Islāmī, 1414/1993. | yes |
| dhahabi | shamela.ws/book/10906/10491–10493 = vol. 17, pp. 80–82. Book card: vol. 17 ed. al-ʿIrqsūsī; al-Risāla, 3rd ed. 1405/1985. p. 82: al-Qifṭī "سنة ثلاث وتسعين وثلاث مائة … وقيل: مات في حدود سنة أربع مائة". | yes |
| haywood | archive.org in.gov.ignca.12555, `12555_djvu.txt` downloaded fresh. Ch. 6, "The Rhyme Arrangement: the Sahah of al-Jauhari", pp. 68–76. Page breaks placed from the printed page numbers in the OCR. | yes |
| baalbaki-2019 | AUB PDF, 24 pp., *Journal of Abbasid Studies* 6 (2019) 185–208. n. 1 on p. 186: "al-Jawharī's (d. ca. 400/1010) al-Ṣiḥāḥ". | yes |
| attar-ed | shamela.ws/book/23235. Book card: تحقيق أحمد عبد الغفور عطار, Dār al-ʿIlm lil-Malāyīn, 4th printing 1407/1987, 6 vols. kfr: ids 1597/1598 = vol. 2, p. 807, and id 1600 = p. 808 (breadcrumb باب الراء › فصل الكاف). rkE: id 2418 = vol. 3, p. 1222. Alh: ids 4401–4403 = vol. 6, pp. 2223–2224. | yes |
| attar-essay | shamela.ws/book/23235/12–22. Heading "[الجوهري مبتكر منهج الصحاح:]". /12–19 carry headers vol. 1, pp. 12–19. /20–22 carry the digital headers "ج1 - ص1–3" under "مقدمة المؤلف", although the text is continuous with the essay. The citation's "Shāmila pages 12–22" describes this honestly. | yes |
| lisan-intro | shamela.ws/book/1687/7–8. Dār Ṣādir, 3rd printing 1414. p. 7: "فتداولوه وتناقلوه … قد صحّف وحرّف … فأتيح له الشيخ أبو محمد بن بري فتتبع ما فيه … ورتبته ترتيب [الصحاح] في الأبواب والفصول". p. 8: "هذه الأصول الخمسة". | yes |
| iranica-dict | Wayback copy, via curl. Vol. VII, Fasc. 4, pp. 387–397 (1995). Part i signed ʿALĪ AŠRAF ṢĀDEQĪ: "Moḥammad Naḵjavānī's Ṣehāḥ al-fors (… comp. 728/1328) … arranged on the model of the Arabic Ṣeḥāḥ al-loḡa by Jawharī Fārābī". | yes |
| mawsua | arab-ency.com.sy/details/5188. Signed شوقي المعري; vol. 7, 2003 printing, p. 822. It gives Ibn Barrī "(ت582هـ)" and the 396 passage quoted under C25. | yes |
| hawramani | Collection page, HTTP 200. It names no edition: no match for عطار, تحقيق, طبعة or "edition". It gives "d. 1003 CE / 393 AH". | yes |

Every listed source is used in the essay, and every URL opens the work it claims to be.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim | V | Evidence |
|---|---|---|---|
| C1 | Title al-Ṣiḥāḥ / الصحاح | S | Shamela book title; Muzhir 1:74 |
| C2 | Full title *Tāj al-Lugha wa-Ṣiḥāḥ al-ʿArabiyya*; gloss "Crown of Language and the Sound Words of Arabic" | S | Preface heading (23235/50); Haywood p. 70 ("The crown of language and the correct of Arabic") |
| C3 | Abū Naṣr Ismāʿīl ibn Ḥammād al-Jawharī | S | Preface: "قال الشيخ أبو نصر إسماعيل بن حماد الجوهري" |
| C4 | Period: d. 393 or c. 400; disputed | S | Dhahabī 17:82 (al-Qifṭī); Baalbaki p. 186 n. 1; Mawsūʿa ("وفي سنة وفاته خلاف") |
| C5 | Kind "Rhyme-ordered general dictionary"; sortYear 1003 | S | Haywood ch. 6 title; Baalbaki n. 1 ("general lexica") |
| C6 | Summary: compact, c. 1000, filed by last letter | S | Preface; Haywood p. 71 |
| C7 | Summary: set out to include only what he judged sound | S | Preface "ما صح عندي"; Haywood p. 71 "only correct words" |
| C8 | Summary: absorbed, and corrected, by later dictionaries such as Lisān | S | Lisān intro 1:7–8 (Ṣiḥāḥ plus Ibn Barrī's corrections among the five uṣūl) |
| C9 | Lede: the preface is only a few lines long | S | 23235/50 (one paragraph); Haywood p. 71 "remarkably short" |
| C10 | Lede: among its claims, two define it: sound "in my judgement", and a new arrangement | S | Preface p. 33; Haywood p. 71 "makes two claims" |
| C11 | Lede: entries name authorities, show a grammarian's interest, leave much out | S | Entries 155 and 109; Haywood pp. 74–75 ("deep interest in grammar"; "had omitted much") |
| C12 | Preface quotation, Arabic and translation | S | 23235/50. The Arabic matches and the ellipses cover omitted text. The translation is accurate. |
| C13 | "The standard is personal: *ʿindī*" | S | Reading of "ما صح عندي" (interpretation, clearly framed) |
| C14 | Al-Suyūṭī (d. 911/1505): the first to confine himself to sound material, "and for this he named his book al-Ṣiḥāḥ" | S | Muzhir 1:74; book card (d. 911) |
| C15 | Also voiced al-Ṣaḥāḥ | S | Muzhir 1:75 (al-Tibrīzī: "ويقال: الصَّحاح بالفتح") |
| C16 | Not to be confused with al-Zabīdī's much later Tāj al-ʿArūs | S | Site data (al-Zabīdī 1790); separate guide |
| C17 | Born in Fārāb in Transoxiana | S | Iranica "Fārāb"; Haywood p. 69. Yāqūt 2:656 says only "أصله … من فاراب". |
| C18 | Studied Arabic in Iraq with Abū ʿAlī al-Fārisī and Abū Saʿīd al-Sīrāfī | S | Yāqūt 2:656 "دخل العراق فقرأ علم العربية على … أبي علي الفارسي وأبي سعيد السيرافي" |
| C19 | Travelled among the tribes of Rabīʿa and Muḍar | S | Yāqūt 2:656 "وطوّف بلاد ربيعة ومضر"; Mawsūʿa "طوَّف في قبائل ربيعة، ومُضَر"; Haywood p. 69 "the lands of the Mudar and Rabi'a tribes" |
| C20 | Settled in Nishapur, teaching and copying books | S | Yāqūt 2:656 "التدريس والتأليف وتعليم الخط وكتابة المصاحف والدفاتر" |
| C21 | He died in 393 (1002–3) or around 400 (c. 1010) | S | Dhahabī 17:82; Baalbaki p. 186 n. 1 |
| C22 | Story from al-Mujāshiʿī quoted by Yāqūt: al-Bīshakī, for whom the book was written, heard it only as far as ḍād; a pupil fair-copied the rest and "made gross errors in several places" | S | Yāqūt 2:658 "صنف «كتاب الصحاح» للأستاذ أبي منصور … البيشكي، وسمعه منه إلى باب الضاد … فبيّضه أبو إسحاق إبراهيم بن صالح الوراق تلميذ الجوهري … فغلط فيه في عدة مواضع غلطا فاحشا" |
| C23 | Haywood suggests "a pinch of salt" | S | Haywood p. 69 |
| C24 | Yāqūt himself saw an autograph copy dated 396 (1005–6 CE) | S | Yāqūt 2:658–659 "وقفت على نسخة بالصحاح بخطّ الجوهري بدمشق … كتبها في سنة ست وتسعين وثلاثمائة" |
| C25 | A modern reference notes that this contradicts the story and puts his death after 396 | S | Mawsūʿa p. 822 "وهذا الخبر يناقض ما ذكر من أن الجوهري أتم كتابة الصحاح حتى حرف الضاد، كما يستدل منه على أن وفاة الجوهري كانت بعد سنة 396هـ" |
| C26 | Al-Tibrīzī judged that some taṣḥīf was the author's own | S | Muzhir 1:75 "فيه تصحيف لا يشك في أنه من المصنف لا من الناسخ" |
| C27 | Roots filed by last letter, in 28 chapters (bāb) | S | Preface "في ثمانية وعشرين بابا"; Haywood p. 71 |
| C28 | Chapters divided into sections (faṣl) by first letter | S | Haywood p. 71 "Within each chapter, roots are entered according to the first, and then the intermediate radicals" |
| C29 | Kufr sits in bāb al-rāʾ, faṣl al-kāf, vol. 2 p. 807 | S | Shamela 23235/1598: breadcrumb باب الراء › فصل الكاف; header ج2 ص807 |
| C30 | How new this was is disputed; his maternal uncle al-Fārābī used final-letter order inside the subsections of *Dīwān al-Adab* | S | Haywood p. 69 ("studied under his maternal uncle … the rhyme order was only used in subsections"); Yāqūt 2:656 "ابن أخت أبي إسحاق الفارابي صاحب «ديوان الأدب»"; attar-essay (al-Jāsir, al-ʿAṭiyya, Krenkow) |
| C31 | ʿAṭṭār grants "part of the foundation" to the uncle and prior date to al-Bandanījī, still calls al-Jawharī the originator, and rejects al-Jāsir | S | Shamela 23235/20–22 (quoted above) |
| C32 | Lisān arranged "in the order of the Ṣiḥāḥ" | S | Lisān intro 1:7 |
| C33 | A 14th-century Persian dictionary was modelled on it | S | Iranica "Dictionaries i": Ṣeḥāḥ al-fors, 728/1328 |
| C34 | On our site each entry stands alone under its root, so the arrangement is not visible | S | Site behaviour: one entry per root page |
| C35 | Vowels spelled out (bi-l-fatḥ, bi-l-kasr) or shown by a model word after *mithl* | S | Haywood p. 74; entry 155 "بالفتح", "بالكسر", "مثل جائع وجياع", "مثل برد وبرود" |
| C36 | A named authority marks a report; unattributed sentences are presented as his own (the guide's advice) | S | Presented as advice, not cited; consistent with entries 155 and 109 |
| C37 | Haywood: his definitions often coincide with al-ʿAyn's | S | Haywood p. 74 |
| C38 | Kfr entry opens with religious senses, then covering | S | Entry 155 (unbelief → ingratitude → "والكفر بالفتح: التغطية") |
| C39 | Kfr excerpt 1 and translation | S | Entry 155 = Shamela 2:807. Translation accurate. |
| C40 | "Denial" illustrated by Q 28:48 and Q 17:99 | S | Entry 155 "(إنا بكل كافرون) … أي جاحدون … (فأبى الظالمون إلا كفورا)"; checked against the verse texts of 28:48 and 17:99 |
| C41 | "Covering" illustrated by a verse recited by al-Aṣmaʿī | S | Entry 155 "وأنشد الاصمعي: … غير رماد مكفور" |
| C42 | Further senses: village, grave, dark of night, sea, great river, farmer "because he covers the seed with soil" | S | Entry 155 |
| C43 | The link between the two groups appears partway, in Ibn al-Sikkīt's name | S | Entry 155 |
| C44 | Excerpt 2 and translation | S | Entry 155. Translation accurate. |
| C45 | Ibn Fāris makes covering the governing principle, in his own voice; excerpt and translation | S | Entry 163 "أصل صحيح يدل على معنى واحد، وهو الستر والتغطية … والكفر: ضد الإيمان، سمي لأنه تغطية الحق". Translation accurate. |
| C46 | Ibn Fāris unifies (the truth is what is covered); al-Jawharī lists and lets Ibn al-Sikkīt derive the word from covering God's favour | S | Entries 163 and 155 |
| C47 | Ibn Fāris cites Q 57:20 for *kuffār* as farmers; al-Jawharī gives the sense without the verse | S | Entry 163 "{أعجب الكفار نباته} [الحديد: 20]"; entry 155 "والكفار: الزراع" with no verse |
| C48 | A poetry line gets two readings: sea (sunset) or night | S | Entry 155 "يعني الشمس أنها بدأت في المغيب. ويحتمل أن يكون أراد الليل" |
| C49 | Law and doctrine terms: the qibla maxim; kaffāra (Q 5:89 uses the word); takfīr of sins likened to iḥbāṭ; no witness quoted | S | Entry 155 (Shamela 2:808); Q 5:89 "فكفارته … ذلك كفارة أيمانكم" |
| C50 | Ibn Barrī d. 582 AH | S | Mawsūʿa |
| C51 | Ibn Barrī wrote corrective notes on the book | S | Muzhir 1:76 "الحواشي على الصحاح"; Lisān 1:7 "مخرجا لسقطاته، مؤرخا لغلطاته" |
| C52 | Ibn Barrī: "the most grammatical of the lexicographers" | S | Muzhir 1:75 "وقال ابن برِّي: الجوهري أَنْحَى اللغويين" |
| C53 | Alh: alaha glossed "he worshipped"; Ibn ʿAbbās's reading "and your worship" at Q 7:127 | S | Entry 109; Q 7:127 "ويذرك وآلهتك" |
| C54 | Alh excerpt (Allāh < ilāh; hamza dropped; the al-ilāh argument; Abū ʿAlī) and translation | S | Entry 109 = Shamela 6:2223. Translation accurate. |
| C55 | He states his view, reports Abū ʿAlī's opposite view at length and without reply, and adds Sībawayh's alternative | S | Entry 109 "وسمعت أبا على النحوي يقول … وجوز سيبويه أن يكون أصله لاها" |
| C56 | Ibn Barrī's reply survives in Lisān; excerpt and translation | S | Lisān Alh (displayed): "قال ابن بري عند قول الجوهري … هذا رد على أبي علي الفارسي … ولا يلزمه …". Translation accurate. |
| C57 | "Idols" excerpt and translation | S | Entry 109 |
| C58 | rkE is the whole entry; no witness, no verse | S | Entry 5785 = Shamela 3:1222 (the editor's footnote is not part of the entry) |
| C59 | Ibn Manẓūr: people "passed it from hand to hand"; it had misreadings that Ibn Barrī traced | S | Lisān intro 1:7 |
| C60 | Al-Ṣaghānī's *Takmila*, a completion of what it missed | S | Muzhir 1:76 "التكملة على الصحاح ذكر فيها ما فاته من اللغة" |
| C61 | Fīrūzābādī: "two-thirds of the language or more"; singled it out because it was widely used and teachers relied on it | S | Muzhir 1:77–78 "فاته ثلثا اللغة أو أكثر … لتداوله واشتهاره … واعتماد المدرسين على نقوله" |
| C62 | Lisān used it, with Ibn Barrī's notes, as a source | S | Lisān intro 1:7–8 |
| C63 | On our site you often meet al-Jawharī by name inside Lisān and Tāj | S | grep "الجوهري": 802 of 1,452 displayed Lisān entries; 1,157 of 1,600 displayed Tāj entries |
| C64 | Lisān kfr repeats "or he may have meant the night" and credits al-Jawharī | S | Lisān kfr (id 158) "قال الجوهري: ويحتمل أن يكون أراد الليل" |
| C65 | Mukhtār al-Ṣiḥāḥ is an abridgement | S | Haywood p. 75; Mawsūʿa ("من أشهر الكتب التي اختصرته «مختار الصحاح»") |
| C66 | The date belongs to the compilation, not the usages; silence proves nothing; the verse must be weighed | S | Methodological framing, consistent with the brief |
| C67 | 866 roots displayed | S | `_dict_guide_tool.py dicts`; direct scan (866 rows) |
| C68 | Hawramani names no edition | S | Collection page |
| C69 | Compared entries (Alh, kfr, rkE) match ʿAṭṭār's Shamela text word for word, without the editor's footnotes | S | Shamela ids 1597–1600, 2418, 4401–4403 compared: same wording; footnote markers (١)(٢) and footnotes absent from the stored text |
| C70 | "stray asterisks from the digital text included" | **NQ** | The asterisks do appear in both texts ("(إنَّا بكُلٍّ كافِرون) *", "(*) ومنه قولنا"). "Stray … from the digital text" asserts they are digitisation artefacts rather than marks of the printed edition. I could not see the print, so that part is unverified. |
| C71 | Hamza often unwritten; vowel marks partial | S | Stored text "لانه", "الاله", "الاصمعي", "الشئ"; vowelling sporadic |
| C72 | 17 hamza-final roots open with the weak-letter root's entry; qrA opens with *qarw*, a wooden bowl | S | Scan: jyA, swA, nbA, qrA, mrA, brA, n$A, xTA, bwA, bdA, DwA, *rA, hyA, hnA, SbA, $TA, plus xsA (opens [خسا] "خساً أو زكاً") = 17. qrA "[قرا] القَرْوُ: قدحٌ من خشب" |
| C73 | Nine repeat their heading over a similar-looking root's passage; nZr opens with *nāṭūr*, vineyard keeper | S | Scan for a repeated bracketed heading finds 9. nZr (نطر), xlf (خطف), jbl (جيل), rjf (رخف), lHq (لخقوق), brq (يرقان), xsA (حسا), Hlq (حلقن), Anf (أثف). I read each block. nZr "[نظر] الناطر والناطور: حافظ الكرم" |
| C74 | A few entries are cut short; Ayd is two words | S | Ayd = "[أيد] أبو زيد:". Amm, bwr and xfD also end on a colon. |
| C75 | Our English summary for kufr calls covering "the root sense"; al-Jawharī does not | S | kfr harmonized_en §3 "Kafr as covering — the root sense"; no such phrase in entry 155 |
| C76 | Bibliographic details in `sources` (editors, printings, volumes, pages, URLs) | S | Book cards and page headers as listed above |

## Flagged items and fixes

1. **C70, `onOurSite`, "stray asterisks from the digital text included" (needs qualification).** The asterisks do occur in both the stored text and the Shamela text. Calling them "stray" marks from the digital text is an unverified claim about their origin; they may come from the printed edition. **Fix:** replace with "including the asterisks that appear in that digital text", or "asterisks included". This does not change the word count.

## Brief issues (not factual)

- **suggestion: an ambiguous "Here".** "Here a line of poetry gets two readings …" follows directly on the Ibn Fāris comparison. Ibn Fāris's own entry also gives two readings of the same Thaʿlaba line ("مغيب الشمس" / "البحر"), so a reader could credit "or he may have meant the night" to the wrong dictionary. **Fix:** "Back in al-Jawharī's entry, a line of poetry gets two readings …".
- **suggestion: the defect counts overlap.** xsA is counted in both the "seventeen" and the "nine", so 25 distinct entries are affected, not 26. The sentence does not claim a total, so this is optional. For precision, add "(one, خسا, has both)" or leave as is.
- **suggestion: heading.** "What he promised" survives although the lede now says "claims". Consider "What he claimed". This is optional.
- The length is fine: lede + body 1,099 words (per the validator; at the ceiling), `onOurSite` about 142 words, summary 45 words, lede about 70 words.
- Found none of the following: padding, rankings, generic praise, an encyclopedia-style biography, a forced "original root meaning" narrative (the essay contrasts al-Jawharī's listing with Ibn Fāris's unifying and flags our own "root sense" framing), a bare root mention, or an unlabeled translation.

## URL problems

None. Every URL opens the stated work. WebFetch cannot reach the two Wayback (Iranica) links, but curl and browsers load them.

## Validator

`node scripts/validate-dictionary-guides.mjs al-sihah` → **ok**: 12 root links (9 distinct pairs), 7 excerpts, 1,099 words; 1/1 guides pass.

## Site-data issues

- **Date.** The stored death year 1003 (= 393 AH) follows al-Qifṭī (via al-Dhahabī), the Shamela book card ("ت ٣٩٣هـ") and Hawramani. Other sources disagree. Al-Mawsūʿa says most sources give about 400 (1009–10) and infers a death after 396 from Yāqūt's autograph; Baalbaki gives "ca. 400/1010"; Haywood gives "not later than 398/1007". The stored date is defensible but is one side of a dispute. It affects panel order only relative to Ibn Fāris (stored 1004).
- **Merged and truncated entries** (disclosed correctly in `onOurSite`). 17 hamza-final entries begin with the weak-letter root's entry. 9 entries repeat their heading over a neighbouring root's passage: nZr, xlf, jbl, rjf, lHq, brq, xsA, Hlq, Anf. xsA falls in both groups. Ayd is truncated to "أبو زيد:", and Amm, bwr and xfD also end on a colon.
