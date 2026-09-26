# Brief (from the site owner, 2026-09-26) — verbatim

Create a new section on our site that helps readers understand the classical dictionaries displayed on our root and word pages. An example word page is:
`http://localhost:4000/word/39:53/14`
Each classical dictionary should have a dedicated page explaining the work, its author, its historical setting, and—most importantly—how to read and use it.
Please carry this through from researching the dictionaries to creating the content and connecting the new pages to the existing site.

1. Begin with the dictionaries already on our site
Identify every classical dictionary currently available on the root and word pages. Check how each work is named and what text we actually display.
Distinguish between an original dictionary and any translation, abridgment, adaptation, or edited selection. Do not assume that the person associated with a displayed title is necessarily the original author.
Create one page per distinct work, avoiding duplicate pages for alternate names of the same dictionary. Choose clear, consistent routes that fit the site.

2. Write for a curious reader studying Qur'anic Arabic
The central question for every page is:
"What kind of guide is this dictionary, and how should I read it?"
Write an engaging essay, not an encyclopedia entry or a list of answers. Readers should leave knowing what makes this dictionary useful, how its author approaches language, and how to interpret the excerpts they encounter on our site.
Use plain English. Explain unfamiliar scholarly terms when they are necessary. Include Arabic where it helps, with an accessible translation or explanation.
Aim for roughly 700–1,100 words when reliable sources support that depth. Write substantially less when evidence is sparse. Never pad a page to meet a word count.
Keep biography relevant to the dictionary. Avoid generic praise, unsupported claims of importance, and long lists of publications or teachers that do not explain the work.

3. Address these questions where the evidence allows
Weave the relevant answers into a coherent essay. These are research questions, not mandatory headings.

The author and his purpose
* Who wrote the dictionary, and when and where did he work?
* Which aspects of his education, scholarly interests, or intellectual setting help explain the dictionary?
* What problem was he trying to solve?
* Who was the intended audience?
* What do we know about his purpose from his own introduction, and what comes from later scholarship?

The dictionary's approach
* How does the author understand the relationship between a root and its words?
* Does he seek a shared underlying meaning, collect distinct senses, explain difficult vocabulary, preserve earlier scholarship, or combine several approaches?
* How does he handle meanings that do not fit an apparent pattern?
* How is the work organized, and what should a reader know to understand an individual entry?
* What conventions or recurring expressions might otherwise confuse a modern reader?

Evidence and scholarly judgment
* What kinds of evidence does the dictionary use: Qur'anic passages, hadith, poetry, dialects, reported speech, or earlier lexicographers?
* How does the author weigh or question that evidence?
* Does he report competing explanations, choose between them, or leave them unresolved?
* When several scholars are quoted, how can readers distinguish their statements from the compiler's own judgment?

What makes the work distinctive
* What does this dictionary help a reader notice that another dictionary might not?
* Is its strength breadth, concision, semantic connections, fine distinctions, quotations, unusual vocabulary, or something else?
* Which earlier works does it draw on?
* Does it compile, shorten, correct, expand, or challenge those works?
* Which later dictionaries demonstrably used or responded to it?

Using it for Qur'anic study
* What can this dictionary clarify about a Qur'anic word?
* What cannot be settled by consulting it alone?
* How should readers distinguish a word's broader range of meanings from its meaning in a particular verse?
* What should readers understand about the date and provenance of the linguistic evidence it preserves?
* What limitations, disputed interpretations, or gaps matter in practice?

Do not force every dictionary into the same account of "original root meanings." Describe each work on its own terms.

4. Make the method tangible through actual root entries
For each dictionary, aim to include two or three verified root examples. Use fewer if the available evidence does not support more.
At least one example should receive a close reading that shows:
* The root and relevant Arabic words.
* The meanings discussed in the dictionary.
* The evidence or reasoning the author uses.
* What this example reveals about his method.
* Any uncertainty or competing explanation that matters.
Where useful and well supported, briefly compare how another dictionary treats the same root. Explain a meaningful difference in reasoning, evidence, or emphasis.
Choose examples that are actually available in that dictionary on our site wherever possible. Confirm that the displayed entry supports the essay's explanation. If the site shows only an abridgment or translation, do not suggest that users will find material there that has been omitted.
Never invent an example, quotation, etymology, or connection between meanings. Do not attribute your own explanation to the author.
An individual example illustrates a method; it does not automatically establish how the author treats every root.

