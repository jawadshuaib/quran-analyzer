import type { ReactNode } from 'react';

/**
 * Small metadata pills for the saved word/root cards. Tones are lifted from
 * the tints those data already use across the app (roots = emerald, word
 * meaning = violet, dictionary/frequency = amber, saved/verse = rose) so the
 * cards read as part of the existing system rather than a new vocabulary.
 */

type Tone = 'stone' | 'emerald' | 'violet' | 'amber' | 'rose';

const TONES: Record<Tone, string> = {
  stone: 'bg-stone-100 text-stone-500',
  emerald: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
  violet: 'bg-violet-100 text-violet-700',
  amber: 'bg-amber-50 text-amber-700 border border-amber-200/70',
  rose: 'bg-rose-50 text-rose-600 border border-rose-200/70',
};

export function MetaChip({
  tone = 'stone',
  icon,
  title,
  children,
}: {
  tone?: Tone;
  icon?: ReactNode;
  title?: string;
  children: ReactNode;
}) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${TONES[tone]}`}
    >
      {icon}
      {children}
    </span>
  );
}

/**
 * An emerald root chip that navigates to /root/<bw>. Rendered as a
 * `role="link"` span (NOT an <a>) because the saved card's content is already
 * an <a> — nested anchors are invalid. Mirrors the existing RootRefLink
 * pattern (stopPropagation so the chip wins over the card's own navigation).
 * In `inert` mode (the quick panel, whose row is a <button>) it renders the
 * same look without a handler — the whole row already navigates.
 */
export function RootLink({
  rootArabic,
  rootBuckwalter,
  inert = false,
}: {
  rootArabic?: string;
  rootBuckwalter: string;
  inert?: boolean;
}) {
  const body = (
    <>
      {rootArabic && (
        <span dir="rtl" lang="ar" className="font-arabic text-xs text-emerald-800">
          {rootArabic}
        </span>
      )}
      <span className="text-emerald-500">({rootBuckwalter})</span>
    </>
  );
  const cls =
    'inline-flex items-center gap-1 rounded-full bg-emerald-50 border border-emerald-200 px-2 py-0.5 text-[10px] font-medium text-emerald-700';
  if (inert) return <span className={cls}>{body}</span>;
  return (
    <span
      role="link"
      tabIndex={0}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
        window.location.href = `/root/${encodeURIComponent(rootBuckwalter)}`;
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          e.stopPropagation();
          window.location.href = `/root/${encodeURIComponent(rootBuckwalter)}`;
        }
      }}
      className={`${cls} hover:bg-emerald-100 transition-colors cursor-pointer`}
    >
      {body}
    </span>
  );
}
