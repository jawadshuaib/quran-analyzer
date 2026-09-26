# Verification round 1: salmone-dictionary

Verifier: independent fact-check agent (round 1), 2026-09-26.
Page checked: `roots/frontend/src/content/dictionary-guides/guides/salmone-dictionary.ts`
I did not open research-notes.md or any revision file. Every verdict rests on sources I opened myself.

## Primary evidence used

- **Print scan (vol. 1, London: Trübner, 1890)**: https://archive.org/details/arabicenglishdic0000unse. I read the full OCR (`_djvu.txt`) and checked these page images directly:
  - n7: title page (OCR)
  - n10: preface p. ix
  - n13: "Table of Arabic Derived Forms"
  - n18: explanatory notes p. xvii
  - n185: p. 160 (حنف)
  - n282: p. 257 (ربب)
  - n515: p. 490 (طبع)
  - n620: p. 595 (علم)
- **Perseus digital text** (2002.02.0005), including the entries for rbb, Slw, Elm, TbE, dnw and dny.
- **LC authority record** nr90023582 (JSON).
- **Haywood, *Arabic Lexicography* (1960)**, IA OCR, pp. 109 and 124.
- **Hawramani dictionary page.**
- **Site entries** via `_dict_guide_tool.py`:
  - Salmoné: Amn = 9, rbb = 129, Hnf = 6345, TbE = 6655, Slw = 1398, dnw = 1000
  - Lane: Hnf = 6343
- **Google Books**: the cited record (-pcOAAAAYAAJ) is blocked for automated access (Google "sorry"/429). A search result confirms its title. The sibling record MS4KAQAAIAAJ gives the title, Al-Biruni, 1976 and 1431 pp.
- **Wikidata** Q53421609 and **Wikisource** Author:Habib_Anthony_Salmoné. I used these only to test the "dates disagree" claim.

## Claims table

S = supported, NQ = needs qualification, U = unsupported.

