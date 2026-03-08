export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col">
      <div className="mx-auto max-w-3xl px-4 py-10 flex-1 w-full text-center">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-stone-800 mb-2">
            <a href="/" className="hover:opacity-80 transition-opacity">The Quran Explorer</a>
          </h1>
        </header>

        <div className="py-20">
          <p className="text-8xl font-bold text-stone-200 mb-4">404</p>
          <p className="text-xl text-stone-600 mb-2">Page not found</p>
          <p className="text-stone-400 mb-8">
            The page you're looking for doesn't exist or has been moved.
          </p>
          <a
            href="/"
            className="inline-block rounded-lg bg-emerald-600 px-6 py-2.5 text-white font-medium hover:bg-emerald-700 transition-colors"
          >
            Go Home
          </a>
        </div>
      </div>
    </div>
  );
}
