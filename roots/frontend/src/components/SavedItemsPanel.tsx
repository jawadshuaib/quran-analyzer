import { useState, useEffect, useCallback, useRef, type ReactNode } from 'react';
import {
  getSavedItems,
  removeSavedItem,
  getSavedCount,
  type SavedItem,
  type SavedItemType,
} from '../utils/saved-items';
import {
  getAllNotes as userNotesGetAll,
  deleteNote as userNotesDelete,
  setNote as userNotesSet,
  subscribeToNotes,
} from '../utils/user-notes';
import { getSurahName } from '../utils/surah-names';
import NoteEditor from './NoteEditor';

const TYPE_LABELS: Record<SavedItemType, string> = {
  verse: 'Verses',
  word: 'Words',
  root: 'Roots',
};

const TYPE_ICONS: Record<SavedItemType, ReactNode> = {
  verse: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
      <path fillRule="evenodd" d="M2 3.5A1.5 1.5 0 013.5 2h9A1.5 1.5 0 0114 3.5v11.75A2.75 2.75 0 0016.75 18h-12A2.75 2.75 0 012 15.25V3.5zm3.75 7a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-4.5zm0-3a.75.75 0 000 1.5h4.5a.75.75 0 000-1.5h-4.5z" clipRule="evenodd" />
    </svg>
  ),
  word: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
      <path d="M5.127 3.502L5.25 3.5h9.5c.041 0 .082 0 .123.002A2.251 2.251 0 0012.75 2h-5.5a2.25 2.25 0 00-2.123 1.502zM1 10.25A2.25 2.25 0 013.25 8h13.5A2.25 2.25 0 0119 10.25v5.5A2.25 2.25 0 0116.75 18H3.25A2.25 2.25 0 011 15.75v-5.5zm11.457-3.75H7.543a2.25 2.25 0 00-2.218 1.871l8.35.001a2.25 2.25 0 00-2.218-1.872z" />
    </svg>
  ),
  root: (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
      <path d="M10 2a.75.75 0 01.75.75v.258a33.186 33.186 0 016.668.83.75.75 0 01-.336 1.461 31.28 31.28 0 00-1.103-.232l1.702 7.545a.75.75 0 01-.387.832A4.981 4.981 0 0115 14c-.825 0-1.606-.2-2.294-.556a.75.75 0 01-.387-.832l1.77-7.849a31.743 31.743 0 00-3.339-.254v11.505A20.01 20.01 0 0114.5 17.5h1.25a.75.75 0 010 1.5h-11.5a.75.75 0 010-1.5H5.5c1.26 0 2.5-.088 3.75-.269V5.986a31.77 31.77 0 00-3.339.254l1.77 7.849a.75.75 0 01-.387.832A4.981 4.981 0 015 14c-.825 0-1.606-.2-2.294-.556a.75.75 0 01-.387-.832l1.702-7.545a31.28 31.28 0 00-1.103.232.75.75 0 01-.336-1.462 33.186 33.186 0 016.668-.829V2.75A.75.75 0 0110 2z" />
    </svg>
  ),
};

/** Global event name to notify when saved items change */
export const SAVED_ITEMS_CHANGED = 'saved-items-changed';

/** Open the saved-items panel from anywhere. Optional `tab` hint will
 *  pre-select a tab once the panel grows tabs (Phase C). */
export const OPEN_SAVED_PANEL = 'open-saved-panel';

/** Call this from any component after toggling a save to refresh the panel */
export function notifySavedItemsChanged() {
  window.dispatchEvent(new CustomEvent(SAVED_ITEMS_CHANGED));
}

export function openSavedPanel(tab: 'saved' | 'notes' = 'saved') {
  window.dispatchEvent(new CustomEvent(OPEN_SAVED_PANEL, { detail: { tab } }));
}

interface ThemeData {
  theme: string;
  confidence: number;
}

interface VerseThemes {
  [verseKey: string]: ThemeData[];
}

interface Props {
  onNavigate?: (href: string) => void;
}

type FilterValue = SavedItemType | 'all' | 'notes';

