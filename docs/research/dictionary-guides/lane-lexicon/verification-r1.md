# Lane's Lexicon guide — verification round 1

Checked file: `roots/frontend/src/content/dictionary-guides/guides/lane-lexicon.ts`
Checker: independent verifier, round 1 (2026-09-26). I did not open research-notes.md or any revision file.

## What I checked it against

- **Lane's Preface (Part 1, 1863).** I read it in the Internet Archive item `LAB1865AREN` (Librairie du Liban reprint, 1968). I used the OCR text (`…(VOL. 1)_djvu.txt`) and page images I rendered from `…(VOL. 1).pdf`. I checked page numbers against the running heads (for example "xx PREFACE", "PREFACE. xxi").
- **Lexicon pages.** I viewed page images of p. 31 (اخر), p. 658 (حنف), p. 1749 (صوم), p. 2486–87 (the قتر…قتو block and its "See Supplement" line) and p. 2984 (Supplement, قبل–قتل). I also viewed the Part 7 and Part 8 title pages and the page "SUPPLEMENT TO PARTS VII. AND VIII." In this Internet Archive item the file labelled "VOL. 3" is Part 7, "VOL. 7" is Part 3, and "VOL. 5" contains Part 5 followed by Lane-Poole's Editor's Preface (July 1877), his Postscript (1 January 1893) and the Memoir.
- **Lane-Poole's Editor's Preface (1877).** I read it from the page image. The OCR garbles the article name, but the image clearly shows "engaged on the article قد".
- **Haywood, *Arabic Lexicography* (1960).** I read the OCR text of archive.org `in.gov.ignca.12555`, pp. 123–26.
- **DNB, "Lane, Edward William"** on Wikisource.
- **Perseus** (`doc=ASl`). The page opens and shows the bibliographic note "London. Williams and Norgate. 1863." with the CC BY-SA licence. Its digital text marks sense breaks as "-b2-" and "-A2-".
- **Hawramani's Lane page.** It opens. It says the text was "sourced from Tufts University", worked from "a TXT version created by … Navid-ul-Islam", and "fixes various errors from both the Persues project … and the TXT version".
- **Displayed data.** I ran `_dict_guide_tool.py entry` for Swm (5692), Hnf (6343), qtl (729) and al-Rāghib Hnf (6348). I also ran `roots` (1,410 roots, 427 of them from qāf to yāʾ) and `grep` for "See Supplement" (5 entries) and "CCC" (22 entries). I read verse texts from `quran.db`.

## Claims table

