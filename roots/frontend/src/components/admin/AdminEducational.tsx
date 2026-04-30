import { useEffect, useState } from 'react';
import {
  getEducationalPool,
  getEducationalCandidates,
  queueEducationalCandidate,
  getEducationalVideos,
  type EducationalPool,
  type EducationalCandidate,
  type EducationalType,
  type EducationalVideo,
} from '../../api/admin';

/**
 * Admin landing for the Educational Video pipeline.
 *
 * Phase 1 (this iteration): three sub-types share one page; for each
 * we show pool size, a sample of candidates, and a "Queue" action that
 * inserts the candidate into educational_videos with status='candidate'.
 * Script generation (Phase 2) and rendering (Phase 3) will pick those
 * candidates up and progress them through the lifecycle.
 *
 * Tabs:
 *   Word Origins        — verses with content words whose root has
 *                         cognates in ≥2 distinct Semitic languages
 *   What Translators Hide — verses with substantial departure_notes
 *                         on their AI translation
 *   Grammar Insights    — verses with V7 insights at primary tier &
 *                         confidence ≥ 0.7 (counterfactuals weighted
 *                         higher because they make the strongest hooks)
 */

const TABS: { id: EducationalType; label: string; blurb: string }[] = [
  {
    id: 'word_origins',
    label: 'Word Origins',
    blurb:
      "A content word's root traced across Semitic — Arabic, Hebrew, Aramaic, Akkadian and beyond.",
  },
  {
    id: 'translation_hides',
    label: 'What Translators Hide',
    blurb:
      'Verses where standard renderings flatten a real nuance — the departure note is the payload.',
  },
  {
    id: 'grammar_insights',
    label: 'Grammar Insights',
    blurb:
      'V7 grammar moves with strong evidence — perspective shifts, counterfactuals, royal we, etc.',
  },
];

export default function AdminEducational() {
  const [pool, setPool] = useState<EducationalPool | null>(null);
  const [active, setActive] = useState<EducationalType>('word_origins');

  useEffect(() => {
    getEducationalPool().then(setPool).catch(() => setPool(null));
  }, []);

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-2">Educational Pipeline</h1>
      <p className="text-sm text-stone-500 mb-6 max-w-3xl">
        Teach-and-enlighten shorts grounded in our morphology, cognate, and
        grammar-insight data. Three series share one render flow. Phase 1 (now):
        candidate selection. Phase 2: script generation. Phase 3: visual
        templates + ffmpeg compose.
      </p>

      {/* Pool counts */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActive(t.id)}
            className={`text-left p-4 rounded-lg border transition-all ${
              active === t.id
                ? 'border-stone-800 bg-white'
                : 'border-stone-200 bg-white hover:border-stone-400'
            }`}
          >
            <div className="flex items-baseline justify-between mb-1">
              <h3 className="font-semibold text-stone-800 text-sm">{t.label}</h3>
              <span className="text-xs text-stone-400 font-mono">
                {pool ? formatPool(pool[t.id]) : '…'}
              </span>
            </div>
            <p className="text-xs text-stone-500 leading-relaxed">{t.blurb}</p>
          </button>
        ))}
      </div>

      <CandidatesPanel type={active} />

      <VideosPanel type={active} />
    </div>
  );
}