export default function SavedItemsPanel({ onNavigate }: Props) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<SavedItem[]>([]);
  const [count, setCount] = useState(() => getSavedCount());
  const [filter, setFilter] = useState<FilterValue>('all');
  const [verseThemes, setVerseThemes] = useState<VerseThemes>({});
  const [groupByTheme, setGroupByTheme] = useState(true);
  // User notes (mirrored from quranExplorer.notes). Updated reactively
  // so toggling between Saved + Notes tabs reflects current state.
  const [notesMap, setNotesMap] = useState<Record<string, string>>(() => userNotesGetAll());
  const panelRef = useRef<HTMLDivElement>(null);

  // Refresh items from localStorage
  const refresh = useCallback(() => {
    const all = getSavedItems();
    setItems(all);
    setCount(all.length);
  }, []);

  // Fetch themes for saved verses
  const fetchThemes = useCallback(async (verseItems: SavedItem[]) => {
    if (verseItems.length === 0) {
      setVerseThemes({});
      return;
    }
    const newThemes: VerseThemes = {};
    await Promise.all(
      verseItems.map(async (item) => {
        if (verseThemes[item.key]) {
          newThemes[item.key] = verseThemes[item.key];
          return;
        }
        try {
          const resp = await fetch(`/api/verse/${item.key}/themes`);
          if (resp.ok) {
            const data = await resp.json();
            newThemes[item.key] = data.themes || [];
          }
        } catch { /* ignore */ }
      }),
    );
    setVerseThemes(newThemes);
  }, [verseThemes]);

  // Initial load + listen for changes from other components
  useEffect(() => {
    refresh();
    const handler = () => refresh();
    window.addEventListener(SAVED_ITEMS_CHANGED, handler);
    window.addEventListener('storage', handler);
    return () => {
      window.removeEventListener(SAVED_ITEMS_CHANGED, handler);
      window.removeEventListener('storage', handler);
    };
  }, [refresh]);

  // Open the panel when something fires the global open event (e.g. the
  // Saved / Notes links in the top nav). The event detail can include
  // a tab hint so we open straight on Notes when the Notes link is clicked.
  useEffect(() => {
    function onOpen(e: Event) {
      setOpen(true);
      const detail = (e as CustomEvent).detail as { tab?: 'saved' | 'notes' } | undefined;
      if (detail?.tab === 'notes') setFilter('notes');
      else if (detail?.tab === 'saved') setFilter('all');
    }
    window.addEventListener(OPEN_SAVED_PANEL, onOpen);
    return () => window.removeEventListener(OPEN_SAVED_PANEL, onOpen);
  }, []);

  // Mirror the user's notes for the Notes tab. Updates as the user
  // adds/removes notes from anywhere on the site.
  useEffect(() => {
    return subscribeToNotes(() => setNotesMap(userNotesGetAll()));
  }, []);

  // Fetch themes when panel opens or items change
  useEffect(() => {
    if (open) {
      refresh();
      const verses = getSavedItems().filter((i) => i.type === 'verse');
      fetchThemes(verses);
    }
  }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  // Close panel on outside click
  useEffect(() => {
    if (!open) return;
    function handleClick(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, [open]);

  const handleRemove = useCallback(
    (type: SavedItemType, key: string) => {
      removeSavedItem(type, key);
      notifySavedItemsChanged();
    },
    [],
  );

  const handleNavigate = useCallback(
    (href: string) => {
      setOpen(false);
      if (onNavigate) {
        onNavigate(href);
      } else {
        window.location.href = href;
      }
    },
    [onNavigate],
  );

  const filtered =
    filter === 'all' || filter === 'notes'
      ? items
      : items.filter((i) => i.type === filter);

  // Count by type for filter badges
  const countByType: Record<SavedItemType, number> = { verse: 0, word: 0, root: 0 };
  for (const item of items) {
    countByType[item.type]++;
  }

  // Notes — sorted by ref for stable display
  const notesEntries = Object.entries(notesMap).sort(([a], [b]) => {
    const [as, av] = a.split(':').map(Number);
    const [bs, bv] = b.split(':').map(Number);
    return as !== bs ? as - bs : av - bv;
  });
  const notesCount = notesEntries.length;

  // Group verses by theme (or separate types when mixed) — only on Saved tab
  const verseCount = countByType.verse;
  const nonVerseCount = countByType.word + countByType.root;
  const hasMixedTypes = verseCount > 0 && nonVerseCount > 0;
  const shouldGroup = filter !== 'notes' && groupByTheme && (verseCount >= 2 || hasMixedTypes) && (filter === 'all' || filter === 'verse');

  const groupedContent = useGroupedByTheme(filtered, verseThemes, shouldGroup);

  // Don't render anything if no saved items AND no notes
  if (count === 0 && notesCount === 0 && !open) return null;

  // Floating button (closed state)
  const totalCount = count + notesCount;
  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 left-6 z-50 flex items-center gap-2 rounded-full
                   bg-rose-500 text-white shadow-lg shadow-rose-200
                   hover:bg-rose-600 hover:shadow-xl hover:shadow-rose-300
                   transition-all duration-200
                   px-4 py-3 sm:px-5 sm:py-3.5"
        title={`${count} saved · ${notesCount} note${notesCount !== 1 ? 's' : ''}`}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          className="w-5 h-5"
        >
          <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
        </svg>
        <span className="text-sm font-medium hidden sm:inline">
          Saved &amp; Notes ({totalCount})
        </span>
        {/* Mobile-only count badge */}
        <span className="sm:hidden absolute -top-1 -right-1 min-w-[18px] h-[18px] flex items-center justify-center
                         rounded-full bg-white text-rose-600 text-[10px] font-bold shadow-sm">
          {totalCount}
        </span>
      </button>
    );
  }

  // Open panel
  return (
    <div
      ref={panelRef}
      className="fixed bottom-6 left-6 z-50 w-[calc(100vw-2rem)] sm:w-[400px]
                 rounded-2xl border border-rose-200 bg-white shadow-2xl shadow-rose-100/50
                 overflow-hidden flex flex-col"
      style={{ maxHeight: 'calc(100vh - 6rem)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-stone-100 bg-stone-50/80">
        <div className="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="currentColor"
            className="w-4.5 h-4.5 text-rose-500"
          >
            <path d="M11.645 20.91l-.007-.003-.022-.012a15.247 15.247 0 01-.383-.218 25.18 25.18 0 01-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0112 5.052 5.5 5.5 0 0116.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.175 0 01-4.244 3.17 15.247 15.247 0 01-.383.219l-.022.012-.007.004-.003.001a.752.752 0 01-.704 0l-.003-.001z" />
          </svg>
          <span className="text-sm font-semibold text-stone-700">
            Saved Items
          </span>
          <span className="text-xs text-stone-400">({count})</span>
        </div>
        <div className="flex items-center gap-1">
          {/* Theme grouping toggle — show when 2+ verses or mixed types */}
          {(verseCount >= 2 || hasMixedTypes) && (
            <button
              onClick={() => setGroupByTheme((prev) => !prev)}
              className={`rounded-md p-1.5 transition-colors ${
                groupByTheme
                  ? 'text-rose-500 bg-rose-50'
                  : 'text-stone-300 hover:text-stone-500 hover:bg-stone-100'
              }`}
              aria-label={groupByTheme ? 'Show flat list' : 'Group by theme'}
              title={groupByTheme ? 'Show flat list' : 'Group by theme'}
            >
              {/* Grid/group icon */}
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                <path fillRule="evenodd" d="M2.5 3A1.5 1.5 0 001 4.5v4A1.5 1.5 0 002.5 10h6A1.5 1.5 0 0010 8.5v-4A1.5 1.5 0 008.5 3h-6zm11 2A1.5 1.5 0 0012 6.5v7a1.5 1.5 0 001.5 1.5h4a1.5 1.5 0 001.5-1.5v-7A1.5 1.5 0 0017.5 5h-4zm-11 7A1.5 1.5 0 001 13.5v2A1.5 1.5 0 002.5 17h6A1.5 1.5 0 0010 15.5v-2A1.5 1.5 0 008.5 12h-6z" clipRule="evenodd" />
              </svg>
            </button>
          )}
          <button
            onClick={() => setOpen(false)}
            className="rounded-md p-1.5 text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors"
            aria-label="Close saved items"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>
      </div>

      {/* Type filter tabs */}
      {(items.length > 0 || notesCount > 0) && (
        <div className="flex items-center gap-1 px-3 py-2 border-b border-stone-100 overflow-x-auto">
          {items.length > 0 && (
            <FilterTab
              label="All"
              count={items.length}
              active={filter === 'all'}
              onClick={() => setFilter('all')}
            />
          )}
          {(['verse', 'word', 'root'] as SavedItemType[]).map((t) =>
            countByType[t] > 0 ? (
              <FilterTab
                key={t}
                label={TYPE_LABELS[t]}
                count={countByType[t]}
                active={filter === t}
                onClick={() => setFilter(t)}
              />
            ) : null,
          )}
          {notesCount > 0 && (
            <FilterTab
              label="Notes"
              count={notesCount}
              active={filter === 'notes'}
              onClick={() => setFilter('notes')}
            />
          )}
        </div>
      )}

      {/* Items list */}
      <div className="flex-1 overflow-y-auto overscroll-contain" style={{ maxHeight: '60vh' }}>
        {filter === 'notes' ? (
          notesEntries.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
              <p className="text-sm text-stone-400">No notes yet</p>
              <p className="text-xs text-stone-300 mt-1">
                Tap the pencil on any verse to add one
              </p>
            </div>
          ) : (
            <ul className="divide-y divide-stone-100">
              {notesEntries.map(([key, text]) => (
                <NoteRow
                  key={key}
                  refKey={key}
                  text={text}
                  onNavigate={() => handleNavigate(`/verse/${key}`)}
                />
              ))}
            </ul>
          )
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1}
              stroke="currentColor"
              className="w-10 h-10 text-stone-200 mb-3"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21.75 8.25c0-3.15-2.35-5.25-5.437-5.25A5.5 5.5 0 0012 5.052 5.5 5.5 0 007.688 3C4.6 3 2.25 5.1 2.25 8.25c0 7.22 9.75 12.75 9.75 12.75s9.75-5.53 9.75-12.75z"
              />
            </svg>
            <p className="text-sm text-stone-400">No saved items yet</p>
            <p className="text-xs text-stone-300 mt-1">
              Tap the heart on any verse to save it
            </p>
          </div>
        ) : shouldGroup && groupedContent.length > 0 ? (
          /* Grouped by theme view */
          <div className="divide-y divide-stone-100">
            {groupedContent.map((group) => (
              <div key={group.theme}>
                {/* Theme header */}
                <div className="sticky top-0 bg-stone-50/95 backdrop-blur-sm px-4 py-2 border-b border-stone-100">
                  <span className="text-[11px] font-semibold tracking-wide text-rose-600/80 uppercase">
                    {group.theme}
                  </span>
                  <span className="ml-1.5 text-[10px] text-stone-400">{group.items.length}</span>
                </div>
                <ul>
                  {group.items.map((item) => (
                    <SavedItemRow
                      key={`${item.type}-${item.key}`}
                      item={item}
                      onNavigate={handleNavigate}
                      onRemove={handleRemove}
                    />
                  ))}
                </ul>
              </div>
            ))}
          </div>
        ) : (
          /* Flat list view */
          <ul className="divide-y divide-stone-100">
            {filtered.map((item) => (
              <SavedItemRow
                key={`${item.type}-${item.key}`}
                item={item}
                onNavigate={handleNavigate}
                onRemove={handleRemove}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

/** Single saved item row */
function SavedItemRow({
  item,
  onNavigate,
  onRemove,
}: {
  item: SavedItem;
  onNavigate: (href: string) => void;
  onRemove: (type: SavedItemType, key: string) => void;
}) {
  return (
    <li className="group">
      <div className="flex items-start gap-3 px-4 py-3 hover:bg-stone-50 transition-colors">
        {/* Type icon */}
        <span className="mt-0.5 shrink-0 text-stone-300 group-hover:text-stone-400 transition-colors">
          {TYPE_ICONS[item.type]}
        </span>

        {/* Content — clickable */}
        <button
          className="flex-1 text-left min-w-0"
          onClick={() => onNavigate(item.href)}
        >
          <span className="text-sm font-medium text-stone-700 group-hover:text-stone-900 transition-colors line-clamp-1">
            {item.label}
          </span>
          {item.subtitle && (
            <span className="block text-xs text-stone-400 mt-0.5 line-clamp-2 leading-relaxed">
              {item.subtitle}
            </span>
          )}
        </button>

        {/* Remove button — always visible */}
        <button
          onClick={() => onRemove(item.type, item.key)}
          className="mt-0.5 shrink-0 rounded p-1 text-stone-300 hover:text-rose-500 hover:bg-rose-50 transition-colors"
          aria-label={`Remove ${item.label} from saved`}
          title="Remove"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
            <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 006 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 10.23 1.482l.149-.022.841 10.518A2.75 2.75 0 007.596 19h4.807a2.75 2.75 0 002.742-2.53l.841-10.519.149.023a.75.75 0 00.23-1.482A41.03 41.03 0 0014 4.193V3.75A2.75 2.75 0 0011.25 1h-2.5zM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4zM8.58 7.72a.75.75 0 00-1.5.06l.3 7.5a.75.75 0 101.5-.06l-.3-7.5zm4.34.06a.75.75 0 10-1.5-.06l-.3 7.5a.75.75 0 101.5.06l.3-7.5z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </li>
  );
}

/** Group saved items by verse theme */
function useGroupedByTheme(
  items: SavedItem[],
  verseThemes: VerseThemes,
  enabled: boolean,
): { theme: string; items: SavedItem[] }[] {
  if (!enabled) return [];

  const verses = items.filter((i) => i.type === 'verse');
  const nonVerses = items.filter((i) => i.type !== 'verse');

  // Need at least 2 verses OR a mix of verses + non-verses to group
  if (verses.length === 0 && nonVerses.length === 0) return [];
  if (verses.length < 2 && nonVerses.length === 0) return [];

  // Build theme → verses map using primary (highest confidence) theme
  const themeMap = new Map<string, SavedItem[]>();
  const ungrouped: SavedItem[] = [];

  for (const verse of verses) {
    const themes = verseThemes[verse.key];
    if (themes && themes.length > 0) {
      const primaryTheme = themes[0].theme;
      const existing = themeMap.get(primaryTheme) || [];
      existing.push(verse);
      themeMap.set(primaryTheme, existing);
    } else {
      ungrouped.push(verse);
    }
  }

  // Build sorted groups (largest first)
  const groups: { theme: string; items: SavedItem[] }[] = [];
  for (const [theme, themeItems] of themeMap) {
    groups.push({ theme, items: themeItems });
  }
  groups.sort((a, b) => b.items.length - a.items.length);

  // Add ungrouped verses
  if (ungrouped.length > 0) {
    groups.push({ theme: 'Other', items: ungrouped });
  }

  // Add non-verse items in their own group
  if (nonVerses.length > 0) {
    groups.push({ theme: 'Words & Roots', items: nonVerses });
  }

  return groups;
}

function FilterTab({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex-shrink-0 rounded-full px-2.5 py-1 text-xs font-medium transition-colors
                  ${active
                    ? 'bg-rose-100 text-rose-700'
                    : 'text-stone-400 hover:text-stone-600 hover:bg-stone-100'}`}
    >
      {label}
      <span className="ml-1 text-[10px] opacity-70">{count}</span>
    </button>
  );
}

// --------------------------------------------------------------------
// NoteRow — one entry in the Notes filter tab.
// --------------------------------------------------------------------

function NoteRow({
  refKey,
  text,
  onNavigate,
}: {
  refKey: string;
  text: string;
  onNavigate: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [surahN, verseN] = refKey.split(':').map(Number);

  function handleSave(newText: string) {
    if (newText.trim()) {
      userNotesSet(surahN, verseN, newText);
    } else {
      userNotesDelete(surahN, verseN);
    }
  }

  if (editing) {
    return (
      <li className="px-3 py-3 bg-stone-50/50">
        <div className="flex items-baseline justify-between mb-2">
          <span className="text-[11px] font-medium text-rose-600">
            {getSurahName(surahN)} · {refKey}
          </span>
        </div>
        <NoteEditor
          initial={text}
          onSave={handleSave}
          onClose={() => setEditing(false)}
          accent="violet"
        />
      </li>
    );
  }

  return (
    <li className="group flex items-start gap-2 px-3 py-3 hover:bg-stone-50">
      <div
        className="flex-1 min-w-0 cursor-pointer"
        onClick={onNavigate}
      >
        <div className="flex items-baseline gap-2 mb-1">
          <span className="text-[11px] font-medium text-rose-600">
            {getSurahName(surahN)} · {refKey}
          </span>
        </div>
        <p className="text-xs text-stone-700 leading-relaxed line-clamp-3 whitespace-pre-line">
          {text}
        </p>
      </div>
      <div className="flex flex-col items-center gap-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            setEditing(true);
          }}
          className="text-[10px] text-stone-400 hover:text-violet-600"
          aria-label="Edit note"
        >
          Edit
        </button>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            if (confirm('Delete this note? This cannot be undone.')) {
              userNotesDelete(surahN, verseN);
            }
          }}
          className="text-[10px] text-stone-400 hover:text-red-600"
          aria-label="Delete note"
        >
          Delete
        </button>
      </div>
    </li>
  );
}
