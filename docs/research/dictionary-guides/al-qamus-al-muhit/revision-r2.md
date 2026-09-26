# al-Qāmūs al-Muḥīṭ — revision after verification round 2

Guide: `roots/frontend/src/content/dictionary-guides/guides/al-qamus-al-muhit.ts`
Input: `verification-r2.md` (62 claims: 59 S, 3 NQ, 0 U; no must-fix brief issues; five suggestions).
Validator after revision: `node scripts/validate-dictionary-guides.mjs al-qamus-al-muhit` → **ok**: 10 root links (10 distinct pairs), 5 excerpts, **1,098 words** (lede + body, excluding excerpts; was 1,100).

Everything quoted below was opened by me during this revision (2026-09-26), unless marked otherwise.

## What I could and could not open

- **Opened:** Britannica "Sufism", section "Sufi thought and practice" (browser pane); Risāla preface pp. 28 and 32 and article p. 727 (Shamela 7283/4, /8, /703; page titles «ص28», «ص32», «ص727»); Haywood, archive.org djvu text, pp. 71, 85, 87, 88, 89–90; Lane, Preface, laneslexicon.github.io transcription (the *Tāj* paragraph); displayed *Tāj* د ر س entry (`_dict_guide_tool.py entry drs murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus`).
- **Not openable:** Brill EI² "Abdāl" (SIM-0132): HTTP 403 from CloudFront in the browser pane and to curl, also via the DOI redirect (doi.org/10.1163/1573-3912_islam_SIM_0132 → referenceworks.brill.com → 403). Baalbaki p. 393: Google Books redirected WebFetch and curl to google.com/sorry (a CAPTCHA, which I did not bypass); the Books API returns 429 (daily quota 0). WebSearch budget for the session was exhausted, so no further snippet search was possible.

## Flagged claims

### C51, "puts back what was cut" → "fills in the names" (qualified)
- Old: "al-Zabīdī's commentary, Tāj al-ʿArūs, puts back what was cut: it names *dārasta* as the reading of Ibn Kathīr and Abū ʿAmr, credits the gloss to Ibn ʿAbbās, and on Idrīs gives both sides with names: …"
- New: "al-Zabīdī's commentary, Tāj al-ʿArūs, fills in the names: it identifies *dārasta* as the reading of Ibn Kathīr and Abū ʿAmr, credits the gloss to Ibn ʿAbbās, and on Idrīs sets out both sides: Ibn Khaṭīb al-Dahsha for the foreign origin, followed by a verdict that it is sounder, and Ibn al-Jawwānī for the derivation from study."
- Why: the verifier showed that Ibn Khaṭīb al-Dahsha died after al-Fīrūzābādī and that the names are not in the displayed *al-Muḥkam* entry either, so nothing shows they were "cut". "Fills in the names" claims only that the *Tāj* supplies names the *Qāmūs* does not give, which the two displayed entries show. "with names" was dropped because the new verb already says it.
- Evidence (displayed *Tāj* drs entry, re-read): «ومنه قوله تعالى: وليقولوا دارست في قراءة ابن كثير وأبي عمرو، وفسره ابن عباس رضي الله عنهما بقوله: قرأت على اليهود، وقرؤوا عليك» and «وقال ابن خطيب الدهشة: وهو اسم أعجمي، لا ينصرف، للعلمية والعجمة. وقيل: إنما سمي به لكثرة درسه، ليكون عربيا. والأول أصح. وقال ابن الجواني: سمي إدريس لدرسه الثلاثين صحيفة التي أنزلت عليه.»

