import { useState, useEffect } from 'react';
import { changePassword, getVoices, addVoice, deleteVoice, getPreferences, savePreferences } from '../../api/admin';
import type { Voice } from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

// Ready-to-paste prompt for a browser-driving Claude agent. The agent opens
// the admin settings + OAuth Playground, configures the Playground with the
// admin's credentials, walks through the consent flow, and pastes the
// resulting refresh token back into the admin — leaving only the Google
// sign-in step for the human to complete.
const YOUTUBE_AGENT_PROMPT = `I need to refresh my YouTube OAuth refresh token for al-nuqta.com. Please drive the browser through the entire process without pausing unless something goes wrong.

My Google account for YouTube: jawad.php@gmail.com

1. Open https://al-nuqta.com/admin/settings in a new tab.
   - If the admin page loads directly (I'm already logged in): continue.
   - If an admin login form appears: PAUSE and tell me — I'll enter my password.
   Scroll to the "YouTube" section. Read the "Client ID" and "Client Secret" values from the input fields. The Client Secret is masked by default — click the "Show" button next to it to reveal the full value. If either field is empty, PAUSE and tell me — the one-time Google Cloud Console setup hasn't been done yet and this flow can't proceed until those credentials are in place.

2. Open https://developers.google.com/oauthplayground in another tab.

3. Click the gear/settings icon (⚙️) in the top-right of the Playground. In the settings panel:
   - Check "Use your own OAuth credentials"
   - Paste the Client ID into "OAuth Client ID"
   - Paste the Client Secret into "OAuth Client secret"
   - Set "Force prompt" to "Consent"
   - Close the gear panel

4. In the left pane, locate "YouTube Data API v3" and expand it. Check the scope:
   https://www.googleapis.com/auth/youtube.upload

5. Click "Authorize APIs". Google will show an account selector or consent screen.
   - If jawad.php@gmail.com is listed as an already-signed-in account: click it, then on the consent screen click "Continue" / "Allow". Keep going without pausing.
   - If only jawad.php@gmail.com is signed in and Google goes straight to the consent screen: click "Continue" / "Allow" and keep going.
   - If jawad.php@gmail.com is NOT in the signed-in list, or Google asks for a password: PAUSE and tell me — I'll handle sign-in and then ask you to continue.

6. After consent, Google redirects back to the Playground and "Step 2: Exchange authorization code for tokens" becomes active. Click that button.

7. In the JSON response, locate the "refresh_token" value. Copy the string value (not the key, not the access_token). Note: if the response doesn't include a refresh_token, the flow failed — go back to step 3 and verify "Force prompt" is set to "Consent".

8. Return to the al-nuqta admin settings tab. In the YouTube section, paste the refresh token into the "Refresh Token" field. Click "Save".

9. Confirm success: a green "Connected" pill should appear at the top of the YouTube section, and the age badge next to Refresh Token should show "Saved less than an hour ago". Report back that it's done.

If any step fails, tell me exactly where it failed and show me the error message so I can fix it.`;

function computeTokenAge(savedAtIso: string | null): {
  days: number;
  severity: 'ok' | 'warn' | 'danger';
  label: string;
} | null {
  if (!savedAtIso) return null;
  const saved = new Date(savedAtIso).getTime();
  if (isNaN(saved)) return null;
  const days = (Date.now() - saved) / (1000 * 60 * 60 * 24);
  // Testing-mode refresh tokens expire after 7 days. Warn at 5, danger at 7.
  let severity: 'ok' | 'warn' | 'danger' = 'ok';
  let label = `Saved ${formatAge(days)} ago`;
  if (days >= 7) {
    severity = 'danger';
    label = `Likely expired (${formatAge(days)} old)`;
  } else if (days >= 5) {
    severity = 'warn';
    label = `Expires soon (${formatAge(days)} old)`;
  }
  return { days, severity, label };
}

