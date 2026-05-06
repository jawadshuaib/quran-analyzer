import { useState } from 'react';
import AskAssistant from '../AskAssistant';
import { buildVerseContext } from '../../utils/context-builders';

interface Props {
  surah: number;
  /** The verse the user is most-focused on right now (most-visible). */
  anchor: number;
}

/**
 * Reader-page "Ask the Quran" launcher.
 *
 * Lives at the bottom-right of /read/<surah>. While the user scrolls,
 * we render a custom pill that previews the *current* anchor verse
 * ("Ask about 25:7"). The first click freezes that anchor and mounts
 * AskAssistant in opened state with `pageKey='<surah>:<anchor>'` —
 * exactly the same shape as the verse-detail page would have used,
 * so the resulting Q&A appears in the verse's shared history and
 * gets the same insight-evaluation treatment.
 *
 * Once frozen, the anchor stays for the rest of the page session: the
 * user can close and re-open the panel and it stays on the same
 * verse. To re-anchor they refresh. This keeps the pageKey stable
 * across the conversation thread without us needing to build a
 * re-anchor mid-conversation flow.
 *
 * Nothing-on-screen edge case (initial mount, fast scroll): the pill
 * is hidden until at least one verse meets the visibility threshold.
 */
export default function ReaderAsk({ surah, anchor }: Props) {
  const [snapshotAnchor, setSnapshotAnchor] = useState<number | null>(null);

  // Once anchor is locked, AskAssistant takes over and renders its
  // own floating button. We just hand it the frozen verse number.
  if (snapshotAnchor !== null) {
    return (
      <AskAssistant
        pageType="verse"
        pageKey={`${surah}:${snapshotAnchor}`}
        defaultOpen
        contextGatherer={() => buildVerseContext(surah, snapshotAnchor)}
      />
    );
  }

  // No snapshot yet — show a live-preview pill if we have a sensible
  // anchor.
  if (anchor <= 0) return null;

  const verseLabel = `${surah}:${anchor}`;

  function handleClick() {
    setSnapshotAnchor(anchor);
  }

  return (
    <button
      onClick={handleClick}
      className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full
                 bg-violet-600 text-white shadow-lg shadow-violet-200
                 hover:bg-violet-700 hover:shadow-xl hover:shadow-violet-300
                 transition-all duration-200
                 px-4 py-3 sm:px-5 sm:py-3.5 max-w-[calc(100vw-3rem)]"
      title={`Ask the Quran about ${verseLabel}`}
    >
      <svg className="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
        />
      </svg>
      <span className="text-sm font-medium hidden sm:inline truncate">
        Ask about {verseLabel}
      </span>
      <span className="text-sm font-medium sm:hidden truncate">
        Ask {verseLabel}
      </span>
    </button>
  );
}
