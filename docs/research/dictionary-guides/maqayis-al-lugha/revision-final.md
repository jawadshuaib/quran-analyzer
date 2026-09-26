# Maqāyīs al-Lugha: final conservative pass (2026-09-26)

Input: the guide after revision r2 and verification r3. Three claims were still flagged "needs qualification": C17, C31 and C64. All three rest on Baalbaki, *The Arabic Lexicographical Tradition*. No round could open that book, because Google Books served a reCAPTCHA every time. One brief issue was open (B1): do not mark the page verified while a direct Baalbaki citation remains.

This pass removes every Baalbaki citation. It adds no new factual claim.

## Changes

| Claim | Before | After | Why |
|---|---|---|---|
| C17 (body, "A thesis in the preface", end of paragraph 3) | "The words are inherited; the analysis is his. Nor did he aim at an exhaustive lexicon, as Ramzi Baalbaki notes.[^baalbaki\|p. 349]" | "The words are inherited; the analysis is his." | No round opened p. 349, and no quotation of it was found. The paragraph now ends on a sentence that r3 marked supported (C16). |
| C31 (body, "How an entry works", after the *qabl* excerpt) | "Hārūn thought Ibn Fāris hardly ever failed to find the shared sense.[^harun-ed\|editor's introduction, p. 23] Baalbaki, by contrast, finds his proposed *uṣūl* "frequently arbitrary and unconvincing".[^baalbaki\|p. 351]" | "Hārūn thought Ibn Fāris hardly ever failed to find the shared sense;[^harun-ed\|editor's introduction, p. 23] entries like this one let a reader test that judgment." | The wording, the author and p. 351 are known only through Larsen (*JAS* 5, 2018, n. 21), and Larsen applies the phrase to Ibn Fāris's "etymologies" in general. What p. 351 actually describes (the *uṣūl*, the derivations or the *naḥt* analyses) is unverified, so the sentence is deleted. The new clause is a transition. It gives reading advice and states no fact. It keeps Hārūn's verdict framed as the editor's judgment, which the *qabl* entry just shown lets the reader weigh, so the paragraph does not end on the editor's praise alone. |
| C64 (sources) | Source `baalbaki`: "… pp. 348–56 (section on *al-Maqāyīs* and *al-Mujmal*); consulted in the Google Books preview", URL books.google.ca/books?id=cme7AwAAQBAJ&pg=PA349 | Source removed | Nothing in the text cites it now. The page range, the section title, "consulted in the Google Books preview" and the URL could not be confirmed (C64). |

## Removed claims

1. That Ibn Fāris did not aim at an exhaustive lexicon, attributed to Baalbaki, p. 349.
2. That Baalbaki finds Ibn Fāris's proposed *uṣūl* "frequently arbitrary and unconvincing", p. 351.
3. The Baalbaki source entry: pp. 348–56, the section title, the Google Books preview and the Google Books URL.

## Not added

- **Ejz replacement for C17.** r3 suggested this replacement: "under ع ج ز he says he has left words out 'for fear of repetition'" (entry 4076, "وما تركنا في هذا كراهة التكرار"). I did not apply it. It would be a new claim with a new root link, and this pass adds none. The evidence is recorded in verification-r3.md (C17) if a later round wants it.
- **Larsen as a source for C31.** r3 suggested this too. I did not apply it, because it would bring in a new source and a narrowed, second-hand attribution.
- **Hārūn's own qualification (r3 S3).** r3 cites intro p. 39, where Hārūn says Ibn Fāris "does not rely on the regularity of the measure in all the material". I did not add it, because it would be a new claim.

## Left as is

- Every other claim. r3 found all of them supported (64 of 67). The only claims r3 flagged are C17, C31 and C64, and all three are dealt with above.
- `onOurSite`: unchanged. It is 192 words against FORMAT's ≈60–150 (r3 S1). The sentence r3 suggested cutting ("Entries run from a single line to over a thousand words") covers something FORMAT asks this section to mention (very short and very long entries), so I kept it.
- "It had been read, though." (r3 S2): unchanged. r3 marked it supported.
- `limitedEvidence`: not needed. The page is not deliberately short: the lede and body run to 1,072 words.
- `lastVerified`: not set in this pass. No Baalbaki citation remains, so B1 no longer blocks it. Setting it is left to the orchestrator or a verification round, as in the other guides' final passes.

## Validator

`node scripts/validate-dictionary-guides.mjs maqayis-al-lugha` returns **ok**:

- 13 root links (9 distinct pairs);
- 3 excerpts;
- 1,072 words for the lede and body, excluding excerpts;
- 1/1 guides pass.

It gives 3 warnings, all from before this pass. Each is a `none` link (rdd in the body; rbb and rdd in onOurSite), and each is explained in its own sentence.

## Still open (not essay text)

- A person with ordinary browser access to Baalbaki 2014 (pp. 348–56) could restore a scholarly assessment later. Any restored sentence would need a new verification round.
- The site-data issues r3 reported are unchanged, and the database was not touched:
  - the doubled-root sections were never collected;
  - six entries carry a letter's closing chapter on longer words (kfr, jvm, SrT, r*l, nml, srd);
  - the kfr English renderings mislabel that material as belonging to the k-f root.
