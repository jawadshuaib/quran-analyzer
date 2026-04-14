import { useState, useEffect } from 'react';
import { useSEO } from '../hooks/useSEO';
import {
  getApiKey,
  setApiKey,
  removeApiKey,
  getModel,
  setModel,
  AVAILABLE_MODELS,
} from '../utils/assistant-storage';

export default function SettingsPage() {
  const [key, setKey] = useState('');
  const [saved, setSaved] = useState(false);
  const [selectedModel, setSelectedModel] = useState(getModel());
  const hasKey = !!getApiKey();

  useSEO({
    title: 'Settings',
    description: 'Configure your al-nuqta experience. Set up "Ask the Quran" with your own API key to get answers grounded in the Quran\'s text.',
    path: '/settings',
    noindex: true,
  });

  useEffect(() => {
    const existing = getApiKey();
    if (existing) {
      // Show masked version
      setKey(existing.slice(0, 10) + '...' + existing.slice(-4));
    }
  }, []);

  function handleSave() {
    // Don't save the masked version
    if (key && !key.includes('...')) {
      setApiKey(key);
    }
    setModel(selectedModel);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  function handleRemove() {
    removeApiKey();
    setKey('');
    setSaved(false);
  }

  return (
    <div className="mx-auto w-full max-w-2xl px-4 py-10">
      <div className="text-center mb-10">
        <p className="text-xs text-ink-muted tracking-[0.08em] uppercase mb-3.5">Settings</p>
        <h1 className="font-serif text-2xl sm:text-[34px] font-medium tracking-tight leading-tight text-ink mb-2">
          Configure your experience
        </h1>
        <p className="text-sm sm:text-[15px] text-ink-secondary leading-relaxed">
          Personalize how al-nuqta works for you.
        </p>
      </div>

      {/* Intro */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 mb-6">
        <h2 className="text-lg font-semibold text-stone-800 mb-1">Ask the Quran</h2>
        <p className="text-sm text-stone-500 mb-3">
          "Ask the Quran" lets you ask questions in plain language and get answers
          grounded in the Quran's own text &mdash; with verse references, root word
          analysis, and cross-references drawn from the corpus. It appears as a
          floating button on every verse page.
        </p>
        <p className="text-sm text-stone-500 mb-4">
          To power the responses, it uses Claude (by Anthropic) behind the scenes.
          You'll need your own API key &mdash; it stays stored in your browser and is
          never sent to our servers.
        </p>
      </section>

      {/* API Key Section */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 mb-6">
        <h2 className="text-lg font-semibold text-stone-800 mb-1">API Key</h2>
        <p className="text-sm text-stone-500 mb-4">
          Your key is stored locally in your browser. We never see or transmit it.
        </p>

        <div className="rounded-lg bg-stone-50 border border-stone-200 p-4 mb-4">
          <h3 className="text-sm font-medium text-stone-700 mb-2">How to get a key:</h3>
          <ol className="text-sm text-stone-600 space-y-1.5 list-decimal list-inside">
            <li>
              Go to{' '}
              <a
                href="https://console.anthropic.com/settings/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-800 underline"
              >
                console.anthropic.com/settings/keys
              </a>
            </li>
            <li>Sign up or log in to your Anthropic account</li>
            <li>Click "Create Key" and copy the key that starts with <code className="text-xs bg-stone-200 px-1 rounded">sk-ant-</code></li>
            <li>Paste it below</li>
          </ol>
          <p className="text-xs text-stone-400 mt-3">
            Cost: Typically $0.01–0.05 per question depending on context size and model.
          </p>
        </div>

        <label className="block text-sm font-medium text-stone-700 mb-1">API Key</label>
        <div className="flex gap-2">
          <input
            type="password"
            value={key}
            onChange={(e) => {
              setKey(e.target.value);
              setSaved(false);
            }}
            onFocus={() => {
              // Clear masked value on focus so user can paste new key
              if (key.includes('...')) setKey('');
            }}
            placeholder="sk-ant-..."
            className="flex-1 rounded-lg border border-stone-300 px-3 py-2 text-sm
                       focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 outline-none"
          />
          {hasKey && (
            <button
              onClick={handleRemove}
              className="px-3 py-2 rounded-lg border border-red-200 text-red-600
                         hover:bg-red-50 text-sm transition-colors"
            >
              Remove
            </button>
          )}
        </div>
      </section>

      {/* Model Selection */}
      <section className="rounded-xl border border-stone-200 bg-white p-5 mb-6">
        <h2 className="text-lg font-semibold text-stone-800 mb-1">Model</h2>
        <p className="text-sm text-stone-500 mb-4">
          Choose which model powers "Ask the Quran." Faster models cost less per question;
          larger models give more nuanced answers.
        </p>
        <div className="space-y-2">
          {AVAILABLE_MODELS.map((m) => (
            <label
              key={m.id}
              className={`flex items-center gap-3 rounded-lg border p-3 cursor-pointer transition-colors ${
                selectedModel === m.id
                  ? 'border-indigo-300 bg-indigo-50'
                  : 'border-stone-200 hover:border-stone-300'
              }`}
            >
              <input
                type="radio"
                name="model"
                value={m.id}
                checked={selectedModel === m.id}
                onChange={() => {
                  setSelectedModel(m.id);
                  setSaved(false);
                }}
                className="text-indigo-600"
              />
              <span className="text-sm text-stone-700">{m.label}</span>
            </label>
          ))}
        </div>
      </section>

      {/* Save Button */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSave}
          className="px-5 py-2.5 rounded-lg bg-indigo-600 text-white font-medium text-sm
                     hover:bg-indigo-700 transition-colors"
        >
          Save Settings
        </button>
        {saved && (
          <span className="text-sm text-emerald-600 font-medium">
            Settings saved
          </span>
        )}
      </div>
    </div>
  );
}
