import { useEffect, useState, useCallback } from 'react';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from 'recharts';
import {
  getWebsiteStats, getYoutubeStats, refreshYoutubeStats, repinYoutubeChannel,
  type WebsiteStats, type YoutubeStats, type YoutubeStatsVideo, type StatsRange,
} from '../../api/admin';
import { getSurahsForSearch } from '../../utils/surah-search';
import type { SurahInfo } from '../../types';

type YoutubeSortKey = 'recent' | 'views' | 'growth';

// ---------------------------------------------------------------------------
// StatsPage — admin /admin/stats
//
// Two tabs: Website (visitor analytics) and YouTube (per-video performance).
// Both tabs share a 7d/30d range selector. Charts are recharts;
// computations (trend %, gain) are done in-component from the API payload.
// ---------------------------------------------------------------------------
type Tab = 'website' | 'youtube';

export default function StatsPage() {
  // Honor a #youtube hash on initial load so the dashboard's YouTube
  // tile can deep-link straight to that tab. Read once on mount; later
  // clicks on the tab buttons update React state without touching the
  // URL.
  const initialTab: Tab = typeof window !== 'undefined'
    && window.location.hash === '#youtube' ? 'youtube' : 'website';
  const [tab, setTab] = useState<Tab>(initialTab);
  const [range, setRange] = useState<StatsRange>('7d');

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      <div className="mb-6 flex items-end justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-stone-900">Stats</h1>
          <p className="text-sm text-stone-500 mt-1">
            Public-site visitor analytics and YouTube performance. Admin
            browsing is automatically excluded.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <RangeButton active={range === '7d'} onClick={() => setRange('7d')}>Last 7 days</RangeButton>
          <RangeButton active={range === '30d'} onClick={() => setRange('30d')}>Last 30 days</RangeButton>
        </div>
      </div>

      <div className="border-b border-stone-200 mb-6 flex gap-6">
        <TabButton active={tab === 'website'} onClick={() => setTab('website')}>
          Website
        </TabButton>
        <TabButton active={tab === 'youtube'} onClick={() => setTab('youtube')}>
          YouTube
        </TabButton>
      </div>

      {tab === 'website' && <WebsiteStatsView range={range} />}
      {tab === 'youtube' && <YoutubeStatsView range={range} />}
    </div>
  );
}

function RangeButton({
  active, onClick, children,
}: {
  active: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={
        'px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ' +
        (active
          ? 'bg-stone-900 text-white border-stone-900'
          : 'bg-white text-stone-700 border-stone-300 hover:bg-stone-50')
      }
    >
      {children}
    </button>
  );
}

function TabButton({
  active, onClick, children,
}: {
  active: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={
        'pb-3 -mb-px font-medium text-sm border-b-2 transition-colors ' +
        (active
          ? 'border-stone-900 text-stone-900'
          : 'border-transparent text-stone-500 hover:text-stone-800')
      }
    >
      {children}
    </button>
  );
}

