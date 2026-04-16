export default function AdminMedia() {
  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-2">Media</h1>
      <p className="text-sm text-stone-500 mb-6">Tools for creating media content.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <a
          href="/admin/media/recitations"
          className="block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all"
        >
          <h2 className="font-semibold text-stone-800 mb-1">Verse Recitations</h2>
          <p className="text-sm text-stone-500">
            Preview recitations with spoken translation and cache TTS audio.
          </p>
        </a>
        <a
          href="/admin/media/resources"
          className="block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all"
        >
          <h2 className="font-semibold text-stone-800 mb-1">Background Videos</h2>
          <p className="text-sm text-stone-500">
            Upload and manage MP4 background videos for generated content.
          </p>
        </a>
        <a
          href="/admin/media/music"
          className="block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all"
        >
          <h2 className="font-semibold text-stone-800 mb-1">Background Music</h2>
          <p className="text-sm text-stone-500">
            Upload audio tracks to use as subtle background music in videos.
          </p>
        </a>
        <a
          href="/admin/media/generate"
          className="block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all"
        >
          <h2 className="font-semibold text-stone-800 mb-1">Generate Video</h2>
          <p className="text-sm text-stone-500">
            Combine background video, recitation, and translation into a final video.
          </p>
        </a>
        <a
          href="/admin/media/explanations"
          className="block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all"
        >
          <h2 className="font-semibold text-stone-800 mb-1">Verse Explanations</h2>
          <p className="text-sm text-stone-500">
            Curate thematic verse groups with transitions and closing reflections.
          </p>
        </a>
        <a
          href="/admin/media/generate-explanation"
          className="block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all"
        >
          <h2 className="font-semibold text-stone-800 mb-1">Generate Explanation Video</h2>
          <p className="text-sm text-stone-500">
            Create videos from saved verse explanations with background and music.
          </p>
        </a>
      </div>
    </div>
  );
}
