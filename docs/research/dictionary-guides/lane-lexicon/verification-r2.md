# Lane's Lexicon guide — verification round 2

- **File checked:** `roots/frontend/src/content/dictionary-guides/guides/lane-lexicon.ts` (the version revised after round 1).
- **Checker:** independent verifier, round 2, 2026-09-26.
- **Independence:** I did not open research-notes.md or revision-r1.md. I read verification-r1.md only for the list of earlier flags. Every point below was re-checked against the sources.

## What I checked against

- **Lane's Preface (Part 1, 1863).** Source: Internet Archive item `LAB1865AREN` (Librairie du Liban reprint, Beirut 1968).
  - I read the OCR text of the file labelled "VOL. 1": pp. v, viii–ix, xiv–xxvii, the tables, and xxxii.
  - I viewed page images from the item's jp2 set:
    - p. xxxi (table IV), which confirms `AO` = Aboo-'Obeydeh, `A` = the Asās, `Bd` = El-Beydáwee, and that most authorities were drawn "through the medium of" the TA or L;
    - p. xxxii, which confirms مدّ القاموس, the "two meanings", and the date "December, 1862".
- **Lexicon pages (page images).**
  - p. 31 (art. اخر; shows the arrow, dash and double rule).
  - p. 658 (art. حنف).
  - pp. 1749–50 (art. صوم): ‡ on "from speech" and on the wind; † on the Ibn ʿAbbās reading, the horse and the water; "— [Hence,]" at b2; "══" at A2 and A3.
  - p. 2487 (Part 7, file "VOL. 3", leaf 14): "[قتع قتل قتم قتن قتو See Supplement.]".
  - p. 2984 (Supplement, file "VOL. 8", leaf 237): art. قتل, beginning "†He knew the thing".
  - Title-page dates of all eight parts, from the OCR of each file: 1863, 1865, 1867, 1872, 1874, 1877, 1885, 1893.
- **Stanley Lane-Poole.**
  - Editor's Preface (July 1877): OCR plus the page image (leaf 4), which clearly shows "engaged on the article قد".
  - Postscript (1 January 1893): OCR.
  - Both are in the file labelled "VOL. 5". Its page-number map shows the Part 5 title page (leaf 3), then the Editor's Preface (leaves 4–5), the Postscript (leaf 6), the Memoir (from leaf 7), and only then the lexicon text of Part 5 (pp. 1760–2219, from leaf 44).
- **Haywood, *Arabic Lexicography* (1960):** OCR of archive.org `in.gov.ignca.12555`, pp. 124–25.
- **DNB, "Lane, Edward William"** (Wikisource): "The succeeding parts came out in 1865, 1867, 1872, 1874, and posthumously … in 1877, 1885, and 1892."
- **Perseus `doc=ASl`:** the bibliographic note reads "London. Williams and Norgate. 1863." It carries a CC BY-SA 3.0 US licence, and its text uses "― -b2-" and "-A2-" markers.
- **hawramani Lane page:** "sourced from Tufts University … We used a TXT version created by … Navid-ul-Islam", and it fixes errors in both.
- **Displayed data (`_dict_guide_tool.py`):**
  - `entry` for Swm (5692), Hnf (6343), qtl (729), mTr, and al-Rāghib Hnf (6348);
  - `roots` (1,410 roots; 427 whose first letter is ق to ي);
  - `grep` "See Supplement" (5 entries), "CCC" (22 entries), and source tags in the original vs the harmonized text (TA 1,361 vs 119; Msb 1,261 vs 151; "tropical" 978 vs 312; "(tropical :)/(assumed tropical :)" 782 vs 0).
- **`verses` table** in quran.db: 19:26, 19:27, 4:156, 4:157, 2:181, 2:183, 2:185, 2:187.

## Claims table

