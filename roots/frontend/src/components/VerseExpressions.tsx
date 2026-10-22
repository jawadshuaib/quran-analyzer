import { useId } from 'react';
import type { VerseExpression } from '../types';
import { setWordHover, clearWordHover } from '../utils/word-hover';

/**
 * "Expressions in this verse": the /expressions entries that draw on a verse,
 * each linking to its page. Pointing at one marks its words in the verse
 * (the span comes from the API; wide or unplaceable ones mark nothing).
 *
 * Most verses have none, so this renders nothing then, and stays quiet
 * otherwise: no card, just a small heading over a short list.
 */
export default function VerseExpressions({
  items,
  verseKey,
  variant = 'research',
}: {
  items?: VerseExpression[];
  verseKey: string;
  /** 'reader' matches the reader's notes panel headings and ink colours. */
  variant?: 'research' | 'reader';
}) {
  if (!items?.length) return null;
  const reader = variant === 'reader';
  return (
    <div className={reader ? '' : 'mt-4 border-t border-stone-100 pt-3'}>
      <h4
        className={
          reader
            ? 'text-[11px] uppercase tracking-wide font-medium text-gold mb-1.5'
            : 'text-xs font-medium text-stone-500 mb-1.5'
        }
      >
        {items.length === 1 ? 'Expression in this verse' : 'Expressions in this verse'}
      </h4>
      <ul className="space-y-1.5">
        {items.map((e) => (
          <ExpressionItem key={e.slug} e={e} verseKey={verseKey} reader={reader} />
        ))}
      </ul>
    </div>
  );
}

function ExpressionItem({
  e,
  verseKey,
  reader,
}: {
  e: VerseExpression;
  verseKey: string;
  reader: boolean;
}) {
  // Several items may mark overlapping words; the owner keeps one item's
  // mouse-out from clearing a mark the next item has already claimed.
  const owner = useId();
  const canMark = e.start != null && e.end != null;
  const claim = () => {
    if (canMark) setWordHover({ verseKey, start: e.start!, end: e.end! }, owner);
  };
  const release = () => clearWordHover(owner);
  return (
    <li>
      <a
        href={`/expressions/${e.slug}`}
        onMouseEnter={claim}
        onMouseLeave={release}
        onFocus={claim}
        onBlur={release}
        className="group block rounded-md -mx-1.5 px-1.5 py-0.5 transition-colors hover:bg-stone-50"
      >
        <span className="flex flex-wrap items-baseline gap-x-2">
          <span
            dir="rtl"
            lang="ar"
            className={`font-arabic text-lg leading-[1.8] ${reader ? 'text-ink' : 'text-stone-800'}`}
          >
            {e.expression_ar}
          </span>
          <span
            className={`text-sm group-hover:text-gold-hover ${reader ? 'text-ink-secondary' : 'text-stone-700'}`}
          >
            {e.title}
          </span>
          <span className="text-[11px] text-stone-400">
            {e.kind_label}
            {e.verse_count > 1 && ` · ${e.verse_count} verses`}
          </span>
        </span>
        {e.role && (
          <span className="block line-clamp-2 text-xs leading-relaxed text-stone-500">{e.role}</span>
        )}
      </a>
    </li>
  );
}
