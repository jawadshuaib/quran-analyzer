import { useState, useEffect, useCallback, type ReactNode } from 'react';
import {
  getAdminQA, getAdminQAStats, updateAdminQA, deleteAdminQA,
  type AdminQAItem, type AdminQAStats, type AdminQAStatus, type AdminQASort,
} from '../../api/admin';

const LIMIT = 25;

/* ---------------------------------------------------------------- */
/*  Helpers                                                          */
/* ---------------------------------------------------------------- */

/** Deep-link to the public page a Q&A is anchored to, when we know the
 *  URL shape. Verse is the common case the admin actually wants to open. */
function pageHref(item: AdminQAItem): string | null {
  if (item.page_type === 'verse') return `/verse/${item.page_key}`;
  if (item.page_type === 'word') return `/word/${item.page_key}`;
  if (item.page_type === 'root') return `/root/${item.page_key}`;
  return null;
}

function pageLabel(item: AdminQAItem): string {
  if (item.page_type === 'verse') {
    const [s, a] = item.page_key.split(':');
    return a ? `Surah ${s} · Ayah ${a}` : item.page_key;
  }
  return `${item.page_type} · ${item.page_key}`;
}

/** created_at/edited_at are stored UTC without a 'Z' suffix. */
function parseUtc(ts: string): Date {
  return new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(ts) ? ts : ts + 'Z');
}

