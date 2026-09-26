# tuhfat-al-arib — verification of the cross-check revision (round 99, 2026-09-26)

Independent check of the single change logged for the cross-guide consistency pass. Research notes and revision logs were not used as evidence. The only revision log read was the file naming the change under review.

## Changed passage

Lede, first sentence: "*Tuḥfat al-Arīb* is less a dictionary than a glossary." became "*Tuḥfat al-Arīb* is a glossary."

**Verdict: SUPPORTED.** The edit removes framing and adds no new fact. The claim left behind, that the work is a glossary, is backed by two things:

- **The author's introduction.** Read in the al-Maktaba al-Shāmila digital text of al-Majdhūb's edition (https://shamela.ws/book/13304/3, "[مقدمة المؤلف]"). Abū Ḥayyān calls the book "هذا المختصر" (this concise work). He limits it to the *gharīb* class of Qur'anic vocabulary, arranges it "على حروف المعجم" (by the letters of the alphabet) by root letters, and restricts it to "شرح الكلمة الواقعة في القرآن العزيز" (explaining the word as it occurs in the Qur'an). A concise, alphabetical list that explains difficult words in a single text fits "glossary". The web page shows no printed page number. The guide cites this passage as p. 40, which I could not check again this round, but the change under review does not affect that citation.
- **The displayed entries.** I sampled the stored entry for ظنن (Znn) with `_dict_guide_tool.py entry Znn …`. It gives the Qur'anic form and a one-word equivalent (`{بظنين}: بمتهم. {يظنون}: يوقنون.`), which is glossary form.

The new wording also matches the page's `kind` field ("Glossary of Qurʾānic gharīb") and the `summary` ("A concise glossary…"). The rest of the lede is unchanged. The change creates no new inconsistency with the body.

## New claims

None were introduced, and I found none.

## Validator

`node scripts/validate-dictionary-guides.mjs tuhfat-al-arib` passes: 12 root links, 5 excerpts, 1,077 words (lede + body). There is one warning: `[[root:kyn|none|…]]` in onOurSite. It is acceptable because the sentence says "the *Tuḥfa* has no entry there".

## Edits made by the verifier

None.
