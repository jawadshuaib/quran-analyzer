import { useState, useEffect } from 'react';
import { isLoggedIn, verifyToken, clearToken } from '../../api/admin';
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

type AdminRoute = 'dashboard' | 'settings' | 'scheduler' | 'media' | 'recitations' | 'resources' | 'music' | 'generate' | 'explanations' | 'generate-explanation' | 'pipelines';

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
  return 'dashboard';
}

export default function AdminPage() {
  const [authed, setAuthed] = useState(false);
  const [checking, setChecking] = useState(true);
  const [username, setUsername] = useState('');

  const route = getAdminRoute();

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
    <div className="min-h-screen bg-stone-50">
      {/* Admin nav */}
      <nav className="border-b border-stone-200 bg-white">
        <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <a href="/" className="text-sm font-serif font-medium text-stone-800 hover:text-stone-600">
              al-nuqta
            </a>
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

      {/* Content */}
      <div className="max-w-5xl mx-auto px-4 py-8">
        {route === 'dashboard' && (
          <div>
            <h1 className="text-xl font-semibold text-stone-800 mb-2">Admin Dashboard</h1>
            <p className="text-sm text-stone-500">Welcome back, {username}.</p>
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
      </div>
    </div>
  );
}
