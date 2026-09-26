# al-Ṣiḥāḥ: independent verification, round 3 (2026-09-26)

Checked: `roots/frontend/src/content/dictionary-guides/guides/al-sihah.ts`, the version after revision r2.
I did not open `research-notes.md` or any `revision-*.md`. I read `verification-r2.md` only to see what round 2 flagged. Then I re-checked the whole essay myself.

Method. I fetched every Shamela page again with curl and read its printed-page header (ج/ص) and breadcrumb. I downloaded Haywood's OCR text (`12555_djvu.txt`) and Baalbaki's PDF. I fetched the Iranica articles (through Wayback), al-Mawsūʿa and Hawramani with curl. I read the stored entries with `_dict_guide_tool.py entry` and ran a direct read-only scan of `dictionary_entries`. I compared the stored text of kfr, Alh and rkE with ʿAṭṭār's Shamela text word by word (difflib, after removing vowel marks and footnote numbers). I checked the Qur'an references against the local verse API.

**Totals: 77 claims. 76 supported, 1 needs qualification, 0 unsupported.** The validator passes.

## Round-2 flags and the new claim

| Item | Now reads | Verdict |
|---|---|---|
| C70, asterisks (NQ in r2) | "…word for word, including that digital text's asterisks but not the editor's footnotes." | **Fixed.** The Shamela text has the asterisks: 23235/1597 "(إنَّا بكُلٍّ كافِرون) *"; /4402 opens "(*) ومنه قولنا"; /4404 opens "(*) وقد جاء". The stored text has them in the same places. The sentence no longer says where they come from. |
| Brief: ambiguous "Here" | "Back in al-Jawharī's entry, a line of poetry gets two readings…" | Fixed. |
| Brief: overlap of the counts | "…; one root is in both groups." | Fixed and supported (C77 below). |
| Brief: heading | "What he claimed" | Fixed. |
| NEW: "one root is in both groups" | onOurSite | **Supported.** My scan of the 866 displayed entries finds 17 whose first bracketed heading ends in ا and a later one ends in أ. It finds 9 with a repeated heading. xsA (entry 9982) is in both: [خسا] خساً أو زكاً / [خسا] حسوت المرق… / [خسأ] خسأت الكلب. |

**New finding in this round.** The "word for word" match (C69) is not quite exact. The stored أ ل ه entry has one garbled word: "فك م سموها", where ʿAṭṭār's Shamela text (23235/4404, vol. 6 p. 2224) reads "فكأنهم سموها". kfr (ids 1597–1600) and rkE (id 2418) match exactly. The difflib comparison shows only insertions on the Shamela side: the neighbouring entries and the footnotes.

## Sources opened (round 3)

