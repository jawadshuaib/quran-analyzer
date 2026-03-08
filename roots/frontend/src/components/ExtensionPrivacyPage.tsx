export default function ExtensionPrivacyPage() {
  return (
    <div className="min-h-screen bg-stone-50 py-10">
      <div className="mx-auto max-w-3xl rounded-xl border border-stone-200 bg-white px-6 py-8 shadow-sm sm:px-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-stone-900">Chrome Extension Privacy Policy</h1>
          <p className="mt-2 text-sm text-stone-500">Last updated: March 8, 2026</p>
        </header>

        <section className="mb-6 space-y-3 text-sm leading-7 text-stone-700">
          <p>
            This policy applies to the <strong>Quran Research Tool</strong> Chrome extension.
            The extension helps users analyze Quranic text on supported Quran-focused websites.
          </p>
          <p>
            If you have questions about this policy, contact the publisher through the project repository.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">What the extension accesses</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>Page text on supported domains to detect Quranic Arabic words and verses.</li>
            <li>The URL of your active tab to infer a verse reference when available.</li>
            <li>Metadata needed to display morphology, roots, and related verse information.</li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">How data is used</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>Detection and highlighting runs locally in your browser.</li>
            <li>
              The extension sends verse identifiers (for example, <code>2:255</code>) to the API at
              <code> al-nuqta.com</code> to fetch analysis data.
            </li>
            <li>The extension does not require account login.</li>
          </ul>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Data sharing and selling</h2>
          <p className="text-sm leading-7 text-stone-700">
            We do not sell personal data. We do not share browsing data with data brokers.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Data retention</h2>
          <p className="text-sm leading-7 text-stone-700">
            The extension does not create a user account database or profile store. Temporary in-memory
            caching may be used during active browsing sessions for performance.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Your controls</h2>
          <ul className="list-disc space-y-2 pl-6 text-sm leading-7 text-stone-700">
            <li>You can disable or remove the extension at any time from Chrome Extensions settings.</li>
            <li>You can clear browser data from Chrome settings.</li>
          </ul>
        </section>

        <section>
          <h2 className="mb-2 text-lg font-semibold text-stone-900">Policy updates</h2>
          <p className="text-sm leading-7 text-stone-700">
            We may update this policy to reflect product or compliance changes. Updates will be published on
            this page with a revised effective date.
          </p>
        </section>
      </div>
    </div>
  );
}
