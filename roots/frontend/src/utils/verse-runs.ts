import type { SavedItem } from './saved-items';

/** Largest ayah distance between two saved verses that still reads as one
 *  passage. 3 keeps "consecutive or semi-consecutive" runs together — 12:3,
 *  12:5, 12:6 is one passage — without chaining distant verses that merely
 *  share a surah. */
export const MAX_RUN_GAP = 3;

/** A stretch of saved verses close enough together to have been saved as one
 *  passage. `items.length === 1` means an ordinary standalone verse. */
export interface VerseRun {
  /** Stable React key. */
  key: string;
  surah: number;
  startAyah: number;
  endAyah: number;
  /** Always in ayah order — a passage should read top to bottom. */
  items: SavedItem[];
}

function parseRef(key: string): { surah: number; ayah: number } | null {
  const m = /^(\d+):(\d+)$/.exec(key);
  if (!m) return null;
  return { surah: Number(m[1]), ayah: Number(m[2]) };
}

/**
 * Group saved verses into runs of near-neighbours, so a folder shows the
 * passages the user actually collected rather than a flat list of refs.
 *
 * The caller's ordering is respected AT THE RUN LEVEL: each run takes the
 * position of its earliest member in `items`, so "recently saved" and "mushaf"
 * both still drive the sequence. Within a run, verses are always ascending —
 * that's the point of showing them as a passage.
 *
 * Verses whose key doesn't parse are returned as their own single-item runs,
 * never dropped.
 */
export function groupVersesByProximity(
  items: SavedItem[],
  maxGap: number = MAX_RUN_GAP,
): VerseRun[] {
  const order = new Map<SavedItem, number>();
  items.forEach((item, i) => order.set(item, i));

  const parsed: Array<{ item: SavedItem; surah: number; ayah: number }> = [];
  const unparsed: SavedItem[] = [];
  for (const item of items) {
    const ref = parseRef(item.key);
    if (ref) parsed.push({ item, ...ref });
    else unparsed.push(item);
  }

  // Adjacency only makes sense in mushaf order, independent of how the caller
  // sorted; the run's display position is restored from `order` afterwards.
  parsed.sort((a, b) => a.surah - b.surah || a.ayah - b.ayah);

  const runs: VerseRun[] = [];
  let current: typeof parsed = [];

  const flush = () => {
    if (!current.length) return;
    const first = current[0];
    const last = current[current.length - 1];
    runs.push({
      key: `${first.surah}:${first.ayah}-${last.ayah}`,
      surah: first.surah,
      startAyah: first.ayah,
      endAyah: last.ayah,
      items: current.map((p) => p.item),
    });
    current = [];
  };

  for (const entry of parsed) {
    const prev = current[current.length - 1];
    if (prev && entry.surah === prev.surah && entry.ayah - prev.ayah <= maxGap) {
      current.push(entry);
    } else {
      flush();
      current = [entry];
    }
  }
  flush();

  for (const item of unparsed) {
    runs.push({
      key: `x:${item.key}`,
      surah: 0,
      startAyah: 0,
      endAyah: 0,
      items: [item],
    });
  }

  const rank = (run: VerseRun) =>
    Math.min(...run.items.map((i) => order.get(i) ?? Number.MAX_SAFE_INTEGER));
  return runs.sort((a, b) => rank(a) - rank(b));
}
