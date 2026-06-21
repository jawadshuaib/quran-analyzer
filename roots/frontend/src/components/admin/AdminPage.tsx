import { useState, useEffect, type ReactNode } from 'react';
import {
  isLoggedIn, verifyToken, clearToken, getPreferences,
  getYoutubeUploadSchedule, getPipelineSchedules,
  getAllEducationalSchedules,
  getPipelineScheduleRuns, getYoutubeUploadRuns,
  getAllEducationalScheduleRuns,
  getWebsiteStats, getYoutubeStats,
} from '../../api/admin';
import type {
  PipelineScheduleRun, YoutubeUploadRun,
  EducationalScheduleRunGlobal,
} from '../../api/admin';
import { getBuildInfo, type BuildInfo } from '../../api/quran';
import AdminLogin from './AdminLogin';
import AdminSettings from './AdminSettings';
import AdminMedia from './AdminMedia';
import VerseRecitations from './VerseRecitations';
import AdminResources from './AdminResources';
import GenerateVideo from './GenerateVideo';
import AdminMusic from './AdminMusic';
import ExplanationBuilder from './ExplanationBuilder';
import GenerateExplanationVideo from './GenerateExplanationVideo';
import PipelineManager from './PipelineManager';
import SchedulerPage from './SchedulerPage';
import AdminVocabulary from './AdminVocabulary';
import AdminVocabularyStudio from './AdminVocabularyStudio';
import AdminRevisions from './AdminRevisions';
import AdminProperNouns from './AdminProperNouns';
import VerseSettings from './VerseSettings';
import AdminEducational from './AdminEducational';
import AdminEducationalPipelines from './AdminEducationalPipelines';
import AdminPipelines from './AdminPipelines';
import AdminVerseOfTheDay from './AdminVerseOfTheDay';
import StatsPage from './StatsPage';
import JudgeLessonsPage from './JudgeLessonsPage';
import AdminAssistantQA from './AdminAssistantQA';
import AdminExegesis from './AdminExegesis';

type AdminRoute =
  | 'dashboard' | 'settings' | 'scheduler'
  | 'media' | 'recitations' | 'resources' | 'music' | 'generate'
  | 'explanations' | 'generate-explanation'
  // Pipelines hub + sub-routes (top-level admin section)
  | 'pipelines-hub'
  | 'pipelines-recitation'
  | 'pipelines-educational'
  | 'pipelines-educational-candidates'
  | 'revisions' | 'vocabulary' | 'vocabulary-studio' | 'proper-nouns'
  | 'verse-settings'
  | 'verse-of-the-day'
  | 'stats'
  | 'judge-lessons'
  | 'assistant-qa'
  | 'exegesis';

function getAdminRoute(): AdminRoute {
  const path = window.location.pathname;
  // Pipelines (top-level)
  if (/^\/admin\/pipelines\/recitation\/?$/.test(path)) return 'pipelines-recitation';
  if (/^\/admin\/pipelines\/educational\/candidates(\/.*)?\/?$/.test(path)) return 'pipelines-educational-candidates';
  if (/^\/admin\/pipelines\/educational(\/.*)?\/?$/.test(path)) return 'pipelines-educational';
  if (/^\/admin\/pipelines\/?$/.test(path)) return 'pipelines-hub';
  // Legacy /admin/media/pipelines* paths still resolve so old bookmarks
  // and footer links don't 404. They render the same components as the
  // new top-level routes below.
  if (/^\/admin\/media\/pipelines\/?$/.test(path)) return 'pipelines-recitation';
  if (/^\/admin\/media\/educational\/pipelines(\/.*)?\/?$/.test(path)) return 'pipelines-educational';
  if (/^\/admin\/media\/educational(\/.*)?\/?$/.test(path)) return 'pipelines-educational-candidates';
  // Media sub-routes
  if (/^\/admin\/media\/recitations\/?$/.test(path)) return 'recitations';
  if (/^\/admin\/media\/resources\/?$/.test(path)) return 'resources';
  if (/^\/admin\/media\/music\/?$/.test(path)) return 'music';
  if (/^\/admin\/media\/generate\/?$/.test(path)) return 'generate';
  if (/^\/admin\/media\/explanations\/?$/.test(path)) return 'explanations';
  if (/^\/admin\/media\/generate-explanation\/?$/.test(path)) return 'generate-explanation';
  if (/^\/admin\/media\/?$/.test(path)) return 'media';
  if (/^\/admin\/scheduler\/?$/.test(path)) return 'scheduler';
  if (/^\/admin\/settings\/?$/.test(path)) return 'settings';
  if (/^\/admin\/revisions\/?$/.test(path)) return 'revisions';
  if (/^\/admin\/vocabulary\/?$/.test(path)) return 'vocabulary';
  const m = path.match(/^\/admin\/vocabulary\/([^/]+)\/?$/);
  if (m) return 'vocabulary-studio';
  if (/^\/admin\/proper-nouns\/?$/.test(path)) return 'proper-nouns';
  if (/^\/admin\/verse-settings\/?$/.test(path)) return 'verse-settings';
  if (/^\/admin\/verse-of-the-day\/?$/.test(path)) return 'verse-of-the-day';
  if (/^\/admin\/stats\/?$/.test(path)) return 'stats';
  if (/^\/admin\/judge-lessons\/?$/.test(path)) return 'judge-lessons';
  if (/^\/admin\/qa\/?$/.test(path)) return 'assistant-qa';
  if (/^\/admin\/exegesis\/?$/.test(path)) return 'exegesis';
  return 'dashboard';
}

interface AdminSection {
  href: string;
  label: string;
  description: string;
  matches: (route: AdminRoute) => boolean;
}