5. Make every root reference lead to the relevant dictionary entry
Whenever a root is referenced in an essay, make it a clickable link to its root page.
For example, a root page may look like:
`http://localhost:4000/root/dxn`
The link must do more than open the root page. It should:
1. Open the correct root page.
2. Expand the specific dictionary being discussed.
3. Scroll to that dictionary's entry so the reader can immediately inspect the evidence.
Use the site's existing root identifiers and dictionary identities. Do not guess a root's URL from its Arabic spelling.
These links must work when clicked from a dictionary essay, opened in a new tab, or shared directly. They must also work on the deployed site, without depending on `localhost`.
If an example compares two dictionaries, provide a clear link to each dictionary's entry for that root.
If the dictionary entry is unavailable, do not silently send the reader to another dictionary. Prefer another verified example, or clearly explain the limitation.
Keep the experience comfortable on mobile and ensure that the destination entry is visible below any fixed page header.

6. Use a separate verification agent
Use a separate agent specifically to check factual accuracy and prevent hallucinated content. This agent must review every essay independently against the sources, rather than merely accepting the drafting agent's research notes.
The verifier should check:
* The work's identity and its relationship to any translation or abridgment.
* Author names, dates, places, and relevant biographical details.
* Claims about purpose, method, organization, and intended audience.
* Claims about influence, borrowing, and relationships between dictionaries.
* Every Arabic quotation, translation, root example, and comparison.
* Whether a statement belongs to the author or to someone he quotes.
* Whether the linked entry actually supports the explanation.
* Whether citations support the precise claims attached to them.
Pay particular attention to dictionaries and authors for whom information is sparse.
The verifier should classify substantive claims as supported, needing qualification, or unsupported. Revise or remove unsupported claims before considering a page complete. Recheck any new factual claims introduced during revision.
A plausible statement is not enough. Agreement between agents is not evidence.
If reliable sources are unavailable, publish a shorter, restrained account that explains what can be established. Do not infer a biography from the author's name, assume a methodology from the title, or manufacture scholarly consensus.

7. Research and cite responsibly
Prefer the dictionary itself, especially its introduction and actual entries, together with reliable scholarly editions, academic research, and reputable reference works.
Use general reference pages as starting points where helpful, but do not build the essays entirely from them.
For each essay:
* Provide unobtrusive citations close to the claims they support.
* Include a short list of sources with usable links where available.
* Give traceable references for root examples, identifying the root entry and the edition or version consulted.
* Distinguish direct quotation, translation, paraphrase, and interpretation.
* Label translations supplied for these essays.
* Acknowledge meaningful disagreement or uncertainty.
* Never fabricate a citation, page number, quotation, or source URL.
Do not treat the dictionary's composition date as the date of every usage it records. Do not present one scholar's semantic proposal as an established historical fact.
Keep detailed verification notes separate from the reader-facing essays so the pages remain enjoyable to read.

8. Integrate the pages into the site
Add a clearly discoverable way to learn about each dictionary from wherever it appears on root and word pages. Use a concise label such as "About this dictionary," placed naturally alongside the dictionary's name.
Create a simple overview page introducing the available classical dictionaries and linking to their essays. Give each work a short description that communicates its particular usefulness without making unsupported rankings.
Each dictionary page should include:
* The dictionary's recognizable title and Arabic title where verified.
* The author's name.
* A concise historical date or period, using approximate dates when appropriate.
* A brief opening that communicates what is distinctive about the work.
* The essay, with a few useful headings if needed.
* Clickable root examples with the expansion and scrolling behavior described above.
* Sources and relevant notes about the version displayed on our site.
Match the existing site's visual style and make Arabic and English text comfortable to read together.

9. Check the finished experience
Before finishing, verify that:
* Every classical dictionary currently shown on the site is accounted for.
* Its "About" links reach the correct page from root and word pages.
* Every referenced root leads to the correct root page.
* Each example link expands and scrolls to the intended dictionary.
* Direct links and new-tab navigation work.
* Comparisons link to the correct entries in both dictionaries.
* Pages read well on desktop and mobile.
* The independent factual review is complete and its findings have been addressed.
At the end, give me a concise report listing the pages created, the navigation added, the checks performed, and any remaining evidence gaps. Clearly identify any work whose account was intentionally kept short because reliable information was limited.
Use your judgment for routine editorial and design decisions. Prioritize accuracy, useful examples, and a smooth reading experience.
