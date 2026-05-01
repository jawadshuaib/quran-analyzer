const card = "block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all";

export default function AdminMedia() {
  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-2">Media</h1>
      <p className="text-sm text-stone-500 mb-8">Tools for creating media content.</p>

      {/* Assets */}
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-3">Assets</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <a href="/admin/media/resources" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Background Videos</h3>
          <p className="text-sm text-stone-500">Upload and manage MP4 background videos for generated content.</p>
        </a>
        <a href="/admin/media/music" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Background Music</h3>
          <p className="text-sm text-stone-500">Upload audio tracks to use as subtle background music in videos.</p>
        </a>
      </div>

      {/* Verse Recitations */}
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-3">Verse Recitations</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <a href="/admin/media/recitations" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Verse Recitations</h3>
          <p className="text-sm text-stone-500">Preview recitations with spoken translation and cache TTS audio.</p>
        </a>
        <a href="/admin/media/generate" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Generate Verse Recitation Video</h3>
          <p className="text-sm text-stone-500">Combine background video, recitation, and translation into a final video.</p>
        </a>
      </div>

      {/* Verse Explanations */}
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-3">Verse Explanations</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <a href="/admin/media/explanations" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Verse Explanations</h3>
          <p className="text-sm text-stone-500">Curate thematic verse groups with transitions and closing reflections.</p>
        </a>
        <a href="/admin/media/generate-explanation" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Generate Explanation Video</h3>
          <p className="text-sm text-stone-500">Create videos from saved verse explanations with background and music.</p>
        </a>
      </div>

      {/* Pipelines */}
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-3">Pipelines</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-8">
        <a href="/admin/media/pipelines?lang=english" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">English Pipeline</h3>
          <p className="text-sm text-stone-500">Automated YouTube Shorts with AI-selected verses, polished English TTS, and auto-generated metadata.</p>
        </a>
        <a href="/admin/media/pipelines?lang=arabic" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Arabic Pipeline</h3>
          <p className="text-sm text-stone-500">Arabic recitation shorts with on-screen English translation. Passages capped at 55 seconds for copyright safety.</p>
        </a>
      </div>

      {/* Educational pipeline — different shape from recitation pipelines:
          three sub-types (word origins, translation hides, grammar
          insights) sharing one candidate→script→render→upload flow. */}
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-400 mb-3">Educational Pipeline</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <a href="/admin/media/educational" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Candidates & manual generation</h3>
          <p className="text-sm text-stone-500">Browse the candidate pool for each series, queue verses, generate scripts, and render videos by hand.</p>
        </a>
        <a href="/admin/media/educational/pipelines" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Pipelines (automated)</h3>
          <p className="text-sm text-stone-500">Configure named pipelines (voice, format, dim, music) and run them on demand. Scheduling lands in the next iteration.</p>
        </a>
      </div>
    </div>
  );
}
