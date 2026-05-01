import { useState, useEffect } from 'react';
import { changePassword, getVoices, addVoice, deleteVoice, getPreferences, savePreferences, getTiktokStatus, startTiktokAuth, disconnectTiktok } from '../../api/admin';
import type { Voice, TiktokStatus } from '../../api/admin';
import { useConfirm } from './shared/useConfirm';

// Ready-to-paste prompt for a browser-driving Claude agent. The agent opens
// the admin settings + OAuth Playground, configures the Playground with the
// admin's credentials, walks through the consent flow, and pastes the
// resulting refresh token back into the admin — leaving only the Google
// sign-in step for the human to complete.
const YOUTUBE_AGENT_PROMPT = `I need to refresh my YouTube OAuth refresh token for al-nuqta.com. Please drive the browser through the entire process without pausing unless something goes wrong.

My Google account for sign-in: jawad.php@gmail.com
Target YouTube channel (brand account): Al-Nuqta

1. Open https://al-nuqta.com/admin/settings in a new tab.
   - If the admin page loads directly (I'm already logged in): continue.
   - If an admin login form appears: PAUSE and tell me — I'll enter my password.

   Scroll to the "YouTube" section. Read the "Client ID" and "Client Secret" values from the input fields. The Client Secret is masked by default — click the "Show" button next to it to reveal the full value. If either field is empty, PAUSE and tell me — the one-time Google Cloud Console setup hasn't been done yet and this flow can't proceed until those credentials are in place.

2. Open https://developers.google.com/oauthplayground in another tab.

3. Click the gear/settings icon (⚙️) in the top-right of the Playground. In the settings panel:
   - Check "Use your own OAuth credentials"
   - Paste the Client ID into "OAuth Client ID"
   - Paste the Client Secret into "OAuth Client secret"
   - Set "Force prompt" to "Consent" (it may already say "Consent Screen" — that's the same thing, leave it)
   - Close the gear panel

4. In the left pane, either find "YouTube Data API v3" and check
   https://www.googleapis.com/auth/youtube.upload, OR paste that scope URL directly into the "Input your own scopes" box at the bottom — either works.

5. Click "Authorize APIs". Google will walk you through TWO selectors in sequence. Read carefully — getting either wrong publishes uploads to the wrong channel.

   Selector 1 — Google account picker ("Choose an account, to continue to Al-Nuqta"):
   - I have multiple Google accounts signed in. Pick jawad.php@gmail.com specifically, even if another account appears first or is marked default.
   - If jawad.php@gmail.com isn't listed or a password prompt appears: PAUSE and tell me.

   Selector 2 — Brand account picker ("Choose your account or a brand account, to continue to Al-Nuqta"):
   - This screen lists my personal account plus YouTube brand accounts (e.g. "Minute M4th", "Al-Nuqta").
   - Pick the Al-Nuqta brand account (labeled "Youtube"). Do NOT pick the personal "Jawad Shuaib / jawad.php@gmail.com" entry — that uploads to my personal channel, not the Al-Nuqta channel.
   - If "Al-Nuqta" isn't in the list: PAUSE and tell me.

   "Google hasn't verified this app" warning (may appear after Selector 2):
   - Click "Continue" / the small "Advanced → Go to Al-Nuqta (unsafe)" link. This is my own unverified OAuth app, not a phishing risk.

   Consent screen ("Al-Nuqta wants access to your Google Account"):
   - Verify the account shown under the title is Al-Nuqta (not "Jawad Shuaib / jawad.php@gmail.com"). If it's wrong, go back and re-pick at Selector 2.
   - Click "Continue" / "Allow".

6. After consent, Google redirects back to the Playground and "Step 2: Exchange authorization code for tokens" becomes active. Click that button.

7. In the JSON response on the right, locate the "refresh_token" value. Copy the string value (not the key, not the access_token). If the response doesn't include a refresh_token field at all, the flow failed — go back to step 3, verify "Force prompt" is set to "Consent", and retry. (Missing-but-consent-was-set usually means Google deduplicated because consent was already granted recently; forcing consent again fixes it.)

8. Return to the al-nuqta admin settings tab. In the YouTube section, paste the refresh token into the "Refresh Token" field (replacing whatever's there). Click "Save".

9. Confirm success: a green "Connected" pill should appear next to the "YouTube" heading, and the age badge next to Refresh Token should show "Saved less than an hour ago". Report back that it's done.

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

/** Settings are grouped into categories so the page is scannable.
 *  Each section anchors via id so the side nav can scroll to it. */
const SETTINGS_GROUPS: Array<{
  title: string;
  blurb?: string;
  sections: Array<{ id: string; label: string; render: () => React.ReactElement }>;
}> = [
  {
    title: 'Account',
    sections: [
      { id: 'change-password', label: 'Change password', render: () => <ChangePasswordSection /> },
    ],
  },
  {
    title: 'Site & analytics',
    blurb: 'How visitors discover, track, and install al-nuqta.',
    sections: [
      { id: 'google-analytics', label: 'Google Analytics', render: () => <GoogleAnalyticsSection /> },
      { id: 'chrome-extension', label: 'Chrome extension', render: () => <ChromeExtensionSection /> },
    ],
  },
  {
    title: 'AI providers',
    blurb: 'API keys for translation, voice, and reasoning models.',
    sections: [
      { id: 'claude-api', label: 'Claude API', render: () => <ClaudeApiSection /> },
      { id: 'ollama', label: 'Ollama', render: () => <OllamaSection /> },
      { id: 'elevenlabs', label: 'ElevenLabs', render: () => <ElevenLabsSection /> },
    ],
  },
  {
    title: 'Social distribution',
    blurb: 'OAuth credentials for video uploads.',
    sections: [
      { id: 'youtube', label: 'YouTube', render: () => <YoutubeSection /> },
      { id: 'youtube-playlists', label: 'YouTube Playlists', render: () => <YoutubePlaylistsSection /> },
      { id: 'tiktok', label: 'TikTok', render: () => <TiktokSection /> },
    ],
  },
];

export default function AdminSettings() {
  return (
    <div className="flex flex-col lg:flex-row gap-8">
      {/* Sticky side nav — collapses to a horizontal pill bar on mobile. */}
      <aside className="lg:w-56 lg:flex-shrink-0">
        <nav className="lg:sticky lg:top-6 space-y-5">
          {SETTINGS_GROUPS.map((g) => (
            <div key={g.title}>
              <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-stone-400 mb-1.5">
                {g.title}
              </p>
              <ul className="space-y-0.5">
                {g.sections.map((s) => (
                  <li key={s.id}>
                    <a
                      href={`#${s.id}`}
                      className="block rounded-md px-2 py-1 text-sm text-stone-600 hover:bg-stone-100 hover:text-stone-900 transition-colors"
                    >
                      {s.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>
      </aside>

      <div className="flex-1 min-w-0 space-y-12">
        {SETTINGS_GROUPS.map((g) => (
          <section key={g.title} className="space-y-8">
            <div>
              <h1 className="text-xl font-semibold text-stone-800">{g.title}</h1>
              {g.blurb && <p className="text-sm text-stone-500 mt-0.5">{g.blurb}</p>}
            </div>
            {g.sections.map((s, i) => (
              <div key={s.id} id={s.id} className="scroll-mt-6">
                {i > 0 && <hr className="border-stone-200 mb-8" />}
                {s.render()}
              </div>
            ))}
          </section>
        ))}
      </div>
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
/*  YouTube Playlist auto-add                                         */
/* ------------------------------------------------------------------ */

function YoutubePlaylistsSection() {
  // One playlist key per pipeline series. Default applies to the
  // existing recitation pipelines (English + Arabic). Educational
  // sub-types each get their own so word-origins shorts land on the
  // word-origins playlist, etc.
  const PLAYLIST_KEYS: Array<{
    key: string;
    label: string;
    blurb: string;
  }> = [
    {
      key: 'youtube_playlist_default',
      label: 'Recitation pipelines (default)',
      blurb: 'Used by the English & Arabic pipelines when they auto-upload to YouTube.',
    },
    {
      key: 'youtube_playlist_word_origins',
      label: 'Educational · Word Origins',
      blurb: 'Auto-adds Word Origins shorts to this playlist after upload.',
    },
    {
      key: 'youtube_playlist_translation_hides',
      label: 'Educational · What Translators Hide',
      blurb: '',
    },
    {
      key: 'youtube_playlist_grammar_insights',
      label: 'Educational · Grammar Insights',
      blurb: '',
    },
  ];

  const [vals, setVals] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    getPreferences().then((prefs) => {
      const next: Record<string, string> = {};
      for (const p of PLAYLIST_KEYS) next[p.key] = prefs[p.key] || '';
      setVals(next);
    });
    // Effect runs once on mount; PLAYLIST_KEYS is module-stable.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleSave() {
    setSaving(true);
    setMsg('');
    try {
      const patch: Record<string, string> = {};
      for (const p of PLAYLIST_KEYS) patch[p.key] = (vals[p.key] || '').trim();
      await savePreferences(patch);
      setMsg('Saved');
      setTimeout(() => setMsg(''), 2000);
    } catch {
      setMsg('Failed to save');
    } finally { setSaving(false); }
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-stone-800 mb-1">YouTube Playlists</h2>
      <p className="text-sm text-stone-500 mb-4">
        Optional. When set, every successful upload from the matching pipeline is
        added to the playlist via the YouTube Data API. Failure to add to
        the playlist doesn't fail the upload — the video still publishes.
      </p>

      <details className="mb-4 max-w-2xl text-xs text-stone-600">
        <summary className="cursor-pointer text-stone-500 hover:text-stone-700">
          How to find a playlist ID
        </summary>
        <ol className="mt-2 pl-5 list-decimal space-y-1 leading-relaxed">
          <li>Open the playlist on YouTube (you must be the owner).</li>
          <li>The URL looks like <code className="px-1 bg-stone-100 rounded">…/playlist?list=PLxxxxxxxxxxxxxxxx</code>.</li>
          <li>Copy the part after <code className="px-1 bg-stone-100 rounded">list=</code> — that's the ID. It usually starts with <code className="px-1 bg-stone-100 rounded">PL</code> (~24-34 chars).</li>
          <li>Paste it into the corresponding row below and Save.</li>
        </ol>
      </details>

      <div className="max-w-md space-y-4">
        {PLAYLIST_KEYS.map((p) => (
          <div key={p.key}>
            <label className="block text-sm font-medium text-stone-700 mb-1">{p.label}</label>
            <input
              type="text"
              value={vals[p.key] || ''}
              onChange={(e) => setVals((v) => ({ ...v, [p.key]: e.target.value }))}
              className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
              placeholder="PLxxxxxxxxxxxxxxxx"
              spellCheck={false}
              autoCorrect="off"
              autoCapitalize="off"
            />
            {p.blurb && <p className="mt-1 text-[11px] text-stone-400">{p.blurb}</p>}
          </div>
        ))}

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
/*  TikTok Configuration                                              */
/* ------------------------------------------------------------------ */

function TiktokSection() {
  const [clientKey, setClientKey] = useState('');
  const [clientSecret, setClientSecret] = useState('');
  const [secretMasked, setSecretMasked] = useState(true);
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');
  const [status, setStatus] = useState<TiktokStatus | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  async function refreshAll() {
    const [prefs, st] = await Promise.all([getPreferences(), getTiktokStatus()]);
    if (prefs.tiktok_client_key) setClientKey(prefs.tiktok_client_key);
    if (prefs.tiktok_client_secret) setClientSecret(prefs.tiktok_client_secret);
    setStatus(st);
  }

  useEffect(() => {
    refreshAll().catch(() => {});

    // Pick up callback result from URL (?tiktok_connected=1 / ?tiktok_error=...)
    const params = new URLSearchParams(window.location.search);
    if (params.get('tiktok_connected')) {
      setMsg('TikTok connected');
      setTimeout(() => setMsg(''), 3000);
      const url = new URL(window.location.href);
      url.searchParams.delete('tiktok_connected');
      window.history.replaceState({}, '', url.toString());
    }
    const err = params.get('tiktok_error');
    if (err) {
      setMsg(`TikTok connect failed: ${err}`);
      const url = new URL(window.location.href);
      url.searchParams.delete('tiktok_error');
      window.history.replaceState({}, '', url.toString());
    }
  }, []);

  async function handleSave() {
    setSaving(true);
    setMsg('');
    try {
      await savePreferences({
        tiktok_client_key: clientKey,
        tiktok_client_secret: clientSecret,
      });
      setMsg('Saved');
      await refreshAll();
      setTimeout(() => setMsg(''), 2000);
    } catch {
      setMsg('Failed to save');
    } finally { setSaving(false); }
  }

  async function handleConnect() {
    setConnecting(true);
    setMsg('');
    try {
      const { authorize_url } = await startTiktokAuth();
      window.location.href = authorize_url;
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Failed to start auth');
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    setDisconnecting(true);
    setMsg('');
    try {
      await disconnectTiktok();
      await refreshAll();
      setMsg('Disconnected');
      setTimeout(() => setMsg(''), 2000);
    } catch (e) {
      setMsg(e instanceof Error ? e.message : 'Failed to disconnect');
    } finally { setDisconnecting(false); }
  }

  const maskedSecret = secretMasked && clientSecret.length > 4
    ? '\u2022'.repeat(clientSecret.length - 4) + clientSecret.slice(-4)
    : clientSecret;

  const connected = !!status?.connected;
  const canConnect = !!(clientKey && clientSecret) && !connected;

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-lg font-semibold text-stone-800">TikTok</h2>
        {connected && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 text-green-700">
            Connected
          </span>
        )}
        {status && !connected && (clientKey || clientSecret) && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-100 text-amber-700">
            Not authorized
          </span>
        )}
      </div>
      <p className="text-sm text-stone-500 mb-4">
        Used for uploading generated videos to TikTok via the Content Posting API. Sandbox /
        unapproved apps post as <code className="px-1 bg-stone-100 rounded text-xs">SELF_ONLY</code>{' '}
        (visible only to you) until TikTok approves the scope.
      </p>

      <details className="mb-4 max-w-2xl text-xs text-stone-600">
        <summary className="cursor-pointer text-stone-500 hover:text-stone-700">
          One-time setup (TikTok Developer Portal)
        </summary>
        <ol className="mt-2 pl-5 list-decimal space-y-1 leading-relaxed">
          <li>Go to <a href="https://developers.tiktok.com/" target="_blank" rel="noopener noreferrer" className="underline">developers.tiktok.com</a> → your app.</li>
          <li>Under <b>Login Kit</b> and <b>Content Posting API</b>, add these scopes: <code className="px-1 bg-stone-100 rounded">user.info.basic</code>, <code className="px-1 bg-stone-100 rounded">video.upload</code>, <code className="px-1 bg-stone-100 rounded">video.publish</code>.</li>
          <li>Set the redirect URI to exactly <code className="px-1 bg-stone-100 rounded">{status?.redirect_uri || 'https://al-nuqta.com/admin/tiktok/callback'}</code>.</li>
          <li>Add your TikTok username as a <b>sandbox tester</b> so you can OAuth pre-approval.</li>
          <li>Copy the Client Key and Client Secret into the fields below, click Save, then click Connect.</li>
        </ol>
      </details>

      <div className="max-w-md space-y-4">
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Client Key</label>
          <input
            type="text"
            value={clientKey}
            onChange={(e) => setClientKey(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="aw..."
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
              placeholder="Secret from TikTok developer portal"
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

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>

          {!connected && (
            <button
              onClick={handleConnect}
              disabled={!canConnect || connecting}
              title={!canConnect ? 'Save Client Key + Secret first' : 'Redirects to TikTok to authorize'}
              className="px-4 py-2 rounded-lg border border-stone-800 text-stone-800 text-sm font-medium hover:bg-stone-800 hover:text-white disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
            >
              {connecting ? 'Redirecting…' : 'Connect TikTok'}
            </button>
          )}

          {connected && (
            <button
              onClick={handleDisconnect}
              disabled={disconnecting}
              className="px-4 py-2 rounded-lg border border-red-300 text-red-700 text-sm font-medium hover:bg-red-50 disabled:opacity-50 cursor-pointer"
            >
              {disconnecting ? 'Disconnecting…' : 'Disconnect'}
            </button>
          )}

          {msg && <span className="text-xs text-stone-500">{msg}</span>}
        </div>

        {connected && status && (
          <div className="mt-2 rounded-md border border-stone-200 bg-stone-50 p-3 text-xs text-stone-600 space-y-1">
            <div>
              <span className="text-stone-400">Open ID:</span>{' '}
              <code className="text-stone-700">{status.open_id || '(not provided)'}</code>
            </div>
            {status.connected_at && (
              <div>
                <span className="text-stone-400">Connected:</span>{' '}
                {new Date(status.connected_at).toLocaleString()}
              </div>
            )}
            <div>
              <span className="text-stone-400">Scopes:</span>{' '}
              <code className="text-stone-700">{status.scopes}</code>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Google Analytics Configuration                                    */
/* ------------------------------------------------------------------ */

function GoogleAnalyticsSection() {
  const [gaId, setGaId] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    getPreferences().then((prefs) => {
      if (prefs.google_analytics_id) setGaId(prefs.google_analytics_id);
    });
  }, []);

  const looksValid = /^G-[A-Z0-9]{4,20}$/.test(gaId.trim());
  const isEmpty = !gaId.trim();
  const showFormatHint = !isEmpty && !looksValid;

  async function handleSave() {
    setSaving(true);
    setMsg('');
    try {
      await savePreferences({ google_analytics_id: gaId.trim() });
      setMsg(gaId.trim() ? 'Saved — tracking is now live on public pages.' : 'Cleared.');
      setTimeout(() => setMsg(''), 3500);
    } catch {
      setMsg('Failed to save');
    } finally { setSaving(false); }
  }

  return (
    <div>
      <div className="flex items-center gap-2 mb-1">
        <h2 className="text-lg font-semibold text-stone-800">Google Analytics</h2>
        {looksValid && (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-green-100 text-green-700">
            Tracking
          </span>
        )}
      </div>
      <p className="text-sm text-stone-500 mb-4">
        Paste your GA4 Measurement ID (looks like <code className="px-1 bg-stone-100 rounded text-xs">G-XXXXXXXXXX</code>)
        and we'll inject the gtag snippet on every public page. Admin pages
        (<code className="px-1 bg-stone-100 rounded text-xs">/admin/*</code>) are excluded so your own activity doesn't pollute the data.
      </p>

      <details className="mb-4 max-w-2xl text-xs text-stone-600">
        <summary className="cursor-pointer text-stone-500 hover:text-stone-700">
          How to find your Measurement ID
        </summary>
        <ol className="mt-2 pl-5 list-decimal space-y-1 leading-relaxed">
          <li>Go to <a href="https://analytics.google.com/" target="_blank" rel="noopener noreferrer" className="underline">analytics.google.com</a> → your al-nuqta property.</li>
          <li>Open <b>Admin</b> (gear icon, bottom-left) → <b>Data Streams</b> → click your web stream.</li>
          <li>Copy the <b>Measurement ID</b> shown in the top-right of the stream details (starts with <code className="px-1 bg-stone-100 rounded">G-</code>).</li>
          <li>Paste it below and click Save. Visit any public page and verify in GA4 <b>Reports → Realtime</b>.</li>
        </ol>
      </details>

      <div className="max-w-md">
        <label className="block text-sm font-medium text-stone-700 mb-1">Measurement ID</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={gaId}
            onChange={(e) => setGaId(e.target.value)}
            className="flex-1 px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="G-XXXXXXXXXX"
            spellCheck={false}
            autoCorrect="off"
            autoCapitalize="off"
          />
          <button
            onClick={handleSave}
            disabled={saving || (!isEmpty && !looksValid)}
            title={showFormatHint ? 'Format must be G- followed by 4-20 letters/digits' : undefined}
            className="px-4 py-2 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 disabled:opacity-50 cursor-pointer"
          >
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
        {showFormatHint && (
          <p className="mt-1 text-xs text-amber-600">
            That doesn't look like a GA4 ID. Expected format: <code className="px-1 bg-amber-50 rounded">G-XXXXXXXXXX</code>.
          </p>
        )}
        {msg && <p className="mt-1 text-xs text-stone-500">{msg}</p>}
        <p className="mt-2 text-[11px] text-stone-400">
          Leave blank to disable tracking entirely.
        </p>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Chrome Extension Configuration                                    */
/* ------------------------------------------------------------------ */

function ChromeExtensionSection() {
  const [extId, setExtId] = useState('');
  const [storeUrl, setStoreUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState('');

  useEffect(() => {
    getPreferences().then((prefs) => {
      if (prefs.chrome_extension_id) setExtId(prefs.chrome_extension_id);
      if (prefs.chrome_extension_store_url) setStoreUrl(prefs.chrome_extension_store_url);
    });
  }, []);

  async function handleSave() {
    setSaving(true);
    setMsg('');
    try {
      await savePreferences({
        chrome_extension_id: extId.trim(),
        chrome_extension_store_url: storeUrl.trim(),
      });
      setMsg('Saved');
      setTimeout(() => setMsg(''), 2000);
    } catch {
      setMsg('Failed to save');
    } finally { setSaving(false); }
  }

  // Auto-derive the store URL when the ID changes and the URL field is
  // either empty or still pointed at the old pattern. Admin can override.
  function handleIdChange(next: string) {
    setExtId(next);
    const trimmed = next.trim();
    if (trimmed && (!storeUrl.trim() || /\/detail\/quran-research-tool\//.test(storeUrl))) {
      setStoreUrl(`https://chromewebstore.google.com/detail/quran-research-tool/${trimmed}`);
    }
  }

  return (
    <div>
      <h2 className="text-lg font-semibold text-stone-800 mb-1">Chrome Extension</h2>
      <p className="text-sm text-stone-500 mb-4">
        Controls the "Get Chrome Extension" banner and the installed-check ping. Update the ID
        here whenever a Chrome Web Store resubmission issues a new one — no code deploy needed.
      </p>

      <div className="max-w-xl space-y-4">
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Extension ID</label>
          <input
            type="text"
            value={extId}
            onChange={(e) => handleIdChange(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="jbalbedmilokgefgknhieckdidnlikdm"
          />
          <div className="mt-1.5 text-[11px] text-stone-500 leading-relaxed space-y-1">
            <div>
              The 32-character string at the <b>end</b> of your Chrome Web Store URL:
            </div>
            <div className="font-mono text-stone-400 break-all">
              https://chromewebstore.google.com/detail/quran-research-tool/
              <span className="text-stone-700 font-semibold underline decoration-stone-300 underline-offset-2">
                jbalbedmilokgefgknhieckdidnlikdm
              </span>
            </div>
            <div className="text-stone-400">
              Also shown on <code className="px-1 bg-stone-100 rounded">chrome://extensions</code> once "Developer mode" (top right) is enabled.
            </div>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-stone-700 mb-1">Store URL</label>
          <input
            type="text"
            value={storeUrl}
            onChange={(e) => setStoreUrl(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-stone-400"
            placeholder="https://chromewebstore.google.com/detail/quran-research-tool/…"
          />
          <p className="mt-1 text-[11px] text-stone-400">
            Where the "Get Chrome Extension" banner links. Auto-derives from the ID; override if the slug differs.
          </p>
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
