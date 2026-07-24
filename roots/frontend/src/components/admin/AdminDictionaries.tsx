import { useEffect, useState, useCallback } from 'react';
import {
  getAdminDictionaries, getAdminDictionaryStats, updateAdminDictionary, bulkAdminDictionaries,
  type AdminDictItem, type AdminDictStats, type AdminDictSort,
} from '../../api/admin';

/** The Lexicon Library review queue. Harmonized classical-dictionary entries
 *  land here as `pending`; an admin reads the harmonized English (and, one click
 *  down, the original Arabic + faithful translation), edits if needed, and
 *  approves. Only approved + visible entries reach the public root/word pages.
 *  Faithfulness-verify flags surface first so hand-checking is targeted. */

const LIMIT = 20;

function Pill({ children, tone }: { children: React.ReactNode; tone: string }) {
  return <span className={`rounded-full px-1.5 py-0.5 text-[10px] font-medium ${tone}`}>{children}</span>;
}

function EntryCard({ item, onChange }: { item: AdminDictItem; onChange: () => void }) {
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(false);
  const [harm, setHarm] = useState(item.harmonized_en || '');
  const [trans, setTrans] = useState(item.translation_en || '');
  const [busy, setBusy] = useState(false);

  const patch = useCallback(async (p: Parameters<typeof updateAdminDictionary>[1]) => {
    setBusy(true);
    try { await updateAdminDictionary(item.id, p); onChange(); }
    catch (e) { alert(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusy(false); }
  }, [item.id, onChange]);

  const century = item.author_death_year ? Math.floor(item.author_death_year / 100) + 1 : null;
  const statusTone = item.review_status === 'approved' ? 'bg-emerald-100 text-emerald-700'
    : item.review_status === 'rejected' ? 'bg-red-100 text-red-600'
    : 'bg-amber-100 text-amber-700';

  return (
    <div className={`rounded-lg border bg-white p-3 ${item.hidden ? 'opacity-60 border-stone-200' : 'border-stone-200'}`}>
      <div className="flex flex-wrap items-baseline gap-2">
        <a href={item.link} target="_blank" rel="noopener noreferrer"
           className="font-arabic text-lg text-stone-800 hover:text-emerald-700" dir="rtl">{item.root_arabic}</a>
        <span className="text-xs text-stone-400">{item.root_buckwalter}</span>
        <span className="font-medium text-stone-700">{item.name_en}</span>
        <span className="text-xs text-stone-500">{item.author}{century ? ` · ${century}th c.` : ''}</span>
        <div className="ml-auto flex items-center gap-1.5">
          <Pill tone={statusTone}>{item.review_status}</Pill>
          {item.hidden && <Pill tone="bg-stone-200 text-stone-500">hidden</Pill>}
          {item.is_quran_specific && <Pill tone="bg-emerald-50 text-emerald-600">Qurʾān</Pill>}
          {item.verify_ok === false && (
            <Pill tone="bg-red-100 text-red-600"><span title={item.verify_reason || ''}>⚑ verify</span></Pill>
          )}
          {item.verify_ok === true && <Pill tone="bg-emerald-50 text-emerald-600">✓</Pill>}
          {item.confidence != null && (
            <span className="text-[10px] tabular-nums text-stone-400">{item.confidence.toFixed(2)}</span>
          )}
        </div>
      </div>

      {!item.harmonized_en && (
        <p className="mt-2 text-xs italic text-stone-400">Not harmonized yet ({item.orig_len} ch of Arabic scraped).</p>
      )}

      {item.harmonized_en && !editing && (
        <>
          <p className={`mt-2 whitespace-pre-line text-sm text-stone-700 ${open ? '' : 'line-clamp-3'}`}>
            {item.harmonized_en}
          </p>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-[11px]">
            <button onClick={() => setOpen((o) => !o)} className="text-stone-400 hover:text-stone-600">
              {open ? 'less' : `more (${item.harm_len} ch)`}
            </button>
            {open && item.original_text_ar && (
              <details className="w-full">
                <summary className="cursor-pointer text-emerald-600">Original Arabic + faithful translation</summary>
                <div className="mt-2 grid gap-3 rounded border border-stone-200 bg-stone-50 p-2 sm:grid-cols-2">
                  <div dir="rtl" lang="ar" className="font-arabic text-sm leading-loose text-stone-800">{item.original_text_ar}</div>
                  <div className="whitespace-pre-line text-xs text-stone-600">{item.translation_en}</div>
                </div>
              </details>
            )}
          </div>
        </>
      )}

      {editing && (
        <div className="mt-2 space-y-2">
          <div>
            <label className="text-[10px] uppercase tracking-wide text-stone-400">Harmonized (readable)</label>
            <textarea value={harm} onChange={(e) => setHarm(e.target.value)} rows={8}
              className="w-full rounded border border-stone-300 p-2 text-sm" />
          </div>
          <div>
            <label className="text-[10px] uppercase tracking-wide text-stone-400">Faithful translation</label>
            <textarea value={trans} onChange={(e) => setTrans(e.target.value)} rows={5}
              className="w-full rounded border border-stone-300 p-2 text-xs" />
          </div>
        </div>
      )}

      <div className="mt-2 flex flex-wrap gap-1.5">
        {item.review_status !== 'approved' && (
          <button disabled={busy || !item.harmonized_en} onClick={() => patch({ review_status: 'approved' })}
            className="rounded bg-emerald-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-40">
            Approve
          </button>
        )}
        {item.review_status !== 'rejected' && (
          <button disabled={busy} onClick={() => patch({ review_status: 'rejected' })}
            className="rounded border border-red-200 px-2.5 py-1 text-xs font-medium text-red-600 hover:bg-red-50">
            Reject
          </button>
        )}
        {item.review_status !== 'pending' && (
          <button disabled={busy} onClick={() => patch({ review_status: 'pending' })}
            className="rounded border border-stone-200 px-2.5 py-1 text-xs text-stone-500 hover:bg-stone-50">
            Pending
          </button>
        )}
        <button disabled={busy} onClick={() => patch({ hidden: !item.hidden })}
          className="rounded border border-stone-200 px-2.5 py-1 text-xs text-stone-500 hover:bg-stone-50">
          {item.hidden ? 'Unhide' : 'Hide'}
        </button>
        {editing ? (
          <>
            <button disabled={busy} onClick={() => { patch({ harmonized_en: harm, translation_en: trans }); setEditing(false); }}
              className="rounded bg-stone-800 px-2.5 py-1 text-xs font-medium text-white hover:bg-stone-900">Save edits</button>
            <button onClick={() => { setEditing(false); setHarm(item.harmonized_en || ''); setTrans(item.translation_en || ''); }}
              className="rounded border border-stone-200 px-2.5 py-1 text-xs text-stone-500">Cancel</button>
          </>
        ) : (
          item.harmonized_en && (
            <button onClick={() => setEditing(true)} className="rounded border border-stone-200 px-2.5 py-1 text-xs text-stone-500 hover:bg-stone-50">Edit</button>
          )
        )}
      </div>
    </div>
  );
}

export default function AdminDictionaries() {
  const [stats, setStats] = useState<AdminDictStats | null>(null);
  const [items, setItems] = useState<AdminDictItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [dict, setDict] = useState('');
  const [reviewStatus, setReviewStatus] = useState('pending');
  const [sort, setSort] = useState<AdminDictSort>('root');
  const [search, setSearch] = useState('');
  const [busyBulk, setBusyBulk] = useState(false);

  const refreshStats = useCallback(() => {
    getAdminDictionaryStats().then(setStats).catch(() => { /* non-fatal */ });
  }, []);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getAdminDictionaries({
        dictionary_slug: dict || undefined, review_status: reviewStatus || undefined,
        q: search || undefined, sort, only: 'harmonized', limit: LIMIT, offset,
      });
      setItems(res.items); setTotal(res.total);
    } catch (e) { alert(e instanceof Error ? e.message : 'Failed to load'); }
    finally { setLoading(false); }
  }, [dict, reviewStatus, search, sort, offset]);

  useEffect(() => { refreshStats(); }, [refreshStats]);
  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => { setOffset(0); }, [dict, reviewStatus, search, sort]);

  const afterChange = useCallback(() => { refresh(); refreshStats(); }, [refresh, refreshStats]);

  async function bulkApprove() {
    const scope = dict ? `all harmonized entries for “${dict}”` : 'ALL harmonized pending entries';
    if (!confirm(`Approve ${scope}? (This publishes them to the public root pages once synced.)`)) return;
    setBusyBulk(true);
    try {
      const r = await bulkAdminDictionaries({ action: 'approve', dictionary_slug: dict || undefined, review_status: 'pending' });
      afterChange();
      alert(`Approved ${r.updated} entries.`);
    } catch (e) { alert(e instanceof Error ? e.message : 'Bulk failed'); }
    finally { setBusyBulk(false); }
  }

  const pct = stats && stats.total ? Math.round((stats.harmonized / stats.total) * 100) : 0;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-stone-800">The Lexicon Library</h2>
        <p className="text-sm text-stone-500">Harmonized classical-dictionary root definitions. Approve entries to publish them on the root & word pages.</p>
      </div>

      {stats && (
        <div className="rounded-lg border border-stone-200 bg-white p-3">
          <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
            <span><b className="tabular-nums">{stats.harmonized}</b>/{stats.total} harmonized ({pct}%)</span>
            <span className="text-amber-700"><b className="tabular-nums">{stats.pending}</b> pending</span>
            <span className="text-emerald-700"><b className="tabular-nums">{stats.approved}</b> approved</span>
            <span className="text-red-600"><b className="tabular-nums">{stats.rejected}</b> rejected</span>
            <span className="text-stone-500"><b className="tabular-nums">{stats.roots}</b> roots</span>
          </div>
          <details className="mt-2">
            <summary className="cursor-pointer text-xs text-stone-400">Per-dictionary coverage</summary>
            <div className="mt-2 grid gap-x-4 gap-y-0.5 text-xs text-stone-600 sm:grid-cols-2">
              {stats.by_dictionary.map((d) => (
                <div key={d.slug} className="flex justify-between">
                  <span>d.{d.author_death_year} {d.name_en}</span>
                  <span className="tabular-nums text-stone-400">{d.approved}✓ / {d.n}</span>
                </div>
              ))}
            </div>
          </details>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        <select value={dict} onChange={(e) => setDict(e.target.value)} className="rounded border border-stone-300 px-2 py-1 text-sm">
          <option value="">All dictionaries</option>
          {stats?.by_dictionary.map((d) => <option key={d.slug} value={d.slug}>{d.name_en} ({d.n})</option>)}
        </select>
        <select value={reviewStatus} onChange={(e) => setReviewStatus(e.target.value)} className="rounded border border-stone-300 px-2 py-1 text-sm">
          <option value="">Any status</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
        <select value={sort} onChange={(e) => setSort(e.target.value as AdminDictSort)} className="rounded border border-stone-300 px-2 py-1 text-sm">
          <option value="root">By root</option>
          <option value="recent">Recently edited</option>
          <option value="confidence">Low confidence first</option>
          <option value="longest">Longest</option>
        </select>
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search text / root"
          className="rounded border border-stone-300 px-2 py-1 text-sm" />
        <button disabled={busyBulk} onClick={bulkApprove}
          className="ml-auto rounded bg-emerald-600 px-3 py-1 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-40">
          {busyBulk ? 'Approving…' : dict ? 'Approve all in this dictionary' : 'Approve all pending'}
        </button>
      </div>

      {loading ? (
        <p className="py-8 text-center text-sm text-stone-400">Loading…</p>
      ) : items.length === 0 ? (
        <p className="py-8 text-center text-sm text-stone-400">No entries match.</p>
      ) : (
        <div className="space-y-2">
          {items.map((it) => <EntryCard key={it.id} item={it} onChange={afterChange} />)}
        </div>
      )}

      {total > LIMIT && (
        <div className="flex items-center justify-between text-sm">
          <button disabled={offset === 0} onClick={() => setOffset((o) => Math.max(0, o - LIMIT))}
            className="rounded border border-stone-200 px-3 py-1 disabled:opacity-40">Prev</button>
          <span className="text-stone-400">{offset + 1}–{Math.min(offset + LIMIT, total)} of {total}</span>
          <button disabled={offset + LIMIT >= total} onClick={() => setOffset((o) => o + LIMIT)}
            className="rounded border border-stone-200 px-3 py-1 disabled:opacity-40">Next</button>
        </div>
      )}
    </div>
  );
}
