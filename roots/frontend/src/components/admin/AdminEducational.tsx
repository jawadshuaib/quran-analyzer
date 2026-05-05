import { useEffect, useState } from 'react';
import {
  getEducationalPool,
  getEducationalCandidates,
  queueEducationalCandidate,
  getEducationalVideos,
  getEducationalVideoDetail,
  generateEducationalScript,
  editEducationalScript,
  renderEducationalVideo,
  type EducationalPool,
  type EducationalCandidate,
  type EducationalType,
  type EducationalVideo,
  type EducationalVideoDetail,
  type ScriptEdits,
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
      <div className="flex items-start justify-between gap-3 mb-2">
        <h1 className="text-xl font-semibold text-stone-800">Educational Pipeline</h1>
        <a
          href="/admin/media/educational/pipelines"
          className="px-3 py-1.5 rounded-md border border-stone-300 bg-white text-stone-700 text-sm font-medium hover:bg-stone-50"
        >
          Manage pipelines →
        </a>
      </div>
      <p className="text-sm text-stone-500 mb-6 max-w-3xl">
        Teach-and-enlighten shorts grounded in our morphology, cognate, and
        grammar-insight data. Below: browse the candidate pool and queue / generate
        manually. For automated runs configure a <a href="/admin/media/educational/pipelines" className="underline">pipeline</a>.
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
  // Grammar Insights only — filter the visible candidates by V7
  // category. 'all' shows everything. Calculated client-side from
  // the loaded list so changing the filter doesn't refetch.
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setErr('');
    // Pull a deeper pool for grammar so the category filter has
    // material to work with — different categories may be sparse.
    const fetchLimit = type === 'grammar_insights' ? 40 : 12;
    getEducationalCandidates(type, fetchLimit)
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

  // Distinct categories present in the current candidate list
  // (grammar only). Sorted by frequency desc so the most common
  // categories appear first in the filter dropdown.
  const categoryCounts = (() => {
    if (type !== 'grammar_insights') return [];
    const map = new Map<string, number>();
    for (const c of candidates) {
      const k = c.category || '(uncategorized)';
      map.set(k, (map.get(k) ?? 0) + 1);
    }
    return Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
  })();

  const visibleCandidates = (
    type === 'grammar_insights' && categoryFilter !== 'all'
      ? candidates.filter((c) => (c.category || '(uncategorized)') === categoryFilter)
      : candidates
  ).slice(0, 12);

  return (
    <section className="mb-10">
      <div className="flex items-baseline justify-between mb-3 gap-3 flex-wrap">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-stone-400">
          Top candidates
        </h2>
        <div className="flex items-center gap-3">
          {type === 'grammar_insights' && categoryCounts.length > 1 && (
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="text-xs border border-stone-200 rounded-md px-2 py-1 bg-white text-stone-700"
              aria-label="Filter by V7 category"
            >
              <option value="all">All categories ({candidates.length})</option>
              {categoryCounts.map(([cat, count]) => (
                <option key={cat} value={cat}>
                  {cat.replace(/_/g, ' ')} ({count})
                </option>
              ))}
            </select>
          )}
          <button
            onClick={() => setBumpKey((k) => k + 1)}
            className="text-xs text-stone-500 hover:text-stone-800 cursor-pointer"
          >
            Refresh
          </button>
        </div>
      </div>

      {err && (
        <div className="mb-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
          {err}
        </div>
      )}

      {loading ? (
        <div className="text-sm text-stone-400">Loading…</div>
      ) : visibleCandidates.length === 0 ? (
        <div className="text-sm text-stone-400">No candidates available — pool exhausted.</div>
      ) : (
        <div className="space-y-2">
          {visibleCandidates.map((c, i) => (
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
          <>
            <div className="text-sm text-stone-700 mb-1 flex items-center flex-wrap gap-1.5">
              {/* Tier badge — A is the strongest video material; C is
                  eligible but ranks below. Color reflects the rubric:
                  emerald=A, amber=B, stone=C. */}
              {c.tier && (
                <span
                  className={
                    'inline-block px-1.5 py-0.5 rounded-sm text-[10px] font-bold tracking-wider ' +
                    (c.tier === 'A' ? 'bg-emerald-100 text-emerald-800'
                     : c.tier === 'B' ? 'bg-amber-100 text-amber-800'
                     : 'bg-stone-100 text-stone-600')
                  }
                  title={
                    c.tier === 'A' ? 'Counterfactual + video-shaped category — strongest material'
                    : c.tier === 'B' ? 'Counterfactual present — strong'
                    : 'Eligible but no counterfactual — ranks below'
                  }
                >
                  Tier {c.tier}
                </span>
              )}
              <span className="font-medium">{c.title}</span>
            </div>
            <div className="text-xs text-stone-500 flex items-center flex-wrap gap-1.5 mb-1">
              <span>{(c.category || '').replace(/_/g, ' ')}</span>
              {c.has_counterfactual && (
                <span className="px-1.5 py-0.5 rounded-sm bg-amber-50 text-amber-700 border border-amber-200 text-[10px]">
                  counterfactual
                </span>
              )}
              <span className="font-mono">
                {((c.confidence ?? 0) * 100).toFixed(0)}% conf
              </span>
            </div>
            {/* Preview drawer — collapsed details:summary so the row
                stays scannable but the operator can read claim +
                counterfactual + payoff before queueing. */}
            {(c.claim_observation || c.counterfactual_text || c.payoff_text) && (
              <details className="mt-1 mb-1">
                <summary className="cursor-pointer text-xs text-stone-500 hover:text-stone-800 select-none">
                  Preview details
                </summary>
                <div className="mt-2 ml-1 pl-3 border-l-2 border-stone-200 space-y-2 text-xs">
                  {c.claim_observation && (
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5">Claim</div>
                      <div className="text-stone-700 leading-relaxed">{c.claim_observation}</div>
                    </div>
                  )}
                  {c.counterfactual_text && (
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5">Counterfactual</div>
                      <div className="text-stone-700 leading-relaxed">{c.counterfactual_text}</div>
                    </div>
                  )}
                  {c.payoff_text && (
                    <div>
                      <div className="text-[10px] uppercase tracking-wider text-stone-400 mb-0.5">Meaning payoff</div>
                      <div className="text-stone-700 leading-relaxed">{c.payoff_text}</div>
                    </div>
                  )}
                </div>
              </details>
            )}
          </>
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
  const [bumpKey, setBumpKey] = useState(0);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getEducationalVideos(type)
      .then((rows) => { if (!cancelled) setVideos(rows); })
      .catch(() => { if (!cancelled) setVideos([]); })
      .finally(() => { if (!cancelled) setLoading(false); });
  }, [type, bumpKey]);

  // While any row is in 'rendering', poll the list every 4s so the
  // status pill flips to 'rendered' or 'failed' without a manual refresh.
  useEffect(() => {
    if (!videos.some((v) => v.status === 'rendering')) return;
    const t = setInterval(() => setBumpKey((k) => k + 1), 4000);
    return () => clearInterval(t);
  }, [videos]);

  return (
    <section>
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-stone-400">
          Queued & generated
        </h2>
        <button
          onClick={() => setBumpKey((k) => k + 1)}
          className="text-xs text-stone-500 hover:text-stone-800 cursor-pointer"
        >
          Refresh
        </button>
      </div>
      {loading ? (
        <div className="text-sm text-stone-400">Loading…</div>
      ) : videos.length === 0 ? (
        <div className="text-sm text-stone-400">
          Nothing queued for this series yet.
        </div>
      ) : (
        <div className="border border-stone-200 rounded-lg overflow-hidden bg-white">
          {videos.map((v) => (
            <VideoRow
              key={v.id}
              video={v}
              expanded={expandedId === v.id}
              onToggle={() => setExpandedId(expandedId === v.id ? null : v.id)}
              onChange={() => setBumpKey((k) => k + 1)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function VideoRow({
  video: v,
  expanded,
  onToggle,
  onChange,
}: {
  video: EducationalVideo;
  expanded: boolean;
  onToggle: () => void;
  onChange: () => void;
}) {
  return (
    <div className="border-b border-stone-100 last:border-b-0">
      <div className="flex items-center gap-3 px-3 py-2 text-sm">
        <span className="font-mono text-stone-700 w-20 flex-shrink-0">
          {v.chapter}:{v.verse}
        </span>
        <span className="text-stone-500 font-mono text-xs w-32 flex-shrink-0 truncate">
          {v.anchor_word_pos != null && `p${v.anchor_word_pos}`}
          {v.anchor_insight_id || ''}
          {v.anchor_word_pos == null && !v.anchor_insight_id && '—'}
        </span>
        <div className="flex-shrink-0">
          <StatusPill status={v.status} />
        </div>
        <span className="flex-1 text-stone-400 text-xs truncate">
          {v.error_message || formatDate(v.created_at)}
        </span>
        <VideoActions video={v} onChange={onChange} onPreview={onToggle} expanded={expanded} />
      </div>
      {expanded && <VideoExpandedPanel videoId={v.id} bumpKey={v.id} />}
    </div>
  );
}

function VideoActions({
  video: v,
  onChange,
  onPreview,
  expanded,
}: {
  video: EducationalVideo;
  onChange: () => void;
  onPreview: () => void;
  expanded: boolean;
}) {
  const [busy, setBusy] = useState(false);

  async function handleGenerate() {
    setBusy(true);
    try {
      await generateEducationalScript(v.id);
      onChange();
    } catch (e) {
      // The backend records the error on the row; refresh to surface it.
      onChange();
      alert(e instanceof Error ? e.message : 'Failed');
    } finally {
      setBusy(false);
    }
  }

  async function handleRender(format: 'long' | 'short') {
    setBusy(true);
    try {
      await renderEducationalVideo(v.id, format);
      onChange();
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Failed');
    } finally {
      setBusy(false);
    }
  }

  const noScript = v.status === 'candidate' || v.status === 'failed';
  const isRendering = v.status === 'rendering';
  const isRendered = v.status === 'rendered' || v.status === 'uploaded';

  return (
    <div className="flex items-center gap-2 flex-shrink-0">
      {noScript && (
        <button
          onClick={handleGenerate}
          disabled={busy}
          className="px-2.5 py-1 rounded-md bg-stone-800 text-white text-xs font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
          title="Phase 2: call Claude to draft a hook + verse intro + insight + close, plus long & short voiceovers."
        >
          {busy ? 'Generating…' : v.status === 'failed' ? 'Retry' : 'Generate script'}
        </button>
      )}
      {!noScript && !isRendering && (
        <>
          <button
            onClick={handleGenerate}
            disabled={busy}
            className="px-2.5 py-1 rounded-md border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-50 disabled:opacity-50 cursor-pointer"
            title="Re-run the generator. The previous script is overwritten."
          >
            Regenerate
          </button>
          <button
            onClick={onPreview}
            className="px-2.5 py-1 rounded-md border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-50 cursor-pointer"
          >
            {expanded ? 'Hide' : 'Preview'}
          </button>
          <button
            onClick={() => handleRender('long')}
            disabled={busy}
            className="px-2.5 py-1 rounded-md bg-stone-800 text-white text-xs font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
            title="Phase 3: ElevenLabs TTS + ffmpeg compose. Renders the long form (~2:00 mp4)."
          >
            Render long
          </button>
          <button
            onClick={() => handleRender('short')}
            disabled={busy}
            className="px-2.5 py-1 rounded-md bg-stone-800 text-white text-xs font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
            title="Render the short form (sub-60s mp4 for YouTube Shorts / TikTok)."
          >
            Render short
          </button>
        </>
      )}
      {isRendering && (
        <span className="text-xs text-amber-600 font-medium animate-pulse">
          Rendering…
        </span>
      )}
      {isRendered && !isRendering && (
        <a
          href={`/api/admin/educational/${v.id}/video?token=${encodeURIComponent(localStorage.getItem('admin_token') || '')}`}
          target="_blank"
          rel="noopener noreferrer"
          className="px-2.5 py-1 rounded-md border border-emerald-300 text-emerald-700 text-xs font-medium hover:bg-emerald-50 cursor-pointer"
          title={`Format: ${v.format ?? '?'} · ${v.file_size ? Math.round(v.file_size / 1024) + ' KB' : ''}`}
        >
          Open mp4
        </a>
      )}
    </div>
  );
}

function VideoExpandedPanel({ videoId, bumpKey }: { videoId: number; bumpKey: number }) {
  const [detail, setDetail] = useState<EducationalVideoDetail | null>(null);
  const [err, setErr] = useState('');
  const [editing, setEditing] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setDetail(null);
    setErr('');
    setEditing(false);
    getEducationalVideoDetail(videoId)
      .then((d) => { if (!cancelled) setDetail(d); })
      .catch((e) => { if (!cancelled) setErr(e instanceof Error ? e.message : String(e)); });
  }, [videoId, bumpKey, reloadKey]);

  if (err) return <div className="px-3 py-3 text-sm text-red-600 bg-red-50">{err}</div>;
  if (!detail) return <div className="px-3 py-3 text-sm text-stone-400">Loading…</div>;
  const s = detail.script;
  if (!s) {
    return (
      <div className="px-3 py-3 text-sm text-stone-500 bg-stone-50">
        No script generated yet.
      </div>
    );
  }
  const longText = detail.voiceover_text || s.voiceover_long;

  if (editing) {
    return (
      <ScriptEditPanel
        videoId={videoId}
        initial={{
          hook: s.hook,
          verse_intro: s.verse_intro,
          insight: s.insight,
          close: s.close,
          voiceover_long: longText,
          voiceover_short: s.voiceover_short,
        }}
        onCancel={() => setEditing(false)}
        onSaved={() => {
          setEditing(false);
          setReloadKey((k) => k + 1);
        }}
      />
    );
  }

  return (
    <div className="px-3 py-3 bg-stone-50 border-t border-stone-200 space-y-3">
      <div className="flex items-center justify-end">
        <button
          onClick={() => setEditing(true)}
          className="px-2.5 py-1 rounded-md border border-stone-300 bg-white text-stone-700 text-xs font-medium hover:bg-stone-50 cursor-pointer"
          title="Edit beats and voiceover before locking in for render"
        >
          Edit script
        </button>
      </div>

      <ScriptBeat label="Hook" text={s.hook} />
      <ScriptBeat label="Verse intro" text={s.verse_intro} />
      <ScriptBeat label="Insight" text={s.insight} />
      <ScriptBeat label="Close" text={s.close} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-stone-200">
        <VoiceoverBlock
          label="Long voiceover (TTS-ready)"
          subtitle="220–340 words · regular YouTube"
          text={longText}
          rawText={s.voiceover_long_raw}
        />
        <VoiceoverBlock
          label="Short voiceover (TTS-ready)"
          subtitle="≤120 words · sub-55s Shorts (recitation cap)"
          text={s.voiceover_short}
          rawText={s.voiceover_short_raw}
        />
      </div>

      {s.languages_referenced && s.languages_referenced.length > 0 && (
        <div className="text-xs text-stone-500">
          <span className="font-medium text-stone-600">Languages cited: </span>
          {s.languages_referenced.join(', ')}
        </div>
      )}
      {s.notes && (
        <div className="text-xs italic text-stone-500">Notes: {s.notes}</div>
      )}

      {/* Inline player — shown only when an mp4 has been rendered.
          The 9:16 aspect ratio matches our render output. Auth on the
          backend uses Bearer token via authFetch; the <video> element
          can't send headers, so the endpoint accepts a query-string
          token alternative... actually we use cookie-less auth, so we
          rely on the operator clicking "Open mp4" in a new tab where
          their session token is included. For an inline preview we
          just embed a controls-only video pointing at the same URL —
          works for the same-origin admin session since the backend
          allows the GET when the request originates from a logged-in
          tab via the Authorization header... but <video> can't send
          one. Fall back to the new-tab link instead of broken inline. */}
      {detail.filename && (
        <div className="pt-2 border-t border-stone-200">
          <div className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 mb-1">
            Rendered video ({detail.format ?? 'unknown'})
          </div>
          <div className="text-xs text-stone-600 mb-2">
            {detail.file_size ? `${Math.round(detail.file_size / 1024)} KB` : ''}
            {detail.completed_at && (
              <span className="text-stone-400"> · {formatDate(detail.completed_at)}</span>
            )}
          </div>
          {/* Inline 9:16 player. Width is capped so portrait videos
              don't dominate the panel; click "Open mp4" for a fuller
              view. Token is appended to the src so the unauthenticated
              <video> request still passes admin_required. */}
          <video
            controls
            preload="metadata"
            className="w-48 max-w-full rounded-md border border-stone-300 bg-stone-900"
            src={`/api/admin/educational/${detail.id}/video?token=${encodeURIComponent(localStorage.getItem('admin_token') || '')}`}
          />
          <div className="mt-1">
            <a
              href={`/api/admin/educational/${detail.id}/video?token=${encodeURIComponent(localStorage.getItem('admin_token') || '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-emerald-700 underline hover:no-underline"
            >
              Open full mp4 →
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Inline script editor                                              */
/* ------------------------------------------------------------------ */

function ScriptEditPanel({
  videoId,
  initial,
  onCancel,
  onSaved,
}: {
  videoId: number;
  initial: Required<ScriptEdits>;
  onCancel: () => void;
  onSaved: () => void;
}) {
  const [edits, setEdits] = useState<Required<ScriptEdits>>(initial);
  const [saving, setSaving] = useState(false);
  const [issues, setIssues] = useState<string[]>([]);

  function update<K extends keyof ScriptEdits>(key: K, value: string) {
    setEdits((e) => ({ ...e, [key]: value }));
  }

  async function handleSave() {
    setSaving(true);
    setIssues([]);
    try {
      // Only send fields the operator actually changed — prevents the
      // backend's merge from over-writing when the operator only
      // tweaked one beat. Compares against `initial` snapshot.
      const diff: ScriptEdits = {};
      (Object.keys(edits) as (keyof ScriptEdits)[]).forEach((k) => {
        if (edits[k] !== initial[k]) diff[k] = edits[k];
      });
      if (Object.keys(diff).length === 0) {
        onCancel();
        return;
      }
      await editEducationalScript(videoId, diff);
      onSaved();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      // Backend prefixes with "validation failed: " — split out the
      // semicolon-separated issues for readable display.
      if (msg.startsWith('validation failed: ')) {
        setIssues(msg.slice('validation failed: '.length).split('; ').filter(Boolean));
      } else {
        setIssues([msg]);
      }
    } finally {
      setSaving(false);
    }
  }

  const longWc = wordCount(edits.voiceover_long || '');
  const shortWc = wordCount(edits.voiceover_short || '');
  const longInRange = longWc >= 180 && longWc <= 380;
  const shortInRange = shortWc <= 130 && shortWc > 0;

  return (
    <div className="px-3 py-3 bg-stone-50 border-t border-stone-200 space-y-3">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-stone-700">Editing script</h3>
        <span className="text-[11px] text-stone-400">
          Changes are sanitized + re-validated on save.
        </span>
      </div>

      {issues.length > 0 && (
        <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
          <div className="font-semibold mb-1">Validation failed — fix and try again:</div>
          <ul className="list-disc pl-4 space-y-0.5">
            {issues.map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
        </div>
      )}

      <EditField
        label="Hook"
        subtitle="1 sentence, ≤22 words"
        value={edits.hook}
        onChange={(v) => update('hook', v)}
        rows={2}
      />
      <EditField
        label="Verse intro"
        subtitle="1 sentence introducing the verse"
        value={edits.verse_intro}
        onChange={(v) => update('verse_intro', v)}
        rows={2}
      />
      <EditField
        label="Insight"
        subtitle="2–4 sentences"
        value={edits.insight}
        onChange={(v) => update('insight', v)}
        rows={5}
      />
      <EditField
        label="Close"
        subtitle="1 reflective sentence"
        value={edits.close}
        onChange={(v) => update('close', v)}
        rows={2}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-stone-200">
        <EditField
          label="Long voiceover"
          subtitle={`220–340 words · regular YouTube · ${longWc} words ${longInRange ? '✓' : '⚠'}`}
          value={edits.voiceover_long}
          onChange={(v) => update('voiceover_long', v)}
          rows={10}
          mono
        />
        <EditField
          label="Short voiceover"
          subtitle={`≤120 words · Shorts cap · ${shortWc} words ${shortInRange ? '✓' : '⚠'}`}
          value={edits.voiceover_short}
          onChange={(v) => update('voiceover_short', v)}
          rows={10}
          mono
        />
      </div>

      <p className="text-[11px] text-stone-400 italic">
        IPA marks (ʕ ʔ ʿ ʾ ḥ ġ ā ī ū s¹ s² etc.) and Arabic-script will be
        stripped from voiceover text on save — no need to clean them yourself.
      </p>

      <div className="flex items-center justify-end gap-2 pt-1">
        <button
          onClick={onCancel}
          disabled={saving}
          className="px-3 py-1.5 rounded-md text-stone-600 text-sm hover:bg-stone-100 disabled:opacity-50 cursor-pointer"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-3 py-1.5 rounded-md bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
        >
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
    </div>
  );
}

function EditField({
  label,
  subtitle,
  value,
  onChange,
  rows = 3,
  mono = false,
}: {
  label: string;
  subtitle?: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  mono?: boolean;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between mb-0.5">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-stone-400">
          {label}
        </span>
        {subtitle && <span className="text-[10px] text-stone-400">{subtitle}</span>}
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={rows}
        className={`w-full bg-white border border-stone-300 rounded-md px-2 py-1.5 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-stone-400 ${mono ? 'font-mono text-xs' : ''}`}
      />
    </div>
  );
}

function wordCount(s: string): number {
  return (s.match(/\b\w[\w'-]*\b/g) ?? []).length;
}

function ScriptBeat({ label, text }: { label: string; text: string }) {
  return (
    <div>
      <div className="text-[10px] font-semibold uppercase tracking-wider text-stone-400 mb-0.5">
        {label}
      </div>
      <p className="text-sm text-stone-700 leading-relaxed">{text}</p>
    </div>
  );
}

function VoiceoverBlock({
  label,
  subtitle,
  text,
  rawText,
}: {
  label: string;
  subtitle: string;
  text: string;
  rawText?: string;
}) {
  const wc = (text || '').match(/\b\w[\w'-]*\b/g)?.length ?? 0;
  const wasSanitized = rawText && rawText !== text;
  const [showRaw, setShowRaw] = useState(false);
  return (
    <div>
      <div className="flex items-baseline justify-between mb-0.5">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-stone-400">
          {label}
        </span>
        <span className="text-[10px] text-stone-400 font-mono">{wc} words</span>
      </div>
      <div className="text-[11px] text-stone-400 mb-1">{subtitle}</div>
      <pre className="whitespace-pre-wrap font-sans text-xs text-stone-700 leading-relaxed bg-white border border-stone-200 rounded-md p-2 max-h-48 overflow-auto">
        {showRaw && rawText ? rawText : text}
      </pre>
      {wasSanitized && (
        <div className="mt-1 flex items-center gap-2 text-[11px] text-amber-700">
          <span>Sanitized: stripped IPA / Arabic for ElevenLabs.</span>
          <button
            onClick={() => setShowRaw((v) => !v)}
            className="underline hover:no-underline cursor-pointer"
          >
            {showRaw ? 'Show TTS-ready' : 'Show raw'}
          </button>
        </div>
      )}
    </div>
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
