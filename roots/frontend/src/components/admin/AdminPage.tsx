import { useState, useEffect } from 'react';
import {
  isLoggedIn, verifyToken, clearToken, getPreferences,
  getYoutubeUploadSchedule,
} from '../../api/admin';
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

type AdminRoute = 'dashboard' | 'settings' | 'scheduler' | 'media' | 'recitations' | 'resources' | 'music' | 'generate' | 'explanations' | 'generate-explanation' | 'pipelines' | 'revisions' | 'vocabulary' | 'vocabulary-studio' | 'proper-nouns';

function getAdminRoute(): AdminRoute {
  const path = window.location.pathname;
  if (/^\/admin\/media\/recitations\/?$/.test(path)) return 'recitations';
  if (/^\/admin\/media\/resources\/?$/.test(path)) return 'resources';
  if (/^\/admin\/media\/music\/?$/.test(path)) return 'music';
  if (/^\/admin\/media\/generate\/?$/.test(path)) return 'generate';
  if (/^\/admin\/media\/explanations\/?$/.test(path)) return 'explanations';
  if (/^\/admin\/media\/generate-explanation\/?$/.test(path)) return 'generate-explanation';
  if (/^\/admin\/media\/pipelines\/?$/.test(path)) return 'pipelines';
  if (/^\/admin\/media\/?$/.test(path)) return 'media';
  if (/^\/admin\/scheduler\/?$/.test(path)) return 'scheduler';
  if (/^\/admin\/settings\/?$/.test(path)) return 'settings';
  if (/^\/admin\/revisions\/?$/.test(path)) return 'revisions';
  if (/^\/admin\/vocabulary\/?$/.test(path)) return 'vocabulary';
  const m = path.match(/^\/admin\/vocabulary\/([^/]+)\/?$/);
  if (m) return 'vocabulary-studio';
  if (/^\/admin\/proper-nouns\/?$/.test(path)) return 'proper-nouns';
  return 'dashboard';
}

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
      {/* Admin nav */}
      <nav className={`border-b ${isDev ? 'border-rose-300 bg-rose-100' : 'border-stone-200 bg-white'}`}>
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <a href="/" className="text-sm font-serif font-medium text-stone-800 hover:text-stone-600">
              al-nuqta
            </a>
            {isDev && (
              <span
                className="px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wider bg-rose-600 text-white uppercase"
                title="You are on local dev — data is sandboxed and separate from production"
              >
                Dev
              </span>
            )}
            <span className="text-stone-300">|</span>
            <a
              href="/admin"
              className={`text-sm ${route === 'dashboard' ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
            >
              Dashboard
            </a>
            <a
              href="/admin/media"
              className={`text-sm ${route === 'media' || route === 'recitations' || route === 'resources' || route === 'music' || route === 'generate' || route === 'explanations' || route === 'generate-explanation' || route === 'pipelines' ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
            >
              Media
            </a>
            <a
              href="/admin/scheduler"
              className={`text-sm ${route === 'scheduler' ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
            >
              Scheduler
            </a>
            <a
              href="/admin/revisions"
              className={`text-sm ${route === 'revisions' || route === 'vocabulary' || route === 'vocabulary-studio' || route === 'proper-nouns' ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
            >
              Revisions
            </a>
            <a
              href="/admin/settings"
              className={`text-sm ${route === 'settings' ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
            >
              Settings
            </a>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-stone-400">{username}</span>
            <button
              onClick={handleLogout}
              className="text-xs text-stone-500 hover:text-stone-700 cursor-pointer"
            >
              Sign out
            </button>
          </div>
        </div>
      </nav>

      {/* Breadcrumbs for nested routes */}
      {(route === 'recitations' || route === 'resources' || route === 'music' || route === 'generate' || route === 'explanations' || route === 'generate-explanation' || route === 'pipelines') && (
        <div className="max-w-5xl mx-auto px-4 py-2">
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
              {route === 'pipelines' && 'Pipelines'}
            </span>
          </div>
        </div>
      )}
      {(route === 'vocabulary' || route === 'vocabulary-studio' || route === 'proper-nouns') && (
        <div className="max-w-5xl mx-auto px-4 py-2">
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
      <div className="max-w-5xl mx-auto px-4 py-8">
        {route === 'dashboard' && (
          <div>
            <h1 className="text-xl font-semibold text-stone-800 mb-2">Admin Dashboard</h1>
            <p className="text-sm text-stone-500 mb-6">Welcome back, {username}.</p>
            <DashboardAlerts />
          </div>
        )}
        {route === 'settings' && <AdminSettings />}
        {route === 'scheduler' && <SchedulerPage />}
        {route === 'media' && <AdminMedia />}
        {route === 'recitations' && <VerseRecitations />}
        {route === 'resources' && <AdminResources />}
        {route === 'music' && <AdminMusic />}
        {route === 'generate' && <GenerateVideo />}
        {route === 'explanations' && <ExplanationBuilder />}
        {route === 'generate-explanation' && <GenerateExplanationVideo />}
        {route === 'pipelines' && <PipelineManager />}
        {route === 'revisions' && <AdminRevisions />}
        {route === 'vocabulary' && <AdminVocabulary />}
        {route === 'vocabulary-studio' && <AdminVocabularyStudio />}
        {route === 'proper-nouns' && <AdminProperNouns />}
      </div>
    </div>
  );
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
    ]).then(([prefs, ytSchedule]) => {
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
