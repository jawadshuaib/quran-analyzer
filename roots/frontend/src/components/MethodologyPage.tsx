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
function Example({ label, children }: { label: string; children: React.ReactNode }) {
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
    description: 'Our translation methodology uses three lenses: the Quran\'s own internal cross-references, Semitic cognate etymology across 59 languages, and morphological precision — ensuring every word is grounded in evidence.',
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
          Rather than inheriting earlier English glosses, every word and verse
          is examined through three independent lenses: the Quran's own
          internal usage, the morphological form of each word, and the
          etymological record preserved across Semitic languages.
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
            <p
              dir="rtl"
              lang="ar"
              className="font-arabic text-2xl text-ink text-right leading-[2] mb-3"
            >
              ٱقْرَأْ بِٱسْمِ رَبِّكَ ٱلَّذِى خَلَقَ
            </p>
            <p className="text-sm text-ink-secondary">
              The word <span className="font-medium text-ink">ٱقْرَأْ</span> (from
              the root <a href="/root/qrA" className="text-emerald-700 hover:underline font-medium">q-r-ʾ</a>)
              is conventionally rendered as "read." But cross-referencing its
              other Quranic occurrences — particularly in verses like 17:14 and
              75:18 — reveals a broader meaning: to proclaim, to recite aloud,
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

        {/* ─── 2. Root & Cognate Analysis ─── */}
        <Section
          id="roots"
          number="2"
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
              <span className="font-medium text-ink">arḥām</span> (wombs, 2:228)
              preserves this concrete sense. Understanding the root's origin
              transforms "mercy" from an abstract attribute into something
              visceral — a compassion as intimate as a mother's bond with the
              life she carries.
            </p>
          </Example>
        </Section>

        {/* ─── 3. Morphological Precision ─── */}
        <Section
          id="morphology"
          number="3"
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

          <Example label="Example · Root ع ل م (ʿ-l-m) — Three forms, three meanings">
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
                    to know. Appears in 96:5, <span className="italic">"taught the human what he did not know."</span>
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

        {/* ─── 4. Word-by-word alignment ─── */}
        <Section
          id="word-by-word"
          number="4"
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

          <Example label="Example · Verse 2:3, word 4">
            <div className="flex items-center gap-4 mb-3">
              <span dir="rtl" lang="ar" className="font-arabic text-2xl text-ink">ٱلصَّلَوٰةَ</span>
              <div>
                <p className="text-sm font-medium text-ink">aṣ-ṣalāh</p>
                <p className="text-xs text-ink-muted">Root: ص ل و (ṣ-l-w)</p>
              </div>
            </div>
            <p className="text-sm text-ink-secondary">
              Rather than splitting "establish prayer" across two words and
              "the prayer" across a third — causing meaning to bleed between
              neighbours — each word receives its own precise, non-overlapping
              gloss. The word <span className="font-medium text-ink">yaqīmūna</span> (يُقِيمُونَ)
              carries "establish" and <span className="font-medium text-ink">aṣ-ṣalāh</span> carries
              "the ṣalāh" — with the full verse translation providing the
              unified reading.
            </p>
          </Example>
        </Section>

        {/* ─── 5. Evidence hierarchy ─── */}
        <Section
          id="evidence"
          number="5"
          title="Evidence hierarchy"
          subtitle="When sources disagree, a clear priority determines the outcome."
        >
          <p>
            Not all evidence carries equal weight. Our translations follow a
            strict hierarchy:
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
                <p className="font-medium text-ink text-sm">Semitic cognate evidence</p>
                <p className="text-sm text-ink-secondary">
                  The etymological record confirms Quranic usage or
                  disambiguates rare words — but never overrides internal
                  evidence.
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <span className="shrink-0 w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold flex items-center justify-center">4</span>
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

        {/* ─── 6. Departure transparency ─── */}
        <Section
          id="departures"
          number="6"
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