function relTime(ts: string): string {
  const d = parseUtc(ts);
  const diff = Date.now() - d.getTime();
  if (isNaN(diff)) return '';
  const min = Math.round(diff / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min}m ago`;
  const h = Math.round(min / 60);
  if (h < 24) return `${h}h ago`;
  const days = Math.round(h / 24);
  if (days < 30) return `${days}d ago`;
  return d.toLocaleDateString();
}

/** Trim noisy model tags to something scannable in a badge. */
function shortModel(model: string | null): string {
  if (!model) return 'unknown';
  return model.replace(/^anthropic\//, '').replace(/-\d{8}$/, '');
}

/* ---------------------------------------------------------------- */
/*  Main                                                            */
/* ---------------------------------------------------------------- */

export default function AdminAssistantQA() {
  const [stats, setStats] = useState<AdminQAStats | null>(null);
  const [items, setItems] = useState<AdminQAItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Query controls
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [pageType, setPageType] = useState('');
  const [model, setModel] = useState('');
  const [status, setStatus] = useState<AdminQAStatus>('all');
  const [sort, setSort] = useState<AdminQASort>('recent');
  const [offset, setOffset] = useState(0);

  // Per-row interaction
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editQuestion, setEditQuestion] = useState('');
  const [editAnswer, setEditAnswer] = useState('');
  const [busyId, setBusyId] = useState<number | null>(null);

  // Confirmation dialog for consequential one-click actions (hide / unhide /
  // delete). Each changes what the public sees, so none of them fire until
  // the admin confirms in the dialog.
  const [pending, setPending] = useState<{ kind: 'hide' | 'unhide' | 'delete'; item: AdminQAItem } | null>(null);
  const [actionBusy, setActionBusy] = useState(false);
  const [actionError, setActionError] = useState('');

  // Debounce the search box
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => clearTimeout(t);
  }, [search]);

  // Any filter change resets us to the first page
  useEffect(() => { setOffset(0); }, [debouncedSearch, pageType, model, status, sort]);

  const loadStats = useCallback(async () => {
    try { setStats(await getAdminQAStats()); } catch { /* non-fatal */ }
  }, []);

  const loadList = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await getAdminQA({
        q: debouncedSearch, page_type: pageType, model, status, sort,
        limit: LIMIT, offset,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load Q&A');
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch, pageType, model, status, sort, offset]);

  useEffect(() => { loadStats(); }, [loadStats]);
  useEffect(() => { loadList(); }, [loadList]);

  /* --- actions --- */

  // Runs the action the admin confirmed in the dialog. Hide/unhide/delete
  // all flow through here so there's a single confirmed-write path.
  async function runPending() {
    if (!pending) return;
    const { kind, item } = pending;
    setActionBusy(true);
    setActionError('');
    try {
      if (kind === 'delete') {
        await deleteAdminQA(item.id);
        setItems((prev) => prev.filter((i) => i.id !== item.id));
        setTotal((t) => Math.max(0, t - 1));
      } else {
        const updated = await updateAdminQA(item.id, { hidden: kind === 'hide' });
        applyUpdate(updated);
      }
      loadStats();
      setPending(null);
    } catch (e) {
      setActionError(e instanceof Error ? e.message : 'Action failed');
    } finally {
      setActionBusy(false);
    }
  }

  function startEdit(item: AdminQAItem) {
    setEditingId(item.id);
    setEditQuestion(item.question);
    setEditAnswer(item.answer);
    setExpandedId(item.id);
  }

  async function saveEdit(item: AdminQAItem) {
    if (!editQuestion.trim() || !editAnswer.trim()) {
      setError('Question and answer cannot be empty.');
      return;
    }
    setBusyId(item.id);
    setError('');
    try {
      const updated = await updateAdminQA(item.id, {
        question: editQuestion.trim(),
        answer: editAnswer.trim(),
      });
      applyUpdate(updated);
      setEditingId(null);
      loadStats();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed');
    } finally {
      setBusyId(null);
    }
  }

  function applyUpdate(updated: AdminQAItem) {
    setItems((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
  }

  const hasActiveFilters = !!(debouncedSearch || pageType || model || status !== 'all');
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + LIMIT, total);

  return (
    <div>
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
        <div>
          <h1 className="font-serif text-2xl font-medium text-stone-800">Ask the Quran</h1>
          <p className="text-sm text-stone-500 mt-1 max-w-2xl">
            Every answer the assistant gives is saved and shown to the next visitor of
            that verse. Review what's being asked, fix or hide weak answers, and remove spam.
          </p>
        </div>
        <button
          onClick={() => { loadList(); loadStats(); }}
          className="text-xs text-stone-500 hover:text-stone-800 border border-stone-200 rounded-lg px-3 py-1.5 hover:border-stone-300 transition-colors cursor-pointer shrink-0"
        >
          Refresh
        </button>
      </div>

      {/* Stats strip */}
      <StatsStrip stats={stats} />

      {/* Insights: most-asked verses + model mix */}
      {stats && (stats.top_pages.length > 0 || stats.by_model.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 mb-6">
          <TopPagesPanel stats={stats} onPick={(pt, pk) => { setPageType(pt); setSearch(''); setSearch(pk); }} />
          <ModelMixPanel stats={stats} />
        </div>
      )}

      {/* Toolbar */}
      <div className="rounded-xl border border-stone-200 bg-white p-3 mb-4">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex-1 min-w-[200px]">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11a6 6 0 11-12 0 6 6 0 0112 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search questions and answers…"
              className="w-full rounded-lg border border-stone-300 pl-9 pr-3 py-2 text-sm focus:border-violet-400 focus:ring-1 focus:ring-violet-400 outline-none"
            />
          </div>

          <Select value={pageType} onChange={setPageType} title="Page type">
            <option value="">All types</option>
            {(stats?.by_type ?? []).map((t) => (
              <option key={t.page_type} value={t.page_type}>{t.page_type} ({t.count})</option>
            ))}
          </Select>

          <Select value={model} onChange={setModel} title="Model">
            <option value="">All models</option>
            {(stats?.by_model ?? []).filter((m) => m.model !== 'unknown').map((m) => (
              <option key={m.model} value={m.model}>{shortModel(m.model)} ({m.count})</option>
            ))}
          </Select>

          <Select value={status} onChange={(v) => setStatus(v as AdminQAStatus)} title="Visibility">
            <option value="all">All</option>
            <option value="visible">Visible</option>
            <option value="hidden">Hidden</option>
          </Select>

          <Select value={sort} onChange={(v) => setSort(v as AdminQASort)} title="Sort">
            <option value="recent">Newest</option>
            <option value="oldest">Oldest</option>
            <option value="slowest">Slowest</option>
            <option value="longest">Longest answer</option>
          </Select>
        </div>
      </div>

      {/* Results meta */}
      <div className="flex items-center justify-between mb-2 px-1">
        <p className="text-xs text-stone-500">
          {loading ? 'Loading…' : total === 0
            ? (hasActiveFilters ? 'No Q&A match these filters' : 'No questions have been asked yet')
            : `Showing ${from}–${to} of ${total.toLocaleString()}`}
        </p>
        {hasActiveFilters && (
          <button
            onClick={() => { setSearch(''); setPageType(''); setModel(''); setStatus('all'); }}
            className="text-xs text-violet-600 hover:text-violet-800 cursor-pointer"
          >
            Clear filters
          </button>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 text-red-700 text-sm px-3 py-2 mb-3">{error}</div>
      )}

      {/* List */}
      {loading && items.length === 0 ? (
        <div className="flex justify-center py-16">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
        </div>
      ) : items.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-300 bg-stone-50/40 p-10 text-center text-sm text-stone-500">
          {hasActiveFilters
            ? 'Nothing matches. Try clearing the filters.'
            : 'When visitors ask the assistant about a verse, their Q&A will appear here.'}
        </div>
      ) : (
        <div className={`space-y-3 ${loading ? 'opacity-60 pointer-events-none' : ''}`}>
          {items.map((item) => (
            <QACard
              key={item.id}
              item={item}
              expanded={expandedId === item.id}
              editing={editingId === item.id}
              busy={busyId === item.id}
              editQuestion={editQuestion}
              editAnswer={editAnswer}
              onToggleExpand={() => setExpandedId(expandedId === item.id ? null : item.id)}
              onRequestToggleHidden={() => setPending({ kind: item.hidden ? 'unhide' : 'hide', item })}
              onStartEdit={() => startEdit(item)}
              onChangeQuestion={setEditQuestion}
              onChangeAnswer={setEditAnswer}
              onSaveEdit={() => saveEdit(item)}
              onCancelEdit={() => setEditingId(null)}
              onRequestDelete={() => setPending({ kind: 'delete', item })}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > LIMIT && (
        <div className="flex items-center justify-between mt-5">
          <button
            disabled={offset === 0 || loading}
            onClick={() => setOffset(Math.max(0, offset - LIMIT))}
            className="text-sm px-3 py-1.5 rounded-lg border border-stone-200 text-stone-600 hover:border-stone-300 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            ← Previous
          </button>
          <span className="text-xs text-stone-400">Page {Math.floor(offset / LIMIT) + 1} of {Math.max(1, Math.ceil(total / LIMIT))}</span>
          <button
            disabled={to >= total || loading}
            onClick={() => setOffset(offset + LIMIT)}
            className="text-sm px-3 py-1.5 rounded-lg border border-stone-200 text-stone-600 hover:border-stone-300 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            Next →
          </button>
        </div>
      )}

      <ConfirmDialog
        pending={pending}
        busy={actionBusy}
        error={actionError}
        onConfirm={runPending}
        onCancel={() => { if (!actionBusy) { setPending(null); setActionError(''); } }}
      />
    </div>
  );
}

/* ---------------------------------------------------------------- */
/*  Stats strip                                                     */
/* ---------------------------------------------------------------- */

function StatsStrip({ stats }: { stats: AdminQAStats | null }) {
  const tiles: { label: string; value: string; tone?: string }[] = stats ? [
    { label: 'Total Q&A', value: stats.total.toLocaleString() },
    { label: 'Visible', value: stats.visible.toLocaleString() },
    { label: 'Hidden', value: stats.hidden.toLocaleString(), tone: stats.hidden > 0 ? 'amber' : undefined },
    { label: 'Verses & pages', value: stats.pages.toLocaleString() },
    { label: 'Last 7 days', value: stats.last_7_days.toLocaleString() },
    { label: 'Askers', value: stats.sessions.toLocaleString() },
  ] : [];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
      {(stats ? tiles : Array(6).fill(null)).map((t, i) => (
        <div
          key={i}
          className={`rounded-xl border px-4 py-3 ${
            t?.tone === 'amber' ? 'border-amber-200 bg-amber-50/40' : 'border-stone-200 bg-white'
          }`}
        >
          {t ? (
            <>
              <div className="text-[10px] font-semibold uppercase tracking-wider text-stone-500 mb-1">{t.label}</div>
              <div className="text-2xl font-semibold text-stone-800 tracking-tight">{t.value}</div>
            </>
          ) : (
            <>
              <div className="h-3 w-16 bg-stone-100 rounded animate-pulse mb-2" />
              <div className="h-6 w-10 bg-stone-100 rounded animate-pulse" />
            </>
          )}
        </div>
      ))}
    </div>
  );
}

function TopPagesPanel({ stats, onPick }: { stats: AdminQAStats; onPick: (pageType: string, pageKey: string) => void }) {
  if (stats.top_pages.length === 0) return null;
  const max = Math.max(...stats.top_pages.map((p) => p.count), 1);
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">Most asked</h2>
      <ul className="space-y-1.5">
        {stats.top_pages.map((p) => {
          const label = p.page_type === 'verse'
            ? p.page_key
            : `${p.page_type} ${p.page_key}`;
          return (
            <li key={`${p.page_type}:${p.page_key}`}>
              <button
                onClick={() => onPick(p.page_type, p.page_key)}
                className="w-full group flex items-center gap-2 text-left cursor-pointer"
                title="Filter to this page"
              >
                <span className="w-20 shrink-0 text-xs font-medium text-stone-700 group-hover:text-violet-700 tabular-nums">{label}</span>
                <span className="flex-1 h-2 rounded-full bg-stone-100 overflow-hidden">
                  <span className="block h-full bg-violet-300 group-hover:bg-violet-400 transition-colors" style={{ width: `${(p.count / max) * 100}%` }} />
                </span>
                <span className="w-6 shrink-0 text-right text-xs text-stone-400 tabular-nums">{p.count}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function ModelMixPanel({ stats }: { stats: AdminQAStats }) {
  if (stats.by_model.length === 0) return null;
  return (
    <div className="rounded-xl border border-stone-200 bg-white p-4">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">Models used</h2>
      <div className="flex flex-wrap gap-1.5">
        {stats.by_model.map((m) => (
          <span key={m.model} className="inline-flex items-center gap-1.5 rounded-full border border-stone-200 bg-stone-50 px-2.5 py-1 text-xs text-stone-600">
            {shortModel(m.model)}
            <span className="font-semibold text-stone-800 tabular-nums">{m.count}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- */
/*  Small UI atoms                                                  */
/* ---------------------------------------------------------------- */

function Select({ value, onChange, title, children }: {
  value: string; onChange: (v: string) => void; title: string; children: ReactNode;
}) {
  return (
    <select
      value={value}
      title={title}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-stone-300 bg-white px-2.5 py-2 text-sm text-stone-700 focus:border-violet-400 focus:ring-1 focus:ring-violet-400 outline-none cursor-pointer"
    >
      {children}
    </select>
  );
}

function Badge({ children, tone = 'stone' }: { children: ReactNode; tone?: 'stone' | 'violet' | 'amber' | 'sky' | 'emerald' }) {
  const cls = {
    stone: 'bg-stone-100 text-stone-600 border-stone-200',
    violet: 'bg-violet-50 text-violet-700 border-violet-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    sky: 'bg-sky-50 text-sky-700 border-sky-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  }[tone];
  return <span className={`inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10px] font-medium ${cls}`}>{children}</span>;
}

/* ---------------------------------------------------------------- */
/*  Q&A card                                                        */
/* ---------------------------------------------------------------- */

interface QACardProps {
  item: AdminQAItem;
  expanded: boolean;
  editing: boolean;
  busy: boolean;
  editQuestion: string;
  editAnswer: string;
  onToggleExpand: () => void;
  onRequestToggleHidden: () => void;
  onStartEdit: () => void;
  onChangeQuestion: (v: string) => void;
  onChangeAnswer: (v: string) => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onRequestDelete: () => void;
}

function QACard(p: QACardProps) {
  const { item } = p;
  const href = pageHref(item);

  return (
    <div className={`rounded-xl border bg-white transition-colors ${item.hidden ? 'border-amber-200 bg-amber-50/20' : 'border-stone-200'}`}>
      <div className="p-4">
        {/* Top meta row */}
        <div className="flex items-center justify-between gap-3 mb-2 flex-wrap">
          <div className="flex items-center gap-2 flex-wrap min-w-0">
            {href ? (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm font-semibold text-violet-700 hover:text-violet-900 hover:underline whitespace-nowrap"
                title="Open the public page in a new tab"
              >
                {pageLabel(item)} ↗
              </a>
            ) : (
              <span className="text-sm font-semibold text-stone-700">{pageLabel(item)}</span>
            )}
            <Badge tone="sky">{item.page_type}</Badge>
            {item.context_range && <Badge tone="stone">range {item.context_range}</Badge>}
            {item.hidden && <Badge tone="amber">Hidden</Badge>}
            {item.edited_at && <Badge tone="violet">Edited</Badge>}
          </div>
          <div className="flex items-center gap-2 text-xs text-stone-400 shrink-0">
            <span title={shortModel(item.model_used)} className="max-w-[140px] truncate">{shortModel(item.model_used)}</span>
            {item.response_time_ms != null && <span>· {(item.response_time_ms / 1000).toFixed(1)}s</span>}
            <span title={parseUtc(item.created_at).toLocaleString()}>· {relTime(item.created_at)}</span>
          </div>
        </div>

        {p.editing ? (
          /* --- Edit mode --- */
          <div className="space-y-2">
            <label className="block text-[11px] font-medium text-stone-500">Question</label>
            <textarea
              value={p.editQuestion}
              onChange={(e) => p.onChangeQuestion(e.target.value)}
              rows={2}
              maxLength={500}
              className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm focus:border-violet-400 focus:ring-1 focus:ring-violet-400 outline-none"
            />
            <label className="block text-[11px] font-medium text-stone-500">Answer (shown publicly)</label>
            <textarea
              value={p.editAnswer}
              onChange={(e) => p.onChangeAnswer(e.target.value)}
              rows={10}
              className="w-full rounded-lg border border-stone-300 px-3 py-2 text-sm font-mono leading-relaxed focus:border-violet-400 focus:ring-1 focus:ring-violet-400 outline-none"
            />
            <div className="flex items-center gap-2">
              <button
                onClick={p.onSaveEdit}
                disabled={p.busy}
                className="px-3 py-1.5 rounded-lg bg-violet-600 text-white text-sm font-medium hover:bg-violet-700 disabled:opacity-50 cursor-pointer"
              >
                {p.busy ? 'Saving…' : 'Save changes'}
              </button>
              <button
                onClick={p.onCancelEdit}
                disabled={p.busy}
                className="px-3 py-1.5 rounded-lg border border-stone-200 text-stone-600 text-sm hover:border-stone-300 cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          /* --- View mode --- */
          <>
            <p className="text-sm font-semibold text-stone-800 mb-1">{item.question}</p>
            <div
              onClick={p.onToggleExpand}
              className={`text-sm text-stone-600 leading-relaxed whitespace-pre-wrap cursor-pointer ${p.expanded ? '' : 'line-clamp-3'}`}
              title={p.expanded ? 'Click to collapse' : 'Click to expand'}
            >
              {item.answer}
            </div>
            {!p.expanded && item.answer.length > 220 && (
              <button onClick={p.onToggleExpand} className="text-xs text-violet-500 hover:text-violet-700 mt-1 cursor-pointer">
                Show full answer
              </button>
            )}

            {p.expanded && (item.context_summary || item.session_short) && (
              <div className="mt-3 pt-3 border-t border-stone-100 text-[11px] text-stone-400 space-y-1">
                {item.context_summary && (
                  <p><span className="font-medium text-stone-500">Context:</span> {item.context_summary}</p>
                )}
                <p>
                  <span className="font-medium text-stone-500">Asker:</span> {item.session_short || '—'}
                  {item.edited_at && <> · edited {relTime(item.edited_at)}</>}
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center gap-1.5 mt-3 pt-3 border-t border-stone-100 flex-wrap">
              {href && (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs px-2.5 py-1 rounded-md border border-stone-200 text-stone-600 hover:border-stone-300 hover:bg-stone-50 cursor-pointer"
                >
                  Open verse
                </a>
              )}
              <button
                onClick={p.onRequestToggleHidden}
                disabled={p.busy}
                className={`text-xs px-2.5 py-1 rounded-md border cursor-pointer disabled:opacity-50 ${
                  item.hidden
                    ? 'border-emerald-200 text-emerald-700 hover:bg-emerald-50'
                    : 'border-amber-200 text-amber-700 hover:bg-amber-50'
                }`}
              >
                {item.hidden ? 'Unhide' : 'Hide'}
              </button>
              <button
                onClick={p.onStartEdit}
                disabled={p.busy}
                className="text-xs px-2.5 py-1 rounded-md border border-stone-200 text-stone-600 hover:border-stone-300 hover:bg-stone-50 cursor-pointer disabled:opacity-50"
              >
                Edit
              </button>
              <button
                onClick={p.onRequestDelete}
                disabled={p.busy}
                className="text-xs px-2.5 py-1 rounded-md border border-stone-200 text-red-500 hover:border-red-200 hover:bg-red-50 cursor-pointer ml-auto disabled:opacity-50"
              >
                Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- */
/*  Confirmation dialog                                             */
/* ---------------------------------------------------------------- */

const CONFIRM_COPY = {
  hide: {
    title: 'Hide this answer?',
    body: 'It will immediately stop showing to visitors on this verse. Nothing is deleted — you can unhide it again at any time.',
    confirm: 'Hide',
    tone: 'amber' as const,
  },
  unhide: {
    title: 'Make this answer public again?',
    body: 'It will be shown to visitors on this verse the next time they open the assistant.',
    confirm: 'Unhide',
    tone: 'emerald' as const,
  },
  delete: {
    title: 'Delete this Q&A permanently?',
    body: 'This removes the question and answer for good and cannot be undone. If you only want to take it off the public page, use Hide instead.',
    confirm: 'Delete permanently',
    tone: 'danger' as const,
  },
};

function ConfirmDialog({ pending, busy, error, onConfirm, onCancel }: {
  pending: { kind: 'hide' | 'unhide' | 'delete'; item: AdminQAItem } | null;
  busy: boolean;
  error: string;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  // Esc cancels. We deliberately do NOT bind Enter to confirm so a stray
  // keypress can't trigger a destructive action.
  useEffect(() => {
    if (!pending) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !busy) onCancel(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [pending, busy, onCancel]);

  if (!pending) return null;
  const copy = CONFIRM_COPY[pending.kind];
  const confirmCls = {
    amber: 'bg-amber-600 hover:bg-amber-700',
    emerald: 'bg-emerald-600 hover:bg-emerald-700',
    danger: 'bg-red-600 hover:bg-red-700',
  }[copy.tone];

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm"
      onClick={() => !busy && onCancel()}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="w-full max-w-md rounded-2xl bg-white shadow-2xl border border-stone-200 p-5"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="text-base font-semibold text-stone-900">{copy.title}</h3>
        <p className="text-sm text-stone-600 mt-2 leading-relaxed">{copy.body}</p>

        <div className="mt-3 rounded-lg bg-stone-50 border border-stone-100 px-3 py-2">
          <p className="text-[11px] font-medium uppercase tracking-wider text-stone-400">{pageLabel(pending.item)}</p>
          <p className="text-sm text-stone-700 line-clamp-2">{pending.item.question}</p>
        </div>

        {error && (
          <div className="mt-3 rounded-lg border border-red-200 bg-red-50 text-red-700 text-xs px-3 py-2">{error}</div>
        )}

        <div className="flex items-center justify-end gap-2 mt-5">
          <button
            onClick={onCancel}
            disabled={busy}
            className="px-3 py-1.5 rounded-lg border border-stone-200 text-stone-600 text-sm hover:border-stone-300 cursor-pointer disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className={`px-3 py-1.5 rounded-lg text-white text-sm font-medium cursor-pointer disabled:opacity-60 ${confirmCls}`}
          >
            {busy ? 'Working…' : copy.confirm}
          </button>
        </div>
      </div>
    </div>
  );
}
