# Lisān al-ʿArab: revision after verification round 2

Reviser: revision agent, 2026-09-26.

Input: `verification-r2.md`, which found 75 claims: 74 supported, 1 needing qualification (C32) and 0 unsupported. It also made 2 suggestions.

Files edited:
- `roots/frontend/src/content/dictionary-guides/guides/lisan-al-arab.ts`
- `docs/research/dictionary-guides/lisan-al-arab/research-notes.md` (§13 appended)
- this log

Nothing else in the repo was touched.

Validator after revision: `node scripts/validate-dictionary-guides.mjs lisan-al-arab` gave **ok, 1/1 pass, 0 errors**.
- Lede + body: 1,097 words (was 1,080; ceiling 1,100).
- Root links: 12 (10 pairs). jmE is new, and the validator confirms the entry is displayed.
- Excerpts: 3, unchanged.
- The only warnings are the two deliberate `none` links (slm, Slw) in onOurSite. The sentence there explains both.

## Flagged claim

### C32 (needs qualification): departures from the five sources

**Before:** "Occasionally, though, he steps outside them and says so, as with al-Suhaylī below."

**After:** "Occasionally, though, he steps outside them and says so, as with al-Suhaylī below; yet under [[root:jmE|ibn-manzur-lisan-al-arab|ج م ع]] al-Suhaylī's *al-Rawḍ al-unuf* is quoted unsigned, with no word on how it reached the entry.[^lisan-ds|vol. 8, p. 58]"

**Evidence I opened myself:**
- **Displayed jmE entry** (`_dict_guide_tool.py entry jmE ibn-manzur-lisan-al-arab`): "وزعم ثعلب أَن أَوّل من سماه به كعبُ بن لؤيّ … وذكر السهيلي في الرَّوْض الأُنُف أَنَّ كعب بن لؤيّ أَوّلُ من جَمَّع يوم العَرُوبةِ، ولم تسمَّ العَروبةُ الجُمعة إِلا مُذ جاء الإِسلام". Neither "قال محمد بن المكرم" nor any closing formula comes before or after it.
- **Print:** Dār Ṣādir vol. 8 p. 58 (Shamela 1687/3906; page selector "ج: 8", `data-page-num` 58). It has the same passage, also unsigned: "وَذَكَرَ السُّهَيْلِيُّ فِي الرَّوْض الأُنُف أَنَّ كَعْبَ بْنَ لُؤَيٍّ أَوّلُ مَنْ جَمَّع يَوْمَ العَرُوبةِ …".
- **Site English rendering:** the displayed English also carries the passage ("al-Suhaylī (in al-Rawḍ al-Unuf): Kaʿb was the first to 'gather' …"), so a reader who follows the link will find it.

**Why this wording and not the verifier's first proposal:**
- The verifier's main fix said he "reaches beyond them … sometimes not". That makes the jmE passage a departure from the five. The verifier's own note says its "exact route is not established".
- I have not ruled out that it came through one of the five sources, for example Ibn Barrī's notes. So I kept the verified facts only: the quotation is unsigned, and the entry does not say how it got there.
- The sentence no longer lets a reader infer that every quotation of a later authority is flagged, which was the verifier's concern. It also does not claim the jmE remark is Ibn Manẓūr's own addition.
- I added the print locator so the claim can be traced in the edition as well as on our site.

## Brief suggestions (both taken)

1. **Locator for "By his own account he kept within his five books"** changed from `vol. 1, p. 7` to `vol. 1, pp. 7–8`. The p. 7 sentence ("ولم أخرج فيه عما في هذه الأصول") covers the four sources named so far. The Nihāya and the phrase "الأصول الخمسة" come on p. 8. Both points are per verification-r2 C30, and research-notes §2 and §12 agree.
2. **onOurSite citation placement.** `[^haywood|p. 81]` now follows "(Cairo, 1300–1308 AH)," directly. That is the only thing Haywood p. 81 n. 15 supports. The footnote sentence keeps `[^lisan-ds|vol. 1, p. 3; vol. 4, p. 44]` alone.

## Other edits

- **Word budget.** The addition pushed lede + body to 1,105 words. I trimmed two places to get back under the 1,100 ceiling:
  - I merged the new clause into the C32 sentence ("; yet under …") instead of adding a separate sentence.
  - "appears in just 24 of the 1,452 entries on our site" became "appears in just 24 of our 1,452 entries". The meaning is the same.
- **lisan-ds source citation.** The list of entries consulted now reads "entries صلح (vol. 2), بحر (vol. 4) and جمع (vol. 8)", to match the new locator.

## Removed claims

None. C32's clause "he steps outside them and says so, as with al-Suhaylī below" stays; the verifier found it true of bHr. It is now followed by a counter-example, so it no longer implies that departures are always announced.

## New claims (each with its evidence)

1. **"under [[root:jmE|…|ج م ع]] al-Suhaylī's *al-Rawḍ al-unuf* is quoted unsigned"**. The displayed jmE entry and Dār Ṣādir vol. 8 p. 58 (Shamela 1687/3906) both read "وذكر السهيلي في الروض الأنف أن كعب بن لؤي أول من جمع يوم العروبة…". Neither has a signature.
2. **"with no word on how it reached the entry"**. The same passage names no intermediate source. The sentences on either side are "وزعم ثعلب…" before and "وفي الحديث: أول جمعة جمعت بالمدينة" after. Neither names one of the five books as the source of the al-Suhaylī quotation.

## Disputed

None. I accepted the verifier's qualification. I did not adopt the proposed wording "reaches beyond them … sometimes not", because it goes one step further than the evidence. The verifier's report says the route is unestablished.