| # | Claim (field) | Verdict | Evidence |
|---|---|---|---|
| C1 | title "An Advanced Learner's Arabic-English Dictionary" is the reissue/digitised title (title, body) | S | Perseus header; Google Books MS4KAQAAIAAJ (Al-Biruni 1976) |
| C2 | titleGloss: first published as *An Arabic-English Dictionary on a New System* (London, 1890) | S | IA metadata and title page (Trübner, Ludgate Hill, 1890, "in two volumes") |
| C3 | author H. Anthony Salmoné / authorFull Habib Anthony Salmoné | S | title page; LC nr90023582 ("Salmoné, H. Anthony (Habib Anthony)") |
| C4 | period: preface dated 1889, published 1890 | S | preface p. x signed "21st November 1889"; title page 1890 |
| C5 | kind: learner's Arabic–English dictionary | S | preface p. vii–viii ("ordinary student", "the beginner") |
| C6 | summary: compact student dictionary; London 1890; verbs/nouns/plurals/prepositions; classical and modern side by side; no quoted evidence or named authorities | S | preface; Notes; pp. 160, 257; grep of 948 displayed entries |
| C7 | lede: lectured on Arabic at University College London | S | title page "Arabic Lecturer at University College, London" |
| C8 | lede: "comprehensive, handy and cheap" | S | preface p. vii |
| C9 | lede/summary: quotes no poetry or scripture, names no authorities | S | 0 displayed entries match Kor/Qur/Koran or Lane/Freytag/Dozy/Kazim/Jauhari; sampled print pages show glosses and idioms only |
| C10 | title page: Arabic Lecturer at UCL; professor at School for Modern Oriental Studies set up by the Imperial Institute | S | title page OCR; LC citation note repeats it |
| C11 | "We have found no reliable account of his life beyond that" | S (as a search report) | I also found only unreferenced Wikidata/Wikisource data and a hawramani one-liner |
| C12 | preface signed at University College, 21 November 1889 | S | p. x |
| C13 | quote "either too bulky and expensive … vocabulary-like dimensions" p. vii | S | p. vii |
| C14 | "a living language" p. vii | S | p. vii |
| C15 | sets modern and colloquial meanings beside classical ones | S | Notes 9 [coll.]; preface p. ix "classical and modern writing" |
| C16 | numbers refer to "a table of model forms" p. viii | S | p. viii |
| C17 | seventy patterns such as *faʿīl* and *fuʿalāʾ* | S | Table image: 1–70; 25 = فَعِيل, 43 = فُعَلَاء |
| C18 | derived verbs appear only as Roman numerals | S | Notes 5; images pp. 160 and 257 |
| C19 | ḥanīf line reads in full "25, (pl. 43), Mussulman." p. 160 | S | p. 160 image (OCR misreads 43 as 48; the image shows 43) |
| C20 | site title is the 1970s reissue title and the digitised title | S | Google Books (Al-Biruni 1976); Perseus |
| C21 | chief aids: Lane (minus wāw and yāʾ), Cuche, Bustānī's *Muḥīṭ al-Muḥīṭ* | S | p. viii |
| C22 | checked against Freytag, Kazimirski, Dozy and others | S | pp. viii–ix (also Wahrmund, Richardson) |
| C23 | added words "hitherto unrecorded" from "both classical and modern writing" | S | p. ix (image n10) |
| C24 | Lane built on the Arabic dictionaries, above all the *Tāj* | S | Haywood p. 124 ("could best serve as the basis of his lexicon"; transcriptions of the Taj "and other dictionaries") |
| C25 | al-Bustānī took over the material of the *Qāmūs* | S | Haywood p. 109 ("took all the material of the Qamus, and supplemented it…") |
| C26 | glosses reach the classical lexicons "at one or two removes, condensed again" | S (interpretation) | follows from C21, C24 and C25 |
| C27 | fixed article order (verb, derived verbs, nouns, participles/verbal nouns, other words, idioms) p. xvii | S | Expl. note 10, p. xvii (simplified) |
| C28 | (a)(b)(c) number senses; "first meaning … invariably the most important…" p. xv | S | Notes 4; Expl. note 1, p. xv |
| C29 | n. ac., N. Ag., N. P., [Bi]/['Ala], [coll.] quote, P./T./G./H./S./Ch. | S | "Notes" 6–9, unnumbered page before p. xv |
| C30 | about a third of displayed entries carry [coll.] | S | 321 of 948 displayed entries match "coll." |
| C31 | "Read the tag as a warning when present, not a guarantee when absent"; TbE gloss and Q 4:155; "Printing-press" carries no tag | NQ | the quoted glosses match entry 6655 and Q 4:155 is right. But the print marks طبع with an **asterisk** (p. 490), which by Notes 10 means "the root or most of the derived forms are used in the modern language". Perseus and our copy drop it. The essay implies the book gave no signal. |
| C32 | Amn excerpt; Salmoné separates two constructions of *āmana* | S | entry 9 (text matches) |
| C33 | Q 9:61 uses both constructions; translation labelled | S | Q 9:61 *yuʾminu bi-llāhi wa-yuʾminu li-l-muʾminīna* |
| C34 | rbb excerpt 1 | S | entry 129; p. 257 |
| C35 | by his rule "lord…" is the most important sense; no link between lordship and rearing given | S | p. xv; entry 129 |
| C36 | *rabb*, *rubb* "Syrup; preserve", *ribāb* P. viol, participle "Preserve, jam…" | S | p. 257; entry 129 |
| C37 | nothing marks which sense belongs to which period (rbb) | S | p. 257: no [coll.], no asterisk on ربّ |
| C38 | rbb excerpt 2 | S | entry 129 (text matches) |
| C39 | *rabāʾib* is the word of Q 4:23 "your step-daughters in your care" | S | Q 4:23 *rabāʾibukumu llātī fī ḥujūrikum* |
| C40 | plural of *rabbānī* in Q 3:79, 5:44, 5:63 | S | Qur'an text |
| C41 | three glosses, no indication of which belongs where or when | S | entry 129 |
| C42 | "'Doctor of the sacred law' is the English of a later learned title" | NQ | no source is given and I found none showing that this sense is post-Qur'anic. It is the essay's own dating judgment, stated as fact. |
| C43 | "see 23tb" is a trace of print "see 23t.—(b)" p. 257; (a) = *ribāba*, (b) "Divinity, godhead" | S | p. 257 image ("27yit, see 23t.—(b), Divinity"); Table 23 = فِعَال, t = ـة; Perseus same |
| C44 | Hnf excerpt | S | entry 6345; p. 160 |
| C45 | "Mussulman" is his English for *muslim*; plural note uses مُسْلِم p. xvii | S | p. xvii image |
| C46 | Q 3:67 *ḥanīfan musliman*; translation labelled | S | Q 3:67 |
| C47 | Lane is one of the chief aids; Lane excerpt | S | p. viii; entry 6343 (text matches verbatim) |
| C48 | abbreviations name Lane's sources; reading of "conventional term of the professors" | S (labelled as reading) | entry 6343 |
| C49 | Lane gives other explanations ("inclining to a right state or tendency", pilgrimage, circumcision), each sourced | S | entry 6343 |
| C50 | How to use: "it flags modern usage only some of the time" | NQ | as C31. The print had a second device, the asterisk (Notes 10), that our copy loses at root heads. |
| C51 | its date is the compilation's, not the meanings' | S | editorial guidance consistent with the preface |
| C52 | onOurSite: 948 roots, from the Arabic–English volume | S | `_dict_guide_tool.py dicts`; vol. 1 is Arabic–English |
| C53 | text = Perseus digital edition via hawramani via Alpheios | S | hawramani page ("sourced from the Alpheos Project and originally provided by Tufts"); Perseus text identical for rbb and Slw |
| C54 | Perseus imprint "Beirut. Librairie du Liban. 1889" is not the London original of 1890 | S | Perseus page footer; title page |
| C55 | Perseus "spelled the print's pattern numbers and Roman numerals out as Arabic words" | NQ | Perseus supplies a reconstructed Arabic form **beside** each number and keeps the number (e.g. "رُبُوْب 27", "رَبَّبَ II", "صَلَاة [ 4tA ]"). It does not replace them. |
| C56 | our copy drops the numbers and aorist vowel letters but keeps cross-references; "see V", "see 21 (a)" explained | S | entry 129 vs Perseus ("رَبَّ U"); entry 6655 "طَابَع a. see 21 (a)" (21 = فاعِل) |
| C57 | stray ڤ marks a garbled form | S | entry 129 "N. P. رَبڤبَ" = Perseus; 197 displayed entries contain ڤ |
| C58 | empty [] once held a pattern number | S | Perseus Slw "[ 4A ]", "[ 38A ]", "[ 4tA ]" vs entry 1398 "[]" |
| C59 | صَلَّوَ stands for صَلَّى | S | Form II of ṣ-l-w; Perseus has the same form |
| C60 | "Ignore the string '_ast;'" | **U** | contradicted. "_ast;" (24 displayed entries) is the print's asterisk. p. 595 image: "* (ـِ) A (n. ac. 2) … Knew" is Perseus/our "_ast; عَلِمَ". Notes 10: the asterisk means the root or most derived forms are used in the modern language. |
| C61 | for some roots ending in wāw/yāʾ, e.g. dnw, "we show one line; the rest sits under the spelling with final yāʾ" | NQ | true in Perseus (root dny holds the rest). But the site has no دني root (`find-root دني` → no match), so readers cannot find "the rest" on al-nuqta. The wording implies they can. |
| C62 | limitedEvidence: no scholarly study of this dictionary found | S (as a search report) | I found none either |
| C63 | limitedEvidence: "the records we found disagree about his dates and cite no evidence" | NQ | Wikidata (1 Sep 1860 Beirut – Oct 1904 London; 0 references) and Wikisource (1860–1904) **agree**. I found no disagreeing record. "Cite no evidence" is correct. |
| C64 | source salmone-1890: "explanatory notes (pp. xv–xix)" | NQ | the explanatory notes run to p. xxi (OCR page heads "XX EXPLANATORY NOTES", "EXPLANATORY NOTES. XXI") |
| C65 | LC record supports "(Habib)" | S | LC JSON: authoritative label "Salmoné, H. Anthony (Habib Anthony)" |

Totals: 65 claims. 57 supported, 7 need qualification (C31, C42, C50, C55, C61, C63, C64), 1 unsupported (C60).

## Flagged items and fixes

1. **C60 (U): "Ignore the string '_ast;'."** This is the print's asterisk. Notes item 10 says "The asterisk indicates that the root or most of the derived forms are used in the modern language." See p. 595, علم. **Fix:** replace with: "The string '_ast;' stands for the print's asterisk, which Salmoné used to mark a root or form 'used in the modern language'; our copy keeps it only inside some entries and drops it from root headings."
2. **C31 and C50 (NQ): modern usage flagged "only some of the time" / "not a guarantee when absent".** The print marks طبع with an asterisk on p. 490, a modern-use signal that our copy drops. **Fix:** keep the TbE observation about [coll.], but add one clause: "the print also put an asterisk beside roots 'used in the modern language', and طبع carries one, but our copy drops it". Then soften "flags modern usage only some of the time" to "flags modern usage only coarsely, and our copy loses part of that marking".
3. **C42 (NQ):** "'Doctor of the sacred law' is the English of a later learned title." There is no evidence that the sense is post-Qur'anic. **Fix:** "'Doctor of the sacred law' sounds like a scholarly title; nothing in the entry says whether that is how the word was used in the Qur'an's time." Alternatively, delete "later".
4. **C55 (NQ):** Perseus did not "spell out" the numbers in place of the originals. **Fix:** "That edition added a reconstructed Arabic form beside each pattern number and Roman numeral; our copy keeps those forms but drops the numbers and the present-tense vowel letters…"
5. **C61 (NQ):** the dnw "rest" is not on our site. **Fix:** "…we show one line; in the source edition the rest sits under the spelling with final *yāʾ* (دني), which our site does not display."
6. **C63 (NQ):** the dates do not disagree. Wikidata and Wikisource both give 1860–1904, unreferenced. **Fix:** "the only dates we found (1860–1904, in unreferenced online records) cite no evidence, so this page gives none."
7. **C64 (NQ):** in the salmone-1890 source citation, change "explanatory notes (pp. xv–xix)" to "(pp. xv–xxi)".

## Brief issues (not factual)

- *suggestion*: Lede and body come to 1,069 words, at the top of the range. The depth rests on the book's own preface and notes, which is legitimate. Still, the biographical evidence is thin, so trim where possible. The abbreviation paragraph and the onOurSite repair notes are dense.
- *suggestion*: The abbreviations paragraph reads like a key or list. That is acceptable for a how-to-read section. Consider adding the asterisk convention there, where it belongs with [coll.] (see flag 2).
- *suggestion*: The "One word, one gloss" section rests on a single root (حنف). The essay generalises carefully ("The book's economy shows most where a word is contested"), and that framing is fine. Avoid implying every contested word is flattened this way.
- *suggestion*: The Google Books citation (-pcOAAAAYAAJ) cannot be opened by automated tools. It is the stated work according to its search-result title. Consider citing the sibling record MS4KAQAAIAAJ as well, which shows Al-Biruni, 1976, 1431 pp.
- No padding, praise or ranking. The page does not force a root-meaning narrative. Every root mention is linked, and every translation is labelled.

## Source URLs

| id | URL | Status |
|---|---|---|
| lc | id.loc.gov nr90023582 | opens; is the stated record |
| salmone-1890 | archive.org arabicenglishdic0000unse | opens; vol. 1, Trübner 1890; page locators confirmed (vii, viii, viii–ix, xv, xvii, "Notes", Table, 160, 257) |
| gbooks | books.google.com -pcOAAAAYAAJ | blocked for automated fetch (Google 429/"sorry"). Title confirmed via search result; publisher and year confirmed via sibling record MS4KAQAAIAAJ. |
| perseus | perseus.tufts.edu 2002.02.0005 | opens (some per-root URLs return 503 intermittently); the imprint line and NSF funding statement are present |
| haywood | archive.org in.gov.ignca.12555 | opens; pp. 109 and 124 confirmed |
| hawramani | arabiclexicon.hawramani.com Salmoné page | opens; states the Alpheios/Tufts provenance |

All listed sources are used in the text. None is unusable.

## Validator

`node scripts/validate-dictionary-guides.mjs salmone-dictionary` returned **ok**: 7 root links, 5 excerpts, 1,069 words, 1/1 pass.

## Site-data issues

1. **The stored date 1889 is not a death year.** The panel orders works by the author's death year, but 1889 is the preface date and the (doubtful) Perseus "Beirut 1889" imprint year. The book was first published in London in 1890. Unreferenced Wikidata and Wikisource give the compiler's death as 1904. That date is unverified, so no correction can be sourced firmly.
2. **The site title is the 1976 Al-Biruni reissue title.** The original title is *An Arabic-English Dictionary on a New System* (1890). This is acceptable as a label, but it is not the original title.
3. **The stored text drops the print's root-level asterisk** (modern-use marker) and keeps a mid-entry asterisk as the literal string "_ast;" (24 entries).
4. **The harmonized English for rbb (entry 129) and Amn (entry 9) mislabels the work** as "an English-Arabic learner's dictionary". It is Arabic–English.
5. **The harmonized English for TbE (entry 6655) ends with an interpretive paragraph** ("The entry ties the abstract senses together: the same act that stamps…") that Salmoné's entry does not contain.