### C21, Baalbaki on the additions (qualified; option (b) of the report)
- Old: "The *Qāmūs*'s additions to those two sources, Ramzi Baalbaki notes, are mostly names of the Prophet's Companions, ḥadīth scholars, poets, places and plants, and "hardly substantiate" the preface's claim to distil two thousand works.[^baalbaki|p. 393][^qamus-risala|p. 32]"
- New: "Ramzi Baalbaki judges that the *Qāmūs*'s additions hardly bear out the preface's claim to distil two thousand works; most, he notes, are names of the Prophet's Companions, ḥadīth scholars, poets and places, or plants.[^baalbaki|p. 393][^qamus-risala|p. 32]"
- What changed: (1) "to those two sources" is gone; the sentence no longer says what the additions are additions *to*. (2) The quotation marks around "hardly substantiate" are gone; the judgment is paraphrased and attributed to Baalbaki ("judges", "he notes"). (3) The order now follows the snippet: judgment first, then "most of these additions are…".
- Evidence: I could not open p. 393 (see above). The wording rests on the p. 393 snippet recorded by verifier r1, who saw it directly: "…hardly substantiate its author's claim that it contains the digest of two thousand works (ṣarḥ alfay muṣannaf). Most of these additions are names of Companions of the Prophet, scholars of Ḥadīth, poets, place names and plants…". The claim being judged I did open: Risāla p. 32 (Shamela 7283/8, «ص32»): «وكتابي هذا - بحمد الله تعالى - صريح ألفي مصنف من الكتب الفاخرة».
- Not added: the verifier's suggested co-citation of Haywood p. 88. That page reports that critics blamed the author "for filling his work with geographical and other proper names" (re-read), which corroborates the gist. But the sentence is now attributed to Baalbaki, and a Haywood citation would appear to support Baalbaki's own judgment and his list, including plants, which Haywood does not mention.

