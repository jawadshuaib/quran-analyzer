import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
  getAdminPoetry, getAdminPoetryStats, updateAdminPoetry, deleteAdminPoetry, bulkAdminPoetry,
  type AdminPoetryItem, type AdminPoetryStats, type AdminPoetrySort, type AdminExegesisBulkOp,
  type PoetryKind,
} from '../../api/admin';
import FormattedText from '../FormattedText';

const LIMIT = 25;

/* The note body runs through the same FormattedText renderer the public pages
   use. The admin payload omits the quoted-lines lookup, so the [[q:…]] markers
   degrade to plain Arabic here — fine for review (the reviewer reads the prose;
   the hover tooltips only matter to the reader). */
function PoetryBody({ markdown }: { markdown: string }) {
  return <FormattedText text={markdown} className="text-[15px] leading-relaxed text-stone-700" />;
}

export default function AdminPoetry() {
  const [kind, setKind] = useState<PoetryKind>('root');
  const [stats, setStats] = useState<AdminPoetryStats | null>(null);
  const [items, setItems] = useState<AdminPoetryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [reviewStatus, setReviewStatus] = useState('');
  const [status, setStatus] = useState<'all' | 'visible' | 'hidden'>('all');
  const [sort, setSort] = useState<AdminPoetrySort>('recent');
  const [offset, setOffset] = useState(0);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [confirm, setConfirm] = useState<null | { label: string; run: () => Promise<void> }>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(t);
  }, [search]);
  useEffect(() => { setOffset(0); setSelected(new Set()); }, [debouncedSearch, reviewStatus, status, sort, kind]);

  const loadStats = useCallback(async () => {
    try { setStats(await getAdminPoetryStats()); } catch { /* non-fatal */ }
  }, []);
  const loadList = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const res = await getAdminPoetry({ kind, q: debouncedSearch, review_status: reviewStatus, status, sort, limit: LIMIT, offset });
      setItems(res.items); setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load poetry notes');
    } finally { setLoading(false); }
  }, [kind, debouncedSearch, reviewStatus, status, sort, offset]);

  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => { loadList(); }, [loadList]);

  const refresh = () => { loadList(); loadStats(); };

  async function setReview(id: number, rs: string) {
    setBusyId(id);
    try { await updateAdminPoetry(kind, id, { review_status: rs }); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusyId(null); }
  }
  async function toggleHide(item: AdminPoetryItem) {
    setBusyId(item.id);
    try { await updateAdminPoetry(kind, item.id, { hidden: !item.hidden }); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusyId(null); }
  }
  async function saveEdit(id: number) {
    if (!editText.trim()) return;
    setBusyId(id);
    try { await updateAdminPoetry(kind, id, { markdown: editText }); setEditingId(null); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed'); }
    finally { setBusyId(null); }
  }
  async function runBulk(op: AdminExegesisBulkOp) {
    const ids = [...selected];
    if (!ids.length) return;
    await bulkAdminPoetry(kind, ids, op);
    setSelected(new Set());
    await refresh();
  }

  const allChecked = items.length > 0 && items.every((i) => selected.has(i.id));
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + LIMIT, total);
  const hasFilters = !!(debouncedSearch || reviewStatus || status !== 'all');

  const tiles = useMemo(() => stats ? [
    { label: 'Root notes', value: stats.roots },
    { label: 'Verse notes', value: stats.verses },
    { label: 'Pending', value: stats.pending, tone: stats.pending > 0 ? 'amber' : '' },
    { label: 'Approved', value: stats.approved, tone: 'emerald' },
    { label: 'Rejected', value: stats.rejected, tone: stats.rejected > 0 ? 'rose' : '' },
    { label: 'Hidden', value: stats.hidden, tone: stats.hidden > 0 ? 'amber' : '' },
  ] : [], [stats]);

  const kindStats = stats ? stats[kind] : null;

  return (
    <div>
      <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
        <div>
          <h1 className="font-serif text-2xl font-medium text-stone-800">Pre-Islamic Poetry</h1>
          <p className="text-sm text-stone-500 mt-1 max-w-2xl">
            The &ldquo;In Pre-Islamic Poetry&rdquo; comparisons (per root) and the verse-level notes that
            set a Qurʾānic verse beside the Jahilī poets. Approve, reject, fix, hide, or remove before
            they go public. Edits to the prose keep the inline <code className="text-[12px]">[[q:…]]</code> quote markers intact.
          </p>
        </div>
        <button onClick={refresh} className="text-xs text-stone-500 hover:text-stone-800 border border-stone-200 rounded-lg px-3 py-1.5 hover:border-stone-300 cursor-pointer shrink-0">Refresh</button>
      </div>

      {/* Kind toggle */}
      <div className="inline-flex rounded-lg border border-stone-200 bg-white p-0.5 mb-5">
        {(['root', 'verse'] as PoetryKind[]).map((k) => (
          <button
            key={k}
            onClick={() => setKind(k)}
            className={`px-3.5 py-1.5 text-sm rounded-md cursor-pointer transition-colors ${
              kind === k ? 'bg-amber-600 text-white' : 'text-stone-600 hover:bg-stone-50'
            }`}
          >
            {k === 'root' ? 'Root comparisons' : 'Verse notes'}
            {stats && <span className="ml-1.5 opacity-70 tabular-nums">{stats[k].total}</span>}
          </button>
        ))}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2 mb-5">
        {(stats ? tiles : Array(6).fill(null)).map((t, i) => (
          <div key={i} className="rounded-xl border border-stone-200 bg-white px-3 py-2.5">
            <div className="text-lg font-semibold text-stone-800 tabular-nums">{t ? t.value.toLocaleString() : '—'}</div>
            <div className="text-[11px] text-stone-500">{t ? t.label : ''}</div>
          </div>
        ))}
      </div>

      {kindStats && kindStats.pending > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-3 mb-4 flex items-center justify-between gap-3 flex-wrap">
          <div className="text-sm text-amber-900"><span className="font-semibold">{kindStats.pending} pending</span> {kind} note(s) awaiting review</div>
          <button onClick={() => { setStatus('all'); setReviewStatus('pending'); }} className="text-xs font-medium px-3 py-1.5 rounded-lg bg-amber-600 text-white hover:bg-amber-700 cursor-pointer shrink-0">Review pending ({kindStats.pending}) →</button>
        </div>
      )}

      {/* Toolbar */}
      <div className="rounded-xl border border-stone-200 bg-white p-3 mb-4 flex flex-wrap items-center gap-2">
        <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder={kind === 'root' ? 'Search text or root…' : 'Search text or verse…'} className="flex-1 min-w-[180px] rounded-lg border border-stone-300 px-3 py-2 text-sm outline-none focus:border-amber-400" />
        <Select value={reviewStatus} onChange={setReviewStatus} title="Review status">
          <option value="">All reviews</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </Select>
        <Select value={status} onChange={(v) => setStatus(v as 'all' | 'visible' | 'hidden')} title="Visibility">
          <option value="all">All</option>
          <option value="visible">Visible</option>
          <option value="hidden">Hidden</option>
        </Select>
        <Select value={sort} onChange={(v) => setSort(v as AdminPoetrySort)} title="Sort">
          <option value="recent">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="longest">Longest</option>
        </Select>
        {hasFilters && <button onClick={() => { setSearch(''); setReviewStatus(''); setStatus('all'); }} className="text-xs text-stone-500 hover:text-stone-800 cursor-pointer">Clear</button>}
      </div>

      {/* Bulk bar */}
      {selected.size > 0 && (
        <div className="rounded-xl border border-stone-300 bg-stone-50 p-2.5 mb-4 flex items-center gap-2 flex-wrap text-sm">
          <span className="font-medium text-stone-700">{selected.size} selected</span>
          <button onClick={() => runBulk('approve')} className="px-2.5 py-1 rounded-md bg-emerald-600 text-white text-xs hover:bg-emerald-700 cursor-pointer">Approve</button>
          <button onClick={() => runBulk('reject')} className="px-2.5 py-1 rounded-md bg-rose-600 text-white text-xs hover:bg-rose-700 cursor-pointer">Reject</button>
          <button onClick={() => runBulk('hide')} className="px-2.5 py-1 rounded-md bg-stone-600 text-white text-xs hover:bg-stone-700 cursor-pointer">Hide</button>
          <button onClick={() => setConfirm({ label: `Delete ${selected.size} ${kind} note(s)? This cannot be undone.`, run: () => runBulk('delete') })} className="px-2.5 py-1 rounded-md border border-rose-300 text-rose-700 text-xs hover:bg-rose-50 cursor-pointer">Delete</button>
          <button onClick={() => setSelected(new Set())} className="text-xs text-stone-500 hover:text-stone-800 ml-auto cursor-pointer">Clear selection</button>
        </div>
      )}

      {error && <div className="rounded-lg border border-rose-200 bg-rose-50 text-rose-700 text-sm px-3 py-2 mb-4">{error}</div>}

      {/* List header */}
      <div className="flex items-center justify-between text-xs text-stone-500 mb-2 px-1">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={allChecked} onChange={(e) => setSelected(e.target.checked ? new Set(items.map((i) => i.id)) : new Set())} />
          {total > 0 ? `${from}–${to} of ${total.toLocaleString()}` : 'No notes yet'}
        </label>
        <div className="flex gap-1">
          <button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMIT))} className="px-2 py-1 rounded border border-stone-200 disabled:opacity-40 cursor-pointer">‹ Prev</button>
          <button disabled={to >= total} onClick={() => setOffset(offset + LIMIT)} className="px-2 py-1 rounded border border-stone-200 disabled:opacity-40 cursor-pointer">Next ›</button>
        </div>
      </div>

      {loading ? (
        <div className="text-center text-stone-400 py-12 text-sm">Loading…</div>
      ) : items.length === 0 ? (
        <div className="text-center text-stone-400 py-12 text-sm">No {kind} notes match these filters.</div>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li key={item.id} className={`rounded-xl border bg-white p-4 ${item.hidden ? 'border-stone-200 opacity-70' : 'border-stone-200'}`}>
              <div className="flex items-start gap-3">
                <input type="checkbox" className="mt-1.5" checked={selected.has(item.id)} onChange={(e) => { const n = new Set(selected); if (e.target.checked) n.add(item.id); else n.delete(item.id); setSelected(n); }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <a href={item.link} target="_blank" rel="noopener noreferrer" className={`text-sm font-semibold text-amber-700 hover:underline ${kind === 'root' ? 'font-arabic text-base' : 'font-mono'}`}>{item.label}</a>
                    <ReviewBadge item={item} />
                    {item.verdict && <Badge tone={item.continuity ? 'emerald' : 'amber'}>{item.verdict}</Badge>}
                    {item.quoted_count > 0 && <Badge tone="stone">{item.quoted_count} quoted</Badge>}
                    {item.auth_tier_max && <Badge tone="stone">tier {item.auth_tier_max}</Badge>}
                    {item.hidden && <Badge tone="amber">Hidden</Badge>}
                    {item.edited_at && <Badge tone="stone">edited</Badge>}
                  </div>

                  {editingId === item.id ? (
                    <div>
                      <textarea value={editText} onChange={(e) => setEditText(e.target.value)} rows={12} className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm font-mono outline-none focus:border-amber-400" />
                      <div className="flex gap-2 mt-2">
                        <button disabled={busyId === item.id} onClick={() => saveEdit(item.id)} className="px-3 py-1.5 rounded-lg bg-amber-600 text-white text-xs hover:bg-amber-700 cursor-pointer disabled:opacity-50">Save</button>
                        <button onClick={() => setEditingId(null)} className="px-3 py-1.5 rounded-lg border border-stone-300 text-xs cursor-pointer">Cancel</button>
                      </div>
                    </div>
                  ) : (
                    <PoetryBody markdown={item.markdown} />
                  )}

                  {editingId !== item.id && (
                    <div className="flex items-center gap-1.5 mt-3 flex-wrap">
                      {item.review_status !== 'approved' && <ActBtn tone="emerald" busy={busyId === item.id} onClick={() => setReview(item.id, 'approved')}>Approve</ActBtn>}
                      {item.review_status !== 'rejected' && <ActBtn tone="rose" busy={busyId === item.id} onClick={() => setReview(item.id, 'rejected')}>Reject</ActBtn>}
                      <ActBtn tone="stone" busy={busyId === item.id} onClick={() => { setEditingId(item.id); setEditText(item.markdown); }}>Edit</ActBtn>
                      <ActBtn tone="stone" busy={busyId === item.id} onClick={() => toggleHide(item)}>{item.hidden ? 'Unhide' : 'Hide'}</ActBtn>
                      <ActBtn tone="rose-outline" busy={busyId === item.id} onClick={() => setConfirm({ label: `Delete the ${kind} note for ${item.label}? This cannot be undone.`, run: async () => { await deleteAdminPoetry(kind, item.id); await refresh(); } })}>Delete</ActBtn>
                    </div>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {confirm && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4" onClick={() => setConfirm(null)}>
          <div className="bg-white rounded-xl p-5 max-w-md w-full" onClick={(e) => e.stopPropagation()}>
            <p className="text-sm text-stone-700 mb-4">{confirm.label}</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setConfirm(null)} className="px-3 py-1.5 rounded-lg border border-stone-300 text-sm cursor-pointer">Cancel</button>
              <button onClick={async () => { const c = confirm; setConfirm(null); await c.run(); }} className="px-3 py-1.5 rounded-lg bg-rose-600 text-white text-sm hover:bg-rose-700 cursor-pointer">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Select({ value, onChange, title, children }: { value: string; onChange: (v: string) => void; title: string; children: ReactNode }) {
  return (
    <select value={value} title={title} onChange={(e) => onChange(e.target.value)} className="rounded-lg border border-stone-300 bg-white px-2.5 py-2 text-sm text-stone-700 outline-none focus:border-amber-400 cursor-pointer">
      {children}
    </select>
  );
}

function Badge({ children, tone = 'stone' }: { children: ReactNode; tone?: 'stone' | 'amber' | 'emerald' | 'rose' }) {
  const cls = { stone: 'bg-stone-100 text-stone-600 border-stone-200', amber: 'bg-amber-50 text-amber-700 border-amber-200', emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200', rose: 'bg-rose-50 text-rose-700 border-rose-200' }[tone];
  return <span className={`inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium ${cls}`}>{children}</span>;
}

function ReviewBadge({ item }: { item: AdminPoetryItem }) {
  if (item.review_status === 'approved') return <Badge tone="emerald">Approved</Badge>;
  if (item.review_status === 'rejected') return <Badge tone="rose">Rejected</Badge>;
  return <Badge tone="amber">Pending</Badge>;
}

function ActBtn({ children, onClick, tone, busy }: { children: ReactNode; onClick: () => void; tone: 'emerald' | 'rose' | 'stone' | 'rose-outline'; busy: boolean }) {
  const cls = {
    emerald: 'bg-emerald-600 text-white hover:bg-emerald-700',
    rose: 'bg-rose-600 text-white hover:bg-rose-700',
    stone: 'border border-stone-300 text-stone-600 hover:bg-stone-50',
    'rose-outline': 'border border-rose-300 text-rose-700 hover:bg-rose-50',
  }[tone];
  return <button disabled={busy} onClick={onClick} className={`px-2.5 py-1 rounded-md text-xs cursor-pointer disabled:opacity-50 ${cls}`}>{children}</button>;
}
