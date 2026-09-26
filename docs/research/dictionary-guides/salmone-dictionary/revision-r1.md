# Revision round 1: salmone-dictionary

Reviser: drafting-side reviser, 2026-09-26, working from `verification-r1.md`.
Guide: `roots/frontend/src/content/dictionary-guides/guides/salmone-dictionary.ts`
Validator after revision: **ok**. 7 root links, 5 excerpts, 1,089 words (lede and body). onOurSite is 163 words.

I opened every source below myself during this round. Page images of the 1890 print come from `https://archive.org/download/arabicenglishdic0000unse/page/n{leaf}_w1000.jpg`, and I viewed each one directly.

## Flagged claims

### C60 [U]: onOurSite "Ignore the string '_ast;'."

**Action:** deleted and replaced with: `"_ast;" is the print's modern-usage asterisk, kept before some forms but dropped from root headings.` The asterisk convention itself is now explained in the body (see C31).

**Evidence (opened):**
- **"Notes" page (leaf n14, unnumbered, before p. xv), item 10:** "The asterisk indicates that the root or most of the derived forms are used in the modern language."
- **p. 595 (leaf n620):** the علم article has "* (ـِ) A (n. ac. 2) [acc. or Bi], Knew, was acquainted with". The asterisk sits beside the kasra form, not the root line. Our stored Elm entry has "_ast; عَلِمَ(n. ac. عِلْم) a. [acc. or Bi], Knew…".
- **"kept before some forms":**
  - `_dict_guide_tool.py grep … '_ast;'` finds 24 displayed entries.
  - In all 24, `_ast;` is mid-entry, directly before a verb form (Elm, nfs, qbl, kvr, kbr, slm, …).
  - `grep … '^\S+\s+_ast;'` (asterisk straight after the root heading) finds 0 entries.
- **"dropped from root headings":**
  - p. 22 (leaf n47) prints "* أَمَنَ I (n. ac. 1), Believed, trusted in." Stored Amn (entry 9) begins "ءمن أَمَنَ(n. ac. أَمْن)…", with no asterisk.
  - p. 490 (leaf n515) prints an asterisk beside طبع. Stored TbE (entry 6655) begins "طبع طَبَعَ(n. ac. طَبْع)…", with no asterisk.

### C31 [NQ]: [coll.] "a warning when present, not a guarantee when absent"; طبع / "Printing-press"

**Action:**
- I rewrote the abbreviation paragraph. It now names both of the print's modern-usage devices, each quoted from the Notes: "[coll.]" after a meaning that is "especially modern or used in the colloquial language only", and the asterisk "that the root or most of the derived forms are used in the modern language".
- I kept the طبع observation, which now reads: "'Printing-press' carries no [coll.]. In the print, the only mark that covers it is an asterisk beside the root,[pp. 490–491] and our copy drops that."
- I dropped the phrase "a warning when present, not a guarantee when absent" and replaced it with "Both marks are coarse."

**Evidence (opened):**
- **p. 490 (leaf n515), right column, about line 52:** an asterisk stands beside the root طبع, and its line begins "A (n. ac. 1) [acc. or 'Ala], Stamped, sealed; made an impression or mark on; printed (book)…".
- **p. 491 (leaf n516), left column:** "—20t, (pl. 44), Printing-press." carries no [coll.] and no asterisk. The [coll.] tags on this page belong to other senses: "(e) [coll.], Was broken in, trained (animal)" and "N.P.II [coll.], Broken in, trained (animal)".
- **Conclusion:** the only modern-use signal covering "Printing-press" in the print is the asterisk at the root on p. 490. Our stored entry has no asterisk.

### C50 [NQ]: How to use, "flags modern usage only some of the time"

**Action:** now reads "It flags modern usage only coarsely, and our copy loses part of that marking." This is the verifier's wording, split out of the previous sentence.

**Evidence:** the same as C31 and C60.

### C42 [NQ]: "'Doctor of the sacred law' is the English of a later learned title."

**Action:** I removed the dating judgment. The passage now reads: "'Doctor of the sacred law' sounds like a scholar's title, and nothing in the entry says whether the word meant that in the Qur'an's time. The verses themselves have to decide." This makes no claim about when the sense arose.

### C55 [NQ]: Perseus "spelled the print's pattern numbers and Roman numerals out as Arabic words"

**Action:** now reads "Perseus set a reconstructed Arabic form beside each of the print's pattern numbers and Roman numerals; our copy keeps the forms but drops most numbers and the present-tense vowel letters."

