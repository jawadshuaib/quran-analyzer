# Lisān al-ʿArab — revision after verification round 1

Reviser: revision agent, 2026-09-26. Input: `verification-r1.md` (68 supported, 3 needs qualification, 0 unsupported; 7 suggestions).
File edited: `roots/frontend/src/content/dictionary-guides/guides/lisan-al-arab.ts` (nothing else in the repo touched).

Validator after revision: `node scripts/validate-dictionary-guides.mjs lisan-al-arab` → **ok, 1/1 pass, 0 errors**. Lede + body 1,080 words (was 1,101). onOurSite 141 words (was ≈190). 11 root links (9 pairs), 3 excerpts, all unchanged. The only warnings are the two deliberate `none` links (slm, Slw) in onOurSite, which the sentence explains.

## Flagged claims

### C30 (needs qualification): Baalbaki and the "second-hand" scholars

- **Before:** "And the many older scholars named reach him second-hand — 'obviously on the authority of his five sources', as Ramzi Baalbaki puts it."
- **After:** "By his own account he kept within his five books,[^lisan-ds|vol. 1, p. 7] and the works the *Lisān* cites come, Ramzi Baalbaki notes, 'obviously on the authority of his five sources'.[^baalbaki-2019|p. 203 n. 84] Occasionally, though, he steps outside them and says so, as with al-Suhaylī below."
- **Evidence I opened myself:**
  - Baalbaki, *JAS* 6 (2019), AUB PDF, page headed 203 (PDF p. 19), n. 84: "Note also that among the works cited by Ibn Manẓūr — obviously on the authority of his five sources — are several works on gharīb al-Ḥadīth, only one on gharīb al-Qurʾān, and one which combines both types". The phrase describes the *works cited*, so the guide now applies it to works, not to every scholar named.
  - Ibn Manẓūr's introduction, Dār Ṣādir vol. 1 p. 7 (Shamela 1687/7, page label "ج1 - ص7"): "ولم أخرج فيه عما في هذه الأصول، ورتبته ترتيب [الصحاح] في الأبواب والفصول" ("I did not go beyond what is in these sources, and I arranged it as the Ṣiḥāḥ is arranged"). This is the source for "by his own account he kept within his five books".
  - For the exception: the displayed bHr entry (id 2760) has the signed remark "شرطي في هذا الكتاب أن أذكر ما قاله مصنفو الكتب الخمسة … لكن هذه نكتة لم يسعني إهمالها" and the closing "هذا آخر ما رأيته منقولا عن السهيلي". The guide already quotes the first and paraphrases the second.
- **Why this wording:** "Occasionally … and says so" reports what the displayed entries show. The verifier's cases (al-Suhaylī in bHr; Ibn Khallikān in brd; marginal notes in dwr and sll, all opened with "قال محمد بن المكرم") are signed. The sentence does not claim that every departure is signed.

### C36 (needs qualification): the signature count

- **Before:** "His own voice is rare and signed: 'Muḥammad ibn al-Mukarram said', a label found in 21 of the 1,452 entries on our site."
- **After:** "His own signature, 'Muḥammad ibn al-Mukarram said' or a variant, appears in just 24 of the 1,452 entries on our site."
- **Evidence:** `python3 _dict_guide_tool.py grep ibn-manzur-lisan-al-arab 'المكرم'` returned 33 matches. Dropping the false hits (المكرم = "the honoured", in Ebd, qrb, Hbb, krm, Avr, Ewn, Dyf, wfd, dss) leaves 24 signed entries: nfs, $rk, Amm ("محمد ابن المكرم"), jzy, Hmd, dwr, bHr ("عبدا محمد بن المكرم"), vql, Emr, $kk, fqr ("عبد الله محمد بن المكرم"), jld, Trq ("ابن المكرم"), jdd, nqD, fyA ("عبدالله بن المكرم"), brd, gwr, sll, bhm, wqb, njd, gwl, Smt. A second grep for "بن مكرم|ابن منظور|قال المؤلف|قال مصنفه" found no further self-signatures. Its only two hits, $hb and Smt, are editors' notes quoting "شارح القاموس" and "الشارح". The new wording counts signatures only; it no longer implies that all of his interventions are signed or that they are rare.

### C66 (needs qualification): durar locator

- **Before:** "…vol. 1, pp. 4–5." **After:** "…vol. 1, p. 4."
- **Evidence:** Shamela 1687/4 (page label "ج1 - ص4") holds Ibn Ḥajar's *Durar* notice in full. It includes "ولد سنة ٦٣٠ في المحرم", al-Ṣafadī's "لا أعرف في الأدب وغيره كتابا مطولا إلا وقد اختصره", "جمع فيه بين التهذيب والمحكم والصحاح والجمهرة والنهاية وحاشية الصحاح" and "وخدم في ديوان الإنشاء طول عمره وولي قضاء طرابلس", and ends "مات في شعبان سنة ٧١١". Al-Suyūṭī's *Bughya* notice follows and ends "مات في شعبان سنة ٧١١." on the same page. Shamela 1687/5 (label "ج1 - ص5") opens "مقدمة الطبعة الأولى", the first-edition preface.

## Brief suggestions (all taken)

