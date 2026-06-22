import { useState, useId } from 'react';
import type { PoetryQuotedLine } from '../types';

/**
 * An inline pre-Islamic poetry quote, rendered amid the prose of a root- or
 * verse-level note. The note's markdown carries `[[q:<line_root_id>|<arabic>]]`
 * markers (injected around the poet's own words); FormattedText turns each into
 * one of these.
 *
 * The reader sees only the short Arabic fragment, dotted-underlined in amber so
 * it never reads as Qurʾān. Hovering reveals the full line, the poet, and a
 * translation; clicking opens the whole poem with this line highlighted. The
 * full bayt is deliberately NOT shown inline — a layperson could mistake a
 * standalone Arabic line for revelation.
 */
export default function PoetryQuote({
  q,
  text,
}: {
  q: PoetryQuotedLine;
  text: string;
}) {
  const [open, setOpen] = useState(false);
  const tipId = useId();
  const href =
    q.poem_id != null
      ? `/poem/${q.poem_id}${q.line_no != null ? `#line-${q.line_no}` : ''}`
      : undefined;

  return (
    <span
      className="relative inline-block align-baseline"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <a
        href={href}
        lang="ar"
        dir="rtl"
        aria-describedby={open ? tipId : undefined}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        className="font-arabic text-amber-800 decoration-amber-400 decoration-dotted underline underline-offset-4 hover:text-amber-900 hover:decoration-amber-600 cursor-pointer"
      >
        {text}
      </a>

      {open && (
        <span
          id={tipId}
          role="tooltip"
          className="absolute bottom-full left-1/2 z-30 mb-2 w-72 max-w-[80vw] -translate-x-1/2 rounded-lg border border-amber-200 bg-white p-3 text-left shadow-lg"
        >
          {q.poet && (
            <span dir="rtl" lang="ar" className="block font-arabic text-sm text-stone-700">
              {q.poet}
            </span>
          )}
          {q.arabic && (
            <span
              dir="rtl"
              lang="ar"
              className="mt-1 block font-arabic text-base leading-loose text-stone-800"
            >
              {q.arabic}
            </span>
          )}
          {q.english && (
            <span className="mt-1.5 block text-xs italic leading-snug text-stone-500">
              {q.english}
            </span>
          )}
          <span className="mt-2 block text-[10px] uppercase tracking-wide text-amber-600">
            Pre-Islamic poetry — tap to read the full poem
          </span>
          {/* little pointer */}
          <span className="absolute left-1/2 top-full -translate-x-1/2 -translate-y-px border-4 border-transparent border-t-white" />
        </span>
      )}
    </span>
  );
}
