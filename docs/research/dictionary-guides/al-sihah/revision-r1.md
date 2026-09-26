# al-Ṣiḥāḥ — revision after verification round 1 (2026-09-26)

File revised: `roots/frontend/src/content/dictionary-guides/guides/al-sihah.ts`.
Every source quoted below was re-opened in this session (Shamela pages fetched as raw HTML, page headers read; Haywood from the archive.org full text; al-Mawsūʿa from arab-ency.com.sy). Fuller quotations are in `research-notes.md` §8.

Validator after revision: `node scripts/validate-dictionary-guides.mjs al-sihah`: **ok**, no errors, no warnings. 12 root links, 7 excerpts, **1,099 words** (lede + body; unchanged from 1,099). onOurSite is about 140 words (it was about 190).

## Flagged claims

| # | Was | Now | Evidence |
|---|---|---|---|
| C8 | "it makes two promises" (cited to the preface only) | "Among its claims, two define the book: …" cited to the preface **and** `[^haywood\|p. 71]`. It no longer implies the preface makes only two claims. | Preface (Shamela 23235/50, vol. 1 p. 33) also has "وتهذيب لم أغلب عليه". Haywood p. 71: "Al-Jauhari's modest preface makes two claims: to have included only correct words, and to have initiated a new arrangement." |
| C9 | "(hence its short title, *al-Ṣiḥāḥ*, 'the sound [words]')" in the lede, cited to the preface | Deleted from the lede. The naming explanation stays in the body, attributed to al-Suyūṭī with `[^muzhir\|vol. 1, pp. 74–75]`. | Muzhir 1:74: "وأولُ مِن التزمَ الصحيح مقتصرا عليه … الجَوْهَري ولهذا سمَّى كتابه بالصحاح". |
| C29 | "the editor ʿAṭṭār, while granting the uncle some groundwork, rejects Ḥamad al-Jāsir's argument that al-Bandanījī's older rhyme book had anticipated it" | "the editor ʿAṭṭār, granting that the uncle laid 'part of the foundation' and that al-Bandanījī's rhyme book came first, still calls al-Jawharī the originator and rejects Ḥamad al-Jāsir's case for al-Bandanījī." The attar-essay source now says "(Shāmila pages 12–22)". | Shamela 23235/21: "ونحن لا نشك في أن الفارابي يعد واضع بعض أساس منهج الصحاح" (ʿAṭṭār quoting and re-affirming his own *Muqaddima*, pp. 80–81). /20: "وإن كان مسبوقا في الزمن والتأليف من قبل البندنيجي أو الفارابي"; "أما دعواه في نفي الابتكار عن الجوهري أن البندنيجي سبقه فمردودة". /22: "فالامام الجوهري مبتكر منهجه ابتكارا … وإن ظهر … أن «كتاب التقفية» تقدم معجم الصحاح بزمن غير يسير". See **Disputed** for the original wording. |
| C33 | "Authorities are named where they speak …; unattributed sentences are in al-Jawharī's voice, though they may draw silently on older books.[^haywood\|p. 74]" | "And a named authority ('Ibn al-Sikkīt said…') marks a report; unattributed sentences are presented as al-Jawharī's own." This is the guide's own reading advice and carries no citation. A separate sentence follows: "Haywood notes, though, that his definitions often coincide with those of [[guide:kitab-al-ayn\|Kitāb al-ʿAyn]].[^haywood\|p. 74]" The lead-in "Two conventions help" is now "Two things help", because the second item is advice, not a convention. | Haywood p. 74: "succinct definitions, (often coinciding with those of the 'Ain')". |
| C35 | "'Denial' is supported by two Qur'anic phrases (Q 28:48 and Q 17:99) and a note from al-Akhfash" | "'Denial' is illustrated by two Qur'anic phrases (Q 28:48 and Q 17:99)". Al-Akhfash is dropped. | Entry 155: "وقوله تعالى: (إنَّا بكُلٍّ كافِرون) *، أي جاحدون. وقوله عزوجل: (فأبى الظالمون إلا كُفوراً) *. قال الأخفش: هو جمع الكفر، مثل برد وبرود." The verses were checked in the `verses` table (28:48 ends "إنا بكل كافرون"; 17:99 ends "فأبى الظالمون إلا كفورا"). |
| C43 | "*takfīr* of sins set against *iḥbāṭ*" | "*takfīr* of sins likened to *iḥbāṭ*" | Entry 155: "والتكفير في المعاصي، كالإحباط في الثواب". |
| C65 | "nine include a passage from a similar-looking root" | Kept at **nine**, reworded as "nine repeat their heading over a similar-looking root's passage". See **Disputed**. | Scan of all 866 displayed entries (method in research-notes §8). |