const ADMIN_SECTIONS: AdminSection[] = [
  {
    href: '/admin/pipelines',
    label: 'Pipelines',
    description: 'Recitation (English/Arabic) and Educational pipelines that auto-generate YouTube Shorts.',
    matches: (r) =>
      r === 'pipelines-hub' || r === 'pipelines-recitation' ||
      r === 'pipelines-educational' || r === 'pipelines-educational-candidates',
  },
  {
    href: '/admin/scheduler',
    label: 'Scheduler',
    description: 'Daily run times for every pipeline + the global YouTube upload schedule.',
    matches: (r) => r === 'scheduler',
  },
  {
    href: '/admin/media',
    label: 'Media',
    description: 'Recitations, background videos, music, verse-explanation builder.',
    matches: (r) =>
      r === 'media' || r === 'recitations' || r === 'resources' || r === 'music' ||
      r === 'generate' || r === 'explanations' || r === 'generate-explanation',
  },
  {
    href: '/admin/revisions',
    label: 'Revisions',
    description: 'Vocabulary surveys and proper-noun edits.',
    matches: (r) => r === 'revisions' || r === 'vocabulary' || r === 'vocabulary-studio' || r === 'proper-nouns',
  },
  {
    href: '/admin/verse-of-the-day',
    label: 'Verse of the Day',
    description: 'Curate the rotation of verses shown on the homepage.',
    matches: (r) => r === 'verse-of-the-day',
  },
  {
    href: '/admin/stats',
    label: 'Stats',
    description: 'Public-site analytics and YouTube performance with 7d/30d trends.',
    matches: (r) => r === 'stats',
  },
  {
    href: '/admin/judge-lessons',
    label: 'Judge Lessons',
    description: 'Performance-driven refinements to the interestingness judge — what YouTube engagement is teaching the pipeline.',
    matches: (r) => r === 'judge-lessons',
  },
  {
    href: '/admin/qa',
    label: 'Ask the Quran',
    description: 'Review, correct, hide, or remove the saved Q&A the assistant shows on each verse.',
    matches: (r) => r === 'assistant-qa',
  },
  {
    href: '/admin/exegesis',
    label: 'Exegesis',
    description: 'Teacher-voice commentary distilled from the verse Q&A, shown beneath the translation notes.',
    matches: (r) => r === 'exegesis',
  },
  {
    href: '/admin/verse-settings',
    label: 'Verse Settings',
    description: 'Default reciter for the public reader.',
    matches: (r) => r === 'verse-settings',
  },
  {
    href: '/admin/settings',
    label: 'Settings',
    description: 'API keys, OAuth credentials, integrations.',
    matches: (r) => r === 'settings',
  },
];

