export default function AdminMedia() {
  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-2">Media</h1>
      <p className="text-sm text-stone-500 mb-6">Tools for creating media content.</p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <a
          href="/admin/media/recitations"
          className="block p-5 rounded-xl border border-stone-200 bg-white hover:border-stone-400 hover:shadow-sm transition-all"
        >
          <h2 className="font-semibold text-stone-800 mb-1">Verse Recitations</h2>
          <p className="text-sm text-stone-500">
            Generate YouTube Shorts with Quran recitation and spoken translation.
          </p>
        </a>
      </div>
    </div>
  );
}
