import { useCallback, useEffect, useState } from 'react';
import {
  fetchRootMeanings, fetchRootMeaningStats, updateRootMeaning, bulkRootMeanings,
  type RootMeaning, type RootMeaningStats,
} from '../../api/admin';

/**
 * Review queue for the root core-meaning passages shown in the word tooltip.
 *
 * The unit of review is a SENSE, not a root: 213 roots carry more than one
 * word in the same radicals (tarf "a glance" against taraf "an edge"), and the
 * lemma under the reader's cursor decides which passage they get. So a row
 * shows the sense's lemmas, not just the root.
 *
 * Nothing here is visible to a reader until it is approved AND unhidden, and
 * the two move together on approve.
 */
const PAGE = 25;

function GateBadges({ item }: { item: RootMeaning }) {
  if (!item.gates.length) {
    return <span className="text-[11px] px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700">clean</span>;
  }
  return (
    <span className="flex flex-wrap gap-1">
      {item.gates.map((g, i) => (
        <span
          key={i}
          title={g.msg}
          className={`text-[11px] px-1.5 py-0.5 rounded cursor-help ${
            g.severity === 'hard'
              ? 'bg-rose-50 text-rose-700'
              : 'bg-amber-50 text-amber-700'
          }`}
        >
          {g.gate}
        </span>
      ))}
    </span>
  );
}

