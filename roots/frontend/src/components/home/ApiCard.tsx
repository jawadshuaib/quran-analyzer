export default function ApiCard() {
  return (
    <a
      href="/developers"
      className="block bg-white border border-card-border rounded-xl p-4 mb-8 hover:border-gold/40 transition-colors"
    >
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-ink mb-1">Free public API</p>
          <p className="text-xs text-ink-secondary">
            Build your own tools on top of the corpus.
          </p>
        </div>
        <code className="hidden sm:block text-xs text-ink-secondary bg-cream-dark px-2.5 py-1.5 rounded-md whitespace-nowrap font-mono">
          GET /api/v1/verse/2:255
        </code>
      </div>
    </a>
  );
}
