# al-Mufradāt guide: revision after verification round 1

- File revised: `roots/frontend/src/content/dictionary-guides/guides/al-mufradat.ts`
- Report answered: `verification-r1.md` (73 claims: 65 S, 8 NQ, 0 U; 1 must-fix brief issue and 7 suggestions)
- Reviser: 2026-09-26. The extra checks made during this revision are logged in `research-notes.md` §10.
- Validator: `node scripts/validate-dictionary-guides.mjs al-mufradat` → **ok, 1/1 pass, no warnings**. Result: 5 root links, 3 excerpts, **1,122 words** (lede + body). Before the revision the count was 1,109. For the length, see "Brief issues" below.
- Rendering: checked at http://localhost:4000/classical-dictionaries/al-mufradat.

## Flagged claims

### C7: "typically" (summary and lede)

Applied the verifier's wording in both fields.

- **Summary:** "Many entries start from a word's basic sense and follow it through the verses; some explain how a sense was borrowed, extended or narrowed, or how a word differs from a near-synonym." (44 words)
- **Lede:** "Many entries open with a plain, often physical sense and then follow the word from verse to verse; in some he also explains how a sense was borrowed, extended or narrowed, or how the word differs from its near neighbours."

### C18: "the habit runs through the *Mufradāt*"

Now: "Dāwūdī could not find the sequel, but the habit surfaces in a few dozen of the *Mufradāt* entries we display, among them ح م د".

Support for "a few dozen": `_dict_guide_tool.py grep … '(أخص|أعم|أبلغ) من'` returns 61 displayed entries. The verifier found the same number.

### C20: Hmd translation

Now: "*Ḥamd* to God Most High: praising Him for [His] excellence. It is narrower than *madḥ* and broader than *shukr*."

### C31: kfr poetry

Now: "He starts 'in the language' with a physical act of covering, citing two half-lines by poets he does not name. The first time, he quotes one to correct some philologists who took *kāfir* in it as a name for night and sower; for him the word only describes them."

Support, from entry 157 (Dāwūdī p. 714): "ووصف الليل بِالْكَافِرِ لستره الأشخاص، والزّرّاع لستره البذر في الأرض، وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع: ألقت ذكاء يمينها في كافر".

"The first time" is deliberate. The same half-line comes back later in the entry as ordinary evidence: "ويقال الْكَافِرُ للسّحاب الذي يغطّي الشمس والليل، قال الشاعر: ألقت ذكاء يمينها في كافر". So it would be wrong to say he quotes it only to correct the philologists.

I paraphrased "some philologists" without quotation marks, so no translation label is needed there. The poets' names in Dāwūdī's notes are already mentioned in onOurSite.

### C44: sjd analysis

Now: "The entry also sets out, attributing it to no one, an analysis: *sujūd* is by choice or by subjection (*taskhīr*), and the prostration of shadows, by subjection, is 'a silent yet speaking indication' that such things are made by a wise Maker (translation for this guide)."

- "His own analysis" is removed.
- "bowing" is now "prostration".
- "sign" is now "indication", and the phrase is labelled.

Source text: "فهذا سجود تسخير، وهو الدّلالة الصامتة الناطقة المنبّهة على كونها مخلوقة، وأنّها خلق فاعل حكيم".

For consistency, the next sentence now says "read the scheme as **an** interpretation", not "**his** interpretation".

### C54: "His own voice is in the definitions, the reasoning, and first-person asides"

Now: "So an unattributed definition may be older than al-Rāghib, sometimes taken over word for word, and a view introduced by *qīla* … is reported, not necessarily endorsed. His own voice is surest in first-person asides like that reference to the *Dharīʿa*."

This departs from the verifier's suggested wording, and is narrower. The suggestion said his voice is "clearest in the reasoning … in the classifications". Two things argue against that:

- Under C44 the guide now says the *ḍarbān* classification in sjd is unattributed. Calling classifications his clearest voice would contradict that.
- Dāwūdī p. 21 says he sometimes copies *al-Mujmal* verbatim ("وربما ينقل عنه حرفيا"). I have no evidence that the "since … it came to be used" reasoning is his rather than borrowed.

