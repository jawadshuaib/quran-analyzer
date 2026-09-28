import { useState } from 'react';
import { useSEO } from '../hooks/useSEO';

/* ───────── tiny accordion helper ───────── */
function Section({
  id,
  number,
  title,
  subtitle,
  children,
  defaultOpen = false,
}: {
  id: string;
  number: string;
  title: string;
  subtitle: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="rounded-xl border border-card-border bg-white overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full text-left px-5 sm:px-7 py-5 sm:py-6 flex items-start gap-4 hover:bg-cream-dark/40 transition-colors"
        aria-expanded={open}
        aria-controls={`section-${id}`}
      >
        <span className="shrink-0 w-8 h-8 rounded-full bg-gold/10 text-gold text-sm font-semibold flex items-center justify-center mt-0.5">
          {number}
        </span>
        <div className="flex-1 min-w-0">
          <h2 className="font-serif text-lg sm:text-xl font-medium text-ink">{title}</h2>
          <p className="text-sm text-ink-secondary mt-0.5 leading-relaxed">{subtitle}</p>
        </div>
        <svg
          className={`w-5 h-5 text-ink-muted shrink-0 mt-1 transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div id={`section-${id}`} className="px-5 sm:px-7 pb-6 sm:pb-8 pt-0">
          <div className="border-t border-card-border pt-5 space-y-4 text-[14.5px] sm:text-[15px] text-ink-secondary leading-relaxed">
            {children}
          </div>
        </div>
      )}
    </section>
  );
}

/* ───────── example card used inside sections ───────── */
function Example({ label, children }: { label: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-cream border border-card-border p-4 sm:p-5">
      <p className="text-[11px] text-ink-muted tracking-wider uppercase mb-2">{label}</p>
      {children}
    </div>
  );
}

/* ───────── main page ───────── */
export default function MethodologyPage() {
  useSEO({
    title: 'Methodology — How We Translate the Quran',
    description: 'How we read the Quran\'s words: its own internal usage first, then the pre-Islamic poetry of its time, sixteen classical Arabic dictionaries, Semitic cognates across 59 languages, and morphology — every step grounded in open evidence.',
    path: '/methodology',
  });

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10 flex-1">
      {/* Header */}
      <div className="text-center mb-10">
        <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3.5">Our Approach</p>
        <h1 className="font-serif text-2xl sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-2">
          How we translate the Quran
        </h1>
        <p className="text-sm sm:text-[15px] text-ink-secondary leading-relaxed max-w-2xl mx-auto">
          Rather than inheriting earlier English glosses, we read each word
          against the evidence of how Arabic was actually used: first the
          Quran's own internal usage, then the poetry of the Quran's own time,
          the classical Arabic dictionaries, the related Semitic languages, and
          the grammatical form of the word itself.
        </p>
      </div>

      {/* Principle statement */}
      <div className="rounded-xl border border-gold/20 bg-gold-light/40 px-5 sm:px-7 py-5 sm:py-6 mb-6 text-center">
        <p className="font-serif text-base sm:text-[17px] text-ink leading-relaxed italic">
          "The best interpreter of the Quran is the Quran itself."
        </p>
        <p className="text-xs text-ink-muted mt-1.5">A classical principle of Quranic study</p>
      </div>

      {/* Sections */}
      <div className="space-y-4">

        {/* ─── 1. Quranic Cross-Reference ─── */}
        <Section
          id="cross-ref"
          number="1"
          title="The Quran as its own commentary"
          subtitle="Every word is understood by how the Quran itself uses it elsewhere."
          defaultOpen={true}
        >
          <p>
            When a word appears in a verse, we look at every other place the
            Quran uses that same word — the same root, the same lemma, sometimes
            the same grammatical form. This internal cross-referencing reveals
            patterns and nuances that a standalone dictionary entry cannot.
          </p>
          <p>
            For each verse, a relevance algorithm identifies the most
            semantically related verses — those that share the most distinctive
            vocabulary. Common function words are automatically down-weighted so
            the comparisons focus on meaningful, content-bearing terms.
          </p>

          <Example label="Example · Verse 96:1">
            <a
              href="/verse/96:1"
              dir="rtl"
              lang="ar"
              className="block font-arabic text-2xl text-ink text-right leading-[2] mb-3 hover:text-gold-hover transition-colors"
            >
              ٱقْرَأْ بِٱسْمِ رَبِّكَ ٱلَّذِى خَلَقَ
            </a>
            <p className="text-sm text-ink-secondary">
              The word <a href="/word/96:1/1" className="font-arabic font-medium text-ink hover:text-gold-hover transition-colors" lang="ar">ٱقْرَأْ</a> (from
              the root <a href="/root/qrA" className="text-emerald-700 hover:underline font-medium">q-r-ʾ</a>)
              is conventionally rendered as "read." But cross-referencing its
              other Quranic occurrences — particularly in verses like{' '}
              <a href="/verse/17:14" className="text-gold-hover hover:text-gold font-medium">17:14</a> and{' '}
              <a href="/verse/75:18" className="text-gold-hover hover:text-gold font-medium">75:18</a>{' '}
              — reveals a broader meaning: to proclaim, to recite aloud,
              to gather and deliver. The Quran's own usage shapes the gloss,
              not an inherited English convention.
            </p>
          </Example>

          <p>
            Each translation also includes notes whenever it departs from
            conventional glosses, explaining which Quranic cross-references
            motivated the departure.
          </p>
        </Section>

        {/* ─── 2. Pre-Islamic poetry ─── */}
        <Section
          id="poetry"
          number="2"
          title="The poetry of the Quran's own time"
          subtitle="How the Quran's first hearers used its words, as the poetry before Islam records it."
        >
          <p>
            The Quran was addressed to people who already spoke its language.
            The fullest record of how they spoke is the poetry of the
            generations before Islam: the Muʿallaqāt and the collected poems of
            Imruʾ al-Qays, Ṭarafa, Zuhayr, al-Nābigha, ʿAntara and their
            contemporaries. When a root turns up in that poetry, it shows what
            the word could mean in the Quran's own time, before later
            scholarship gave many words a settled technical sense.
          </p>
          <p>
            That record needs care. The poems were carried by memory and
            written down only in the eighth and ninth centuries, and critics
            from Ibn Sallām al-Jumaḥī in the ninth century to Ṭāhā Ḥusayn in
            the twentieth showed that some of it was reworked or invented
            later. So every poem is graded by how reliably it was transmitted:
            the Muʿallaqāt first, then the collected poems of the major poets,
            then the rest. A contrast between the poets and the Quran is never
            drawn from the least reliable poems alone.
          </p>
          <p>
            On a root's page, <em>In Pre-Islamic Poetry</em> sets out the
            senses the root carries in this poetry, each backed by quoted lines
            that open in the full poem, with a translation. For some roots it
            also compares the poets' usage with the Quran's. A comparison says
            the Quran departs from the poets only after a search for
            counter-examples, and it reports continuity where it finds it: the
            poets already use <span className="italic">taqwā</span> (root{' '}
            <a href="/root/wqy#poetry" className="text-emerald-700 hover:underline font-medium">w-q-y</a>)
            for a person's moral character, so the Quran inherited the word's
            inward sense rather than coining it.
          </p>

          <Example label={<>Example · Root <a href="/root/dhr#poetry" className="text-gold-hover hover:text-gold">د ه ر (d-h-r)</a></>}>
            <a
              href="/poem/296#line-13"
              dir="rtl"
              lang="ar"
              className="block font-arabic text-xl text-ink text-right leading-[2] mb-1 hover:text-gold-hover transition-colors"
            >
              فَسَطا عَلَيَّ الدَهرُ سَطوَةَ غادِرٍ وَالدَهرُ يَبخُلُ تارَةً وَيَجودُ
            </a>
            <p className="text-sm text-ink-secondary italic mb-3">
              "Time assailed me like a traitor; Time is now miserly, now generous." (ʿAntara)
            </p>
            <p className="text-sm text-ink-secondary">
              In the poets, <span className="font-medium text-ink">dahr</span>,
              "time", is a power that gives, withholds and destroys. The Quran
              quotes that view in the mouths of those who say there is nothing
              beyond this life, "nothing destroys us but time"
              (<a href="/verse/45:24" className="text-gold-hover hover:text-gold font-medium">45:24</a>),
              and answers it: "of that they have no knowledge; they only
              conjecture." Its one other use of the word
              (<a href="/verse/76:1" className="text-gold-hover hover:text-gold font-medium">76:1</a>)
              is a plain stretch of time.
            </p>
          </Example>

          <p>
            The poetry corroborates; it never overrides. The Quran's own usage
            stays the primary evidence, and the poetry is kept out of the
            exegesis notes, which draw on the Quran alone. Where a verse has a
            poetry note, it sits below the exegesis under its own heading. The
            poems can be read in full on the{' '}
            <a href="/poems" className="text-gold-hover hover:text-gold font-medium underline underline-offset-2">Pre-Islamic Poetry</a>{' '}
            page, and the metres they were composed in are explained, with
            their rhythms, on the{' '}
            <a href="/meters" className="text-gold-hover hover:text-gold font-medium underline underline-offset-2">Metres</a>{' '}
            pages.
          </p>
        </Section>

        {/* ─── 3. Classical dictionaries ─── */}
        <Section
          id="dictionaries"
          number="3"
          title="The classical Arabic dictionaries"
          subtitle="Sixteen dictionaries, from the eighth century to the nineteenth, read as witnesses to usage."
        >
          <p>
            From the late eighth century, Arab philologists gathered the
            language from Bedouin speakers, poetry and proverbs and set it down
            in dictionaries. Each root's page gathers what up to sixteen of
            them say about it, in the order their authors lived: from
            al-Khalīl's <span className="italic">Kitāb al-ʿAyn</span>, the first
            Arabic dictionary, through Ibn Fāris's{' '}
            <span className="italic">Maqāyīs al-Lugha</span> and Ibn Manẓūr's{' '}
            <span className="italic">Lisān al-ʿArab</span>, to the Arabic–English
            lexicons of Lane and Salmoné in the nineteenth century. Each entry
            has a readable English version, with the original text (and, for
            the Arabic works, a close translation) one click beneath it, and a
            link to where the text was taken from.
          </p>
          <p>
            The dictionaries come after the Quran. The earliest was compiled
            more than a century later, and by then some words had taken on the
            settled meanings of religious practice and law. So they are read as
            witnesses, not as final authorities. They are most valuable where
            they preserve older usage: a line of verse, a Bedouin expression,
            the concrete sense a word was built from. Where a dictionary gives
            a later technical definition, it is reported as that
            lexicographer's account, not as the meaning of the Quran's word,
            and each view is credited to the scholar the dictionary quotes.
          </p>

          <Example label={<>Example · Root <a href="/root/kfr#dict-ibn-faris-maqayis-al-lugha" className="text-gold-hover hover:text-gold">ك ف ر (k-f-r)</a> in the <span className="normal-case italic">Maqāyīs</span></>}>
            <p className="text-sm text-ink-secondary">
              Ibn Fāris (d. 1004) traces <span className="font-medium text-ink">k-f-r</span> to
              a single meaning: covering and concealing. A man who puts a
              garment over his mail-coat has <span className="italic">kafara</span> it,
              and a sower is a <span className="italic">kāfir</span> because he
              covers the seed with soil. He cites the Quran's own use of the
              word for sowers: rain "whose growth delights the{' '}
              <span className="italic">kuffār</span>"
              (<a href="/verse/57:20" className="text-gold-hover hover:text-gold font-medium">57:20</a>).
              <span className="italic"> Kufr</span>, usually rendered
              "disbelief", he derives from the same sense, as a covering-over of
              the truth, just as <span className="italic">kufrān al-niʿma</span>,
              ingratitude, covers over a kindness received.
            </p>
          </Example>

          <p>
            Reading the dictionaries in order of date is part of the method: it
            shows when a sense first appears and how the account grows over the
            centuries. A{' '}
            <a href="/classical-dictionaries" className="text-gold-hover hover:text-gold font-medium underline underline-offset-2">reader's guide</a>{' '}
            to each dictionary explains who wrote it, how it is arranged and
            what to watch for, and the{' '}
            <a href="/dictionary" className="text-gold-hover hover:text-gold font-medium underline underline-offset-2">dictionary search</a>{' '}
            finds a root from an English meaning, an Arabic word or a
            transliteration.
          </p>
        </Section>

        {/* ─── 4. Root & Cognate Analysis ─── */}
        <Section
          id="roots"
          number="4"
          title="Root words and Semitic cognates"
          subtitle="Tracing each Arabic root back through its family of Semitic languages."
        >
          <p>
            Classical Arabic belongs to a family of Semitic languages — Hebrew,
            Aramaic, Syriac, Akkadian, Ge'ez, and others — that share a common
            ancestor. Many Quranic roots have cognates in these languages,
            often preserving a core meaning that illuminates the Arabic.
          </p>
          <p>
            Over 50% of the Quran's roots have documented cognates across 59
            Semitic languages. We use this etymological data as supplementary
            evidence — not to override the Quran's own usage, but to confirm
            it, or to shed light on rare words where the Quran provides fewer
            internal examples.
          </p>

          <Example label="Example · Root ر ح م (r-ḥ-m)">
            <div className="flex flex-wrap gap-2 mb-3">
              <a
                href="/root/rHm"
                className="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium border bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100 transition-colors"
              >
                <span dir="rtl" lang="ar" className="font-arabic text-base">ر ح م</span>
                <span className="text-xs text-emerald-500">(rHm)</span>
              </a>
              <span className="text-xs text-ink-muted self-center">313 verses</span>
            </div>
            <p className="text-sm text-ink-secondary mb-2">
              The root <span className="font-medium text-ink">r-ḥ-m</span> appears in
              two of the most frequent divine attributes: <span className="font-medium text-ink">ar-Raḥmān</span> and{' '}
              <span className="font-medium text-ink">ar-Raḥīm</span>.
              Conventional translations flatten both into "merciful."
            </p>
            <p className="text-sm text-ink-secondary">
              But the cognate record tells a richer story. Across Hebrew
              (<span className="italic">reḥem</span> — womb), Aramaic, Syriac, Ge'ez, and
              even Akkadian (<span className="italic">rēmu</span> — womb), this root
              consistently refers to the womb — the seat of tender, nurturing
              care. The Quran's own usage of the plural{' '}
              <span className="font-medium text-ink">arḥām</span> (wombs, <a href="/verse/2:228" className="text-gold-hover hover:text-gold font-medium">2:228</a>)
              preserves this concrete sense. Understanding the root's origin
              transforms "mercy" from an abstract attribute into something
              visceral — a compassion as intimate as a mother's bond with the
              life she carries.
            </p>
          </Example>
        </Section>

        {/* ─── 5. Morphological Precision ─── */}
        <Section
          id="morphology"
          number="5"
          title="Morphological precision"
          subtitle="Verb forms, case, voice, and number as hard constraints on meaning."
        >
          <p>
            Arabic is a morphologically rich language. A single root can
            generate dozens of words through systematic patterns — verb forms
            (I through X), active and passive voice, singular / dual / plural,
            masculine / feminine, and case endings. Each form carries its own
            semantic nuance.
          </p>
          <p>
            Our translations treat morphology as a hard constraint: the
            grammatical form of a word limits what meanings are possible,
            regardless of what a dictionary might list for the bare root.
          </p>

          <Example label={<>Example · Root <a href="/root/Elm" className="text-gold-hover hover:text-gold">ع ل م (ʿ-l-m)</a> — Three forms, three meanings</>}>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <span dir="rtl" lang="ar" className="font-arabic text-xl text-ink shrink-0 w-16 text-center">عَلِمَ</span>
                <div>
                  <span className="text-xs font-medium text-ink-muted uppercase tracking-wide">Form I · verb</span>
                  <p className="text-sm text-ink-secondary">
                    <span className="font-medium text-ink">ʿalima</span> — "he knew / came to know."
                    The base form: a simple act of knowing.
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span dir="rtl" lang="ar" className="font-arabic text-xl text-ink shrink-0 w-16 text-center">عَلَّمَ</span>
                <div>
                  <span className="text-xs font-medium text-ink-muted uppercase tracking-wide">Form II · verb</span>
                  <p className="text-sm text-ink-secondary">
                    <span className="font-medium text-ink">ʿallama</span> — "he taught."
                    Form II adds a causative shade: to cause someone else
                    to know. Appears in <a href="/verse/96:5" className="text-gold-hover hover:text-gold font-medium">96:5</a>, <span className="italic">"taught the human what he did not know."</span>
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <span dir="rtl" lang="ar" className="font-arabic text-xl text-ink shrink-0 w-16 text-center">عِلْم</span>
                <div>
                  <span className="text-xs font-medium text-ink-muted uppercase tracking-wide">Noun (maṣdar)</span>
                  <p className="text-sm text-ink-secondary">
                    <span className="font-medium text-ink">ʿilm</span> — "knowledge."
                    The abstract noun form. Translating all three as simply
                    "knowledge" would erase the distinction between knowing,
                    teaching, and the state of knowledge itself.
                  </p>
                </div>
              </div>
            </div>
          </Example>

          <p>
            Every word in our corpus carries full morphological tagging — stem,
            form, person, number, gender, case, and voice — ensuring that
            translations respect these grammatical realities rather than
            defaulting to a single dictionary gloss.
          </p>
        </Section>

        {/* ─── 6. Word-by-word alignment ─── */}
        <Section
          id="word-by-word"
          number="6"
          title="Word-by-word transparency"
          subtitle="Every Arabic word has its own tooltip gloss, aligned with the verse translation."
        >
          <p>
            Most translations offer either a full verse or a word-by-word
            interlinear — but rarely do the two align. A verse translation
            might say "establish prayer" while the word tooltip says "perform
            worship," leaving the reader to reconcile the difference.
          </p>
          <p>
            We ensure that word-level glosses and verse-level translations use
            consistent vocabulary. When a verse translation renders a word in
            a particular way, the corresponding tooltip reflects that same
            choice, with the reasoning available on the word's detail page.
          </p>

          <Example label={<>Example · <a href="/verse/2:3" className="text-gold-hover hover:text-gold">Verse 2:3</a>, word 4</>}>
            <div className="flex items-center gap-4 mb-3">
              <a href="/word/2:3/4" dir="rtl" lang="ar" className="font-arabic text-2xl text-ink hover:text-gold-hover transition-colors">ٱلصَّلَوٰةَ</a>
              <div>
                <p className="text-sm font-medium text-ink">aṣ-ṣalāh</p>
                <p className="text-xs text-ink-muted">Root: <a href="/root/Slw" className="text-emerald-700 hover:underline">ص ل و (ṣ-l-w)</a></p>
              </div>
            </div>
            <p className="text-sm text-ink-secondary">
              Rather than splitting "establish prayer" across two words and
              "the prayer" across a third — causing meaning to bleed between
              neighbours — each word receives its own precise, non-overlapping
              gloss. The word <a href="/word/2:3/3" className="font-medium text-ink hover:text-gold-hover transition-colors">yaqīmūna</a> (يُقِيمُونَ)
              carries "establish" and <a href="/word/2:3/4" className="font-medium text-ink hover:text-gold-hover transition-colors">aṣ-ṣalāh</a> carries
              "the ṣalāh" — with the <a href="/verse/2:3" className="text-gold-hover hover:text-gold font-medium">full verse translation</a> providing the
              unified reading.
            </p>
          </Example>
        </Section>

        {/* ─── 7. Evidence hierarchy ─── */}
        <Section
          id="evidence"
          number="7"
          title="Evidence hierarchy"
          subtitle="When sources disagree, a clear priority determines the outcome."
        >
          <p>
            Not all evidence carries equal weight. Across the site it is
            weighed in a strict order:
          </p>

          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center">1</span>
              <div>
                <p className="font-medium text-ink text-sm">Quranic self-reference</p>
                <p className="text-sm text-ink-secondary">
                  How the Quran uses the same root and lemma elsewhere. This is
                  the primary evidence — the text interpreting itself.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center">2</span>
              <div>
                <p className="font-medium text-ink text-sm">Contextual coherence</p>
                <p className="text-sm text-ink-secondary">
                  Meaning must flow naturally within the surrounding passage —
                  the verses before and after — and fit the broader narrative arc.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center">3</span>
              <div>
                <p className="font-medium text-ink text-sm">Usage in the Quran's own time</p>
                <p className="text-sm text-ink-secondary">
                  How the poets of the Quran's age used the root, graded by how
                  reliably each poem was transmitted. It can confirm or narrow a
                  reading, but never overrides the Quran's own usage.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center">4</span>
              <div>
                <p className="font-medium text-ink text-sm">The classical dictionaries</p>
                <p className="text-sm text-ink-secondary">
                  The philologists' record of usage, read in order of date:
                  strongest where it preserves older usage, and weighed against
                  the Quran where it gives a later technical definition.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center">5</span>
              <div>
                <p className="font-medium text-ink text-sm">Semitic cognate evidence</p>
                <p className="text-sm text-ink-secondary">
                  The etymological record confirms Quranic usage or
                  disambiguates rare words — but never overrides internal
                  evidence.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center">6</span>
              <div>
                <p className="font-medium text-ink text-sm">Morphological constraints</p>
                <p className="text-sm text-ink-secondary">
                  Verb form, voice, case, and number act as hard filters on
                  which meanings are grammatically possible.
                </p>
              </div>
            </div>
          </div>

          <p>
            When a conventional gloss conflicts with what the Quran's own
            usage patterns suggest, the translation follows the Quranic
            evidence and documents the departure with a clear note.
          </p>
        </Section>

        {/* ─── 8. Departure transparency ─── */}
        <Section
          id="departures"
          number="8"
          title="Departure notes"
          subtitle="When we differ from convention, we explain why."
        >
          <p>
            Every translation that departs from a conventional English gloss
            is accompanied by a note explaining which evidence — Quranic
            cross-references, cognate data, or morphological analysis —
            motivated the change.
          </p>
          <p>
            This is not a claim of authority. It is an invitation to verify.
            The underlying data — every root, every cross-reference, every
            cognate — is open and explorable on this site, so you can follow
            the same trail of evidence yourself.
          </p>

          <Example label="Example">
            <p className="text-sm text-ink-secondary">
              On any verse page, click a word to see its full analysis: the
              root it belongs to, every other verse using the same lemma, the
              Semitic cognate family, and — if the translation differs from the
              conventional one — a note explaining the reasoning.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <a
                href="/verse/96:1"
                className="text-xs text-gold-hover hover:text-gold font-medium underline underline-offset-2"
              >
                Try verse 96:1 →
              </a>
              <a
                href="/word/96:1/1"
                className="text-xs text-gold-hover hover:text-gold font-medium underline underline-offset-2"
              >
                Word analysis: ٱقْرَأْ →
              </a>
              <a
                href="/root/qrA"
                className="text-xs text-gold-hover hover:text-gold font-medium underline underline-offset-2"
              >
                Root: q-r-ʾ →
              </a>
            </div>
          </Example>
        </Section>

        {/* ─── 9. Verse exegesis ─── */}
        <Section
          id="exegesis"
          number="9"
          title="Verse exegesis"
          subtitle="A short reflection on each verse, built only from the Quran's own cross-references."
        >
          <p>
            Beneath the translation, departure, and grammar notes, many verses
            carry a short <em>exegesis note</em> — two or three paragraphs in a
            teacher's voice that take the verse's most substantive insight and
            develop it carefully, opening on a concrete feature of the wording
            and arriving at a single earned observation.
          </p>
          <p>
            These notes follow the same discipline as the rest of the site:
            every claim is grounded in the Quran's own usage. The reflection is
            earned through cross-references to other verses — never imported from
            outside the text, and never resting on external narratives or
            sectarian commentary. Each note is editorially reviewed before it
            appears, and the roots and verse references inside it are themselves
            links, so you can follow every step of the reasoning.
          </p>

          <Example label="Example">
            <p className="text-sm text-ink-secondary">
              On <a href="/verse/113:1" className="text-gold-hover hover:text-gold font-medium underline underline-offset-2">verse 113:1</a>,
              the note traces the title "Lord of the daybreak" to the root{' '}
              <span className="italic">f-l-q</span> — a forceful <em>cleaving</em>, not
              the gentle morning — and weighs it against the verses that follow.
              Hover the root or any verse reference in the note to look it up
              without leaving the page.
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <a
                href="/verse/113:1"
                className="text-xs text-gold-hover hover:text-gold font-medium underline underline-offset-2"
              >
                Try verse 113:1 →
              </a>
              <a
                href="/verse/112:1"
                className="text-xs text-gold-hover hover:text-gold font-medium underline underline-offset-2"
              >
                Try verse 112:1 →
              </a>
            </div>
          </Example>
        </Section>
      </div>

      {/* Closing */}
      <div className="mt-10 text-center">
        <p className="text-sm text-ink-secondary leading-relaxed max-w-xl mx-auto">
          This methodology is applied consistently across all 6,236 verses, 77,000+
          words, and 1,600+ roots in the Quran. Every piece of data is open and
          explorable — start with any{' '}
          <a href="/verse/2:255" className="text-gold-hover hover:text-gold font-medium underline underline-offset-2">verse</a>,{' '}
          <a href="/root/rHm" className="text-gold-hover hover:text-gold font-medium underline underline-offset-2">root</a>, or{' '}
          <a href="/word/96:1/1" className="text-gold-hover hover:text-gold font-medium underline underline-offset-2">word</a> and
          follow the evidence yourself.
        </p>
      </div>
    </div>
  );
}