function formatAge(days: number): string {
  if (days < 1) {
    const hours = Math.max(0, Math.round(days * 24));
    return hours <= 1 ? 'less than an hour' : `${hours} hours`;
  }
  const d = Math.round(days);
  return d === 1 ? '1 day' : `${d} days`;
}

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
      <hr className="border-stone-200" />
      <YoutubeSection />
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
  const { confirm, dialog: confirmDialog } = useConfirm();

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
    const voice = voices.find((v) => v.id === id);
    const ok = await confirm({
      title: 'Delete voice?',
      message: voice
        ? `Remove "${voice.name}" from your saved voices? You can add it again later using the same Voice ID.`
        : 'Remove this voice from your saved voices?',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
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
      {confirmDialog}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Ollama Configuration                                              */
/* ------------------------------------------------------------------ */

function OllamaSection() {
  const [baseUrl, setBaseUrl] = useState('');
  const [model, setModel] = useState('');
  const [metadataModel, setMetadataModel] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [masked, setMasked] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    getPreferences().then((prefs) => {
      if (prefs.ollama_base_url) setBaseUrl(prefs.ollama_base_url);
      if (prefs.ollama_model) setModel(prefs.ollama_model);
      if (prefs.ollama_metadata_model) setMetadataModel(prefs.ollama_metadata_model);
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
        ollama_metadata_model: metadataModel,
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
          <p className="mt-1 text-xs text-stone-400">Default model used for all Ollama tasks.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">
            Metadata Model <span className="font-normal text-stone-400">(optional)</span>
          </label>
          <input
            type="text"
            value={metadataModel}
            onChange={(e) => setMetadataModel(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="e.g. qwen3.5:397b-cloud"
          />
          <p className="mt-1 text-xs text-stone-400">
            Override just for YouTube title/description/tags generation. Leave blank to use
            the default model above. Recommended: <code className="px-1 bg-stone-100 rounded">qwen3.5:397b-cloud</code> —
            its reasoning produces noticeably sharper descriptions than smaller models.
          </p>
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
/*  YouTube Configuration                                             */
/* ------------------------------------------------------------------ */

function YoutubeSection() {
  const [channelId, setChannelId] = useState('');
  const [clientId, setClientId] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [refreshToken, setRefreshToken] = useState('');
  const [secretMasked, setSecretMasked] = useState(true);
  const [refreshMasked, setRefreshMasked] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const [refreshSavedAt, setRefreshSavedAt] = useState<string | null>(null);
  const [promptCopied, setPromptCopied] = useState(false);

  useEffect(() => {
    getPreferences().then((prefs) => {
      if (prefs.youtube_channel_id) setChannelId(prefs.youtube_channel_id);
      if (prefs.youtube_client_id) setClientId(prefs.youtube_client_id);
      if (prefs.youtube_client_secret) setClientSecret(prefs.youtube_client_secret);
      if (prefs.youtube_refresh_token) setRefreshToken(prefs.youtube_refresh_token);
      if (prefs.youtube_refresh_token_saved_at) setRefreshSavedAt(prefs.youtube_refresh_token_saved_at);
    });
  }, []);

  async function handleSave() {
    setSaving(true);
    setMsg('');
    try {
      await savePreferences({
        youtube_channel_id: channelId,
        youtube_client_id: clientId,
        youtube_client_secret: clientSecret,
        youtube_refresh_token: refreshToken,
      });
      setMsg('Saved');
      // The backend stamps youtube_refresh_token_saved_at only if the token
      // actually changed. Re-pull prefs so the age display updates.
      getPreferences().then((p) => {
        if (p.youtube_refresh_token_saved_at) {
          setRefreshSavedAt(p.youtube_refresh_token_saved_at);
        }
      });
      setTimeout(() => setMsg(''), 2000);
    } catch {
      setMsg('Failed to save');
    } finally { setSaving(false); }
  }

  function copyAgentPrompt() {
    navigator.clipboard.writeText(YOUTUBE_AGENT_PROMPT).then(() => {
      setPromptCopied(true);
      setTimeout(() => setPromptCopied(false), 2500);
    });
  }

  // Compute token age for the visible badge next to the refresh field
  const tokenAge = computeTokenAge(refreshSavedAt);

  const maskedSecret = secretMasked && clientSecret.length > 4
    ? '\u2022'.repeat(clientSecret.length - 4) + clientSecret.slice(-4)
    : clientSecret;
  const maskedRefresh = refreshMasked && refreshToken.length > 4
    ? '\u2022'.repeat(refreshToken.length - 4) + refreshToken.slice(-4)
    : refreshToken;

  const connected = !!(clientId && clientSecret && refreshToken);

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-lg font-semibold text-stone-800">YouTube</h2>
        {connected && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 text-green-700">
            Connected
          </span>
        )}
      </div>
      <p className="text-sm text-stone-500 mb-4">
        Used for uploading generated videos to YouTube. Admin-only — one set of credentials for your channel.
      </p>

      <div className="mb-4 max-w-2xl flex items-start gap-3 rounded-lg border border-stone-200 bg-stone-50 p-3">
        <div className="flex-1 text-xs text-stone-600 leading-relaxed">
          <div className="font-semibold text-stone-700 mb-0.5">Have a browser-driving Claude agent do this for you</div>
          <p className="text-stone-500">
            Copies a ready-made prompt to your clipboard. Paste it into Claude
            (with a browser) and it will drive the OAuth Playground end-to-end.
            You only have to sign in to Google when it asks.
          </p>
        </div>
        <button
          type="button"
          onClick={copyAgentPrompt}
          className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-2 rounded-md border border-stone-300 bg-white text-xs font-medium text-stone-700 hover:bg-stone-50 cursor-pointer"
          title="Copy the browser-agent prompt"
        >
          {promptCopied ? (
            <>
              <CheckIcon /> Copied
            </>
          ) : (
            <>
              <ClipboardIcon /> Copy AI prompt
            </>
          )}
        </button>
      </div>

      <details className="mb-4 max-w-2xl text-xs text-stone-600">
        <summary className="cursor-pointer text-stone-500 hover:text-stone-700">
          Or do it manually (6 steps, ~5 minutes)
        </summary>
        <ol className="mt-2 pl-5 list-decimal space-y-1 leading-relaxed">
          <li>Go to <a href="https://console.cloud.google.com/" target="_blank" rel="noopener noreferrer" className="underline">Google Cloud Console</a>, create a project.</li>
          <li>Enable the <b>YouTube Data API v3</b> for that project.</li>
          <li>Create OAuth credentials (type: <b>Web application</b>). Add
            <code className="mx-1 px-1 bg-stone-100 rounded">https://developers.google.com/oauthplayground</code>
            as an authorized redirect URI. Copy the Client ID + Client Secret here.</li>
          <li>Open <a href="https://developers.google.com/oauthplayground" target="_blank" rel="noopener noreferrer" className="underline">OAuth 2.0 Playground</a> ⚙️ → check "Use your own OAuth credentials", paste the ID/Secret.</li>
          <li>In the scope list add <code className="mx-1 px-1 bg-stone-100 rounded">https://www.googleapis.com/auth/youtube.upload</code>, click Authorize APIs, sign in with the account that owns the channel.</li>
          <li>Click "Exchange authorization code for tokens", copy the <b>Refresh token</b> here.</li>
        </ol>
      </details>

      <div className="max-w-md space-y-4">
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Channel ID</label>
          <input
            type="text"
            value={channelId}
            onChange={(e) => setChannelId(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="UCxxxxxxxxxxxxxxxxxxxxxx"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Client ID</label>
          <input
            type="text"
            value={clientId}
            onChange={(e) => setClientId(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="xxxxxxxx.apps.googleusercontent.com"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Client Secret</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={secretMasked ? maskedSecret : clientSecret}
              onChange={(e) => { setClientSecret(e.target.value); setSecretMasked(false); }}
              onFocus={() => setSecretMasked(false)}
              className="flex-1 px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
              placeholder="GOCSPX-..."
            />
            {clientSecret && (
              <button
                type="button"
                onClick={() => setSecretMasked(!secretMasked)}
                className="px-2 text-xs text-stone-400 hover:text-stone-600 cursor-pointer"
              >
                {secretMasked ? 'Show' : 'Hide'}
              </button>
            )}
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-sm font-medium text-stone-700">Refresh Token</label>
            {tokenAge && (
              <span className={`text-[10px] font-medium px-2 py-0.5 rounded-full ${
                tokenAge.severity === 'danger'
                  ? 'bg-red-100 text-red-700'
                  : tokenAge.severity === 'warn'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-stone-100 text-stone-500'
              }`}>
                {tokenAge.label}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <input
              type="text"
              value={refreshMasked ? maskedRefresh : refreshToken}
              onChange={(e) => { setRefreshToken(e.target.value); setRefreshMasked(false); }}
              onFocus={() => setRefreshMasked(false)}
              className="flex-1 px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
              placeholder="1//0g..."
            />
            {refreshToken && (
              <button
                type="button"
                onClick={() => setRefreshMasked(!refreshMasked)}
                className="px-2 text-xs text-stone-400 hover:text-stone-600 cursor-pointer"
              >
                {refreshMasked ? 'Show' : 'Hide'}
              </button>
            )}
          </div>
          {tokenAge && tokenAge.severity !== 'ok' && (
            <p className={`mt-1 text-xs ${tokenAge.severity === 'danger' ? 'text-red-600' : 'text-amber-600'}`}>
              Testing-mode OAuth refresh tokens expire after 7 days. Click "Copy AI prompt" above to refresh it.
            </p>
          )}
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

function ClipboardIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
      <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"></path>
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"></polyline>
    </svg>
  );
}

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
