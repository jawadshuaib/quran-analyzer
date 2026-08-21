import { useState } from 'react';
import type { SessionQAEntry } from '../../api/assistant';
import FormattedText from '../FormattedText';
import { linkifyGrammarTermRefs } from '../../utils/grammar-term-refs';
import { useGrammarTermsIfMentioned } from '../../hooks/useGrammarTerms';

interface Props {
  /** The user's own Ask-the-Quran Q&A for this verse, newest first. */
  items: SessionQAEntry[];
}

/**
 * The user's Ask-the-Quran answers, rendered under their verse on the /saved
 * page — an AI-produced counterpart to the personal note. Indigo accent (vs
 * the note's violet) + a small "AI" chip so the two never blur together.
 * Answers collapse behind their question line; FormattedText gives the same
 * verse-ref/root auto-linking as exegesis.
 */
export default function VerseQABlock({ items }: Props) {
  const [openId, setOpenId] = useState<number | null>(null);
  // An answer can name a grammar term ("Form III", "khabar") with nothing to
  // explain it — same glossary tooltip as everywhere else.
  const grammarTerms = useGrammarTermsIfMentioned(items.map((qa) => qa.answer));

  if (items.length === 0) return null;

  return (
    <div className="mt-2 rounded-md border-l-2 border-indigo-300 bg-indigo-50/50 px-2.5 py-1.5">
      <div className="mb-0.5 flex items-center gap-1.5">
        <svg viewBox="0 0 16 16" className="h-3 w-3 text-indigo-400" fill="currentColor" aria-hidden>
          <path d="M8 1.5a6.5 6.5 0 00-6.5 6.5c0 1.42.46 2.73 1.23 3.8L2 14.5l2.87-.68A6.5 6.5 0 108 1.5zm-.75 3.75a.75.75 0 011.5 0v.5a.75.75 0 01-1.5 0v-.5zM8 7a.75.75 0 01.75.75v3a.75.75 0 01-1.5 0v-3A.75.75 0 018 7z" />
        </svg>
        <span className="text-[10px] font-semibold uppercase tracking-wide text-indigo-500/90">
          Ask the Quran
        </span>
        <span className="rounded-full bg-indigo-100 px-1.5 py-px text-[9px] font-bold text-indigo-600">
          AI
        </span>
        {items.length > 1 && (
          <span className="text-[10px] text-stone-400">{items.length}</span>
        )}
      </div>
      <ul className="divide-y divide-indigo-100/70">
        {items.map((qa) => {
          const open = openId === qa.id;
          return (
            <li key={qa.id}>
              <button
                type="button"
                onClick={() => setOpenId(open ? null : qa.id)}
                aria-expanded={open}
                className="flex w-full items-start gap-1.5 py-1.5 text-left cursor-pointer group/qa"
              >
                <svg
                  viewBox="0 0 20 20"
                  className={`mt-0.5 h-3 w-3 shrink-0 text-indigo-300 transition-transform ${open ? 'rotate-90' : ''}`}
                  fill="currentColor"
                >
                  <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
                </svg>
                <span
                  className={`flex-1 min-w-0 text-xs leading-relaxed text-stone-700 group-hover/qa:text-stone-900 ${
                    open ? 'font-medium' : ''
                  }`}
                >
                  {qa.question}
                </span>
              </button>
              {open && (
                <div className="pb-2 pl-[18px] text-xs leading-relaxed text-stone-600">
                  <FormattedText
                    text={linkifyGrammarTermRefs(qa.answer)}
                    grammarTerms={grammarTerms ?? undefined}
                  />
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