## Brief issues

- **must-fix (unlabelled translations from Arabic sources): fixed.** The attribution line of the first quotation (the preface) now reads "(translation for this guide, like every translation from Arabic on this page)". This label comes at the first translation and covers the later inline renderings from al-Muzhir, Yāqūt, Ibn Barrī (via al-Muzhir), the Lisān introduction, Fīrūzābādī (via al-Muzhir), and ʿAṭṭār's "part of the foundation".
- **suggestion (death-date paragraph): adopted.** It is now one sentence: "He died in 393 (1002–3 CE) or around 400 (c. 1010).[^dhahabi|vol. 17, p. 82][^baalbaki-2019|p. 186, n. 1]". The 396 autograph moved into the story paragraph, where it does argumentative work (next item).
- **suggestion (C22): adopted.** Now: "A story Yāqūt quotes from al-Mujāshiʿī says al-Jawharī died when al-Bīshakī, for whom he wrote the book, had heard it only as far as the chapter of *ḍād*; a pupil fair-copied the rest of the draft and 'made gross errors in several places'. Haywood suggests 'a pinch of salt'. Yāqūt himself saw a copy in al-Jawharī's hand dated 396 (1005–6 CE), which, a modern reference notes, contradicts the story and puts his death after that year.[^mawsua]"
- **suggestion (onOurSite length): adopted.** About 190 words cut to about 140. The two defect counts now sit in one sentence ("Some entries carry another root's text: seventeen … and nine …"). The footnote and asterisk points are merged into one clause.
- **suggestion (word count): met (no net increase).** 1,099 → 1,099. The label and the C22 changes added words. To offset them, I cut "(hence its short title …)" and al-Akhfash, condensed the death dates, and replaced the closing "Read the Ṣiḥāḥ as a compact, sourced account of what one scholar around the year 1000 accepted as good Arabic. That date belongs …" with "The Ṣiḥāḥ's date, around 1000, belongs to the compilation, not to the usages it records." The lede already says "one careful scholar's selection".
- Lede, second sentence: "Both shape what you meet on our site: …" is now "What you meet on our site are compact entries that name their authorities, show a grammarian's interest in how words are built, and leave much out." The old wording implied the new arrangement is visible on our site, and the body says it is not.

## Removed claims

1. The preface "makes two promises" (C8). Replaced as above.
2. Lede: the short title's meaning presented as coming from the preface ("hence its short title …") (C9).
3. Al-Akhfash's note as support for the sense "denial" (C35).
4. "set against" for takfīr/iḥbāṭ (C43).
5. The reading convention presented under a Haywood citation, and "unattributed sentences are in al-Jawharī's voice, though they may draw silently on older books" (C33).
6. "while granting the uncle some groundwork" (C29). Replaced by a direct quotation from ʿAṭṭār.
7. The explicit attributions "al-Qifṭī gave 393 … noting a report of 'around 400'" and "a recent study gives 'ca. 400/1010'". Condensed to "He died in 393 … or around 400 …" with the same two citations.
8. "read the book with a student" (C22 wording).
9. The closing sentence "Read the Ṣiḥāḥ as a compact, sourced account of what one scholar around the year 1000 accepted as good Arabic." Cut for length. It is no factual loss.

## New claims

