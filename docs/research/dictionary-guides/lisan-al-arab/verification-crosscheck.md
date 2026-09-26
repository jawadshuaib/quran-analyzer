# Verification — cross-check revision (round 99), *Lisān al-ʿArab*

Verifier: independent fact-check agent, 2026-09-26. I did not read research-notes.md or revision-*.md. I checked every changed passage and every new claim against sources I opened myself: the displayed entries (`_dict_guide_tool.py entry …`), the Shamela Dār Ṣādir text of the introduction, and the Baalbaki 2019 PDF.

Validator: `node scripts/validate-dictionary-guides.mjs lisan-al-arab` gives **ok** (12 root links, 3 excerpts, 1,096 words). It raises two warnings, both from earlier rounds: `[[root:slm|none|…]]` and `[[root:Slw|none|…]]` in onOurSite. The sentence around them explains that the *Lisān* has no entry for these roots here, so they need no change.

I made no edits to the guide.

## Changed passages

1. **Link `[[guide:al-muhkam|*al-Muḥkam*]]`.** SUPPORTED. The introduction names "الْمُحكم لأبي الْحسن عَليّ بن إِسْمَاعِيل بن سَيّده" (Shamela 1687, vol. 1, p. 7). `al-muhkam` is in registry.ts, mapped from `ibn-sida-al-mursi-al-muhkam-wa-l-muhit-al-aazam`, and guides/al-muhkam.ts exists. In `utils/dictionary-guide-markup.tsx`, `renderGuideInline` renders a guide-link label recursively, so the `*…*` in the label shows as italic. INLINE_RE matches `[[guide:` before `*`, so the link is parsed correctly.
2. **Link `[[guide:al-sihah|*al-Ṣiḥāḥ*]]`.** SUPPORTED. The introduction names "أَبَا نصر إِسْمَاعِيل بن حَمَّاد الْجَوْهَرِي … مُختصره" (vol. 1, p. 7). `al-sihah` is in registry.ts and guides/al-sihah.ts exists.
3. **Heading renamed to "A survey, not a verdict".** This makes no factual claim. It fits the section, which says the *Lisān* "cannot tell you which sense a verse uses" and reports glosses as opinions.
4. **"Most of its evidence is older than the book: its sources were already old — al-Azharī died in 370/981, Ibn al-Athīr in 606/1210[^baalbaki-2019|p. 202] — …"** SUPPORTED.
   - The introduction presents the book as a compilation of five earlier works: "فليعتدّ منْ ينْقل عَن كتابي هَذَا أَنه ينْقل عَن هَذِه الْأُصُول الْخَمْسَة" and "وَلم أبدل مِنْهُ شَيْئا" (vol. 1, p. 8).
   - Baalbaki 2019, printed p. 202 (checked in the PDF text), gives "Al-Azharī's (d. 370/981) Tahdhīb al-lugha" and "Ibn al-Athīr (d. 606/1210) in al-Nihāya". The citation and locator are accurate.
   - "Most" is the right hedge, because of the compiler's own additions (see the new claims below).
5. **The rest of that sentence, unchanged but now joined by a colon: "a single entry can move from poetry and hadith to the physicians' *buḥrān* … which al-Jawharī flags as post-classical (*muwallad*)".** SUPPORTED. The displayed *Ṣiḥāḥ* entry for bHr reads "والاطباء يسمون التغير الذى يحدث للعليل دفعة في الامراض الحادة بحرانا … وجميع ذلك مولد". The displayed *Lisān* bHr entry reproduces this, and Ibn Barrī's comment follows it: "قال ابن بري عند قول الجوهري: إنه مولد".

## New claims (from the reviser's evidence for "most")

I searched the displayed *Lisān* entries (tool `grep`/`entry`, vowel marks stripped) and read the context around each passage.

6. **vql.** SUPPORTED. The passage "وزنة المثقال هذا المتعامل به الآن: درهم واحد وثلاثة أسباع درهم …" sits inside a remark signed "قال محمد بن المكرم", which answers Ibn al-Athīr's note on *mithqāl*. It records the weight in use in the compiler's own day, and gives it relative to "رطل مصر".
7. **dwr.** SUPPORTED. The entry reads "قال محمد بن المكرم: وجدت هنا في بعض الأصول حاشية بخط سيدنا الشيخ … بهاء الدين محمد ابن الشيخ محيي الدين إبراهيم بن النحاس النحوي، فسح الله في أجله". The formula is one used for a living person, so the claim that the scholar was alive when Ibn Manẓūr wrote is a fair reading.
8. **Trq.** SUPPORTED, with one note. The entry reads "قال ابن المكرم: ما أعرف نجما يقال له كوكب الصبح ولا سمعت من يذكره في غير هذا الموضع". The reviser's translation in the revision log stops at "…anyone mention it" and leaves out "في غير هذا الموضع" ("except in this passage"). The remark is still Ibn Manẓūr's own testimony. The translation appears only in the working notes, not on the page, so the guide needs no change. If anyone quotes it later, restore the full phrase.
9. **Five named sources (intro vol. 1, pp. 7–8), cited alongside the changed sentence.** SUPPORTED. Page 7 names al-Azharī, Ibn Sīda, al-Jawharī and Ibn Barrī. Page 8 names Ibn al-Athīr's *Nihāya* ("أَبَا السعادات الْمُبَارك بن مُحَمَّد بن الْأَثِير الْجَزرِي قد جَاءَ فِي ذَلِك بالنهاية") and contains the disclaimer "وَلَيْسَ لي فِي هَذَا الْكتاب فَضِيلَة أمتُّ بهَا".

## Editorial note (suggestion, not a factual problem)

Because of the colon, the *buḥrān* clause now reads as support for "older than the book". That is true: al-Jawharī, d. c. 400/1010, already flags the usage. But the clause's real point is that one entry holds layers of evidence from different periods. Joining it with "and a single entry mixes layers: …" would state that point more directly. This is optional.

## Result

All 9 checked claims are supported. None was unsupported or needed qualification, and I made no changes to the guide. The validator passes.
