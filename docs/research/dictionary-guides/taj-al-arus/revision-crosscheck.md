# Tāj al-ʿArūs: cross-guide consistency revision (2026-09-26)

Source of the issues: the cross-guide consistency critic. File edited:
`roots/frontend/src/content/dictionary-guides/guides/taj-al-arus.ts`.

## Changes applied

1. **Cross-links.** First body paragraph: "the *Qāmūs* was prized" now links the
   Qāmūs guide (`[[guide:al-qamus-al-muhit|*Qāmūs*]]`). In the brackets section,
   "Ibn Manẓūr's introduction to the *Lisān*" now links the Lisān guide
   (`[[guide:lisan-al-arab|*Lisān*]]`). Both slugs exist in `guides/`; the
   italic-label pattern is already used in al-qamus-al-muhit.ts and
   al-misbah-al-munir.ts.
2. **Summary, second sentence.** "Useful for finding who recorded a meaning
   and on what evidence, once its several voices are told apart." became "It
   often shows who recorded a meaning and on what evidence; on our site the
   *Qāmūs*'s words are not always bracketed apart." (44 words in all.)
   Deviation from the critic's wording: added "often". The guide itself reports
   Lane's complaint that al-Zabīdī took most of his additions from the *Lisān*
   without saying so, so an unqualified "It shows who recorded a meaning" would
   contradict the body.
3. **Headings.** "Whose words are these?" became "Brackets, markers and a
   borrowed self-portrait". Deviation: the critic proposed "…a borrowed
   preface". Only 28 lines of the introduction are borrowed, not the whole
   preface, and the section already calls the passage "the modest self-portrait
   [that] is borrowed". "What it can and cannot settle" became "As old as its
   sources", which echoes the section's closing sentence.
4. **Stock closing line deleted.** "It cannot tell you what a word means in a
   particular verse, nor date a usage." The same point is made concretely in
   the fasād section ("to be weighed against that verse's context"), the ṣalāt
   section ("The entry does not decide how a given verse uses *ṣalāt*") and the
   ṣ-l-ḥ paragraph ("Nor does an entry date its witnesses").
5. **Lede ending.** "Reading an entry well means keeping track of voices: …"
   became "Its entries interleave three voices: the *Qāmūs*, al-Zabīdī himself,
   and the many scholars he quotes." Deviation: the critic proposed "Each entry
   interleaves at least three voices". I checked the shortest displayed entries.
   لقب (lqb) names no quoted scholar at all, and دين (dyn) is defective (it runs
   into another root's text). So "each entry" is false for our copy, and "at
   least" is redundant next to "the many scholars". The generic plural
   describes the work without making a universal claim.

## New claims

- Summary: "on our site the *Qāmūs*'s words are not always bracketed apart."
  This is not new evidence. It restates onOurSite ("In roughly a third of
  entries by our count … the *Qāmūs*'s words are not bracketed"), which was
  verified in verification-r1 C55 (531/1,600), r3 C66 (488–521/1,600) and r4
  C66 (477–521/1,600). Rechecked today with SQL on the displayed set
  (review_status='approved', not hidden, harmonized_en non-empty): 23 of 1,600
  have no "(" at all, and 106 have fewer than three. Most unbracketed entries
  still contain "(" around verse lines, which is why the earlier heuristics
  exclude verse and sura brackets. Kfr and xlq, the onOurSite examples, were
  confirmed in r1/r3/r4. Supported.
- Lede: "Its entries interleave three voices …". This claim was already in the
  lede ("keeping track of voices: the *Qāmūs*, al-Zabīdī himself, and the many
  scholars he quotes"). Spot check of the shortest displayed entries: دسو (dsw)
  has the bracketed Qāmūs, al-Zabīdī's "أهمله الجوهري", al-Layth and Ibn
  al-Aʿrābī. سوح (swH) has the bracketed Qāmūs, Kurāʿ and al-Jawharī. دخر
  (dxr) has the bracketed Qāmūs, al-Zajjāj and *al-Asās*. غصب (gSb) has the
  bracketed Qāmūs, al-Azharī and *Lisān al-ʿArab*. A regex for attribution
  words (قال|قاله|نقله|عن ابن|عن ابي|الجوهري|الازهري|الليث|شيخنا) matches
  1,599 of 1,600 displayed entries (a loose check, since قال also matches
  يقال). Exception: لقب (lqb). Hence the generic plural rather than "each".
  Supported as a characterisation.
- No other factual content was added. The deleted sentence and the renamed
  headings remove no claim that is not made elsewhere in the essay.

## Validator

`node scripts/validate-dictionary-guides.mjs taj-al-arus`: ok. 11 root links,
4 excerpts, 1,111 words (lede + body), no warnings.
