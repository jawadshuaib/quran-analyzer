import { useSEO } from '../hooks/useSEO';

/**
 * Site-wide Terms of Service. Written plainly — al-nuqta is a free,
 * non-commercial educational tool and the terms should reflect that.
 */
export default function TermsPage() {
  useSEO({
    title: 'Terms of Service',
    description: 'Terms of service for al-nuqta.com — permitted use, disclaimers, and scholarly caveats.',
    path: '/terms',
  });

  return (
    <div className="py-10">
      <div className="mx-auto max-w-3xl rounded-xl border border-card-border bg-white px-6 py-8 shadow-sm sm:px-8">
        <header className="mb-8 text-center">
          <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3.5">Terms</p>
          <h1 className="font-serif text-[34px] font-medium tracking-tight leading-tight text-ink mb-2.5">
            Terms of Service
          </h1>
          <p className="text-[15px] text-ink-secondary">Last updated: April 22, 2026</p>
        </header>

        <section className="mb-6 space-y-3 text-sm leading-7 text-stone-700">
          <p>
            These terms apply to anyone using <strong>al-nuqta.com</strong> and its related
            services (the "Service"). By using the Service you agree to these terms. If you
            don't agree, please stop using the Service.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">What al-nuqta is</h2>
          <p className="text-sm leading-7 text-stone-700">
            al-nuqta is a free, non-commercial Quran research tool. It offers morphological
            analysis, root-word tracing, Semitic cognate data, AI-assisted translation notes,
            AI-assisted grammar notes, and related study aids. It is not a substitute for
            traditional scholarly study.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Permitted use</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>Personal study, research, and educational use is welcome and encouraged.</li>
            <li>You may reference the Service, link to specific pages, and share short excerpts
                for academic or religious discussion.</li>
            <li>
              The public API at <code>/api/v1</code> is intended for non-commercial integrations.
              Please respect rate limits and cache where possible. If you plan heavy or
              commercial use, contact the maintainer first.
            </li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Prohibited use</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>Do not attempt to disrupt the Service, overwhelm the API, or circumvent rate limits.</li>
            <li>Do not republish bulk portions of the Service's derived analysis (AI translations,
                grammar notes, etc.) as though they were your own scholarship. Attribution and
                linking is fine; reposting without context is not.</li>
            <li>Do not use the Service to generate content that misrepresents the Quran, spreads
                hateful material, or targets any group for harm.</li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Content &amp; intellectual property</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>
              <strong>Quranic text.</strong> The Quranic Arabic text is in the public domain.
              al-nuqta asserts no ownership over it.
            </li>
            <li>
              <strong>Conventional translations.</strong> Third-party English translations displayed
              on the site are used under the terms of their respective licenses and are credited
              where they appear.
            </li>
            <li>
              <strong>Original content.</strong> AI-generated translation notes, grammar notes,
              term glossary entries, and root-based analyses are produced by this project.
              You may quote them with attribution for non-commercial educational purposes.
            </li>
            <li>
              <strong>Code.</strong> The source code for al-nuqta is available at the GitHub
              repository linked in the site footer. Refer to the repository for its license.
            </li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">AI-generated content disclaimer</h2>
          <p className="text-sm leading-7 text-stone-700">
            The Service uses large language models (Anthropic Claude, Ollama-hosted open models) to
            produce translation notes, grammar commentary, and "Ask the Quran" responses. These
            outputs are generated mechanically and may contain errors, mistranslations, or
            interpretive choices that traditional scholarship would dispute. Treat them as
            starting points for your own study, not as authoritative rulings. The Service does
            not issue religious verdicts (fatwas) and should not be used as a basis for legal,
            medical, or spiritual decisions without human expert review.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">No warranty</h2>
          <p className="text-sm leading-7 text-stone-700">
            The Service is provided <strong>as is</strong>, without warranty of any kind — express
            or implied — including accuracy, fitness for a particular purpose, or uninterrupted
            availability. The maintainer is not liable for any loss or damage arising from your
            use of the Service.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Changes to the Service and terms</h2>
          <p className="text-sm leading-7 text-stone-700">
            The Service is under active development. Features may change, be removed, or require
            updates without notice. These terms may be revised — the "Last updated" date at the
            top of this page reflects the most recent version. Continued use of the Service after
            a revision constitutes acceptance of the updated terms.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Contact</h2>
          <p className="text-sm leading-7 text-stone-700">
            Questions about these terms can be directed to the maintainer via the project's
            GitHub repository linked in the site footer.
          </p>
        </section>
      </div>
    </div>
  );
}
