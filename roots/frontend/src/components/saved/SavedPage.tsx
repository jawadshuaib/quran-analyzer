import { useEffect, useMemo, useState } from 'react';
import {
  getSavedItems,
  getFolders,
  getFolderCounts,
  getItemsInFolder,
  addItemsToFolder,
  removeItemsFromFolder,
  createFolder,
  subscribeToSavedItems,
  type Folder,
  type SavedItem,
  type SavedItemRef,
  type SavedItemType,
} from '../../utils/saved-items';
import { removeSavedItemsAndCleanup, ensureNotedVersesSaved } from '../../utils/saved-item-actions';
import {
  buildMultiVerseCopyPayload,
  copyToClipboard,
  type MultiCopyFormat,
  type MultiCopySource,
} from '../../utils/verse-copy';
import { getAllNotes, subscribeToNotes } from '../../utils/user-notes';
import { fetchSessionQA, type SessionQAEntry } from '../../api/assistant';
import { getSurahName } from '../../utils/surah-names';
import { useVerseThemes, groupItemsByTheme } from '../../hooks/useGroupedByTheme';
import { useSEO } from '../../hooks/useSEO';
import FolderChips from './FolderChips';
import SavedItemCard from './SavedItemCard';
import BulkBar from './BulkBar';

type TabValue = 'all' | SavedItemType | 'notes';
type SortValue = 'recent' | 'mushaf';

// ----- Page prefs (sort + theme grouping), remembered like copyPrefs --------

const PREFS_KEY = 'quranExplorer.savedPagePrefs';

interface PagePrefs {
  sort: SortValue;
  groupByTheme: boolean;
}

function loadPrefs(): PagePrefs {
  try {
    const raw = localStorage.getItem(PREFS_KEY);
    const parsed = raw ? (JSON.parse(raw) as Partial<PagePrefs>) : {};
    return {
      sort: parsed.sort === 'mushaf' ? 'mushaf' : 'recent',
      groupByTheme: typeof parsed.groupByTheme === 'boolean' ? parsed.groupByTheme : true,
    };
  } catch {
    return { sort: 'recent', groupByTheme: true };
  }
}

function savePrefs(prefs: PagePrefs): void {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  } catch {
    /* quota / disabled */
  }
}

// ----- URL state -------------------------------------------------------------

function readParams(): { folder: string | null; tab: TabValue; q: string } {
  const p = new URLSearchParams(window.location.search);
  const tab = p.get('tab');
  return {
    folder: p.get('folder'),
    tab: tab === 'verse' || tab === 'root' || tab === 'word' || tab === 'notes' ? tab : 'all',
    q: p.get('q') ?? '',
  };
}

// ----- Sorting / searching ----------------------------------------------------

function verseNums(key: string): [number, number, number] {
  const m = key.match(/^(\d+):(\d+)(?:\/(\d+))?$/);
  return m ? [Number(m[1]), Number(m[2]), Number(m[3] ?? 0)] : [999, 999, 999];
}

function sortItems(items: SavedItem[], sort: SortValue): SavedItem[] {
  const copy = [...items];
  if (sort === 'mushaf') {
    copy.sort((a, b) => {
      if (a.type === 'root' || b.type === 'root') return a.key.localeCompare(b.key);
      const [as, av, ap] = verseNums(a.key);
      const [bs, bv, bp] = verseNums(b.key);
      return as - bs || av - bv || ap - bp;
    });
  } else {
    copy.sort((a, b) => (a.savedAt < b.savedAt ? 1 : a.savedAt > b.savedAt ? -1 : 0));
  }
  return copy;
}

function matchesQuery(item: SavedItem, q: string): boolean {
  const needle = q.toLowerCase();
  return [item.label, item.subtitle, item.arabic, item.translation, item.key]
    .some((s) => !!s && s.toLowerCase().includes(needle));
}

const refKey = (r: SavedItemRef) => `${r.type} ${r.key}`;

const TYPE_SECTIONS: Array<{ type: SavedItemType; label: string }> = [
  { type: 'verse', label: 'Verses' },
  { type: 'root', label: 'Roots' },
  { type: 'word', label: 'Words' },
];

/**
 * /saved — the full-page home of the saved library: folder chips, search,
 * sort, theme grouping, bulk actions, and the Notes section. The floating
 * quick panel stays for everywhere else; this page is where management
 * happens.
 */
