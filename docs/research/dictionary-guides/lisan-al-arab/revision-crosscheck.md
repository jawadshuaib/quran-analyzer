# Lisān al-ʿArab: cross-guide consistency fixes

Reviser: cross-check revision agent, 2026-09-26.

Input: two issues from the cross-guide consistency critic, one [cross-link] and one [sameness].

Files edited:
- `roots/frontend/src/content/dictionary-guides/guides/lisan-al-arab.ts`
- this log

Nothing else was touched.

Validator after revision (`node scripts/validate-dictionary-guides.mjs lisan-al-arab`): **ok, 1/1 pass, 0 errors**. Lede and body now total 1,096 words (was 1,097). There are 12 root links and 3 excerpts, both unchanged. The only warnings are the two deliberate `none` links (slm, Slw) in onOurSite, which are explained in the sentence that contains them.

## Changes

1. **Cross-link, applied as specified.** In "Five books in one":
   - "Ibn Sīda's *al-Muḥkam*" is now "Ibn Sīda's [[guide:al-muhkam|*al-Muḥkam*]]".
   - "al-Jawharī's *al-Ṣiḥāḥ*" is now "al-Jawharī's [[guide:al-sihah|*al-Ṣiḥāḥ*]]".

   Both slugs are in registry.ts (`ibn-sida-…` maps to `al-muhkam` and `ismail-bin-hammad-al-jawhari-…` maps to `al-sihah`). The inline renderer (`utils/dictionary-guide-markup.tsx`) renders the label recursively, so the italic inside it displays.

2. **Heading, applied as specified.** "## What it can and cannot settle" is now "## A survey, not a verdict". The new heading fits the paragraph's opening ("Use the *Lisān* as a survey…") and Haywood's remark in the previous section that Ibn Manẓūr "tends merely to repeat what both have said". One caveat: the heading echoes lane-lexicon's "## Many voices, no verdict", since both use "verdict". The echo is mild, but I leave it for the critic to judge.

3. **Stock formula, applied with a qualification.** The critic proposed changing "Nor is its date the date of its evidence. Its sources were already old —" to "Its evidence is older than the book, and its sources were already old —". The final text reads "**Most of** its evidence is older than the book**:** its sources were already old —".
   - I added "Most of" because the critic's version says all of the evidence predates the book. The displayed entries show that this is not quite true (see New claims).
   - The colon replaces ", and" so that "older than the book" and "already old" no longer sit side by side as two statements of the same point.

## New claims

**N1: "Most of its evidence is older than the book."** SUPPORTED as qualified.
- Why it holds for most of the evidence:
  - Ibn Manẓūr's introduction says the book gathers what was scattered in five earlier works (Dār Ṣādir vol. 1, pp. 7–8, already cited as `lisan-ds`).
  - The same sentence dates two of those sources by their authors' deaths: al-Azharī in 370/981 and Ibn al-Athīr in 606/1210 (Baalbaki 2019, p. 202, already cited).
  - Ibn Manẓūr lived 630–711/1232–1311.
- Why "most" and not "all": I opened his own signed remarks in the displayed entries (`_dict_guide_tool.py grep ibn-manzur-lisan-al-arab "محمد بن المكرم|ابن المكرم"`, 22 matching entries; the guide's count of 24 also includes variant signatures). A few of them bring in the usage or testimony of his own day:
  - **vql (ثقل):** he corrects Ibn al-Athīr on the *mithqāl* and gives "وزِنة المِثْقالِ هذا المُتعامَلِ به الآن", "the weight of this *mithqāl* in use now", measured against the raṭl of Egypt.
  - **dwr (دور):** he quotes a marginal note "بخط سيدنا الشيخ الإِمام المفيد بهاء الدين … بن النحاس النحوي، فسح الله في أَجله". The blessing "may God lengthen his term" shows the scholar was alive when Ibn Manẓūr wrote.
  - **Trq (طرق):** "ما أَعرف نجماً يقال له كوكب الصبح ولا سمعت من يذكره", "I know of no star called the morning star, nor have I heard anyone mention it". This is his own testimony.
- These additions are rare against 1,452 entries, so "most" is accurate. The unqualified wording would not be.

No other factual content was changed. The claims in the edited sentences (the *yamm* gloss, the death dates, *buḥrān* flagged *muwallad*) are unchanged and were verified in verification-r3 (C60 and others).

## Not applied / disputed

None of the actions was rejected. Change 3 departs from the critic's exact wording (see above). A related observation for the critic: "## Whose words are these?" is shared by lisan-al-arab and taj-al-arus. It was not raised for this guide, so I did not change it.
