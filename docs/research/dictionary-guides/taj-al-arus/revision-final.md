# Tāj al-ʿArūs — final conservative pass (2026-09-26)

Scope: the claims still flagged after verification rounds 1–3. One item was open (C71, needs-qualification). No brief issues were open.

## C71 — "Already mentioned" / "will come" (onOurSite)

**Flag (verification-r3):** The claim is true, but the locator `[^haywood|p. 88]` supports only part of it. Haywood p. 88 says the *Qāmūs*'s "choice of the rhyme order was deliberate". It does not say that the order runs by the last letter. That definition is on p. 69.

**Action: citation corrected. The sentence was kept unchanged.**
- In `onOurSite`, `[^haywood|p. 88]` became `[^haywood|pp. 69, 88]`.
- In `sources`, the `haywood` citation's range "pp. 88–90" became "pp. 69, 88–90".

This is the fix verification-r3 prescribed. It adds no factual claim and changes no wording in the essay.

**Checked again in this pass:**
- **Haywood OCR** (https://archive.org/download/in.gov.ignca.12555/12555_djvu.txt), fetched fresh.
  - p. 69: "Within these chapters, words were arranged in alphabetical order according to the last radical. Thus, the rhyme order was only used in subsections…"
  - p. 88: "First we must accept that the choice of the rhyme order was deliberate and considered."
  - Not used: p. 68 (the start of ch. 6) also defines the rhyme arrangement as the one "by which roots were listed according to their final radicals". I did not add this locator, because it is outside the evidence recorded in the r1–r3 verification files.
- **Stored Slw entry.** `_dict_guide_tool.py grep` finds «وقد ذكرنا شيئا من ذلك في حرف الثاء المثلثة» in the displayed صلو entry. It is the only match.

## Removed claims

None. The one flagged claim was kept, with a corrected citation.

## New claims

None.

## Validator

`node scripts/validate-dictionary-guides.mjs taj-al-arus`: "taj-al-arus — ok"; 1/1 guides pass.
- 11 root links (10 distinct root/dictionary pairs); 4 excerpts.
- 1,130 words (lede + body). This is 30 words over the house range. Verification-r3 raised it only as a suggestion (B1), and no brief issue is open. Nothing was trimmed, because this pass only removes or neutralises flagged claims.

`limitedEvidence` was not added. The page is not deliberately short.
