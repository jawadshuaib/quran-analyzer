# al-misbah-al-munir: verification of the cross-check revision (2026-09-26)

Independent check of the heading and wording revision described in
revision-crosscheck.md. I did not read research-notes.md or the revision files
as evidence. I checked the guide text itself, the sources it cites, the site
code and the validator.

## Scope

The revision changed three headings and two sentences. It declared no new
claims. The rest of the guide was verified in earlier rounds (r1, r2) and was
not re-audited here.

## Changed passages

1. `## Reading an entry` became `## Fixing a word's form`.
   The section (lines 23-35) covers the *min bāb* model-verb formulas,
   *bi-l-alif* and *bi-l-tashdīd*, *lugha*, *ʿāmmī* and *al-ṣawāb*, and his
   sources. Most of it is about fixing a word's vowelling, conjugation and
   correct form, so the heading fits. The last paragraph, on sources and
   al-Azharī, is secondary to the heading but is not misdescribed.
   **Supported.**

2. "Entries work to fix a word's form, as the introduction explains:" became
   "His introduction explains how:".
   The quotation that follows is from the introduction. I opened
   ar.wikisource.org/wiki/المصباح_المنير/مقدمة, which reads:
   "وقيدت ما يحتاج إلى تقييد بألفاظ مشهورة البناء فقلت مثل فلس وفلوس وقفل
   وأقفال … وفي الأفعال مثل ضرب يضرب أو من باب قتل وشبه ذلك". This matches
   the guide's quotation and its use of an ellipsis. In "explains how", the
   word "how" points back to the heading (how he fixes a word's form), and the
   quotation says exactly that. **Supported.**

3. `## Whose voice?` became `## Where a quotation stops`.
   The section (lines 63-75) shows *hādhā lafẓuhu* closing al-Azharī's
   quotation and *wa-fīhi naẓar* as al-Fayyūmī's own voice. It then shows the
   quotation of Abū Ḥayyān in the ف ض ل entry. The heading fits.
   **Supported.**

4. "A reader of so condensed a book needs to know where a quotation stops."
   became "So condensed a book makes it easy to lose track of who is
   speaking."
   This is an editorial framing, not a factual claim. "Condensed" is supported
   by the introduction, where he says he abridged his longer work:
   "أحببت اختصاره على النهج المعروف" (Wikisource, as above). This matches the
   guide's existing statement that the *Miṣbāḥ* abridges the earlier book.
   **Supported (interpretation, suitably framed).**

5. `## Using it with the Qur'an` became `## Form, register and date`.
   The section (lines 77-81) covers form, the legal and ordinary register, and
   what the book can and cannot say about the date of a meaning. Its last
   paragraph is about later lexicographers who used the book, which the new
   heading does not name. The old heading did not cover that paragraph either,
   so the fit is no worse. **Supported.**

## New claims

None were declared, and none were found. Comparing the current text with the
changes described, the edits touch only headings and wording. No fact, count,
citation, quotation, translation or root link was altered.

## Site checks

- Heading uniqueness: a search of `roots/frontend/src/content/dictionary-guides/guides/`
  for the three new headings finds them only in al-misbah-al-munir.ts.
- Anchors: `DictionaryGuideProse.tsx` derives each heading id from the heading
  text (`headingId(b.text)`). A search of roots/frontend/src and
  roots/frontend/scripts for the old or new slugified anchors
  (reading-an-entry, whose-voice, using-it-with-the-qur…, and the new ones)
  finds nothing, so no internal link breaks.
- Validator: `node scripts/validate-dictionary-guides.mjs al-misbah-al-munir`
  gives "ok": 10 root links, 3 excerpts, 1,139 words in lede and body, with no
  errors or warnings.

## Notes (not caused by this revision)

- At 1,139 words, lede and body are slightly above the brief's target of about
  700-1,100 words. The revision cut the count by roughly 4 words. The validator
  does not flag this. I did not trim anything, because this round is limited to
  the changed passages.

## Result

All 5 changed passages are supported. No new claims were made. No fixes were
needed, and the guide file was not edited in this round.
