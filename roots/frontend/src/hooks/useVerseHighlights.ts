import { useEffect, useMemo, useState } from 'react';
import {
  getHighlights,
  subscribeToHighlights,
  type Highlight,
  type HighlightColor,
} from '../utils/verse-highlights';

export interface PosHighlight {
  color: HighlightColor;
  id: string;
  /** First covered position (for anchoring the delete affordance). */
  start: number;
  /** Last covered position. */
  end: number;
}

/**
 * Subscribe to one verse's highlights and expose a position → highlight map
 * for rendering. The map lets a word-token renderer ask "is position N
 * highlighted, in what color, and is N the start of its highlight?" in O(1).
 */
export function useVerseHighlights(verseKey: string): {
  highlights: Highlight[];
  posMap: Map<number, PosHighlight>;
} {
  const [highlights, setHighlights] = useState<Highlight[]>(() => getHighlights(verseKey));

  useEffect(() => {
    const update = () => setHighlights(getHighlights(verseKey));
    update();
    return subscribeToHighlights(update);
  }, [verseKey]);

  const posMap = useMemo(() => {
    const m = new Map<number, PosHighlight>();
    for (const h of highlights) {
      for (let p = h.startPos; p <= h.endPos; p++) {
        m.set(p, { color: h.color, id: h.id, start: h.startPos, end: h.endPos });
      }
    }
    return m;
  }, [highlights]);

  return { highlights, posMap };
}
