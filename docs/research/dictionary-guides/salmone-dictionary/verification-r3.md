# Verification round 3: salmone-dictionary

Verifier: independent fact-check agent (round 3), 2026-09-26.
Page checked: `roots/frontend/src/content/dictionary-guides/guides/salmone-dictionary.ts` (revision after r2).
I did not open research-notes.md or any revision-*.md file. I read verification-r2.md for its list of flags only. Every verdict below rests on evidence I opened myself in this round.

## Evidence opened in this round

- **1890 print, vol. 1** (Trübner, London), Internet Archive `arabicenglishdic0000unse`: https://archive.org/details/arabicenglishdic0000unse
  - IA metadata: "An Arabic-English Dictionary on a New System Vol. 1", H. Anthony Salmone, Trubner & Co., 1890.
  - Full OCR (`_djvu.txt`), and `_page_numbers.json` for mapping leaves to printed pages.
  - Page images I viewed myself: n6 (title page), n11 (p. x), n13 (Table of Arabic Derived Forms), n14 ("Notes"), n16 (p. xv, Explanatory Notes 1–3), n18 (p. xvii, notes 9–13), n47 (p. 22, أمن), n185 (p. 160, حنف), n282 (p. 257, ربب), n482 (p. 457, صلو), n483 (p. 458, صلي), n515 (p. 490, طبع), n516 (p. 491, طبع cont.). Preface pp. vii–ix read in the OCR; the page heads "VIII PREFACE" and "PREFACE. IX" are in the OCR.
- **Perseus text 2002.02.0005**: main page (imprint and NSF lines) and root pages rbb, dnw, dny and Slw, fetched with curl.
- **arabiclexicon.hawramani.com** Salmoné dictionary page (fetched).
- **Library of Congress** nr90023582: the `.json` record opens. The `.html` URL returns 403 to curl (Cloudflare bot check).
- **Open Library** OL15560928M: the `.json` record opens. The HTML URL redirects curl to `verify_human`.
- **Haywood, *Arabic Lexicography*** (IA `in.gov.ignca.12555`, OCR): p. 109 (al-Bustānī) and p. 124 (Lane and the Tāj). I checked the page heads: "lOy" = 109 between the 108 and 114 heads; "124" is printed before the Lane passage. No mention of Salmoné anywhere in the OCR.
- **Wikidata Q53421609** (JSON): born 1860-09-01, died 1904-10, with 0 references on each claim. **Sue Young Histories** page "Habib Anthony Salmone (1830-1895)" (2013-11-26): gives 1830–1895, and cites JRAS and *The Academy* vol. 46 p. 556 for his professorship, not for the dates.
- **Site entries** via `_dict_guide_tool.py`:
  - Salmoné entries: Amn = 9, rbb = 129, TbE = 6655, Hnf = 6345, Slw = 1398, dnw = 1000.
  - Lane entry: Hnf = 6343.
  - Greps over all displayed Salmoné entries: Mussulman (3 entries, incl. slm "N. Ag. أسلم a. Mussulman, Moslem, Muslim"); `_ast;` (24 entries, every one mid-entry before a verb form); ڤ (about 80 entries); Lane, Qamus, Taj, Koran/Qur, Freytag, Dozy, Bustani (0 each). The poet, verse and tradition hits are all glosses.
  - `find-root دني` finds no match.
- **Qur'an text** (local API): Q 4:155, 9:61, 4:23, 3:79, 5:44, 5:63, 3:67.
- **Web search**: unavailable, because the session's search budget was exhausted. Everything above was opened directly by URL.

## Status of the round-2 flags

