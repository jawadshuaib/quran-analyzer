import { useState, useEffect } from 'react';
import { isLoggedIn, verifyToken, clearToken } from '../../api/admin';
import AdminLogin from './AdminLogin';
import AdminSettings from './AdminSettings';

export default function AdminPage() {
  const [authed, setAuthed] = useState(false);
  const [checking, setChecking] = useState(true);
  const [username, setUsername] = useState('');

  const isSettingsPath = /^\/admin\/settings\/?$/.test(window.location.pathname);

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
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <a href="/" className="text-sm font-serif font-medium text-stone-800 hover:text-stone-600">
              al-nuqta
            </a>
            <span className="text-stone-300">|</span>
            <a
              href="/admin"
              className={`text-sm ${!isSettingsPath ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
            >
              Dashboard
            </a>
            <a
              href="/admin/settings"
              className={`text-sm ${isSettingsPath ? 'font-semibold text-stone-800' : 'text-stone-500 hover:text-stone-700'}`}
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

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        {isSettingsPath ? (
          <AdminSettings />
        ) : (
          <div>
            <h1 className="text-xl font-semibold text-stone-800 mb-2">Admin Dashboard</h1>
            <p className="text-sm text-stone-500">Welcome back, {username}.</p>
          </div>
        )}
      </div>
    </div>
  );
}
