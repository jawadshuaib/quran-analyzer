# Lane's Lexicon guide: verification round 3

- **File checked:** `roots/frontend/src/content/dictionary-guides/guides/lane-lexicon.ts` (the version revised after round 2).
- **Checker:** independent verifier, round 3, 2026-09-26.
- **Independence:** I did not open research-notes.md or any revision-*.md file. I read verification-r2.md only for its list of flags. I re-checked every claim against the sources myself.

## What I checked against

- **Internet Archive item `LAB1865AREN`** (Librairie du Liban reprint, Beirut 1968; the VOL. 1 OCR has "LIBRAIRIE DU LIBAN … BEIRUT … 1968" and "WILLIAMS AND NORGATE").
  - I used each file's `_hocr_searchtext` and `_hocr_pageindex` to tie OCR text to leaves, and `_page_numbers.json` to tie leaves to print pages. In VOL. 1 the leaf number equals the roman page number of the Preface. The header "PREFACE. xxiii" falls between "would" and "frequently have misled me", which confirms the mapping.
  - **Page images I viewed myself:**
    - p. 31 (VOL. 1 leaf 67, art. اخر): ▼ arrow-heads, dash, double rule, ‡.
    - p. 1749 (VOL. 4 leaf 472, art. صوم): "by a tropical application, (TA,) ‡from speech"; "means † [Verily I have vowed unto the Compassionate] an abstaining from speech. (Ṣ, M, Mṣb.)"; "† The horse stood without eating of fodder"; "‡ He abstained from going along".
    - p. 1750 (leaf 473): wind ‡, water †, day ‡, ostrich ‡, and "══ صام منيته".
    - p. 2487 (VOL. 3 leaf 14): "[قتع قتل قتم قتن قتو See Supplement.]".
    - Editor's Preface (VOL. 5 leaf 4): "At the time of his death my Uncle was engaged on the article قد. Up to this point every article is ready for the printers. Of the rest the majority are written, but some need collation."
  - **OCR only:**
    - p. 658 (VOL. 2 leaf 293, art. حنف): "Er-Rághib explains [حنف] better … (TA.)"; "a conventional term of the professors: (Mgh:) [or,] accord. to AO …".
    - p. 2984 (VOL. 8 leaf 237): art. قتل beginning "†He knew the thing … (Bd in iv. 156, and TA,)". It matches entry 729.
    - The full Editor's Preface (VOL. 5 leaves 4–5, signed "July, 1877") and Postscript (leaf 6, "1st January, 1893").
    - Title-page leaves: VOL. 3 = Part 7, 1885; VOL. 8 = Part 8, 1893.
