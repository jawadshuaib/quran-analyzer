# Tāj al-ʿArūs — verification of the cross-check revision (round 99)

Verifier: independent fact-check agent, 2026-09-26. Scope: only the passages
changed in the cross-check revision and the two new or reworded claims. I did
not read research-notes.md or any revision-*.md. The guide file was not
modified by this check.

## Validator

`node scripts/validate-dictionary-guides.mjs taj-al-arus` → **ok** (1/1 pass).
11 root links (10 distinct pairs), 4 excerpts, 1,111 words (lede + body).
Summary 44 words (limit 45). Lede 73 words.

## Changed passages

| # | Change | Check | Verdict |
|---|---|---|---|
| 1 | Body ¶1: `[[guide:al-qamus-al-muhit|*Qāmūs*]]` | registry.ts maps `firuzabadi-al-qamus-al-muhit` → `al-qamus-al-muhit`. The sentence is about al-Fīrūzābādī's *Qāmūs*, so the target is right. Validator accepts it. | supported |
| 2 | Brackets section: `[[guide:lisan-al-arab|*Lisān*]]` | registry.ts maps `ibn-manzur-lisan-al-arab` → `lisan-al-arab`. The sentence names Ibn Manẓūr's introduction to the *Lisān*, so the target is right. | supported |
| 3 | Summary sentence 2 | See claim A. "Often shows who recorded a meaning and on what evidence" fits the displayed entries. For example, fsd credits Muslim al-Baṭīn and al-Zajjāj for verse readings. An attribution scan (claim B) finds a named authority in 1,599 of 1,600 entries. "Often" rather than "always" suits entries like lqb, where the quoted material has no name attached. | supported |
| 4 | Heading "Brackets, markers and a borrowed self-portrait" | The section covers three things. First, the bracket and red-ink conventions. Second, markers (*al-muṣannif*, *shaykhunā*, *qultu*, *intahā*, *wa-mimmā yustadrak ʿalayh*). Third, the modest passage the body itself calls "the modest self-portrait is borrowed", taken from Ibn Manẓūr. The heading describes the section and adds no new claim. | supported |
| 5 | Heading "As old as its sources" | This echoes the section's own closing sentence ("Each item in an entry is as old as its source, not as old as the *Tāj*"). It adds no new claim. | supported |
| 6 | Deleted stock line ("It cannot tell you what a word means…") | Confirmed absent. Removing it drops no citation and leaves no dangling reference. | n/a (deletion) |
| 7 | Lede ending "Its entries interleave three voices…" | See claim B. | supported |

## New / reworded claims

**A. "on our site the *Qāmūs*'s words are not always bracketed apart."**
I recomputed this myself from `dictionary_entries`, using the same
displayed-entry filter as `_dict_guide_tool.py`, over the 1,600 displayed
Tāj entries:
- 626 of 1,600 (39%) have no round bracket in their first 80 characters.
- 589 have fewer than 2 round brackets per 1,000 characters. 23 have none at all.
- A random sample of the first group shows the *Qāmūs* text running on with no
  brackets: dkk, Ewq and k$f (dkk and Ewq have stray `{ }` digitisation
  marks in their place) and hmr. A random sample of the second group shows
  proper brackets: gnm, Hdb and *rw.
- kfr and xlq, which onOurSite cites, open unbracketed. Their few brackets
  (0.8 and 1.5 per 1,000 characters) enclose verse and Qur'an citations.

"Not always" is the weaker form of onOurSite's "roughly a third". Both hold on
my count (roughly 37–39% by the two measures). **Supported.**

**B. "Its entries interleave three voices: the *Qāmūs*, al-Zabīdī himself, and the many scholars he quotes."**
- I scanned all 1,600 displayed entries (vowel marks removed) for named
  authorities or sources: قال/قاله, الجوهري, الصحاح, الليث, الأزهري,
  التهذيب, المحكم, شيخنا, ابن سيده, الفراء, ثعلب, العباب, الصاغاني,
  الأساس and others. 1,599 match. The only exception is **lqb**, whose
  commentary quotes material with no name attached ("يقول: …").
- I read the four shortest entries. Each one has bracketed *Qāmūs* text,
  commentary and a named authority:
  - dsw: الجوهري, الليث, ابن الأعرابي
  - swH: كراع, الجوهري
  - dxr: الزجاج, الأساس, a hadith
  - wTr: الزجاج, الخليل, الليث. Here the *Qāmūs* text is marked by `{ }` rather than `( )`.
- The claim is a general description ("its entries"), not "each entry", so
  the one exception does not falsify it. The guide already says elsewhere
  (onOurSite; Lane's complaint about unacknowledged *Lisān* borrowings) that
  the voices cannot always be told apart. **Supported.**

## Notes (not errors)

- Lede + body is 1,111 words. That is marginally over the brief's "roughly
  700–1,100" and within "roughly". No cut is needed for accuracy.
- Site data: stored date 1790 vs death in Shaʿbān 1205 AH, which falls in
  April–May 1791 CE (the guide says "the spring of 1791", citing al-Jabartī).
  This was reported in earlier rounds, and the database was not edited.

## Result

No unsupported claims and nothing needing qualification. No edits were made to
the guide in this round.
