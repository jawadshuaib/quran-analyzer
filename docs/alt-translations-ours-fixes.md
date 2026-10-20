# Our translation: fixes from the alt-translation review (awaiting approval)

**Status:** proposal only. Nothing has been written to the DB and nothing is
synced. Exact before/after texts are in
[alt-translations-ours-fixes.json](alt-translations-ours-fixes.json). Each
change there was produced by a one-hit string replacement on today's
`COALESCE(revised_text, translation_text)` (config 10).

**Source:** `verse_alt_translations` rows with `review_status='pending'` (24) in
the local dev DB. Only `ours_omits` / `ours_mistranslates` differences with
`verifier: "confirmed"` were checked. Each claim was re-read against the Arabic,
the `morphology.features_raw` row and our `departure_notes`. 5:6 was added by
request, and 56:87 because the 56:83/86 fix needs it.

## Summary

| Verdict | Verses |
|---|---|
| **Fix** (19 queue verses + 56:87 companion) | 5:58, 7:203, 9:30, 10:42, 15:8, 23:74, 23:110, 27:36, 37:149, 38:14, 40:57, 50:3, 50:7, 51:59, 53:56, 56:83, 56:86 (+56:87), 102:7, 108:2 |
| **Keep ours**: claim rejected (5) | 2:129, 55:6 (deliberate transliteration), 9:17 (house style), 30:10, 36:35 (Arabic allows our parse) |
| **Owner decision** (not in queue) | 5:6, where I recommend the fix |

Every fix changes only the faulty words. No word-sense choice argued in the
departure notes is touched.

---

## Fixes

### 5:58: نَادَيْتُمْ is active
- **Claim:** "you are called out" is passive. The Arabic is active 2MP ("you call").
- **Check:** `PERF|(III)|2MP`, active. The passive would be نُودِيتُمْ. **Right.**
- **Now:** And when you are called out to the prayer, they take it as mockery and play. …
- **Proposed:** And when **you call** to the prayer, they take it as mockery and play. …

### 7:203: second-person "you bring them"
- **Claim:** "no sign comes to them" drops the addressee.
- **Check:** تَأْتِ `IMPF|2MS|MOOD:JUS` + هِم, and أَتَى بِـ means "bring". The next clause, ٱجْتَبَيْتَهَا, is also 2MS. **Right.**
- **Now:** And when no sign comes to them, they say, …
- **Proposed:** And when **you do not bring them a sign**, they say, …

### 9:30: يُضَٰهِـُٔونَ has the people as subject
- **Claim:** the participle "resembling" attaches to "their saying". The Arabic is a finite 3MP verb.
- **Check:** يُضَٰهِـُٔونَ is a finite imperfect 3MP, and its object is قَوْلَ. The ones doing it are the speakers, not the saying. **Right.**
- **Now:** That is their saying with their mouths, resembling the saying of those who covered [the truth] before.
- **Proposed:** That is their saying with their mouths; **they imitate** the saying of those who covered [the truth] before.

### 10:42: يَسْتَمِعُونَ is plural
- **Check:** `(VIII)|3MP`. مَن takes its number from the verb, so it means "those who". **Right.** The note's "attentively" is kept.
- **Now:** And among them is one who listens attentively to you.
- **Proposed:** And among them **are those who listen** attentively to you.

### 15:8: إِذًا makes the clause hypothetical
- **Check:** وَمَا كَانُوا إِذًا مُنظَرِينَ: إِذًا with a perfect verb forms an apodosis ("in that case they would not be …"). Ours reads as a flat present. **Right.**
- **Now:** … and then they are not ones given respite.
- **Proposed:** … and **in that case they would not be** ones given respite.

### 23:74: لَنَٰكِبُونَ is an active participle
- **Check:** `ACT|PCPL`, form I نَكَبَ, intransitive ("swerve, turn aside"). "Turned away" suggests an outside agent. **Right, but minor.** The note's own image, "turning aside / deflected", is used instead.
- **Now:** … are surely turned away from the path.
- **Proposed:** … are surely **turning aside** from the path.
- Departure note: change the quoted rendering from "are surely turned away from the path" to "are surely turning aside from the path".