1. **Length** (lede + body 1,101 → 1,080 words). Cuts: the header dates repeated in the first body sentence; the "two kinds of lexicographers" sentence compressed; "in his image"; the rhyme-order sentence shortened. The Haywood line moved out of the baḥīra paragraph and merged into the "Three readings" paragraph, where it replaces "The *Lisān* does not choose. It hands you the range". It is kept because it is the only scholarly statement that his habit of leaving disagreements unresolved is general, not just a feature of one entry. Also cut: the SlH parenthesis no longer repeats "the words are Ibn Sīda's", the previous sentence says so, and a few words in the hadith and Suhaylī paragraphs. No facts removed except the duplicated dates. The additions for C30, C33 and the Ḥ-M-D clause were absorbed.
2. **onOurSite** (≈190 → 141 words). Merged the footnote sentences. "flag doubtful readings, give variants or name a verse's poet" became "editors' notes on readings and variants". The typing-slip and entry-length sentences are joined. "for example" and "only" are dropped. No claim added.
3. **SlH wording (C33).** "only the *Tahdhīb* and Ibn Barrī are named" became "of his five sources, only the *Tahdhīb* and Ibn Barrī are named". Re-checked in the stored entry 696: التهذيب ×1 and ابن بري ×2; الجوهري, ابن سيده, المحكم, الصحاح, ابن الأثير and النهاية ×0.
4. **"Whose words are these?" first paragraph.** The four-label run became three sentences. Al-Azharī appears by name, by-name or book; Ibn Sīda, al-Jawharī and Ibn Barrī are flagged the same way; hadith is sometimes under Ibn al-Athīr's name, often *wa-fī l-ḥadīth*. The support is the same as before (C26–C28).
5. **Ḥ-M-D contradiction made explicit.** Added: "Here the introduction's promise to change nothing openly gives way — to a theological scruple, not a lexical one, since the meaning, he says, is the same." Support: introduction vol. 1 p. 8, "لأنني نقلت من كل أصل مضمونه، ولم أبدل منه شيئا" (research-notes §2; the verifier confirmed C22), together with the Hmd entry (id 61), "فعدلت عنها وقلت حميد بمعنى محمود، وإن كان المعنى واحدا".
6. **lisan-ds citation.** "whose corrector's notes it keeps" became "with the Būlāq corrector's notes and later annotations (credited in the Shamela catalogue to al-Yāzijī and a group of lexicographers)". See New claims.
7. **Haywood URL.** Switched to https://archive.org/details/in.gov.ignca.12555. The archive.org metadata API returns title "Arabic lexicography", creator "Haywood, John A.", date 1960, with no access restriction, and `12555_djvu.txt` downloads openly. In that text I found "Ibn Manzur retained al-Jauhari's arrangement as being the handiest" (p. 80), "Tripoli for some time" (pp. 77–78), "where two of them disagree, he tends merely to repeat what both have said" (p. 81), al-Jawharī's roots arranged "according to their final radicals in the first instance" (p. 71), and the Būlāq-edition footnote (p. 81). The OCR is poor, but the passages are legible.

## Removed claims

- "His own voice is rare and signed" (the implied claim that his interventions are always signed and rare), replaced by a count of signatures.
- "the many older scholars named reach him second-hand" (a claim about every scholar named), replaced by his own statement plus Baalbaki's remark about works cited, with the exception noted.
- The count "21" (superseded by 24).
- The second locator page (p. 5) of the *durar* source.
- Duplicated header dates in the first body sentence (not a claim removal, only a repetition).

## New claims (each with its evidence)

1. **"By his own account he kept within his five books"** — *Lisān* intro, Dār Ṣādir vol. 1 p. 7 (Shamela 1687/7): "ولم أخرج فيه عما في هذه الأصول". The sentence was opened by me. The quote is from the text.
2. **"Occasionally, though, he steps outside them and says so, as with al-Suhaylī below"** — bHr entry 2760 (displayed): signed "شرطي في هذا الكتاب أن أذكر ما قاله مصنفو الكتب الخمسة … لكن هذه نكتة لم يسعني إهمالها", followed by the al-Suhaylī passage and "هذا آخر ما رأيته منقولا عن السهيلي". Further signed departures: brd (Ibn Khallikān), dwr and sll (marginal notes, "حاشية … في بعض الأصول"), found by my grep.
3. **"appears in just 24 of the 1,452 entries on our site"** — `_dict_guide_tool.py grep` as listed under C36 above.
4. **"Here the introduction's promise to change nothing openly gives way"** — intro vol. 1 p. 8, "ولم أبدل منه شيئا"; Hmd entry 61.
5. **lisan-ds: "with the Būlāq corrector's notes and later annotations (credited in the Shamela catalogue to al-Yāzijī and a group of lexicographers)"** — Shamela card for book 1687: "الحواشي: لليازجي وجماعة من اللغويين". Publisher's preface, vol. 1 p. 3 (Shamela 1687/3): "ورأينا أن نثبت تحقيقات مصحح الطبعة الأولى الواردة في الهوامش بنصها", and the same preface says the edition was corrected "مستعينين بنخبة من علماء اللغة المتخصصين". The credit to al-Yāzijī is attributed to the catalogue, not asserted independently.

## Disputed

None. All three qualifications were accepted as the verifier framed them. For C30 I used a slightly narrower wording than the verifier's proposal: Baalbaki's phrase is tied to "the works the *Lisān* cites", and the "kept within his five books" part rests on Ibn Manẓūr's own statement, not on Baalbaki.

## Checks not re-run

- Displayed entries byn, Hmd, bHr, DyE and the counts 831 and 1,452 are unchanged in the text and were confirmed by the verifier. I re-checked only SlH (labels) and the signature grep.