export default function AdminPage() {
  const [authed, setAuthed] = useState(false);
  const [checking, setChecking] = useState(true);
  const [username, setUsername] = useState('');

  const route = getAdminRoute();

  // Visual indicator that we're on local dev, not production.
  // Prevents the "settings appear wiped" panic when looking at the local
  // sandbox's admin_preferences table (which is naturally empty) and
  // mistaking it for production.
  const isDev = typeof window !== 'undefined' && (
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1' ||
    window.location.hostname.endsWith('.local')
  );

  useEffect(() => {
    if (!isLoggedIn()) {
      setChecking(false);
      return;
    }
    verifyToken()
      .then((data) => {
        setAuthed(true);
        setUsername(data.username);
      })
      .catch(() => {
        clearToken();
      })
      .finally(() => setChecking(false));
  }, []);

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-stone-50">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
      </div>
    );
  }

  if (!authed) {
    return <AdminLogin onLogin={() => window.location.reload()} />;
  }

  function handleLogout() {
    clearToken();
    window.location.href = '/admin';
  }

  return (
    <div className={`min-h-screen ${isDev ? 'bg-rose-50' : 'bg-stone-50'}`}>
      {/* Admin nav. Wider container + wrapping section links so the
          full list of pages fits comfortably as the admin surface
          grows. Previously max-w-5xl with no wrap, which crowded
          everything onto one tight line once Judge Lessons + Stats
          were both added. */}
      <nav className={`border-b ${isDev ? 'border-rose-300 bg-rose-100' : 'border-stone-200 bg-white'}`}>
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-start justify-between gap-4">
          <div className="flex items-center gap-x-4 gap-y-1.5 flex-wrap min-w-0">
            <a href="/" className="text-sm font-serif font-medium text-stone-800 hover:text-stone-600 whitespace-nowrap">
              al-nuqta
            </a>
            {isDev && (
              <span
                className="px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-rose-600 text-white uppercase whitespace-nowrap"
                title="You are on local dev — data is sandboxed and separate from production"
              >
                Dev
              </span>
            )}
            <span className="text-stone-300">|</span>
            <a
              href="/admin"
              className={`text-sm whitespace-nowrap ${route === 'dashboard' ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
            >
              Dashboard
            </a>
            {/* Section links live in the dashboard tile grid when the
                user is on /admin. Once they drill into a section, the
                links reappear in the nav for quick lateral movement. */}
            {route !== 'dashboard' && ADMIN_SECTIONS.map((s) => (
              <a
                key={s.href}
                href={s.href}
                className={`text-sm whitespace-nowrap ${s.matches(route) ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
              >
                {s.label}
              </a>
            ))}
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <span className="text-xs text-stone-400 whitespace-nowrap">{username}</span>
            <button
              onClick={handleLogout}
              className="text-xs text-stone-500 hover:text-stone-700 cursor-pointer"
            >
              Sign out
            </button>
          </div>
        </div>
      </nav>

      {/* Breadcrumbs for nested routes — Media branch */}
      {(route === 'recitations' || route === 'resources' || route === 'music' || route === 'generate' || route === 'explanations' || route === 'generate-explanation') && (
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="flex items-center gap-1.5 text-xs text-stone-400">
            <a href="/admin/media" className="hover:text-stone-600">Media</a>
            <span>/</span>
            <span className="text-stone-600">
              {route === 'recitations' && 'Verse Recitations'}
              {route === 'resources' && 'Background Videos'}
              {route === 'music' && 'Background Music'}
              {route === 'generate' && 'Generate Verse Recitation Video'}
              {route === 'explanations' && 'Verse Explanations'}
              {route === 'generate-explanation' && 'Generate Explanation Video'}
            </span>
          </div>
        </div>
      )}
      {/* Breadcrumbs — Pipelines branch */}
      {(route === 'pipelines-recitation' || route === 'pipelines-educational' || route === 'pipelines-educational-candidates') && (
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="flex items-center gap-1.5 text-xs text-stone-400">
            <a href="/admin/pipelines" className="hover:text-stone-600">Pipelines</a>
            <span>/</span>
            <span className="text-stone-600">
              {route === 'pipelines-recitation' && 'Recitation (English/Arabic)'}
              {route === 'pipelines-educational' && 'Educational pipelines'}
              {route === 'pipelines-educational-candidates' && 'Educational candidates'}
            </span>
          </div>
        </div>
      )}
      {(route === 'vocabulary' || route === 'vocabulary-studio' || route === 'proper-nouns') && (
        <div className="max-w-7xl mx-auto px-4 py-2">
          <div className="flex items-center gap-1.5 text-xs text-stone-400">
            <a href="/admin/revisions" className="hover:text-stone-600">Revisions</a>
            <span>/</span>
            <span className="text-stone-600">
              {(route === 'vocabulary' || route === 'vocabulary-studio') && 'Vocabulary'}
              {route === 'proper-nouns' && 'Proper Nouns'}
            </span>
          </div>
        </div>
      )}

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {route === 'dashboard' && <AdminDashboard username={username} />}
        {route === 'settings' && <AdminSettings />}
        {route === 'scheduler' && <SchedulerPage />}
        {route === 'media' && <AdminMedia />}
        {route === 'recitations' && <VerseRecitations />}
        {route === 'resources' && <AdminResources />}
        {route === 'music' && <AdminMusic />}
        {route === 'generate' && <GenerateVideo />}
        {route === 'explanations' && <ExplanationBuilder />}
        {route === 'generate-explanation' && <GenerateExplanationVideo />}
        {route === 'pipelines-hub' && <AdminPipelines />}
        {route === 'pipelines-recitation' && <PipelineManager />}
        {route === 'pipelines-educational' && <AdminEducationalPipelines />}
        {route === 'pipelines-educational-candidates' && <AdminEducational />}
        {route === 'revisions' && <AdminRevisions />}
        {route === 'vocabulary' && <AdminVocabulary />}
        {route === 'vocabulary-studio' && <AdminVocabularyStudio />}
        {route === 'proper-nouns' && <AdminProperNouns />}
        {route === 'verse-settings' && <VerseSettings />}
        {route === 'verse-of-the-day' && <AdminVerseOfTheDay />}
        {route === 'stats' && <StatsPage />}
        {route === 'judge-lessons' && <JudgeLessonsPage />}
        {route === 'assistant-qa' && <AdminAssistantQA />}
        {route === 'exegesis' && <AdminExegesis />}
      </div>
    </div>
  );
}

/* =================================================================== */
/*  Admin dashboard                                                    */
/* =================================================================== */

/**
 * The Admin Dashboard at /admin. Composes:
 *   - DashboardAlerts (silent-failure traps)
 *   - DashboardHero (time-aware greeting + at-a-glance status pill)
 *   - DashboardStats (3 live tiles: pipeline runs, uploads, queue)
 *   - DashboardSections (the section grid, redesigned with icons)
 *   - DashboardActivity (the most recent events across all sources)
 *
 * Each subsection fetches its own data so a slow endpoint can't
 * delay the whole page; tiles render their loading state
 * independently.
 */
function AdminDashboard({ username }: { username: string }) {
  return (
    <div>
      <DashboardAlerts />
      <DashboardHero username={username} />
      <DashboardStats />
      <DashboardSections />
      <DashboardActivity />
    </div>
  );
}

/* ------------------------------------------------------------- */

function timeOfDayGreeting(): string {
  const h = new Date().getHours();
  if (h < 5) return 'Up late';
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  if (h < 22) return 'Good evening';
  return 'Up late';
}