| r2 flag | Now reads | Verdict |
|---|---|---|
| C16 (NQ, locator): preface date and place cited only to p. vii | `[^salmone-1890\|p. x]` now follows "signed at University College on 21 November 1889," | **Resolved: S.** Image n11: head "X PREFACE."; foot "H. ANTHONY SALMONÉ. / 21st November 1889. / UNIVERSITY COLLEGE, / LONDON." |
| (optional) "(a), (b), (c) number the senses" | `[^salmone-1890\|"Notes", before p. xv]` | **Resolved: S.** Image n14, Notes item 4: "(a), (b), (c) &c. represent the 1st, 2nd, 3rd &c. meanings of the verb or derived form." n14 comes before n16 (p. xv). |
| C71 (NQ): "Perseus set a reconstructed Arabic form beside…" | "The Perseus text sets a reconstructed Arabic form beside each of the print's pattern numbers and Roman numerals" | **Attribution resolved, but the claim still needs qualification for a different reason** (see C74 and flag 1). The print itself already writes out the Arabic word beside a bracketed number in defective and hamzated roots (Expl. note 15a.1; pp. 457–458). So Perseus's form is not a reconstruction "beside each" number. |
| C25 (U): gbooks source | deleted | **Resolved.** There is no `gbooks` id or marker left in the file. "Reissued in the 1970s" rests on OL (1972), verified. |
| Lede wording: "a few compact lines" | "packs a whole root into one compact article" | **S.** p. xvii (note 10) calls each root's treatment an "article"; p. 257 shows the ربب article in about 45 short column lines. "Compact" is loose but fair for the book's design (preface: "portable form"). |
| Summary wording | "with terse English equivalents" | **S.** |

