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
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <a href="/admin/media/explanations" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Verse Explanations</h3>
          <p className="text-sm text-stone-500">Curate thematic verse groups with transitions and closing reflections.</p>
        </a>
        <a href="/admin/media/generate-explanation" className={card}>
          <h3 className="font-semibold text-stone-800 mb-1">Generate Explanation Video</h3>
          <p className="text-sm text-stone-500">Create videos from saved verse explanations with background and music.</p>
        </a>
      </div>
    </div>
  );
}