function DashboardHero({ username }: { username: string }) {
  // Tiny status pill on the right summarizes auto-publishing health
  // in one glance — same data the SchedulerPage's full status panel
  // shows, condensed to a chip.
  const [healthState, setHealthState] = useState<'ok' | 'warn' | 'bad' | 'loading'>('loading');
  const [healthDetail, setHealthDetail] = useState('');
  // Build metadata baked into the image at deploy time. On local dev
  // these come back empty and we just render nothing; the dashboard
  // doesn't need a "running locally" hint cluttering the hero.
  const [build, setBuild] = useState<BuildInfo | null>(null);

  useEffect(() => {
    getBuildInfo().then(setBuild).catch(() => setBuild(null));
  }, []);

  useEffect(() => {
    Promise.all([
      getPreferences().catch(() => ({} as Record<string, string>)),
      getPipelineSchedules().catch(() => []),
      getAllEducationalSchedules().catch(() => []),
      getYoutubeUploadSchedule().catch(() => null),
    ]).then(([prefs, recScheds, eduScheds, ytSched]) => {
      const hasCreds = !!(prefs.youtube_client_id && prefs.youtube_client_secret && prefs.youtube_refresh_token);
      const allScheds = [
        ...recScheds.map((s) => ({ enabled: s.enabled, times: s.times })),
        ...eduScheds.map((s) => ({ enabled: s.enabled, times: s.times })),
      ];
      const anyPipelineRunning = allScheds.some((s) => s.enabled && s.times.length > 0);
      const uploadRunning = !!(ytSched?.enabled && ytSched.times.length > 0);

      if (!hasCreds || (!uploadRunning && anyPipelineRunning)) {
        setHealthState('bad');
        setHealthDetail(!hasCreds ? 'YouTube not connected' : 'Upload disabled');
      } else if (!uploadRunning || !anyPipelineRunning) {
        setHealthState('warn');
        setHealthDetail('Setup incomplete');
      } else {
        setHealthState('ok');
        setHealthDetail('Auto-publishing');
      }
    });
  }, []);

  const stateUI = {
    loading: { dot: 'bg-stone-300', label: 'Checking…',  ring: 'ring-stone-200' },
    ok:      { dot: 'bg-emerald-500', label: healthDetail, ring: 'ring-emerald-200' },
    warn:    { dot: 'bg-amber-500',   label: healthDetail, ring: 'ring-amber-200' },
    bad:     { dot: 'bg-red-500',     label: healthDetail, ring: 'ring-red-200' },
  }[healthState];

  return (
    <div className="relative mb-8 overflow-hidden rounded-2xl border border-stone-200 bg-gradient-to-br from-stone-50 via-amber-50/30 to-emerald-50/20 px-6 py-7 sm:px-8 sm:py-9">
      {/* Decorative wash — a soft warm-cream texture in the corner.
          Subtle enough not to fight content, present enough that the
          hero feels different from a generic card. */}
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 -right-24 h-64 w-64 rounded-full bg-amber-200/30 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -bottom-32 -left-16 h-72 w-72 rounded-full bg-emerald-200/20 blur-3xl"
      />
      <div className="relative flex items-start justify-between gap-4 flex-wrap">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-1">
            al-nuqta · admin
          </div>
          <h1 className="font-serif text-3xl sm:text-4xl font-medium text-stone-800 tracking-tight">
            {timeOfDayGreeting()}, {username}.
          </h1>
          <p className="text-sm text-stone-600 mt-2 max-w-xl">
            Here's what's happening with your pipelines and the
            content flowing through them today.
          </p>
          {build && build.sha_short && (
            <BuildInfoLine build={build} />
          )}
        </div>
        <a
          href="/admin/scheduler"
          className={`inline-flex items-center gap-2 rounded-full bg-white/70 backdrop-blur-sm px-4 py-2 text-xs font-medium text-stone-700 ring-1 ${stateUI.ring} hover:bg-white transition-colors`}
          title="Auto-publishing health — click for details"
        >
          <span className={`h-2 w-2 rounded-full ${stateUI.dot}`} />
          {stateUI.label}
        </a>
      </div>
    </div>
  );
}