| id | What I saw | OK? |
|---|---|---|
| jawhari-preface | shamela.ws/book/23235/50. Title "ج1 - ص33 … مقدمة المؤلف". Full preface: "أودعت هذا الكتاب ما صح عندي … على ترتيب لم أسبق إليه … في ثمانية وعشرين بابا، وكل باب منها ثمانية وعشرون فصلا … بعد تحصيلها بالعراق رواية، وإتقانها دراية، ومشافهتي بها العرب العاربة، في ديارهم بالبادية". | yes |
| muzhir | 6936/68–72 = vol. 1, pp. 74–78. Book card: al-Suyūṭī (d. 911), ed. Fuʾād ʿAlī Manṣūr, DKI, 1st ed. 1418/1998. | yes |
| iranica-farab | Wayback. "Article by Clifford Edmund Bosworth … Vol. IX, Fasc. 2, p. 208 … Published December 15, 1999". "The lexicographer Abū Naṣr Ḥammād Jawharī (d. 393/1003?) … was born in Fārāb". Fārāb is "on the middle Syr Darya … in Transoxania". | yes |
| yaqut | 9788/656–659 = vol. 2, pp. 656–659. Book card: ed. Iḥsān ʿAbbās, Dār al-Gharb al-Islāmī, 1414/1993. | yes |
| dhahabi | 10906/10491 and 10493 = vol. 17, pp. 80 and 82. Book card: vol. 17 ed. al-ʿIrqsūsī; al-Risāla, 3rd ed. 1405/1985. p. 82 quotes al-Qifṭī: "سنة ثلاث وتسعين وثلاث مائة … وقيل: مات في حدود سنة أربع مائة". | yes |
| haywood | archive.org in.gov.ignca.12555, the OCR text. Ch. 6 "The Rhyme Arrangement: the 'Sahah' of al-Jauhari", pp. 68–76. I placed the page breaks from the printed numbers 69–75 in the OCR. | yes |
| baalbaki-2019 | AUB PDF, *JAS* 6 (2019) 185–208. The continuation of n. 1 on p. 186 reads: "al-Jawharī's (d. ca. 400/1010) al-Ṣiḥāḥ". | yes |
| attar-ed | 23235 book card: ed. ʿAṭṭār, Dār al-ʿIlm lil-Malāyīn, 4th printing 1407/1987, 6 vols. kfr: ids 1597–1598 = vol. 2 p. 807 (breadcrumb باب الراء › فصل الكاف), ids 1599–1600 = p. 808. rkE: id 2418 = vol. 3 p. 1222. Alh: ids 4402–4404 = vol. 6 pp. 2223–2224. | yes |
| attar-essay | 23235/12 has the heading "[الجوهري مبتكر منهج الصحاح:]" (vol. 1 p. 12). /20–22 (digital headers "ج1 - ص1–3") contain "وإن كان مسبوقا في الزمن والتأليف من قبل البندنيجي"; "أما دعواه … أن البندنيجي سبقه فمردودة"; "ونحن لا نشك في أن الفارابي يعد واضع بعض أساس منهج الصحاح"; and "فالامام الجوهري مبتكر منهجه ابتكارا … وإن ظهر … أن «كتاب التقفية» تقدم معجم الصحاح بزمن غير يسير". | yes |
| lisan-intro | 1687/7–8. Dār Ṣādir, 3rd printing 1414. p. 7: "فتداولوه وتناقلوه … قد صحّف وحرّف … فأتيح له الشيخ أبو محمد بن بري فتتبع ما فيه … ورتبته ترتيب [الصحاح] في الأبواب والفصول". p. 8: "هذه الأصول الخمسة". | yes |
| iranica-dict | Wayback. "Vol. VII, Fasc. 4, pp. 387-397 Published December 15, 1995". Part i is signed (ʿALĪ AŠRAF ṢĀDEQĪ): "Moḥammad Naḵjavānī's Ṣehāḥ al-fors (… comp. 728/1328) … arranged on the model of the Arabic Ṣeḥāḥ al-loḡa by Jawharī Fārābī". | yes |
| mawsua | arab-ency.com.sy/details/5188. Signed شوقي المعري. Vol. 7, 2003 printing, p. 822. It has "وفي سنة وفاته خلاف"; "وهذا الخبر يناقض … كما يستدل منه على أن وفاة الجوهري كانت بعد سنة 396هـ"; "حواشي عبد الله بن برّي (ت582هـ)"; and "مختار الصحاح" among the abridgements. | yes |
| hawramani | Collection page, HTTP 200. Title "Ismāʿīl bin Ḥammād al-Jawharī, Tāj al-Lugha wa Ṣiḥāḥ al-ʿArabīya". It names no edition: no match for عطار, تحقيق, طبعة or "edition". It gives "d. 1003 CE / 393 AH". | yes |

