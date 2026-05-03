import { useState, useEffect, useCallback } from 'react';
import {
  getVerseOfTheDayPool, addVerseOfTheDay, deleteVerseOfTheDay,
} from '../../api/admin';
import type { VerseOfTheDayPoolItem } from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

/**
 * Admin page for the homepage's verse-of-the-day rotation.
 *
 * The pool is a flat list of (chapter, verse) refs. The home page
 * picks one each day deterministically by day-of-year, so changes
 * here take effect tomorrow at the earliest (today's pick is
 * already displayed). The "Today's pick" tile at the top makes
 * that obvious.
 *
 * UX:
 *   - Add by typing a verse reference like "2:255" or "55:13"
 *   - Each pool entry shows surah name + Arabic preview + English
 *     translation snippet so the admin can see what they're
 *     adding/removing without leaving the page
 *   - The current day's pick is highlighted with a gold ring
 *   - Remove with confirmation if it's today's pick (so the
 *     homepage doesn't suddenly fall back to 2:255 mid-day)
 */
export default function AdminVerseOfTheDay() {
  const [items, setItems] = useState<VerseOfTheDayPoolItem[]>([]);
  const [today, setToday] = useState<{ chapter: number; verse: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [adding, setAdding] = useState(false);
  const [newRef, setNewRef] = useState('');
  const [addErr, setAddErr] = useState('');
  const { confirm, dialog } = useConfirm();

  const load = useCallback(async () => {
    setErr('');
    try {
      const data = await getVerseOfTheDayPool();
      setItems(data.items);
      setToday(data.today);
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  function parseRef(input: string): { chapter: number; verse: number } | null {
    // Accept "2:255", "2 255", "2,255", "2-255". Reject anything else.
    const m = input.trim().match(/^(\d+)\s*[:,\s\-]\s*(\d+)$/);
    if (!m) return null;
    const chapter = parseInt(m[1], 10);
    const verse = parseInt(m[2], 10);
    if (!(chapter >= 1 && chapter <= 114 && verse >= 1)) return null;
    return { chapter, verse };
  }

  async function handleAdd() {
    setAddErr('');
    const parsed = parseRef(newRef);
    if (!parsed) {
      setAddErr('Use format like "2:255" — chapter 1-114, verse ≥ 1');
      return;
    }
    setAdding(true);
    try {
      await addVerseOfTheDay(parsed.chapter, parsed.verse);
      setNewRef('');
      await load();
    } catch (e) {
      setAddErr(e instanceof Error ? e.message : 'Add failed');
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(item: VerseOfTheDayPoolItem) {
    const isToday = today && today.chapter === item.chapter && today.verse === item.verse;
    const ok = await confirm({
      title: isToday ? "Remove today's verse?" : 'Remove verse from rotation?',
      message: isToday
        ? `Quran ${item.chapter}:${item.verse} is what's showing on the homepage RIGHT NOW. ` +
          `Removing it will leave today's homepage showing the rotation's next pick (or 2:255 if the pool empties). Continue?`
        : `Quran ${item.chapter}:${item.verse} (${item.surah_name}) will no longer rotate onto the homepage. The other ${items.length - 1} verses stay.`,
      confirmLabel: 'Remove',
      tone: 'danger',
    });
    if (!ok) return;
    try {
      await deleteVerseOfTheDay(item.id);
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : 'Delete failed');
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-stone-800 mb-1">Verse of the Day</h1>
        <p className="text-sm text-stone-500 max-w-2xl">
          Curate the rotation that shows on{' '}
          <a href="/" className="underline decoration-dotted underline-offset-2 hover:text-stone-700">the homepage</a>.
          One verse per day, picked deterministically by day-of-year so every visitor sees the same
          verse. Edits take effect on the next day's rotation — today's pick stays put.
        </p>
      </div>

      {err && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
          {err}
        </div>
      )}

      {/* Today's pick — emphasized so the admin knows what's currently
          on the homepage before they decide what to change. */}
      {today && (
        <div className="mb-6 rounded-xl border border-amber-200 bg-gradient-to-br from-amber-50/60 to-white px-4 py-3 flex items-center gap-3 flex-wrap">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-amber-700">
            Today
          </span>
          <span className="font-mono text-sm text-stone-800">
            {today.chapter}:{today.verse}
          </span>
          {(() => {
            const t = items.find((i) => i.chapter === today.chapter && i.verse === today.verse);
            return t ? (
              <span className="text-sm text-stone-600 truncate flex-1 min-w-0">
                {t.surah_name && <span className="font-medium">{t.surah_name}</span>}
                {t.translation_preview && <span className="ml-2 italic">— {t.translation_preview}</span>}
              </span>
            ) : null;
          })()}
        </div>
      )}

      {/* Add row */}
      <div className="mb-6 rounded-xl border border-stone-200 bg-white p-4">
        <div className="flex items-end gap-2 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-stone-600 mb-1">
              Add a verse to the rotation
            </label>
            <input
              type="text"
              value={newRef}
              onChange={(e) => setNewRef(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); void handleAdd(); } }}
              placeholder="e.g. 2:255 or 55:13"
              className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            />
          </div>
          <button
            onClick={() => void handleAdd()}
            disabled={adding || !newRef.trim()}
            className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
          >
            {adding ? 'Adding…' : 'Add verse'}
          </button>
        </div>
        {addErr && <p className="mt-2 text-xs text-red-600">{addErr}</p>}
      </div>

      {/* Pool list */}
      <div className="mb-3 flex items-baseline justify-between">
        <h2 className="text-sm font-semibold text-stone-700">
          Rotation <span className="text-stone-400 font-normal">({items.length} verse{items.length === 1 ? '' : 's'})</span>
        </h2>
      </div>
      {items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-300 bg-stone-50/40 p-8 text-sm text-stone-500 text-center">
          The rotation is empty. Add at least one verse above — the homepage will fall back to 2:255 until you do.
        </div>
      ) : (
        <ul className="rounded-xl border border-stone-200 bg-white divide-y divide-stone-100 overflow-hidden">
          {items.map((item) => {
            const isToday = today && today.chapter === item.chapter && today.verse === item.verse;
            return (
              <li
                key={item.id}
                className={`px-4 py-3 flex items-start gap-3 ${
                  isToday ? 'bg-amber-50/40' : 'hover:bg-stone-50/60'
                }`}
              >
                <div className="flex-shrink-0 w-20">
                  <div className="font-mono text-sm text-stone-800">
                    {item.chapter}:{item.verse}
                  </div>
                  {isToday && (
                    <div className="text-[10px] font-semibold uppercase tracking-wider text-amber-700 mt-0.5">
                      Today
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  {item.surah_name && (
                    <div className="text-sm font-medium text-stone-700">{item.surah_name}</div>
                  )}
                  {item.arabic_preview && (
                    <div
                      dir="rtl"
                      lang="ar"
                      className="font-arabic text-base text-stone-700 mt-0.5 truncate"
                    >
                      {item.arabic_preview}
                    </div>
                  )}
                  {item.translation_preview && (
                    <div className="text-xs text-stone-500 mt-0.5 italic line-clamp-2">
                      {item.translation_preview}
                    </div>
                  )}
                </div>
                <div className="flex-shrink-0 flex items-center gap-2">
                  <a
                    href={`/verse/${item.chapter}:${item.verse}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-stone-400 hover:text-stone-700"
                    title="Open this verse on the public site"
                  >
                    View ↗
                  </a>
                  <button
                    onClick={() => void handleDelete(item)}
                    className="px-2.5 py-1 rounded-md border border-red-200 text-red-700 text-xs font-medium hover:bg-red-50 cursor-pointer"
                  >
                    Remove
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      {dialog}
    </div>
  );
}
