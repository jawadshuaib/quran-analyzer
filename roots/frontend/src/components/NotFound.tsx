import { useSEO } from '../hooks/useSEO';
import VerseOfTheDay from './home/VerseOfTheDay';

export default function NotFound() {
  useSEO({
    title: '404 — Page Not Found',
    description: 'The page you are looking for does not exist.',
    noindex: true,
  });
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 flex-1 w-full">
      <div className="text-center pt-10 pb-8">
        <p className="text-7xl sm:text-8xl font-medium text-cream-dark mb-3 font-serif">404</p>
        <h1 className="font-serif text-[28px] sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-2.5">
          This page wandered off
        </h1>
        <p className="text-[15px] text-ink-secondary mb-6 max-w-lg mx-auto">
          The page you were looking for doesn't exist or has moved. While
          you're here — a verse to take with you.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-3 mb-10">
          <a
            href="/"
            className="inline-block rounded-lg bg-gold px-6 py-2.5 text-white font-medium hover:bg-gold-hover transition-colors text-sm"
          >
            Go home
          </a>
          <a
            href="/read/1"
            className="inline-block rounded-lg border border-card-border px-6 py-2.5 text-ink-secondary hover:border-gold hover:text-gold transition-colors text-sm"
          >
            Read Al-Fatihah
          </a>
        </div>
      </div>
      <VerseOfTheDay
        onNavigate={(s, a) => { window.location.href = `/verse/${s}:${a}`; }}
      />
    </div>
  );
}