Every listed source is cited in the essay, and every URL opens the stated work.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim | V | Evidence |
|---|---|---|---|
| C1 | Title al-Ṣiḥāḥ / الصحاح | S | Shamela book title; Muzhir 1:74 |
| C2 | Full title Tāj al-Lugha wa-Ṣiḥāḥ al-ʿArabiyya, glossed "The Crown of Language and the Sound Words of Arabic" | S | Preface heading (23235/50); Haywood p. 70 ("The crown of language and the correct of Arabic") |
| C3 | Author Abū Naṣr Ismāʿīl ibn Ḥammād al-Jawharī; al-Jawharī / الجوهري | S | Preface: "قال الشيخ أبو نصر إسماعيل بن حماد الجوهري" |
| C4 | Period: d. 393 AH (1002–3) or c. 400 (c. 1010); disputed | S | Dhahabī 17:82; Baalbaki p. 186 n. 1; Mawsūʿa "في سنة وفاته خلاف" |
| C5 | Kind "Rhyme-ordered general dictionary"; sortYear 1003 | S | Haywood ch. 6 title; Baalbaki n. 1 "general lexica" |
| C6 | Summary: compact general dictionary from about 1000, filed by last letter | S | Preface; Haywood pp. 71, 74 |
| C7 | Summary: set out to include only what he judged sound | S | Preface "ما صح عندي" |
| C8 | Summary: absorbed and corrected by later dictionaries such as Lisān | S | Lisān intro 1:7–8 (Ṣiḥāḥ and Ibn Barrī's corrections among the five uṣūl); Muzhir 1:78 (Fīrūzābādī's corrections) |
| C9 | Lede: the preface is only a few lines long | S | 23235/50, one paragraph; Haywood p. 71 "remarkably short" |
| C10 | Lede: two claims define it: sound "in my judgement", and a new arrangement | S | Preface; Haywood p. 71 "makes two claims: to have included only correct words, and to have initiated a new arrangement" |
| C11 | Lede: entries name authorities, show a grammarian's interest in how words are built, and leave much out | S | Entries 155 and 109; Haywood p. 74 ("deep interest in grammar, syntax, and derivation"), p. 75 ("had omitted much") |
| C12 | Preface quotation: Arabic and translation | S | 23235/50. The Arabic matches and the ellipses mark omitted text. The translation is accurate. |
| C13 | "The standard is personal: ʿindī" | S | Reading of "ما صح عندي" (framed as interpretation) |
| C14 | Al-Suyūṭī (d. 911/1505): first to confine himself to sound material, "and for this he named his book al-Ṣiḥāḥ" | S | Muzhir 1:74 "وأولُ مِن التزمَ الصحيح مقتصرا عليه … الجَوْهَري ولهذا سمَّى كتابه بالصحاح" |
| C15 | Also voiced al-Ṣaḥāḥ | S | Muzhir 1:75 (al-Tibrīzī: "ويقال: الصَّحاح بالفتح") |
| C16 | Not to be confused with al-Zabīdī's much later Tāj al-ʿArūs | S | Site data (al-Zabīdī stored 1790); separate guide |
| C17 | Born in Fārāb in Transoxiana | S | Iranica "Fārāb"; Haywood p. 69. Yāqūt 2:656 says only "أصله … من فاراب". |
| C18 | Studied Arabic in Iraq with Abū ʿAlī al-Fārisī and Abū Saʿīd al-Sīrāfī | S | Yāqūt 2:656 "دخل العراق فقرأ علم العربية على … أبي علي الفارسي وأبي سعيد السيرافي" |
| C19 | Travelled among the tribes of Rabīʿa and Muḍar | S | Yāqūt 2:656 "طوّف بلاد ربيعة ومضر"; Mawsūʿa "طوَّف في قبائل ربيعة، ومُضَر" |
| C20 | Settled in Nishapur, teaching and copying books | S | Yāqūt 2:656 "التدريس والتأليف وتعليم الخط وكتابة المصاحف والدفاتر" |
| C21 | Died 393 (1002–3) or around 400 (c. 1010) | S | Dhahabī 17:82; Baalbaki p. 186 n. 1 |
| C22 | Al-Mujāshiʿī's story (via Yāqūt): al-Bīshakī, for whom the book was written, heard it only as far as ḍād; a pupil fair-copied the rest and "made gross errors in several places" | S | Yāqūt 2:658 "صنف «كتاب الصحاح» للأستاذ أبي منصور … البيشكي، وسمعه منه إلى باب الضاد … فبيّضه أبو إسحاق إبراهيم بن صالح الوراق … فغلط فيه في عدة مواضع غلطا فاحشا" |
| C23 | Haywood: "a pinch of salt" | S | Haywood p. 69 |
| C24 | Yāqūt saw a copy in al-Jawharī's hand dated 396 (1005–6) | S | Yāqūt 2:658–659 "وقفت على نسخة بالصحاح بخطّ الجوهري بدمشق … كتبها في سنة ست وتسعين وثلاثمائة" |
| C25 | A modern reference: this contradicts the story and puts his death after 396 | S | Mawsūʿa p. 822 (quoted above) |
| C26 | Al-Tibrīzī: some taṣḥīf is the author's own | S | Muzhir 1:75 "فيه تصحيفٌ لا يُشَكُّ في أنه من المصنِّف لا من الناسخ" |
| C27 | Filed by last letter, in 28 chapters (bāb) | S | Preface "في ثمانية وعشرين بابا"; Haywood p. 71 |
| C28 | Sections (faṣl) by first letter | S | Preface ("ثمانية وعشرون فصلا"); Haywood p. 71 "according to the first, and then the intermediate radicals" |
| C29 | Kufr: bāb al-rāʾ, faṣl al-kāf, vol. 2 p. 807 | S | 23235/1598: breadcrumb باب الراء › فصل الكاف; header ج2 ص807 |
| C30 | The novelty is disputed; the maternal uncle al-Fārābī used final-letter order inside the subsections of Dīwān al-Adab | S | Haywood p. 69 "the rhyme order was only used in subsections"; Yāqūt 2:656 "ابن أخت أبي إسحاق الفارابي صاحب «ديوان الأدب»" |
| C31 | ʿAṭṭār grants the uncle "part of the foundation" and al-Bandanījī's rhyme book prior date, still calls al-Jawharī the originator, and rejects al-Jāsir | S | attar-essay 23235/20–22 (quoted above) |
| C32 | Lisān arranged "in the order of the Ṣiḥāḥ" | S | Lisān intro 1:7 |
| C33 | A 14th-century Persian dictionary was modelled on it | S | Iranica "Dictionaries i": Ṣeḥāḥ al-fors, 728/1328 |
| C34 | On our site each entry stands alone, so the arrangement is invisible | S | Site behaviour (one entry per root page) |
| C35 | Vowels are spelled out (bi-l-fatḥ, bi-l-kasr) or shown by a model word after mithl | S | Haywood p. 74; entry 155 "بالفتح", "بالكسر", "مثل جائع وجياع" |
| C36 | A named authority marks a report; unattributed sentences are presented as his own | S | The guide's reading advice, not cited; it fits entries 155 and 109 |
| C37 | Haywood: his definitions often coincide with al-ʿAyn's | S | Haywood p. 74 "(often coinciding with those of the 'Ain')" |
| C38 | The kfr entry opens with the religious senses, then turns to covering | S | Entry 155 |
| C39 | kfr excerpt 1 and its translation | S | Entry 155 = Shamela 2:807 |
| C40 | "Denial" is illustrated by Q 28:48 and Q 17:99 | S | Entry 155; verse texts checked (17:99 is the only verse with "فأبى الظالمون إلا كفورا") |
| C41 | "Covering" is illustrated by a line recited by al-Aṣmaʿī | S | Entry 155 "وأنشد الاصمعي … غير رماد مكفور" |
| C42 | Further senses: village, grave, dark of night, sea, great river, the farmer "because he covers the seed with soil" | S | Entry 155 |
| C43 | Partway through, the link between the two groups appears in Ibn al-Sikkīt's name | S | Entry 155 |
| C44 | kfr excerpt 2 and its translation | S | Entry 155 |
| C45 | Ibn Fāris's excerpt and translation; covering as the governing principle, in his own voice | S | Entry 163 |
| C46 | Ibn Fāris unifies (the truth is covered); al-Jawharī lists, and Ibn al-Sikkīt derives the word from covering God's favour | S | Entries 163 and 155 |
| C47 | Ibn Fāris cites Q 57:20 for kuffār = farmers; al-Jawharī gives the sense without the verse | S | Entry 163 "{أعجب الكفار نباته} [الحديد: 20]"; entry 155 "والكُفَّارُ: الزرّاعُ" |
| C48 | In al-Jawharī's entry, the poetry line gets two readings (sea/sunset, or night) | S | Entry 155 "يعني الشمس أنها بدأت في المغيب. ويحتمل أن يكون أراد الليلَ" |
| C49 | Law and doctrine terms: the qibla maxim; kaffāra (Q 5:89); takfīr of sins likened to iḥbāṭ; no witness quoted | S | Entry 155; Q 5:89 "فكفارته … ذلك كفارة أيمانكم" |
| C50 | Ibn Barrī d. 582 AH | S | Mawsūʿa "(ت582هـ)" |
| C51 | Ibn Barrī wrote corrective notes on the book | S | Muzhir 1:76 "الحواشيَ على الصِّحاح"; Lisān 1:7; Mawsūʿa |
| C52 | Ibn Barrī: "the most grammatical of the lexicographers" | S | Muzhir 1:75 "الجوهري أَنْحَى اللغويين" |
| C53 | Alh: alaha = worshipped; Ibn ʿAbbās's reading at Q 7:127 | S | Entry 109; Q 7:127 "ويذرك وءالهتك" |
| C54 | Alh excerpt and translation | S | Entry 109 = Shamela 6:2223 |
| C55 | He states his view, reports Abū ʿAlī's opposite view at length and without reply, and adds Sībawayh's alternative; nothing is resolved | S | Entry 109 "وسمعت أبا على النحوي يقول … وجوز سيبويه أن يكون أصله لاها" |
| C56 | Ibn Barrī's reply survives in Lisān; excerpt and translation | S | Lisān Alh, entry 111 (displayed) |
| C57 | "Idols" excerpt and translation | S | Entry 109 = Shamela 6:2224 (id 4404) |
| C58 | The rkE excerpt is the whole entry; no witness and no verse | S | Entry 5785 = Shamela 3:1222 |
| C59 | Ibn Manẓūr: "passed it from hand to hand"; it had misreadings that Ibn Barrī traced | S | Lisān intro 1:7 |
| C60 | Al-Ṣaghānī's Takmila, a completion of what it missed | S | Muzhir 1:76 |
| C61 | Fīrūzābādī: "two-thirds of the language or more"; he singled it out because it was widely used and teachers relied on it | S | Muzhir 1:77–78 "فاته ثلثا اللغة أو أكثر … لِتَدَاوُله واشتهارِه … واعتماد المدرسين على نُقُوله" |
| C62 | Lisān used it, with Ibn Barrī's notes, as a source | S | Lisān intro 1:7–8 |
| C63 | On our site al-Jawharī is often named inside Lisān and Tāj | S | My count: "الجوهري" appears in 801 of 1,452 displayed Lisān entries and 377 of 1,600 displayed Tāj entries |
| C64 | Lisān kfr repeats "or he may have meant the night" and credits al-Jawharī | S | Lisān kfr (id 158) "قال الجوهري: ويحتمل أن يكون أراد الليل" |
| C65 | Mukhtār al-Ṣiḥāḥ is an abridgement | S | Haywood p. 75; Mawsūʿa |
| C66 | The date belongs to the compilation, not the usages; silence proves nothing; the verse must be weighed | S | Methodological framing, consistent with the brief |
| C67 | 866 roots displayed | S | Scan: 866 approved and visible (of 1,470 rows) |
| C68 | Hawramani names no edition | S | Collection page |
| C69 | Compared entries (Alh, kfr, rkE) match ʿAṭṭār's Shamela text "word for word", without the footnotes | **NQ** | kfr and rkE are exact. Alh has one garbled word in our copy: "فك م سموها" against Shamela "فكأنهم سموها" (23235/4404). Otherwise identical. |
| C70 | "including that digital text's asterisks" | S | Asterisks at 23235/1597, /4402 and /4404 and in the stored text |
| C71 | Hamza often unwritten; vowel marks partial | S | Stored "لانه", "الاله", "الاصمعي", "الشئ" |
| C72 | 17 hamza-final roots open with the weak-letter root's entry; qrA opens with qarw, a wooden bowl | S | Scan: jyA, swA, nbA, qrA, mrA, brA, n$A, xTA, bwA, bdA, DwA, *rA, xsA, hyA, hnA, SbA, $TA. qrA "[قرا] القَرْوُ: قدحٌ من خشب" |
| C73 | Nine repeat their heading over a similar-looking root's passage; nZr opens with nāṭūr, vineyard keeper | S | Scan: nZr (نطر), xlf (خطف), jbl (جيل), rjf (رخف), lHq (لخقوق), brq (يرقان), xsA (حسا), Hlq (حلقن), Anf (أثف). nZr "[نظر] الناطر والناطور: حافظ الكرم" |
| C74 | A few are cut short; Ayd is two words | S | Ayd "[أيد] أبو زيد:". Amm, bwr and xfD also end on a colon. |
| C75 | Our English summary for kufr calls covering "the root sense"; al-Jawharī does not | S | kfr harmonized_en §3 "Kafr as covering — the root sense"; not in entry 155 |
| C76 | Bibliographic details in `sources` | S | Book cards, page headers and article headers as listed above |
| C77 | NEW: one root is in both groups | S | xsA, entry 9982 (see above) |

