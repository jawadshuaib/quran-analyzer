# al-Qāmūs al-Muḥīṭ — revision after verification round 1

Guide: `roots/frontend/src/content/dictionary-guides/guides/al-qamus-al-muhit.ts`
Input: `verification-r1.md` (62 claims: 56 S, 6 NQ, 0 U; no must-fix brief issues).
Validator after revision: `node scripts/validate-dictionary-guides.mjs al-qamus-al-muhit` → **ok**, 10 root links, 5 excerpts, **1,100 words** (lede + body, excluding excerpts). Summary: 44 words.

Every source quoted below was opened by me during this revision (2026-09-26), except where marked.

## Flagged claims — what was done

### C4 (period / death date) — qualified
- Body now: "…at Zabīd, where he died in 817/1415,[^sakhawi|vol. 10, pp. 81, 86] though some sources give 816.[^lane-preface|p. xvi]"
- `period` kept as "729–817 AH / 1329–1415 CE" (the verifier said no "c." needed).
- Evidence: Lane, Preface p. xvi (laneslexicon.github.io transcription, text between page markers xvi and xvii): "The "Ḳámoos" of El-Feyroozábádee, … who was born in the year of the Flight 729, and died in 816." al-Sakhāwī p. 86 (817) as recorded by the verifier; p. 81 for the Zabīd judgeship.
- Birth: I did not add Haywood's 726/1326 (Haywood p. 83: "(726/1326-817/1414)"). al-Sakhāwī p. 79, the EI² abstract (re-opened: "Rabīʿ II or Djumādā II 729/February or April 1329") and Lane p. xvi all give 729. Noted here, not on the page.

### C7 (summary) — rewritten
- Now: "al-Fīrūzābādī's fourteenth-century digest of *al-Muḥkam* and *al-ʿUbāb*, written with al-Jawharī's *al-Ṣiḥāḥ* in view to mark what it lacked and where he judged it wrong. Terse lists of forms and senses, with abbreviations and few quotations; useful for surveying a root's recorded senses and vowellings." (44 words)
- Evidence: Risāla preface p. 27 (Shamela 7283/3, print p. 27): «ولخصت كل ثلاثين سفرا في سفر، وضمنته خلاصة ما في "العباب"، و"المحكم"» — then, as a second aim, «ولما رأيت إقبال الناس على "صحاح" الجوهري … غير أنه فاته نصف اللغة أو أكثر»; p. 28 (7283/4): «ثم إني نبهت فيه على أشياء ركب فيها الجوهري رحمه الله خلاف الصواب».

### C22 (Baalbaki on the additions) — qualified
- Now: "The *Qāmūs*'s additions to those two sources, Ramzi Baalbaki notes, are mostly names of the Prophet's Companions, ḥadīth scholars, poets, places and plants, and "hardly substantiate" the preface's claim to distil two thousand works.[^baalbaki|p. 393][^qamus-risala|p. 32]"
- "modest" and "medical terms" **removed**. I tried to read Baalbaki p. 393 myself: Google Books page view returned no page text (WebFetch), the search-inside endpoints returned a CAPTCHA (not bypassed), and the Books API was over quota. So the wording follows only what the verifier saw in the p. 393 snippet ("…hardly substantiate its author's claim that it contains the digest of two thousand works (ṣarḥ alfay muṣannaf). Most of these additions are names of Companions of the Prophet, scholars of Ḥadīth, poets, place names and plants…"). **I did not open this page myself.**
- The claim itself, now cited to the preface, p. 32 (Shamela 7283/8, print p. 32): «وكتابي هذا - بحمد الله تعالى - صريح ألفي مصنف من الكتب الفاخرة» ("this book of mine is the pure essence of two thousand fine works").

