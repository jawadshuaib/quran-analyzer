import { useEffect, useState, useCallback } from 'react';
import {
  ResponsiveContainer, LineChart, Line, BarChart, Bar,
  XAxis, YAxis, Tooltip, CartesianGrid, Legend,
} from 'recharts';
import {
  getWebsiteStats, getYoutubeStats, refreshYoutubeStats,
  type WebsiteStats, type YoutubeStats, type YoutubeStatsVideo, type StatsRange,
} from '../../api/admin';

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
  const [tab, setTab] = useState<Tab>('website');
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

  useEffect(() => {
    setLoading(true);
    setError('');
    getWebsiteStats(range)
      .then((d) => { setData(d); setLoading(false); })
      .catch((e: Error) => { setError(e.message); setLoading(false); });
  }, [range]);

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
                <Tooltip />
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

  if (loading) return <div className="text-stone-500 py-12 text-center">Loading…</div>;
  if (error) return <div className="text-red-600 py-12 text-center">{error}</div>;
  if (!data) return null;

  const noData = data.snapshot_count === 0;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <SummaryTile
          label="Total videos"
          value={data.totals.videos}
          help="snapshots present"
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
          label="Last refresh"
          stringValue={data.last_refresh ? relativeTime(data.last_refresh) : '—'}
          help={data.last_refresh ?? 'never'}
        />
      </div>

      {/* Trend chart — videos ordered chronologically (oldest left,
          newest right). Visual shape answers "are recent videos
          getting more views than older ones?" without reading rows. */}
      {!noData && (
        <ChartCard
          title="Views per video over time"
          subtitle="Each bar is one video, ordered by upload date (oldest → newest). Hover for details."
        >
          <YoutubeViewsTrendChart videos={data.videos} />
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
                  <tr key={v.youtube_video_id} className="hover:bg-stone-50">
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
function YoutubeViewsTrendChart({ videos }: { videos: YoutubeStatsVideo[] }) {
  const chronological = videos
    .slice()
    .filter((v) => v.published_at)
    .sort((a, b) => (a.published_at ?? '').localeCompare(b.published_at ?? ''));

  // recharts wants a stable shape: x = a label key, y = the value. We
  // also pass title + date through so the tooltip can render them.
  const chartData = chronological.map((v, i) => ({
    idx: i + 1,
    views: v.current_views,
    title: v.title ?? v.youtube_video_id,
    date: v.published_at
      ? new Date(v.published_at).toLocaleDateString()
      : '—',
  }));

  if (chartData.length === 0) {
    return <EmptyHint>No videos with a known publish date.</EmptyHint>;
  }

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} margin={{ top: 10, right: 16, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
        <XAxis dataKey="idx" tick={false} label={{ value: 'oldest →  newest', position: 'insideBottom', offset: -2, style: { fontSize: 11, fill: '#78716c' } }} />
        <YAxis tick={{ fontSize: 11 }} allowDecimals={false} tickFormatter={compactNumber} />
        <Tooltip content={<YoutubeBarTooltip />} />
        <Bar dataKey="views" fill="#0ea5e9" />
      </BarChart>
    </ResponsiveContainer>
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
