# Tuḥfat al-Arīb: final conservative pass (2026-09-26)

Input: the guide after revision r2 and verification r3. One claim was still flagged (C8, needs qualification). No brief issues were open.

## Change

| Field | Before | After | Why |
|---|---|---|---|
| `summary` | "Entries quote the Qur'anic form and usually give a one- or two-word equivalent suited to a particular verse, seldom showing evidence." | "Entries quote the Qur'anic form and usually give a one- or two-word equivalent, often suited to one particular verse, and seldom show evidence." | Verification r3 (C8): "usually" was attached to the verse-specific claim. Many glosses are verse-bound, such as ظ ن ن {يظنون}: يوقنون and the 221 multi-word braced phrases. But on a loose skeleton match, about 515 single-word glossed forms occur in 4 or more verses. Some glosses are plainly general: {الكهف}: غار في الجبل (p. 272) and {عدن}: إقامة (p. 230). "Usually" now applies only to the length of the gloss, which C7 supports: 61–63% of glosses are two words or fewer. The verse-specific part drops to "often". This is the verifier's suggested wording and matches the lede, where C12 found it supported. |

## Removed

- The claim that the usual gloss is "suited to a particular verse". It is now "often suited to one particular verse".

## Not added

- No new factual claim. "Often suited to one particular verse" restates the lede's hedge, which verification r3 checked (C12). The rest of the sentence is unchanged apart from grammar ("seldom showing" became "and seldom show").

## Left as is

- The lede and body. Verification r3 found every other claim supported (71 of 72).
- `onOurSite` length (about 185 words). Verification r3 suggested an optional trim but did not require it, and every sentence there is a verified, work-specific fact. No brief issue was open, so I left it.
- Essay length: 1,081 words, within the ceiling and not padded.
- `limitedEvidence`: not needed. The page is not deliberately short.
- `lastVerified`: not set in this pass.

## Validator

`node scripts/validate-dictionary-guides.mjs tuhfat-al-arib` returns **ok**: 12 root links (10 distinct pairs), 5 excerpts, 1,081 words; 1/1 guides pass. The summary is 44 words (limit 45).

- One warning remains: the `[[root:kyn|none|…]]` link in `onOurSite`. The sentence around it explains the link: the *Tuḥfa* has no ك ي ن entry and glosses *istakānū* under ك و ن.

## Still open (site data, not the essay; carried from verification r3)

- kwn (entry 117). The harmonized and faithful English present the modern editor's bracket "[جسرة]" as a manuscript variant.
- mEn (entry 16654). The harmonized English ends with an editorial aside that is not the author's.
- About 50–55 printed headwords (e.g. برزخ, عدن, ويل) have no stored entry, although hawramani's index lists several of them. This is a gap in our scrape.