S = supported. NQ = needs qualification. U = unsupported.

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| C1 | Title *An Arabic–English Lexicon* | S | Title page, Part 1 (1863) |
| C2 | titleAr مدّ القاموس | S | Arabic title on the 1863 title page (PDF p. 4). Preface p. xxxii: "The Arabic title مدّ القاموس" |
| C3 | titleGloss: "the flow of the sea" and "the extension of the Qāmūs" | S | Preface p. xxxii: "It has two meanings: 'The Flow of the Sea' and 'The Extension of the Kámoos.'" (The page does not cite this; see brief issues.) |
| C4 | Author Edward William Lane | S | Title pages |
| C5 | period "published 1863–93 (Lane d. 1876)" | S | Title pages of Part 1 (1863) and Part 8 (1893). Editor's Preface: died 10 Aug 1876 |
| C6 | kind "Arabic–English lexicon" | S | Title page |
| C7 | Summary: the lexicons are read mainly through the *Tāj*; a source is named for almost every sense; Lane's own additions are bracketed | S | Preface p. xix ("the medium through which I have drawn most of the contents"), p. xxvi ("nothing … without indicating at least one authority, except … square brackets") |
| C8 | Summary: he died at qāf; entries from there on were published later, some only as notes | S | Editor's Preface 1877; Postscript 1893; Supplement to Parts VII and VIII |
| C9 | "Thirty-four years" | S | Editor's Preface: "After thirty-four years of labour at the Lexicon" |
| C10 | Lede: initials on almost every meaning, brackets, marks for figurative senses (by an authority or by Lane) | S | Preface pp. xxv, xxvi |
| C11 | Lede: "you can tell, line by line, whose voice you are hearing" | **NQ** | Preface pp. xx and xxvii: Lane often wrote from the *Lisān* but cited the *Tāj*. Preface p. xxxi: many authorities are cited "through the medium of" the *Tāj* or *Lisān* without saying so. So a tag names Lane's proximate source, not necessarily the person who first said it |
| C12 | Lord Prudhoe (later Duke of Northumberland) funded the work from 1842 | S | Preface p. v, first sentence |
| C13 | Golius contrast; "epitomes or abstracts or manuals"; "the most copious Eastern sources" | S | Preface p. v |
| C14 | Al-Zabīdī's *Tāj* finished in the 1760s | S | Preface p. xviii: citing al-Jabartī, "finished the Táj el-'Aroos A.D. 1767 or 1768" |
| C15 | "the medium through which I have drawn most of the contents of my lexicon" | S | Preface p. xix |
| C16 | Copying and collating, mostly by Shaykh Ibrāhīm al-Dasūqī, took over thirteen years | S | Preface p. xxi: "more than thirteen years … Upon him the task of transcription mainly devolved" |
| C17 | Most of the *Tāj*'s additions were word for word in the *Lisān*; Lane often composed from the *Lisān* but named the *Tāj* | S | Preface p. xx: "from three-fourths to about nine-tenths … verbatim … very often to compose articles … principally from the Lisán … giving the latter [Tāj] as my authority in most instances" |
| C18 | "as nearly as possible in the words in which some person of authority has transmitted it" | S | Preface p. xxii |
| C19 | Nothing without an authority except bracketed additions | S | Preface p. xxvi |
| C20 | Modern Arabic helped him but "would frequently have misled me … since the classical age" | S | Preface pp. xxii–xxiii |
| C21 | Caution about guessing meanings "by means of analogy" | S | Preface p. xxiii |
| C22 | "Rather than reduce a root to one idea, he orders its senses by their relations" | **NQ** | Preface p. xxv supports the second half ("paid attention to their relations"). Nothing I read has Lane contrasting his method with reducing a root to one idea; that framing is the essay's own |
| C23 | Figurative marks show "genealogies"; he marks breaks and complete breaks | S | Preface p. xxv: "— … a break in the relations"; "== … a complete, dissociation" |
| C24 | "Classical" = pre-Islamic poets and those who lived into Islam; the age "nearly ended with the first century" | **NQ** | Preface pp. viii–ix: Jāhilī and Mukhaḍram poets are absolute authorities. Lane also says the best Islāmī poets "are generally regarded, as holding classical rank" (with lesser authority), which is why the age runs to about the end of the first century |
| C25 | The Arabs held the Qur'an to be the highest authority | S | Preface p. ix: "The highest of all authorities … is held by the Arabs to be the Kur-án" |
| C26 | Post-classical words excluded "with very few exceptions" | S | Preface p. xxvi |
| C27 | Abbreviations S, K, TA, Msb, A, M, L, Mgh, Kur, Bd, Jel, KT | S | Preface p. xxxi, table IV (image checked) |
| C28 | Grouped initials agree "essentially, or mainly; but not always … in words" | S | Preface p. xxvi |
| C29 | Senses joined by "or": "one is right in one instance, and another in another" | S | Preface p. xxv |
| C30 | Aor. = aorist (imperfect), often shown by its vowel alone; inf. n.; i. q. = idem quod | S | Preface p. xxix, table II ("Aor., for aorist"; "Inf. n., for infinitive noun"; "I. q., for idem quod"). "Vowel alone" matches the displayed entries (e.g. "aor. ـُ") |
| C31 | "Tropical" = *majāz*; ‡ = affirmed by an authority, generally the Asās; † = Lane's own judgment. Our text has "(tropical:)" and "(assumed tropical:)" | S | Preface p. xxv. Table p. xxix: "Tropical, مَجَاز and مَجَازِىّ"; "‡ means asserted to be tropical … † supposed by me to be tropical". Print p. 1749 ‡/† match the stored "(tropical:)"/"(assumed tropical:)" |
| C32 | ↓ flags a word explained under another headword | S | Preface p. xxiv: "an arrow-head … to render conspicuous a word explained in a paragraph headed by another word" |
| C33 | صوم excerpt | S | Entry 5692; the validator passes |
| C34 | Apart from brackets and †, every claim in the excerpt is credited to someone else | S | Entry 5692 as excerpted |
| C35 | The *Tāj* calls "he abstained" the primary sense | S | Entry 5692: "this is the primary signification: ( TA :)" |
| C36 | The *Miṣbāḥ*, finished 734 AH (1333–4 CE), sets "the proper language of the Arabs" against "the language of the law" | S | Preface p. xvi ("finished its composition in the year of the Flight 734"). Entry 5692 |
| C37 | The *Mughrib* is a lexicon of words in traditions and legal works; for it, "abstaining from eating" is the proper sense and fasting a secondary application | S | Preface p. xv. Entry 5692 |
| C38 | KT = *Kitāb al-Taʿrīfāt*, which gives the daybreak-to-sunset definition | S | Preface p. xxxi ("KT, The 'Kitáb et-Taareefát'"). Entry 5692 |
| C39 | Al-Khalīl, through the *Ṣiḥāḥ*: "the standing without work" | S | Entry 5692: "accord. to Kh … ( S .)". Table: Kh = El-Khaleel |
| C40 | Ibn ʿAbbās's reading of Q 19:26 is filed under † | S | Entry 5692: "(assumed tropical :)". Print p. 1749 shows † |
| C41 | Horse, wind and water senses carry ‡ or † | S | Entry 5692: horse †, wind ‡, water † |
| C42 | Sense order is an arrangement by relation, not a dated history | S | Preface p. xxv |
| C43 | Lane's xix. 27 = Q 19:26 and ii. 181 = Q 2:185 on this site | S | `verses` table: 19:26 contains إِنِّى نَذَرْتُ لِلرَّحْمَٰنِ صَوْمًا; 2:185 contains شَهْرُ رَمَضَانَ … فَمَن شَهِدَ |
| C44 | حنف excerpt; the explanations are lined up without a verdict | S | Entry 6343; the validator passes |
| C45 | Al-Rāghib: *mayl ʿan al-ḍalāl ilā l-istiqāma*; the *ḥanīf* is one who so inclines; the Arabs called anyone who made the pilgrimage or was circumcised *ḥanīf* (translation checked) | S | Entry 6348 original: الحنف: هو ميل عن الضلال إلى الاستقامة … والحنيف هو المائل إلى ذلك … وسمت العرب كل من حج أو اختتن حنيفا |
| C46 | The verdict that al-Rāghib explains ḥanaf "better" is tagged TA (p. 658) | S | Entry 6343: "… better, … ( TA .)". Print p. 658 (image) |
| C47 | Abū ʿUbayda's report "stands, unreconciled, beside glosses meaning 'a Muslim'" | **NQ** | Entry 6343: AO's own report goes on "and when El-Islám came, they thus called the Muslim". So AO links the two usages himself. What is true is that Lane does not weigh the explanations |
| C48 | The *Mughrib* flags "a Muslim" as "a conventional term" | S | Entry 6343: "a conventional term of the professors: ( Mgh :)" |
| C49 | Lane saw five parts through the press (1863–74) | S | DNB: "The succeeding parts came out in 1865, 1867, 1872, 1874", after the 1863 part |
| C50 | He died 10 Aug 1876 while working on the article قد | S | Editor's Preface (image): "engaged on the article قد" |
| C51 | "Up to that point … every article ready for the printers; 'of the rest the majority are written, but some need collation'" | **NQ** | The quotation is accurate (Editor's Preface). But the same paragraph says Lane "was of necessity obliged to write in the order of the Ṣiḥāḥ" (by last radical) and found articles "in three different stages". The essay leaves this out, so "up to that point" reads as "every root before قد". Its own example contradicts that: قتل comes before قد, yet p. 2487 of the main text has "[قتع قتل قتم قتن قتو See Supplement.]" |
| C52 | Lane-Poole published ghayn and fāʾ in 1877, and qāf to yāʾ in 1885 and 1893 | S | Editor's Preface ("contains only غ and ف"). Title pages Part 7 (1885) and Part 8 (1893). DNB |
| C53 | Instead of writing the missing articles from the *Tāj* (by then printed at Būlāq), he added a Supplement of Lane's notes | S | Postscript 1893 |
| C54 | Postscript quotes: "not to be accepted as the final decision of their writer"; "most familiar to the student will often be found missing" | S | Postscript 1893 (the reprint puts it after Part 5) |
| C55 | Book II never appeared | S | Postscript 1893 ("the materials are wanting") |
| C56 | Haywood called the 1877 statement inaccurate and the lexicon "a very inadequate reference work" after that article | S | Haywood p. 125: "showed how inaccurate this statement was … a very inadequate reference work after the article 'qadda'" |
| C57 | Our قتل entry is a Supplement note, p. 2984 | S | Main text p. 2487: "قتل … See Supplement". Supplement p. 2984 (running head قبل–قتل). Text matches entry 729 |
| C58 | The قتل excerpt cites al-Bayḍāwī on Q 4:157 and never glosses the verb as "he killed" | S | Entry 729 ("Bd in iv. 156" = Q 4:157 on the site) |
| C59 | Lane shows the recorded range and who records it; he cannot decide a verse | S | Follows from C19 and C27 (interpretive, fairly framed) |
| C60 | A tag dates a book, not a usage; in *ṣawm*, Ibn ʿAbbās reaches Lane through the *Ṣiḥāḥ* | S | Entry 5692: "( S , M ) by I'Ab ( S )" |
| C61 | Bd and Jel are commentators' readings | S | Table p. xxxi: expositions of the Kur-án |
| C62 | Labels such as "language of the law" or "post-classical" mark specialised or later use; their absence proves nothing | S | Interpretive. Consistent with pp. xxii and xxvi |
| C63 | Stored text = the Perseus/Tufts digitisation of the London printing, corrected on hawramani | S | Perseus biblio note; hawramani page. Minor: hawramani worked from an intermediate TXT by Navid-ul-Islam |
| C64 | ‡ → "(tropical:)", † → "(assumed tropical:)", dash → b2…, double rule → A2… | S | Perseus shows "-b2-" and "-A2-". Print p. 31 and p. 1749 compared with the stored text |
| C65 | A stray "CCC" in a few entries "is a conversion error" | **NQ** | 22 displayed entries contain "CCC". No source I found says what causes it; "conversion error" is inferred |
| C66 | 427 of the 1,410 roots begin with qāf to yāʾ and come from the 1885 and 1893 parts | S | `roots` count: 1410 total, 427 in ق–ي |
| C67 | Nothing in the stored text says whether an entry is a finished article or a Supplement note | S | Entry 729 has no marker |
| C68 | A "كفل كفن كفى See Supplement" line is a cross-reference, not part of the entry | S | Entry for kfr. Print p. 2487 shows the same pattern |
| C69 | Lane's verse numbers often differ from standard numbering, and the English versions repeat them | S | Entry 5692 harmonized: "cf. Qur'an 2:181", "Qur'an 19:27" |
| C70 | Source note: DNB dates the last part 1892 but the part is dated 1893 | S | DNB (Wikisource) "1877, 1885, and 1892". Part 8 title page 1893 |

**Totals:** 70 claims. 64 supported, 6 need qualification, 0 unsupported.

## Flagged items and fixes

1. **C51 (must-fix).** The essay presents "Up to that point, … every article ready for the printers" with no context, then shows قتل (which comes before قد) as a Supplement note. A reader will see a contradiction.
   - **Fix:** after "in the letter qāf", add that Lane had written in the order of the *Ṣiḥāḥ*, arranged by a root's last letter, so Lane-Poole found articles "in three different stages". Even some qāf roots before قد, such as قتل, were never written up [^lane-poole|Editor's Preface, 1877].
   - Keep the collation quote and Haywood.
   - This also explains the qtl paragraph that follows.
