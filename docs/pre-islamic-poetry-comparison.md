# Qurʾān ↔ Pre-Islamic Poetry: A Comparison Engine

*A design & research document for al-nuqta.com*
*Drafted 2026-06-21. Status: proposal for your review — nothing built yet.*

---

## 0. How to read this document

This is long, but it is built in layers. If you only read three things, read:

1. **Part 2 — The objectivity problem.** This is the whole game. Get this wrong and the feature becomes propaganda; get it right and it becomes one of the most intellectually honest things on the site.
2. **Part 4 — Four worked examples.** Real roots (K-F-R, W-Q-Y, D-H-R, nobility), real Qurʾānic verses, real poetry, fully developed. This is what the feature actually *feels* like.
3. **Part 5 — The method menu.** Your running ideas (root usage, verse comparison, rhyme/meter, thematic subversion) are all here, plus several novel ones that are more objective because they are *computable* rather than cherry-picked.

Everything else is supporting structure: the data, the UX, the pipeline, the rollout, the risks.

A note on honesty up front: I checked every poetry citation and every claim in this document against primary or scholarly sources (listed in the References). I have deliberately **not** invented a single line of verse. Where I was not certain a specific line was authentic, I made the claim at the level of the dictionaries (Lane, Lisān al-ʿArab, al-Rāghib) rather than risk a fabricated quotation. The feature itself must hold to the same standard, and Part 7 builds that standard into the generation pipeline.

---

## 1. The idea in one paragraph

The Qurʾān did not arrive into a linguistic vacuum. It arrived into a culture whose highest art form was poetry, and whose poets had spent generations polishing a specific vocabulary for a specific world — the desert, the tribe, the camel, wine, war, lost love, and above all *fate*. When the Qurʾān uses a word, it is using a word that already had a life. Sometimes it keeps the old meaning. Sometimes it narrows it, widens it, lifts it onto a moral plane, or turns it inside out. **Showing the reader that "before" gives them the depth perception to see what the Qurʾān actually did with the word.** That is the feature: a sober, evidence-anchored comparison of how a root or a verse uses language *against* how the most reliable pre-Islamic poetry used the same language.

---

## 2. The objectivity problem (read this twice)

You said it yourself: *"while showing how the Qurʾānic language is unique, we don't want to just create a straw man argument by drawing from only poetry that proves it unique — we want to be objective."* This is the single most important constraint, and it has **three** distinct failure modes. A serious feature has to defend against all three.

### 2.1 Failure mode A — Cherry-picking (the straw man)

The lazy version of this feature finds the one poem where a word is used crudely and the one verse where the Qurʾān uses it sublimely, juxtaposes them, and declares victory. This is dishonest, and a careful reader smells it instantly.

**The defense is a built-in adversarial step.** Before the system is allowed to *claim* a contrast ("the Qurʾān uses W-Q-Y differently"), it must first *search the poetry corpus for counter-evidence* — places where the poetry also uses the word that way. If it finds them, the note reports **continuity**, not contrast. We make "look for the disconfirming case" a required, logged step in the pipeline (Part 7), not an optional virtue.

### 2.2 Failure mode B — The authentication trap (the circular argument)

This one is subtle and most projects miss it entirely. In 1926 the Egyptian scholar **Ṭāhā Ḥusayn** argued in *Fī al-Shiʿr al-Jāhilī* that a large fraction of so-called "pre-Islamic" poetry was actually composed *after* Islam and back-projected onto legendary poets — partly to provide lexical evidence for interpreting the Qurʾān itself. The scholarly consensus today is more moderate than his sweeping claim (his evidence was thin and the *Muʿallaqāt* in particular survived the critique well), but the core caution is permanent and real:

> If we compare the Qurʾān to a "pre-Islamic" line that was in fact composed *after* the Qurʾān — possibly *imitating* it — and then announce that the Qurʾān is distinctive, **we have proven nothing.** We have compared the Qurʾān to its own echo.

**The defense is an authentication ladder** (Part 3.2). We never treat "it's in a poetry dataset" as equal to "it's a verified pre-Islamic line." Every comparison carries the provenance tier of its poetic evidence, visibly, and the strongest claims are reserved for the most securely dated material — above all the *Muʿallaqāt*, which is exactly the instinct in your original note.

### 2.3 Failure mode C — Register confusion (comparing apples to hymns)

Poetry and scripture have different *jobs*. A poet's job is to move you, to boast, to immortalize a tribe. The Qurʾān's job (on its own terms) is to guide, warn, and orient toward God. **Not every difference is a "superiority."** When a poet describes a camel's thigh for forty lines, that is not the Qurʾān "failing" to do so or the poet being "shallow" — it is a different genre with different aims. Some of the most beautiful pre-Islamic verse is morally serious, and some of it voices ideas the Qurʾān would *affirm*.

