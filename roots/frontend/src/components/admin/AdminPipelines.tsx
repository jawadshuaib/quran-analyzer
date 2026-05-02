/**
 * Pipelines hub — top-level admin section.
 *
 * Both pipeline families share the same lifecycle (configure → generate
 * candidates → render → upload to YouTube), so they live together as a
 * standalone admin section instead of being nested under "Media".
 *
 * Card pattern is identical to AdminMedia / Dashboard so the visual
 * weight of each entry feels the same. Scheduling for both families
 * lives at /admin/scheduler — surfaced via a callout below the grid.
 */
const card =
  'block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all';

export default function AdminPipelines() {
  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-2">Pipelines</h1>
      <p className="text-sm text-stone-500 mb-8">
        Automated YouTube Shorts generators. Pick the series to configure
        pipelines, browse candidates, and review rendered videos. Upload
        cadence for every pipeline below is controlled from{' '}
        <a
          href="/admin/scheduler"
          className="underline decoration-dotted underline-offset-2 hover:text-stone-700"
        >
          Scheduler
        </a>
        .
      </p>

      {/* Recitation pipelines — English + Arabic share the same backend
          (admin_pipeline_videos / admin_pipelines) and the same UI
          (PipelineManager); the lang query param picks which one. */}
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-3">
        Recitation
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <a href="/admin/pipelines/recitation?lang=english" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">English Pipeline</h3>
          <p className="text-sm text-stone-500">
            Automated YouTube Shorts with AI-selected verses, polished
            English TTS, and auto-generated metadata.
          </p>
        </a>
        <a href="/admin/pipelines/recitation?lang=arabic" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Arabic Pipeline</h3>
          <p className="text-sm text-stone-500">
            Arabic recitation shorts with on-screen English translation.
            Passages capped at 55 seconds for copyright safety.
          </p>
        </a>
      </div>

      {/* Educational pipelines — three series (word origins, translation
          hides, grammar insights) sharing one candidate→script→render→
          upload flow. */}
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-3">
        Educational
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <a href="/admin/pipelines/educational" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Pipelines (configured runs)</h3>
          <p className="text-sm text-stone-500">
            Configure named pipelines (voice, format, dim, music), run
            them on demand, and review rendered videos with per-row
            YouTube upload + stats.
          </p>
        </a>
        <a href="/admin/pipelines/educational/candidates" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Candidates &amp; manual generation</h3>
          <p className="text-sm text-stone-500">
            Browse the candidate pool for each series, queue verses,
            generate scripts, and render videos by hand.
          </p>
        </a>
      </div>

      {/* Cross-link to the scheduler — closes the loop on "I configured
          a pipeline, where do I set it to run?" */}
      <div className="rounded-xl border border-stone-200 bg-stone-50 p-5">
        <h3 className="font-semibold text-stone-800 mb-1">Scheduling &amp; uploads</h3>
        <p className="text-sm text-stone-600 mb-3">
          All pipeline schedules and YouTube auto-upload settings are
          managed in one place to avoid drift between recitation and
          educational. Daily fire times, grace windows, daily caps, and
          the YouTube upload schedule (which drains both pipelines)
          live there.
        </p>
        <a
          href="/admin/scheduler"
          className="inline-block px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700"
        >
          Open Scheduler →
        </a>
      </div>
    </div>
  );
}
