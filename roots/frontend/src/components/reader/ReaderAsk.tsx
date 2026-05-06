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
 * ("Ask about 25:7"). Clicking the pill snapshots that verse, opens
 * AskAssistant against it, and pageKey='<surah>:<anchor>' is keyed
 * identically to the verse-detail page — so the resulting Q&A appears
 * in the verse's shared history and runs through the same insight-
 * evaluation pipeline.
 *
 * The pill / panel cycle:
 *   - Closed → live pill, label updates as user scrolls.
 *   - Click pill → re-anchor to current visible verse, open panel.
 *   - Close panel (X) → revert to live pill, conversation state
 *     persists in the still-mounted AskAssistant, so re-clicking
 *     the pill (with the same anchor still visible) resumes the
 *     thread. Scrolling to a different verse and clicking the pill
 *     starts a fresh thread anchored to the newly-visible verse.
 *
 * Nothing-on-screen edge case (initial mount, fast scroll): the pill
 * is hidden until at least one verse meets the visibility threshold.
 */
export default function ReaderAsk({ surah, anchor }: Props) {
  // Anchor of the most-recent open. Stays set after close so a
  // quick "close, change my mind, re-open" preserves the thread.
  const [snapshotAnchor, setSnapshotAnchor] = useState<number | null>(null);
  // Controlled open state for AskAssistant — lets us flip back to
  // our pill whenever the panel is closed.
  const [panelOpen, setPanelOpen] = useState(false);

  function handlePillClick() {
    // Re-anchor to whatever's most visible *now*. If this matches the
    // last snapshot, AskAssistant's pageKey stays the same and the
    // existing conversation continues. If it differs, AskAssistant's
    // pageType/pageKey effect wipes the thread for a fresh start.
    setSnapshotAnchor(anchor);
    setPanelOpen(true);
  }

  const verseLabel = anchor > 0 ? `${surah}:${anchor}` : '';
  const showPill = !panelOpen && anchor > 0;

  return (
    <>
      {snapshotAnchor !== null && (
        <AskAssistant
          pageType="verse"
          pageKey={`${surah}:${snapshotAnchor}`}
          contextGatherer={() => buildVerseContext(surah, snapshotAnchor)}
          isOpen={panelOpen}
          onOpenChange={setPanelOpen}
        />
      )}
      {showPill && (
        <button
          onClick={handlePillClick}
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
      )}
    </>
  );
}
