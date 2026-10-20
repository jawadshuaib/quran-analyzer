import { useCallback, useEffect, useState } from 'react';
import {
  getAdminAltTranslations, updateAdminAltTranslation,
  type AdminAltItem, type AdminAltListResponse, type AdminAltStatus,
} from '../../api/admin';

const LIMIT = 25;

const TIER_LABEL: Record<number, string> = {
  0: '0 · hidden',
  1: '1 · light link',
  2: '2 · dark link',
  3: '3 · shown',
};

const STATUS_TABS: { key: AdminAltStatus; label: string }[] = [
  { key: 'pending', label: 'Needs review' },
  { key: 'shown', label: 'Shown on site' },
  { key: 'hidden', label: 'Hidden' },
  { key: 'all', label: 'All' },
];

/* Difference types that count against OUR translation get a red chip so the
   reviewer sees at a glance why a verse is in the queue. */
const TYPE_TONE: Record<string, string> = {
  ours_omits: 'bg-red-50 text-red-700 ring-red-100',
  ours_mistranslates: 'bg-red-50 text-red-700 ring-red-100',
  alt_reading: 'bg-amber-50 text-amber-700 ring-amber-100',
  nuance: 'bg-sky-50 text-sky-700 ring-sky-100',
};

function AltRow({ item, onChanged }: { item: AdminAltItem; onChanged: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [note, setNote] = useState(item.note);
  const [showJudges, setShowJudges] = useState(item.needs_review);

  const patch = async (p: Parameters<typeof updateAdminAltTranslation>[1]) => {
    setBusy(true); setError('');
    try { await updateAdminAltTranslation(item.ref, p); onChanged(); }
    catch (e) { setError(e instanceof Error ? e.message : 'Update failed'); }
    finally { setBusy(false); }
  };

  return (
    <li className="rounded-xl border border-stone-200 bg-white p-4">
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <a href={`/verse/${item.ref}`} target="_blank" rel="noreferrer"
           className="font-semibold text-stone-800 hover:underline">{item.ref}</a>
        <span className="rounded bg-stone-100 px-1.5 py-0.5 text-stone-600">{TIER_LABEL[item.tier]}</span>
        <span className="text-stone-400">{item.review_status}</span>
        {item.needs_review && <span className="rounded bg-red-50 px-1.5 py-0.5 text-red-700">judge flags ours</span>}
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <div>
          <div className="text-[11px] uppercase tracking-wide text-stone-400">Ours</div>
          <p className="mt-1 text-sm leading-relaxed text-stone-700">{item.ours}</p>
        </div>
        <div>
          <div className="text-[11px] uppercase tracking-wide text-stone-400">{item.translator}</div>
          <p className="mt-1 text-sm leading-relaxed text-stone-700">{item.text}</p>
        </div>
      </div>

      <label className="mt-3 block text-[11px] uppercase tracking-wide text-stone-400">Reader note</label>
      <textarea
        value={note}
        onChange={(e) => setNote(e.target.value)}
        rows={2}
        className="mt-1 w-full rounded-lg border border-stone-200 p-2 text-sm text-stone-700"
      />

      <button type="button" onClick={() => setShowJudges((s) => !s)}
              className="mt-2 text-xs text-stone-500 hover:text-stone-800">
        {showJudges ? 'Hide' : 'Show'} judges' reasoning
      </button>
      {showJudges && (
        <div className="mt-2 space-y-3">
          {item.judges.map((j) => (
            <div key={j.model} className="rounded-lg bg-stone-50 p-3 text-xs text-stone-600">
              <div className="font-medium text-stone-800">{j.model} · tier {j.tier} · picked {j.best}</div>
              {j.summary && <p className="mt-1">{j.summary}</p>}
              {j.ours_check.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {j.ours_check.map((o, i) => (
                    <li key={i}><span className="text-red-700">audit · {o.problem}</span> <span dir="rtl">{o.arabic}</span>: {o.why}</li>
                  ))}
                </ul>
              )}
              <ul className="mt-2 space-y-1">
                {j.differences.map((d, i) => (
                  <li key={i}>
                    <span className={`mr-1 rounded px-1 py-px ring-1 ${TYPE_TONE[d.type ?? ''] ?? 'bg-white text-stone-500 ring-stone-200'}`}>{d.type}</span>
                    “{d.ours}” → “{d.best}” — {d.why}
                    {d.verifier && (
                      <span className="ml-1 text-stone-400">
                        [verifier: {d.verifier}{d.verifier_reason ? ` — ${d.verifier_reason}` : ''}]
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button type="button" disabled={busy}
                onClick={() => patch({ review_status: 'approved', note })}
                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 disabled:opacity-50">
          Approve
        </button>
        <button type="button" disabled={busy}
                onClick={() => patch({ review_status: 'hidden' })}
                className="rounded-lg border border-stone-300 px-3 py-1.5 text-xs text-stone-700 hover:bg-stone-50 disabled:opacity-50">
          Hide
        </button>
        <span className="ml-2 text-xs text-stone-400">Set tier:</span>
        {[0, 1, 2, 3].map((t) => (
          <button key={t} type="button" disabled={busy || t === item.tier}
                  onClick={() => patch({ tier: t, note })}
                  className="rounded border border-stone-200 px-2 py-1 text-xs text-stone-600 hover:bg-stone-50 disabled:opacity-40">
            {t}
          </button>
        ))}
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
    </li>
  );
}

export default function AdminAltTranslations() {
  const [status, setStatus] = useState<AdminAltStatus>('pending');
  const [tier, setTier] = useState<number | ''>('');
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<AdminAltListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => { setOffset(0); }, [status, tier]);

  const load = useCallback(async () => {
    setLoading(true); setError('');
    try { setData(await getAdminAltTranslations({ status, tier, limit: LIMIT, offset })); }
    catch (e) { setError(e instanceof Error ? e.message : 'Failed to load'); }
    finally { setLoading(false); }
  }, [status, tier, offset]);

  useEffect(() => { load(); }, [load]);

  const counts = data?.counts;

  return (
    <div className="mx-auto max-w-5xl">
      <h1 className="text-xl font-semibold text-stone-800">Alternative translations</h1>
      <p className="mt-1 text-sm text-stone-500">
        The most Qur&apos;an-faithful public-domain translation for each verse, picked and graded by two
        LLM judges. “Needs review” lists verses where a judge says our own translation leaves something
        out or breaks the grammar: fix ours, or approve or hide the alternative.
      </p>
      {counts && (
        <p className="mt-2 text-xs text-stone-500">
          Tiers (not hidden): {[3, 2, 1, 0].map((t) => `${TIER_LABEL[t]} ${counts.tiers[String(t)] ?? 0}`).join(' · ')}
          {' · '}needs review {counts.pending} · hidden {counts.hidden}
        </p>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        {STATUS_TABS.map((t) => (
          <button key={t.key} type="button" onClick={() => setStatus(t.key)}
                  className={`rounded-full px-3 py-1 text-xs ${status === t.key ? 'bg-stone-800 text-white' : 'bg-stone-100 text-stone-600 hover:bg-stone-200'}`}>
            {t.label}
          </button>
        ))}
        <select value={tier} onChange={(e) => setTier(e.target.value === '' ? '' : Number(e.target.value))}
                className="ml-auto rounded-lg border border-stone-200 px-2 py-1 text-xs text-stone-600">
          <option value="">All tiers</option>
          {[3, 2, 1, 0].map((t) => <option key={t} value={t}>{TIER_LABEL[t]}</option>)}
        </select>
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}
      {loading && !data && <p className="mt-4 text-sm text-stone-400">Loading…</p>}
      {data && data.items.length === 0 && !loading && (
        <p className="mt-6 text-sm text-stone-400">Nothing here.</p>
      )}
      <ul className="mt-4 space-y-3">
        {data?.items.map((item) => <AltRow key={item.ref} item={item} onChanged={load} />)}
      </ul>

      {data && data.total > LIMIT && (
        <div className="mt-4 flex items-center justify-between text-xs text-stone-500">
          <button type="button" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - LIMIT))}
                  className="rounded border border-stone-200 px-3 py-1 disabled:opacity-40">Previous</button>
          <span>{offset + 1}–{Math.min(offset + LIMIT, data.total)} of {data.total}</span>
          <button type="button" disabled={offset + LIMIT >= data.total} onClick={() => setOffset(offset + LIMIT)}
                  className="rounded border border-stone-200 px-3 py-1 disabled:opacity-40">Next</button>
        </div>
      )}
    </div>
  );
}
