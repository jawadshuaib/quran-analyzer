# al-Ṣiḥāḥ: cross-guide consistency fixes (2026-09-26)

Input: two issues raised by the consistency critic across all guides. Both were applied.

## Changes

| Field | Before | After | Why |
|---|---|---|---|
| `body` (After al-Jawharī) | Fīrūzābādī "said it lacked \"two-thirds of the language or more\" and that he singled it out…"[^muzhir 1:77–78] | "…said it lacked \"two-thirds of the language or more\" (so al-Suyūṭī quotes his preface; the printed *Qāmūs* reads \"half\"[^qamus-preface\|p. 27]) and that he singled it out…"[^muzhir 1:77–78] | [contradiction] The al-qamus-al-muhit guide quotes the same preface from the printed Risāla edition as "half the language or more". Both quotations are accurate. The variant is in the sources, so the page now names it. |
| `lede` (last sentence) | "Read it as one careful scholar's selection, not a record of everything the Arabs said." | "The title promises soundness, as one scholar judged it, not completeness." | [sameness] About eleven ledes end on the "Read it as…" / "Reading it well means…" formula. The new sentence rests on claims the page already supports: the preface's "what was sound in my judgement" (*mā ṣaḥḥa ʿindī*, vol. 1, p. 33) and al-Suyūṭī's remark that this is why the book is called al-Ṣiḥāḥ (Muzhir 1:74–75). "Not completeness" is the guide's own reading. The page makes no claim that the preface promised completeness. |
| `sources` | none | new entry `qamus-preface` (primary): al-Fīrūzābādī, author's preface to *al-Qāmūs al-Muḥīṭ*, Risāla 8th ed. (Beirut, 2005), p. 27, Shāmila 7283/3 | Supports the "half" reading. The renderer numbers sources by citation order, so the new entry sits after `lisan-intro` in the array. |

## New claims

1. **al-Suyūṭī's text of the Qāmūs preface reads "two-thirds" (ثلثا).** Opened https://shamela.ws/book/6936/71 and https://shamela.ws/book/6936/72 (al-Muzhir, ed. Fuʾād ʿAlī Manṣūr, page-matched). Shāmila's print-page field reads 77 and 78. Page 77 ends «ولما رأيت إقْبالَ الناس على صحاح الجوهري وهو جدير بذلك غيرَ أنه فاته», and page 78 begins «ثلثا اللغة أو أكثر إما بإهمال المادة أو بترك المعاني الغريبة النَّادّة». This confirms the existing citation `[^muzhir|vol. 1, pp. 77–78]`. The new part of the claim is only its attribution: "so al-Suyūṭī quotes his preface".
2. **The printed *Qāmūs* reads "half" (نصف).** Opened https://shamela.ws/book/7283/3. Shāmila's print-page field reads 27. The book card at https://shamela.ws/book/7283 gives: ed. Maktab Taḥqīq al-Turāth fī Muʾassasat al-Risāla, under the supervision of Muḥammad Naʿīm al-ʿArqsūsī; Muʾassasat al-Risāla, Beirut; 8th ed., 1426/2005; "[ترقيم الكتاب موافق للمطبوع]" (the pagination matches the printed book). The page reads «ولما رأيت إقبال الناس على "صحاح" الجوهري، وهو جدير بذلك، غير أنه فاته نِصْفُ اللغة أو أكثر، إما بإهمال المادة، أو بترك المعاني الغريبة النادة». This supports `[^qamus-preface|p. 27]`.
3. **The lede sentence** "The title promises soundness, as one scholar judged it, not completeness." This is interpretation. It rests on facts already verified on the page (the preface's «ما صح عندي», vol. 1, p. 33; al-Suyūṭī, Muzhir 1:74–75, «ولهذا سمى كتابه بالصحاح»). No new source is needed. "As one scholar judged it" paraphrases *ʿindī*, "in my judgement".

## Not done

- I did not say which reading is original. I opened no manuscript evidence, and neither source comments on the variant.
- I did not add Haywood's paraphrase ("scarcely contains half the language", p. 75, per research-notes.md). It is not needed, and it would add words.

## Validator

`node scripts/validate-dictionary-guides.mjs al-sihah` returns **ok**: 12 root links (9 distinct pairs), 7 excerpts, 1,107 words (lede + body); 1/1 guides pass. The count was 1,101 before these fixes: +10 words for the variant, −4 for the new lede sentence. That is still "roughly 1,100", so I did not trim verified text.
