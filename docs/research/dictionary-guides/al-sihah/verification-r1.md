# al-Ṣiḥāḥ — independent verification, round 1 (2026-09-26)

Checked: `roots/frontend/src/content/dictionary-guides/guides/al-sihah.ts`.
The research notes and revision files were **not** opened. Every source below was opened and read by the verifier.
Shamela pages were read as raw HTML with curl. Each page header gives the printed volume and page, so page numbers were checked against it.

Totals: **68 claims. 61 supported, 7 need qualification, 0 unsupported.** The validator passes.

## Sources opened

| id | What I saw | Usable? |
|---|---|---|
| jawhari-preface | shamela.ws/book/23235/50. Header "ج1 - ص33 … مقدمة المؤلف". Preface full text read. | yes |
| muzhir | shamela.ws/book/6936/68–72. ed. Fuʾād ʿAlī Manṣūr, DKI 1998 (book card). Pages vol. 1, pp. 74–78. | yes |
| iranica-farab | archive copy opened with curl. Bosworth, Vol. IX Fasc. 2 p. 208. Says "The lexicographer … Jawharī (d. 393/1003?) … was born in Fārāb". Fārāb is "on the middle Syr Darya … in Transoxania". | yes (WebFetch cannot reach web.archive.org; curl can) |
| yaqut | shamela.ws/book/9788/656–660. ed. Iḥsān ʿAbbās, Dār al-Gharb 1993 (book card). | yes |
| dhahabi | shamela.ws/book/10906/10491–10493. Vol. 17 pp. 80–82; editor of vol. 17 is al-ʿIrqsūsī (book card). | yes |
| haywood | archive.org in.gov.ignca.12555. Full text (djvu.txt) read. Ch. 6 runs pp. 68–76. Page breaks were placed using the running heads. | yes |
| baalbaki-2019 | AUB PDF read. p. 186, n. 1 has "al-Jawharī's (d. ca. 400/1010) al-Ṣiḥāḥ". | yes |
| attar-ed | shamela.ws/book/23235. 4th printing 1987, Dār al-ʿIlm lil-Malāyīn (book card). Pages found by binary search on the page headers: kfr at ids 1597–1600 = vol. 2 pp. 807–808; rkE at id 2418 = vol. 3 p. 1222; Alh at ids 4402–4404 = vol. 6 pp. 2223–2224. | yes |
| attar-essay | shamela.ws/book/23235/12–19, "الجوهري مبتكر منهج الصحاح", vol. 1 pp. 12–19. | yes |
| lisan-intro | shamela.ws/book/1687/7–8. Dār Ṣādir 3rd printing 1414 (book card), vol. 1 pp. 7–8. | yes |
| iranica-dict | archive copy opened with curl. Vol. VII Fasc. 4 pp. 387–397. Says "Naḵjavānī's Ṣehāḥ al-fors (… comp. 728/1328) … arranged on the model of the Arabic Ṣeḥāḥ al-loḡa by Jawharī Fārābī". | yes |
| mawsua | arab-ency.com.sy/details/5188. Signed شوقي المعري, vol. 7 (2003) p. 822. Gives "حواشي عبد الله بن برّي (ت582هـ)". | yes |
| hawramani | Collection page returns HTTP 200. It names no edition: I searched for عطار / تحقيق / طبعة / edition and found no match. | yes |

