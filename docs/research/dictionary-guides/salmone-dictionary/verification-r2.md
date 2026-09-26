# Verification round 2: salmone-dictionary

Verifier: independent fact-check agent (round 2), 2026-09-26.
Page checked: `roots/frontend/src/content/dictionary-guides/guides/salmone-dictionary.ts` (the revised version).
I did not open research-notes.md or any revision-*.md file. I read verification-r1.md only for the list of earlier flags. Every verdict below rests on sources I opened myself in this round.

## Primary evidence used in this round

- **Print scan, vol. 1** (London: Trübner, 1890): https://archive.org/details/arabicenglishdic0000unse
  - IA metadata: title "An Arabic-English Dictionary on a New System Vol. 1", Trubner & Co., 1890.
  - Full OCR (`_djvu.txt`): title page, preface pp. vii–x, Notes, explanatory notes pp. xv–xxi.
  - `_page_numbers.json`, for mapping leaves to printed pages.
  - Page images I viewed myself:
    - n9: p. viii
    - n13: Table of Arabic Derived Forms
    - n23: p. xxii, "The Alphabet", which shows the notes end on p. xxi
    - n47: p. 22
    - n185: p. 160
    - n282: p. 257
    - n515: p. 490
    - n516: p. 491
    - n620: p. 595