S = supported. NQ = needs qualification. U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *An Arabic–English Lexicon* | S | Title page, Part 1 (1863): "AN ARABIC-ENGLISH LEXICON" |
| C2 | titleAr مدّ القاموس | S | Preface p. xxxii (image): "The Arabic title مدّ القاموس" |
| C3 | titleGloss: Lane glossed it as "the flow of the sea" and "the extension of the Qāmūs" | S | p. xxxii: "It has two meanings: 'The Flow of the Sea' and 'The Extension of the Kámoos.'" |
| C4 | Author Edward William Lane | S | Title pages |
| C5 | Period "published 1863–93 (Lane d. 1876)" | S | Title pages of Parts 1 (1863) and 8 (1893). Editor's Preface: died 10 Aug 1876 |
| C6 | Kind "Arabic–English lexicon" | S | Title page |
| C7 | Summary: Lane put the Arabic lexicons, read mainly through the *Tāj*, into English | S | Preface p. xix: "the medium through which I have drawn most of the contents of my lexicon" |
| C8 | Summary: a source is named for almost every sense, and his own additions are bracketed | S | p. xxvi: "nothing … without indicating at least one authority … except interwoven additions … square brackets" |
| C9 | Summary: he died at qāf; later entries were published posthumously, some only as notes | S | Editor's Preface 1877; Postscript 1893; Supplement p. 2984 |
| C10 | Lede: thirty-four years | S | Editor's Preface: "After thirty-four years of labour at the Lexicon" |
| C11 | Lede: initials on almost every meaning, square brackets, marks separating an authority's "figurative" from Lane's own | S | pp. xxv, xxvi |
| C12 | Lede: "less a dictionary in the modern sense than a translated anthology" | S (interpretation) | Grounded in p. xxii ("every explanation … in the words in which some person of authority has transmitted it") and p. xxvi. The essay's own framing, fairly signalled |
| C13 | Lede: learn the signals and you can tell "which source Lane is reporting and where he speaks himself" | S | Round-1 fix applied. Tags name Lane's cited authority (p. xxvi); brackets and † mark Lane's voice (pp. xxv–xxvi) |
| C14 | 1842; not Golius-style "epitomes or abstracts or manuals" but "the most copious Eastern sources" | S | Preface p. v, first two paragraphs |
| C15 | *Tāj* finished in the 1760s | S | p. xviii: "finished the Táj el-'Aroos A.D. 1767 or 1768" |
| C16 | "the medium through which I have drawn most of the contents of my lexicon" | S | p. xix |
| C17 | Most of the *Tāj*'s additions are verbatim in the *Lisān*; Lane often composed from the *Lisān* but usually named the *Tāj* | S | p. xx: "from three-fourths to about nine-tenths … verbatim … compose articles … principally from the Lisán … giving the latter as my authority in most instances" |
| C18 | "as nearly as possible in the words in which some person of authority has transmitted it" | S | p. xxii |
| C19 | Nothing without an authority except "interwoven additions", always in square brackets | S | p. xxvi |
| C20 | "would frequently have misled me" … "since the classical age" | S | pp. xxii–xxiii |
| C21 | Guessing meanings "by means of analogy" needs the same caution | S | p. xxiii |
| C22 | He orders senses by their relations, marks figurative senses to show "genealogies", and marks breaks and complete dissociations | S | p. xxv. The round-1 fix is applied (the "one idea" contrast is gone) |
| C23 | "Classical": pre-Islamic poets and those who lived into Islam; the best Islāmī poets hold "classical rank"; the age "nearly ended with the first century" | S | pp. viii–ix, quoted exactly. Round-1 fix applied |
| C24 | The Arabs held the Qur'an to be the highest authority | S | p. ix |
| C25 | Post-classical words and senses excluded "with very few exceptions" | S | p. xxvi |
| C26 | "The initials after each sense name Lane's authority for it" | S | p. xxvi ("indicating at least one authority") |
| C27 | S, K, TA, Msb, A, M, L, Mgh, Kur, Bd, Jel expanded as given | S | Table IV, p. xxxi (image and OCR) |
| C28 | Grouped initials agree "essentially, or mainly; but not always … in words" | S | p. xxvi |
| C29 | Senses joined by "or": "one is right in one instance, and another in another" | S | p. xxv |
| C30 | Aor. = aorist (the imperfect), often shown by vowel alone; inf. n. = *maṣdar*; i. q. = "the same as" | S | Table II, p. xxix ("Aor., for aorist"; "Inf. n., for infinitive noun"; "I. q., for idem quod"). Vowel-only aor. seen in entry 5692 |
| C31 | "Tropical" = *majāz*. ‡ → "(tropical:)": asserted by an authority, "generally on the authority of the Asás". † → "(assumed tropical:)": Lane's own judgment | S | p. xxv; table p. xxix; print p. 1749 against the stored 5692 |
| C32 | ↓ flags a word explained under another headword | S | p. xxiv |
| C33 | صوم excerpt | S | Entry 5692; validator passes |
| C34 | Apart from brackets and †, every claim in the excerpt is credited to someone else | S | Entry 5692 as excerpted |
| C35 | The *Tāj* calls "he abstained" the primary sense | S | "this is the primary signification: ( TA :)" |
| C36 | *Miṣbāḥ* finished 734 AH (1333–4 CE); it contrasts "proper language of the Arabs" with "language of the law" | S | p. xvi; entry 5692. 734 AH = Sept 1333 – Sept 1334 |
| C37 | *Mughrib* is a lexicon of words in traditions and legal works; for it, abstaining from eating is the proper sense and the fast a secondary application | S | p. xv; entry 5692 |
| C38 | KT = *Kitāb al-Taʿrīfāt*, which gives daybreak-to-sunset | S | Table p. xxxi; entry 5692 |
| C39 | Al-Khalīl via the *Ṣiḥāḥ*: "the standing without work" | S | "accord. to Kh … ( S .)"; table: Kh = El-Khaleel |
| C40 | Ibn ʿAbbās's reading of Q 19:26 is filed under † | S | Print p. 1749 shows † ; stored "(assumed tropical :)" |
| C41 | Further down: horse † , still water † , wind ‡ | S | Print pp. 1749–50; entry 5692 |
| C42 | The order follows relations between senses, not a dated history | S | p. xxv (interpretive, fair) |
| C43 | Lane's "xix. 27" = Q 19:26 here | S | `verses` 19:26 contains إِنِّى نَذَرْتُ لِلرَّحْمَٰنِ صَوْمًا |
| C44 | حنف excerpt | S | Entry 6343; validator passes |
| C45 | Lane lines the explanations up and gives no verdict of his own | S | Entry 6343 / p. 658. Lane's brackets are only "[and particularly]", "[and]", "[or,]" |
| C46 | Al-Rāghib: *mayl ʿan al-ḍalāl ilā l-istiqāma*; the *ḥanīf* is one who so inclines; the Arabs called anyone who made the pilgrimage or was circumcised *ḥanīf* (translation checked) | S | Entry 6348: الحنف: هو ميل عن الضلال إلى الاستقامة … والحنيف هو المائل إلى ذلك … وسمت العرب كل من حج أو اختتن حنيفا |
| C47 | In Lane, al-Rāghib is the first witness; the verdict that he explains *ḥanaf* "better" is tagged TA (p. 658) | S | Print p. 658 (image): "but Er-Rághib explains حنف better … (TA.)"; ḥanīf paragraph opens "(Er-Rághib, TA:)" |
| C48 | AO's report (idol-worshippers called themselves *ḥanīf*; with Islam the name passed to the Muslim) sits beside the rest unweighed | S | Entry 6343; AO = Aboo-'Obeydeh (table p. xxxi image). Round-1 fix applied |
| C49 | The *Mughrib* flags "a Muslim" as "a conventional term" (a scholars' technical usage) | S | "a conventional term of the professors: ( Mgh :)" |
| C50 | Lane saw five parts through the press (1863–74) | S | DNB; title pages of Parts 1–5 (1863, 1865, 1867, 1872, 1874) |
| C51 | He died 10 Aug 1876 while working on the article قد, in qāf | S | Editor's Preface (image, VOL. 5 leaf 4) |
| C52 | The *Ṣiḥāḥ* files a root by its last letter | S | p. xiv: "mentioning each word according to the place of the last letter of the root" |
| C53 | Lane wrote in the *Ṣiḥāḥ*'s order and finished articles as the printers neared them, so articles were "in three different stages", from bare notes to ready for press | S | Editor's Preface: "I found articles in three different stages … Mr. Lane was of necessity obliged to write in the order of the Sihah, and … as the printers gradually approached him he finished those articles …" |
| C54 | Stanley Lane-Poole was his great-nephew | S | Editor's Preface: "my Great-Uncle" |
| C55 | Lane-Poole reported every article ready up to قد; "of the rest the majority are written, but some need collation" | S | Editor's Preface, verbatim; now attributed ("he reported"). Round-1 fix applied |
| C56 | Lane-Poole published ghayn and fāʾ in 1877, and qāf to yāʾ in 1885 and 1893 | S | Editor's Preface ("contains only غ and ف"); title pages of Parts 6 (1877), 7 (1885), 8 (1893) |
| C57 | Rather than write the missing articles from the *Tāj* (by then printed at Būlāq), he added a Supplement of Lane's notes | S | Postscript 1893 |
| C58 | "are not to be accepted as the final decision of their writer" | S | Postscript |
| C59 | Many notes record the "contemporary speech" of Lane's day | S | Postscript: "many of them are clearly the record of contemporary speech, which he would doubtless have excluded" |
| C60 | Meanings "most familiar to the student will often be found missing" | S | Postscript |
| C61 | Haywood called Lane-Poole's estimate inaccurate, and the lexicon "a very inadequate reference work" after قد | S | Haywood p. 125: "showed how inaccurate this statement was … a very inadequate reference work after the article 'qadda'" |
| C62 | قتل precedes قد, yet the main text says "See Supplement", and our entry is that note | S | Print p. 2487 (image); Supplement p. 2984 (image) matches entry 729 word for word |
| C63 | قتل excerpt | S | Entry 729; validator passes |
| C64 | It cites al-Bayḍāwī on Q 4:157 and never glosses the verb as "he killed" | S | Entry 729 "Bd in iv. 156"; `verses` 4:157 contains وَمَا قَتَلُوهُ. The Form I gloss is "He knew the thing" only |
| C65 | Lane shows the recorded range and who records it; he cannot say which sense a verse carries; for *ṣawm* the fasting verses (Q 2:183–187) decide | S | Interpretive, consistent with pp. xxii, xxvi; `verses` 2:183–187 are the fasting passage |
| C66 | A tag dates a book, not a usage; in *ṣawm*, Ibn ʿAbbās reaches Lane through the *Ṣiḥāḥ* | S | Entry 5692: "( S , M ) by I'Ab ( S )" |
| C67 | Bd and Jel are commentators' readings | S | Table p. xxxi: "Exposition of the Kur-án" |
| C68 | Labels such as "language of the law" or "post-classical" mark specialised or later use; their absence proves nothing | S | Interpretive, consistent with pp. xxii, xxvi |
| C69 | onOurSite: stored text = Perseus/Tufts digitisation of the London printing, as corrected on hawramani | S | Perseus biblio note; hawramani page (via an intermediate TXT by Navid-ul-Islam; minor) |
| C70 | ‡ → "(tropical:)", † → "(assumed tropical:)", dash → b2…, double rule → A2… | S | Print pp. 1749–50 against entry 5692; Perseus markers |
| C71 | A stray "CCC" in some entries is not Lane's; it appears to be a digitisation artefact | S | 22 displayed entries; the wording is hedged. Round-1 fix applied |
| C72 | The readable English version drops most source initials and ‡/† labels and can say more than Lane does | S | grep counts above. Swm harmonized: "Lane traces every sense back to a single underlying idea" (not in Lane) |
| C73 | 1,410 roots; 427 qāf–yāʾ from the 1885/1893 parts | S | `roots` count; Part 6 = غ ف only |
| C74 | Nothing in the stored text marks a finished article vs a Supplement note | S | Entry 729 has no marker |
| C75 | A "كفل كفن كفى See Supplement" line points to other roots; it is not part of the entry | S | kfr entry; p. 2487 pattern. (But see site-data issue 7: in mTr the stored text runs on into another root) |
| C76 | Lane's verse numbers often differ; English versions repeat them | S | Swm harmonized "2:181", "19:27"; qtl harmonized "4:156" |
| C77 | Source `lane-poole`: Editor's Preface and Postscript "follow Part 5 in the file labelled 'VOL. 5'" | **NQ** | VOL. 5 page-number map and OCR: they sit at the front of the file (leaves 4–6), after only the Part 5 title page and before the Memoir and the Part 5 lexicon text (pp. 1760ff. from leaf 44). They do not follow Part 5 |
| C78 | Source `dnb`: the DNB dates the last part 1892; the part is dated 1893 | S | Wikisource DNB; Part 8 title page "1893" |
| C79 | Source `lexicon`: page list (pp. 31, 658, 1749, 2487, 2984; Part 8 title page) | S | All viewed as page images |
| C80 | Source `lane-preface`: pp. v–xxxii, dated December 1862 | S | p. xxxii image: "December, 1862. E. W. L." |

**Totals:** 80 claims. 79 supported, 1 needs qualification, 0 unsupported.

## Round-1 flags: status

| Flag | Status |
|---|---|
| C51 (r1): "every article ready" | Fixed. Now attributed, explained by the Ṣiḥāḥ order and "three stages", and set against قتل |
| C11 (r1): "whose voice you are hearing" | Fixed |
| C22 (r1): "Rather than reduce a root to one idea" | Fixed (deleted) |
| C24 (r1): classical age | Fixed ("classical rank" added) |
| C47 (r1): AO report | Fixed |
| C65 (r1): CCC | Fixed |
| Brief: titleGloss | Fixed ("which Lane glossed as…") |
| Brief: "Later senses" | Fixed ("Further down") |
| Brief: "The commonest are" | Fixed ("They include") |
| Brief: harmonized-version warning | Added to onOurSite |

All new claims introduced by the reviser were re-checked (C3, C23, C52, C53, C55, C59, C62, C72, C77). All are supported except the source-list locator (C77).

## Flagged items and fixes

1. **C77 (source citation `lane-poole`, needs qualification).**
   - The citation says both texts "follow Part 5 in the file labelled 'VOL. 5'". In that file they come first:
     - leaf 3: Part 5 title page (1874);
     - leaves 4–5: Editor's Preface;
     - leaf 6: Postscript;
     - leaf 7 onward: Memoir;
     - leaf 44 onward: the lexicon pages of Part 5 (pp. 1760–2219).
   - Round 1 carried the same error.
   - **Fix:** change "where both follow Part 5 in the file labelled 'VOL. 5'" to "where both are printed at the front of the file labelled 'VOL. 5', after the Part 5 title page and before Lane-Poole's Memoir".

## Brief issues

- **suggestion.** The صوم excerpt's first "…" skips "and (S,*M,&c.) by a tropical application, (TA,) ‡ from speech". The print (p. 1749) shows the *Tāj* calling the "from speech" sense tropical (‡), while the Ibn ʿAbbās reading of the verse gets †. The essay's sentence "Lane files Ibn ʿAbbās's reading … under his †" is accurate. But a reader could take "abstaining from speech" as figurative on Lane's judgment alone.
  - Optional, if words allow: add "(the general sense 'from speech' carries ‡, on the *Tāj*'s word)".
  - Otherwise leave as is.
- **suggestion.** The body is at 1,100 words, the upper limit. Any addition must be offset by a cut.
- **suggestion.** The abbreviation paragraph is still list-like. It is acceptable as a reading key; keep it tight.
- **suggestion.** The `lane-preface` source names "the transcription at laneslexicon.github.io" without a working deep link. The Preface is at https://laneslexicon.github.io/lexicon/site/lane/preface/ (the site's navigation lists `lane/preface/` and `lane/postscript/`). Either give that URL in the citation text or drop the mention; all checks here were made against the archive.org scans.
- No padding, rankings, generic praise or bare root mentions found. All Arabic quoted in excerpts is from displayed entries. The one Arabic-derived translation in running text (al-Rāghib) is labelled "(our translation)".

## URLs

- https://archive.org/details/LAB1865AREN: opens; Lane, Librairie du Liban reprint, 8 files. Used for `lane-preface`, `lexicon` and `lane-poole`.
- https://en.wikisource.org/wiki/Dictionary_of_National_Biography,_1885-1900/Lane,_Edward_William: opens; DNB vol. 32, by Stanley Lane-Poole.
- https://archive.org/details/in.gov.ignca.12555: opens; Haywood, *Arabic lexicography*, 1960.
- http://www.perseus.tufts.edu/hopper/text?doc=ASl&fromdoc=Perseus:text:2002.02.0015: opens; the Lane text with the note "London. Williams and Norgate. 1863." and the CC BY-SA licence.
- https://arabiclexicon.hawramani.com/william-edward-lane-arabic-english-lexicon/: opens; states the Tufts source, the Navid-ul-Islam TXT and its corrections.
- No listed source is unused.

## Validator

`node scripts/validate-dictionary-guides.mjs lane-lexicon` → **ok**: 4 root links (4 distinct pairs), 3 excerpts, 1,100 words (lede + body), example roots Swm, Hnf, qtl; 1/1 guides pass.

## Site-data issues (report only; not for this guide to fix)

1. **`name_ar` = "Lane's Lexicon".** That is not an Arabic title. Lane's Arabic title is مدّ القاموس (Preface p. xxxii; 1863 title page).
2. **Stored date 1876** is Lane's death year. That is fine for ordering. The posthumous parts appeared 1877–93.
3. **"CCC" artefacts** appear in 22 displayed Lane entries (e.g. kfr, jEl).
4. **The Swm harmonized English (the default view) attributes to Lane things he does not say:**
   - "Throughout, Lane traces every sense back to a single underlying idea";
   - "all built on the idea of stillness/holding-back";
   - "Lane reports this as the primary, original meaning" (this is the *Tāj*'s statement, tagged TA).
5. **Harmonized texts repeat Lane's verse numbers** (Swm "Qur'an 2:181", "Qur'an 19:27"; qtl "Qurʾan 4:156"). As verse links they point to the wrong verses; they should be Q 2:185, 19:26 and 4:157.
6. **The qtl harmonized text cites "Kashshaf"** as a source. Lane's entry (entry 729; print p. 2984) cites only Bd, K, TA, Msb, A, S, JM, Mgh and El-Jurjánee. The *Kashshāf* is an invented attribution.
7. **Segmentation errors: some stored Lane entries run on into another root's article.**
   - mTr continues after "مطس &c. See Supplement" with the article مظ ("The pomegranate-tree …").
   - kns appears to contain "كنس كنيس …" material after its "See Supplement" line.