No source is listed without being used, and every URL opens the work it claims to be.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Short title al-Ṣiḥāḥ / الصحاح | S | Shamela title "الصحاح تاج اللغة وصحاح العربية"; Muzhir 1:74 |
| C2 | Full title *Tāj al-Lugha wa-Ṣiḥāḥ al-ʿArabiyya*; gloss | S | Preface heading (23235/50); Haywood p. 70 "The crown of language and the correct of Arabic" |
| C3 | Author Abū Naṣr Ismāʿīl ibn Ḥammād al-Jawharī | S | Preface: "قال الشيخ أبو نصر إسماعيل بن حماد الجوهري" |
| C4 | Period: d. 393 or c. 400, disputed | S | Dhahabī 17:82 (al-Qifṭī 393; "وقيل … في حدود سنة أربعمائة"); Baalbaki p. 186 n. 1; Mawsūʿa ("وفي سنة وفاته خلاف") |
| C5 | Kind: rhyme-ordered general dictionary | S | Haywood ch. 6 title; Baalbaki n. 1 ("general lexica") |
| C6 | Summary: compact, c. 1000, last-letter order, only what he judged sound, absorbed and corrected by Lisān | S | Preface; Lisān intro p. 7 |
| C7 | Lede: the preface is only a few lines long | S | Preface p. 33 (one paragraph); Haywood p. 71 "remarkably short" |
| C8 | Lede: the preface "makes two promises" | **NQ** | Haywood p. 71 reads it as "two claims", but the preface also claims "تهذيب لم أغلب عليه" (a refinement no one has bettered). The guide cites only the preface. |
| C9 | Lede: "(hence its short title …)" cited to the preface | **NQ** | The preface does not explain the name. That explanation is al-Suyūṭī's: "ولهذا سمى كتابه بالصحاح" (Muzhir 1:74). |
| C10 | Lede: entries name their authorities, show a grammarian's interest, and filter out much | S | Haywood pp. 74–75; kfr and Alh entries |
| C11 | Preface quotation: Arabic and translation | S | 23235/50: the Arabic matches, and the ellipses are honest. Translation checked and accurate. |
| C12 | Al-Suyūṭī: first to confine himself to sound material, and named the book for it | S | Muzhir 1:74 "وأول من التزم الصحيح مقتصرا عليه … ولهذا سمى كتابه بالصحاح" |
| C13 | Also voiced al-Ṣaḥāḥ | S | Muzhir 1:75 (al-Tibrīzī) |
| C14 | Not to be confused with al-Zabīdī's later Tāj al-ʿArūs | S | Registry and site data (al-Zabīdī stored as 1790) |
| C15 | Born in Fārāb in Transoxiana | S | Iranica "was born in Fārāb", "in Transoxania"; Haywood p. 69 "born in Farab … in Transoxiana". Note: Yāqūt p. 656 only says "أصله … من فاراب". |
| C16 | Studied Arabic in Iraq with al-Fārisī and al-Sīrāfī | S | Yāqūt 2:656 |
| C17 | Travelled among Rabīʿa and Muḍar | S | Yāqūt 2:656 "وطوّف بلاد ربيعة ومضر" |
| C18 | Settled in Nishapur, teaching and copying | S | Yāqūt 2:656 "التدريس والتأليف وتعليم الخط وكتابة المصاحف والدفاتر" |
| C19 | Al-Qifṭī gave 393 and noted "around 400" | S | Dhahabī 17:82 |
| C20 | Yāqūt saw an autograph copy dated 396 | S | Yāqūt 2:658–659 "نسخة بالصحاح بخط الجوهري … سنة ست وتسعين وثلاثمائة" |
| C21 | A recent study gives "ca. 400/1010" | S | Baalbaki 2019 p. 186 n. 1 |
| C22 | Story: book read only as far as ḍād; the pupil who fair-copied the rest "made gross errors in several places" | S | Yāqūt 2:658, quoting al-Mujāshiʿī: "سمعه منه إلى باب الضاد … فبيّضه … فغلط فيه في عدة مواضع غلطا فاحشا". The listener was al-Bīshakī, for whom the book was written; "a student" is a loose gloss. |
| C23 | Haywood: "a pinch of salt" | S | Haywood p. 69 |
| C24 | Al-Tibrīzī judged some taṣḥīf to be the author's own | S | Muzhir 1:75 "فيه تصحيف لا يشك في أنه من المصنف لا من الناسخ" |
| C25 | Filed by last letter, in 28 chapters | S | Preface "في ثمانية وعشرين بابا"; Haywood p. 71 |
| C26 | Sections (faṣl) by first letter | S | Haywood p. 71; preface |
| C27 | Kufr sits in bāb al-rāʾ, faṣl al-kāf, vol. 2 p. 807 | S | Shamela id 1597, breadcrumb "باب الراء: فصل الكاف [كفر]", ج2 ص807 |
| C28 | Uncle al-Fārābī used final-letter order in the subsections of Dīwān al-Adab | S | Haywood p. 69 "the rhyme order was only used in subsections" |
| C29 | ʿAṭṭār grants the uncle "some groundwork" and rejects al-Jāsir's case for al-Bandanījī | **NQ** | The rejection of al-Jāsir is supported (attar-essay). On al-Fārābī, ʿAṭṭār only says that a claim for him "لكان في دعواه نظر" (would be open to consideration or question). He also concedes al-Jawharī may have been "مسبوقا في الزمن والتأليف من قبل البندنيجي أو الفارابي" but still calls him the originator. "Granting the uncle some groundwork" is not his wording. |
| C30 | Lisān arranged "in the order of the Ṣiḥāḥ" | S | Lisān 1:7 "ورتبته ترتيب [الصحاح] في الأبواب والفصول" |
| C31 | A 14th-century Persian dictionary was modelled on it | S | Iranica "Dictionaries": Ṣeḥāḥ al-fors, 728/1328 |
| C32 | Vowels spelled out in words (bi-l-fatḥ, bi-l-kasr) or shown by a model word (mithl) | S | Haywood p. 74 (spelled-out vowelling, model words); entries show "بالفتح", "بالكسر", "مثل برد وبرود" |
| C33 | "Authorities are named where they speak; unattributed sentences are in al-Jawharī's voice, though they may draw silently on older books [haywood p. 74]" | **NQ** | Haywood p. 74 says only that definitions are "often coinciding with those of the ʿAin". He states no reading convention. The first half is the guide's own advice presented under a citation. |
| C34 | Kfr opens with the religious senses, then covering; excerpt 1 | S | Entry 155 (matches Shamela 2:807). Translation accurate. |
| C35 | "Denial" is supported by Q 28:48, Q 17:99 "and a note from al-Akhfash" | **NQ** | The two verses are correctly identified. But al-Akhfash's note ("هو جمع الكفر، مثل برد وبرود") is about the plural form of *kufūr*; it does not support the sense. |
| C36 | "Covering" is supported by a verse recited by al-Aṣmaʿī | S | Entry 155 |
| C37 | Further senses: village, grave, night, sea, great river, farmer | S | Entry 155 |
| C38 | The link between the groups is attributed to Ibn al-Sikkīt; excerpt 2 | S | Entry 155 "قال ابن السكيت: ومنه سمي الكافر…". Translation accurate. |
| C39 | Ibn Fāris excerpt: a single meaning, covering | S | Entry 163. Translation accurate. |
| C40 | Ibn Fāris unifies (the thing covered is the truth); al-Jawharī lists | S | Entries 163 and 155 |
| C41 | Ibn Fāris cites Q 57:20 for kuffār as farmers; al-Jawharī does not | S | Entry 163 "{أعجب الكفار نباته} [الحديد: 20]"; entry 155 "والكفار: الزراع" with no verse |
| C42 | A poetry line read two ways (sea or night) | S | Entry 155 "ويحتمل أن يكون أراد الليل" |
| C43 | Law and doctrine terms: the maxim, kaffāra (Q 5:89), takfīr of sins "set against" iḥbāṭ; no witness | **NQ** | The entry reads "التكفير في المعاصي، كالإحباط في الثواب": takfīr is *likened to* iḥbāṭ, not contrasted with it. Everything else is correct: no witness is given, and Q 5:89 uses كفارة. |
| C44 | Ibn Barrī d. 582 AH | S | Mawsūʿa vol. 7 p. 822 |
| C45 | Ibn Barrī wrote corrective notes | S | Muzhir 1:76 "الحواشي على الصحاح"; Lisān 1:7 "فتتبع ما فيه … مخرجا لسقطاته" |
| C46 | Ibn Barrī: "the most grammatical of the lexicographers" | S | Muzhir 1:75 "وقال ابن برِّي: الجوهري أَنْحَى اللغويين" |
| C47 | Alh: alaha = "he worshipped"; Ibn ʿAbbās's reading at Q 7:127 | S | Entry 109 |
| C48 | Alh excerpt (Allāh < ilāh; the hamza dropped; the al-ilāh argument; Abū ʿAlī) | S | Entry 109 = Shamela 6:2223. Translation accurate. |
| C49 | He states his view, reports Abū ʿAlī's opposing view at length without reply, and adds Sībawayh | S | Entry 109 "وسمعت أبا على النحوي يقول … وجوز سيبويه أن يكون أصله لاها" |
| C50 | Ibn Barrī's answer survives in Lisān; excerpt | S | Lisān Alh (displayed). Text matches; translation accurate. |
| C51 | "Idols" excerpt | S | Entry 109. Translation accurate. |
| C52 | rkE: the whole entry; no witness, no verse | S | Entry 5785 (70 characters) = Shamela 3:1222 |
| C53 | Ibn Manẓūr: people "passed it from hand to hand"; misreadings that Ibn Barrī traced | S | Lisān 1:7 "فتداولوه وتناقلوه … قد صحّف وحرّف … فتتبع ما فيه" |
| C54 | Al-Ṣaghānī's Takmila | S | Muzhir 1:76 |
| C55 | Fīrūzābādī: "two-thirds of the language or more"; singled it out because it was widely used and relied on | S | Muzhir 1:77–78 "فاته ثلثا اللغة أو أكثر … لتداوله واشتهاره … واعتماد المدرسين على نقوله" |
| C56 | Lisān used it, with Ibn Barrī's notes, as a source | S | Lisān 1:7–8 (the five uṣūl) |
| C57 | Lisān kfr repeats "or he may have meant the night" and credits al-Jawharī | S | Lisān kfr "قال الجوهري: ويحتمل أن يكون أراد الليل" |
| C58 | Mukhtār al-Ṣiḥāḥ is an abridgement | S | Haywood p. 75; Mawsūʿa |
| C59 | The compilation date is not the date of the usages it records | S | Framing only; consistent with the house rules |
| C60 | 866 roots displayed | S | `_dict_guide_tool.py dicts` |
| C61 | Hawramani names no edition | S | Collection page |
| C62 | Wording matches ʿAṭṭār/Shamela, including the bracketed asterisks | S | kfr and Alh compared line by line. "(إنَّا بكُلٍّ كافِرون) *" and "(*) ومنه قولنا" appear in both; 81 displayed entries contain an asterisk. |
| C63 | Editor's footnotes omitted; hamza often unwritten; vowel marks partial | S | Shamela footnotes (١)(٢) are absent from the stored text; the stored text has "الشئ" and "لانه" |
| C64 | 17 hamza-final entries open with the weak-letter root; qrA opens with qarw | S | DB scan: jyA, swA, nbA, qrA, mrA, brA, n$A, xTA, bwA, bdA, DwA, *rA, xsA, hyA, hnA, SbA, $TA = 17 |
| C65 | "Nine" entries include a passage from a similar-looking root; nZr opens with nāṭūr | **NQ** | nZr is confirmed. A headword scan finds **8**: nZr (نطر), xlf (خطف), jbl (جيل), rjf (رخف), lHq (لخق), brq (يرق), Hlq (حلقن), Anf (أثف). A ninth may have no bracketed header, but I could not confirm it. |
| C66 | A few entries are cut short; Ayd is two words | S | Ayd = "[أيد] أبو زيد:". Amm, xfD and bwr also end on a colon. |
| C67 | The English summary calls covering "the root sense" | S | kfr harmonized_en §3 "Kafr as covering — the root sense" |
| C68 | Page refs Alh 6:2223–24, rkE 3:1222, kfr 2:807–08 | S | Shamela page headers (ids 4402–4403, 2418, 1597–1600) |