**Evidence (opened):**
- **Perseus rbb, fetched from** `https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A2002.02.0005%3Aalphabetic+letter%3Dr%3Aroot%3Drbb`:
  - "رَبَّ U ( n. ac. رَبّ 1 ), a. Was, became lord…"
  - "رَبَّبَ II , a. Reared, brought up."
  - "رَبّ 1 , ( pl. رُبُوْب 27 , أَرْبَاْب 38 )"
  - "رُبُوْبِيَّة 27yit , a. see 23t . b. Divinity, godhead."
  - The numbers are kept, and the Arabic form is added beside them.
- **"Most":** I changed "drops the numbers" to "drops most numbers" because some numbers survive in our copy:
  - stored rbb: "أَرْبَاْب 38" and "see 23tb"
  - stored TbE: "مَطْبَع مَطْبَعَة 17t"

### C61 [NQ]: dnw, "the rest sits under the spelling with final yāʾ"

**Action:** now reads "…show one line; in the Perseus text the rest, *dunyā* ("world") included, sits under دني, a spelling our site does not display.[^perseus|roots dnw and dny]"

**Evidence (opened):**
- **Perseus dnw:** "دَنَا U ( n. ac. دَنَاوَة [ 22t ] , دُنُوّ [ 27 ] ) a. [ Min or Ila ], Was near, drew near, approached." That is the whole entry.
- **Perseus dny:** "دَنِيَ A ( n. ac. دَنًا [ 4A ] , دَنَايَة [ 22tI ] ), a. Was vile, contemptible. دَنَّيَ II , a. Drew near, made to come near. … دَنَاوَة [ 22t ], a. Proximity, nearness. … دُنْيَا ( pl. دُنَي 9 ), a. World, this present world. دُنْيَوِيّ , دُنْيَاوِيّ a. Worldly, of the world."
- **Site:** `_dict_guide_tool.py find-root دني` returns "no match".

### C63 [NQ]: limitedEvidence, "the records we found disagree about his dates and cite no evidence"

**Action:** now reads "the few online records of his dates disagree with one another, most give no source, and we could not check any of them, so this page gives none." I did not adopt the verifier's proposed wording; see **Disputed**.

**Evidence (opened):**
- **Wikidata Q53421609:** born 1 September 1860, Beirut; died October 1904, London; "0 references" on each statement.
- **English Wikisource, Author:Habib_Anthony_Salmoné:** "(1860–1904)", "Syrian Professor educated in England". No source is cited.
- **Sue Young Histories blog** (`http://sueyounghistories.com/archives/2013/11/26/habib-anthony-salmone-1830-1895/`): the page title gives "Habib Anthony Salmone (1830-1895)" and names an obituary in *The Academy*, vol. 46 (1895), p. 556. I could not locate that obituary, so it is unchecked.

### C64 [NQ]: source "explanatory notes (pp. xv–xix)"

**Action:** changed to "(pp. xv–xxi)".

**Evidence (opened):** page heads in the IA scan:
- leaf n21: "XX … EXPLANATORY NOTES."
- leaf n22: "EXPLANATORY NOTES. XXI"
- leaf n23: "THE ALPHABET.(*)"
- leaf n24: "TABLE OF CONJUGATIONS. XXIII"

## Brief suggestions

- **Length (1,069 words, top of range).** Adding the asterisk convention cost words, so I trimmed elsewhere. Lede and body now total 1,089, inside the 700–1,100 range. I cut:
  - "We have found no reliable account of his life beyond that." The limitedEvidence note already says this.
  - "About a third of the entries we display carry at least one [coll.] (our count)."
  - The rbb participle gloss "Preserve, jam; sweetmeat, confectionery".
  - The full list of six language letters, now shortened to "letters such as P. (Persian) or T. (Turkish) flag words derived from another language". This paraphrases Notes 8: "showing that the word is derived from that language".
  - Words in onOurSite, which went from about 185 to 163 after the fixes.
- **Asterisk convention in the abbreviation paragraph.** Done; see C31.
- **"One word, one gloss" rests on one root.** The section now opens "The book's economy can flatten a contested word. One example is the entry for ح ن ف…". This replaces "shows most where a word is contested", so the section no longer implies the pattern holds for every contested word.
- **Google Books record blocked for automated tools.** I could not open either Google Books record myself: both redirect to Google's "sorry" page, and the Books API returned 429. I did not try to get around this. I did not add MS4KAQAAIAAJ, because I could not open it. Instead I added an Open Library edition record that opens (see **New claims**) as a second citation for "reissued in the 1970s". The gbooks citation stays, because the round-1 verifier confirmed its title through a search result.