function BuildInfoLine({ build }: { build: BuildInfo }) {
  // Format the deploy timestamp as a relative-then-absolute hint:
  // "2 hours ago" reads at a glance, but a hover-title showing the
  // exact ISO timestamp + commit subject lets the operator
  // disambiguate "is this the deploy I just pushed?".
  const date = build.date ? new Date(build.date) : null;
  const relative = date && !isNaN(date.getTime()) ? buildRelative(date) : '';
  const absolute = date && !isNaN(date.getTime()) ? date.toLocaleString() : '';
  const commitUrl = build.repo
    ? `https://github.com/${build.repo}/commit/${build.sha}`
    : null;

  return (
    <p className="text-[11px] text-stone-500 mt-2.5 max-w-xl">
      Website last updated{' '}
      <span title={absolute || undefined}>
        {relative || (absolute || 'recently')}
      </span>
      {build.sha_short && (
        <>
          {' '}via commit{' '}
          {commitUrl ? (
            <a
              href={commitUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-stone-700 underline decoration-dotted underline-offset-2 hover:text-stone-900"
              title={build.message || build.sha}
            >
              {build.sha_short}
            </a>
          ) : (
            <span className="font-mono text-stone-700" title={build.message || build.sha}>
              {build.sha_short}
            </span>
          )}
        </>
      )}
      {build.message && (
        <span className="text-stone-400"> — {truncate(build.message, 80)}</span>
      )}
    </p>
  );
}

function buildRelative(d: Date): string {
  const diffMs = Date.now() - d.getTime();
  if (diffMs < 0) return 'in the future';
  const min = Math.round(diffMs / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min} minute${min === 1 ? '' : 's'} ago`;
  const h = Math.round(min / 60);
  if (h < 24) return `${h} hour${h === 1 ? '' : 's'} ago`;
  const days = Math.round(h / 24);
  if (days < 30) return `${days} day${days === 1 ? '' : 's'} ago`;
  return d.toLocaleDateString();
}

function truncate(s: string, max: number): string {
  if (s.length <= max) return s;
  return s.slice(0, max - 1).trimEnd() + '…';
}

/* ------------------------------------------------------------- */

interface StatTile {
  label: string;
  primary: string;
  secondary?: string;
  href?: string;
  state?: 'neutral' | 'ok' | 'warn' | 'bad';
}

function DashboardStats() {
  const [tiles, setTiles] = useState<StatTile[] | null>(null);

  useEffect(() => {
    // Pull every source the dashboard summarizes. Each .catch returns a
    // sentinel so one failing endpoint doesn't blank the whole strip.
    Promise.all([
      getWebsiteStats('7d').catch(() => null),
      getYoutubeStats('7d').catch(() => null),
      getYoutubeUploadRuns(200).catch(() => [] as YoutubeUploadRun[]),
    ]).then(([webStats, ytStats, ytRuns]) => {
      // YouTube uploads tile shows the last 24h — operationally that's
      // the window where a stuck or failing scheduler matters. The
      // analytics tiles next to it use 7d via the stats API.
      const since = Date.now() - 86_400_000;

      // Tile 1 — Website visits (replaces the old Pipeline Runs tile).
      // Primary = page views; secondary = unique visitors. Trend pill in
      // the secondary line so the operator sees instantly whether the
      // site is growing.
      let webPrimary = '—';
      let webSecondary = 'unavailable';
      let webState: StatTile['state'] = 'neutral';
      if (webStats) {
        const pv = webStats.totals.page_views;
        const uv = webStats.totals.unique_visitors;
        const pvPrior = webStats.totals.page_views_prior;
        const trend = pvPrior > 0
          ? Math.round(((pv - pvPrior) / pvPrior) * 100)
          : (pv > 0 ? 100 : 0);
        const arrow = trend > 0 ? '▲' : trend < 0 ? '▼' : '·';
        webPrimary = pv.toLocaleString();
        webSecondary = `${uv.toLocaleString()} unique · ${arrow} ${Math.abs(trend)}%`;
        webState = pv === 0 ? 'neutral' : (trend < 0 ? 'warn' : 'ok');
      }

      // Tile 2 — YouTube views with 7-day gain. Empty when no snapshots
      // have been taken yet (post-deploy / fresh install).
      let ytPrimary = '—';
      let ytSecondary = 'no snapshots yet';
      let ytState: StatTile['state'] = 'neutral';
      if (ytStats && ytStats.snapshot_count > 0) {
        const total = ytStats.totals.total_views;
        const gain = ytStats.totals.views_gain_period;
        ytPrimary = total.toLocaleString();
        ytSecondary = `+${gain.toLocaleString()} this week`;
        ytState = gain > 0 ? 'ok' : 'neutral';
      }

      // Tile 3 — YouTube upload pipeline health (kept from old dashboard).
      const recentUploads = ytRuns.filter((r) => new Date(r.fired_at).getTime() >= since);
      const uploaded = recentUploads.filter((r) => r.status === 'uploaded').length;
      const failed = recentUploads.filter((r) => r.status === 'error').length;

      // Tile 4 — YouTube subscribers (replaces the old Educational
      // Candidates tile). null channel block means we haven't taken
      // the first snapshot yet (post-deploy / OAuth scope issue).
      let subPrimary = '—';
      let subSecondary = 'no snapshots yet';
      let subState: StatTile['state'] = 'neutral';
      if (ytStats && ytStats.channel) {
        const ch = ytStats.channel;
        subPrimary = ch.current_subscribers.toLocaleString();
        if (ch.subscribers_gain > 0) {
          subSecondary = `+${ch.subscribers_gain.toLocaleString()} this week`;
          subState = 'ok';
        } else if (ch.subscribers_gain < 0) {
          subSecondary = `${ch.subscribers_gain.toLocaleString()} this week`;
          subState = 'warn';
        } else {
          subSecondary = 'flat this week';
          subState = 'neutral';
        }
      }

      setTiles([
        {
          label: 'Website visits · 7d',
          primary: webPrimary,
          secondary: webSecondary,
          href: '/admin/stats',
          state: webState,
        },
        {
          label: 'YouTube views · 7d',
          primary: ytPrimary,
          secondary: ytSecondary,
          // Deep-link with #youtube hash so StatsPage opens on the
          // YouTube tab directly. The Website tile keeps the bare path
          // since 'website' is the default.
          href: '/admin/stats#youtube',
          state: ytState,
        },
        {
          label: 'YouTube uploads · 24h',
          primary: `${uploaded}`,
          secondary: failed > 0 ? `${uploaded} published · ${failed} failed` : `${uploaded} published`,
          href: '/admin/scheduler#youtube-upload',
          state: failed > 0 ? 'warn' : (uploaded === 0 ? 'neutral' : 'ok'),
        },
        {
          label: 'YouTube subscribers',
          primary: subPrimary,
          secondary: subSecondary,
          href: '/admin/stats#youtube',
          state: subState,
        },
      ]);
    });
  }, []);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-8">
      {(tiles ?? Array(4).fill(null)).map((t, i) => (
        <StatTileView key={i} tile={t} />
      ))}
    </div>
  );
}

function StatTileView({ tile }: { tile: StatTile | null }) {
  if (!tile) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white px-5 py-4">
        <div className="h-3 w-24 bg-stone-100 rounded animate-pulse mb-3" />
        <div className="h-7 w-16 bg-stone-100 rounded animate-pulse mb-2" />
        <div className="h-3 w-32 bg-stone-100 rounded animate-pulse" />
      </div>
    );
  }
  const accent = {
    neutral: 'border-stone-200',
    ok:      'border-emerald-200 bg-gradient-to-br from-white to-emerald-50/30',
    warn:    'border-amber-200 bg-gradient-to-br from-white to-amber-50/30',
    bad:     'border-red-200 bg-gradient-to-br from-white to-red-50/30',
  }[tile.state ?? 'neutral'];
  const Wrapper: React.ElementType = tile.href ? 'a' : 'div';
  return (
    <Wrapper
      {...(tile.href ? { href: tile.href } : {})}
      className={`block rounded-xl border ${accent} px-5 py-4 transition-all ${tile.href ? 'hover:shadow-sm hover:-translate-y-0.5' : ''}`}
    >
      <div className="text-[10px] font-semibold uppercase tracking-wider text-stone-500 mb-1.5">
        {tile.label}
      </div>
      <div className="text-3xl font-semibold text-stone-800 tracking-tight">
        {tile.primary}
      </div>
      {tile.secondary && (
        <div className="text-xs text-stone-500 mt-1">{tile.secondary}</div>
      )}
    </Wrapper>
  );
}

/* ------------------------------------------------------------- */

interface SectionStyle {
  href: string;
  label: string;
  description: string;
  icon: ReactNode;
  accent: string;  // tailwind classes for the icon tile bg + ring
}

const SECTION_STYLES: SectionStyle[] = [
  {
    href: '/admin/pipelines',
    label: 'Pipelines',
    description: 'Recitation (English/Arabic) and Educational pipelines that auto-generate YouTube Shorts.',
    accent: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <path d="M3 6h13l4 4v8H3z" />
        <path d="M8 6V3h8v3" />
        <circle cx="9" cy="13" r="1.5" /><circle cx="15" cy="13" r="1.5" />
      </svg>
    ),
  },
  {
    href: '/admin/scheduler',
    label: 'Scheduler',
    description: 'Daily run times for every pipeline + the global YouTube upload schedule.',
    accent: 'bg-violet-50 text-violet-700 ring-violet-100',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </svg>
    ),
  },
  {
    href: '/admin/media',
    label: 'Media',
    description: 'Recitations, background videos, music, verse-explanation builder.',
    accent: 'bg-blue-50 text-blue-700 ring-blue-100',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <rect x="3" y="5" width="18" height="14" rx="2" />
        <path d="M10 9l5 3-5 3z" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
  {
    href: '/admin/revisions',
    label: 'Revisions',
    description: 'Vocabulary surveys and proper-noun edits.',
    accent: 'bg-rose-50 text-rose-700 ring-rose-100',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <path d="M14 4l6 6-10 10H4v-6z" />
        <path d="M13 5l6 6" />
      </svg>
    ),
  },
  {
    href: '/admin/verse-of-the-day',
    label: 'Verse of the Day',
    description: 'Curate the rotation of verses shown on the homepage.',
    accent: 'bg-teal-50 text-teal-700 ring-teal-100',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <path d="M4 19V5a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v14l-4-3-4 3-4-3-4 3z" />
        <path d="M9 8h6M9 12h4" />
      </svg>
    ),
  },
  {
    href: '/admin/verse-settings',
    label: 'Verse Settings',
    description: 'Default reciter for the public reader.',
    accent: 'bg-amber-50 text-amber-700 ring-amber-100',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <path d="M4 6h12M4 12h16M4 18h8" />
        <circle cx="18" cy="6" r="2" /><circle cx="14" cy="18" r="2" />
      </svg>
    ),
  },
  {
    href: '/admin/qa',
    label: 'Ask the Quran',
    description: 'Review and moderate the saved Q&A the assistant shows on each verse.',
    accent: 'bg-violet-50 text-violet-700 ring-violet-100',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <path d="M21 12a8 8 0 0 1-11.5 7.2L4 20l1-4.5A8 8 0 1 1 21 12z" />
        <path d="M9.6 9.4a2.4 2.4 0 1 1 3.1 2.4c-.7.3-1.2.9-1.2 1.6" />
        <path d="M11.5 16.3h.01" />
      </svg>
    ),
  },
  {
    href: '/admin/exegesis',
    label: 'Exegesis',
    description: 'Review teacher-voice exegesis notes built from grade-3/4 Q&A, shown at the bottom of translation notes.',
    accent: 'bg-indigo-50 text-indigo-700 ring-indigo-100',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <path d="M4 5a2 2 0 0 1 2-2h9l5 5v11a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
        <path d="M14 3v5h5" />
        <path d="M8 13h8M8 17h5" />
      </svg>
    ),
  },
  {
    href: '/admin/settings',
    label: 'Settings',
    description: 'API keys, OAuth credentials, integrations.',
    accent: 'bg-stone-100 text-stone-700 ring-stone-200',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="h-5 w-5">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 0 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 0 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3 1.7 1.7 0 0 0 1-1.5V3a2 2 0 0 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8v0a1.7 1.7 0 0 0 1.5 1H21a2 2 0 0 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
      </svg>
    ),
  },
];

function DashboardSections() {
  return (
    <div className="mb-10">
      <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500 mb-3">Manage</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {SECTION_STYLES.map((s) => (
          <a
            key={s.href}
            href={s.href}
            className="group relative block rounded-xl border border-stone-200 bg-white px-5 py-4 hover:border-stone-400 hover:shadow-sm transition-all hover:-translate-y-0.5"
          >
            <div className={`inline-flex items-center justify-center h-9 w-9 rounded-lg ring-1 mb-3 ${s.accent}`}>
              {s.icon}
            </div>
            <div className="font-semibold text-stone-800">{s.label}</div>
            <div className="text-xs text-stone-500 mt-1 leading-relaxed">{s.description}</div>
            <span className="absolute top-4 right-4 text-stone-300 group-hover:text-stone-500 transition-colors">
              →
            </span>
          </a>
        ))}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------- */

interface ActivityRow {
  kind: 'pipeline' | 'educational' | 'upload';
  label: string;
  detail: string;
  status: string;
  status_tone: 'ok' | 'warn' | 'bad' | 'neutral';
  when: Date;
}

function DashboardActivity() {
  const [rows, setRows] = useState<ActivityRow[] | null>(null);

  useEffect(() => {
    Promise.all([
      getPipelineScheduleRuns({ limit: 8 }).catch(() => [] as PipelineScheduleRun[]),
      getAllEducationalScheduleRuns(8).catch(() => [] as EducationalScheduleRunGlobal[]),
      getYoutubeUploadRuns(8).catch(() => [] as YoutubeUploadRun[]),
    ]).then(([rec, edu, ups]) => {
      const merged: ActivityRow[] = [
        ...rec.map((r) => ({
          kind: 'pipeline' as const,
          label: r.pipeline_name || 'Recitation pipeline',
          detail: r.note || `Scheduled ${r.scheduled_time}`,
          status: r.status,
          status_tone: statusTone(r.status),
          when: new Date(r.fired_at),
        })),
        ...edu.map((r) => ({
          kind: 'educational' as const,
          label: r.pipeline_name || 'Educational pipeline',
          detail: r.note || `Scheduled ${r.scheduled_time}`,
          status: r.status,
          status_tone: statusTone(r.status),
          when: new Date(r.fired_at),
        })),
        ...ups.map((r) => ({
          kind: 'upload' as const,
          label: 'YouTube upload',
          detail: r.note || (r.youtube_video_id ? `→ ${r.youtube_video_id}` : `Scheduled ${r.scheduled_time}`),
          status: r.status,
          status_tone: statusTone(r.status),
          when: new Date(r.fired_at),
        })),
      ];
      // Newest first; cap at the 8 most recent so the dashboard
      // doesn't sprawl. Operators wanting more go to the full
      // audit logs on /admin/scheduler.
      merged.sort((a, b) => b.when.getTime() - a.when.getTime());
      setRows(merged.slice(0, 8));
    });
  }, []);

  return (
    <div className="mb-6">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500">Recent activity</h2>
        <a href="/admin/scheduler" className="text-xs text-stone-500 hover:text-stone-700">Full audit log →</a>
      </div>
      {rows === null ? (
        <div className="rounded-xl border border-stone-200 bg-white p-4">
          <div className="text-sm text-stone-400">Loading…</div>
        </div>
      ) : rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-300 bg-stone-50/40 p-6 text-sm text-stone-500 text-center">
          No activity yet. Once your pipelines and YouTube uploads start firing, you'll see them here.
        </div>
      ) : (
        <div className="rounded-xl border border-stone-200 bg-white overflow-hidden">
          <ul className="divide-y divide-stone-100">
            {rows.map((r, i) => (
              <li key={i} className="flex items-start gap-3 px-4 py-3 text-sm hover:bg-stone-50/60 transition-colors">
                <KindIcon kind={r.kind} />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-stone-800 truncate">{r.label}</span>
                    <ActivityStatusBadge tone={r.status_tone} label={prettyStatus(r.status)} />
                  </div>
                  <div className="text-xs text-stone-500 mt-0.5 truncate">{r.detail}</div>
                </div>
                <div className="text-xs text-stone-400 flex-shrink-0">{relativeTime(r.when)}</div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function KindIcon({ kind }: { kind: ActivityRow['kind'] }) {
  // Tiny shape per kind so the eye can scan vertically: pipeline /
  // educational / upload are immediately distinguishable without
  // reading text.
  const { bg, fill, glyph } = {
    pipeline:    { bg: 'bg-emerald-50', fill: 'text-emerald-700', glyph: 'P' },
    educational: { bg: 'bg-violet-50',  fill: 'text-violet-700',  glyph: 'E' },
    upload:      { bg: 'bg-red-50',     fill: 'text-red-700',     glyph: '↑' },
  }[kind];
  return (
    <span className={`flex-shrink-0 inline-flex items-center justify-center h-7 w-7 rounded-md text-[11px] font-semibold ${bg} ${fill}`}>
      {glyph}
    </span>
  );
}

function ActivityStatusBadge({ tone, label }: { tone: ActivityRow['status_tone']; label: string }) {
  const cls = {
    ok:      'bg-emerald-50 text-emerald-700 border-emerald-100',
    warn:    'bg-amber-50 text-amber-700 border-amber-100',
    bad:     'bg-red-50 text-red-700 border-red-100',
    neutral: 'bg-stone-50 text-stone-600 border-stone-200',
  }[tone];
  return (
    <span className={`inline-block rounded border px-1.5 py-0.5 text-[10px] font-medium ${cls}`}>
      {label}
    </span>
  );
}

function statusTone(s: string): ActivityRow['status_tone'] {
  if (s === 'fired' || s === 'uploaded' || s === 'running') return 'ok';
  if (s.startsWith('skipped_sanity')) return 'warn';
  if (s.startsWith('skipped')) return 'neutral';
  if (s === 'error') return 'bad';
  return 'neutral';
}

function prettyStatus(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function relativeTime(d: Date): string {
  const diffMs = Date.now() - d.getTime();
  const min = Math.round(diffMs / 60000);
  if (min < 1) return 'just now';
  if (min < 60) return `${min}m ago`;
  const h = Math.round(min / 60);
  if (h < 24) return `${h}h ago`;
  const days = Math.round(h / 24);
  if (days < 30) return `${days}d ago`;
  return d.toLocaleDateString();
}

/**
 * Alerts that show at the top of the Admin Dashboard.
 * Today: YouTube refresh token expiry.
 * Over time, other time-sensitive admin concerns can live here.
 */
function DashboardAlerts() {
  const [alerts, setAlerts] = useState<{
    severity: 'warn' | 'danger';
    title: string;
    body: string;
    href?: string;
    hrefLabel?: string;
  }[]>([]);

  useEffect(() => {
    Promise.all([
      getPreferences(),
      getYoutubeUploadSchedule().catch(() => null),
      getPipelineSchedules().catch(() => []),
      getAllEducationalSchedules().catch(() => []),
    ]).then(([prefs, ytSchedule, pipelineScheds, eduScheds]) => {
      const out: typeof alerts = [];

      // YouTube upload scheduler is enabled but credentials are incomplete.
      // This is a silent-failure trap — scheduler fires, upload fails, user
      // doesn't notice until days later. Surface it front and center.
      if (ytSchedule?.enabled) {
        const hasCreds = !!(prefs.youtube_client_id && prefs.youtube_client_secret && prefs.youtube_refresh_token);
        if (!hasCreds) {
          out.push({
            severity: 'danger',
            title: 'YouTube upload scheduler is enabled but credentials are missing',
            body: 'The scheduler is set to auto-upload, but one or more of Client ID / Client Secret / Refresh Token is not saved. Every scheduled upload will fail silently until this is fixed.',
            href: '/admin/settings',
            hrefLabel: 'Set credentials',
          });
        }

        // YouTube upload scheduler is enabled but has no configured
        // times — it never fires. Same silent-failure shape as the
        // credentials gap.
        if (!ytSchedule.times || ytSchedule.times.length === 0) {
          out.push({
            severity: 'danger',
            title: 'YouTube upload scheduler is enabled but has no times',
            body: 'Without at least one HH:MM slot, the upload scheduler never fires. Configured pipeline videos will pile up unuploaded.',
            href: '/admin/scheduler',
            hrefLabel: 'Add a time',
          });
        }
      }

      // Pipeline schedules enabled but no times — same trap, on the
      // generation side. Aggregated across both pipeline families so
      // a single banner covers everything misconfigured.
      const allScheds: Array<{
        kind: 'recitation' | 'educational';
        name: string;
        enabled: boolean;
        times: string[];
      }> = [
        ...pipelineScheds.map((s) => ({
          kind: 'recitation' as const,
          name: s.pipeline_name,
          enabled: s.enabled,
          times: s.times,
        })),
        ...eduScheds.map((s) => ({
          kind: 'educational' as const,
          name: s.pipeline_name,
          enabled: s.enabled,
          times: s.times,
        })),
      ];
      const enabledNoTimes = allScheds.filter((s) => s.enabled && (!s.times || s.times.length === 0));
      if (enabledNoTimes.length > 0) {
        const names = enabledNoTimes.map((s) => `"${s.name}"`).join(', ');
        out.push({
          severity: 'warn',
          title: `${enabledNoTimes.length} pipeline schedule${enabledNoTimes.length === 1 ? '' : 's'} enabled with no times`,
          body: `${names} ${enabledNoTimes.length === 1 ? 'is' : 'are'} marked enabled but ${enabledNoTimes.length === 1 ? 'has' : 'have'} no daily times — the scheduler will never fire ${enabledNoTimes.length === 1 ? 'it' : 'them'}.`,
          href: '/admin/scheduler',
          hrefLabel: 'Add times',
        });
      }

      // Pipeline schedules are enabled but the YT upload schedule is
      // disabled — videos render and queue up but never reach
      // YouTube. Surface this because it's the most common
      // "uploads aren't happening" cause we've seen.
      const anyPipelineEnabled = allScheds.some((s) => s.enabled && s.times.length > 0);
      if (anyPipelineEnabled && ytSchedule && !ytSchedule.enabled) {
        out.push({
          severity: 'warn',
          title: 'Pipeline schedules are firing but YouTube upload is disabled',
          body: 'You have at least one pipeline schedule enabled, so videos will be generated. But the YouTube upload schedule is off, so they won\'t auto-publish — they\'ll sit on disk waiting. Enable the upload schedule (or upload manually).',
          href: '/admin/scheduler',
          hrefLabel: 'Enable upload',
        });
      }

      // YouTube refresh-token expiry
      const savedAt = prefs.youtube_refresh_token_saved_at;
      const token = prefs.youtube_refresh_token;
      if (token && savedAt) {
        const days = (Date.now() - new Date(savedAt).getTime()) / (1000 * 60 * 60 * 24);
        if (!isNaN(days)) {
          if (days >= 7) {
            out.push({
              severity: 'danger',
              title: 'YouTube refresh token likely expired',
              body: `Your OAuth refresh token was saved ${Math.round(days)} days ago. Google testing-mode tokens expire after 7 days. Uploads will start failing with invalid_grant errors.`,
              href: '/admin/settings',
              hrefLabel: 'Refresh it now',
            });
          } else if (days >= 5) {
            out.push({
              severity: 'warn',
              title: 'YouTube refresh token expiring soon',
              body: `Your OAuth refresh token is ${Math.round(days)} days old. It will stop working at the 7-day mark. Refresh it at your convenience.`,
              href: '/admin/settings',
              hrefLabel: 'Refresh it',
            });
          }
        }
      } else if (token && !savedAt) {
        // Legacy path: token saved before we started tracking saved_at.
        // Since we can't tell how old it is, warn proactively.
        out.push({
          severity: 'warn',
          title: 'YouTube refresh token age unknown',
          body: 'A refresh token is saved but we don\'t know when it was created (it predates our tracking). If your uploads start failing with invalid_grant errors, refresh the token.',
          href: '/admin/settings',
          hrefLabel: 'Refresh it',
        });
      }

      setAlerts(out);
    }).catch(() => { /* silent — dashboard shouldn't fail on prefs fetch */ });
  }, []);

  if (alerts.length === 0) return null;

  return (
    <div className="space-y-3 mb-6">
      {alerts.map((a, i) => (
        <div
          key={i}
          className={`rounded-xl border p-4 ${
            a.severity === 'danger'
              ? 'border-red-200 bg-red-50'
              : 'border-amber-200 bg-amber-50'
          }`}
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className={`text-sm font-semibold ${
                a.severity === 'danger' ? 'text-red-800' : 'text-amber-800'
              }`}>
                {a.title}
              </h3>
              <p className={`mt-1 text-xs leading-relaxed ${
                a.severity === 'danger' ? 'text-red-700' : 'text-amber-700'
              }`}>
                {a.body}
              </p>
            </div>
            {a.href && (
              <a
                href={a.href}
                className={`flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap ${
                  a.severity === 'danger'
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-amber-600 text-white hover:bg-amber-700'
                }`}
              >
                {a.hrefLabel || 'Fix'}
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
