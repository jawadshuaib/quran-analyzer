# Highlights for the dictionary entries that open first on al-nuqta

al-nuqta.com has a page for each of the 1,642 Arabic roots used in the Qur'an. Each page lists
what the classical Arabic dictionaries say about the root, and one entry opens automatically: a
readable English version of that dictionary's entry. `entries.csv` holds those 1,642 entries, in
67 batches (b000 to b066). Your job is to add highlights to them so that a reader can see at a
glance what matters most, following the rules in Part B exactly.

Part A is for the session that coordinates the work. Part B is for whoever highlights entries.
Part C shows the standard, with four entries already done (batch b000).

---

## Part A: coordinating the run

You are the coordinator. You hand batches to subagents and keep the branch up to date. Do not read
or highlight entries yourself: that keeps your context small for a long run.

1. Work from the repository root. Check the branch: `git rev-parse --abbrev-ref HEAD` must print
   `claude/dict-highlights`; if not, `git fetch origin claude/dict-highlights && git checkout claude/dict-highlights`.
2. Check progress: `python3 cloud/dict-highlights/job.py status`.
3. Repeat until `python3 cloud/dict-highlights/job.py next 4` prints `(none left)`:
   1. **Pause check.** Run `git fetch origin claude/dict-highlights`, then
      `git show origin/claude/dict-highlights:cloud/dict-highlights/PAUSED`. If that command succeeds,
      the owner has paused the job: commit and push whatever is finished, then stop and say so.
   2. Take the next 4 batch ids from `job.py next 4` and start 4 subagents in parallel (Agent tool),
      one batch each, with this prompt (replace BATCH):

      > You are adding highlights to dictionary entries for al-nuqta.com. Read
      > cloud/dict-highlights/TASK.md, Parts B and C, carefully before you start. Then run
      > `python3 cloud/dict-highlights/job.py show BATCH` and highlight every entry in that batch by
      > the rules, writing cloud/dict-highlights/out/BATCH.json. Run
      > `python3 cloud/dict-highlights/job.py check BATCH` and fix every error it reports until it
      > prints OK. Reply with the checker's final line only.

   3. When all four have replied, run `python3 cloud/dict-highlights/job.py check all`. If a batch
      still fails, give it to one new subagent with the same prompt plus: "An out/BATCH.json already
      exists; fix the errors the checker reports, keeping everything else."
   4. Commit and push the finished files:
      `git add cloud/dict-highlights/out && git commit -m "Highlights: <batch ids>" && git push origin HEAD:claude/dict-highlights`.
4. When no batch is left: run `python3 cloud/dict-highlights/job.py merge`, commit
   `cloud/dict-highlights/highlights.jsonl`, push, and finish with the output of `job.py status`.

Never edit `entries.csv`, `job.py`, `TASK.md` or `out/b000.json`. Never touch files outside
`cloud/dict-highlights/`. Push only to `claude/dict-highlights`.

---

## Part B: how to highlight an entry

### What the highlights are for

The site reads the Qur'an's words from evidence: first the Qur'an's own usage, then how the words
were used in the Qur'an's own time (pre-Islamic poetry, proverbs, the speech of the Arabs). It
does not import meanings codified later (legal, theological, exegetical or hadith-derived
definitions). The highlights follow the same principle. They point at what the entry says and at
its evidence; they never add an interpretation of your own.

Readers see four kinds of mark. Each highlight is a phrase copied exactly from the entry.

### 1. `core` (yellow): core meaning

The entry's statement of what the root's words share: the underlying or original sense that the
author, or an authority he quotes, says the root indicates. It also covers a statement that the
root has two or three separate origins, or that its words share no common sense.

- Usually one; at most two (when the author gives two separate origins, highlight the short
  statement of each).
- A plain definition of one word ("ḥasad is envy") is not a core meaning, unless the entry itself
  presents it as the root's sense.
- Prefer the author's statement to the English editor's summary. A closing line such as "The entry
  is compact: it derives the place-name and the notion of ill omen alike from the single 'left side'
  sense" is the editor's framing; highlight instead "one root whose core notion is **the left-hand side**".
- If the entry makes no such statement, give no core highlight.

### 2. `quran` (orange): the Qur'an's words

`job.py show` lists the word forms the Qur'an uses from the root, with their counts and a rough
translation. Highlight either:

- the entry's definition of a word form on that list, **in the sense the Qur'an uses it**
  (in ʾ-r-ḍ, "al-arḍ, the earth we stand on", and not the head-cold or trembling senses of the same
  root, which the Qur'an does not use); or
- the entry's own explanation of a Qur'anic verse through the ordinary meaning of the word
  ("This word is set as the opposite of istikbār ... in Q 34:33").

Up to 3, or up to 4 in entries over 3,000 characters. Prefer the forms the Qur'an uses most.

You mark only what the entry says; you do not decide a contested meaning. Some words' Qur'anic
meaning is itself the subject of study, among them ṣalāt, zakāt, dīn, islām, īmān, kufr, shirk,
taqwā, ḥajj, ṣawm, jihād, ʿibāda, nabī, rasūl, ḥalāl, ḥarām, ṭahāra, jinn, malak, rūḥ, sunna,
ḥikma and khalīfa. For these, highlight only the entry's concrete, ordinary-language senses (for
ṣ-l-w, "to supplicate" or "to follow closely"). Never give a religious or legal definition the
orange mark: "the ritual prayer with its prescribed bowings" is later interpretation, not the
Qur'an's word.