## Removed claims

- C60: "Ignore the string '_ast;'."
- C42: "'Doctor of the sacred law' is the English of a later learned title" (the dating judgment).
- C55: Perseus "spelled the print's pattern numbers and Roman numerals out as Arabic words".
- C31: "Read the tag as a warning when present, not a guarantee when absent". The طبع example is kept but reframed.
- C63: "the records we found … cite no evidence". Too strong, because the blog names an obituary.
- Trimmed but not flagged:
  - "We have found no reliable account of his life beyond that." (C11; still stated in limitedEvidence)
  - "About a third of the entries we display carry at least one [coll.] (our count)." (C30)
  - The participle gloss "Preserve, jam; sweetmeat, confectionery" (part of C36)
  - The explicit list of all six language letters (part of C29)

## New claims

1. **The print had a second modern-usage device, an asterisk "that the root or most of the derived forms are used in the modern language".**
   - Source: salmone-1890, "Notes", item 10 (leaf n14; image viewed).
2. **"Printing-press" under طبع carries no [coll.]. In the print the only mark covering it is an asterisk beside the root, which our copy drops.**
   - Source: salmone-1890, p. 490 (leaf n515) shows the asterisk beside طبع.
   - p. 491 (leaf n516) reads "—20t, (pl. 44), Printing-press." with no mark.
   - Stored TbE entry 6655 has no asterisk.
3. **"_ast;" is the print's asterisk, kept before some forms but dropped from root headings.**
   - Sources: Notes 10; p. 595 (leaf n620) against stored Elm; p. 22 (leaf n47) against stored Amn; p. 490 against stored TbE; the grep counts given under C60.
4. **Perseus set a reconstructed Arabic form beside each number and numeral; our copy drops most numbers.**
   - Source: Perseus rbb page (quoted under C55).
   - Stored rbb and TbE, where some numbers survive.
5. **In the Perseus text the rest of د ن و, including *dunyā* ("world"), sits under دني, which our site does not display.**
   - Source: Perseus dnw and dny pages (quoted under C61).
   - `find-root دني` returns no match.
   - The gloss in Perseus is "World, this present world"; the guide's "world" is a shortened paraphrase in quotation marks.
6. **The book was reissued in the 1970s (added support).**
   - Source: Open Library edition OL15560928M, opened via WebFetch and via the JSON at `https://openlibrary.org/books/OL15560928M.json`.
   - Title "An advanced learner's Arabic-English dictionary", subtitle "including an English index", by statement "by H. Anthony Salmoné.", publisher "Librairie du Liban", place "Beirut", date "1972", pagination "xxiii, 1252, 179 p.". The record comes from an Oregon Summit MARC catalogue record.
   - The guide's sentence is unchanged: "reissued in the 1970s". It now cites [^openlibrary] as well as [^gbooks]. The page does not state the Beirut 1972 details in prose; they appear only in the source list.
7. **The online dates disagree, most give no source, and we could not check them (limitedEvidence).**
   - Sources: Wikidata, Wikisource and the blog, all quoted under C63.

## Disputed

- **C63, the verifier's proposed wording.** The verifier proposed "the only dates we found (1860–1904, in unreferenced online records) cite no evidence". That is not accurate. The drafting research already recorded, and I re-opened, a blog page (Sue Young Histories, "Habib Anthony Salmone (1830-1895)") that gives different dates, 1830–1895, and names an obituary in *The Academy* vol. 46 (1895), p. 556.
  - The original "disagree" was therefore correct.
  - The original "cite no evidence" was too strong, because the blog does name a source, although we could not check it.
  - The new wording, "disagree with one another, most give no source, and we could not check any of them", states both facts. The page still gives no dates.
  - The blog is not a reliable source and is not cited on the page. It is used only to show that the records disagree.

## Site-data issues (unchanged from verification r1, confirmed)

- The stored date 1889 is the preface date, and it is also the year in the Perseus imprint. It is not a death year. The book appeared in London in 1890. The compiler's death year is not established: unreferenced records give 1904, and a blog gives 1895.
- The stored text drops the print's root-level asterisk and keeps mid-entry asterisks as the literal string "_ast;" (24 entries).
- The Qur'anic root د ن و shows one line in Salmoné. The rest of the article, including دنيا, is filed under دني in the source, and the site does not display that spelling.