Only the first-person asides, such as "وقد بيّنته في كتاب «الذّريعة إلى مكارم الشّريعة»" (entry 157), can only be his. "Sometimes taken over word for word" is Dāwūdī p. 21, cited in the same paragraph.

### C56: Tāj count

"some 280 entries" is now "some 340 entries". The sentence was shortened to "names him in some 340 entries".

My own count, over displayed Tāj entries with vowel marks stripped:

- 340 entries contain الراغب.
- 312 have an explicit "قال/وقال/قاله الراغب", "مفردات" or "الراغب:".
- I read the other 28 in context. 27 are the scholar; `wsl` is the ordinary word ("الواسل: (الراغب إلى الله تعالى)").
- So 339 entries cite him, which rounds to "some 340".

### C70: "Ibn Fāris's generation" (onOurSite)

Now: "The dictionary panel orders the works by a stored death date of 1109 CE (502 AH), which modern scholarship doubts; that is why it lists him after Ibn Sīda, although on the evidence above he was a contemporary of Ibn Fāris."

- "Contemporary" is Key's word (p. 90: "the dictionary of his contemporary Ibn Fāris").
- "Lists him after Ibn Sīda" is a site fact. `dicts` gives Ibn Sīda 1066 and al-Rāghib 1109, and FORMAT.md says the panel orders by the stored year.

I did not adopt the suggested "not after Ibn Sīda". Dāwūdī p. 37 reports that al-Dhahabī put al-Rāghib in the 42nd *ṭabaqa*: "وهذه الطبقة تبدأ وفياتها بسنة ٤٤٠ هـ وتنتهي في حدود سنة ٤٧٠ هـ". Ibn Sīda's d. 458 AH falls inside that range, so the sources do not exclude a death after Ibn Sīda.

## Brief issues

- **must-fix, Key URL.** Replaced the academia.edu link with https://www.ucpress.edu/books/language-between-god-and-the-poets/paper. The DOI stays in the citation text.
  - I could not open either URL the verifier suggested. https://doi.org/10.1525/luminos.54 redirects to luminosoa.org, which returns **403** both to curl and in the browser pane. https://library.oapen.org/handle/20.500.12657/29479 returns **403** to curl, and the browser pane refused to open it.
  - The UC Press page returns 200. Its title is "Language between God and the Poets by Alexander Key … University of California Press", and it shows "Open Access … Read Book · Download EPUB · PDF".
  - I re-verified pp. 11, 13, 90 and 107 against the OAPEN PDF mirrored on archive.org (research-notes §10).
- **suggestion, length.** I trimmed the Tāj/Lane sentence as suggested, along with other sentences: bio, Key, *munāsabāt*, sjd, evidence, Zarkashī. I kept "(translation for this guide)" labels that add words. The final count is 1,122 against 1,109 before. It is still about 2% over the 1,100 guide figure. The extra words are the corrections themselves: the kfr correction, the labels, the alternative title and the introduction framing. Cutting further would have meant removing an example point, so I stopped there. The validator's warning threshold (1,200) is not reached.
- **suggestion, biography placement.** Moved the biography paragraph to open the body, directly after the lede and before "## Bricks for a building". The Ṣafwān Dāwūdī and Alexander Key names are now introduced there.
- **suggestion, "recalling an earlier treatise".** Adopted in a more cautious form: "Recalling his earlier writings, al-Rāghib opens by putting the Qur'an's verbal sciences first…" [^raghib-intro|pp. 53–54]. Evidence (Shamela 23636/35–36):
  - p. 53: "كنت قد ذكرت في «الرسالة المنبهة على فوائد القرآن»".
  - p. 54: "وأشرت في كتاب «الذريعة إلى مكارم الشريعة»", then "ودلّلت في تلك الرسالة", with Dāwūdī n. 3: "أي: الذريعة".
  - The bricks passage then begins "وذكرت أنّ أول ما يحتاج…".
  - Because "تلك الرسالة" is the *Dharīʿa* in the editor's note, it is ambiguous which earlier work the bricks passage restates. I therefore did not name the *Risāla munabbiha* as its source.