function formatPool(n: number): string {
  if (n >= 10000) return '10k+';
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

/* ------------------------------------------------------------------ */
/*  Candidates panel                                                  */
/* ------------------------------------------------------------------ */

function CandidatesPanel({ type }: { type: EducationalType }) {
  const [candidates, setCandidates] = useState<EducationalCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');
  const [bumpKey, setBumpKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErr('');
    getEducationalCandidates(type, 12)
      .then((rows) => { if (!cancelled) setCandidates(rows); })
      .catch((e) => { if (!cancelled) setErr(e instanceof Error ? e.message : String(e)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [type, bumpKey]);

  async function handleQueue(c: EducationalCandidate) {
    try {
      await queueEducationalCandidate(type, c);
      // Refresh — queued anchor is excluded from the pool.
      setBumpKey((k) => k + 1);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <section className="mb-10">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-stone-400">
          Top candidates
        </h2>
        <button
          onClick={() => setBumpKey((k) => k + 1)}
          className="text-xs text-stone-500 hover:text-stone-800 cursor-pointer"
        >
          Refresh
        </button>
      </div>

      {err && (
        <div className="mb-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {err}
        </div>
      )}

      {loading ? (
        <div className="text-sm text-stone-400">Loading…</div>
      ) : candidates.length === 0 ? (
        <div className="text-sm text-stone-400">No candidates available — pool exhausted.</div>
      ) : (
        <div className="space-y-2">
          {candidates.map((c, i) => (
            <CandidateRow key={i} type={type} candidate={c} onQueue={() => handleQueue(c)} />
          ))}
        </div>
      )}
    </section>
  );
}

function CandidateRow({
  type,
  candidate: c,
  onQueue,
}: {
  type: EducationalType;
  candidate: EducationalCandidate;
  onQueue: () => void;
}) {
  return (
    <div className="border border-stone-200 rounded-lg p-3 bg-white flex items-start gap-3">
      <div className="flex-shrink-0 text-xs font-mono text-stone-500 w-16 pt-0.5">
        {c.chapter}:{c.verse}
        {c.word_pos != null && (
          <span className="text-stone-400">·p{c.word_pos}</span>
        )}
      </div>

      <div className="flex-1 min-w-0">
        {/* Type-specific bullet points first */}
        {type === 'word_origins' && (
          <div className="text-sm text-stone-700 mb-1">
            <span dir="rtl" lang="ar" className="font-arabic text-base">
              {c.root_ar}
            </span>
            <span className="text-stone-400 ml-2 font-mono">({c.root_bw})</span>
            <span className="ml-3 text-xs text-stone-500">
              {c.lang_count} languages · {c.deriv_count} derivatives
            </span>
          </div>
        )}
        {type === 'translation_hides' && c.departure_notes && (
          <p className="text-sm text-stone-700 mb-1 line-clamp-3">
            {c.departure_notes.length > 220
              ? c.departure_notes.slice(0, 220) + '…'
              : c.departure_notes}
          </p>
        )}
        {type === 'grammar_insights' && (
          <div className="text-sm text-stone-700 mb-1">
            <span className="font-medium">{c.title}</span>
            <span className="ml-2 text-xs text-stone-500">
              {c.category}
              {c.has_counterfactual && (
                <span className="ml-1 px-1.5 py-0.5 rounded-sm bg-amber-100 text-amber-700 text-[10px]">
                  counterfactual
                </span>
              )}
              <span className="ml-2 font-mono">
                {((c.confidence ?? 0) * 100).toFixed(0)}%
              </span>
            </span>
          </div>
        )}

        {/* Verse text — same for all types */}
        {c.text_uthmani && (
          <p
            dir="rtl"
            lang="ar"
            className="font-arabic text-base text-stone-800 mb-1 truncate"
            title={c.text_uthmani}
          >
            {c.text_uthmani}
          </p>
        )}
        {c.translation && (
          <p className="text-xs text-stone-500 line-clamp-2">{c.translation}</p>
        )}
      </div>

      <div className="flex-shrink-0 flex flex-col items-end gap-1">
        <span className="text-[10px] text-stone-400 font-mono">
          score {c.score.toFixed(1)}
        </span>
        <button
          onClick={onQueue}
          className="px-2.5 py-1 rounded-md bg-stone-800 text-white text-xs font-medium hover:bg-stone-700 cursor-pointer"
        >
          Queue
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Already-queued / generated videos                                 */
/* ------------------------------------------------------------------ */

function VideosPanel({ type }: { type: EducationalType }) {
  const [videos, setVideos] = useState<EducationalVideo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getEducationalVideos(type)
      .then((rows) => { if (!cancelled) setVideos(rows); })
      .catch(() => { if (!cancelled) setVideos([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
  }, [type]);

  return (
    <section>
      <h2 className="text-sm font-semibold uppercase tracking-wider text-stone-400 mb-3">
        Queued & generated
      </h2>
      {loading ? (
        <div className="text-sm text-stone-400">Loading…</div>
      ) : videos.length === 0 ? (
        <div className="text-sm text-stone-400">
          Nothing queued for this series yet.
        </div>
      ) : (
        <div className="border border-stone-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-stone-50 text-xs text-stone-500">
              <tr>
                <th className="text-left px-3 py-2 font-medium">Verse</th>
                <th className="text-left px-3 py-2 font-medium">Anchor</th>
                <th className="text-left px-3 py-2 font-medium">Status</th>
                <th className="text-left px-3 py-2 font-medium">Created</th>
              </tr>
            </thead>
            <tbody>
              {videos.map((v) => (
                <tr key={v.id} className="border-t border-stone-100">
                  <td className="px-3 py-2 font-mono text-stone-700">
                    {v.chapter}:{v.verse}
                  </td>
                  <td className="px-3 py-2 text-stone-500 font-mono text-xs">
                    {v.anchor_word_pos != null && `p${v.anchor_word_pos}`}
                    {v.anchor_insight_id || ''}
                    {v.anchor_word_pos == null && !v.anchor_insight_id && '—'}
                  </td>
                  <td className="px-3 py-2">
                    <StatusPill status={v.status} />
                  </td>
                  <td className="px-3 py-2 text-stone-400 text-xs">
                    {formatDate(v.created_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function StatusPill({ status }: { status: EducationalVideo['status'] }) {
  const tone =
    status === 'failed' ? 'bg-red-100 text-red-700'
    : status === 'uploaded' ? 'bg-green-100 text-green-700'
    : status === 'rendered' ? 'bg-emerald-100 text-emerald-700'
    : status === 'rendering' ? 'bg-amber-100 text-amber-700'
    : status === 'script_ready' ? 'bg-blue-100 text-blue-700'
    : 'bg-stone-100 text-stone-600';
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${tone}`}>
      {status}
    </span>
  );
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return '';
  try {
    return new Date(iso.includes('T') ? iso : iso + 'Z').toLocaleString();
  } catch {
    return iso;
  }
}