## Claims table (whole page re-verified)

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title "An Advanced Learner's Arabic-English Dictionary" | S | OL15560928M title (Beirut: Librairie du Liban, 1972); Perseus header |
| C2 | titleGloss: first published as *An Arabic-English Dictionary on a New System* (London, 1890) | S | title page n6: "AN ARABIC-ENGLISH DICTIONARY ON A NEW SYSTEM … LONDON: TRÜBNER & CO., LUDGATE HILL. 1890."; LC note "His An Arabic-English dictionary on a new system, 1890" |
| C3 | author "H. Anthony Salmoné" | S | title page "BY H. ANTHONY SALMONÉ" |
| C4 | authorFull "Habib Anthony Salmoné" | S | LC JSON: "Salmoné, H. Anthony (Habib Anthony)"; 400 "Salmoné, Habib Anthony" |
| C5 | period "preface dated 1889; published 1890" | S | p. x "21st November 1889"; title page 1890 |
| C6 | kind "Learner's Arabic–English dictionary" | S | title page "VOL. I. ARABIC-ENGLISH"; preface pp. vii–viii ("ordinary student", "the beginner", "the learner") |
| C7 | summary: compact dictionary for students, published in London in 1890 | S | title page; p. vii ("portable form … within the reach of all students") |
| C8 | summary: verbs, nouns, plurals and prepositions with terse English equivalents | S | Notes 3–7; pp. 160, 257, 490–491 |
| C9 | summary: classical and nineteenth-century usage side by side | S | Notes 9 ([coll.] = "especially modern or used in the colloquial language only"), Notes 10; p. ix "both classical and modern writing" |
| C10 | summary/lede: no quoted evidence, no named authorities; quotes no poetry or scripture | S | greps of the displayed entries (0 for Koran/Qur, Lane, Qamus, Taj, Freytag, Dozy, Bustani; poet/verse/tradition hits are glosses); print pp. 22, 160, 257, 457, 490–491 show glosses only |
| C11 | lede: lectured on Arabic at University College London | S | title page "ARABIC LECTURER AT UNIVERSITY COLLEGE, LONDON" |
| C12 | lede: wanted a dictionary "comprehensive, handy and cheap" | S | p. vii (verbatim) |
| C13 | lede: packs a whole root into one compact article: verbs, nouns, plurals, prepositions, English equivalents, classical and modern side by side | S | p. xvii note 10 ("The order of each article, i.e. every fresh root"); p. 257 |
| C14 | lede: read it as a quick map of a word family, not a witness to seventh-century meaning | S (editorial) | follows from C10 and C26–C31 |
| C15 | title page: "Arabic Lecturer at University College, London"; professor of Arabic at the School for Modern Oriental Studies set up by the Imperial Institute | S | title page n6: "PROFESSOR OF ARABIC AT THE SCHOOL FOR MODERN ORIENTAL STUDIES, ESTABLISHED BY THE IMPERIAL INSTITUTE" |
| C16 | "(Habib)" [^lc] | S | LC JSON |
| C17 | preface signed at University College on 21 November 1889 [p. x] | S | image n11 |
| C18 | "either too bulky and expensive, and of no practical utility to the ordinary student, or too small and of vocabulary-like dimensions" | S | p. vii (verbatim) |
| C19 | calls Arabic "a living language" [p. vii] | S | p. vii: "it is a living language spoken or understood throughout the world of Islam" |
| C20 | the dictionary sets modern and colloquial meanings beside classical ones | S | Notes 9–10; entry 6655 "[ coll. ], Broke in… (animal)"; p. ix |
| C21 | "new system" of the original title: a number referring to "a table of model forms" instead of printing each noun and plural [p. viii] | S | p. viii: "Instead of giving under each root the various nouns, adjectives &c., with their plurals, I refer by figures to a table of model forms" |
| C22 | seventy patterns such as *faʿīl* and *fuʿalāʾ* [Table] | S | image n13: forms 1–70; 25 = فَعِيل; 43 = فُعَلاء |
| C23 | derived verbs appear only as Roman numerals | S | Notes 5; p. 160 "—V, Belonged to…"; p. 257 "—II, Reared…"; p. 457 "—II, Prayed" |
| C24 | the ḥanīf line reads in full "25, (pl. 43), Mussulman." [p. 160] | S | image n185, lines 61–62: "—25, (pl. 43), Mussulman.—42, Razor." |
| C25 | the site's title is the one used for the 1970s reissue [^openlibrary] and the digitisation [^perseus] | S | OL JSON: 1972, Beirut, Librairie du Liban; Perseus page header. The Perseus rbb and Slw text matches the 1890 print word for word apart from the forms (pp. 257, 457). |
| C26 | "chief aids": Lane "as far as this work has been published", lacking *wāw* and *yāʾ* by his note; Cuche's Arabic–French vocabulary; al-Bustānī's *Muḥīṭ al-Muḥīṭ* [pp. viii–ix] | S | p. viii: "LANE's Arabic-English Lexicon, as far as this work has been published—i.e. excepting the last two letters (و & ي); CUCHE's Vocabulaire arabe-français and the Muhit-ul-Muhit by BUTROS BUSTANY, Beyrout 1869" |
| C27 | checked against Freytag, Kazimirski, Dozy and others | S | pp. viii–ix (also Wahrmund and Richardson, "and others") |
| C28 | added words "hitherto unrecorded" from "both classical and modern writing" | S | p. ix |
| C29 | Lane built his lexicon on the Arabic dictionaries, above all the *Tāj al-ʿArūs* [Haywood p. 124] | S | Haywood p. 124: the Tāj "could best serve as the basis of his lexicon … transcriptions made from the 'Taj', and other dictionaries" |
| C30 | al-Bustānī took over the material of the *Qāmūs* [Haywood p. 109] | S | Haywood p. 109: "He therefore took all the material of the 'Qamus', and supplemented it from other lexicographers" |
| C31 | "The contents are openly second-hand"; glosses reach the classical lexicons "at one or two removes, condensed again" | S (interpretation) | follows from C26, C29 and C30. The preface names its aids openly. See brief issue 3 on the one exception (his own additions). |
| C32 | fixed article order: basic verb, derived verbs, nouns and adjectives, participles and verbal nouns, other words, idioms [p. xvii] | S | image n18, note 10. Simplified: step 2 (the root with kasra or damma) is omitted, and steps 6–7 are merged as "other words". |
| C33 | (a), (b), (c) number the senses ["Notes"] | S | image n14, item 4 |
| C34 | "the first meaning given in the root is invariably the most important one, and the one that generally runs throughout…" [p. xv] | S | image n16 (first page of Explanatory Notes; the next page is headed XVI): verbatim |
| C35 | "n. ac." ("noun of action") introduces verbal nouns; "N. Ag." and "N. P." mark active and passive participles | S | Notes 3 and 6 (image n14) |
| C36 | a bracketed preposition such as [Bi] or ['Ala] says what a verb takes | S | Notes 7; Expl. note 2 (image n16) |
| C37 | P. (Persian), T. (Turkish) flag words derived from another language | S | Notes 8: "showing that the word is derived from that language" |
| C38 | "[coll.]" = "especially modern or used in the colloquial language only" | S | Notes 9 (verbatim) |
| C39 | asterisk = "that the root or most of the derived forms are used in the modern language" | S | Notes 10 (verbatim) |
| C40 | "Both marks are coarse" | S (interpretation) | Notes 10 (the asterisk covers a whole root); p. 491, where printing words carry no mark |
| C41 | ط ب ع: the verb the Qur'an uses of God sealing hearts (Q 4:155), glossed "Stamped, sealed; made an impression or mark on; printed (book)" | S | Q 4:155 *bal ṭabaʿa llāhu ʿalayhā bi-kufrihim*; entry 6655; p. 490 |
| C42 | "Printing-press" carries no [coll.] | S | entry 6655 "مِطْبَعَة (pl. مَطَاْبِعُ) a. Printing-press."; p. 491 "—20t, (pl. 44), Printing-press." |
| C43 | in the print the only covering mark is the asterisk beside the root [pp. 490–491] | S | image n515: "*" beside طبع; image n516: no mark on printing words |
| C44 | our copy drops that asterisk | S | entry 6655: no asterisk, no `_ast;` |
| C45 | أ م ن: Salmoné separates two constructions of *āmana* (excerpt) | S | entry 9 (verbatim); p. 22 "IV [acc. or bi], Believed, had faith in; … —(c) [La], Trusted himself to, was led by." |
| C46 | he cites no verse; Q 9:61 uses both constructions (*yuʾminu bi-llāhi wa-yuʾminu li-l-muʾminīna*); translation labelled | S | Q 9:61 text; entry 9 |
| C47 | ر ب ب excerpt 1 | S | entry 129 (verbatim); p. 257 |
| C48 | by his own rule "lord, master, owner" is the most important sense | S | p. xv; entry order |
| C49 | nothing in the entry relates lordship to rearing or arranging | S | entry 129; p. 257 |
| C50 | *rabb* "Lord, master; owner, possessor; proprietor"; *rubb* "Syrup; preserve"; *ribāb*, marked P., "A kind of viol; violoncello" | S | entry 129; p. 257 ("—23, Tithe, tenths.—(b), P., A kind of viol; violoncello") |
| C51 | nothing marks which sense belongs to which period | S | p. 257: no asterisk at ربب, no [coll.] in the article |
| C52 | ر ب ب excerpt 2 | S | entry 129 (verbatim) |
| C53 | *rabāʾib* is the word of Q 4:23, "your step-daughters in your care" (labelled) | S | Q 4:23 *wa-rabāʾibukumu llātī fī ḥujūrikum* |
| C54 | plural of *rabbānī* in Q 3:79, 5:44, 5:63 | S | *rabbāniyyīn* (3:79), *al-rabbāniyyūn* (5:44, 5:63) |
| C55 | three glosses with no indication of which belongs where or when; "Doctor of the sacred law" sounds like a scholar's title, and the entry does not date it | S | entry 129; p. 257 "—33yi, Doctor of the sacred law.—(b), Rabbi; teacher.—(c), Divine." Hedged wording. |
| C56 | "see 23tb" is a trace of the print's "see 23t.—(b)"; (a) = *ribāba* "Lordship, dominion, power, authority"; (b) "Divinity, godhead" [p. 257] | S | image n282: "—27yit, see 23t.—(b), Divinity, godhead."; "—23t, Lordship, dominion, power, authority."; table 23 = فِعَال, t = ة |
| C57 | ح ن ف excerpt | S | entry 6345 (verbatim); p. 160 |
| C58 | "Mussulman" is his ordinary English for *muslim*; the plural note uses مُسْلِم "Mussulman" [p. xvii] | S | image n18, note 13: "مُسْلِم Mussulman, pl. مُسْلِمُونَ (nom.)"; stored slm "N. Ag. أسلم a. Mussulman, Moslem, Muslim" |
| C59 | the entry makes *ḥanīf* another word for *muslim*, yet Q 3:67 sets *ḥanīfan musliman* side by side (labelled) | S | Q 3:67; entry 6345 |
| C60 | Lane, one of the chief aids, records that sense and qualifies it (excerpt) | S | p. viii; entry 6343 (verbatim; the validator passes) |
| C61 | the abbreviations name Lane's Arabic sources; "a conventional term of the professors" read (labelled) as technical usage of scholars | S | entry 6343 "( S , Mgh , Msb ;)"; the reading is marked "we read" |
| C62 | Lane gives other explanations, from "inclining to a right state or tendency" to pilgrimage and circumcision, each tied to a source | S | entry 6343: "Inclining to a right state or tendency: ( Er-Rághib , TA :)"; pilgrimage "( As , K , TA :)"; circumcision "( TA :)", "accord. to Akh" |
| C63 | Salmoné keeps one English word, with no sign of origin or age | S | entry 6345; p. 160 |
| C64 | "The book's economy can flatten a contested word. One example is…" | S | framed as one example |
| C65 | How to use: fast survey of verb forms, prepositions, plurals, modern meanings | S | C8, C9 |
| C66 | "It gives no evidence, and its classical material is second-hand" | S (see brief issue 3) | C10, C26. The preface also claims "several words hitherto unrecorded" from his own reading. |
| C67 | "flags modern usage only coarsely, and our copy loses part of that marking" | S | C40, C44, C79 |
| C68 | its date is that of the compilation, not of the meanings | S (editorial) | preface |
| C69 | onOurSite: 948 roots from the Arabic–English volume | S | `_dict_guide_tool.py dicts` (948); title page "VOL. I. ARABIC-ENGLISH" |
| C70 | onOurSite: the Perseus text, which hawramani took via the Alpheios Project [^hawramani] | S | hawramani page: "sourced from the Alpheos Project and originally provided by Tufts University"; Perseus rbb and Slw match the stored text apart from numbers |
| C71 | Perseus imprint "Beirut. Librairie du Liban. 1889" is not that of the London original [^perseus] | S | Perseus main page (verbatim); title page London 1890 |
| C72 | Perseus sets an Arabic form beside Roman numerals and pattern numbers (e.g. "رَبَّبَ II", "رُبُوْب 27") | S | Perseus rbb |
| C73 | our copy keeps the forms but drops most numbers and the present-tense vowel letters | S | Perseus "رَبَّ U ( n. ac. رَبّ 1 )" vs stored "رَبَّ(n. ac. رَبّ)"; some numbers survive (stored "أَرْبَاْب 38", "مَطْبَعَة 17t"); Notes 1 (A/I/U = aorist vowel) |
| C74 | **"a reconstructed Arabic form beside *each* of the print's pattern numbers and Roman numerals"** | **NQ** | Overgeneralised. In defective and hamzated roots the 1890 print itself writes the Arabic word out with the number in brackets (Expl. note 15a.1: "the word is generally written out with the number of form given in brackets"). p. 457 prints صَلًا [4A], صَلَاة [4tA], مُصَلًّى [N.P.II]; p. 458 prints صَلًى [5], مِصْلَاة [20tA]. Perseus's forms in those places come from the print, not from reconstruction. Where the print gives a bare number (e.g. "—II, Prayed" p. 457; all of p. 257), the form is not in the print and was supplied later. Who supplied it is unknown. |
| C75 | cross-references survive; "see V" = the fifth-form verb in the same entry | S | entry 129 "إِرْتَبَبَa. see V"; print p. 257 "—VIII, see V."; Notes 5 |
| C76 | a stray ڤ marks a garbled form | S | entry 129 "N. P. رَبڤبَ" (print "N.P.I"); the same in Perseus; about 80 displayed entries contain ڤ |
| C77 | empty [] once held a pattern number | S | Perseus Slw "[ 4A ]", "[ 38A ]", "[ 4tA ]" and dnw "[ 22t ]", "[ 27 ]" vs stored "[]" (entries 1398, 1000); print p. 457 "[4A]", "[38A]", "[4tA]" |
| C78 | under ص ل و, صَلَّوَ stands for صَلَّى | S | entry 1398 and Perseus Slw "صَلَّوَ II"; print p. 457 has only "—II, Prayed" |
| C79 | "_ast;" is the print's modern-usage asterisk, kept before some forms but dropped from root headings | S | Notes 10; 24 stored occurrences, all mid-entry before a verb form; root asterisks in print at أمن (p. 22), طبع (p. 490), صلا (p. 457), absent in stored entries 9, 6655, 1398 |
| C80 | some roots ending in *wāw* or *yāʾ*, such as د ن و, show one line; in Perseus the rest, *dunyā* ("world") included, sits under دني, which our site does not display [^perseus\|roots dnw and dny] | S | entry 1000 (one line); Perseus dnw (one line) and dny ("دُنْيَا ( pl. دُنَي 9 ), a. World, this present world"); `find-root دني` finds no match |
| C81 | limitedEvidence: no scholarly study of this dictionary found | S (as the team's search report) | I could not re-run a web search (budget exhausted). Haywood (1960) never mentions Salmoné, and nothing else I opened points to a study. Worded as "we found". |
| C82 | limitedEvidence: online dates disagree, most give no source, none checkable; page gives none | S | Wikidata 1860-09-01 to 1904-10 (0 references); Sue Young Histories "(1830-1895)" (its citations support the professorship, not the dates) |
| C83 | limitedEvidence: rests on the book's title page, preface, notes and displayed entries | S | matches the citations used (Haywood is used only for Lane and al-Bustānī) |
| C84 | source salmone-1890 (2 vols, Trübner 1890; title page, preface pp. vii–x, Table, "Notes", explanatory notes pp. xv–xxi, entries) | S | IA metadata; title page "IN TWO VOLUMES"; heads VIII, IX, X, XVI, XVII…XXI; n14 "Notes" |
| C85 | source openlibrary (Beirut: Librairie du Liban, 1972, xxiii, 1252, 179 p.) | S | OL JSON (verbatim pagination "xxiii, 1252, 179 p.") |
| C86 | source perseus (text 2002.02.0005; bibliographic and funding statement; root entries) | S | Perseus main page ("The National Science Foundation provided support for entering this text"); rbb, dnw, dny |
| C87 | source haywood (Brill, 1960) | S | IA `in.gov.ignca.12555`: "Arabic lexicography", Haywood, 1960 |
| C88 | source hawramani | S | page title "Habib Anthony Salmoné, An Advanced Learner's Arabic-English Dictionary (1889)" |
| C89 | source lc | S | LC JSON record nr90023582 |

**Totals: 89 claims. 88 supported, 1 needs qualification (C74), 0 unsupported.**

## Flagged items and concrete fixes

1. **C74 (NQ).** onOurSite says "The Perseus text sets a reconstructed Arabic form beside each of the print's pattern numbers and Roman numerals". This is not true of every number.
   - In the 1890 print, defective and hamzated roots already give the Arabic word written out with its number in brackets. Expl. note 15a.1 says so, and pp. 457–458 show صَلًا [4A], صَلَاة [4tA], مُصَلًّى [N.P.II], صَلًى [5], مِصْلَاة [20tA].
   - Only bare numbers and Roman numerals (e.g. p. 257 throughout; "—II, Prayed" on p. 457) had no printed form.
   - Your own example, empty `[]`, comes from such a bracketed, already-written-out case.
   - **Fix:** "Where the print gives only a pattern number or a Roman numeral, the Perseus text sets an Arabic form beside it; our copy keeps the forms but drops most numbers and the present-tense vowel letters." The following sentence can stay: "Some reconstructions misfire: a stray ڤ…"
   - Alternatively, keep the sentence and change "each of" to "most of".

## Brief issues (not factual)

1. **suggestion:** Lede and body come to 1,088 words (validator), at the top of the 700–1,100 range. The depth is legitimate because it comes from the book's own preface, notes and printed pages, not from padding. Biography is correctly kept to the title page.
2. **suggestion:** onOurSite is about 155 words, slightly above FORMAT's ≈60–150. If the C74 fix adds words, compensate: the "_ast;" sentence or the صَلَّوَ example could be shortened.
3. **suggestion:** In "How to use it", "its classical material is second-hand" is slightly absolute. The preface (p. ix) claims "several words hitherto unrecorded" from his own "careful reading of both classical and modern writing", and the body already reports this. "Largely second-hand" or "mostly second-hand" would match the body.
4. No generic praise, ranking or padding was found. The page does not force a root-meaning narrative, and it explicitly reports that Salmoné gives lists, not arguments. Every root mention is linked (7 links, all to displayed entries), and every translation made for the guide is labelled. The page promises nothing our copy lacks: the دني material is explicitly flagged as not displayed.

## Source URLs

| id | URL | Status |
|---|---|---|
| lc | https://id.loc.gov/authorities/names/nr90023582.html | The HTML returns 403 to curl (Cloudflare bot check). The same record's `.json` opens and is the stated record. It should open in a normal browser. |
| salmone-1890 | https://archive.org/details/arabicenglishdic0000unse | 200. It is vol. 1 (Arabic–English), Trübner 1890. All locators confirmed: title page; pp. vii, viii, viii–ix, x; Table; "Notes"; xv; xvii; xv–xxi; 160; 257; 490–491. |
| openlibrary | https://openlibrary.org/books/OL15560928M | The HTML redirects curl to `verify_human` (bot check). The `.json` opens and is the stated 1972 record. It should open in a browser. |
| perseus | https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A2002.02.0005 | 200. The imprint and NSF lines are present. |
| haywood | https://archive.org/details/in.gov.ignca.12555 | 200. pp. 109 and 124 confirmed. |
| hawramani | https://arabiclexicon.hawramani.com/habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary/ | 200. It states the Alpheios/Tufts provenance. |

Every listed source is cited in the text and was consulted. None is unusable.

## Validator

`node scripts/validate-dictionary-guides.mjs salmone-dictionary` gave: **ok**. It found 7 root links (7 distinct pairs), 5 excerpts, 1,088 words, example roots TbE, Amn, rbb, Hnf, Slw and dnw, and 1/1 guides pass.

## Site-data issues (report only; not edited)

1. **The stored date 1889 is not a death year.** It is the preface date (21 Nov 1889) and the year in the Perseus imprint. The book was published in London in 1890. The compiler's death year is unestablished: unsourced online records give 1895 or 1904. The panel orders works by death year, so this entry's position rests on a publication-era date.
2. **The stored title is the reissue title** (Librairie du Liban, 1972). The original title is *An Arabic-English Dictionary on a New System* (London: Trübner, 1890).
3. **The stored text drops the print's root-level asterisk** (the modern-use marker). This is visible at أمن p. 22, طبع p. 490 and صلا p. 457. Mid-entry asterisks survive only as the literal string `_ast;` (24 entries).
4. **The Harmonized English for Amn (entry 9) and rbb (entry 129) calls the work an "English–Arabic learner's dictionary".** It is Arabic–English.
5. **The Harmonized English for TbE (entry 6655) adds material the original lacks.** It ends with an interpretive paragraph ("The entry ties the abstract senses together…") and labels the printing words "modern derivatives". Salmoné's entry has neither. His only mark there is the root asterisk, which our copy drops.