export default function AdminRootMeanings() {
  const [items, setItems] = useState<RootMeaning[]>([]);
  const [stats, setStats] = useState<RootMeaningStats | null>(null);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [q, setQ] = useState('');
  const [reviewStatus, setReviewStatus] = useState('pending');
  const [gates, setGates] = useState('');
  const [split, setSplit] = useState('');
  const [sort, setSort] = useState('frequency');

  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [editing, setEditing] = useState<number | null>(null);
  const [draft, setDraft] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchRootMeanings({
        q, review_status: reviewStatus, gates, split, sort, limit: PAGE, offset,
      });
      setItems(data.items);
      setTotal(data.total);
      setStats(await fetchRootMeaningStats());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  }, [q, reviewStatus, gates, split, sort, offset]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { setOffset(0); setSelected(new Set()); }, [q, reviewStatus, gates, split, sort]);

  async function doBulk(op: 'approve' | 'reject' | 'pending' | 'hide' | 'unhide') {
    if (!selected.size) return;
    await bulkRootMeanings([...selected], op);
    setSelected(new Set());
    await load();
  }

  async function saveEdit(id: number) {
    await updateRootMeaning(id, { passage: draft });
    setEditing(null);
    await load();
  }

  const toggle = (id: number) => setSelected((s) => {
    const n = new Set(s);
    if (n.has(id)) n.delete(id); else n.add(id);
    return n;
  });

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-stone-800">Root Core Meanings</h2>
        <p className="text-sm text-stone-500 mt-0.5">
          The short passage a reader sees when hovering a word. One per <em>sense</em> of a root —
          roots whose letters carry two different words get a passage each. Approving publishes it.
        </p>
      </div>

      {stats && (
        <div className="flex flex-wrap gap-2 text-xs">
          {([
            ['total', stats.total, 'bg-stone-100 text-stone-700'],
            ['pending', stats.pending, 'bg-sky-50 text-sky-700'],
            ['approved', stats.approved, 'bg-emerald-50 text-emerald-700'],
            ['rejected', stats.rejected, 'bg-stone-100 text-stone-500'],
            ['clean', stats.clean, 'bg-emerald-50 text-emerald-700'],
            ['soft flags', stats.soft, 'bg-amber-50 text-amber-700'],
            ['hard fails', stats.hard, 'bg-rose-50 text-rose-700'],
            ['split senses', stats.split_senses, 'bg-violet-50 text-violet-700'],
            ['declined', stats.declined, 'bg-stone-100 text-stone-500'],
          ] as const).map(([label, n, cls]) => (
            <span key={label} className={`px-2 py-1 rounded ${cls}`}>
              {label}: <strong>{n}</strong>
            </span>
          ))}
        </div>
      )}

      <div className="flex flex-wrap gap-2 items-center">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search passage or root…"
          className="border border-stone-300 rounded px-2 py-1 text-sm w-56"
        />
        <select value={reviewStatus} onChange={(e) => setReviewStatus(e.target.value)}
                className="border border-stone-300 rounded px-2 py-1 text-sm">
          <option value="">any status</option>
          <option value="pending">pending</option>
          <option value="approved">approved</option>
          <option value="rejected">rejected</option>
        </select>
        <select value={gates} onChange={(e) => setGates(e.target.value)}
                className="border border-stone-300 rounded px-2 py-1 text-sm">
          <option value="">any checks</option>
          <option value="clean">clean only</option>
          <option value="soft">soft flags</option>
          <option value="hard">hard failures</option>
        </select>
        <select value={split} onChange={(e) => setSplit(e.target.value)}
                className="border border-stone-300 rounded px-2 py-1 text-sm">
          <option value="">all roots</option>
          <option value="only">split senses only</option>
          <option value="no">single-sense only</option>
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value)}
                className="border border-stone-300 rounded px-2 py-1 text-sm">
          <option value="frequency">most frequent first</option>
          <option value="root">by root</option>
          <option value="longest">longest first</option>
          <option value="recent">newest first</option>
        </select>
      </div>

      {selected.size > 0 && (
        <div className="flex gap-2 items-center bg-stone-50 border border-stone-200 rounded p-2">
          <span className="text-sm text-stone-600">{selected.size} selected</span>
          <button onClick={() => doBulk('approve')}
                  className="text-sm px-2 py-1 rounded bg-emerald-600 text-white">Approve &amp; publish</button>
          <button onClick={() => doBulk('reject')}
                  className="text-sm px-2 py-1 rounded bg-rose-600 text-white">Reject</button>
          <button onClick={() => doBulk('pending')}
                  className="text-sm px-2 py-1 rounded border border-stone-300">Back to pending</button>
          <button onClick={() => setSelected(new Set())}
                  className="text-sm px-2 py-1 text-stone-500">clear</button>
        </div>
      )}

      {error && <div className="text-sm text-rose-600">{error}</div>}
      {loading && <div className="text-sm text-stone-500">Loading…</div>}

      <div className="space-y-2">
        {items.map((it) => (
          <div key={it.id} className="border border-stone-200 rounded p-3 bg-white">
            <div className="flex items-start gap-3">
              <input type="checkbox" checked={selected.has(it.id)}
                     onChange={() => toggle(it.id)} className="mt-1" />
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-1">
                  <span dir="rtl" lang="ar" className="font-arabic text-lg text-stone-800">
                    {it.root_arabic || it.root_buckwalter}
                  </span>
                  <span className="text-xs text-stone-400">{it.root_buckwalter}</span>
                  {it.sense_key && (
                    <span dir="rtl" lang="ar"
                          className="font-arabic text-xs px-1.5 py-0.5 rounded bg-violet-50 text-violet-700">
                      {it.lemmas.join(' · ')}
                    </span>
                  )}
                  <span className="text-xs text-stone-400">{it.verses} verses</span>
                  <GateBadges item={it} />
                  <span className={`text-[11px] px-1.5 py-0.5 rounded ${
                    it.review_status === 'approved' ? 'bg-emerald-100 text-emerald-800'
                    : it.review_status === 'rejected' ? 'bg-stone-200 text-stone-600'
                    : 'bg-sky-50 text-sky-700'}`}>
                    {it.review_status}
                  </span>
                </div>

                {editing === it.id ? (
                  <div className="space-y-2">
                    <textarea value={draft} onChange={(e) => setDraft(e.target.value)} rows={4}
                              className="w-full border border-stone-300 rounded p-2 text-sm" />
                    <div className="flex gap-2 items-center">
                      <button onClick={() => void saveEdit(it.id)}
                              className="text-sm px-2 py-1 rounded bg-stone-800 text-white">Save</button>
                      <button onClick={() => setEditing(null)}
                              className="text-sm px-2 py-1 text-stone-500">Cancel</button>
                      <span className={`text-xs ${draft.length > 400 ? 'text-rose-600' : 'text-stone-400'}`}>
                        {draft.length}/400 characters
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-stone-700 leading-relaxed">
                    {it.passage || <em className="text-stone-400">declined — no passage</em>}
                  </p>
                )}

                <div className="flex flex-wrap gap-3 mt-1.5 text-xs text-stone-400">
                  <span>{(it.passage || '').length} chars</span>
                  {it.stations.length > 0 && <span>{it.stations.join(' → ')}</span>}
                  {it.confidence && <span>confidence: {it.confidence}</span>}
                  {it.edited_at && <span className="text-stone-500">edited</span>}
                  {editing !== it.id && (
                    <button onClick={() => { setEditing(it.id); setDraft(it.passage || ''); }}
                            className="text-stone-500 underline">edit</button>
                  )}
                  <a href={`/root/${encodeURIComponent(it.root_buckwalter)}`} target="_blank"
                     rel="noreferrer" className="text-stone-500 underline">root page</a>
                </div>
              </div>
            </div>
          </div>
        ))}
        {!loading && !items.length && (
          <div className="text-sm text-stone-500">Nothing matches these filters.</div>
        )}
      </div>

      <div className="flex items-center gap-3 text-sm">
        <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE))}
                className="px-2 py-1 border border-stone-300 rounded disabled:opacity-40">Previous</button>
        <span className="text-stone-500">
          {total === 0 ? '0' : `${offset + 1}–${Math.min(offset + PAGE, total)}`} of {total}
        </span>
        <button disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}
                className="px-2 py-1 border border-stone-300 rounded disabled:opacity-40">Next</button>
      </div>
    </div>
  );
}
