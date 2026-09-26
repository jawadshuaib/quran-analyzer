import type { DictionaryGuide } from './types';

/** Lazy loaders, one per guide file — each essay becomes its own small chunk,
 *  fetched only when its page (or the overview) is opened. */
const modules = import.meta.glob<{ default: DictionaryGuide }>('./guides/*.ts');

export const GUIDE_LOADERS: Record<string, () => Promise<DictionaryGuide>> = Object.fromEntries(
  Object.entries(modules).map(([path, load]) => [
    path.replace(/^\.\/guides\//, '').replace(/\.ts$/, ''),
    () => load().then((m) => m.default),
  ]),
);

export function loadAllGuides(): Promise<DictionaryGuide[]> {
  return Promise.all(Object.values(GUIDE_LOADERS).map((l) => l())).then((gs) =>
    gs.sort((a, b) => a.sortYear - b.sortYear || a.title.localeCompare(b.title)),
  );
}