### 23:110: أَنسَوْكُمْ has a 3MP subject
- **Check:** `PERF|(IV)|3MP` + كُمْ, so the subject is the ridiculed group, not "it". **Right.**
- **Now:** … until it made you forget My remembrance …
- **Proposed:** … until **they** made you forget My remembrance …

### 27:36: ءَاتَىٰنِۦَ is "me", not "us"
- **Check:** suffix `PRON:1S`. Our departure note admits "us" is "a slight expansion for natural English". That is a change of person, not a word-sense choice, and nothing in the Arabic needs it. **Right.**
- **Now:** What Allah has given us is better …
- **Proposed:** What Allah has given **me** is better …
- Departure note: drop the bullet that justifies "us".

### 37:149: وَلَهُمُ is "for them"
- **Check:** هُمُ `3MP`, and رَبِّكَ is 2MS (addressed to the one told to ask them). Ours turned the line into direct speech to the deniers and changed both pronouns. 37:150–153 stay in the third person. **Right.**
- **Now:** So ask them for a ruling: "Are the daughters for your Lord, while the sons are for you?"
- **Proposed:** So ask them for a ruling: Are the daughters for your Lord, while the sons are for **them**?

### 38:14: عِقَابِ has a 1S suffix
- **Check:** `PRON:1S` (the kasra stands for the dropped yāʾ: عِقَابِي). **Right.** "Requital" (note) is kept.
- **Now:** … so the requital became duly established.
- **Proposed:** … so **My** requital became duly established.

### 40:57: emphatic لَـ dropped
- **Check:** لَخَلْقُ has `l:EMPH`. Ours renders emphatic lām as "surely" elsewhere (23:74). **Right, but minor.**
- **Now:** The bringing-into-being of the heavens and the earth is greater …
- **Proposed:** **Surely** the bringing-into-being of the heavens and the earth is greater …

### 50:3: أَءِذَا is a question
- **Check:** `A:INTG` on إِذَا. The deniers' line is incredulous, and the clause "shall we be returned?" is left unsaid (ذَٰلِكَ رَجْعٌ بَعِيدٌ answers it). Ours is a statement. **Right.**
- **Now:** "When we have died and become dust—this is a far‑fetched return."
- **Proposed:** "**What, when** we have died and become dust **[shall we be returned]? That** is a far‑fetched return."
- "This" also becomes "That", because ذَٰلِكَ is distal and the word follows a question. Drop that part if you want the smallest possible change.

### 50:7: one noun phrase, not two
- **Check:** زَوْجٍ بَهِيجٍ is a noun with its adjective (`M|INDEF|GEN` / `MS|INDEF|GEN`). Ours split it into "every kind" plus a new head noun, "a delightful pair". The note's "pair" sense is kept. The proposal matches ours for the **identical phrase** in 22:5 ("from every delightful pair") and 26:7 ("of every generous pair"). **Right.**
- **Now:** … and We caused to grow in it, from every kind, a delightful pair.
- **Proposed:** … and We caused to grow in it **of every delightful pair**.
- Departure note: retitle the bullet "from every kind, a delightful pair" to "of every delightful pair". Its argument still holds.

### 51:59: يَسْتَعْجِلُونِ has a 1S object
- **Check:** final نِ is `PRON:1S` (the yāʾ is dropped), so "let them not urge **Me** to hasten". **Right.** "Share" for ذَنُوب is kept.
- **Now:** … so let them not seek to hasten it.
- **Proposed:** … so let them not **ask Me to hasten [it]**.