### C34 (al-Zabīdī's twenty thousand) — replaced, new source
- Now: "…while the *Qāmūs*'s eighteenth-century commentator al-Zabīdī credited it with sixty thousand entries, twenty thousand more than *al-Ṣiḥāḥ*.[^taj-intro|vol. 1, p. 73][^haywood|p. 89]"
- Evidence: *Tāj al-ʿArūs*, Kuwait edition, vol. 1, p. 73 (https://shamela.ws/book/7030/73; card: «تحقيق: جماعة من المختصين … وزارة الإرشاد والأنباء في الكويت - المجلس الوطني للثقافة والفنون والآداب … (١٩٦٥ - ٢٠٠١ م) … [ترقيم الكتاب موافق للمطبوع]»). The passage is in al-Zabīdī's own voice (after «قلت:», following a quotation from «شيخنا»): «قلت: أي فإنه جمع فيه ستين ألف مادة، زاد على الجوهري بعشرين ألف مادة». This compares totals, as the verifier said; the page no longer calls it a count of items missing from *al-Ṣiḥāḥ*.
- "eighteenth-century commentator": Haywood p. 89: "A large-scale commentary on the "Qamus" … was compiled in Egypt in the Eighteenth Century. … It is the "Taj al-ʿArus" of Murtada al-Zabidi". (Haywood p. 90 independently reports "60,000 in the "Qamus", and 40,000 in the "Sahah"" from "amateur statisticians"; not cited.)
- The Baalbaki p. 393 citation was removed from this sentence (not verifiable).

### C41 (the dash) — replaced
- Now: "In print, a dash (ـ) repeats the word just defined, verb or noun: in the *ahl* entry, وـ للبيت is "the *ahl* of a house".[^qamus-risala|p. 963]"
- Evidence: Risāla print p. 963 (Shamela 7283/939): «وأهل الأمر: ولاته،وـ للبيت: سكانه،وـ للمذهب: من يدين به» (dash repeats the noun *ahl*); print p. 964 (7283/940): «واستأهله: استوجبه، لغة جيدة، وإنكار الجوهري باطل،وـ فلان: أخذ الإهالة» (dash repeats the verb). The displayed Ahl entry (id 1117) has the same «وأَهْلُ الأمرِ: وُلاتُه، وـ للبيتِ: سُكَّانُه». The preface does not describe the dash, hence "In print".

### C52 (the Tāj on Idrīs) — replaced
- Now: "al-Zabīdī's commentary, Tāj al-ʿArūs, puts back what was cut: it names *dārasta* as the reading of Ibn Kathīr and Abū ʿAmr, credits the gloss to Ibn ʿAbbās, and on Idrīs gives both sides with names: Ibn Khaṭīb al-Dahsha for the foreign origin, followed by a verdict that it is sounder, and Ibn al-Jawwānī for the derivation from study."
- The verdict is no longer attributed to al-Zabīdī or to anyone. Evidence, displayed Tāj drs entry (`_dict_guide_tool.py entry drs murtada-al-zabidi-taj-al-arus-fi-jawahir-al-qamus`): «وقال ابن خطيب الدهشة: وهو اسم أعجمي، لا ينصرف، للعلمية والعجمة. وقيل: إنما سمي به لكثرة درسه، ليكون عربيا. والأول أصح. وقال ابن الجواني: سمي إدريس لدرسه الثلاثين صحيفة التي أنزلت عليه.»

## Brief suggestions

- **Length**: additions offset by cuts; final 1,100 words. Cuts: "lived for long stretches in Mecca" (Mecca remains via the al-Kirmānī sentence); "who last met him in Mecca" → "by 790/1388 the author had handed a copy to the historian al-Maqrīzī" (al-Sakhāwī pp. 85–86 «آخر ما اجتمع به في مكة سنة تسعين … وناولني قاموسه»: the last meeting was in 790, so any handing-over was by then); the five-volume note shortened to "That larger work was never finished" (citations kept: Lane pp. xvii–xviii "The non-completion of the Lámi' is therefore certain"; al-Sakhāwī p. 82); the standalone "Its two main sources are…" merged into the Baalbaki sentence ("those two sources"); the *al-Ṣiḥāḥ* comparison under أ ل ه tightened; "The Qur'anic quotation needs more care." dropped.
- **Co-citations added** (all opened): Haywood pp. 83, 85 for *qāmūs* = "dictionary" (p. 83: "The word "Qamus", thanks to the wide currency of the dictionary … came to mean a dictionary"; p. 85: "Not only has the word "Qamus" come to mean dictionary"); Haywood p. 88 for the rhyme arrangement ("the choice of the rhyme order was deliberate and considered"); Haywood p. 89 for the *Tāj* restoring material ("put the contents of the "Qamus" in brackets, interpolating commentary material … the mention of authorities or "ruwah", illustrative quotations …, the inclusion of additional words"). Baalbaki pp. 392, 394, 398 kept (drafter's recorded quotations), now each backed by a source the verifier and I could read.
- **bi-hāʾ** now cited [^qamus-risala|p. 28]: «أني إذا ذكرت صيغة المذكر، أتبعتها المؤنث بقولي: وهي بهاء، (ولا أعيد الصيغة)».
- **muḥarraka** glossed "the second consonant also takes *a*, as in *ḥasan*": Haywood p. 87 "Where the second consonant also had fathha, as in "hasan", the explicatory formula was "muharrak" (vowelled)".
- **al-abdāl**: added "a rank in the Sufi hierarchy of saints" with a new source, EI² "Abdāl" (I. Goldziher and H. J. Kissling), https://referenceworks.brill.com/display/entries/EIEO/SIM-0132.xml, freely visible text: "(A.; plur. of badal, "substitute"), one of the degrees in the ṣūfī hierarchical order of saints, who, unknown by the masses …, participate by means of their powerful influence in the preservation of the order of the universe. … The abdāl … have their residence in Syria." I did NOT call it "later" or date it: the visible text gives no date and cites Ibn Ḥanbal's *Musnad* for the number forty. Encyclopaedia Iranica "ABDĀL" was behind a Cloudflare challenge (not bypassed).
- **Threshing sentence**: "…follow, among others."

## Changed (summary)
summary; body ¶1 (dates, death variant, al-Maqrīzī); body ¶3 (Lāmiʿ, Baalbaki, p. 32); Compression sentence (wording); أ ل ه comparison (tightened); Lane sentence (tightened); al-Shidyāq/al-Zabīdī sentence (C34); arrangement citations; bi-hāʾ citation; muḥarraka gloss; dash sentence (C41); cross-reference sentence (tightened); threshing sentence; *darasa* ¶ (dropped one transition; Tāj sentence C52); *al-abdāl* clause; closing paragraph citations; sources: added `taj-intro`, `ei2-abdal`. `period`, `lede`, `onOurSite`, excerpts unchanged.

## Removed claims
1. Summary: "Written to add to and correct al-Jawharī's *al-Ṣiḥāḥ*" as the book's purpose (C7).
2. Baalbaki: additions "modest"; "medical terms" (C22).
3. "al-Zabīdī counted twenty thousand items in the *Qāmūs* that *al-Ṣiḥāḥ* lacks" [^baalbaki|p. 393] (C34).
4. "A dash stands for the verb just given." (C41)
5. *Tāj* "judging the *Qāmūs*'s view sounder" (C52).
6. Trimmed for length (were supported): "lived for long stretches in Mecca" (C13); "who last met him in Mecca"; "al-Sakhāwī saw a note in the author's hand saying five volumes were done" (the citation stays); "Its two main sources are *al-Muḥkam* and *al-ʿUbāb*" as its own sentence; "The Qur'anic quotation needs more care."; summary's "dropping most … sources" and "variants".

## New claims (with evidence)
1. Death "though some sources give 816" — Lane, Preface p. xvi (quoted above).
2. al-Zabīdī credited the *Qāmūs* with 60,000 entries, 20,000 more than *al-Ṣiḥāḥ* — *Tāj* intro, vol. 1, p. 73 (quoted above).
3. al-Zabīdī as the *Qāmūs*'s eighteenth-century commentator — Haywood p. 89.
4. The *Qāmūs*'s additions are "mostly names of the Prophet's Companions, ḥadīth scholars, poets, places and plants" — Baalbaki p. 393, **as read by verifier r1 in a snippet; I could not open it (CAPTCHA)**. The two-thousand claim — Risāla p. 32 (opened).
5. *muḥarraka* = second consonant also *a*, as in *ḥasan* — Haywood p. 87.
6. The printed dash repeats the word just defined, verb or noun — Risāla pp. 963–964; displayed Ahl entry.
7. *Tāj* on Idrīs: Ibn Khaṭīb al-Dahsha (foreign origin), then "the first is sounder" (unattributed), and Ibn al-Jawwānī (derivation from study) — displayed Tāj drs entry.
8. *al-abdāl* is a rank in the Sufi hierarchy of saints — EI² "Abdāl" (Goldziher–Kissling), free text.
9. *qāmūs* = "dictionary" also per Haywood pp. 83, 85; rhyme order per Haywood p. 88; *Tāj* restoring authorities, quotations, words per Haywood p. 89 (co-citations for existing claims).

## Disputed
None. (Note for the next verifier: the drafting notes record "modest" and "in addition to medical terms" at Baalbaki p. 393 in a full-page preview; neither the verifier nor I could see that text, so the page no longer uses them.)