- **suggestion, alternative title.** Added "The book is also known as *Mufradāt alfāẓ al-Qurʾān*." [^iranica]. Iranica (Wayback copy of the cited URL): "The first, more often entitled Mofradāt alfāẓ al-Qorʾān, is a very useful alphabetical dictionary of Qorʾanic Arabic".
- **suggestion, unlabelled glosses.** Labelled as follows:
  - "conventionally understood" and "it has been said" are labelled together: "(translations for this guide)".
  - "a silent yet speaking indication" is labelled.
  - "and the subtle differences between them", from the introduction, is now labelled too. The verifier did not flag it, but it is also a translation made for the guide.
- **suggestion, "usually anonymous".** Rephrased with its own sources: "Poetry is sparse (Dāwūdī counts no more than 500 lines),[^dawudi|p. 25] and the text seldom names the poet; the printed edition's attributions are the editor's.[^dawudi|p. 5]"
  - p. 5, method item 6: "نسبة الأبيات الشعرية لقائليها، وبيان محلها في كتب اللغة والتفسير".
  - "Seldom names the poet" rests on my count of displayed entries: 297 anonymous introductions ("قال الشاعر" and similar) in 239 entries, against 16 that name a poet.
- **suggestion, Dāwūdī year.** Now "1412/1991–92" in both the source citation and onOurSite.

## Changed (summary)

1. summary: C7 wording.
2. lede: C7 wording; "across the whole Qur'an" shortened to "across the Qur'an".
3. Biography paragraph moved to the top of the body. It now introduces Alexander Key and Ṣafwān Dāwūdī by name and adds the alternative title (Iranica).
4. Introduction: "Recalling his earlier writings" (pp. 53–54). *munāsabāt* is now glossed as "between borrowed and derived words" (same source, shorter). The synonyms-sequel quotation is labelled.
5. C18: "surfaces in a few dozen of the … entries we display".
6. C20: Hmd translation.
7. C31: kfr poetry sentence, rewritten as above.
8. Minor tightening of the kfr paragraph ("tendencies, not rules") and of the Ibn Fāris comparison ("illustrated from ordinary speech", "mail-coat"). No change of substance.
9. C44: sjd analysis, as above; "his interpretation" became "an interpretation".
10. Evidence: the poetry sentence is re-sourced (pp. 25 and 5), and "all but a handful" became "nearly every entry we display" (the verifier found 1,242 of 1,267).
11. C54: voice sentence, as above.
12. C56: 340. "Later scholars built on him:" was dropped; the Fīrūzābādī and al-Samīn sentence keeps its citation.
13. Zarkashī paragraph: "explanations offered in the early eleventh century" became "early-eleventh-century explanations"; "gathered in" became "in". No change of substance.
14. onOurSite: 1412/1991–92; the C70 sentence as above.
15. sources: Key URL changed to UC Press; Dāwūdī year changed to 1412/1991–92.

## Removed claims

- "Its entries typically start from a word's plain sense… showing how it was borrowed, extended or narrowed, and how it differs from near-synonyms" (summary), and "A typical entry opens…" (lede). Both over-generalised (C7).
- "the habit runs through the *Mufradāt*" (C18).
- "*Ḥamd* of God Most High" (C20).
- The physical sense "supported by two half-lines from unnamed poets", which implied simple support (C31).
- "The same entry also shows his own analysis" and "the bowing of shadows is 'a silent yet speaking sign'" (C44).
- "His own voice is in the definitions, the 'since … it came to be used' reasoning, and first-person asides" (C54).
- "quotes 'al-Rāghib' by name in some 280 entries" (C56).
- "on the evidence above he belongs in Ibn Fāris's generation" (C70).
- "read the scheme as his interpretation" (it is now "an interpretation", consistent with C44).
- The academia.edu URL for Key.

## New claims (each checked in a source I opened)