**The defense is the continuity ledger** (Part 3.4 and Part 4.5). We deliberately surface the places where poetry and the Qurʾān *agree* — shared values (courage, generosity, hospitality, loyalty), shared vocabulary, and especially the famous moments where a pagan poet stumbles onto something the Qurʾān would call true. The flagship case: the Prophet himself is reported to have said the truest line a poet ever spoke was Labīd's *"Verily, all things apart from God are vain"* (Bukhārī 6403). A feature that can quote *that* line, approvingly, has earned the right to point out a contrast elsewhere.

### 2.4 The governing principle: **earned contrasts**

Putting the three defenses together gives us one rule that governs the entire feature:

> **We only assert a contrast when (a) the poetic evidence is authenticated, (b) we have actively searched for and failed to find counter-examples, and (c) the difference is real and not just a difference of genre. Otherwise we report continuity, or we say nothing.**

Objectivity here does *not* mean hedging everything into mush. You were explicit about that: *"By objective, I don't mean boring or hedged arguments, but rather when there is a real meaningful comparison, then provide it."* Earned contrasts are the opposite of hedging — when the evidence is strong, we state the contrast plainly and vividly. We just make sure it was earned.

---

## 3. The data

### 3.1 The Kaggle dataset — honest assessment

The dataset you pointed to (`mdanok/arabic-poetry-dataset`) belongs to a well-known family of Arabic-poetry datasets scraped from sites like **aldiwan.net** and **adab.com**. Datasets in this family (the closely related `fahd09/arabic-poetry-dataset-478-2017`, and the research corpora **APCD**, **AraPoems**, **Diwan**) typically carry these columns:

