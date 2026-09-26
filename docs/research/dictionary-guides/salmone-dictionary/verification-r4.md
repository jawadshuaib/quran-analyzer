# Verification round 4: salmone-dictionary

Verifier: independent fact-check agent (round 4), 2026-09-26.
Page checked: `roots/frontend/src/content/dictionary-guides/guides/salmone-dictionary.ts` (the revision after r3).
I did not open research-notes.md or any revision-*.md file. I read verification-r3.md for its flags only. Every verdict below rests on evidence I opened myself in this round.

## Evidence opened in this round

- **1890 print, vol. 1** (London: Trübner, 1890), Internet Archive `arabicenglishdic0000unse`. The IA metadata reads: title "An Arabic-English Dictionary on a New System Vol. 1", creator "H. Anthony Salmone", publisher "Trubner & Co.", date 1890.
  - Full OCR (`_djvu.txt`): title page, preface pp. vii–x, Notes, and Explanatory Notes pp. xv–xix.
  - `_page_numbers.json`, used to map printed pages to leaves.
  - Page images I viewed myself:
    - n13: Table of Arabic Derived Forms (70 forms; 23 = فِعَال, 25 = فَعِيل, 43 = فُعَلاء)
    - n47: p. 22, أمن, with an asterisk at the root
    - n185: p. 160, حنف: "25, (pl. 43), Mussulman.—42, Razor"
    - n282: p. 257, ربب, with no asterisk at the root
    - n482: p. 457, صلو/صلا: "*… Hit or hurt in the back.—II, Prayed", and bracketed forms صَلًا [4A], صَلَاة [4tA], مُصَلًّى [N.P.II]
    - n515: p. 490, "* طبع … Stamped, sealed"
    - n516: p. 491: "—20t, (pl. 44), Printing-press." with no [coll.]
    - n864: p. 839, كبر, with the asterisk beside the "(—) U" second-vowel line
- **Perseus text 2002.02.0005**, fetched with curl:
  - The main page gives the imprint "Beirut. Librairie du Liban. 1889." and the line "The National Science Foundation provided support for entering this text."
  - Root pages rbb, Slw, dnw and dny.
- **arabiclexicon.hawramani.com** Salmoné page (200). It says: "The text for this dictionary was sourced from the Alpheos Project and originally provided by Tufts University…"
- **Library of Congress** nr90023582. The `.json` opens (200): "Salmoné, H. Anthony (Habib Anthony)"; "Salmoné, Habib Anthony"; "…new system, 1890". The `.html` returns 403 to curl (bot check).
- **Open Library** OL15560928M. The `.json` opens (200): "An advanced learner's Arabic-English dictionary: including an English index", Beirut, Librairie du Liban, 1972, "xxiii, 1252, 179 p.". The HTML redirects curl to `verify_human`.
- **Haywood, *Arabic Lexicography* (1960)**, IA `in.gov.ignca.12555`, OCR:
  - p. 109 (page head "lOy" = 109): al-Bustānī "took all the material of the 'Qamus', and supplemented it from other lexicographers".
  - p. 124 (head "124"): Lane heard of the *Tāj*, which "could best serve as the basis of his lexicon", and "had transcriptions made from the 'Taj', and other dictionaries".
  - Salmoné is not mentioned anywhere in the OCR.
- **Wikidata Q53421609** (JSON): born 1860-09-01, died 1904-10, with 0 references on each claim.
- **Sue Young Histories** page, "Habib Anthony Salmone (1830-1895)": its citations support his teaching posts, not the dates. The two sets of dates disagree, which confirms the limitedEvidence note.
- **Site entries** via `_dict_guide_tool.py`:
  - Salmoné: Amn = 9, rbb = 129, TbE = 6655, Hnf = 6345, Slw = 1398, dnw = 1000.
  - Lane: Hnf = 6343.
  - Greps over all displayed Salmoné entries:
    - `_ast;`: 24 entries, all mid-entry.
    - Mussulman: 3.
    - Kor|Qur: 0.
    - The hits for Lane|Qam|Taj|Freytag|Dozy|Bust… are all English words such as "bustard" and "robust". The hits for poet/verse/tradition are glosses.
  - `find-root دني`: no match.
  - Shortest displayed w/y-final roots: nsw, nhy, ESw and others run 40–90 characters.