- **laneslexicon.github.io/lexicon/site/lane/preface/** (HTTP 200). A full transcription of the Preface, including table II ("Tropical, مَجَازٌ and مَجَازِىٌّ"; "‡ means asserted to be tropical … † means supposed by me to [be] tropical") and table IV, "Indications of Authorities" (A, AO, Bḍ, I'Ab, JeL, KT, Kh, Ḳ, Ḳur, L, M, Mgh, Mṣb, Ṣ, TA). It ends "E. W. L. December , 1862."
- **Haywood, *Arabic Lexicography*** (archive.org `in.gov.ignca.12555`, `12555_djvu.txt`): pp. 124–26 on Lane. The p. 125 passage reads "showed how inaccurate this statement was … a very inadequate reference work after the article 'qadda'".
- **DNB, "Lane, Edward William"**, by Stanley Lane-Poole, vol. 32 (Wikisource, HTTP 200). It says: "The succeeding parts came out in 1865, 1867, 1872, 1874, and posthumously … in 1877, 1885, and 1892." It also has "died … (10 Aug. 1876)" and "returned to Cairo in 1842".
- **Perseus `doc=ASl`** (HTTP 200). Its note reads "An Arabic-English Lexicon. London. Williams and Norgate. 1863." It carries a CC BY-SA 3.0 US licence.
- **hawramani Lane page** (HTTP 200). It says the text was "sourced from Tufts University … We used a TXT version created by … Navid-ul-Islam. Our version … fixes various errors from both".
- **Displayed data (`_dict_guide_tool.py`):**
  - `entry` for Swm (5692), Hnf (6343), qtl (729) and Axr, and al-Rāghib's Hnf (6348);
  - `dicts`: 1,410 displayed entries, name_ar "Lane's Lexicon";
  - `roots`: 1,410 roots, of which 427 have ق–ي as first letter (ن 92, و 71, ق 69, م 58, ك 53, ل 48, ه 28, ي 8);
  - `grep`: "See Supplement" (5), "CCC" (22), and original vs harmonized counts ("assumed tropical" 782 vs 16; TA 1,361 vs 119; Msb 1,261 vs 151).
- **`verses` table** (quran.db): 19:26 contains إِنِّى نَذَرْتُ لِلرَّحْمَٰنِ صَوْمًا; 4:157 contains وَمَا قَتَلُوهُ; 2:183–187 is the fasting passage; 2:181 is not.

## Claims table

S = supported. NQ = needs qualification. U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *An Arabic–English Lexicon* | S | VOL. 1 title page (OCR); Perseus note |
| C2 | titleAr مدّ القاموس | S | Preface p. xxxii (transcription): "The Arabic title مَدُّ القَامُوس" |
| C3 | titleGloss: Lane glossed it as "the flow of the sea" and "the extension of the Qāmūs" | S | p. xxxii: "two meanings: 'The Flow of the Sea' and 'The Extension of the Ḳámoos.'" |
| C4 | Author Edward William Lane | S | Title pages; DNB |
| C5 | Period "published 1863–93 (Lane d. 1876)" | S | DNB (1863; d. 10 Aug 1876); Part 8 title leaf "1893" |
| C6 | Kind "Arabic–English lexicon" | S | Title |
| C7 | Summary: the medieval lexicons, read mainly through the *Tāj*, put into English | S | p. xix: "the medium through which I have drawn most of the contents of my lexicon" |
| C8 | Summary: a source named for almost every sense; his own additions bracketed | S | p. xxvi: "nothing … without indicating at least one authority … except interwoven additions … square brackets" |
| C9 | Summary: he died at qāf; entries from there on were published later, some only as notes | S | Editor's Preface (image, قد); Postscript; p. 2984 |
| C10 | Lede: thirty-four years | S | Editor's Preface: "After thirty-four years of labour at the Lexicon" |
| C11 | Lede: initials on almost every meaning; brackets; marks separating an authority's "figurative" from Lane's | S | pp. xxv, xxvi |
| C12 | Lede: "less a dictionary in the modern sense than a translated anthology" | S (interpretation) | Grounded in pp. xxii and xxvi; framed as the essay's own view |
| C13 | Lede: the signals show which source Lane reports and where he speaks himself | S | pp. xxv–xxvi |
| C14 | 1842; not Golius-style "epitomes or abstracts or manuals" but "the most copious Eastern sources" | S | p. v, ¶¶1–2 ("Golius and others") |
| C15 | In Cairo he built on al-Zabīdī's *Tāj* | S | p. v ("I knew to exist in Cairo … thither … I betook myself"); p. xix |
| C16 | *Tāj* finished in the 1760s | S | p. xviii: "finished the Táj el-'Aroos A.D. 1767 or 1768" |
| C17 | "the medium through which I have drawn most of the contents of my lexicon" | S | p. xix, verbatim |
| C18 | Most of the *Tāj*'s additions are verbatim in the *Lisān*; he often composed from the *Lisān*, usually naming the *Tāj* | S | p. xx ("existed verbatim in the Lisán"; "compose articles … principally from the Lisán") |
| C19 | "as nearly as possible in the words in which some person of authority has transmitted it" | S | p. xxii, verbatim |
| C20 | Nothing without an authority except "interwoven additions", always in brackets | S | p. xxvi |
| C21 | Modern Arabic "would frequently have misled me" without great caution; changes "since the classical age" | S | pp. xxii–xxiii. Lane also says modern Arabic often solved difficulties; the essay's "admits" is fair |
| C22 | Guessing meanings from one another "by means of analogy" needs the same caution | S | p. xxiii ("Great caution is likewise requisite … by means of analogy") |
| C23 | Senses ordered by relations; figurative ones marked for "genealogies"; breaks and complete dissociations marked | S | p. xxv |
| C24 | "Classical": after the Arab philologists' classes; the age "nearly ended with the first century"; best Islāmī poets hold "classical rank" | S | pp. viii–ix |
| C25 | The Arabs held the Qur'an the highest authority | S | p. ix: "The highest of all authorities … is held by the Arabs to be the Kur-án" |
| C26 | Post-classical words and senses excluded "with very few exceptions" | S | p. xxvi |
| C27 | Initials after each sense name Lane's authority | S | p. xxvi |
| C28 | S, K, TA, Msb, A, M, L, Mgh, Kur, Bd, Jel expanded as given | S | Table IV, p. xxxi (transcription; the OCR places it on leaf 31) |
| C29 | Grouped initials agree "essentially, or mainly; but not always … in words" | S | p. xxvi |
| C30 | Senses joined by "or": "one is right in one instance, and another in another" | S | p. xxv |
| C31 | Aor. = aorist (imperfect), often by its vowel alone; inf. n. = *maṣdar*; i. q. = "the same as" | S | Table II, p. xxix ("Aor., for aorist"; "Inf. n., for infinitive noun"; "I. q., for idem quod"); vowel-only aor. seen in entry 5692 |
| C32 | "Tropical" = *majāz* | S | Table II: "Tropical, مَجَازٌ and مَجَازِىٌّ" |
| C33 | ‡ → "(tropical:)": asserted by an authority, "generally on the authority of the Asás" | S | p. xxv; pp. 1749–50 images against stored 5692 |
| C34 | † → "(assumed tropical:)": Lane's own judgment | S | p. xxv; table p. xxix; p. 1749 image against 5692 |
| C35 | ↓ flags a word explained under another headword | S | p. xxiv ("an arrow-head … to render conspicuous a word explained in a paragraph headed by another word"); p. 31 image ▼ = stored ↓ (Axr) |
| C36 | صوم excerpt, including the new "and … by a tropical application, ( TA ,) ( tropical :) from speech: …" | S | Entry 5692; validator passes |
| C37 | Apart from brackets and †, every claim in the excerpt is credited to someone else | S | Entry 5692 as excerpted |
| C38 | The *Tāj* calls "he abstained" the primary sense | S | "this is the primary signification: ( TA :)" |
| C39 | *Miṣbāḥ* finished 734 AH (1333–4 CE); sets "proper language of the Arabs" against "language of the law" | S | p. xvi ("finished its composition in the year of the Flight 734"); 5692 |
| C40 | *Mughrib*: lexicon of words in traditions and legal works; abstaining from eating is the proper sense, the fast a secondary application | S | p. xv ("particularly of such as occur in books of Traditions, and other works relating to the law"); 5692 |
| C41 | KT = *Kitāb al-Taʿrīfāt*, which gives daybreak-to-sunset | S | Table IV ("KT The Kitáb et-Taạreefát"); 5692 |
| C42 | Al-Khalīl, through the *Ṣiḥāḥ*: "the standing without work" | S | "accord. to Kh … ( S .)"; Table IV: Kh = El-Khaleel |
| C43 | NEW: abstaining "from speech" is figurative (‡) on the *Tāj*'s word | S | p. 1749 image: "by a tropical application, (TA,) ‡from speech"; stored "( tropical :)" |
| C44 | NEW: Ibn ʿAbbās's reading of Mary's vow in Q 19:26 carries Lane's own † | S | p. 1749 image: "means † [Verily …] an abstaining from speech"; I'Ab = Ibn-'Abbás (Table IV); verses 19:26 |
| C45 | Further down: horse †, still water †, wind ‡ | S | p. 1749 (horse †), p. 1750 (water †, wind ‡) images; 5692 |
| C46 | The order follows relations between senses, not a dated history | S | p. xxv (interpretive, fair) |
| C47 | Lane's "xix. 27" = our Q 19:26 | S | `verses` 19:26 |
| C48 | For *ḥanīf*, Lane lines the explanations up and leaves them there | S | Entry 6343; Lane's only brackets there are connective ("[and particularly]", "[and]", "[or,]") |
| C49 | حنف excerpt | S | Entry 6343; validator passes |
| C50 | Al-Rāghib: *mayl ʿan al-ḍalāl ilā l-istiqāma*; the *ḥanīf* is one who so inclines; the Arabs called anyone who made the pilgrimage or was circumcised *ḥanīf* (labelled "our translation") | S | Entry 6348: الحنف: هو ميل عن الضلال إلى الاستقامة … والحنيف هو المائل إلى ذلك … وسمت العرب كل من حج أو اختتن حنيفا |
| C51 | In Lane al-Rāghib is the first witness; the "better" verdict is tagged TA | S | p. 658 (OCR) and 6343: "(Er-Rághib, TA:)" opens the *ḥanīf* paragraph; "Er-Rághib explains حنف better … (TA.)" |
| C52 | AO (Abū ʿUbayda) report: idol-worshippers called themselves *ḥanīf*; with Islam the name passed to the Muslim; left unweighed | S | 6343; Table IV "AO Aboo-'Obeydeh" |
| C53 | *Mughrib* flags "a Muslim" as "a conventional term" (a scholars' technical usage) | S | "a conventional term of the professors: ( Mgh :)" |
| C54 | Lane saw five parts through the press (1863–74) | S | DNB (1863, 1865, 1867, 1872, 1874). See brief issue 3 (proofs to p. 2386) |
| C55 | Died 10 Aug 1876 while working on قد, in qāf | S | Editor's Preface (image); DNB |
| C56 | The *Ṣiḥāḥ* files a root by its last letter | S | p. xiv: "according to the place of the last letter of the root" |
| C57 | Lane wrote in the *Ṣiḥāḥ*'s order and finished articles as printers neared them; "three different stages", from bare notes to ready for press | S | Editor's Preface (image) |
| C58 | Stanley Lane-Poole was his great-nephew | S | Editor's Preface: "my Great-Uncle" |
| C59 | Up to قد every article ready, "he reported"; "of the rest the majority are written, but some need collation" | S | Editor's Preface (image), verbatim; attributed |
| C60 | Lane-Poole published ghayn and fāʾ in 1877, and qāf to yāʾ in 1885 and 1893 | S | Editor's Preface ("contains only غ and ف"; next Parts ق … ي); DNB 1877/1885; title leaves Part 7 (1885), Part 8 (1893) |
| C61 | Rather than write the missing articles from the *Tāj* (printed at Būlāq), he added a Supplement of Lane's notes | S | Postscript 1893 |
| C62 | Notes "are not to be accepted as the final decision of their writer" | S | Postscript, verbatim |
| C63 | Many record the "contemporary speech" of Lane's day | S | Postscript: "many of them are clearly the record of contemporary speech" |
| C64 | Meanings "most familiar to the student will often be found missing" | S | Postscript, verbatim |
| C65 | Haywood: Lane-Poole's estimate inaccurate; "a very inadequate reference work" after قد | S | Haywood p. 125 (OCR, page header "125" nearby) |
| C66 | قتل precedes قد yet the main text says "See Supplement", and our entry is that note | S | p. 2487 (image); p. 2984 (OCR) matches entry 729 |
| C67 | قتل excerpt | S | Entry 729; validator passes |
| C68 | It cites al-Bayḍāwī on Q 4:157 and never glosses the verb as "he killed" | S | 729: "Bd in iv. 156"; `verses` 4:157 وَمَا قَتَلُوهُ; Form I is glossed only "He knew the thing" |
| C69 | Lane shows the recorded range and who records it; he cannot decide a verse; for *ṣawm* the fasting verses (Q 2:183–187) decide | S | Interpretive; consistent with pp. xxii, xxvi; `verses` 2:183–187 |
| C70 | A tag dates a book, not a usage; in *ṣawm* Ibn ʿAbbās reaches Lane through the *Ṣiḥāḥ* | S | 5692: "it is said ( S , M ) by I'Ab ( S )" |
| C71 | Bd/Jel glosses are commentators' readings | S | Table IV: "Exposition of the Ḳur-án" for both |
| C72 | Labels like "language of the law"/"post-classical" mark specialised or later use; absence proves nothing | S | Interpretive; labels occur in 5692 and 6343 |
| C73 | onOurSite: stored text = Perseus/Tufts digitisation of the London printing, as corrected on hawramani | S | Perseus note; hawramani page (via an intermediate TXT, which the essay leaves out; harmless) |
| C74 | ‡ → "(tropical:)", † → "(assumed tropical:)", dash → b2…, double rule → A2… | S | p. 31 image vs Axr (—— → b2, ══ → A2); pp. 1749–50 images vs 5692 |
| C75 | Stray "CCC" is not Lane's; "appears to be" a digitisation artefact | S | 22 displayed entries; hedged |
| C76 | The readable English drops most initials and ‡/† labels and can say more than Lane | S | grep counts above; Swm harmonized: "Throughout, Lane traces every sense back to a single underlying idea" (not in Lane) |
| C77 | 1,410 roots; 427 qāf–yāʾ from the 1885/1893 parts | S | `roots` count; Part 6 = غ ف only |
| C78 | Nothing in the stored text marks a finished article vs a Supplement note | S | Entry 729 has no marker |
| C79 | A "كفل كفن كفى See Supplement" line points to other roots; not part of the entry | S | kfr entry; same pattern as p. 2487 |
| C80 | Lane's verse numbers often differ; English versions repeat them | S | 5692 "ii. 181", "xix. 27"; harmonized "2:181", "19:27"; 729 "iv. 156" |
| C81 | Source `lane-preface`: Williams and Norgate 1863; pp. v–xxxii; dated Dec 1862; LdL 1968 scan; NEW deep link laneslexicon.github.io/lexicon/site/lane/preface/ | S | VOL. 1 OCR; transcription ends "December , 1862"; link HTTP 200, same text |
| C82 | Source `lexicon`: pp. 31, 658, 1749, 2487, 2984; Part 8 title page | S | Each located in the scans (see above). Minor: water and wind are on p. 1750 (brief issue 1) |
| C83 | Source `dnb`: DNB dates the last part 1892; the part itself is 1893 | S | Wikisource; Part 8 title leaf |
| C84 | NEW source `lane-poole`: both printed at the front of the "VOL. 5" file, after the Part 5 title page and before the Memoir | S | VOL. 5 searchtext: leaf 3 title page ("ARABIC-ENGLISH LEXICON …"), leaf 4 "EDITOR'S PREFACE", leaf 6 "POSTSCRIPT", leaf 7 "EDWARD WILLIAM LANE. 1801—1825" (Memoir); leaf 44 = p. 1760 |
| C85 | Source `haywood`: Brill 1960, pp. 123–26 | S | archive.org item: "Arabic lexicography, Haywood, 1960"; Lane section on pp. 124–26 |
| C86 | Source `perseus` | S | Opens; London, Williams and Norgate; CC BY-SA |
| C87 | Source `hawramani` | S | Opens; Tufts source, corrected |

**Totals:** 87 claims. 87 supported, 0 need qualification, 0 unsupported.

## Round-2 flags: status

| Flag | Status |
|---|---|
| C77 (r2): `lane-poole` locator "follow Part 5" | **Fixed.** The new wording ("printed at the front of the file … after the Part 5 title page and before Lane-Poole's Memoir") matches the VOL. 5 leaf order I checked (C84). |
| Brief (r2): ‡ on "from speech" | **Addressed.** The new sentence is accurate (p. 1749 image; C43, C44). |
| Brief (r2): laneslexicon deep link | **Addressed.** The path is now in the citation and opens (C81). |
| Brief (r2): length | 1,099 words (validator). Still at the ceiling. |

All four new claims from the reviser (C43, C44, C81, C84) are supported. The new excerpt text (C36) passes the validator and matches entry 5692.

## Flagged items and fixes

None.

## Brief issues

1. **suggestion.** The `lexicon` source lists p. 1749 for art. صوم. The water (†) and wind (‡) senses the essay mentions are on p. 1750. Change "p. 1749 (art. صوم)" to "pp. 1749–50 (art. صوم)". This touches the source list only, not the word count.
2. **suggestion.** The abbreviations paragraph ("They include S … Jel …") is still list-like. It works as a reading key. Keep it as it is; do not expand it.
3. **suggestion (optional).** "Lane saw five parts through the press (1863–74)" is accurate as a count of parts published in his lifetime (DNB). But the Editor's Preface adds: "Up to p. 2386 the proofs were corrected by Mr. Lane". That is, he also corrected the first part of Part 6. No change is needed. If a word can be spared, "saw five parts published" is marginally more exact.
4. **suggestion.** The page is at 1,099 of 1,100 words. Any future addition needs an equal cut.
5. No padding, rankings, generic praise, bare root mentions or unlabelled translations. The one translation from Arabic in running text (al-Rāghib) is marked "(our translation)". The Lane excerpts are English originals, so none needs a translation. No material is promised that the site does not show; onOurSite warns that Supplement notes are not marked.

## URLs

| URL | Status | Notes |
|---|---|---|
| https://archive.org/details/LAB1865AREN | 200 | Lane, Librairie du Liban reprint, 8 files. Used for `lane-preface`, `lexicon` and `lane-poole` |
| https://laneslexicon.github.io/lexicon/site/lane/preface/ | 200 | Named in the citation text only. Full Preface transcription |
| https://en.wikisource.org/wiki/Dictionary_of_National_Biography,_1885-1900/Lane,_Edward_William | 200 | DNB vol. 32, by Stanley Lane-Poole |
| https://archive.org/details/in.gov.ignca.12555 | 200 | Haywood, *Arabic lexicography*, 1960 |
| http://www.perseus.tufts.edu/hopper/text?doc=ASl&fromdoc=Perseus:text:2002.02.0015 | 200 | Lane text with note "London. Williams and Norgate. 1863." |
| https://arabiclexicon.hawramani.com/william-edward-lane-arabic-english-lexicon/ | 200 | States the Tufts source and its corrections |

Every listed source was used, and each is the work it claims to be.

## Validator

`node scripts/validate-dictionary-guides.mjs lane-lexicon` → **ok**: 4 root links (4 distinct pairs), 3 excerpts, 1,099 words (lede + body), example roots Swm, Hnf, qtl. 1/1 guides pass.

## Site-data issues (report only)

1. **`name_ar` = "Lane's Lexicon".** This is not an Arabic title. Lane's own Arabic title is مدّ القاموس (Preface p. xxxii).
2. **Stored date 1876** is Lane's death year. It works for ordering, but Parts 6–8 appeared in 1877, 1885 and 1893.
3. **"CCC" artefacts** appear in 22 displayed entries (e.g. kfr, jEl, Zlm, nfs).
4. **The Swm harmonized English (default view) attributes to Lane things he does not say:**
   - "Throughout, Lane traces every sense back to a single underlying idea";
   - "all built on the idea of stillness/holding-back";
   - "Lane reports this as the primary, original meaning" (this is the *Tāj*'s statement, tagged TA).
5. **Harmonized texts repeat Lane's Flügel-style verse numbers** as if they were standard: Swm "Qur'an 2:181" and "Qur'an 19:27", qtl "Qurʾan 4:156". As verse links these point to the wrong verses; they should be 2:185, 19:26 and 4:157.
6. **The qtl harmonized text cites "Kashshaf".** Lane's entry (729; p. 2984) cites Bd, K (the *Qāmūs*), TA, Msb, A, S, JM, Mgh and El-Jurjánee, never Ksh. The harmonizer probably misread K.
7. **Segmentation:** the stored mTr entry runs past "مطس &c. See Supplement" into the next article, مظ ("The pomegranate-tree …"). kns also carries material after its "See Supplement" line.