## Flagged items and fixes

1. **C8, "makes two promises"** (lede). Say "Among its claims, two shape what you meet on our site…", or keep "two claims" and cite Haywood (`[^haywood|p. 71]`, which says "two claims"). Do not imply the preface makes only two.
2. **C9, "hence its short title"** (lede). The naming explanation is al-Suyūṭī's. Move it out of the preface citation, e.g. "(al-Suyūṭī took the short title, *al-Ṣiḥāḥ*, 'the sound [words]', to come from this[^muzhir|vol. 1, p. 74])". Or delete "hence".
3. **C29, ʿAṭṭār and the uncle.** Replace "while granting the uncle some groundwork" with: "the editor ʿAṭṭār concedes that al-Fārābī and al-Bandanījī wrote earlier but still defends al-Jawharī as the originator, and rejects Ḥamad al-Jāsir's argument that al-Bandanījī's older rhyme book had anticipated him[^attar-essay]".
4. **C33, reading convention under a Haywood citation.** Present the first half as the guide's own advice with no citation (e.g. "A practical rule: …"). Cite Haywood only for "his definitions often coincide with those of Kitāb al-ʿAyn" (`[^haywood|p. 74]`). Also soften "are in al-Jawharī's voice" to "are presented as his own".
5. **C35, al-Akhfash.** Change to: "'Denial' is illustrated by two Qur'anic phrases (Q 28:48, glossed 'deniers', and Q 17:99), with a grammatical note from al-Akhfash on the plural *kufūr*." Or drop al-Akhfash.
6. **C43, "set against iḥbāṭ".** Change to "*takfīr* of sins likened to *iḥbāṭ*, the voiding of reward". The Arabic is "كالإحباط".
7. **C65, "nine".** Change to "eight" or "several", or re-count with a method that detects unheaded merges. Eight are confirmed: nZr, xlf, jbl, rjf, lHq, brq, Hlq, Anf.