// ---------------------------------------------------------------------------
// Website tab
// ---------------------------------------------------------------------------
function WebsiteStatsView({ range }: { range: StatsRange }) {
  const [data, setData] = useState<WebsiteStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  // Surah list is fetched once and cached at the module level by
  // getSurahsForSearch — prefetched here so the top-pages tooltip can
  // resolve "Surah 2" → "Al-Baqarah" synchronously on hover. Failure
  // is non-fatal: the tooltip falls back to surah numbers.
  const [surahs, setSurahs] = useState<SurahInfo[] | null>(null);

  useEffect(() => {
    setLoading(true);
    setError('');
    getWebsiteStats(range)
      .then((d) => { setData(d); setLoading(false); })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, [range]);

  useEffect(() => {
    getSurahsForSearch().then(setSurahs).catch(() => { /* fall back to numbers */ });
  }, []);

  if (loading) return <div className="text-stone-500 py-12 text-center">Loading…</div>;
  if (error) return <div className="text-red-600 py-12 text-center">{error}</div>;
  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <SummaryTile
          label="Page views"
          value={data.totals.page_views}
          prior={data.totals.page_views_prior}
          help={`vs prior ${range}`}
        />
        <SummaryTile
          label="Unique visitors"
          value={data.totals.unique_visitors}
          prior={data.totals.unique_visitors_prior}
          help={`vs prior ${range}`}
        />
        <SummaryTile
          label="Active now"
          value={data.live.active_last_5min}
          help="last 5 min"
          live
        />
        <SummaryTile
          label="Pages/visitor"
          value={
            data.totals.unique_visitors === 0
              ? 0
              : Number((data.totals.page_views / data.totals.unique_visitors).toFixed(2))
          }
          help="this period"
        />
      </div>

      <ChartCard title="Daily visits">
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data.daily} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={shortDate} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="page_views" stroke="#0ea5e9" strokeWidth={2} dot={false} name="Page views" />
            <Line type="monotone" dataKey="unique_visitors" stroke="#f97316" strokeWidth={2} dot={false} name="Unique" />
          </LineChart>
        </ResponsiveContainer>
      </ChartCard>

      <div className="grid lg:grid-cols-2 gap-6">
        <ChartCard title="Top pages" subtitle={`${data.top_pages.length ? data.top_pages.length : 'No'} routes`}>
          {data.top_pages.length === 0 ? (
            <EmptyHint>No views yet.</EmptyHint>
          ) : (
            <ResponsiveContainer width="100%" height={Math.max(220, data.top_pages.length * 32)}>
              <BarChart
                data={data.top_pages.slice().reverse()}
                layout="vertical"
                margin={{ top: 5, right: 16, left: 0, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
                <XAxis type="number" tick={{ fontSize: 11 }} allowDecimals={false} />
                <YAxis type="category" dataKey="path" tick={{ fontSize: 11 }} width={140} />
                <Tooltip
                  content={<TopPagesTooltip surahs={surahs} />}
                  cursor={{ fill: 'rgba(14, 165, 233, 0.08)' }}
                />
                <Bar dataKey="page_views" fill="#0ea5e9" name="Views" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </ChartCard>

        <ChartCard title="Top referrers" subtitle={`${data.top_referrers.length} sources`}>
          {data.top_referrers.length === 0 ? (
            <EmptyHint>No referrers in range.</EmptyHint>
          ) : (
            <ul className="divide-y divide-stone-100">
              {data.top_referrers.map((r) => (
                <li key={r.referrer} className="py-2 flex items-center justify-between gap-3">
                  <div className="text-sm text-stone-700 truncate flex-1" title={r.referrer}>
                    {r.referrer === '(direct)'
                      ? <span className="text-stone-500 italic">(direct)</span>
                      : <span>{shortReferrer(r.referrer)}</span>}
                  </div>
                  <div className="text-sm font-medium text-stone-900 tabular-nums">
                    {r.page_views.toLocaleString()}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </ChartCard>
      </div>
    </div>
  );
}

function shortDate(d: string): string {
  // YYYY-MM-DD → "May 3"
  try {
    const dt = new Date(d + 'T00:00:00Z');
    return dt.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch {
    return d;
  }
}

// ---------------------------------------------------------------------------
// Smart tooltip for the Top Pages chart.
//
// Routes look like /verse/2:255 or /word/3:18/4 or /root/jml — fine for
// computer code, opaque to a human. Resolve them to "Surah Al-Baqarah,
// verse 255" or "Word #4, Surah Al-Imran, ayah 18" or "Root: jml" using
// regex parsing + the cached surah list. Failure modes degrade to the
// raw path so the chart never *loses* information by adding the
// tooltip; we just augment it.
// ---------------------------------------------------------------------------
interface PathLabel {
  primary: string;
  secondary?: string;
}

function pathToHumanLabel(path: string, surahs: SurahInfo[] | null): PathLabel {
  if (!path || path === '/') return { primary: 'Home' };

  const surahName = (n: number): string => {
    const s = surahs?.find((x) => x.number === n);
    return s ? `${n}. ${s.name}` : `Surah ${n}`;
  };

  let m = path.match(/^\/verse\/(\d+):(\d+)\/?$/);
  if (m) return {
    primary: surahName(parseInt(m[1], 10)),
    secondary: `Verse ${m[1]}:${m[2]}`,
  };

  m = path.match(/^\/word\/(\d+):(\d+)\/(\d+)\/?$/);
  if (m) return {
    primary: surahName(parseInt(m[1], 10)),
    secondary: `Word #${m[3]}, ayah ${m[2]}`,
  };

  m = path.match(/^\/learning\/root\/(.+?)\/?$/);
  if (m) return { primary: 'Root learning', secondary: decodeURIComponent(m[1]) };

  m = path.match(/^\/root\/(.+?)\/?$/);
  if (m) return { primary: 'Root', secondary: decodeURIComponent(m[1]) };

  m = path.match(/^\/read\/(\d+)(?::(\d+)(?:-(\d+))?)?\/?$/);
  if (m) {
    const n = parseInt(m[1], 10);
    const range = m[2] ? (m[3] ? `verses ${m[2]}–${m[3]}` : `verse ${m[2]}`) : 'full surah';
    return { primary: `Reader — ${surahName(n)}`, secondary: range };
  }

  if (/^\/learning\/mnemonic-sheet\/?$/.test(path)) return { primary: 'Mnemonic sheet' };
  if (/^\/learning\/?$/.test(path)) return { primary: 'Learning hub' };
  if (/^\/methodology\/?$/.test(path)) return { primary: 'Methodology' };
  if (/^\/grammar-glossary\/?$/.test(path)) return { primary: 'Grammar glossary' };
  if (/^\/quran-vocabulary\/?$/.test(path)) return { primary: 'Quran vocabulary' };
  if (/^\/privacy(\/extension)?\/?$/.test(path)) return { primary: 'Privacy' };
  if (/^\/terms\/?$/.test(path)) return { primary: 'Terms of use' };
  if (/^\/developers\/?$/.test(path)) return { primary: 'Developers' };
  if (/^\/settings\/?$/.test(path)) return { primary: 'Settings' };
  if (/^\/502\/?$/.test(path)) return { primary: 'Error page (502)' };

  return { primary: path };
}

interface TopPagesTooltipPayload {
  payload: { path: string; page_views: number; unique_visitors: number };
}

function TopPagesTooltip({
  active, payload, surahs,
}: {
  active?: boolean;
  payload?: TopPagesTooltipPayload[];
  surahs: SurahInfo[] | null;
}) {
  if (!active || !payload || payload.length === 0) return null;
  const p = payload[0].payload;
  const label = pathToHumanLabel(p.path, surahs);
  return (
    <div className="bg-white border border-stone-200 rounded-lg shadow-sm px-3 py-2 text-xs max-w-xs">
      <div className="font-medium text-stone-900">{label.primary}</div>
      {label.secondary && (
        <div className="text-stone-600 mt-0.5">{label.secondary}</div>
      )}
      <div className="font-mono text-[10px] text-stone-400 mt-1 truncate">{p.path}</div>
      <div className="mt-1 pt-1 border-t border-stone-100 text-stone-700 tabular-nums">
        <strong>{p.page_views.toLocaleString()}</strong> view{p.page_views === 1 ? '' : 's'}
        {' · '}
        <span>{p.unique_visitors.toLocaleString()} unique</span>
      </div>
    </div>
  );
}

function shortReferrer(url: string): string {
  try {
    const u = new URL(url);
    return u.hostname + (u.pathname && u.pathname !== '/' ? u.pathname : '');
  } catch {
    return url;
  }
}

// ---------------------------------------------------------------------------
// YouTube tab
// ---------------------------------------------------------------------------
function YoutubeStatsView({ range }: { range: StatsRange }) {
  const [data, setData] = useState<YoutubeStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMsg, setRefreshMsg] = useState('');
  const [sortKey, setSortKey] = useState<YoutubeSortKey>('recent');
  const [highlightId, setHighlightId] = useState<string | null>(null);

  // When a bar is clicked: scroll the matching <tr> into view and flash
  // a subtle highlight so the eye lands on the right row immediately.
  // The DOM id on each row is `yt-row-${youtube_video_id}` — a string
  // YouTube guarantees is alphanumeric/dash, safe for an HTML id.
  const handleBarClick = useCallback((videoId: string) => {
    const row = document.getElementById(`yt-row-${videoId}`);
    if (!row) return;
    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setHighlightId(videoId);
    window.setTimeout(() => setHighlightId((v) => (v === videoId ? null : v)), 2000);
  }, []);

  const load = useCallback(() => {
    setLoading(true);
    setError('');
    return getYoutubeStats(range)
      .then((d) => { setData(d); setLoading(false); })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, [range]);

  useEffect(() => { load(); }, [load]);

  async function handleRefresh() {
    setRefreshing(true);
    setRefreshMsg('');
    try {
      const r = await refreshYoutubeStats();
      if (r.ok) {
        setRefreshMsg(`Refreshed ${r.videos_refreshed ?? 0} videos.`);
        await load();
      } else {
        setRefreshMsg(`Refresh failed: ${r.error}`);
      }
    } catch (e) {
      setRefreshMsg(`Refresh failed: ${(e as Error).message}`);
    } finally {
      setRefreshing(false);
      setTimeout(() => setRefreshMsg(''), 6000);
    }
  }

  async function handleRepin() {
    setRefreshing(true);
    setRefreshMsg('');
    try {
      const r = await repinYoutubeChannel();
      if (r.ok) {
        setRefreshMsg(`Re-pinned to channel ${r.title ?? r.channel_id}. Refreshing…`);
        await load();
      } else {
        setRefreshMsg(`Repin failed: ${r.error}`);
      }
    } catch (e) {
      setRefreshMsg(`Repin failed: ${(e as Error).message}`);
    } finally {
      setRefreshing(false);
      setTimeout(() => setRefreshMsg(''), 8000);
    }
  }

  if (loading) return <div className="text-stone-500 py-12 text-center">Loading…</div>;
  if (error) return <div className="text-red-600 py-12 text-center">{error}</div>;
  if (!data) return null;

  const noData = data.snapshot_count === 0;

  const ch = data.channel;
  const mismatch = data.channel_mismatch;

  return (
    <div className="space-y-6">
      {/* Channel-identity banner. The dashboard shows whichever
          channel the OAuth token authenticates against — operator hit
          this 2026-05-25 when re-OAuthing pulled in the wrong account
          and 162 subs for the personal channel replaced the real
          al-nuqta numbers overnight. Always show WHICH channel is
          connected so this is impossible to miss. Surface a red
          mismatch banner when the connected channel != the pinned
          one, with a repin button for intentional switches. */}
      {(ch || mismatch) && (
        <div className={
          mismatch
            ? 'rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800'
            : 'rounded-lg border border-stone-200 bg-stone-50 px-4 py-2 text-xs text-stone-600'
        }>
          {mismatch ? (
            <>
              <div className="font-semibold mb-1">
                ⚠ OAuth channel mismatch — stats are NOT being updated
              </div>
              <div className="mb-2">
                The connected OAuth token resolves to{' '}
                <strong>{mismatch.connected_title || mismatch.connected_channel_id}</strong>{' '}
                (<span className="font-mono">{mismatch.connected_channel_id}</span>),
                but the pinned channel is{' '}
                <span className="font-mono">{mismatch.pinned_channel_id || '?'}</span>.
                Refusing to overwrite stats until this is resolved.
              </div>
              <div className="mb-3 text-xs">
                Either re-OAuth from the original Google account at{' '}
                <a href="/admin/settings" className="underline font-medium">
                  Admin Settings → YouTube
                </a>
                , OR click <em>Repin to current channel</em> if you intentionally
                switched channels.
              </div>
              <button
                onClick={handleRepin}
                disabled={refreshing}
                className="px-3 py-1.5 text-xs rounded-md bg-stone-800 text-white hover:bg-stone-700 disabled:opacity-50"
              >
                {refreshing ? 'Working…' : 'Repin to current channel'}
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-stone-500">Channel:</span>
              <strong className="text-stone-800">{ch?.title || '(no title)'}</strong>
              <span className="text-stone-400 font-mono text-[10px]">
                {ch?.channel_id}
              </span>
              {data.pinned_channel_id && ch?.channel_id === data.pinned_channel_id && (
                <span className="text-emerald-700 text-[10px] uppercase tracking-wider">
                  ✓ pinned
                </span>
              )}
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <SummaryTile
          label="Subscribers"
          value={ch?.current_subscribers ?? 0}
          gain={ch?.subscribers_gain ?? 0}
          help={
            ch
              ? (ch.subscribers_gain !== 0
                  ? `${ch.subscribers_gain > 0 ? '+' : ''}${ch.subscribers_gain.toLocaleString()} in ${range}`
                  : `flat in ${range}`)
              : 'no snapshots yet'
          }
        />
        <SummaryTile
          label="Total views"
          value={data.totals.total_views}
          gain={data.totals.views_gain_period}
          help={`+${data.totals.views_gain_period.toLocaleString()} in ${range}`}
        />
        <SummaryTile
          label="Total likes"
          value={data.totals.total_likes}
          gain={data.totals.likes_gain_period}
          help={`+${data.totals.likes_gain_period.toLocaleString()} in ${range}`}
        />
        <SummaryTile
          label="Total videos"
          value={data.totals.videos}
          help={
            data.last_refresh
              ? `last refreshed ${relativeTime(data.last_refresh)}`
              : 'snapshots present'
          }
        />
      </div>

      {/* Subscribers-over-time line. Two snapshots are needed for the
          line to be more than a dot; we show it the moment we have any
          data (the daemon takes a snapshot daily). */}
      {ch && ch.subscribers_daily.length >= 2 && (
        <ChartCard
          title="Subscribers over time"
          subtitle={ch.title ? `Channel: ${ch.title}` : undefined}
        >
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={ch.subscribers_daily} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={shortDate} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} domain={['auto', 'auto']} />
              <Tooltip />
              <Line type="monotone" dataKey="subscribers" stroke="#dc2626" strokeWidth={2} dot={{ r: 3 }} name="Subscribers" />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      )}

      {/* Trend chart — videos ordered chronologically (oldest left,
          newest right). Visual shape answers "are recent videos
          getting more views than older ones?" without reading rows.
          Clicking a bar scrolls the corresponding row into view. */}
      {!noData && (
        <ChartCard
          title="Views per video over time"
          subtitle="Each bar is one video, ordered by upload date. Click a bar to jump to its row."
        >
          <YoutubeViewsTrendChart videos={data.videos} onBarClick={handleBarClick} />
        </ChartCard>
      )}

      <div className="bg-white rounded-xl border border-stone-200">
        <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-stone-100 flex-wrap">
          <div>
            <div className="font-medium text-stone-900">Per-video performance</div>
            <div className="text-xs text-stone-500">{sortDescription(sortKey, range)}</div>
          </div>
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1 text-xs">
              <span className="text-stone-500 mr-1">Sort:</span>
              <SortChip active={sortKey === 'recent'} onClick={() => setSortKey('recent')}>Most recent</SortChip>
              <SortChip active={sortKey === 'views'} onClick={() => setSortKey('views')}>Most views</SortChip>
              <SortChip active={sortKey === 'growth'} onClick={() => setSortKey('growth')}>Most growth</SortChip>
            </div>
            {refreshMsg && (
              <div className="text-xs text-stone-500">{refreshMsg}</div>
            )}
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="px-3 py-1.5 text-sm font-medium rounded-lg border border-stone-300 bg-white hover:bg-stone-50 disabled:opacity-50"
            >
              {refreshing ? 'Refreshing…' : 'Refresh from YouTube'}
            </button>
          </div>
        </div>

        {noData ? (
          <div className="px-5 py-12 text-center text-stone-500">
            <div>No YouTube snapshots yet.</div>
            <div className="text-xs mt-2">
              Click <strong>Refresh from YouTube</strong> to take the first snapshot.
              Daily refreshes happen automatically at 03:15 UTC.
            </div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-stone-500 text-xs uppercase tracking-wide">
                <tr className="border-b border-stone-100">
                  <th className="text-left font-medium px-5 py-2">Video</th>
                  <th className="text-right font-medium px-3 py-2">Views</th>
                  <th className="text-right font-medium px-3 py-2">Gain ({range})</th>
                  <th className="text-right font-medium px-3 py-2">Likes</th>
                  <th className="text-right font-medium px-3 py-2">Likes Δ</th>
                  <th className="text-right font-medium px-3 py-2">Comments</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100">
                {sortVideos(data.videos, sortKey).map((v) => (
                  <tr
                    key={v.youtube_video_id}
                    id={`yt-row-${v.youtube_video_id}`}
                    className={
                      'transition-colors duration-700 ' +
                      (highlightId === v.youtube_video_id
                        ? 'bg-sky-100'
                        : 'hover:bg-stone-50')
                    }
                  >
                    <td className="px-5 py-2">
                      <a
                        href={v.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sky-700 hover:underline"
                      >
                        {v.title || v.youtube_video_id}
                      </a>
                      {v.published_at && (
                        <div className="text-xs text-stone-400">
                          {new Date(v.published_at).toLocaleDateString()}
                        </div>
                      )}
                    </td>
                    <td className="text-right px-3 py-2 tabular-nums">{v.current_views.toLocaleString()}</td>
                    <td className={'text-right px-3 py-2 tabular-nums font-medium ' + gainClass(v.views_gain)}>
                      {v.views_gain > 0 ? '+' : ''}{v.views_gain.toLocaleString()}
                    </td>
                    <td className="text-right px-3 py-2 tabular-nums">{v.current_likes.toLocaleString()}</td>
                    <td className={'text-right px-3 py-2 tabular-nums ' + gainClass(v.likes_gain)}>
                      {v.likes_gain > 0 ? '+' : ''}{v.likes_gain.toLocaleString()}
                    </td>
                    <td className="text-right px-3 py-2 tabular-nums">{v.current_comments.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function SortChip({
  active, onClick, children,
}: {
  active: boolean; onClick: () => void; children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      className={
        'px-2 py-1 rounded-md font-medium transition-colors ' +
        (active
          ? 'bg-stone-900 text-white'
          : 'bg-white text-stone-600 hover:bg-stone-100 border border-stone-200')
      }
    >
      {children}
    </button>
  );
}

function sortVideos(videos: YoutubeStatsVideo[], key: YoutubeSortKey): YoutubeStatsVideo[] {
  const out = videos.slice();
  if (key === 'recent') {
    out.sort((a, b) => (b.published_at ?? '').localeCompare(a.published_at ?? ''));
  } else if (key === 'views') {
    out.sort((a, b) => b.current_views - a.current_views);
  } else if (key === 'growth') {
    out.sort((a, b) => b.views_gain - a.views_gain);
  }
  return out;
}

function sortDescription(key: YoutubeSortKey, range: StatsRange): string {
  if (key === 'recent') return 'Sorted by upload date — newest first';
  if (key === 'views') return 'Sorted by lifetime view count';
  return `Sorted by views gained in the last ${range}`;
}

// ---------------------------------------------------------------------------
// Views-per-video bar chart, ordered by upload date (oldest → newest).
//
// With a fully populated channel this can be 30+ bars. We hide the X-axis
// labels because video titles or even short dates would overlap badly;
// the visual shape is what matters (rising / falling trend), and the
// tooltip exposes the per-bar identity. Older videos accumulate views
// faster simply by being out longer, so a *flat* trend over time is
// actually a sign the newer content is *outperforming* the channel
// average. Worth knowing at a glance.
// ---------------------------------------------------------------------------
function YoutubeViewsTrendChart({
  videos, onBarClick,
}: {
  videos: YoutubeStatsVideo[];
  onBarClick: (videoId: string) => void;
}) {
  const chronological = videos
    .slice()
    .filter((v) => v.published_at)
    .sort((a, b) => (a.published_at ?? '').localeCompare(b.published_at ?? ''));

  // recharts wants a stable shape: x = a label key, y = the value. We
  // also pass title + date + video id through so the tooltip can render
  // them and the click handler can resolve which row to scroll to.
  const chartData = chronological.map((v, i) => ({
    idx: i + 1,
    views: v.current_views,
    title: v.title ?? v.youtube_video_id,
    date: v.published_at
      ? new Date(v.published_at).toLocaleDateString()
      : '—',
    youtube_video_id: v.youtube_video_id,
  }));

  if (chartData.length === 0) {
    return <EmptyHint>No videos with a known publish date.</EmptyHint>;
  }

  return (
    // Extra bottom padding gives the "oldest → newest" axis hint room
    // to breathe — without it the label gets clipped against the card
    // border at typical viewport sizes.
    <div className="pb-2">
      <ResponsiveContainer width="100%" height={290}>
        <BarChart
          data={chartData}
          margin={{ top: 10, right: 16, left: 0, bottom: 28 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
          <XAxis
            dataKey="idx"
            tick={false}
            label={{
              value: 'oldest  →  newest',
              position: 'insideBottom',
              offset: -18,
              style: { fontSize: 11, fill: '#78716c' },
            }}
          />
          <YAxis tick={{ fontSize: 11 }} allowDecimals={false} tickFormatter={compactNumber} />
          <Tooltip content={<YoutubeBarTooltip />} cursor={{ fill: 'rgba(14, 165, 233, 0.08)' }} />
          <Bar
            dataKey="views"
            fill="#0ea5e9"
            cursor="pointer"
            onClick={(payload: unknown) => {
              const p = payload as { youtube_video_id?: string } | undefined;
              if (p?.youtube_video_id) onBarClick(p.youtube_video_id);
            }}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function compactNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return String(n);
}

interface BarTooltipPayload {
  payload: { idx: number; views: number; title: string; date: string };
}

function YoutubeBarTooltip({
  active, payload,
}: {
  active?: boolean;
  payload?: BarTooltipPayload[];
}) {
  if (!active || !payload || payload.length === 0) return null;
  const p = payload[0].payload;
  return (
    <div className="bg-white border border-stone-200 rounded-lg shadow-sm px-3 py-2 text-xs">
      <div className="font-medium text-stone-900 mb-1 max-w-xs truncate">{p.title}</div>
      <div className="text-stone-500">Uploaded: {p.date}</div>
      <div className="text-stone-700 mt-0.5">
        <strong className="tabular-nums">{p.views.toLocaleString()}</strong> views
      </div>
    </div>
  );
}

function gainClass(n: number): string {
  if (n > 0) return 'text-emerald-700';
  if (n < 0) return 'text-red-600';
  return 'text-stone-400';
}

function relativeTime(iso: string): string {
  try {
    const ms = Date.now() - new Date(iso).getTime();
    if (ms < 60_000) return 'just now';
    const min = Math.floor(ms / 60_000);
    if (min < 60) return `${min}m ago`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr}h ago`;
    return `${Math.floor(hr / 24)}d ago`;
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Shared UI bits
// ---------------------------------------------------------------------------
function SummaryTile({
  label, value, prior, gain, stringValue, help, live,
}: {
  label: string;
  value?: number;
  prior?: number;
  gain?: number;
  stringValue?: string;
  help?: string;
  live?: boolean;
}) {
  const display = stringValue ?? (value ?? 0).toLocaleString();
  let trend: { pct: number; pos: boolean } | null = null;
  if (prior !== undefined && value !== undefined) {
    if (prior === 0) {
      if (value > 0) trend = { pct: 100, pos: true };
    } else {
      const pct = ((value - prior) / prior) * 100;
      trend = { pct: Math.abs(pct), pos: pct >= 0 };
    }
  } else if (gain !== undefined) {
    trend = { pct: 0, pos: gain >= 0 };
  }

  return (
    <div className="bg-white rounded-xl border border-stone-200 px-4 py-3">
      <div className="flex items-center justify-between">
        <div className="text-xs uppercase tracking-wide text-stone-500">{label}</div>
        {live && (
          <span className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-700">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            LIVE
          </span>
        )}
      </div>
      <div className="text-2xl font-semibold text-stone-900 mt-1 tabular-nums">{display}</div>
      <div className="text-xs text-stone-500 mt-0.5 flex items-center gap-1">
        {trend && trend.pct > 0 && (
          <span className={trend.pos ? 'text-emerald-700' : 'text-red-600'}>
            {trend.pos ? '▲' : '▼'} {trend.pct.toFixed(0)}%
          </span>
        )}
        <span>{help}</span>
      </div>
    </div>
  );
}

function ChartCard({
  title, subtitle, children,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-stone-200 px-4 py-4">
      <div className="mb-2">
        <div className="font-medium text-stone-900 text-sm">{title}</div>
        {subtitle && <div className="text-xs text-stone-500">{subtitle}</div>}
      </div>
      {children}
    </div>
  );
}

function EmptyHint({ children }: { children: React.ReactNode }) {
  return <div className="py-8 text-center text-sm text-stone-500">{children}</div>;
}
