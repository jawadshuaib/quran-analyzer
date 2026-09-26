# Revision round 2: salmone-dictionary

Reviser: drafting-side reviser, 2026-09-26, working from `verification-r2.md`.
Guide: `roots/frontend/src/content/dictionary-guides/guides/salmone-dictionary.ts`
Validator after revision: **ok**. 7 root links (7 distinct pairs), 5 excerpts, 1,088 words (lede and body). onOurSite is about 155 words, down from about 163.

I opened every source below myself in this round. The page images are from `https://archive.org/download/arabicenglishdic0000unse/page/n{leaf}_w1000.jpg`, and I viewed each one directly. I also re-read the full-text OCR (`arabicenglishdic0000unse_djvu.txt`).

## Flagged claims

### C16 [NQ, locator]: preface "signed at University College on 21 November 1889"

**Action:**
- Added `[^salmone-1890|p. x]` straight after "…21 November 1889,". The `[^salmone-1890|p. vii]` citation stays after "a living language", which it supports.
- Took the verifier's optional fix too. "Letters (a), (b), (c) number the senses" now carries `[^salmone-1890|"Notes", before p. xv]`, the same locator the next paragraph uses for the Notes page. The p. xv citation now covers only the quotation that follows it.

**Evidence (opened):**
- **p. x (leaf n11), image viewed.** The page head reads "X PREFACE." The foot of the page reads "H. ANTHONY SALMONÉ. / 21st November 1889. / UNIVERSITY COLLEGE, / LONDON."
- **"Notes" page (leaf n14, unnumbered), image viewed.** Item 4 reads: "(a), (b), (c) &c. represent the 1st, 2nd, 3rd &c. meanings of the verb or derived form."

### C71 [NQ]: "Perseus set a reconstructed Arabic form beside each of the print's pattern numbers and Roman numerals"

**Action:** I used the verifier's wording: "The Perseus text sets a reconstructed Arabic form beside each of the print's pattern numbers and Roman numerals; our copy keeps the forms but drops most numbers and the present-tense vowel letters."
- The sentence now describes what the Perseus text contains. It no longer says who added the forms.
- The page's other statement about Perseus is unchanged. It says only that hawramani took the Perseus text and quotes Perseus's imprint line.

**Evidence:** no new evidence is needed for this narrower wording. Round 2 already confirmed the forms beside the numbers in Perseus rbb ("رَبَّبَ II", "رُبُوْب 27") and dnw ("دَنَاوَة [ 22t ]"), and confirmed that the print has numbers only (p. 257, which I viewed again this round; p. 160).

### C25 [U]: source gbooks, "Google Books record … (al-Biruni, 1976)"

**Action:**
- Deleted the `gbooks` entry from `sources`.
- Deleted the `[^gbooks]` marker after "reissued in the 1970s".
- The sentence still rests on `[^openlibrary]`. Round 2 verified that record as Beirut: Librairie du Liban, 1972.

I did not try to get past Google's CAPTCHA, so the al-Biruni 1976 imprint is no longer claimed anywhere on the page.

## Brief suggestions

- **Lede, "packs a whole root into a few compact lines".** Changed to "packs a whole root into one compact article".
  - I did not use the verifier's "a compact paragraph", because the p. 257 image (leaf n282) shows it would also be inexact.
  - The ر ب ب article is printed as four blocks: the verbs ("رب U (n. ac. 1), Was, became lord…—VIII, see V."), the nouns ("1, (pl. 27, 38), Lord, master…Divine."), "N.P.I, Slave, bondman, serf…", and "N.P.II, (pl. …), Preserve, jam…".
  - "Article" is the book's own unit ("Each article follows a fixed order", p. xvii, already cited) and implies no count of lines or paragraphs.
- **Summary, the same figurative issue (not flagged).** "…in a few lines of English equivalents" is now "…with terse English equivalents", for consistency with the lede. The summary is 36 words.
- **onOurSite length (about 163 words).** Cut the "see 21 (a)" gloss. The sentence now reads: 'Cross-references survive: "see V" means the fifth-form verb in the same entry.'
  - The result is about 155 words.
  - I kept the صَلَّوَ example. It is the only repair note tied to a root a Qur'an reader is likely to open (ص ل و), and it shows concretely what "reconstructions misfire" means.
- **Total length (1,089 words).** Now 1,088. I added nothing new to the body and did not pad.
- **"Mussulman" and the stored slm entry.** Not adopted.
  - Round 2 already rated the claim supported on p. xvii, the plural note with مسلم "Mussulman".
  - Adding the stored س ل م entry would mean another root link and about 15 more words, which would push the page past 1,100.

## Removed claims

- **C25:** the Google Books source record, "Habib Anthony Salmoné, *An Advanced Learner's Arabic-English Dictionary: Including an English Index* (al-Biruni, 1976)", with its URL and in-text marker.
- **C71 (attribution only):** the claim that Perseus added the Arabic forms.
- **Trimmed but not flagged:** the onOurSite gloss 'see 21 (a)' = "the first sense of the pattern-21 noun", which round 2 had verified.
- **Reworded, not removed:**
  - The lede's "a few compact lines" is now "one compact article".
  - The summary's "in a few lines of English equivalents" is now "with terse English equivalents".

## New claims

No new factual claims. The two added citations point to evidence for claims that were already on the page:

1. **`[^salmone-1890|p. x]` for the preface date and place.** Source: p. x (leaf n11), image viewed. It reads: "H. ANTHONY SALMONÉ. / 21st November 1889. / UNIVERSITY COLLEGE, / LONDON."
2. **`[^salmone-1890|"Notes", before p. xv]` for "(a), (b), (c) number the senses".** Source: Notes item 4 (leaf n14), image viewed. It reads: "(a), (b), (c) &c. represent the 1st, 2nd, 3rd &c. meanings of the verb or derived form."
3. **Wording change "one compact article", listed for the next verifier.** It makes no factual claim beyond what p. xvii and the entries already support. p. xvii says "Each article follows a fixed order"; the p. 257 layout is described above.

## Disputed

None. I accepted all three flags as stated.

## Site-data issues (unchanged, confirmed)

- **The stored date 1889 is not a death year.** It is the preface date (p. x, 21 November 1889) and the year in the Perseus imprint line. The book was published in London in 1890 (title page). The compiler's death year is not established.
- **The stored title is the reissue title.** The original title is *An Arabic-English Dictionary on a New System* (1890).
- **The stored text drops the print's root-level asterisk.** Mid-entry asterisks survive as the literal string `_ast;` in 24 entries.
- **The Harmonized English for rbb (entry 129) and Amn (entry 9) calls the work "English-Arabic".** It is Arabic–English. (Reported by verification r2; I did not re-check it.)
- **The Harmonized English for TbE (entry 6655) adds interpretive material and a "modern derivatives" label that the original lacks.** (Reported by verification r2; I did not re-check it.)