## Brief issues (not factual)

- **must-fix: unlabeled translations from Arabic sources.** Several inline quotations come from Arabic works, not our stored entries, and are not labeled as translations made for this guide: "and for this he named his book al-Ṣiḥāḥ", "made gross errors in several places", "the most grammatical of the lexicographers", "passed it from hand to hand", "two-thirds of the language or more". The shared page box covers only quotations from stored entries. Add one short label, e.g. "(translations from Arabic sources are ours)" at first use, or a line in `onOurSite`.
- **suggestion: death-date paragraph reads like an encyclopedia.** It packs three dates and four authorities into one sentence (al-Qifṭī, Yāqūt, Baalbaki). It could be condensed to one sentence ("sources give 393/1002–3 or about 400/1010; an autograph copy dated 396 suggests the later date") so the essay stays on how to read the book.
- **suggestion: C22 wording.** "Read the book with a student" should say that the listener was al-Bīshakī, for whom the book was composed, and attribute the story to al-Mujāshiʿī as quoted by Yāqūt. The Mawsūʿa article also notes that the 396 autograph sits awkwardly with the "only as far as ḍād" story. A clause on that would strengthen the "pinch of salt" point.
- **suggestion: `onOurSite` length.** At about 190 words it is over FORMAT.md's ≈60–150. The two defect counts could be merged into one sentence.
- **suggestion: word count.** 1,099 words (per the validator), right at the upper limit. Fixes 1–6 should not add words.
- No padding, rankings or generic praise found. The "original root meaning" narrative is handled well: the guide explicitly contrasts al-Jawharī's listing with Ibn Fāris's unifying, and flags the site's own "root sense" framing. Every root mention is linked, and every excerpt translation is labeled by the page.

## URL problems

None. Every URL opens the stated work. WebFetch cannot reach the two web.archive.org Iranica links, but they load normally in a browser or with curl.

## Validator

`node scripts/validate-dictionary-guides.mjs al-sihah`: **ok** (12 root links, 9 distinct pairs, 7 excerpts, 1,099 words, 1/1 guides pass).

## Site-data notes

- The stored date 1003 matches al-Qifṭī's 393 AH (Hawramani also gives 1003/393). Other sources put the death at about 400/1009–10: Mawsūʿa ("معظم المصادر … نحو سنة 400"), Baalbaki, and Yāqūt's autograph dated 396. The label is not wrong but reflects one side of a dispute. It affects panel order only relative to Ibn Fāris (d. 395/1004).
- The stored text of some entries merges neighbouring roots or has lost its first part: the 17 hamza-final entries plus the 8 merges listed above, and Ayd truncated to "أبو زيد:". This is a data-quality issue, and the guide discloses it correctly.