### 53:56: warner and "warnings" mismatch
- **Check:** after نَذِيرٌ, the partitive مِنَ puts it in the same category, and the lemma is نَذِير (MP, "warners"). Ours, "a warner from the earlier warnings", mixes a person with messages. نُذُر *can* mean "warnings" (54:5), and نَذِير can be a verbal noun ("a warning", 67:17). Either consistent pair works. **Right about the mismatch.** I kept ours' "warner" and changed one word.
- **Now:** This is a warner from the earlier warnings.
- **Proposed:** This is a warner from the earlier **warners**.

### 56:83, 56:86 (+ 56:87): فَلَوْلَا is "why not …?"
- **Check:** `POS:EXH`. The لَوْلَا in 83 is resumed in 86, and its verb comes in 87 (تَرْجِعُونَهَا): "Why then, when it reaches the throat … why then, if you are not to be judged, do you not restore it, if you are truthful?" Ours says "So then … you (all) restore it", which loses the challenge. 56:87 has to change too, or the fixed 83/86 lead nowhere. **Right.**
- **56:83 now:** So then, when it reaches the throat— → **Why then**, when it reaches the throat—
- **56:86 now:** So then, if you are not ones who will be judged, → **Why then**, if you are not ones who will be judged,
- **56:87 now:** you (all) restore it, if you are truthful. → **do** you (all) **not** restore it, if you are truthful**?**
- 56:87 has no `verse_alt_translations` row to approve. Only its `revised_text` changes.

### 102:7: عَيْنَ ٱلْيَقِينِ is adverbial
- **Check:** عَيْنَ is `ACC` (a seeing of the very certainty), so it describes *how* they see. Ours, "see it as the eye of certainty", makes the thing seen be "the eye". "With" mirrors ours' 102:5 ("with the knowledge of certainty"). **Right.**
- **Now:** Then you will surely see it as the eye of certainty.
- **Proposed:** Then you will surely see it **with** the eye of certainty.

### 108:2: the لِ of لِرَبِّكَ was dropped
- **Check:** `l:P+`. The hard-case transliteration pass (`apply_hard_case_transliterations.py`, rule 3) was meant to drop prepositions the Arabic *lacks*. Here it dropped one the Arabic *has*. The original had "for your Lord". **Right.** *ṣalli* stays transliterated.
- **Now:** So *ṣalli* your Lord, and …
- **Proposed:** So *ṣalli* **for** your Lord, and …
- Follow-up, not part of this change: the 108:2 departure note still argues that صَلِّ "clearly denote[s] the established act of prayer". That conflicts with the transliteration and the Qur'an-only principle and should be rewritten.

---

## Claims rejected (keep ours)

### 2:129 *yuzakkīhim* and 55:6 *yasjudāni*: deliberate transliteration
Both judges flagged these as "untranslated". They are hard cases that
`apply_hard_case_transliterations.py` transliterated on purpose: italic,
glossary-tooltip words, chosen because any single English word imports a
meaning. That is the project's policy, not an omission. **Keep.**

### 9:17: مَا كَانَ … "It was not for"
The verifier is right that مَا كَانَ لِـ… أَن states a standing unfitness. But
ours renders this idiom "It was not for …" everywhere (3:161, 8:67, 9:113, 12:38;
19:35 "It was never for"), and in English that wording also carries the sense
"it was never fitting". Changing only 9:17 would break consistency. **Keep.** If
you want "It is not for", it should be one pass over every مَا كَانَ لِـ verse.