export default function SavedPage() {
  useSEO({
    title: 'Saved',
    description:
      'Your saved verses, roots, and words, organized into study folders — stored locally on your device.',
    path: '/saved',
    noindex: true,
  });

  const initial = useMemo(readParams, []);
  const initialPrefs = useMemo(loadPrefs, []);

  const [items, setItems] = useState<SavedItem[]>(() => getSavedItems());
  const [folders, setFolders] = useState<Folder[]>(() => getFolders());
  const [counts, setCounts] = useState<Record<string, number>>(() => getFolderCounts());
  const [notesMap, setNotesMap] = useState<Record<string, string>>(() => getAllNotes());
  const [activeFolderId, setActiveFolderId] = useState<string | null>(initial.folder);
  const [tab, setTab] = useState<TabValue>(initial.tab);
  const [q, setQ] = useState(initial.q);
  const [sort, setSort] = useState<SortValue>(initialPrefs.sort);
  const [groupTheme, setGroupTheme] = useState(initialPrefs.groupByTheme);
  const [selection, setSelection] = useState<Set<string>>(new Set());
  const [toast, setToast] = useState<string | null>(null);
  // The user's own Ask-the-Quran Q&A, grouped by verse key — rendered under
  // saved verse cards like an AI-produced note.
  const [qaMap, setQaMap] = useState<Record<string, SessionQAEntry[]>>({});

  useEffect(() => {
    let cancelled = false;
    fetchSessionQA().then((rows) => {
      if (cancelled) return;
      const map: Record<string, SessionQAEntry[]> = {};
      for (const row of rows) {
        (map[row.page_key] ??= []).push(row);
      }
      setQaMap(map);
    });
    return () => { cancelled = true; };
  }, []);

  // Live store subscription + one-time note migration. Order matters: the
  // subscription must be attached BEFORE ensureNotedVersesSaved runs, so the
  // verse cards it creates for pre-coupling "detached" notes land in state
  // (its saveItem calls notify through this very subscription).
  useEffect(() => {
    const unsubscribe = subscribeToSavedItems(() => {
      const next = getSavedItems();
      setItems(next);
      setFolders(getFolders());
      setCounts(getFolderCounts());
      // Drop any selected refs whose items no longer exist (removed here or in
      // another tab), so the bulk-bar count can't count a phantom.
      setSelection((prev) => {
        if (prev.size === 0) return prev;
        const live = new Set(next.map((i) => `${i.type} ${i.key}`));
        const pruned = new Set([...prev].filter((k) => live.has(k)));
        return pruned.size === prev.size ? prev : pruned;
      });
    });
    ensureNotedVersesSaved();
    return unsubscribe;
  }, []);
  useEffect(() => subscribeToNotes(() => setNotesMap(getAllNotes())), []);

  // A deleted folder can leave a stale filter (e.g. from a stale URL).
  useEffect(() => {
    if (activeFolderId && !folders.some((f) => f.id === activeFolderId)) {
      setActiveFolderId(null);
    }
  }, [activeFolderId, folders]);

  // Reflect filters in the URL (deep-linkable, no history spam).
  useEffect(() => {
    const p = new URLSearchParams();
    if (activeFolderId) p.set('folder', activeFolderId);
    if (tab !== 'all') p.set('tab', tab);
    if (q) p.set('q', q);
    const qs = p.toString();
    window.history.replaceState(null, '', qs ? `/saved?${qs}` : '/saved');
  }, [activeFolderId, tab, q]);

  // Persist prefs
  useEffect(() => savePrefs({ sort, groupByTheme: groupTheme }), [sort, groupTheme]);

  // Selection resets when the visible set changes meaningfully.
  useEffect(() => setSelection(new Set()), [activeFolderId, tab]);

  function showToast(msg: string) {
    setToast(msg);
    window.setTimeout(() => setToast((t) => (t === msg ? null : t)), 2600);
  }

  // ----- Derived visible items ----------------------------------------------
  const scoped = activeFolderId ? getItemsInFolder(activeFolderId) : items;
  const qt = q.trim();
  const searched = qt
    ? scoped.filter(
        (i) =>
          matchesQuery(i, qt) ||
          // A verse's note and its Ask-the-Quran Q&A are part of the verse —
          // search them too.
          (i.type === 'verse' &&
            ((notesMap[i.key] ?? '').toLowerCase().includes(qt.toLowerCase()) ||
              (qaMap[i.key] ?? []).some(
                (x) =>
                  x.question.toLowerCase().includes(qt.toLowerCase()) ||
                  x.answer.toLowerCase().includes(qt.toLowerCase()),
              ))),
      )
    : scoped;

  const byType: Record<SavedItemType, SavedItem[]> = { verse: [], root: [], word: [] };
  for (const item of searched) byType[item.type].push(item);
  const sortedByType: Record<SavedItemType, SavedItem[]> = {
    verse: sortItems(byType.verse, sort),
    root: sortItems(byType.root, sort),
    word: sortItems(byType.word, sort),
  };

  const activeFolder = folders.find((f) => f.id === activeFolderId) ?? null;

  // Verses that carry a personal note — the Notes tab is a FILTER over the
  // verse cards (a note lives under its verse), so notes inherit the active
  // folder scope and the search like everything else.
  const notedVerses = sortedByType.verse.filter((i) => !!notesMap[i.key]);

  // Theme grouping (Verses section, All/Verses tabs, ≥2 verses)
  const groupingActive =
    groupTheme && (tab === 'all' || tab === 'verse') && sortedByType.verse.length >= 2;
  const verseThemes = useVerseThemes(
    groupingActive ? sortedByType.verse.map((i) => i.key) : [],
    groupingActive,
  );
  const verseGroups = groupItemsByTheme(sortedByType.verse, verseThemes, groupingActive);

  // How many rows the CURRENT tab actually renders — drives the empty state
  // per-tab (a type tab shows only its section; the notes tab shows only
  // verses that carry a note).
  const visibleForTab =
    tab === 'notes'
      ? notedVerses.length
      : tab === 'all'
        ? searched.length
        : sortedByType[tab].length;

  // ----- Selection ------------------------------------------------------------
  const selectedItems = searched.filter((i) => selection.has(refKey(i)));
  const selectedRefs: SavedItemRef[] = selectedItems.map((i) => ({ type: i.type, key: i.key }));

  function toggleSelect(item: SavedItem) {
    setSelection((prev) => {
      const next = new Set(prev);
      const k = refKey(item);
      if (next.has(k)) next.delete(k);
      else next.add(k);
      return next;
    });
  }

  // ----- Copy helpers ----------------------------------------------------------
  function toCopySources(list: SavedItem[]): MultiCopySource[] {
    return list
      .filter((i) => i.type === 'verse')
      .map((i) => ({
        verseKey: i.key,
        arabic: i.arabic,
        translation: i.translation,
        surahName: getSurahName(verseNums(i.key)[0]),
      }));
  }

  async function copyVerses(list: SavedItem[], format: MultiCopyFormat) {
    const sources = toCopySources(list);
    if (sources.length === 0) {
      showToast('No verses to copy.');
      return;
    }
    const { payload, copied, skipped } = buildMultiVerseCopyPayload(sources, format, {
      includeReference: true,
    });
    const ok = copied > 0 && (await copyToClipboard(payload));
    showToast(
      ok
        ? `Copied ${copied} verse${copied !== 1 ? 's' : ''}${skipped ? ` (${skipped} skipped — text not stored)` : ''}`
        : 'Copy failed — nothing had stored text.',
    );
  }

  // ----- Bulk handlers ----------------------------------------------------------
  function bulkAddToFolder(folderId: string) {
    addItemsToFolder(selectedRefs, folderId);
    const name = folders.find((f) => f.id === folderId)?.name ?? 'folder';
    showToast(`Added ${selectedRefs.length} to "${name}"`);
  }

  function bulkCreateAndAdd(name: string) {
    const folder = createFolder(name);
    if (folder) bulkAddToFolder(folder.id);
  }

  function bulkRemoveFromActive() {
    if (!activeFolderId) return;
    removeItemsFromFolder(selectedRefs, activeFolderId);
    setSelection(new Set());
  }

  function bulkRemoveEntirely() {
    if (
      window.confirm(
        `Remove ${selectedRefs.length} item${selectedRefs.length !== 1 ? 's' : ''} from Saved? Verse highlights are cleared too.`,
      )
    ) {
      removeSavedItemsAndCleanup(selectedRefs);
      setSelection(new Set());
    }
  }

  // ----- Render -----------------------------------------------------------------
  const nothingSavedAtAll = items.length === 0 && Object.keys(notesMap).length === 0;

  const tabPills: Array<{ value: TabValue; label: string; count: number }> = [
    { value: 'all', label: 'All', count: searched.length },
    ...TYPE_SECTIONS.map(({ type, label }) => ({
      value: type as TabValue,
      label,
      count: sortedByType[type].length,
    })).filter((t) => t.count > 0),
    // Notes = verses that carry a note; scoped by folder + search like the rest.
    ...(notedVerses.length > 0
      ? [{ value: 'notes' as TabValue, label: 'Notes', count: notedVerses.length }]
      : []),
  ];

  function renderVerseSection(list: SavedItem[]) {
    if (groupingActive && verseGroups.length > 0) {
      return (
        <div className="space-y-4">
          {verseGroups.map((group) => (
            <div key={group.theme}>
              <div className="mb-1.5">
                <span className="text-[11px] font-semibold tracking-wide text-rose-600/80 uppercase">
                  {group.theme}
                </span>
                <span className="ml-1.5 text-[10px] text-stone-400">{group.items.length}</span>
              </div>
              <div className="space-y-2">
                {group.items.map((item) => (
                  <SavedItemCard
                    key={refKey(item)}
                    item={item}
                    folders={folders}
                    selected={selection.has(refKey(item))}
                    onToggleSelect={() => toggleSelect(item)}
                    note={notesMap[item.key]}
                    qa={qaMap[item.key]}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      );
    }
    return (
      <div className="space-y-2">
        {list.map((item) => (
          <SavedItemCard
            key={refKey(item)}
            item={item}
            folders={folders}
            selected={selection.has(refKey(item))}
            onToggleSelect={() => toggleSelect(item)}
            note={notesMap[item.key]}
            qa={qaMap[item.key]}
          />
        ))}
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-10">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold text-stone-800">Saved</h1>
        <p className="mt-2 text-sm text-stone-500 leading-relaxed">
          Everything you've bookmarked — verses, roots, and words — organized into study
          folders. Stored only on this device.
        </p>
      </header>

      {nothingSavedAtAll ? (
        <div className="flex flex-col items-center justify-center rounded-xl border border-stone-200 bg-white py-16 px-4 text-center">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1} className="w-10 h-10 text-stone-200 mb-3">
            <path d="M6 3h12a1 1 0 011 1v17l-7-4.5L5 21V4a1 1 0 011-1z" strokeLinejoin="round" />
          </svg>
          <p className="text-sm text-stone-500">Nothing saved yet</p>
          <p className="text-xs text-stone-400 mt-1 max-w-xs">
            Tap the bookmark on any verse, root, or word to keep it here — then group what
            you're studying into folders.
          </p>
          <a
            href="/read/1"
            className="mt-4 rounded-lg bg-rose-500 px-4 py-2 text-xs font-semibold text-white hover:bg-rose-600 transition-colors"
          >
            Start reading →
          </a>
        </div>
      ) : (
        <>
          {/* Controls */}
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Filter by text or reference…"
              className="min-w-0 flex-1 rounded-lg border border-stone-200 bg-white px-3 py-1.5 text-sm
                         text-stone-700 placeholder:text-stone-300 focus:outline-none focus:border-rose-300"
            />
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as SortValue)}
              aria-label="Sort order"
              className="rounded-lg border border-stone-200 bg-white px-2 py-1.5 text-xs text-stone-600
                         focus:outline-none focus:border-rose-300 cursor-pointer"
            >
              <option value="recent">Recently saved</option>
              <option value="mushaf">Mushaf order</option>
            </select>
            <button
              type="button"
              onClick={() => setGroupTheme((v) => !v)}
              aria-label={groupTheme ? 'Show flat list' : 'Group by theme'}
              title={groupTheme ? 'Show flat list' : 'Group by theme'}
              className={`rounded-lg border p-2 transition-colors cursor-pointer ${
                groupTheme
                  ? 'border-rose-200 bg-rose-50 text-rose-500'
                  : 'border-stone-200 bg-white text-stone-300 hover:text-stone-500'
              }`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                <path fillRule="evenodd" d="M2.5 3A1.5 1.5 0 001 4.5v4A1.5 1.5 0 002.5 10h6A1.5 1.5 0 0010 8.5v-4A1.5 1.5 0 008.5 3h-6zm11 2A1.5 1.5 0 0012 6.5v7a1.5 1.5 0 001.5 1.5h4a1.5 1.5 0 001.5-1.5v-7A1.5 1.5 0 0017.5 5h-4zm-11 7A1.5 1.5 0 001 13.5v2A1.5 1.5 0 002.5 17h6A1.5 1.5 0 0010 15.5v-2A1.5 1.5 0 008.5 12h-6z" clipRule="evenodd" />
              </svg>
            </button>
          </div>

          {/* Folder chips */}
          <div className="mb-3">
            <FolderChips
              folders={folders}
              counts={counts}
              totalCount={items.length}
              activeId={activeFolderId}
              onSelect={(id) => setActiveFolderId(id)}
              onCopyAll={(folderId) => copyVerses(getItemsInFolder(folderId), 'translation')}
            />
          </div>

          {/* Type tabs */}
          {tabPills.length > 1 && (
            <div className="mb-4 flex items-center gap-1 overflow-x-auto">
              {tabPills.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setTab(t.value)}
                  className={`flex-shrink-0 rounded-full px-2.5 py-1 text-xs font-medium transition-colors cursor-pointer
                              ${tab === t.value
                                ? 'bg-stone-800 text-white'
                                : 'text-stone-400 hover:text-stone-600 hover:bg-stone-100'}`}
                >
                  {t.label}
                  <span className="ml-1 text-[10px] opacity-70">{t.count}</span>
                </button>
              ))}
            </div>
          )}

          {/* Bulk bar */}
          {selection.size > 0 && (
            <div className="mb-4">
              <BulkBar
                count={selection.size}
                folders={folders}
                activeFolder={activeFolder}
                copyEnabled={selectedItems.some((i) => i.type === 'verse' && !!i.arabic)}
                onAddToFolder={bulkAddToFolder}
                onCreateAndAdd={bulkCreateAndAdd}
                onRemoveFromActive={bulkRemoveFromActive}
                onRemoveEntirely={bulkRemoveEntirely}
                onCopy={(fmt) => copyVerses(selectedItems, fmt)}
                onClear={() => setSelection(new Set())}
              />
            </div>
          )}

          {/* Empty folder / empty search / empty tab */}
          {visibleForTab === 0 && (
            <div className="flex flex-col items-center justify-center rounded-xl border border-stone-200 bg-white py-12 px-4 text-center">
              <p className="text-sm text-stone-500">
                {q.trim()
                  ? 'Nothing matches your filter'
                  : tab === 'notes'
                    ? 'No notes yet'
                    : activeFolder
                      ? `No items in "${activeFolder.name}" yet`
                      : 'Nothing here yet'}
              </p>
              <p className="text-xs text-stone-400 mt-1 max-w-xs">
                {q.trim()
                  ? 'Try a different word or reference.'
                  : tab === 'notes'
                    ? 'Tap the pencil on any verse to add one — it will appear here under its verse.'
                    : activeFolder
                      ? 'Bookmark any verse, then tick this folder in the popup.'
                      : ''}
              </p>
              {activeFolder && !q.trim() && (
                <button
                  type="button"
                  onClick={() => setActiveFolderId(null)}
                  className="mt-3 text-xs font-medium text-rose-600 hover:text-rose-700 cursor-pointer"
                >
                  Show all saved
                </button>
              )}
            </div>
          )}

          {/* Sections */}
          <div className="space-y-6">
            {TYPE_SECTIONS.map(({ type, label }) => {
              if (tab !== 'all' && tab !== type) return null;
              const list = sortedByType[type];
              if (list.length === 0) return null;
              return (
                <section key={type}>
                  <h2 className="mb-2 text-sm font-semibold text-stone-700">
                    {label}
                    <span className="ml-1.5 text-xs font-normal text-stone-400">{list.length}</span>
                  </h2>
                  {type === 'verse' ? renderVerseSection(list) : (
                    <div className="space-y-2">
                      {list.map((item) => (
                        <SavedItemCard
                          key={refKey(item)}
                          item={item}
                          folders={folders}
                          selected={selection.has(refKey(item))}
                          onToggleSelect={() => toggleSelect(item)}
                        />
                      ))}
                    </div>
                  )}
                </section>
              );
            })}

            {/* Notes tab — verse cards filtered to those carrying a note
                (each renders its note beneath it) */}
            {tab === 'notes' && notedVerses.length > 0 && (
              <section>
                <h2 className="mb-2 text-sm font-semibold text-stone-700">
                  Verses with notes
                  <span className="ml-1.5 text-xs font-normal text-stone-400">{notedVerses.length}</span>
                </h2>
                <div className="space-y-2">
                  {notedVerses.map((item) => (
                    <SavedItemCard
                      key={refKey(item)}
                      item={item}
                      folders={folders}
                      selected={selection.has(refKey(item))}
                      onToggleSelect={() => toggleSelect(item)}
                      note={notesMap[item.key]}
                      qa={qaMap[item.key]}
                    />
                  ))}
                </div>
              </section>
            )}
          </div>
        </>
      )}

      {/* Toast */}
      {toast && (
        <div
          className="fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-full bg-stone-800 px-4 py-2
                     text-xs font-medium text-white shadow-lg"
          role="status"
        >
          {toast}
        </div>
      )}
    </div>
  );
}