### C55, *al-abdāl* citation (source replaced)
- `[^ei2-abdal]` → `[^britannica-sufism]`; the `ei2-abdal` source entry was removed and replaced by `britannica-sufism`. The wording "a rank in the Sufi hierarchy of saints" is unchanged.
- Evidence: Britannica, "Sufism", section "Sufi thought and practice", byline "Annemarie Schimmel, Britannica Editors", dated Sep. 21, 2026 (contributor link https://www.britannica.com/contributor/Annemarie-Schimmel/2619): "The invisible hierarchy of saints consists of the 40 abdāl ("substitutes"; for when any of them dies another is elected by God from the rank and file of the saints), seven awtād …, three nuqabāʾ …, headed by the quṭb …".
- EI² was dropped because I could not confirm its text (HTTP 403, see above), as the report asked.
- Note, not used on the page: Britannica gives the abdāl as 40; the displayed *Qāmūs* ب د ل entry says seventy (forty in al-Shām, thirty elsewhere). The page quotes the *Qāmūs*'s figure as the *Qāmūs*'s and does not give a number of its own, so there is no conflict to resolve.

## Brief suggestions

1. **Length** (all fixes word-neutral): 1,100 → 1,098.
2. **Baalbaki source line.** Now: "…(Leiden: Brill, 2014), p. 393, seen only as a Google Books search snippet (no page view)." The Baalbaki-only locators that were already co-cited were removed:
   - Arrangement: `[^baalbaki|p. 394][^haywood|p. 88]` → `[^haywood|pp. 71, 88]` (Risāla p. 1242 kept). Haywood p. 71 (re-read; after the running head "THE RHYME ARRANGEMENT 71"): "Al-Jauhari arranged his roots according to their final radicals in the first instance. … Within each chapter, roots are entered according to the first, and then the intermediate radicals." p. 88: "we are bound to believe that he preferred the rhyme order."
   - *qāmūs* = "dictionary": `[^baalbaki|p. 392]` removed; Haywood pp. 83, 85 kept (p. 83: "The word "Qamus", thanks to the wide currency of the dictionary … came to mean a dictionary"; p. 85: "Not only has the word "Qamus" come to mean dictionary").
   - Closing *Tāj* sentence: `[^baalbaki|p. 398]` removed.
3. **Closing sentence.** "quotes the *Qāmūs* and restores the authorities, quotations and missing words.[^baalbaki|p. 398][^lane-preface|p. xviii][^haywood|p. 89]" → "quotes the *Qāmūs* and adds explanations, authorities, quotations and further words.[^lane-preface|p. xviii][^haywood|pp. 89–90]". Evidence: Haywood pp. 89–90: "The method of the author of the "Taj" was to put the contents of the "Qamus" in brackets, interpolating commentary material. The latter consists of amplification of definitions, the mention of authorities or "ruwah", illustrative quotations …, the inclusion of additional words under roots already to be found in the "Qamus", and also entirely new roots." Lane p. xviii: "…in the form of an interwoven commentary on the Ḳámoos; exhibiting fully and clearly, from the original sources, innumerable explanations which are so abridged in the latter work as to be unintelligible …; and a very large collection of additional words and significations". "explanations" was added (it replaces the word "the"), because both sources name it first and it matches "When a line is too compressed to follow".
4. **Vowelling sentence.** `[^qamus-risala|p. 28]` added before `[^haywood|p. 87]`. Risāla p. 28 (Shamela 7283/4, «ص28»): «وكل كلمة عريتها عن الضبط؛ فإنها بالفتح، إلا ما اشتهر بخلافه اشتهارا رافعا للنزاع من البين، وما سوى ذلك، فأقيده بصريح الكلام، غير مقتنع بتوشيح القلام». The exception ("except what is so well known otherwise…") is why the page already says "normally".
5. **Cross-reference locator.** `pp. 727–728` → `p. 727`. Risāla p. 727 (Shamela 7283/703, «ص727») has the proverb's whole explanation, from «وأما "سرعان ذا إهالة" فأصله: أن رجلا كانت له نعجة عجفاء» to «يضرب لمن يخبر بكينونة الشيء قبل وقته».

## Changed
- body ¶3: the Baalbaki sentence (C21)
- body, arrangement sentence: the citations (Baalbaki p. 394 → Haywood pp. 71, 88)
- body, vowelling sentence: added the Risāla p. 28 citation
- body, cross-reference sentence: the locator is now p. 727
- body, *darasa* ¶: "puts back what was cut … gives both sides with names" → "fills in the names … sets out both sides" (C51)
- body, *al-abdāl* clause: the citation (C55)
- body, closing ¶: "restores the …" → "adds explanations, …"; Baalbaki pp. 398 and 392 removed; Haywood p. 89 → pp. 89–90
- sources: `baalbaki` citation text changed; `ei2-abdal` removed; `britannica-sufism` added

Unchanged: summary, lede, onOurSite, excerpts, period, and every other source entry.

## Removed claims
1. The *Tāj* "puts back what was cut" (C51).
2. That Baalbaki's additions are additions "to those two sources" (the referent); also the quotation marks around "hardly substantiate" (C21).
3. That the *Tāj* "restores" authorities, quotations and missing words: it is now "adds" (suggestion 3).
4. The citation `ei2-abdal` (EI² "Abdāl"), and the Baalbaki locators pp. 392, 394 and 398; the source line's statement that pp. 392–93 and 398 were read in a page preview.

## New claims (with evidence)
1. *al-abdāl* is a rank in the Sufi hierarchy of saints: the claim is not new, the source is. Britannica "Sufism" (Schimmel / Britannica Editors), quoted above.
2. The *Tāj* adds *explanations* (as well as authorities, quotations and further words): Lane p. xviii ("innumerable explanations which are so abridged in the latter work as to be unintelligible"); Haywood p. 89 ("amplification of definitions").
3. Co-citations for existing claims: Haywood p. 71 (rhyme arrangement of *al-Ṣiḥāḥ*); Haywood p. 90 (continuation of the *Tāj* description); Risāla p. 28 (vowelling rule). All quoted above.

## Disputed
None.

## Left as is (for the next verifier)
- `ei2-fleisch` (EI² "al-Fīrūzābādī", SIM-2383) is also behind CloudFront 403 for automated tools. It was read in round 1 and was not flagged. Its only use (birth in Fārs, study in Iraq) is co-cited to al-Sakhāwī vol. 10, pp. 79–80, which verifier r2 confirmed. I did not remove it.
- `baalbaki` p. 393 now carries a single sentence, attributed to Baalbaki. If the next verifier also cannot see the snippet, the fallback is to delete the sentence. The preface's two-thousand-works claim (Risāla p. 32) could then stand without the judgment, or be dropped too; the paragraph reads complete without either.
