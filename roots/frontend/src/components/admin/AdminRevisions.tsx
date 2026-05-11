/**
 * Admin: Revisions landing.
 *
 * Two cards link to the per-surface revision tools:
 *
 *   - Vocabulary  — root-level semantic surveys + bulk re-application
 *                   across word meanings, grammar notes, verse translations.
 *                   Targets ritualistic-narrowing roots and any root the
 *                   admin wants to apply Quran-only methodology to.
 *
 *   - Proper Nouns — detects proper-name calques (e.g. "Abu Lahab" left
 *                   as a transliteration when the underlying Arabic is
 *                   actually descriptive). Two-stage pipeline: Ollama
 *                   cloud filter → Claude Sonnet adjudication → admin
 *                   review queue.
 */
export default function AdminRevisions() {
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h1 className="text-xl font-semibold text-stone-800">Revisions</h1>
      </div>
      <p className="text-sm text-stone-500 mb-8 max-w-2xl">
        Tools for applying Quran-only methodology to translations. Each
        section identifies a different class of conventional-translation
        artifact, derives the canonical reading from corpus evidence, and
        bulk-applies revisions across reader-facing surfaces with one-click
        revert.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
        {/* Vocabulary card */}
        <a
          href="/admin/vocabulary"
          className="group block rounded-xl border border-stone-200 bg-white p-5 hover:border-amber-300 hover:bg-amber-50/30 transition-colors"
        >
          <div className="flex items-baseline justify-between mb-2">
            <h2 className="text-base font-semibold text-stone-800 group-hover:text-amber-700">
              Vocabulary
            </h2>
            <span className="text-xs text-stone-400 group-hover:text-amber-600">
              Per-root semantic survey →
            </span>
          </div>
          <p className="text-xs text-stone-500 leading-relaxed mb-3">
            Survey a Qur&apos;anic root for its abstract semantic core, then
            bulk-apply canonical revisions across translations, grammar
            notes, and word meanings. Each revision is reversible per row.
          </p>
          <div className="flex flex-wrap gap-1.5">
            <span className="text-[10px] text-stone-500 px-2 py-0.5 rounded-full bg-stone-100">
              Claude Opus survey
            </span>
            <span className="text-[10px] text-stone-500 px-2 py-0.5 rounded-full bg-stone-100">
              Sonnet revisions
            </span>
            <span className="text-[10px] text-stone-500 px-2 py-0.5 rounded-full bg-stone-100">
              4 surfaces
            </span>
          </div>
        </a>

        {/* Proper Nouns card */}
        <a
          href="/admin/proper-nouns"
          className="group block rounded-xl border border-stone-200 bg-white p-5 hover:border-amber-300 hover:bg-amber-50/30 transition-colors"
        >
          <div className="flex items-baseline justify-between mb-2">
            <h2 className="text-base font-semibold text-stone-800 group-hover:text-amber-700">
              Proper Nouns
            </h2>
            <span className="text-xs text-stone-400 group-hover:text-amber-600">
              Detect calques →
            </span>
          </div>
          <p className="text-xs text-stone-500 leading-relaxed mb-3">
            Find translations that treat descriptive Arabic phrases as
            proper names (e.g. &quot;Abu Lahab&quot; for{' '}
            <span className="font-arabic" lang="ar">أَبِي لَهَبٍ</span>
            {' '}— &quot;father of [burning] flame&quot;). Two-stage
            detection via Ollama cloud then adjudication by Claude
            Sonnet, with operator review queue.
          </p>
          <div className="flex flex-wrap gap-1.5">
            <span className="text-[10px] text-stone-500 px-2 py-0.5 rounded-full bg-stone-100">
              Mechanical pre-filter
            </span>
            <span className="text-[10px] text-stone-500 px-2 py-0.5 rounded-full bg-stone-100">
              Ollama Qwen 397B
            </span>
            <span className="text-[10px] text-stone-500 px-2 py-0.5 rounded-full bg-stone-100">
              Sonnet adjudicator
            </span>
          </div>
        </a>
      </div>
    </div>
  );
}