### 30:10: ثُمَّ كَانَ عَٰقِبَةَ … ٱلسُّوٓأَىٰٓ أَن كَذَّبُوا
The verifier relied on the Corpus tagging ٱلسُّوٓأَىٰ as NOM. But the word ends
in alif maqṣūra, so its case is **not visible**: the tag is an analysis, not the
text. With عَٰقِبَةَ accusative (fronted predicate), the subject of كَانَ can be
either ٱلسُّوٓأَىٰ ("the worst was the outcome … because they denied") or
أَن كَذَّبُوا ("the outcome of those who did the worst [evil] was that they
denied"), with ٱلسُّوٓأَىٰ as the object of أَسَٰٓـُٔوا. Ours is the second, a
legitimate parse that the visible text fully supports. It also fits the Qur'an's
own pattern of wrongdoing leading to blindness to the signs (61:5, 83:14).
**Keep.**

### 36:35: وَمَا عَمِلَتْهُ أَيْدِيهِمْ
مَا here can be negative ("and their hands did not make it") or relative ("and
[of] what their hands have worked", joined to ثَمَرِهِ). The Corpus picked the
negative reading. That is a choice, not something the text forces. The same
surah uses the relative wording for the same verb-and-hands phrase in 36:71
(مِمَّا عَمِلَتْ أَيْدِينَا, rendered by ours as "from what Our hands have
worked"). **Keep.** Optionally, add a departure-note line that the negative
reading exists (compare 56:63–64, "is it you who make it grow, or We?").

---

## 5:6: feet (owner decision; recommend fix)

- **Arabic (Ḥafṣ, as displayed):** وَٱمْسَحُوا۟ بِرُءُوسِكُمْ وَأَرْجُلَكُمْ إِلَى ٱلْكَعْبَيْنِ
- **Morphology:** بِرُءُوسِ `GEN` (after bi-), أَرْجُلَ **`ACC`**. The same case as وُجُوهَ and أَيْدِيَ, the objects of ٱغْسِلُوا.
- **Ours:** "and wipe your heads and your feet up to the ankles". This follows the other case reading.
- **Assessment:** On the text we display, the case grammar groups the feet with the washed parts. The verse's own structure points the same way: the washed parts have limits (إِلَى ٱلْمَرَافِقِ, إِلَى ٱلْكَعْبَيْنِ), while the head has none. "Wipe" is still grammatically possible: the accusative can be joined to the *position* of بِرُءُوسِكُمْ, the object of the nearer verb. And the genitive reading وَأَرْجُلِكُمْ (Ibn Kathīr, Abū ʿAmr, Ḥamza and Shuʿba, among others) gives "wipe" outright. So this is a real textual question, not a slip. Ours currently takes a side that the displayed text does not show.
- **Recommended:** … and wipe your heads, and **[wash]** your feet up to the ankles. The brackets show the verb is implied by the case, not written.
- **Departure note to add:**
  > - "[wash] your feet": وَأَرْجُلَكُمْ is accusative in the text shown, matching وُجُوهَكُمْ وَأَيْدِيَكُمْ (objects of ٱغْسِلُوا), and like them it has a limit (إِلَى ٱلْكَعْبَيْنِ) where the head (بِرُءُوسِكُمْ, genitive after bi-) has none. "Wash" is therefore supplied in brackets. The genitive reading وَأَرْجُلِكُمْ attaches the feet to ٱمْسَحُوا ("wipe").
- **Alternative:** keep "wipe" and add only the note. I don't recommend this, because the English would then contradict the displayed Arabic.

---

## Applying after approval

1. For each approved entry in `alt-translations-ours-fixes.json`, write `proposed` to `ai_translations.revised_text` (config 10). Do this for both kinds of rows: those where `field_source` is `revised_text` (108:2) and those where it is `translation_text`. Leave `translation_text` untouched. Apply the departure-note edits for 23:74, 27:36, 50:7 and 5:6 (if approved).
2. **The alt rows' public `reader_note` and `tier` quote the old faulty text** (for example, 5:58: "our translation mistranslates it as 'you are called out'"). After step 1, re-run `alt_translations_ai.py judge → verify → notes → load` with `--verses` limited to the fixed refs, so the note and tier describe the corrected text. If you skip this, the notes stay wrong on the site.
3. Then set `review_status='approved'` for all 24 queue rows: the fixed ones, and the five "keep ours" rows, whose claims were reviewed and whose text stands. Use PATCH `/api/admin/alt-translations/<s>:<a>` or SQL.
4. Prod sync only on your go-ahead.
