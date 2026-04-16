import { useState, useEffect } from 'react';
import { isLoggedIn, verifyToken, clearToken } from '../../api/admin';
import AdminLogin from './AdminLogin';
import AdminSettings from './AdminSettings';
import AdminMedia from './AdminMedia';
import VerseRecitations from './VerseRecitations';

type AdminRoute = 'dashboard' | 'settings' | 'media' | 'recitations';

function getAdminRoute(): AdminRoute {
  const path = window.location.pathname;
  if (/^\/admin\/media\/recitations\/?$/.test(path)) return 'recitations';
  if (/^\/admin\/media\/?$/.test(path)) return 'media';
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
              className={`text-sm ${route === 'media' || route === 'recitations' ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
            >
              Media
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
      {route === 'recitations' && (
        <div className="max-w-5xl mx-auto px-4 py-2">
          <div className="flex items-center gap-1.5 text-xs text-stone-400">
            <a href="/admin/media" className="hover:text-stone-600">Media</a>
            <span>/</span>
            <span className="text-stone-600">Verse Recitations</span>
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
        {route === 'media' && <AdminMedia />}
        {route === 'recitations' && <VerseRecitations />}
      </div>
    </div>
  );
}