- **Qur'an text** (local API): Q 4:155, 9:61, 4:23, 3:79, 5:44, 5:63, 3:67.
- **Web search**: unavailable, because the session search budget was exhausted. Everything above was opened directly by URL.

## Status of the round-3 flag and suggestions

| r3 item | Now reads | Verdict |
|---|---|---|
| C74 (NQ): "a reconstructed Arabic form beside *each* of the print's pattern numbers and Roman numerals" | "Beside the print's pattern numbers and Roman numerals the Perseus text has Arabic forms; where the print gives only the number, the form was supplied later. Our copy keeps the forms but drops the present-tense vowel letters and most numbers; an empty [] once held one." | **Resolved: S.** In the print, p. 457 writes out صَلًا [4A] and صَلَاة [4tA]; p. 257 gives bare numbers ("—1t, Mistress"). Perseus rbb has "رَبَّة 1t", so that form was supplied after 1890. Perseus Slw has "صَلَاة [ 4tA ]" where stored entry 1398 has "صَلَاة []". Stored "رَبَّ(n. ac. رَبّ)" drops the Perseus "U", while "أَرْبَاْب 38" and "17t" survive. The claim no longer says "reconstructed" or "each". |
| "Some forms misfire…" (the empty-[] example moved) | "a stray ڤ marks a garbled form, and under ص ل و صَلَّوَ stands for صَلَّى" | **S.** Entry 129 "N. P. رَبڤبَ" matches print "N.P.I" on p. 257. Entry 1398 and Perseus "صَلَّوَ II" match print "—II, Prayed" on p. 457. |
| Brief suggestion 3: "second-hand" | "its classical material is largely second-hand" | **S.** This now matches p. ix ("several words hitherto unrecorded"). |