2. **C11.** "you can tell, line by line, whose voice you are hearing" overstates it.
   - **Fix:** "you can tell, line by line, which source Lane is reporting and where he speaks himself".
   - Optionally add that a TA tag may stand for matter he took from the *Lisān* [^lane-preface|p. xx].
3. **C22.** Delete "Rather than reduce a root to one idea,". Start with "He orders its senses by their relations…". The contrast is the essay's, not Lane's.
4. **C24.** Change to: "the Arabic of the pre-Islamic poets and of those who lived into Islam, with the best early Islamic poets also holding classical rank, an age that 'nearly ended with the first century' of Islam" [^lane-preface|pp. viii–ix].
5. **C47.** Change to: "Abū ʿUbayda's report that idol-worshippers called themselves *ḥanīf*, and that the name passed to Muslims with Islam, sits beside the other glosses with no verdict from Lane."
6. **C65.** Change to: "A stray 'CCC' in some entries is not Lane's; it appears to be an artefact of the digital text." It occurs in 22 displayed entries, so "some" fits better than "a few".

## Brief issues

- **suggestion:** The titleGloss (two meanings of *Madd al-Qāmūs*) is Lane's own explanation (Preface p. xxxii), but nothing on the page says so. Add a short clause in the body or onOurSite: "Lane's Arabic title, *Madd al-Qāmūs*, has, he says, 'two meanings'" [^lane-preface|p. xxxii].
- **suggestion:** "Later senses, such as a horse standing unfed…" can be read as chronologically later. Say "Senses further down the entry…" instead. The next paragraph insists the order is not a history.
- **suggestion:** "The commonest are S … K … TA…" is an unverified frequency claim. Say "Those you will meet most in the examples below are…" or just "They include…".
- **suggestion:** The abbreviation paragraph is list-like. It is acceptable as reference, but keep it tight.
- **suggestion:** Word count is 1,099, at the limit. Offset any wording added for fixes 1 and 4 with cuts, for example in the Golius sentence or the CCC sentence.
- **suggestion:** onOurSite could warn that the default English version drops the source tags and the ‡/† marks and can add framing Lane does not give (see site-data issue 4), so readers should check "Original Text" for whose sense is whose. This belongs in onOurSite, not the shared box.

