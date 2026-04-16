import { useState } from 'react';
import { changePassword } from '../../api/admin';

export default function AdminSettings() {
  const [currentPw, setCurrentPw] = useState('');
  const [newPw, setNewPw] = useState('');
  const [confirmPw, setConfirmPw] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (newPw !== confirmPw) {
      setError('New passwords do not match');
      return;
    }
    if (newPw.length < 8) {
      setError('New password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      await changePassword(currentPw, newPw);
      setSuccess('Password changed successfully');
      setCurrentPw('');
      setNewPw('');
      setConfirmPw('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-stone-800 mb-4">Change Password</h2>

      <form onSubmit={handleSubmit} className="max-w-md space-y-4">
        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
        {success && (
          <div className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">
            {success}
          </div>
        )}

        <div>
          <label htmlFor="current-pw" className="block text-sm font-medium text-stone-700 mb-1">
            Current password
          </label>
          <input
            id="current-pw"
            type="password"
            value={currentPw}
            onChange={(e) => setCurrentPw(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm
                       focus:outline-none focus:ring-2 focus:ring-stone-400 focus:border-stone-400"
            autoComplete="current-password"
            required
          />
        </div>

        <div>
          <label htmlFor="new-pw" className="block text-sm font-medium text-stone-700 mb-1">
            New password
          </label>
          <input
            id="new-pw"
            type="password"
            value={newPw}
            onChange={(e) => setNewPw(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm
                       focus:outline-none focus:ring-2 focus:ring-stone-400 focus:border-stone-400"
            autoComplete="new-password"
            required
            minLength={8}
          />
        </div>

        <div>
          <label htmlFor="confirm-pw" className="block text-sm font-medium text-stone-700 mb-1">
            Confirm new password
          </label>
          <input
            id="confirm-pw"
            type="password"
            value={confirmPw}
            onChange={(e) => setConfirmPw(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm
                       focus:outline-none focus:ring-2 focus:ring-stone-400 focus:border-stone-400"
            autoComplete="new-password"
            required
            minLength={8}
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium
                     hover:bg-stone-700 disabled:opacity-50 transition-colors cursor-pointer"
        >
          {loading ? 'Changing...' : 'Change password'}
        </button>
      </form>
    </div>
  );
}
