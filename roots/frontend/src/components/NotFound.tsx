import { useSEO } from '../hooks/useSEO';

export default function NotFound() {
  useSEO({
    title: '404 — Page Not Found',
    description: 'The page you are looking for does not exist.',
    noindex: true,
  });
  return (
    <div className="mx-auto max-w-3xl px-4 py-10 flex-1 w-full text-center">
      <div className="py-20">
        <p className="text-8xl font-medium text-cream-dark mb-4 font-serif">404</p>
        <h1 className="font-serif text-[34px] font-medium tracking-tight leading-tight text-ink mb-2.5">
          Page not found
        </h1>
        <p className="text-[15px] text-ink-secondary mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <a
          href="/"
          className="inline-block rounded-lg bg-gold px-6 py-2.5 text-white font-medium hover:bg-gold-hover transition-colors text-sm"
        >
          Go Home
        </a>
      </div>
    </div>
  );
}
