import { useSEO } from '../hooks/useSEO';
import VerseOfTheDay from './home/VerseOfTheDay';

export default function BadGateway() {
  useSEO({
    title: '502 — Server Unavailable',
    description: 'The al-nuqta server is temporarily unavailable.',
    noindex: true,
  });

  function handleRetry() {
    // Honor the page they actually wanted; if they landed on /502
    // directly, sending them home is the next-best move.
    if (window.location.pathname === '/502') {
      window.location.href = '/';
    } else {
      window.location.reload();
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 flex-1 w-full">
      <div className="text-center pt-10 pb-8">
        <p className="text-7xl sm:text-8xl font-medium text-cream-dark mb-3 font-serif">502</p>
        <h1 className="font-serif text-[28px] sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-2.5">
          Server is taking a breath
        </h1>
        <p className="text-[15px] text-ink-secondary mb-6 max-w-lg mx-auto">
          The al-nuqta server is temporarily unavailable. This is usually
          a brief hiccup — try again in a moment. While you wait, here's
          a verse to sit with.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 mb-10">
          <button
            onClick={handleRetry}
            className="inline-block rounded-lg bg-gold px-6 py-2.5 text-white font-medium hover:bg-gold-hover transition-colors text-sm cursor-pointer"
          >
            Try again
          </button>
          <a
            href="/"
            className="inline-block rounded-lg border border-card-border px-6 py-2.5 text-ink-secondary hover:border-gold hover:text-gold transition-colors text-sm"
          >
            Go home
          </a>
        </div>
      </div>
      {/* Verse-of-the-day silently renders nothing if the API call fails,
          so this stays graceful when the backend really is down. When
          the user just navigates to /502 directly to preview the page,
          they get a real verse. */}
      <VerseOfTheDay
        onNavigate={(s, a) => { window.location.href = `/verse/${s}:${a}`; }}
      />
    </div>
  );
}