## Claims table (whole page re-verified)

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title "An Advanced Learner's Arabic-English Dictionary" | S | OL JSON title (1972); Perseus header |
| C2 | titleGloss: first published as *An Arabic-English Dictionary on a New System* (London, 1890) | S | IA title page OCR "ARABIC-ENGLISH DICTIONARY … LONDON … 1890"; LC "…new system, 1890"; preface dated 1889, so there is no earlier edition |
| C3 | author "H. Anthony Salmoné" | S | title page "BY H. ANTHONY SALMONÉ" |
| C4 | authorFull "Habib Anthony Salmoné" | S | LC JSON |
| C5 | period "preface dated 1889; published 1890" | S | p. x "21st November 1889"; title page 1890 |
| C6 | kind "Learner's Arabic–English dictionary" | S | title page (vol. I Arabic-English); preface ("ordinary student", "the beginner", "the learner") |
| C7 | summary: compact dictionary for students, London 1890 | S | preface p. vii ("portable form … within the reach of all students"); title page |
| C8 | summary: verbs, nouns, plurals, prepositions, terse English equivalents | S | Notes 3–7; pp. 22, 160, 257, 490–491 |
| C9 | summary: classical and nineteenth-century usage side by side | S | Notes 9–10; p. ix "both classical and modern writing" |
| C10 | summary/lede: no quoted evidence or named authorities; no poetry or scripture | S | greps (0 Kor/Qur; other hits are English glosses); print pp. 22, 160, 257, 457, 490–491 give glosses only |
| C11 | lede: lectured on Arabic at University College London | S | title page "ARABIC LECTURER AT UNIVERSITY COLLEGE, LONDON" |
| C12 | lede: "comprehensive, handy and cheap" | S | p. vii (verbatim) |
| C13 | lede: one compact article per root: verbs, nouns, plurals, prepositions, English equivalents, classical and modern side by side | S | Expl. note 10 (p. xvii, "The order of each article, i.e. every fresh root"); p. 257 |
| C14 | lede: a map of a word family, not a witness to seventh-century meaning | S (editorial) | follows from C10, C26–C31 |
| C15 | title page: "Arabic Lecturer at University College, London"; professor of Arabic at the School for Modern Oriental Studies set up by the Imperial Institute | S | title page OCR: "PROFESSOR OF ARABIC AT THE SCHOOL FOR MODERN ORIENTAL STUDIES, ESTABLISHED BY THE IMPERIAL INSTITUTE" |
| C16 | "(Habib)" [^lc] | S | LC JSON |
| C17 | preface signed at University College on 21 Nov 1889 [p. x] | S | OCR after head "X PREFACE.": "H. ANTHONY SALMONE. 21st November 1889. UNIVERSITY COLLEGE, LONDON." |
| C18 | "either too bulky and expensive, and of no practical utility to the ordinary student, or too small and of vocabulary-like dimensions" | S | p. vii (verbatim; the first page of the preface, before head "VIII") |
| C19 | "a living language" [p. vii] | S | p. vii |
| C20 | the book sets modern and colloquial meanings beside classical ones | S | Notes 9–10; entry 6655 "[ coll. ], Broke in…" |
| C21 | "new system": a number referring to "a table of model forms" instead of each noun and plural [p. viii] | S | p. viii (verbatim) |
| C22 | seventy patterns such as *faʿīl* and *fuʿalāʾ* [Table] | S | image n13: 1–70; 25 فَعِيل; 43 فُعَلاء |
| C23 | derived verbs appear only as Roman numerals | S | Note 5; p. 160 "—V, Belonged to"; p. 257 "—II, Reared"; p. 457 "—II, Prayed" |
| C24 | ḥanīf line reads in full "25, (pl. 43), Mussulman." [p. 160] | S | image n185 |
| C25 | the site's title = the 1970s reissue [OL] and the digitisation [Perseus] | S | OL JSON 1972; Perseus header |
| C26 | "chief aids": Lane "as far as this work has been published" (lacking wāw and yāʾ, per his note); Cuche; al-Bustānī's *Muḥīṭ al-Muḥīṭ* [pp. viii–ix] | S | p. viii: "LANE's Arabic-English Lexicon, as far as this work has been published—i.e. excepting the last two letters (و & ي); CUCHE's Vocabulaire arabe-français and the Muhit-ul-Muhit by BUTROS BUSTANY" |
| C27 | checked against Freytag, Kazimirski, Dozy and others | S | pp. viii–ix, "in checking and revising" |
| C28 | "hitherto unrecorded"; "both classical and modern writing" | S | p. ix (verbatim) |
| C29 | Lane built on the Arabic dictionaries, above all the *Tāj* [Haywood p. 124] | S | Haywood p. 124 |
| C30 | al-Bustānī took over the *Qāmūs* material [Haywood p. 109] | S | Haywood p. 109 |
| C31 | "openly second-hand … at one or two removes, condensed again" | S (interpretation) | C26, C29, C30; the aids are named in the preface |
| C32 | fixed article order: basic verb, derived verbs, nouns and adjectives, participles and verbal nouns, other words, idioms [p. xvii] | S | Expl. note 10 (under head XVII). Simplified: it omits step 2 and merges steps 6–7. |
| C33 | (a), (b), (c) number the senses ["Notes"] | S | Notes 4 |
| C34 | "the first meaning given in the root is invariably the most important one, and the one that generally runs throughout…" [p. xv] | S | Expl. note 1 (the page before head XVI; verbatim) |
| C35 | "n. ac." introduces verbal nouns; "N. Ag." and "N. P." mark participles | S | Notes 3 and 6 |
| C36 | bracketed preposition [Bi], ['Ala] shows what a verb takes | S | Notes 7; Expl. note 2 |
| C37 | P., T. flag words derived from another language | S | Notes 8 ("showing that the word is derived from that language") |
| C38 | "[coll.]": "especially modern or used in the colloquial language only" | S | Notes 9 (verbatim) |
| C39 | asterisk: "that the root or most of the derived forms are used in the modern language" | S | Notes 10 (verbatim) |
| C40 | "Both marks are coarse" | S (interpretation) | Notes 10 (the asterisk covers a root); p. 491 printing words carry no mark |
| C41 | ط ب ع: the Qur'anic verb of God sealing hearts (Q 4:155), glossed "Stamped, sealed; made an impression or mark on; printed (book)" | S | Q 4:155 *bal ṭabaʿa llāhu ʿalayhā*; entry 6655; p. 490 |
| C42 | "Printing-press" carries no [coll.] | S | entry 6655; p. 491 |
| C43 | in the print the only covering mark is the root asterisk [pp. 490–491] | S | images n515, n516 |
| C44 | our copy drops that asterisk | S | entry 6655 |
| C45 | أ م ن: two constructions of *āmana* (excerpt) | S | entry 9 (verbatim); p. 22 "IV [acc. or bi], Believed, had faith in; … —(c) [La], Trusted himself to, was led by." |
| C46 | he cites no verse; Q 9:61 uses both constructions; translation labelled | S | Q 9:61 *yuʾminu bi-llāhi wa-yuʾminu li-l-muʾminīna* |
| C47 | ر ب ب excerpt 1 | S | entry 129 (verbatim) |
| C48 | by his rule "lord, master, owner" is the most important sense | S | p. xv; entry order |
| C49 | the entry does not relate lordship to rearing or arranging | S | entry 129; p. 257 |
| C50 | *rabb*, *rubb* "Syrup; preserve", *ribāb* marked P. "A kind of viol; violoncello" | S | entry 129; p. 257 "—23, Tithe, tenths.—(b), P., A kind of viol" |
| C51 | nothing marks which sense belongs to which period | S | p. 257: no root asterisk and no [coll.] |
| C52 | ر ب ب excerpt 2 | S | entry 129 (verbatim) |
| C53 | *rabāʾib* is the word of Q 4:23 (translation labelled) | S | Q 4:23 *wa-rabāʾibukumu llātī fī ḥujūrikum* |
| C54 | plural of *rabbānī* in Q 3:79, 5:44, 5:63 | S | Qur'an text |
| C55 | three glosses, no indication of which applies where or when; "Doctor of the sacred law" not dated | S | entry 129; p. 257 (the claim is hedged) |
| C56 | "see 23tb" traces the print's "see 23t.—(b)"; (a) = *ribāba*; (b) "Divinity, godhead" [p. 257] | S | image n282 "27yit, see 23t.—(b), Divinity, godhead"; "23t, Lordship, dominion, power, authority"; table 23 = فِعَال |
| C57 | ح ن ف excerpt | S | entry 6345 (verbatim) |
| C58 | "Mussulman" = his ordinary English for *muslim*; plural note uses مُسْلِم "Mussulman" [p. xvii] | S | Expl. note 13 (under head XVII); stored slm "N. Ag. أسلم a. Mussulman, Moslem, Muslim" |
| C59 | entry makes ḥanīf = muslim, yet Q 3:67 has *ḥanīfan musliman* (translation labelled) | S | Q 3:67; entry 6345 |
| C60 | Lane (one of the chief aids) records that sense and qualifies it (excerpt) | S | entry 6343 (verbatim; the validator passes); p. viii |
| C61 | abbreviations = Lane's Arabic sources; "conventional term of the professors" read (labelled) as technical usage of scholars | S | entry 6343 |
| C62 | Lane sets other explanations, from "inclining to a right state or tendency" to pilgrimage and circumcision, each tied to a source | S | entry 6343: "( Er-Rághib , TA :)"; "( As , K , TA :)"; "( TA :)"; "accord. to Akh" |
| C63 | Salmoné keeps one English word with no sign of origin or age | S | entry 6345; p. 160 |
| C64 | "The book's economy can flatten a contested word. One example…" | S | framed as one example |
| C65 | How to use: fast survey of verb forms, prepositions, plurals, modern meanings | S | C8, C9 |
| C66 | "It gives no evidence, and its classical material is largely second-hand" | S | C10, C26, C28 |
| C67 | flags modern usage only coarsely; our copy loses part of that marking | S | C40, C44, C79 |
| C68 | date = date of compilation, not of the meanings | S (editorial) | preface |
| C69 | onOurSite: 948 roots from the Arabic–English volume | S | `dicts` gives 948; title page vol. I Arabic–English |
| C70 | Perseus text, taken by hawramani via the Alpheios Project [^hawramani] | S | hawramani page; Perseus rbb/Slw identical to the stored text apart from numbers and aorist letters |
| C71 | Perseus imprint "Beirut. Librairie du Liban. 1889" is not the London original's [^perseus] | S | Perseus main page (verbatim); title page London 1890 |
| C72 | Perseus has Arabic forms beside the print's pattern numbers and Roman numerals | S | Perseus rbb "رَبَّبَ II", "رُبُوْب 27", "رَبَّة 1t" |
| C73 | where the print gives only the number, the form was supplied later | S | p. 257 "—1t, Mistress" (no Arabic) vs Perseus "رَبَّة 1t"; p. 457 "—II, Prayed" vs Perseus "صَلَّوَ II". The sentence does not say who supplied them, which is correct because that is unknown. |
| C74 | our copy keeps the forms but drops the present-tense vowel letters and most numbers | S | Perseus "رَبَّ U ( n. ac. رَبّ 1 )" vs stored "رَبَّ(n. ac. رَبّ)"; "38", "27" and "17t" survive; Notes 1 (A/I/U = vowel of the aorist, i.e. the imperfect) |
| C75 | an empty [] once held a number | S | stored 1398 "صَلَاة []" vs Perseus "[ 4tA ]"; stored 1000 "دَنَاوَة []" vs Perseus "[ 22t ]"; print p. 457 [4tA] |
| C76 | cross-references survive; "see V" = the fifth-form verb in the same entry | S | entry 129 "إِرْتَبَبَa. see V"; print p. 257 "—VIII, see V." |
| C77 | a stray ڤ marks a garbled form | S | entry 129 "N. P. رَبڤبَ" (print "N.P.I"); TbE "N. P. طَبڤعَ" (print "N.P.I") |
| C78 | under ص ل و, صَلَّوَ stands for صَلَّى | S | entry 1398; print p. 457 "—II, Prayed" |
| C79 | "_ast;" is the print's asterisk, kept before some forms but dropped from root headings | S | 24 stored occurrences, all mid-entry. Print p. 839: asterisk beside كبر's "(—) U, Was, became great" line, and stored kbr has "_ast; كبر … Was, became great". The root asterisks at أمن (p. 22), طبع (p. 490) and صلا (p. 457) are absent from stored entries 9, 6655 and 1398. |
| C80 | some w/y-final roots such as د ن و show one line; in Perseus the rest, *dunyā* ("world") included, sits under دني, which our site does not display [^perseus\|roots dnw and dny] | S | entry 1000 (one line); Perseus dnw (one line); Perseus dny "دُنْيَا ( pl. دُنَي 9 ), a. World, this present world"; `find-root دني` gives no match; other short w/y roots include nsw, nhy, ESw |
| C81 | limitedEvidence: no scholarly study of this dictionary found | S (as the team's report) | I could not re-run a web search. Haywood (1960) never mentions Salmoné, and nothing else I opened points to a study. It is worded as "we found". |
| C82 | limitedEvidence: online dates disagree, most unsourced, none checkable; the page gives none | S | Wikidata 1860–1904 (0 references); Sue Young Histories 1830–1895 (its citations are not for the dates) |
| C83 | limitedEvidence: rests on title page, preface, notes and displayed entries | S | matches the citations |
| C84 | source salmone-1890 (2 vols, Trübner 1890; title page, pp. vii–x, Table, Notes, pp. xv–xxi, entries) | S | IA metadata; title page "IN TWO VOLUMES"; all locators checked |
| C85 | source openlibrary (Beirut, Librairie du Liban, 1972, xxiii, 1252, 179 p.) | S | OL JSON (verbatim) |
| C86 | source perseus (text 2002.02.0005; bibliographic and funding statement; root entries rbb, dnw, dny) | S | Perseus pages |
| C87 | source haywood (Brill, 1960) | S | IA metadata "Arabic lexicography", Haywood, 1960 |
| C88 | source hawramani | S | page title "Habib Anthony Salmoné, An Advanced Learner's Arabic-English Dictionary (1889)" |
| C89 | source lc | S | LC JSON nr90023582 |

**Totals: 89 claims. 89 supported, 0 need qualification, 0 unsupported.**

## Flagged items

None.

## Brief issues (not factual)

1. **suggestion:** onOurSite is about 162 words, above FORMAT's ≈60–150. Two trims would bring it into range:
   - "an empty [] once held one." could go, or become "(empty [] brackets mark a lost number)".
   - The ڤ/صَلَّوَ sentence could be shortened.
2. **suggestion:** Lede and body come to 1,089 words (validator), at the top of the range. This is legitimate because the length rests on the book's own preface, notes and pages. Do not add material.
3. **suggestion:** "present-tense vowel letters" is a loose rendering of Salmoné's "Ao." (aorist, i.e. imperfect). It is acceptable plain English. "imperfect-tense vowel letters" or "the letters A/I/U that give the imperfect's vowel" would be more exact.
4. There is no generic praise, ranking or padding, and no forced root-meaning narrative. All 7 root links go to displayed entries, and every translation made for the guide is labelled. Nothing is promised that our copy lacks: the دني material is flagged as not displayed, and the dropped asterisks are disclosed. Biography is limited to the title page and LC, as the evidence requires.

## Source URLs

| id | URL | Status |
|---|---|---|
| lc | https://id.loc.gov/authorities/names/nr90023582.html | The HTML returns 403 to curl (bot check). The `.json` of the same record opens and is the stated record. It should open in a browser. |
| salmone-1890 | https://archive.org/details/arabicenglishdic0000unse | 200. Vol. 1, Trübner 1890. Locators confirmed. |
| openlibrary | https://openlibrary.org/books/OL15560928M | The HTML redirects curl to `verify_human`. The `.json` opens and is the stated 1972 record. |
| perseus | https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A2002.02.0005 | 200. The imprint and NSF lines are present. |
| haywood | https://archive.org/details/in.gov.ignca.12555 | 200. pp. 109 and 124 confirmed. |
| hawramani | https://arabiclexicon.hawramani.com/habib-anthony-salmone-an-advanced-learners-arabic-english-dictionary/ | 200. It states the Alpheos/Tufts provenance. |

All listed sources are cited and were consulted.

## Validator

`node scripts/validate-dictionary-guides.mjs salmone-dictionary` gave: **ok**. It found 7 root links (7 distinct pairs), 5 excerpts, 1,089 words, example roots TbE, Amn, rbb, Hnf, Slw and dnw, and 1/1 guides pass.

## Site-data issues (report only; not edited)

1. **The stored date 1889 is not a death year.** It is the preface date (21 Nov 1889) and the year in the Perseus imprint. The book was published in London in 1890. The compiler's death year is unestablished: unsourced records give 1895 or 1904. The panel orders works by death year.
2. **The stored title is the 1972 Librairie du Liban reissue title.** The original is *An Arabic-English Dictionary on a New System* (London: Trübner, 1890).
3. **The stored text drops the print's root-level asterisk** (the modern-use marker). This is visible at أمن p. 22, طبع p. 490 and صلا p. 457. Other asterisks survive only as the literal string `_ast;` (24 entries).
4. **The Harmonized English for Amn (entry 9) and rbb (entry 129) calls the work an "English–Arabic learner's dictionary".** It is Arabic–English.
5. **The Harmonized English for TbE (entry 6655) adds material the original lacks.** It ends with an interpretive paragraph ("The entry ties the abstract senses together…") and labels the printing words "modern derivatives". Salmoné's entry has neither.