1. **"The book is also known as *Mufradāt alfāẓ al-Qurʾān*."** Source: Iranica, van Gelder: "The first, more often entitled Mofradāt alfāẓ al-Qorʾān, is a very useful alphabetical dictionary of Qorʾanic Arabic" (read in the Wayback copy of https://www.iranicaonline.org/articles/rageb-esfahani/).
2. **"Recalling his earlier writings, al-Rāghib opens…"** Source: Dāwūdī ed. p. 53, "كنت قد ذكرت في «الرسالة المنبهة على فوائد القرآن»"; p. 54, "وأشرت في كتاب «الذريعة…»" … "وذكرت أنّ أول ما يحتاج أن يشتغل به من علوم القرآن العلوم اللفظية" (shamela.ws/book/23636/35 and /36).
3. **"The first time, he quotes one to correct some philologists who took *kāfir* in it as a name for night and sower; for him the word only describes them."** Source: stored entry 157 (= Dāwūdī p. 714): "ووصف الليل بالكافر … وليس ذلك باسم لهما كما قال بعض أهل اللّغة لمّا سمع: ألقت ذكاء يمينها في كافر".
4. **"attributing it to no one"** (the sjd two-kinds analysis). Source: stored entry 1465. The passage "وذلك ضربان: سجود باختيار … وسجود تسخير … وهو الدّلالة الصامتة الناطقة…" has no *qīla* and no named authority. By contrast, the entry does use *qīla* for Q 2:34, Q 20:130, Q 72:18 and Q 12:100.
5. **"the habit surfaces in a few dozen of the *Mufradāt* entries we display".** Source: tool grep `(أخص|أعم|أبلغ) من` gives 61 displayed entries.
6. **"the text seldom names the poet; the printed edition's attributions are the editor's".** Sources: Dāwūdī p. 5, "نسبة الأبيات الشعرية لقائليها" (shamela.ws/book/23636/1), and my count of displayed entries (297 anonymous introductions against 16 named).
7. **"an unattributed definition may be older than al-Rāghib, sometimes taken over word for word".** Source: Dāwūdī p. 21, "ويبدو أنّ الراغب قد اعتمد عليه كثيرا، مع أنه لم يذكره باسمه … وربما ينقل عنه حرفيا" (verifier C52/C54). "His own voice is surest in first-person asides" is the guide's inference from this.
8. **"names him in some 340 entries"** (Tāj). Source: my count, 339 of 340 entries containing الراغب cite him (see C56 above).
9. **"that is why it lists him after Ibn Sīda".** Source: `_dict_guide_tool.py dicts` (Ibn Sīda 1066, al-Rāghib 1109) and FORMAT.md "Site facts" (the panel orders by the stored year).
10. **Key URL** https://www.ucpress.edu/books/language-between-god-and-the-poets/paper. Opened: HTTP 200, the publisher's page for the book, marked Open Access with Read/Download links.

## Disputed

None. I accept every NQ verdict. Two fixes are applied more narrowly than the verifier proposed:

- **C54:** "reasoning" and "classifications" are dropped from the list of places where his own voice is clearest.
- **C70:** "not after Ibn Sīda" was not adopted.

The reasons are given under each item above. In both cases the evidence the verifier cited, or Dāwūdī p. 37, supports less than the suggested wording.

## Site-data issues (unchanged from verification-r1, restated for the orchestrator)

1. The stored death year of 1109 (502 AH) is doubted:
   - Iranica: "often stated, without any clear evidence".
   - Key p. 11: manuscript of 409/1018.
   - Dāwūdī pp. 37–38: c. 425/1033–34.
   - Because of this date the panel lists him after Ibn Sīda. A disputed early-11th-century value (c. 1020–1034) would place him near Ibn Fāris.
2. Articles filed under short or alif-spelled headwords are missing: حق، رب، صلا، كان, among others (roots Hqq, rbb, Slw, kwn…).
3. fjj is truncated ("…وجمعه").
4. The research notes (§1b, §8) also record two issues that I did not re-check in this round:
   - Root `swA` (evil) displays al-Rāghib's سوا (equality) article.
   - يوم runs on into the يس article.