## Flagged items and fixes

1. **C69, `onOurSite`, "match … word for word" (needs qualification).** Our stored أ ل ه entry has one corrupted word: "فك م" where ʿAṭṭār's Shamela text (vol. 6 p. 2224, Shamela id 4404) has "فكأنهم". kfr and rkE match exactly. **Fix:** change "word for word" to "word for word (bar one garbled word in أ ل ه)". An alternative is "almost word for word". Either fix changes only `onOurSite`, not the lede and body word count.

## Brief issues (not factual)

- **suggestion: length.** The validator counts 1,101 words for lede and body, just over the "roughly 700–1,100" guide. This is acceptable, but a trim of a few words would bring it inside. "Brevity is the book's other face." could become "Brevity is its other face."
- I found none of the following: padding, rankings, generic praise, an encyclopedia-style biography, a forced "original root meaning" narrative, a bare root mention or an unlabeled translation. The r2 brief issues have all been addressed.

## URL problems

None. Every URL opens the stated work. The Iranica links are Wayback copies, and they load through curl.

## Validator

`node scripts/validate-dictionary-guides.mjs al-sihah` returns **ok**: 12 root links (9 distinct pairs), 7 excerpts, 1,101 words; 1/1 guides pass.

## Site-data issues

- **Date.** The stored death year 1003 (= 393 AH) follows al-Qifṭī (via al-Dhahabī), the Shamela card ("ت ٣٩٣هـ") and Hawramani. Other sources disagree. Al-Mawsūʿa says most sources give about 400 AH (it gives 1009 CE) and infers a death after 396. Baalbaki gives "ca. 400/1010", and Haywood gives "not later than 398/1007". The stored date is defensible but is one side of a dispute. It affects panel order only relative to Ibn Fāris (stored 1004).
- **Corrupted stored text.** Alh (entry 109) has "فك م" for "فكأنهم".
- **Merged and truncated entries** are disclosed in `onOurSite`. There are 17 hamza merges and 9 repeated-heading merges, with xsA in both. Ayd is truncated, and Amm, bwr and xfD also end on a colon.
