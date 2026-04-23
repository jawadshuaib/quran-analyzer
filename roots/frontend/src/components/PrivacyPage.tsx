import { useSEO } from '../hooks/useSEO';

/**
 * Site-wide privacy policy. Written to be honest and specific rather than
 * boilerplate — al-nuqta is a non-commercial Quran research tool and the
 * policy reflects that.
 */
export default function PrivacyPage() {
  useSEO({
    title: 'Privacy Policy',
    description: 'Privacy policy for al-nuqta.com — what data we collect, what we don\'t, and how we handle it.',
    path: '/privacy',
  });

  return (
    <div className="py-10">
      <div className="mx-auto max-w-3xl rounded-xl border border-card-border bg-white px-6 py-8 shadow-sm sm:px-8">
        <header className="mb-8 text-center">
          <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3.5">Privacy</p>
          <h1 className="font-serif text-[34px] font-medium tracking-tight leading-tight text-ink mb-2.5">
            Privacy Policy
          </h1>
          <p className="text-[15px] text-ink-secondary">Last updated: April 22, 2026</p>
        </header>

        <section className="mb-6 space-y-3 text-sm leading-7 text-stone-700">
          <p>
            This policy applies to <strong>al-nuqta.com</strong> and the services hosted on it.
            al-nuqta is a non-commercial Quran research tool maintained by a single operator. We do
            not sell data, we do not run advertising, and we do not use third-party analytics.
          </p>
          <p>
            The Chrome extension has its own policy at{' '}
            <a href="/privacy/extension" className="text-emerald-700 underline hover:text-emerald-800">
              /privacy/extension
            </a>.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">What we do NOT collect</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>We do not use Google Analytics, Facebook Pixel, or any third-party tracker.</li>
            <li>We do not set cookies for advertising or cross-site tracking.</li>
            <li>We do not require account registration to read or search Quranic content.</li>
            <li>We do not collect your name, email, phone number, location, or any demographic data.</li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">What we do collect</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>
              <strong>Server access logs.</strong> Our hosting infrastructure logs incoming HTTP
              requests — including IP address, user agent, and requested URL — for security and
              abuse prevention. These logs are rotated and not shared with third parties.
            </li>
            <li>
              <strong>Local browser storage.</strong> We use your browser's <code>localStorage</code>{' '}
              to remember your UI preferences (open/closed sections, saved verses for reference).
              This data never leaves your device.
            </li>
            <li>
              <strong>Questions you submit to "Ask the Quran".</strong> If you use this optional
              feature, your question is forwarded to Anthropic's Claude API to generate a
              response. The question, the returned response, and a session ID are stored on our
              server to enable your question history on the page and to enforce free-tier limits.
              No IP address, user identity, or device information is attached.
            </li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Third-party services</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>
              <strong>Anthropic (Claude API)</strong> — processes "Ask the Quran" questions. See{' '}
              <a href="https://www.anthropic.com/legal/privacy" target="_blank" rel="noopener noreferrer"
                 className="text-emerald-700 underline hover:text-emerald-800">
                Anthropic's privacy policy
              </a>.
            </li>
            <li>
              <strong>Google Fonts</strong> — used for the Arabic serif font. Loaded from Google's CDN.
            </li>
            <li>
              <strong>Quran.com audio CDN</strong> — served when a user plays a recitation. We do
              not embed Quran.com analytics; audio is served from their static file hosts.
            </li>
          </ul>
          <p className="mt-3 text-sm leading-7 text-stone-700">
            We have no other third-party integrations on user-facing pages.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Children's privacy</h2>
          <p className="text-sm leading-7 text-stone-700">
            The site does not knowingly target children under 13. It does not include registration,
            comments, messaging, or social features that would collect information from children.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Data retention and deletion</h2>
          <p className="text-sm leading-7 text-stone-700">
            "Ask the Quran" question history is stored on the server indefinitely but is only
            accessible via your session ID (which is generated per device and stored in your
            browser's <code>localStorage</code>). Clearing your browser storage effectively
            disassociates you from your history. Server access logs are rotated on a rolling
            basis by our hosting provider.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Changes to this policy</h2>
          <p className="text-sm leading-7 text-stone-700">
            If this policy changes, the "Last updated" date above will reflect the new revision.
            Material changes will be noted in a brief changelog at the bottom of this page.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Contact</h2>
          <p className="text-sm leading-7 text-stone-700">
            Questions about this policy can be directed to the maintainer via the project's
            GitHub repository linked in the site footer.
          </p>
        </section>
      </div>
    </div>
  );
}