## URLs

All URLs open and point to the stated works:
- archive.org/details/LAB1865AREN (Lane; this reprint also contains Lane-Poole's preface and postscript)
- archive.org/details/in.gov.ignca.12555 (Haywood 1960)
- en.wikisource DNB "Lane, Edward William"
- Perseus `doc=ASl`
- arabiclexicon.hawramani.com Lane page

Other notes:
- laneslexicon.github.io is named in a citation without its own URL. It opens, but I did not use it; everything above was checked against the archive.org scans.
- No source is listed but unused.
- The "lane-poole" source points to the LAB1865AREN item. That is correct, but the Editor's Preface and Postscript sit in the volume labelled "VOL. 5" (after Part 5). A locator note would help.

## Validator

`node scripts/validate-dictionary-guides.mjs lane-lexicon` → **ok**: 4 root links, 3 excerpts, 1,099 words, 1/1 guides pass.

## Site-data issues

1. **`name_ar` holds "Lane's Lexicon".** That is not an Arabic title. Lane's Arabic title is مدّ القاموس (1863 title page; Preface p. xxxii).
2. **Stored date 1876** is Lane's death. That is fine for ordering, but the posthumous parts run to 1893 (a note only).
3. **"CCC" artefacts** appear in 22 displayed Lane entries (e.g. kfr, jEl, Zlm, nfs, nzl, wld, frq, dwr, jhd).
4. **The Swm harmonized English (the default view) attributes to Lane things he does not say.**
   - It ends: "Throughout, Lane traces every sense back to a single underlying idea: standing still, holding back, or abstaining."
   - It heads the figurative senses "all built on the idea of stillness/holding-back".
   - It says "Lane reports this as the primary, original meaning", when that is the *Tāj*'s statement, tagged TA.
   - None of this is in Lane's text, and it contradicts the guide's (correct) account.
5. **English versions repeat Lane's verse numbers** (e.g. "Qur'an 2:181", "Qur'an 19:27" in Swm). If these become verse links on the site, they point to the wrong verses (Q 2:181 and Q 19:27 instead of Q 2:185 and Q 19:26).