When the entry cites a verse but the explanation comes from an exegete or a hadith ("al-Zajjāj says
it means ...", "Mujāhid said ...", "per Ibn ʿAbbās ..."), that is `later`, not `quran`.

### 3. `early` (blue): early usage

The best witnesses of the word in use in the Qur'an's own time: a line of poetry or rajaz, a
proverb, a saying of the Arabs, a report of how the Bedouin speak.

- Use the line "Poets the entry names (era)". Prefer pre-Islamic poets and poets who lived into
  Islam. Use an Umayyad poet only when the entry has no earlier witness. Never use a later (Abbasid
  or after) poet.
- A proverb or saying of the Arabs counts. An unnamed verse counts only when the entry has no named
  early witness, and preferably when it attests a sense the Qur'an uses.
- Highlight the phrase that shows the witness: the quoted line, or the sentence that names the poet
  and says what the line shows.
- At most two. Prefer witnesses to the senses the Qur'an uses.
- Philologists who report or recite a line (Ibn al-Aʿrābī, al-Aṣmaʿī, Thaʿlab, al-Farrāʾ,
  Abū ʿUbayda, al-Layth, al-Azharī, Sībawayh, Ibn al-Sikkīt and the like) transmitted it; they are
  not its poets.
- The note names the poet and era as the "Poets the entry names" line gives them
  ("Imruʾ al-Qays, pre-Islamic"), or says "proverb", "saying of the Arabs" or "unattributed verse".

### 4. `later` (dotted underline): later interpretation

A sense drawn from a hadith, a prophetic report or a Companion's saying; an exegete's reading of a
verse; a legal (fiqh) or theological definition; Sufi or later technical usage.

- Mark it only where it carries a meaning in the entry, meaning the entry defines or distinguishes
  the word through it. Passing mentions don't count.
- At most three. On the page this is a quiet dotted underline that tells readers to weigh the
  passage; mark the phrase that states the later sense.
- The note gives the kind of source and its name if the entry gives one: "a hadith",
  "exegete al-Zajjāj (d. 923)", "legal definition", "the author's own exegesis of Q 30:54".

### Form and limits (the checker enforces all of these)

- `text` is copied character for character from **one** line of the entry, as numbered (L1, L2 ...)
  by `job.py show`. It is 8 to 300 characters long, occurs only once in the entry (if it occurs
  twice, lengthen it), and has no leading or trailing space.
- Begin after a line's list or heading marker ("1. ", "- ", "## "). Leave section labels
  ("1. **Core sense.**", "Etymology.") unhighlighted and start after them.
- A highlight includes a whole **bold** or *italic* run or none of it; never cut through one.
- Mark phrases, not paragraphs: a clause or a short sentence.
- Highlights never overlap.
- `core`, `quran` and `early` together cover at most 20% of the entry's characters (or 160
  characters in a short entry). Aim for 10 to 15%.
- Typically 3 to 6 highlights for an entry of 1,000 to 2,000 characters, and at most 10 for the
  longest. A very short entry may have only one. `"highlights": []` is allowed when nothing
  qualifies, but it should be rare.
- `note`: at most 100 characters of plain English, shown to readers in a tooltip. It is required
  for `early` and `later` and recommended for the others.

### The output file

One file per batch, `out/<batch>.json`, covering every entry in the batch:

```json
{"batch": "b001", "entries": [
  {"entry_id": 12471, "highlights": [
    {"kind": "core", "text": "one root whose core notion is **the left-hand side**", "note": "Ibn Fāris's root sense"},
    {"kind": "quran", "text": "الْمَشْأَمَة (al-mashʾama) is the left side", "note": "مَشْـَمَة, 3 times"}
  ]},
  ... one object like this for every entry in the batch ...
]}
```

### The standard

Readers will see these highlights on a public site, under the dictionary's name. Precision matters
more than coverage: when you are unsure whether a passage qualifies, leave it unmarked. Never give
the orange mark to a sense the Qur'an does not use (check the word list), and never to a doctrinal
definition.

---

## Part C: worked examples (batch b000, already done)

Run `python3 cloud/dict-highlights/job.py show b000` and read `out/b000.json` beside it.

- **ʾ-r-ḍ, Ibn Fāris.** `core`: "whatever lies low and faces the sky", the principal origin.
  `quran`: "From the same origin comes al-arḍ, the earth we stand on" (the Qur'an's arḍ, 461 times)
  and "it never occurs in the plural in the Qurʾān" (the entry's own note on Qur'anic usage).
  `early`: the Imruʾ al-Qays witness for fertile land. Left unmarked: the head-cold and trembling
  senses, which the Qur'an does not use; and Dhū al-Rumma, an Umayyad poet, since an earlier
  witness exists.
- **j-ʿ-l, al-Muḥkam.** No `core`: the entry never says what the root's words share. `quran`: three
  verbal senses of the Qur'an's jaʿala (place; make; transform X into Y). `early`: Abū Zubayd's
  line (he lived into Islam). `later`: al-Zajjāj's reading "We made it plain". Left unmarked:
  fees, bribes, beetles and palms, none of which is a sense the Qur'an uses.
- **ḥ-s-d, Tāj al-ʿArūs.** `core`: Ibn al-Aʿrābī's root sense, qashr (stripping bark). `quran`:
  the definition of ḥasad. `early`: Shamir al-Ḍabbī's line. `later`: the distinction from ghibṭ,
  drawn from a reply attributed to the Prophet.
- **ḍ-ʿ-f, al-Mufradāt.** Two `core` (weakness; doubling). Three `quran`: al-mustaḍʿafīn, the
  Qur'an's own contrast with istikbār, and the doubling verbs behind yuḍāʿifu. `early`: an
  unattributed verse, since the entry names no early poet. Two `later`: al-Rāghib's own exegesis of
  Q 30:54, and Ibn ʿAbbās's reading of Q 94:5–6.
