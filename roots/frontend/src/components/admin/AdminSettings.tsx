import { useState, useEffect } from 'react';
import { changePassword, getVoices, addVoice, deleteVoice, getPreferences, savePreferences } from '../../api/admin';
import type { Voice } from '../../api/admin';

export default function AdminSettings() {
  return (
    <div className="space-y-10">
      <ChangePasswordSection />
      <hr className="border-stone-200" />
      <ClaudeApiSection />
      <hr className="border-stone-200" />
      <ElevenLabsSection />
      <hr className="border-stone-200" />
      <OllamaSection />
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Change Password                                                   */
/* ------------------------------------------------------------------ */

function ChangePasswordSection() {
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
    if (newPw !== confirmPw) { setError('New passwords do not match'); return; }
    if (newPw.length < 8) { setError('New password must be at least 8 characters'); return; }

    setLoading(true);
    try {
      await changePassword(currentPw, newPw);
      setSuccess('Password changed successfully');
      setCurrentPw(''); setNewPw(''); setConfirmPw('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password');
    } finally { setLoading(false); }
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-stone-800 mb-4">Change Password</h2>
      <form onSubmit={handleSubmit} className="max-w-md space-y-4">
        {error && <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">{error}</div>}
        {success && <div className="text-sm text-green-700 bg-green-50 border border-green-200 rounded-lg px-3 py-2">{success}</div>}
        <InputField id="current-pw" label="Current password" type="password" value={currentPw} onChange={setCurrentPw} autoComplete="current-password" />
        <InputField id="new-pw" label="New password" type="password" value={newPw} onChange={setNewPw} autoComplete="new-password" minLength={8} />
        <InputField id="confirm-pw" label="Confirm new password" type="password" value={confirmPw} onChange={setConfirmPw} autoComplete="new-password" minLength={8} />
        <button type="submit" disabled={loading} className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 transition-colors cursor-pointer">
          {loading ? 'Changing...' : 'Change password'}
        </button>
      </form>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Claude API Configuration                                          */
/* ------------------------------------------------------------------ */

function ClaudeApiSection() {
  const [apiKey, setApiKey] = useState('');
  const [masked, setMasked] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    getPreferences().then((prefs) => {
      if (prefs.claude_api_key) setApiKey(prefs.claude_api_key);
    });
  }, []);

  async function handleSave() {
    setSaving(true);
    setMsg('');
    try {
      await savePreferences({ claude_api_key: apiKey });
      setMsg('Saved');
      setTimeout(() => setMsg(''), 2000);
    } catch {
      setMsg('Failed to save');
    } finally { setSaving(false); }
  }

  const displayKey = masked && apiKey.length > 4
    ? '\u2022'.repeat(apiKey.length - 4) + apiKey.slice(-4)
    : apiKey;

  return (
    <div>
      <h2 className="text-lg font-semibold text-stone-800 mb-1">Claude API</h2>
      <p className="text-sm text-stone-500 mb-4">Used for verse suggestions and AI features</p>

      <div className="max-w-md">
        <label className="block text-sm font-medium text-stone-700 mb-1">API Key</label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={masked ? displayKey : apiKey}
              onChange={(e) => { setApiKey(e.target.value); setMasked(false); }}
              onFocus={() => setMasked(false)}
              className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
              placeholder="sk-ant-..."
            />
          </div>
          <button
            type="button"
            onClick={() => setMasked(!masked)}
            className="px-2 text-xs text-stone-400 hover:text-stone-600 cursor-pointer"
          >
            {masked ? 'Show' : 'Hide'}
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-2 rounded-lg bg-stone-800 text-white text-sm hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
          >
            {saving ? '...' : 'Save'}
          </button>
        </div>
        {msg && <p className="text-xs text-stone-500 mt-1">{msg}</p>}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  ElevenLabs Configuration                                          */
/* ------------------------------------------------------------------ */

function ElevenLabsSection() {
  const [apiKey, setApiKey] = useState('');
  const [apiKeyMasked, setApiKeyMasked] = useState(true);
  const [apiKeySaving, setApiKeySaving] = useState(false);
  const [apiKeyMsg, setApiKeyMsg] = useState('');

  const [voices, setVoices] = useState<Voice[]>([]);
  const [newName, setNewName] = useState('');
  const [newVoiceId, setNewVoiceId] = useState('');
  const [voiceError, setVoiceError] = useState('');
  const [addingVoice, setAddingVoice] = useState(false);

  useEffect(() => {
    getPreferences().then((prefs) => {
      if (prefs.elevenlabs_api_key) setApiKey(prefs.elevenlabs_api_key);
    });
    getVoices().then(setVoices);
  }, []);

  async function handleSaveApiKey() {
    setApiKeySaving(true);
    setApiKeyMsg('');
    try {
      await savePreferences({ elevenlabs_api_key: apiKey });
      setApiKeyMsg('Saved');
      setTimeout(() => setApiKeyMsg(''), 2000);
    } catch {
      setApiKeyMsg('Failed to save');
    } finally { setApiKeySaving(false); }
  }

  async function handleAddVoice(e: React.FormEvent) {
    e.preventDefault();
    setVoiceError('');
    if (!newName.trim() || !newVoiceId.trim()) { setVoiceError('Name and Voice ID required'); return; }
    setAddingVoice(true);
    try {
      const voice = await addVoice(newName, newVoiceId);
      setVoices((v) => [...v, voice]);
      setNewName(''); setNewVoiceId('');
    } catch (err) {
      setVoiceError(err instanceof Error ? err.message : 'Failed to add');
    } finally { setAddingVoice(false); }
  }

  async function handleDelete(id: number) {
    try {
      await deleteVoice(id);
      setVoices((v) => v.filter((x) => x.id !== id));
    } catch {
      // ignore
    }
  }

  const displayKey = apiKeyMasked && apiKey.length > 4
    ? '•'.repeat(apiKey.length - 4) + apiKey.slice(-4)
    : apiKey;

  return (
    <div>
      <h2 className="text-lg font-semibold text-stone-800 mb-4">ElevenLabs</h2>

      {/* API Key */}
      <div className="max-w-md mb-6">
        <label className="block text-sm font-medium text-stone-700 mb-1">API Key</label>
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type={apiKeyMasked ? 'text' : 'text'}
              value={apiKeyMasked ? displayKey : apiKey}
              onChange={(e) => { setApiKey(e.target.value); setApiKeyMasked(false); }}
              onFocus={() => setApiKeyMasked(false)}
              className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
              placeholder="sk_..."
            />
          </div>
          <button
            type="button"
            onClick={() => setApiKeyMasked(!apiKeyMasked)}
            className="px-2 text-xs text-stone-400 hover:text-stone-600 cursor-pointer"
          >
            {apiKeyMasked ? 'Show' : 'Hide'}
          </button>
          <button
            onClick={handleSaveApiKey}
            disabled={apiKeySaving}
            className="px-3 py-2 rounded-lg bg-stone-800 text-white text-sm hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
          >
            {apiKeySaving ? '...' : 'Save'}
          </button>
        </div>
        {apiKeyMsg && <p className="text-xs text-stone-500 mt-1">{apiKeyMsg}</p>}
      </div>

      {/* Voices */}
      <h3 className="text-sm font-semibold text-stone-700 mb-3">Voices</h3>

      {voices.length > 0 && (
        <div className="border border-stone-200 rounded-lg overflow-hidden mb-4 max-w-lg">
          <table className="w-full text-sm">
            <thead className="bg-stone-50 text-stone-500 text-xs">
              <tr>
                <th className="text-left px-3 py-2 font-medium">Name</th>
                <th className="text-left px-3 py-2 font-medium">Voice ID</th>
                <th className="px-3 py-2 w-16"></th>
              </tr>
            </thead>
            <tbody>
              {voices.map((v) => (
                <tr key={v.id} className="border-t border-stone-100">
                  <td className="px-3 py-2 text-stone-800">{v.name}</td>
                  <td className="px-3 py-2 text-stone-500 font-mono text-xs">{v.voice_id}</td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => handleDelete(v.id)}
                      className="text-xs text-red-400 hover:text-red-600 cursor-pointer"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <form onSubmit={handleAddVoice} className="flex gap-2 max-w-lg items-end">
        <div className="flex-1">
          <label className="block text-xs text-stone-500 mb-1">Name</label>
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="e.g. Adam"
          />
        </div>
        <div className="flex-1">
          <label className="block text-xs text-stone-500 mb-1">Voice ID</label>
          <input
            type="text"
            value={newVoiceId}
            onChange={(e) => setNewVoiceId(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="e.g. pNInz6obpgDQGcFmaJgB"
          />
        </div>
        <button
          type="submit"
          disabled={addingVoice}
          className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm hover:bg-stone-700 disabled:opacity-50 cursor-pointer whitespace-nowrap"
        >
          {addingVoice ? '...' : 'Add'}
        </button>
      </form>
      {voiceError && <p className="text-xs text-red-500 mt-2">{voiceError}</p>}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Ollama Configuration                                              */
/* ------------------------------------------------------------------ */

function OllamaSection() {
  const [baseUrl, setBaseUrl] = useState('');
  const [model, setModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [masked, setMasked] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    getPreferences().then((prefs) => {
      if (prefs.ollama_base_url) setBaseUrl(prefs.ollama_base_url);
      if (prefs.ollama_model) setModel(prefs.ollama_model);
      if (prefs.ollama_api_key) setApiKey(prefs.ollama_api_key);
    });
  }, []);

  async function handleSave() {
    setSaving(true);
    setMsg('');
    try {
      await savePreferences({
        ollama_base_url: baseUrl,
        ollama_model: model,
        ollama_api_key: apiKey,
      });
      setMsg('Saved');
      setTimeout(() => setMsg(''), 2000);
    } catch {
      setMsg('Failed to save');
    } finally { setSaving(false); }
  }

  const displayKey = masked && apiKey.length > 4
    ? '\u2022'.repeat(apiKey.length - 4) + apiKey.slice(-4)
    : apiKey;

  return (
    <div>
      <h2 className="text-lg font-semibold text-stone-800 mb-1">Ollama</h2>
      <p className="text-sm text-stone-500 mb-4">Used for generating YouTube titles and descriptions after pipeline videos</p>

      <div className="max-w-md space-y-4">
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Base URL</label>
          <input
            type="text"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="http://localhost:11434"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Model</label>
          <input
            type="text"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="e.g. qwen3:14b"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">API Key <span className="font-normal text-stone-400">(optional, for cloud providers)</span></label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={masked ? displayKey : apiKey}
                onChange={(e) => { setApiKey(e.target.value); setMasked(false); }}
                onFocus={() => setMasked(false)}
                className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
                placeholder="Bearer token (if needed)"
              />
            </div>
            {apiKey && (
              <button
                type="button"
                onClick={() => setMasked(!masked)}
                className="px-2 text-xs text-stone-400 hover:text-stone-600 cursor-pointer"
              >
                {masked ? 'Show' : 'Hide'}
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
          {msg && <span className="text-xs text-stone-500">{msg}</span>}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Shared input field                                                */
/* ------------------------------------------------------------------ */

function InputField({ id, label, type = 'text', value, onChange, autoComplete, minLength }: {
  id: string; label: string; type?: string; value: string;
  onChange: (v: string) => void; autoComplete?: string; minLength?: number;
}) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-stone-700 mb-1">{label}</label>
      <input
        id={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400 focus:border-stone-400"
        autoComplete={autoComplete}
        required
        minLength={minLength}
      />
    </div>
  );
}