1. **ʿAṭṭār grants that al-Fārābī laid "part of the foundation" of the method.** Source: ʿAṭṭār essay, Shamela 23235/21: "ونحن لا نشك في أن الفارابي يعد واضع بعض أساس منهج الصحاح، وفوق هذا أربى الجوهري على خاله". The quoted words are a translation for this guide.
2. **ʿAṭṭār concedes that al-Bandanījī's rhyme book came first, yet calls al-Jawharī the originator.** Source: Shamela 23235/20 ("وإن كان مسبوقا في الزمن والتأليف من قبل البندنيجي أو الفارابي") and /22 ("فالامام الجوهري مبتكر منهجه ابتكارا … وإن ظهر … أن «كتاب التقفية» تقدم معجم الصحاح بزمن غير يسير").
3. **The death story comes from al-Mujāshiʿī. The book was written for al-Bīshakī, who heard it only up to bāb al-ḍād.** Source: Yāqūt 2:658 (Shamela 9788/658): "وذكره أبو الحسن علي بن فضال المجاشعي … كان الجوهري قد صنف «كتاب الصحاح» للأستاذ أبي منصور عبد الرحيم بن محمد البيشكي، وسمعه منه إلى باب الضاد المعجمة".
4. **Yāqūt himself saw the 396 autograph.** This was already in the guide, now reworded. Source: Yāqūt 2:658–659: "ثم وقفت على نسخة بالصحاح بخطّ الجوهري بدمشق … وقد كتبها في سنة ست وتسعين وثلاثمائة".
5. **A modern reference notes that the 396 autograph contradicts the story and implies a death after 396.** Source: al-Mawsūʿa al-ʿArabiyya vol. 7 p. 822 (arab-ency.com.sy/details/5188): "وهذا الخبر يناقض ما ذكر من أن الجوهري أتم كتابة الصحاح حتى حرف الضاد، كما يستدل منه على أن وفاة الجوهري كانت بعد سنة 396هـ". The source was already listed as `mawsua`.
6. **Haywood counts the preface's two claims.** New citation `[^haywood|p. 71]`: "Al-Jauhari's modest preface makes two claims: to have included only correct words, and to have initiated a new arrangement."
7. **His definitions often coincide with those of Kitāb al-ʿAyn, per Haywood.** Now stated explicitly; before, it was implicit under the citation. Source: Haywood p. 74, quoted above. It links to the existing guide `kitab-al-ayn` (registry.ts slug confirmed).
8. **All translations from Arabic on the page were made for this guide.** This is an editorial statement and true: every rendering was made by the guide's authors.
9. **onOurSite: "match … word for word, stray asterisks from the digital text included, without the editor's footnotes".** This rewords existing verified claims C62 and C63 and adds no new fact.

## Disputed

- **C65, "nine".** I kept nine. The verifier's own method (a repeated bracketed heading) finds nine when xsA is included. Scan: all 866 displayed entries, regex `\[([^\]\s\*]{2,6})\]` on `original_text_ar`. Entries with a repeated heading: nZr, xlf, jbl, rjf, lHq, brq, Hlq, Anf, **xsA**. The stored xsA text reads "[خسا] يقال: خَساً أو زَكاً … [خسا] حسوت المرق حسوا. ويوم كَحَسْوِ الطير … [خسأ] خسأت الكلب". The second "[خسا]" block is the entry for حسا (ḥ-s-w, "sipping"), and the site's own faithful translation says so: "the second block's content is in fact the entry for حسا / ḥ-s-w, evidently mis-keyed". خسا and حسا differ by one dot, so xsA is a similar-looking-root merge. It is also one of the 17 hamza merges, because it ends with [خسأ]. That overlap probably explains the verifier's count of 8. The sentence now names the mechanism ("repeat their heading over a similar-looking root's passage"), so the next verifier can re-run the count directly.
- **C29, partly.** The verifier read ʿAṭṭār's essay on Shamela pages 12–19 (and the "لكان في دعواه نظر" passage) and found no "groundwork" concession. The essay continues on Shamela ids 20–22, which the digital text numbers "ج1 - ص1–3". On /21 ʿAṭṭār writes "ونحن لا نشك في أن الفارابي يعد واضع بعض أساس منهج الصحاح", so the original gloss had a basis. I still adopted the verifier's fuller wording, which adds the concession on al-Bandanījī and "still calls al-Jawharī the originator". I replaced the paraphrase "some groundwork" with a direct quotation, "part of the foundation", so the claim can be checked against /21. The attar-essay source entry now gives the page range 12–22.