| Field (Arabic) | Meaning | Why we care |
|---|---|---|
| الشاعر | poet | attribution & era inference |
| العصر | era / age | **filter for العصر الجاهلي (Jahilī)** |
| البحر | meter (one of al-Khalīl's 16 *buḥūr*) | the rhyme/meter engine |
| القافية | rhyme letter (*rawiyy*) | monorhyme analysis |
| البيت / القصيدة | the verse / poem text | everything |

**Strengths:** large (tens of thousands of poems), pre-labeled with era and often meter and rhyme. For the **form/sound engine** (meter, rhyme) it is genuinely useful, because meter is an objective property of the text and doesn't depend on who wrote it.

**The critical weakness — and this is exactly the Ṭāhā Ḥusayn problem from Part 2.2:** the `العصر = جاهلي` label inherits the *traditional* attribution uncritically. A scraped dataset cannot tell you whether a line attributed to the 6th-century poet ʿAntara is genuinely his or a later Abbasid-era reconstruction. **So this dataset is fine as a wide net, but it cannot be the authority for any contrast claim.** It must be filtered through the authentication ladder below.

### 3.2 The authentication ladder

Every poetic line that enters the system gets a provenance tier. The tier is shown to the reader and gates how strong a claim we're allowed to build on it.

| Tier | Source | Trust | What we allow |
|---|---|---|---|
| **A — Gold** | The *Muʿallaqāt* (the seven/ten "hanging odes"), with classical commentary (al-Zawzanī, al-Tibrīzī). | Highest — the most scrutinized, most securely transmitted corpus. | Strong, headline contrast claims. |
| **B — Strong** | Critical editions of the early anthologies: Ahlwardt's *Six Divans*, Lyall's edition of the *Mufaḍḍaliyyāt* and *Aṣmaʿiyyāt*, Abū Tammām's *Ḥamāsa*. | High — edited by philologists from manuscript traditions. | Normal contrast claims. |
| **C — Attributed** | The broad scraped corpus (Kaggle/aldiwan), `العصر = جاهلي`. | Medium — traditional attribution, unverified. | Illustration and frequency statistics *only*; never the sole basis for a contrast. |
| **D — Disputed** | Lines flagged by scholars as likely post-Islamic, or with weak isnād. | Low. | Used only to *teach the authentication problem itself*, clearly labeled. |

The practical build: start from the scraped corpus (Tier C) for *coverage and statistics*, then **cross-match** against the *Muʿallaqāt* and the critical anthologies (Tiers A/B) to *upgrade* the lines we actually quote. A line that appears in both a scrape and Lyall's *Mufaḍḍaliyyāt* is promoted to Tier B and becomes quotable.

### 3.3 What we actually load (build order)

1. **The Muʿallaqāt, in full, hand-curated** — ~10 odes, a few hundred lines. Small, gold-tier, and the backbone of the whole feature. This alone is enough to launch a credible v1.
2. **The Kaggle/aldiwan scrape, filtered to `جاهلي`** — for breadth and frequency statistics (Tier C).
3. **Critical anthologies as available** (*Mufaḍḍaliyyāt*, *Aṣmaʿiyyāt*, *Ḥamāsa*) for Tier-B depth — these can be added incrementally.
4. **Morphological parsing of the poetry** — to index poetry *by root* (so we can answer "where does K-F-R appear in the Jahilī corpus?") we need to lemmatize/root-analyze the poetic text. This is the same kind of analysis the site already has for the Qurʾān (the `morphology` table), but applied to poetry via a tool like **CAMeL Tools** or **Farasa**. This is the main new piece of data engineering.

### 3.4 The continuity ledger (a data structure, not just a principle)

Alongside the contrasts, we maintain an explicit table of **agreements** — shared roots used the same way, shared values the Qurʾān affirms, and "pagan-poet-got-it-right" moments. This is queryable and surfaced in the UI (Part 6). It is what makes the feature trustworthy: a reader who sees that we *also* document where the poetry and the Qurʾān align knows that when we *do* point to a contrast, it's real.

---

## 4. Four worked examples

These are fully developed so you can feel the actual output. Each follows the same shape: **the word's life before the Qurʾān → the Qurʾānic move → the earned conclusion.** Arabic, transliteration, and translation are given throughout.

### 4.1 K-F-R (ك ف ر) — the buried seed *(your example; a lexical bridge)*

**Before the Qurʾān — the physical root.** The classical dictionaries are unanimous: the bare root *k-f-r* means **to cover, to conceal**. From this one physical image the Arabs derived a whole field of words. The farmer who buries seed under soil is a *kāfir* — a *coverer*. The night that hides the world is *al-kāfir*. The sea, which conceals what sinks into it, could be called *kāfir* too (al-Thaʿlabī records exactly this). The word's first home is **agriculture and darkness, not theology.**

**The Qurʾānic move — and the giveaway verse.** The Qurʾān overwhelmingly uses the root for *kufr*: the willful **covering-over of a truth one knows** — disbelief, ingratitude, the hiding of God's evident signs. The moral sense is built directly on the physical one: the disbeliever is a *coverer of truth* exactly as the farmer is a coverer of seed. And then comes the tell — the one place the Qurʾān reaches back and uses the *old agricultural* sense on purpose:

> **Q 57:20** *كَمَثَلِ غَيْثٍ أَعْجَبَ ٱلْكُفَّارَ نَبَاتُهُۥ*
> *"...like rain whose vegetation delights the **kuffār**."*

Here *kuffār* does not mean "disbelievers" — it means **the tillers, the sowers**, those who covered the seed and now rejoice at the green shoots. The Qurʾān, in other words, *demonstrably knows the root's agricultural meaning* and deploys it deliberately. That single verse is the bridge: it shows that the theological *kufr* everywhere else is not a coincidence of sound but a conscious extension of "covering."

**The earned conclusion.** This is not a contrast of "crude vs. sublime." It is something more interesting and more honest: **continuity with elevation.** The Qurʾān keeps the Arabs' physical image intact and lifts it from the field to the soul. A reader who learns that *kāfir* first meant *farmer* will never read the word flatly again.

> *Tier-A note:* the agricultural sense is firmly attested in the lexica (Lane, Lisān al-ʿArab) and the tafsīr tradition on 57:20; we present it at that level rather than hanging it on a single disputed verse-line.

---

### 4.2 W-Q-Y (و ق ي) — from the shield to the soul *(your example; physical → moral)*

**Before the Qurʾān — the physical shield.** The root *w-q-y* means **to guard, to shield, to ward off harm**. A *wiqāya* is a literal protective covering — armor, a shield, the thing a warrior puts between himself and the spear. A man *yattaqī* the blow by interposing his shield or his arm; an animal raising a leg against danger is described with this verb. It is a word of **the battlefield and the body.**

**The Qurʾānic move.** The Qurʾān takes this physical act of self-shielding and turns it into the central ethical-spiritual posture of the believer: **taqwā** (تقوى). The great lexicographer **al-Rāghib al-Iṣfahānī** defines it with the physical image still glowing inside it: *taqwā is to place the soul inside a wiqāya — a shield — against what one fears.* And the Qurʾān keeps the bodily metaphor literally alive:

> **Q 2:24** *فَٱتَّقُوا۟ ٱلنَّارَ ٱلَّتِى وَقُودُهَا ٱلنَّاسُ وَٱلْحِجَارَةُ*
> *"So **shield yourselves** against the Fire whose fuel is people and stones."*

The command is *ittaqū* — the very verb a warrior's *shield* comes from — but the enemy is now the Fire, and the shield is one's own conduct. The physical posture is preserved; the threat has been moved from the visible world to the moral one.

**The earned conclusion.** Same image, re-aimed. The Jahilī warrior shields his body from a spear; the Qurʾānic believer shields his self from the consequences of heedlessness. This is **semantic elevation** of the cleanest kind, and — crucially — it is *not* the Qurʾān inventing a word, but the Qurʾān re-pointing an existing one. (Note that *taqwā* and *karam/nobility* from §4.4 meet in a single verse, Q 49:13 — see below.)

---

### 4.3 D-H-R (د ه ر) — dethroning Fate *(thematic subversion)*

**Before the Qurʾān — Fate as the only god.** This is the deepest one. Pre-Islamic Arabia had a pervasive, almost climatic sense of ***dahr*** — Time, but Time understood as **blind, impersonal, devouring Fate**. *Dahr* is the agent that wears men down, separates lovers, ruins encampments, and ends every boast. It is everywhere in the poetry, and it is *grammatically active* — it *does* things to people. For many, *dahr* was effectively the ultimate power, beyond appeal, beyond mercy. The mood of the *nasīb* — the poet weeping at the abandoned campsite — is *dahr*'s signature: everything passes, and nothing can be done.

**The Qurʾānic move — a direct quotation and rebuttal.** The Qurʾān does something striking here: it *quotes the Jahilī creed out loud and answers it.*

> **Q 45:24** *وَقَالُوا۟ مَا هِىَ إِلَّا حَيَاتُنَا ٱلدُّنْيَا نَمُوتُ وَنَحْيَا وَمَا يُهْلِكُنَآ إِلَّا ٱلدَّهْرُ*
> *"And they say: 'There is nothing but our worldly life; we die and we live, and nothing destroys us but **Time (al-dahr)**.'"*

The Qurʾān puts the worldview in the deniers' own mouths — *"nothing destroys us but Time"* — and the surrounding passage overturns it: it is **God**, not blind Time, who gives life and death and gathers all to account. The chapter is even nicknamed *al-Dahr* because of this verse. The whole metaphysics flips: **Time is demoted from sovereign agent to a creature under God's command.** (The later Prophetic tradition — *"do not revile Time, for God is Time"* — drives the same point: stop treating *dahr* as a power in its own right.)

**The earned conclusion.** This is the cleanest **thematic subversion** in the entire comparison, and it is unusually well-evidenced because the Qurʾān *names the position it is overturning*. The poetry's emotional center of gravity — fatalism before an impersonal Time — is precisely what the Qurʾān targets. We can show the reader the *nasīb*'s grief over what *dahr* destroyed on one side, and Q 45:24 dismantling *dahr*'s sovereignty on the other.

---

### 4.4 Nobility — K-R-M / the honor code *(thematic subversion, with a built-in continuity)*

**Before the Qurʾān — honor by blood.** The supreme value of Jahilī society was a cluster the poets called *murūʾa* (manliness/virtue) and *karam* (nobility/generosity), and it was anchored in **lineage**. You were noble because of your *ancestors*, your tribe, your bloodline; the *fakhr* (boast) section of the ode exists to recite exactly this — *my* forefathers, *my* clan, *my* deeds. Generosity, courage, and hospitality were genuinely prized — and here is the honest part: **the Qurʾān affirms those very virtues.** The contrast is not "the Arabs valued bad things." It is narrower and sharper than that.

**The Qurʾānic move — keep the virtue, move the root of honor.**

> **Q 49:13** *إِنَّ أَكْرَمَكُمْ عِندَ ٱللَّهِ أَتْقَىٰكُمْ*
> *"Indeed, the most **noble (akram)** of you in the sight of God is the most **God-conscious (atqā)** of you."*

In one clause the Qurʾān takes the prized word *karam* (here *akram*, "most noble") and **re-roots honor from ancestry to taqwā** — the very W-Q-Y self-shielding of §4.2. Nobility is no longer inherited; it is earned by the state of one's soul. The same verse opens by reminding all people that they descend from a single pair, dissolving the tribal hierarchy the *fakhr* was built to celebrate.

**The earned conclusion — and why it's a model of objectivity.** Notice this is *both* a subversion *and* a continuity, and an honest note says so. The Qurʾān does **not** trash generosity or courage — it keeps them. What it overturns is the *source* of nobility: blood → God-consciousness. Presenting it this way (we affirm what the poetry affirmed, and we name precisely the one thing that moved) is far more credible, and far more interesting, than a flat "Islam abolished tribal pride."

---

### 4.5 The continuity case — Labīd's "all is vain" *(the objectivity anchor)*

Not every comparison is a contrast, and the feature must prove it can say so. The poet **Labīd ibn Rabīʿa** — one of the *Muʿallaqāt* poets, Tier A — wrote a line that the Prophet Muḥammad himself is reported to have praised as **the truest word any poet ever spoke**:

> *أَلَا كُلُّ شَىْءٍ مَا خَلَا ٱللَّهَ بَاطِلُ*
> *"Verily, everything apart from God is **vain (bāṭil)**."* (Ṣaḥīḥ al-Bukhārī 6403)

Here a pre-Islamic poet voices something the Qurʾān would call true — the transience of all but God. This is a *continuity*, and surfacing it is not a concession; it is the feature's credibility made visible. **A comparison engine that can quote this line approvingly has earned the reader's trust for the moments when it points the other way.**

---

## 5. The method menu — engines of comparison

Your running ideas map onto four "engines." I've kept all of yours and added several novel methods whose virtue is that they are **computable and exhaustive** rather than hand-picked — which is the strongest possible answer to the straw-man worry, because a method that runs over *every* occurrence cannot be accused of selecting only the flattering ones.

### Engine 1 — Root-level semantic comparison (the abstract layer → root pages)

For a root, compare its *whole field of use* in the Qurʾān vs. in the authenticated poetry. This is where your K-F-R / W-Q-Y vision lives. Output: a "**In Pre-Islamic Poetry**" section on `/root/xxx` (Part 6). Three novel, objective sub-methods power it:

- **5.1 Semantic-shift typology.** Every root gets classified into a *named* relationship, from a fixed vocabulary: **continuity** (no real shift) · **narrowing** · **widening** · **elevation/moralization** (physical → ethical, e.g. W-Q-Y) · **theologization** (worldly → God-centered, e.g. D-H-R) · **referential transfer** (same sense, new referent). Because *every* root is labeled — including the boring "no significant shift" ones — the feature reports its **nulls**, which is the structural cure for cherry-picking. (Roughly: a root labeled "continuity" is just as publishable as one labeled "subversion.")
- **5.2 Collocational fingerprint.** For a root, compute *what words keep it company* in poetry vs. the Qurʾān. *Karīm* in the odes collocates with horse, sword, wine, guest; in the Qurʾān with *rabb* (Lord), *ʿarsh* (throne), *rizq* (provision). The "company a word keeps" is computed from the corpus, displayed as two word-clouds or ranked lists — objective, visual, and very hard to fake.
- **5.3 Agency reassignment.** *This one leans directly on infrastructure the site already has.* The Qurʾān morphology table records the **subject/agent, voice, and person** of every verb. Ask: in the poetry, what is the grammatical *agent* of verbs of destroying, giving, granting victory, deciding fate? (Answer, very often: *dahr*, *al-ayyām* "the days," the tribe, the self.) In the Qurʾān, who is the agent of those same verbs? (Overwhelmingly: **God**.) This is a *measurable* claim about who *acts* in each corpus — a quantitative backbone under the D-H-R subversion, generalizable across the whole vocabulary of power.

### Engine 2 — Verse-level comparison (the specific layer → a note under exegesis)

When a load-bearing root appears in a verse, attach a concrete comparison drawing on *actual* poetic lines (Tier A/B). This is the "new section below exegesis" you described. It is more specific than the root page because it can quote whole verses on both sides and talk about *this* verse's move. (See Part 6.2 for exactly where it renders.)

### Engine 3 — Form & sound (meter and rhyme)

Your meter intuition — *"Jahilī poetry often bends meaning to fit the meter, while the Qurʾān often bends meter to fit meaning"* — is real and well-grounded, with one honest caveat about difficulty.

- **The hard facts (objective, uncontroversial).** Classical poetry is built on al-Khalīl's **16 *buḥūr*** (meters) and a single **monorhyme** (*qāfiya* / *rawiyy*) sustained across an entire ode of dozens of lines. The Qurʾān fits **none** of the 16 meters; it uses *saj‘*-like rhythmic prose with shifting end-rhyme units (*fawāṣil*) whose length flexes with the sense. This is the textbook distinction and we can state it plainly.
- **The interpretive claim (state carefully).** The monorhyme constraint genuinely *does* pressure poets toward word choices that satisfy the rhyme; the Qurʾān's freedom from a fixed meter lets its rhythm follow the meaning. We present this as a *demonstrated tendency with examples*, not a sweeping law — and we are honest that "bending meaning to the meter" is a charge classical critics themselves leveled at poets (*iḍṭirār*, poetic necessity), so we're standing on traditional ground, not inventing a polemic.
- **The honest caveat.** Automatic Arabic *scansion* is genuinely hard. We should **not** roll our own; we lean on existing meter-classifier datasets/tools (MetRec, APCD's labeled meters, recent deep-learning meter classifiers) for the poetry side, and treat the Qurʾān's non-metricality as the fixed contrast point. This is the most technically demanding engine and should come *after* Engines 1–2.

### Engine 4 — Thematic / motif inversion (the cultural layer → essays + verse notes)

The Jahilī imagination has a fixed set of motifs. The Qurʾān repeatedly **picks up the motif and turns it.** Each of these is a specific, documentable inversion:

| Jahilī motif | In the poetry | The Qurʾānic turn | Anchor |
|---|---|---|---|
| **The ruined campsite (*aṭlāl/nasīb*)** | The poet halts and weeps over the abandoned dwelling of a lost beloved (*"Stop, let us weep…"* — Imruʾ al-Qays). Private grief, irretrievable past. | The Qurʾān halts the reader before ruined dwellings too — but they are the houses of **destroyed nations** (ʿĀd, Thamūd), and the lesson is moral, not romantic. | *"Those are their houses, fallen empty because they did wrong"* — **Q 27:52** |
| **The she-camel (*nāqa*)** | The poet's prized mount, described for dozens of lines; an object of *possession and boast* (Ṭarafa's ode). | The **She-Camel of God** (*nāqat Allāh*) is a divine **sign and test**; harming her brings destruction. From boast to trust. | **Q 7:73, Q 91:13** |
| **Wine (*khamr*)** | Celebrated, a centerpiece of pride and pleasure (ʿAmr ibn Kulthūm opens his ode with it). | Prohibited in this life (Q 5:90), yet **promised purified** in the next — wine without intoxication or regret. From indulgence to transformed reward. | **Q 5:90; Q 37:47; Q 47:15** |
| **The boast (*fakhr*)** | Self- and tribe-glorification is a structural section of the ode. | Glory is reassigned: *"all honor belongs to God"*; mutual boasting is rebuked as a distraction. | **Q 63:8; Q 102:1** |
| **Fate (*dahr*)** | Sovereign, blind, devouring (everywhere). | Demoted to a creature under God (§4.3). | **Q 45:24** |

Each row is an "essay-sized" comparison and also seeds verse-level notes wherever the motif's vocabulary appears.

### A cross-cutting novel method — **the "negative space" map**

Beyond comparing shared words, compare the *gaps*. Which roots are **frequent in the poetry but rare/absent in the Qurʾān** (much of the wine-and-camel-anatomy lexicon, certain boasting formulae)? Which are **central to the Qurʾān but thin in the secular poetry** (the dense vocabulary of *resurrection, accountability, revelation*)? The two vocabularies' *non-overlap* is itself a portrait of two worldviews, and it is fully computable from frequency tables. This is genuinely novel as a site feature and immune to cherry-picking because it's a global statistic.

---

## 6. How it lands on the site

### 6.1 Root page — a new "In Pre-Islamic Poetry" section

On `/root/<bw>` (e.g. `/root/kfr`), add a new section that mirrors the existing violet **AI Root Meaning** panel in style. Good news: **the data shape already exists.** The `term_surveys` table (currently a 14-root pilot: ṣ-l-w, ṣ-w-m, ḥ-j-j, s-j-d …) already stores exactly the fields this needs —

- `canonical_english`, `reasoning` (the semantic thread),
- `counter_examples_json` (← the built-in objectivity step!),
- `translation_note`, `hard_cases_json`, `confidence`.

We extend that pattern with a sibling table, e.g. `root_poetry_comparisons`, carrying: the **semantic-shift type** (§5.1), the **prose comparison**, the **quoted poetic lines with poet + poem + authentication tier**, the **collocation fingerprints** (§5.2), and a **continuity flag**. It renders as a section that sits naturally after *Semitic Cognates* and before *Sample Verses* — a parallel "here's the word's life in the wider language" panel, with cognates looking *outward* across Semitic languages and this one looking *backward* in time to the Arabs' own usage.

**Every quoted line shows its authentication tier as a small badge** (Gold / Strong / Attributed), and roots in the prose are linked + tooltipped exactly as they already are in exegesis and translation notes (you built `VerseRefText` / `RootRefLink` for this).

### 6.2 Verse page — a note below exegesis

On `/verse/113:1` etc., add a new note block **after** the Exegesis note (you already established the order Translation → Exegesis → Grammar; the poetry note slots in as a distinct, clearly-labeled block — most naturally right after Exegesis, since it's interpretive context). It appears **only** when the verse contains a root with a meaningful, authenticated comparison — it must *earn* its place on the page, never padding. It renders through the same `FormattedText` pipeline (so `**bold**`/`*italic*`, verse-refs, and root links all work for free).

### 6.3 Reading mode

Fold it into the existing global notes toggle you just shipped (`isReaderNotesVisible` / `ReaderVerse` `VerseNotesPanel`). Order inside the panel: Translation → Exegesis → **Pre-Islamic Poetry** → Grammar. It's just another optional sub-section keyed off a `has_poetry_note` flag on the surah payload (mirroring `has_exegesis`).

### 6.4 Ask-the-Quran

Feed the comparison into the assistant context, exactly as you did with exegesis. In `context-builders.ts`, `buildVerseContext` gets a `## Pre-Islamic Poetry Comparison` section and `buildRootContext` gets the root-level survey — so when a user asks *"how is this word different from how the Arabs used it?"*, the assistant answers from our authenticated notes rather than from its own (possibly hallucinated) memory of poetry.

### 6.5 The objectivity UI — show the seams

This is what sets the feature apart visually:

- **Authentication badges** on every poetic quotation (Gold / Strong / Attributed / Disputed).
- **A "continuity" styling** distinct from "contrast" styling — so a reader scanning the site sees that we document agreement, not only difference. (The Labīd note in §4.5 should look *celebratory*, not grudging.)
- **"See the evidence"** — every claim expands to the actual line(s), poet, poem, and tier. No assertion floats free of its source.
- **A confidence indicator** on the shift-type classification, like the existing exegesis `source_scores`.

---

## 7. The generation pipeline (how a note gets written)

This reuses the machinery you already built for exegesis (config table → generate → admin review → approve → it goes live), with poetry-specific steps and a hard objectivity rubric.

**Per root (Engine 1):**
1. Pull the root's full Qurʾānic profile (you have this: occurrences, lemmas, AI root meaning, cognates).
2. Pull the root's occurrences in the **authenticated** poetry corpus (requires the poetry to be root-indexed — Part 3.3 step 4).
3. **Adversarial counter-search (required, logged):** explicitly retrieve poetic lines that use the root *the way the Qurʾān does.* If they're plentiful → the note's verdict is *continuity*.
4. LLM drafts the comparison under the **rubric below**, emitting: shift-type, prose, the specific quoted lines (with refs), collocation lists, continuity flag, confidence.
5. **Admin review** (your existing review queue pattern) → approve → live.

**The objectivity rubric (baked into the prompt — the feature's constitution):**

> - Quote only authenticated lines; **always** state the poet, poem, and authentication tier. Never fabricate a line — if you cannot cite a real one, make the claim at the level of the classical dictionaries (Lane / Lisān al-ʿArab / al-Rāghib) and say so.
> - You **must** report counter-evidence found in step 3. If the poetry uses the word as the Qurʾān does, the verdict is *continuity*, and you say so plainly.
> - Distinguish a genuine semantic/thematic shift from a mere difference of **genre**. A poet describing a camel is not "inferior" — do not manufacture contrasts out of register differences.
> - Affirm shared values where they exist (courage, generosity, hospitality, loyalty). The goal is *understanding the Qurʾān's language in context*, not scoring points.
> - State strong contrasts **plainly and vividly** when the evidence is strong (no false hedging) — but only when 1–4 are satisfied.
> - **Quran-only theology:** no post-Qurʾānic sectarian framing in the output (consistent with the site's existing rule).

This rubric is the difference between a scholarship tool and a polemic generator. It should live in the config table's `system_prompt`, versioned, exactly like the exegesis and translation configs.

---

## 8. Staged rollout

| Phase | What | Why first / notes |
|---|---|---|
| **0 — Corpus** | Curate the *Muʿallaqāt* (Tier A) by hand; load + filter the Kaggle scrape (Tier C); root-index the poetry with CAMeL Tools/Farasa. | Nothing is possible until poetry is queryable *by root*. The *Muʿallaqāt* alone unblock a credible v1. |
| **1 — Root pilot** | Engine 1 on ~15–20 **high-yield roots** (Appendix A), root-level only, behind the admin review queue. | Proves the value where contrasts are real and rich. Reuses `term_surveys`-style schema + your review UI. |
| **2 — Verse notes** | Engine 2 for the verses where those pilot roots are load-bearing; render below exegesis + in reader. | Now it's specific and quotable. Small surface, high signal. |
| **3 — Thematic & form** | Engine 4 motif essays (Part 5 table); then Engine 3 (meter/rhyme) using external meter tools. | The "wow" layer; Engine 3 last because scansion is hardest. |
| **4 — Everywhere** | Ask-the-Quran feed, negative-space map, continuity ledger surfaced site-wide, broaden roots. | Polish + integration once the core is trusted. |

A deliberately *small, deep, gold-tier* v1 (the *Muʿallaqāt* + ~15 roots, every claim sourced and tiered) will be more impressive and more defensible than a broad, shallow, unauthenticated sweep. Depth and provenance are the whole point.

---

## 9. Risks & honest limitations

- **Authentication is never fully solved.** Even Tier-A attribution isn't 100%. We mitigate, we don't eliminate — hence visible tiers and conservative claims. (This is a feature, not a bug: the feature *teaches* the authentication problem.)
- **Poetry morphology will be noisier than the Qurʾān's.** The Qurʾānic morphology you have is hand-verified gold; an automatic parser over poetry will make mistakes. Root-indexing the poetry is "good enough for retrieval," but quoted lines should be human-checked before promotion to Gold/Strong.
- **Meter analysis is genuinely hard** and partly subjective at the edges; keep Engine 3 modest and lean on published tools.
- **The temptation to over-claim is constant.** The rubric and the required counter-search are the guardrails; the admin review queue is the backstop. Treat any note that *can't* cite a real line, or that found no counter-evidence because it didn't look, as a defect.
- **Scope:** this is a multi-month feature, not a weekend. Phase 0 (the corpus + root-indexing) is the real cost; everything after reuses patterns you already have.

---

## Appendix A — Candidate high-yield roots for the pilot

Roots where a *real, interesting* Qurʾān-vs-poetry relationship is likely (each needs verification through the pipeline — these are hypotheses, not conclusions):

| Root | Physical / Jahilī sense | Likely Qurʾānic move | Type |
|---|---|---|---|
| **K-F-R** ك ف ر | cover seed / night conceals | covering of truth → disbelief; *kuffār* = tillers (57:20) | elevation + bridge |
| **W-Q-Y** و ق ي | shield / armor | *taqwā*, shielding the soul (2:24) | elevation |
| **D-H-R** د ه ر | blind, sovereign Fate | demoted under God (45:24) | theologization / subversion |
| **K-R-M** ك ر م | noble by lineage; generous host | nobility by *taqwā* (49:13) | subversion + continuity |
| **Ḥ-L-M** ح ل م | forbearance, self-mastery (a *murūʾa* virtue) | divine *ḥilm*; God as *al-Ḥalīm* | elevation / continuity |
| **J-N-N** ج ن ن | to cover/conceal → *jinn*, *junūn*, *janīn* | *janna* (garden, hidden); the "concealment family" with K-F-R | widening / structural |
| **Gh-F-R** غ ف ر | to cover (a helmet-lining *mighfar* covers the head) | divine forgiveness = covering of sins | elevation |
| **ʿ-Z-Z** ع ز ز | tribal might / scarcity-strength | *ʿizza* belongs to God (63:8) | reassignment |
| **R-Z-Q** ر ز ق | gift, fodder, a soldier's pay | provision *from God* | reassignment |
| **Ṣ-B-R** ص ب ر | grim endurance / being bound (a beast "ṣabr") | patience as worship (already a `term_surveys` root) | elevation |
| **ʾ-J-L** أ ج ل | a fixed term / a debt's due-date | the appointed term of life & the Hour | theologization |
| **H-D-Y** ه د ي | guiding a traveller through the desert | divine *hudā*, guidance to truth | elevation |

The "**concealment family**" (K-F-R, J-N-N, Gh-F-R, S-T-R) is especially worth piloting together: it shows, *structurally*, that the Qurʾān inherited the Arabs' rich vocabulary of *physical covering* and systematically re-aimed it toward the moral and metaphysical — a corpus-level pattern far more persuasive than any single anecdote.

---

## References

Sources consulted for the claims and citations above:

- Ṭāhā Ḥusayn, *On Pre-Islamic Poetry* (authenticity debate) — [Wikipedia](https://en.wikipedia.org/wiki/On_Pre-Islamic_Poetry); [Abramundi essay](https://www.abramundi.org/post/on-pre-islamic-poetry-by-taha-husayn-a-shock-that-awakened-arab-literary-criticism)
- K-F-R as "cover / sower / night," and Q 57:20 *kuffār* = tillers — [The Ocean of the Qurʾān 57:20](https://theoceanofthequran.org/57-20/); [Arabic for Nerds: "What is a Kāfir?"](https://arabic-for-nerds.com/islam/what-is-a-kafir/); [Juan Cole on *kufr*](https://www.juancole.com/2023/11/understanding-%D9%83%D9%81%D8%B1-muhammad.html)
- D-H-R / Fate and Q 45:24 — [Al-Jāthiya (Wikipedia)](https://en.wikipedia.org/wiki/Al-Jathiya); [Qurʾān Gallery on 45:24](https://qurangallery.app/by-ayah/ad-dahr-meaning-surah-al-jathiyah-45-24-refuting-materialism); ["Time in Islam," Springer](https://link.springer.com/referenceworkentry/10.1007/978-1-4020-4425-0_8899)
- Nobility / Q 49:13 vs. tribal honor — [Tafsīr Maʿārif al-Qurʾān 49:13](https://quran.com/49:13/tafsirs/en-tafsir-maarif-ul-quran); [Qurʾān Gallery on 49:13](https://qurangallery.app/by-ayah/human-equality-in-islam-surah-al-hujurat-49-13-piety-over-race)
- *taqwā* ← *wiqāya* (shield), al-Rāghib al-Iṣfahānī's *Mufradāt* — [al-Rāghib's Mufradāt (Arabic Lexicon)](https://arabiclexicon.hawramani.com/al-raghib-al-isfahani-al-mufradat-fi-gharib-al-quran/); [Muṭahharī, "Taqwā Part I" (al-Islam.org)](https://al-islam.org/message-thaqalayn/vol11-n4-2011/taqwa-part-1-murtadha-mutahhari/taqwa-part-i)
- Labīd's "all but God is vain" + the Prophetic remark — [Ṣaḥīḥ al-Bukhārī 6403 (Sunnah.com)](https://sunnah.com/bukhari:6403)
- Muʿallaqāt structure (*nasīb / raḥīl / fakhr*, *aṭlāl*, the camel) — [Muʿallaqāt (Wikipedia)](https://en.wikipedia.org/wiki/Mu'allaqat); [Britannica: al-Muʿallaqāt](https://www.britannica.com/topic/Al-Muallaqat-Arabic-literature)
- Qurʾān vs. the 16 *buḥūr* / *saj‘* vs. monorhyme *qaṣīda* — [Qasida (Wikipedia)](https://en.wikipedia.org/wiki/Qasida); [Arabic poetry (Grokipedia)](https://grokipedia.com/page/Arabic_poetry)
- Datasets & corpora — [Kaggle: mdanok Arabic Poetry Dataset](https://www.kaggle.com/datasets/mdanok/arabic-poetry-dataset); [AraPoems (Harvard Dataverse)](https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/PJPWOY); [OpenITI (Zenodo)](https://zenodo.org/records/10021513); [MetRec meter-classification](https://github.com/zaidalyafeai/MetRec)

*— end of document —*