- **Perseus text 2002.02.0005.** I fetched the main page (imprint line) and the root pages rbb, dnw, dny and Slw.
- **Library of Congress record nr90023582** (JSON).
- **Open Library record OL15560928M** (JSON).
- **Haywood, *Arabic Lexicography***, IA OCR, pp. 109 and 124 (page heads checked).
- **hawramani** Salmoné dictionary page.
- **Wikidata Q53421609** (JSON), the **Wikisource author page** (raw), and the **Sue Young Histories** page "Habib Anthony Salmone (1830-1895)" (found through the site's RSS feed and opened).
- **Site entries** via `_dict_guide_tool.py`:
  - Salmoné entries: Amn = 9, rbb = 129, TbE = 6655, Hnf = 6345, Slw = 1398, dnw = 1000 and Elm.
  - Lane entry: Hnf = 6343.
  - Greps over all 948 displayed Salmoné entries for `_ast;`, `coll.`, `ڤ`, Kor/Qur, authority names and Mussulman/Muslim.
  - `find-root دني` returns no match.
- **Google Books** (-pcOAAAAYAAJ and MS4KAQAAIAAJ): I could **not** open either.
  - Both redirect to Google's "sorry" (CAPTCHA) page.
  - The Books API returns 429.
  - I did not attempt to get past the CAPTCHA.

## Status of round-1 flags

| r1 flag | Now reads | Verdict |
|---|---|---|
| C60 (U) "Ignore the string _ast;" | "'_ast;' is the print's modern-usage asterisk, kept before some forms but dropped from root headings." | **Resolved: S.** Notes item 10 defines the asterisk. On p. 595 there is "* (ـِ) A … Knew", which our Elm entry stores as "_ast; عَلِمَ". Asterisks sit beside the roots أمن (p. 22) and طبع (p. 490), but stored Amn and TbE have none. Of 24 stored `_ast;` occurrences, all are mid-entry and none is at a heading. |
| C31 (NQ) [coll.] "warning … not a guarantee" | Both marks quoted; "Printing-press" carries no [coll.]; the print's only covering mark is the root asterisk, which our copy drops | **Resolved: S.** p. 490: "*" beside طبع. p. 491: "—20t, (pl. 44), Printing-press." with no mark. Entry 6655 has no asterisk. |
| C50 (NQ) "only some of the time" | "only coarsely, and our copy loses part of that marking" | **Resolved: S.** |
| C42 (NQ) "later learned title" | "sounds like a scholar's title, and nothing in the entry says whether the word meant that in the Qur'an's time" | **Resolved: S.** |
| C55 (NQ) Perseus "spelled out" numbers | "Perseus set a reconstructed Arabic form beside each …" | **Partly resolved.** "Beside" is now correct, since Perseus rbb has "رَبَّبَ II", "رُبُوْب 27". But the page now credits Perseus with adding the forms, and I found no evidence of who added them. See flag 2. |
| C61 (NQ) dnw "rest" | "…in the Perseus text the rest, *dunyā* ('world') included, sits under دني, a spelling our site does not display" | **Resolved: S.** Perseus dny has "دُنْيَا ( pl. دُنَي 9 ), a. World, this present world". `find-root دني` finds no match. |
| C63 (NQ) dates | "the few online records of his dates disagree with one another, most give no source, and we could not check any of them" | **Resolved: S.** Wikidata gives born 1860-09-01, died 1904-10, with 0 references. Sue Young Histories gives "(1830-1895)" and names an obituary in *The Academy* vol. 46, p. 556. So the records do disagree. r1's claim that they agree was wrong, because it missed the blog. |
| C64 (NQ) notes pp. xv–xix | "pp. xv–xxi" | **Resolved: S.** The OCR page heads run XVI … "EXPLANATORY NOTES. XXI". Leaf n23 (p. xxii) is "The Alphabet". |

## Claims table (whole essay re-verified)

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title "An Advanced Learner's Arabic-English Dictionary" is the reissue and digitised title (title, body) | S | OL15560928M (Beirut: Librairie du Liban, 1972); Perseus page header |
| C2 | titleGloss: first published as *An Arabic-English Dictionary on a New System* (London, 1890) | S | IA metadata; title page OCR ("LONDON … 1890", "IN TWO VOLUMES"); LC note "His An Arabic-English dictionary on a new system, 1890" |
| C3 | author "H. Anthony Salmoné" | S | title page "BY H. ANTHONY SALMONÉ" |
| C4 | authorFull "Habib Anthony Salmoné" | S | LC nr90023582: "Salmoné, H. Anthony (Habib Anthony)" |
| C5 | period: preface dated 1889, published 1890 | S | p. x "21st November 1889"; title page 1890 |
| C6 | kind: learner's Arabic–English dictionary | S | preface pp. vii–viii ("ordinary student", "the beginner", "the learner") |
| C7 | summary: compact student dictionary published in London in 1890 | S | title page; preface p. vii ("portable form") |
| C8 | summary/lede: verbs, nouns, plurals and prepositions, with classical and modern side by side | S | Notes 5–10; pp. 160, 257, 490–491; preface p. ix |
| C9 | summary/lede: quotes no poetry or scripture, names no authorities | S | Grep of 948 displayed entries: 0 match Kor/Qur/Koran. The 6 "authority" hits are "planet" (Saturn and others), not authorities. The "verse" hits are glosses. Print pp. 22, 160, 257, 490 show glosses only. |
| C10 | lede: lectured on Arabic at UCL | S | title page "ARABIC LECTURER AT UNIVERSITY COLLEGE, LONDON" |
| C11 | lede: "comprehensive, handy and cheap" | S | p. vii |
| C12 | lede: "packs a whole root into a few compact lines" | S (loose) | Print rbb is about 30 narrow column lines (p. 257), and علم runs longer. "A few" is figurative but tolerable. |
| C13 | lede: read as a map of a word family, not a witness to seventh-century meaning | S (editorial) | follows from C9 and C19 |
| C14 | title page: Arabic Lecturer at UCL; professor of Arabic at the School for Modern Oriental Studies set up by the Imperial Institute | S | title page OCR ("ESTABLISHED BY THE IMPERIAL INSTITUTE"); LC note |
| C15 | "(Habib)" [^lc] | S | LC JSON |
| C16 | preface "signed at University College on 21 November 1889" | **NQ (locator)** | The fact is true: p. x has "H. ANTHONY SALMONÉ. 21st November 1889. UNIVERSITY COLLEGE, LONDON." But the only citation in the sentence is p. vii, which does not show the date. |
| C17 | "either too bulky and expensive … vocabulary-like dimensions" | S | p. vii |
| C18 | "a living language" | S | p. vii ("it is a living language spoken or understood throughout the world of Islam") |
| C19 | the dictionary sets modern and colloquial meanings beside classical ones | S | Notes 9 and 10; p. ix; 321 displayed entries carry "coll." |
| C20 | "new system": numbers refer to "a table of model forms" | S | p. viii (image n9) |
| C21 | seventy patterns, such as *faʿīl* and *fuʿalāʾ* | S | Table image n13: forms 1–70; 25 = فَعِيل; 43 = فُعَلَاء |
| C22 | derived verbs appear only as Roman numerals | S | Notes 5; p. 160 ("—V, Belonged to…"); p. 257 ("—II, Reared…") |
| C23 | the ḥanīf line reads in full "25, (pl. 43), Mussulman." (p. 160) | S | p. 160 image, lines 61–62 |
| C24 | reissued in the 1970s [^openlibrary][^gbooks] and digitised [^perseus] | S | OL: 1972, xxiii, 1252, 179 p.; Perseus. (The gbooks half of the citation could not be checked; see C25.) |
| C25 | source gbooks: "Google Books record … (al-Biruni, 1976)" | **U (unverifiable)** | Both Google Books records redirect to Google's CAPTCHA "sorry" page, and the API returns 429. I could not see the publisher or year. Nothing on the page depends on it, because OL already supports C24. |
| C26 | chief aids: Lane "as far as this work has been published", lacking *wāw* and *yāʾ*; Cuche's Arabic–French vocabulary; al-Bustānī's *Muḥīṭ al-Muḥīṭ* | S | p. viii image: "excepting the last two letters (و & ي); CUCHE's Vocabulaire arabe-français and the Muhit-ul-Muhit by BUTROS BUSTANY" |
| C27 | checked against Freytag, Kazimirski, Dozy and others | S | pp. viii–ix (also Wahrmund and Richardson) |
| C28 | "hitherto unrecorded", "both classical and modern writing" | S | p. ix |
| C29 | Lane built on the Arabic dictionaries, above all the *Tāj* | S | Haywood p. 124: the Taj "could best serve as the basis of his lexicon … transcriptions made from the 'Taj', and other dictionaries" |
| C30 | al-Bustānī took over the material of the *Qāmūs* | S | Haywood p. 109: "took all the material of the 'Qamus', and supplemented it from other lexicographers" |
| C31 | glosses reach the classical lexicons "at one or two removes, condensed again" | S (interpretation) | follows from C26, C29 and C30 |
| C32 | fixed article order (p. xvii) | S | Expl. note 10, p. xvii (simplified: it omits the kasra/damma variants of the root) |
| C33 | (a), (b), (c) number the senses | S | Notes 4 (the unnumbered Notes page). The attached locator p. xv covers only the following quotation; see flag 1. |
| C34 | "the first meaning given in the root is invariably the most important one…" (p. xv) | S | Expl. note 1, p. xv (verbatim) |
| C35 | "n. ac.", "N. Ag.", "N. P." | S | Notes 6 |
| C36 | bracketed preposition, e.g. [Bi], ['Ala] | S | Notes 7; Expl. note 2 |
| C37 | P. (Persian) and T. (Turkish) flag words derived from another language | S | Notes 8 ("showing that the word is derived from that language") |
| C38 | "[coll.]" … "especially modern or used in the colloquial language only" | S | Notes 9 (verbatim) |
| C39 | asterisk "that the root or most of the derived forms are used in the modern language" | S | Notes 10 (verbatim); locator "Notes", before p. xv, is correct |
| C40 | "Both marks are coarse" | S (interpretation) | Notes 10: the asterisk covers "the root or most of the derived forms" |
| C41 | TbE: the verb the Qur'an uses of God sealing hearts (Q 4:155), glossed "Stamped, sealed; made an impression or mark on; printed (book)" | S | entry 6655; p. 490; Q 4:155 *bal ṭabaʿa llāhu ʿalayhā bi-kufrihim* |
| C42 | "Printing-press" carries no [coll.] | S | entry 6655 "مِطْبَعَة … Printing-press"; p. 491 "—20t, (pl. 44), Printing-press." |
| C43 | in the print, the only mark covering it is the asterisk beside the root (pp. 490–491) | S | p. 490 image: "*" beside طبع, and no other mark on the printing words |
| C44 | our copy drops that asterisk | S | entry 6655 has no asterisk and no `_ast;` |
| C45 | Amn: Salmoné separates two constructions of *āmana* (excerpt) | S | entry 9 (verbatim); p. 22 ("IV [acc. or bi] … —(c) [La], Trusted himself to") |
| C46 | he cites no verse; Q 9:61 uses both constructions; the translation is labelled | S | Q 9:61 *yuʾminu bi-llāhi wa-yuʾminu li-l-muʾminīna* |
| C47 | rbb excerpt 1 | S | entry 129 (verbatim); p. 257 |
| C48 | by his own rule, "lord, master, owner" is the most important sense | S | p. xv plus entry order |
| C49 | nothing in the entry relates lordship to rearing or arranging | S | entry 129; p. 257 |
| C50 | *rabb* "Lord, master; owner, possessor; proprietor"; *rubb* "Syrup; preserve"; *ribāb*, marked P., "A kind of viol; violoncello" | S | entry 129; p. 257 |
| C51 | nothing marks which sense belongs to which period | S | p. 257: no [coll.] and no asterisk on ربب |
| C52 | rbb excerpt 2 | S | entry 129 (verbatim) |
| C53 | *rabāʾib* is the word of Q 4:23, "your step-daughters in your care" (labelled) | S | Q 4:23 *wa-rabāʾibukumu llātī fī ḥujūrikum* |
| C54 | plural of *rabbānī* in Q 3:79, 5:44, 5:63 | S | Qur'an text (*rabbāniyyīn*, *al-rabbāniyyūn* ×2) |
| C55 | three glosses with no indication of which belongs where or when; "Doctor of the sacred law" sounds like a scholar's title, and the entry does not date it | S | entry 129. The wording is now hedged. |
| C56 | "see 23tb" is a trace of the print's "see 23t.—(b)" (p. 257): (a) = *ribāba*; (b) "Divinity, godhead" | S | p. 257 image: "27yit, see 23t.—(b), Divinity, godhead"; Table 23 = فِعَال, "t" = ة; "—23t, Lordship, dominion, power, authority" |
| C57 | Hnf excerpt | S | entry 6345 (verbatim); p. 160 |
| C58 | "Mussulman" is his ordinary English for *muslim*; the plural note uses مُسْلِم (p. xvii) | S | Expl. note 13, p. xvii ("مسلم Mussulman, pl. مسلمون"); stored slm entry "N. Ag. أَسْلَمَ a. Mussulman, Moslem, Muslim" |
| C59 | Q 3:67 *ḥanīfan musliman* (labelled) | S | Q 3:67 |
| C60 | Lane, one of the chief aids, records the sense and qualifies it (excerpt) | S | p. viii; entry 6343 (text verbatim, validator ok) |
| C61 | the abbreviations name Lane's Arabic sources; "conventional term of the professors" is labelled as our reading | S | entry 6343 (S, Mgh, Msb) |
| C62 | Lane gives other explanations, from "inclining to a right state or tendency" to pilgrimage and circumcision, each tied to a source | S | entry 6343: "Inclining to a right state or tendency: ( Er-Rághib , TA :)"; pilgrimage "( As , K , TA :)"; circumcision "( TA :)" |
| C63 | Salmoné keeps one English word, with no sign of origin or age | S | entry 6345; p. 160 |
| C64 | framing "The book's economy can flatten a contested word. One example is…" | S | framed as one example, not a generalisation |
| C65 | How to use: fast survey; gives no evidence; classical material second-hand | S | C9, C26 |
| C66 | "flags modern usage only coarsely, and our copy loses part of that marking" | S | Notes 9–10; C44, C77 |
| C67 | its date is that of the compilation, not of the meanings | S (editorial) | preface |
| C68 | onOurSite: 948 roots, from the Arabic–English volume | S | `_dict_guide_tool.py dicts`; IA vol. 1 is Arabic–English, pp. 1–1254 |
| C69 | Perseus text, taken by hawramani via the Alpheios Project | S | hawramani: "sourced from the Alpheos Project and originally provided by Tufts University"; Perseus rbb and Slw text is identical to ours apart from the numbers |
| C70 | Perseus imprint "Beirut. Librairie du Liban. 1889" is not that of the London original | S | Perseus main page footer (verbatim); title page London 1890 |
| C71 | "**Perseus set** a reconstructed Arabic form beside each of the print's pattern numbers and Roman numerals" | **NQ** | The Perseus text does carry Arabic forms beside the numbers ("رَبَّبَ II", "رُبُوْب 27", "دَنَاوَة [ 22t ]"), and the 1890 print has numbers only (pp. 160, 257). I found no evidence of who added the forms: Perseus, the Beirut edition it names as its source, or an earlier encoder. |
| C72 | our copy keeps the forms but drops most numbers and the present-tense vowel letters | S | Perseus "رَبَّ U ( n. ac. رَبّ 1 )" vs stored "رَبَّ(n. ac. رَبّ)". Some numbers survive (stored "أَرْبَاْب 38", "مَطْبَعَة 17t"). Notes 1: A/I/U mark the aorist vowel. |
| C73 | cross-references survive; "see V", "see 21 (a)" explained | S | entry 129 "إِرْتَبَبَ a. see V"; entry 6655 "طَابَع a. see 21 (a)" (21 = فاعِل → طابِع (a) "Stamp, seal") |
| C74 | a stray ڤ marks a garbled form | S | entry 129 "N. P. رَبڤبَ" (print "N.P.I"); 197 displayed entries contain ڤ |
| C75 | empty [] once held a pattern number | S | Perseus Slw "[ 4A ]", "[ 38A ]", "[ 4tA ]" vs entry 1398 "[]" |
| C76 | under ص ل و, صَلَّوَ stands for صَلَّى | S | entry 1398 and Perseus Slw "صَلَّوَ II , a. Prayed" |
| C77 | "_ast;" is the print's modern-usage asterisk, kept before some forms but dropped from root headings | S | Notes 10; p. 595 vs stored Elm; p. 22 vs Amn and p. 490 vs TbE (heading asterisks lost); 24 stored occurrences, all mid-entry |
| C78 | dnw shows one line; in Perseus the rest, *dunyā* included, sits under دني, which our site does not display | S | entry 1000; Perseus dnw (one line) and dny; `find-root دني` finds no match |
| C79 | limitedEvidence: no scholarly study of this dictionary found | S (as a search report) | This is worded as the team's own search. My web-search budget was exhausted, so I could not re-run a search. Nothing I opened (Haywood, LC, OL, hawramani, Wikisource) points to one. |
| C80 | limitedEvidence: online dates disagree, most give no source, none could be checked; the page gives none | S | Wikidata 1860–1904 (0 references); Wikisource dates come from Wikidata (the raw page has none); Sue Young Histories "(1830-1895)", naming an *Academy* obituary. 2 of 3 are unsourced. |
| C81 | limitedEvidence: the page rests on the book's title page, preface, notes and displayed entries | S | matches the citations actually used |
| C82 | source salmone-1890 citation (2 vols, Trübner 1890; preface pp. vii–x; notes pp. xv–xxi) | S | IA metadata; OCR page heads; leaf n23 |
| C83 | source openlibrary citation | S | OL JSON: title and subtitle, Beirut, Librairie du Liban, 1972, "xxiii, 1252, 179 p." |
| C84 | source perseus citation (text 2002.02.0005; bibliographic and funding statement; root entries) | S | main page ("The National Science Foundation provided support…"); root pages rbb, dnw, dny |
| C85 | source haywood citation | S | IA in.gov.ignca.12555: "Arabic lexicography", Haywood, 1960 |
| C86 | source hawramani citation | S | page title "Habib Anthony Salmoné, An Advanced Learner's Arabic-English Dictionary (1889)" |
| C87 | source lc citation | S | LC JSON record nr90023582 |

**Totals: 87 claims. 84 supported, 2 need qualification (C16, C71), 1 unsupported (C25).**

## Flagged items and concrete fixes

1. **C16 (NQ, locator).** The body's first section says the preface was "signed at University College on 21 November 1889", but the only citation in that sentence is `[^salmone-1890|p. vii]`, and the date and place are on p. x.
   - **Fix:** change that citation to `[^salmone-1890|pp. vii, x]`, or add `[^salmone-1890|p. x]` right after "21 November 1889,".
   - Optional, same kind: "Letters (a), (b), (c) number the senses" comes from the unnumbered "Notes" page (item 4), not p. xv. Add `[^salmone-1890|"Notes"]` after "senses", or leave it, because the next paragraph cites "Notes".
2. **C71 (NQ).** "Perseus set a reconstructed Arabic form beside each of the print's pattern numbers and Roman numerals" credits Perseus with an editorial act that no source shows. The Perseus text names a Beirut edition as its source, and I could not see that edition.
   - **Fix:** "The Perseus text sets a reconstructed Arabic form beside each of the print's pattern numbers and Roman numerals; our copy keeps the forms but drops most numbers…" Alternatively: "In the Perseus text, each pattern number and Roman numeral has an Arabic form written out beside it…"
3. **C25 (U, unverifiable source).** The gbooks source ("Google Books record … al-Biruni, 1976") could not be opened in this round. Both Google Books records return Google's CAPTCHA page, and the Books API returns 429. I could not confirm the publisher or year.
   - **Fix:** delete the `gbooks` source and its `[^gbooks]` marker. `[^openlibrary]` (1972 reissue, verified) already supports "reissued in the 1970s".
   - If the author wants to keep it, a human should open the record in a browser and confirm "Al-Biruni, 1976" before publishing.

## Brief issues (not factual)

- **suggestion:** Lede and body come to 1,089 words (validator count), at the top of the 700–1,100 range. The depth rests on the book's own preface, notes and entries, which is legitimate even though biography is thin.
- **suggestion:** onOurSite is about 163 words, above FORMAT's ≈60–150. The repair notes (ڤ, empty [], صَلَّوَ, `_ast;`, دني) are useful but dense. Consider cutting the صَلَّوَ example or the "see 21 (a)" gloss.
- **suggestion:** In the lede, "packs a whole root into a few compact lines" is figurative. Large roots run to many printed lines. "A compact paragraph" would be safer.
- **suggestion:** C58 could be strengthened cheaply by citing the stored slm entry ("Mussulman, Moslem, Muslim").
- The page contains no padding, praise or ranking, and does not force a root-meaning narrative. Every root mention is linked and every translation is labelled. The page promises nothing absent from our copy: the دني material is explicitly said not to be displayed.

## Source URLs

| id | URL | Status |
|---|---|---|
| lc | https://id.loc.gov/authorities/names/nr90023582.html | The HTML returns a Cloudflare 403 "Just a moment" page to automated tools. The same record's JSON (`.json`) opens and is the stated record. It should open in a browser. |
| salmone-1890 | https://archive.org/details/arabicenglishdic0000unse | Opens (200). It is vol. 1, Trübner 1890. All page locators confirmed: vii, viii, viii–ix, ix, xv, xvii, "Notes", Table, 160, 257, 490–491, xv–xxi. |
| openlibrary | https://openlibrary.org/books/OL15560928M | Opens (303 to slug URL, then 200). It is the stated 1972 record. |
| gbooks | https://books.google.com/books/about/…?id=-pcOAAAAYAAJ | **Not openable by automated tools** (Google "sorry"/CAPTCHA redirect; API 429). Contents unverified in this round. |
| perseus | https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A2002.02.0005 | Opens. It has the imprint and NSF lines, and the root pages rbb, dnw, dny and Slw were fetched. |
| haywood | https://archive.org/details/in.gov.ignca.12555 | Opens (200). pp. 109 and 124 confirmed. |
| hawramani | https://arabiclexicon.hawramani.com/habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary/ | Opens. It states the Alpheios/Tufts provenance. |

All sources are cited in the text. Only gbooks is unusable for verification.

## Validator

`node scripts/validate-dictionary-guides.mjs salmone-dictionary` gave: **ok**. It found 7 root links (7 distinct pairs), 5 excerpts, 1,089 words, example roots TbE, Amn, rbb, Hnf, Slw and dnw, and 1/1 guides pass.

## Site-data issues

1. **The stored date 1889 is not a death year.** It matches the preface date (21 Nov 1889) and the Perseus imprint year "Beirut … 1889". The book was published in London in 1890. The compiler's death year is unestablished: online records give 1895 or 1904, both without verifiable sources. The panel orders works by death year, so this work's position rests on a publication-era date. That is harmless, but it is not what the column means.
2. **The stored title is the reissue title** (Librairie du Liban 1972). The original title is *An Arabic-English Dictionary on a New System* (1890).
3. **The stored text drops the print's root-level asterisk** (the modern-use marker; e.g. أمن p. 22, طبع p. 490). A mid-entry asterisk survives as the literal string `_ast;` in 24 entries.
4. **The Harmonized English for rbb (entry 129) and Amn (entry 9) calls the work "an English-Arabic learner's dictionary".** It is Arabic–English.
5. **The Harmonized English for TbE (entry 6655) adds material the original lacks.** It ends with an interpretive paragraph that Salmoné's entry does not contain ("The entry ties the abstract senses together…"). It also labels the printing words "modern derivatives", a label the original does not give them. The only mark is the root asterisk, which our copy drops.
