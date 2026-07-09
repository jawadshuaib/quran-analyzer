const BASE = '/api/admin';
const TOKEN_KEY = 'admin_token';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn(): boolean {
  return !!getToken();
}

async function authFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const isFormData = options.body instanceof FormData;
  const headers: Record<string, string> = {
    // Don't set Content-Type for FormData — browser sets multipart boundary automatically
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers as Record<string, string> || {}),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(url, { ...options, headers });
  if (res.status === 401) {
    clearToken();
    window.location.href = '/admin';
    throw new Error('Session expired');
  }
  return res;
}

export async function login(
  username: string,
  password: string,
  remember = false,
): Promise<{ token: string; username: string }> {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, remember }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Login failed');
  setToken(data.token);
  return data;
}

export async function verifyToken(): Promise<{ username: string }> {
  const res = await authFetch(`${BASE}/me`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Invalid session');
  return data;
}

// --------------- Voices ---------------

export interface Voice {
  id: number;
  name: string;
  voice_id: string;
  created_at: string;
}

export async function getVoices(): Promise<Voice[]> {
  const res = await authFetch(`${BASE}/voices`);
  return res.json();
}

export async function addVoice(name: string, voiceId: string): Promise<Voice> {
  const res = await authFetch(`${BASE}/voices`, {
    method: 'POST',
    body: JSON.stringify({ name, voice_id: voiceId }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to add voice');
  return data;
}

export async function deleteVoice(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/voices/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete voice');
  }
}

// --------------- Preferences ---------------

export async function getPreferences(): Promise<Record<string, string>> {
  const res = await authFetch(`${BASE}/preferences`);
  return res.json();
}

export async function savePreferences(prefs: Record<string, string>): Promise<void> {
  const res = await authFetch(`${BASE}/preferences`, {
    method: 'PUT',
    body: JSON.stringify(prefs),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to save preferences');
  }
}

// --------------- Vocabulary Studio ---------------

export interface VocabSurveyState {
  root_buckwalter: string;
  root_arabic: string;
  canonical_english: string | null;
  reasoning: string | null;
  counter_examples: Array<{ ref: string; usage?: string; how_canonical_fits: string }>;
  translation_note: string | null;
  leave_untranslated: number;
  confidence: number | null;
  hard_cases: Array<{ ref: string; arabic_word: string; transliteration: string; reason: string }>;
  occurrence_count: number;
  surveyor_model: string | null;
  surveyor_run_at: string | null;
}

export interface VocabRevisions {
  hard_cases_total: number;
  translations_revised: number;
  verse_translations_revised: number;
  verse_translations_total: number;
  grammar_notes_revised: number;
  grammar_notes_total: number;
  word_meanings_revised: number;
  word_meanings_total: number;
  total_word_occurrences: number;
}

export interface VocabReviseChunkResult {
  ok: true;
  processed: number;
  revised: number;
  errors: number;
  remaining: number;
  elapsed_ms: number;
  samples: Array<{ ref: string; before: string; after: string; hard_case?: boolean }>;
  errors_detail?: Array<{ ref: string; message: string; hard_case?: boolean }>;
  revisions: VocabRevisions;
}

export interface VocabStudioState {
  root_buckwalter: string;
  root_arabic: string;
  occurrences: Array<{
    chapter: number;
    verse: number;
    word_pos: number;
    arabic_word: string;
    pos: string | null;
    translation: string;
  }>;
  occurrence_count: number;
  survey: VocabSurveyState | null;
  revisions: VocabRevisions;
}

export async function getVocabStudio(rootBw: string): Promise<VocabStudioState> {
  const res = await authFetch(`${BASE}/vocab/${encodeURIComponent(rootBw)}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load vocab studio');
  return data;
}

export async function runVocabSurvey(
  rootBw: string,
  opts: { force?: boolean; extra_constraint?: string; model?: string } = {},
): Promise<{ ok: true; elapsed_ms: number; model: string; state: VocabSurveyState }> {
  const res = await authFetch(`${BASE}/vocab/${encodeURIComponent(rootBw)}/survey`, {
    method: 'POST',
    body: JSON.stringify(opts),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Survey failed');
  return data;
}

export async function saveVocabEdits(
  rootBw: string,
  edits: Partial<VocabSurveyState>,
): Promise<{ ok: true; state: VocabSurveyState }> {
  const res = await authFetch(`${BASE}/vocab/${encodeURIComponent(rootBw)}`, {
    method: 'PUT',
    body: JSON.stringify(edits),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Save failed');
  return data;
}

export async function applyVocabTransliteration(
  rootBw: string,
): Promise<{ ok: true; results: Array<{ ref: string; outcome: string }>; revisions: VocabRevisions }> {
  const res = await authFetch(`${BASE}/vocab/${encodeURIComponent(rootBw)}/apply-transliteration`, {
    method: 'POST',
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Apply failed');
  return data;
}

export async function revertVocabTransliteration(
  rootBw: string,
  chapter: number,
  verse: number,
): Promise<{ ok: true; revisions: VocabRevisions }> {
  const res = await authFetch(
    `${BASE}/vocab/${encodeURIComponent(rootBw)}/revert-transliteration/${chapter}/${verse}`,
    { method: 'POST' },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Revert failed');
  return data;
}

// ---- Phase 2 actions: regenerate translation note + bulk revise word
// meanings + bulk revise grammar notes (each with revert). Word meanings
// and grammar notes are chunked — caller polls until remaining == 0.

export async function regenerateTranslationNote(
  rootBw: string,
): Promise<{ ok: true; elapsed_ms: number; model: string; translation_note: string | null; state: VocabStudioState['survey'] }> {
  const res = await authFetch(
    `${BASE}/vocab/${encodeURIComponent(rootBw)}/regenerate-translation-note`,
    { method: 'POST', body: JSON.stringify({}) },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Regeneration failed');
  return data;
}

export async function reviseVocabWordMeanings(
  rootBw: string,
  opts: { limit?: number; force?: boolean } = {},
): Promise<VocabReviseChunkResult> {
  const res = await authFetch(
    `${BASE}/vocab/${encodeURIComponent(rootBw)}/revise-word-meanings`,
    { method: 'POST', body: JSON.stringify(opts) },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Word-meanings revision failed');
  return data;
}

export async function revertVocabWordMeanings(
  rootBw: string,
): Promise<{ ok: true; reverted: number; revisions: VocabRevisions }> {
  const res = await authFetch(
    `${BASE}/vocab/${encodeURIComponent(rootBw)}/revert-word-meanings`,
    { method: 'POST' },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Word-meanings revert failed');
  return data;
}

export async function reviseVocabGrammarNotes(
  rootBw: string,
  opts: { limit?: number; force?: boolean } = {},
): Promise<VocabReviseChunkResult> {
  const res = await authFetch(
    `${BASE}/vocab/${encodeURIComponent(rootBw)}/revise-grammar-notes`,
    { method: 'POST', body: JSON.stringify(opts) },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Grammar-notes revision failed');
  return data;
}

export async function revertVocabGrammarNotes(
  rootBw: string,
): Promise<{ ok: true; reverted: number; revisions: VocabRevisions }> {
  const res = await authFetch(
    `${BASE}/vocab/${encodeURIComponent(rootBw)}/revert-grammar-notes`,
    { method: 'POST' },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Grammar-notes revert failed');
  return data;
}

export async function reviseVocabVerseTranslations(
  rootBw: string,
  opts: { limit?: number; force?: boolean } = {},
): Promise<VocabReviseChunkResult> {
  const res = await authFetch(
    `${BASE}/vocab/${encodeURIComponent(rootBw)}/revise-verse-translations`,
    { method: 'POST', body: JSON.stringify(opts) },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Verse-translation revision failed');
  return data;
}

export async function revertVocabVerseTranslations(
  rootBw: string,
): Promise<{ ok: true; reverted: number; revisions: VocabRevisions }> {
  const res = await authFetch(
    `${BASE}/vocab/${encodeURIComponent(rootBw)}/revert-verse-translations`,
    { method: 'POST' },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Verse-translation revert failed');
  return data;
}

/** Search roots — public endpoint, no auth needed but admin uses it. */
export interface RootSearchHit {
  root_buckwalter: string;
  root_arabic: string;
  occurrences?: number;
  meaning?: string;
}

export async function searchAdminRoots(query: string): Promise<RootSearchHit[]> {
  const res = await fetch(`/api/roots/search?q=${encodeURIComponent(query)}&limit=15`);
  if (!res.ok) return [];
  return res.json();
}

// --------------- Proper Nouns ---------------

export interface ProperNounCandidate {
  id: number;
  chapter: number;
  verse: number;
  word_pos: number;
  arabic_word: string | null;
  root_buckwalter: string | null;
  lemma_buckwalter: string | null;
  surface_translation: string | null;
  candidate_type: string | null;

  is_indefinite: number;
  root_quran_frequency: number | null;
  has_compound_marker: string | null;

  qwen_verdict: string | null;
  qwen_confidence: number | null;
  qwen_reasoning: string | null;
  gptoss_verdict: string | null;
  gptoss_confidence: number | null;
  gptoss_reasoning: string | null;
  stage1_run_at: string | null;

  sonnet_verdict: string | null;
  sonnet_alternatives: Array<{ translation: string; rationale: string }>;
  sonnet_reasoning: string | null;
  sonnet_supporting_refs: string[];
  stage2_run_at: string | null;

  operator_action: string | null;
  operator_translation: string | null;
  operator_notes: string | null;
  reviewed_at: string | null;

  applied_at: string | null;
  applied_to_verses: Array<{ chapter: number; verse: number; word_pos: number; original_translation: string | null; original_source: string | null }>;
}

export interface ProperNounStats {
  total: number;
  stage1_done: number;
  stage2_done: number;
  literal: number;
  name: number;
  ambiguous: number;
  approved: number;
  rejected: number;
  applied: number;
}

export async function listProperNouns(params: {
  status?: string;
  verdict?: string;
  type?: string;
  root?: string;
  limit?: number;
  offset?: number;
  order?: string;
} = {}): Promise<{ candidates: ProperNounCandidate[]; total_matched: number; limit: number; offset: number; stats: ProperNounStats }> {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== '') q.set(k, String(v));
  }
  const res = await authFetch(`${BASE}/proper-nouns?${q.toString()}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to list candidates');
  return data;
}

export async function detectProperNouns(): Promise<{
  ok: true;
  inserted: number;
  skipped_existing: number;
  skipped_no_translation: number;
  by_type: Record<string, number>;
  summary: ProperNounStats;
}> {
  const res = await authFetch(`${BASE}/proper-nouns/detect`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Stage 0 detection failed');
  return data;
}

export async function clearProperNouns(force = false): Promise<{
  ok: true;
  cleared: number;
  summary: ProperNounStats;
}> {
  const res = await authFetch(`${BASE}/proper-nouns/clear`, {
    method: 'POST',
    body: JSON.stringify({ force }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Clear failed');
  return data;
}

export async function runProperNounsOllama(opts: {
  limit?: number;
  models?: string;
  refresh?: boolean;
} = {}): Promise<{
  ok: true;
  processed: number;
  qwen_ok: number;
  qwen_err: number;
  gptoss_ok: number;
  gptoss_err: number;
  remaining: number;
  elapsed_ms: number;
  summary: ProperNounStats;
}> {
  const res = await authFetch(`${BASE}/proper-nouns/run-ollama`, {
    method: 'POST',
    body: JSON.stringify(opts),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Stage 1 (Ollama) failed');
  return data;
}

export async function runProperNounsSonnet(opts: {
  limit?: number;
  refresh?: boolean;
  only_disagreement?: boolean;
} = {}): Promise<{
  ok: true;
  processed: number;
  adjudicated: number;
  errors: number;
  errors_detail?: Array<{ ref: string; message: string }>;
  remaining: number;
  elapsed_ms: number;
  summary: ProperNounStats;
}> {
  const res = await authFetch(`${BASE}/proper-nouns/run-sonnet`, {
    method: 'POST',
    body: JSON.stringify(opts),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Stage 2 (Sonnet) failed');
  return data;
}

export async function reviewProperNoun(
  id: number,
  body: { action: 'approved' | 'rejected' | 'edited'; translation?: string | null; notes?: string | null },
): Promise<{ ok: true; candidate: ProperNounCandidate }> {
  const res = await authFetch(`${BASE}/proper-nouns/${id}`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Review failed');
  return data;
}

export async function applyProperNoun(
  id: number,
): Promise<{ ok: true; candidate: ProperNounCandidate; summary: ProperNounStats }> {
  const res = await authFetch(`${BASE}/proper-nouns/${id}/apply`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Apply failed');
  return data;
}

export async function revertProperNoun(
  id: number,
): Promise<{ ok: true; reverted: number; candidate: ProperNounCandidate; summary: ProperNounStats }> {
  const res = await authFetch(`${BASE}/proper-nouns/${id}/revert`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Revert failed');
  return data;
}

// --------------- Reciters ---------------

export interface Reciter {
  id: number;
  reciter_name: string;
  style: string | null;
  translated_name: { name: string; language_name: string };
}

export async function getReciters(): Promise<Reciter[]> {
  const res = await authFetch(`${BASE}/reciters`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch reciters');
  return data;
}

// --------------- Recitation Preview ---------------

export interface PreviewVerse {
  surah: number;
  ayah: number;
  surah_name: string;
  arabic_text: string;
  translation: string;
  audio_url: string;
}

export async function getRecitationPreview(params: {
  reciter_id: number;
  from_surah: number;
  from_ayah: number;
  to_surah: number;
  to_ayah: number;
}): Promise<PreviewVerse[]> {
  const res = await authFetch(`${BASE}/recitation-preview`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load preview');
  return data.verses;
}

// --------------- TTS ---------------

export async function generateTTS(
  text: string, voiceId: string, chapter: number, verse: number,
): Promise<string> {
  const res = await authFetch(`${BASE}/tts`, {
    method: 'POST',
    body: JSON.stringify({ text, voice_id: voiceId, chapter, verse }),
  });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'TTS failed');
  }
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

// --------------- TTS Cache ---------------

export interface TTSCacheEntry {
  id: number;
  chapter: number;
  verse: number;
  voice_id: string;
  voice_name: string;
  surah_name: string;
  translation_text: string;
  filename: string;
  created_at: string;
}

export async function getTTSCache(): Promise<TTSCacheEntry[]> {
  const res = await authFetch(`${BASE}/tts-cache`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch TTS cache');
  return data;
}

export async function deleteTTSCache(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/tts-cache/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete');
  }
}

export function ttsCacheAudioUrl(id: number): string {
  return `${BASE}/tts-cache/${id}/audio`;
}

export interface StaleTTSEntry {
  id: number;
  chapter: number;
  verse: number;
  surah_name: string;
  cached_text: string;
  latest_text: string;
}

export async function getStaleTTSCache(): Promise<StaleTTSEntry[]> {
  const res = await authFetch(`${BASE}/tts-cache/stale`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to check stale entries');
  return data;
}

// --------------- Resources ---------------

export interface Resource {
  id: number;
  original_name: string;
  filename: string;
  file_size: number;
  duration_seconds: number | null;
  width: number | null;
  height: number | null;
  description?: string;
  /** Comma-separated lowercase list. Filters background-video pools
   *  per pipeline series (e.g. 'word-origins'). Stored canonical;
   *  the input field accepts free-form whitespace. */
  tags?: string;
  created_at: string;
}

export async function getResources(): Promise<Resource[]> {
  const res = await authFetch(`${BASE}/resources`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch resources');
  return data;
}

export async function uploadResource(file: File): Promise<Resource> {
  const formData = new FormData();
  formData.append('video', file);
  const res = await authFetch(`${BASE}/resources`, {
    method: 'POST',
    body: formData,
  });
  const text = await res.text();
  let data: Record<string, unknown>;
  try {
    data = JSON.parse(text);
  } catch {
    // Flask itself allows 500MB, but a 413 here usually means the
    // host's reverse proxy (nginx/Caddy/Cloudflare) is enforcing its
    // default ~1MB limit before the request reaches Flask. The fix is
    // host-side, not in this app. Surface that explicitly so the
    // operator doesn't waste time tweaking app-side config.
    throw new Error(
      res.status === 413
        ? 'Upload rejected by reverse proxy (HTTP 413). The Flask app allows 500MB, '
          + 'but the host\'s nginx/Caddy is capping uploads. Raise '
          + 'client_max_body_size on the host (see DEPLOY.md).'
        : `Upload failed (${res.status})`,
    );
  }
  if (!res.ok) throw new Error((data.error as string) || 'Upload failed');
  return data as unknown as Resource;
}

export async function deleteResource(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/resources/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete resource');
  }
}

export async function updateResource(
  id: number,
  patch: { description?: string; tags?: string },
): Promise<Resource> {
  const res = await authFetch(`${BASE}/resources/${id}`, {
    method: 'PUT',
    body: JSON.stringify(patch),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to update resource');
  return data;
}

export function resourceThumbnailUrl(id: number): string {
  return `${BASE}/resources/${id}/thumbnail`;
}

// --------------- Background Music ---------------

export interface MusicTrack {
  id: number;
  original_name: string;
  filename: string;
  file_size: number;
  duration_seconds: number | null;
  description?: string;
  created_at: string;
}

export async function getMusicTracks(): Promise<MusicTrack[]> {
  const res = await authFetch(`${BASE}/music`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch music');
  return data;
}

export async function uploadMusicTrack(file: File): Promise<MusicTrack> {
  const formData = new FormData();
  formData.append('audio', file);
  const res = await authFetch(`${BASE}/music`, {
    method: 'POST',
    body: formData,
  });
  const text = await res.text();
  let data: Record<string, unknown>;
  try {
    data = JSON.parse(text);
  } catch {
    throw new Error(
      res.status === 413
        ? 'Upload rejected by reverse proxy (HTTP 413). Raise '
          + 'client_max_body_size on the host (see DEPLOY.md).'
        : `Upload failed (${res.status})`,
    );
  }
  if (!res.ok) throw new Error((data.error as string) || 'Upload failed');
  return data as unknown as MusicTrack;
}

export async function deleteMusicTrack(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/music/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete');
  }
}

export async function updateMusicTrack(id: number, description: string): Promise<MusicTrack> {
  const res = await authFetch(`${BASE}/music/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ description }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to update music track');
  return data;
}

export function musicAudioUrl(id: number): string {
  return `${BASE}/music/${id}/audio`;
}

// --------------- Video Generation ---------------

export interface GeneratedVideo {
  id: number;
  title: string;
  format: string;
  resource_id: number;
  reciter_id: number;
  status: string;
  progress: string;
  filename: string | null;
  file_size: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export async function startVideoGeneration(params: {
  title: string;
  format: 'short' | 'regular';
  resource_id: number;
  reciter_id: number;
  verses: Array<{ chapter: number; verse: number; tts_cache_id: number }>;
  english_only?: boolean;
  arabic_only?: boolean;
  music_id?: number;
}): Promise<{ id: number; status: string }> {
  const res = await authFetch(`${BASE}/generate-video`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to start generation');
  return data;
}

export async function getGeneratedVideos(): Promise<GeneratedVideo[]> {
  const res = await authFetch(`${BASE}/generated-videos`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch videos');
  return data;
}

export async function deleteGeneratedVideo(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/generated-videos/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete video');
  }
}

export function generatedVideoDownloadUrl(id: number): string {
  return `${BASE}/generated-videos/${id}/download`;
}

// --------------- Video Description Generation ---------------

export async function generateDescription(
  verses: { chapter: number; verse: number }[],
): Promise<string> {
  const res = await authFetch(`${BASE}/generate-description`, {
    method: 'POST',
    body: JSON.stringify({ verses }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to generate description');
  return data.description;
}

// --------------- Moving Verse Suggestions ---------------

export interface MovingVerseGroup {
  id: number;
  chapter: number;
  verse_start: number;
  verse_end: number;
  surah_name: string;
  emotional_score: number;
  category: string;
  title: string;
  reasoning: string;
  translation_snippet: string;
  remaining_count: number;
}

export async function getMovingVerseSuggestion(
  excludeIds?: number[],
  category?: string,
): Promise<MovingVerseGroup> {
  const body: Record<string, unknown> = {};
  if (excludeIds?.length) body.exclude_ids = excludeIds;
  if (category) body.category = category;
  const res = await authFetch(`${BASE}/moving-verse-suggestions`, {
    method: 'POST',
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch suggestion');
  return data;
}

// --------------- Verse Explanations ---------------

export interface ExplanationSegment {
  type: 'transition' | 'verses' | 'closing';
  text?: string;
  translation?: string;
  chapter?: number;
  ayah_start?: number;
  ayah_end?: number;
  ref?: string;
  tts_filename?: string | null;
}

export interface Explanation {
  id: number;
  title: string;
  segments: ExplanationSegment[];
  status: 'draft' | 'ready';
  created_at: string;
  updated_at: string;
}

export interface ExplanationListItem {
  id: number;
  title: string;
  status: 'draft' | 'ready';
  segment_count: number;
  verse_count: number;
  created_at: string;
  updated_at: string;
}

export interface RelatedVerse {
  chapter: number;
  ayah: number;
  ref: string;
  translation: string;
  similarity_score: number;
  shared_roots: { root_buckwalter: string; root_arabic: string }[];
}

export async function createExplanation(
  title: string,
  verse_groups: { chapter: number; ayah_start: number; ayah_end: number }[],
): Promise<Explanation> {
  const res = await authFetch(`${BASE}/explanations`, {
    method: 'POST',
    body: JSON.stringify({ title, verse_groups }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to create explanation');
  return data;
}

export async function getExplanations(): Promise<ExplanationListItem[]> {
  const res = await authFetch(`${BASE}/explanations`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch explanations');
  return data;
}

export async function getExplanation(id: number): Promise<Explanation> {
  const res = await authFetch(`${BASE}/explanations/${id}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch explanation');
  return data;
}

export async function updateExplanation(
  id: number,
  updates: { title?: string; segments?: ExplanationSegment[] },
): Promise<Explanation> {
  const res = await authFetch(`${BASE}/explanations/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to update explanation');
  return data;
}

export async function deleteExplanation(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/explanations/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete');
  }
}

export async function suggestRelatedVerses(
  chapter: number,
  ayah: number,
): Promise<RelatedVerse[]> {
  const res = await authFetch(`${BASE}/explanation-suggest`, {
    method: 'POST',
    body: JSON.stringify({ chapter, ayah }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to get suggestions');
  return data;
}

export async function generateClosingReflection(
  segments: ExplanationSegment[],
): Promise<string> {
  const res = await authFetch(`${BASE}/explanation-closing`, {
    method: 'POST',
    body: JSON.stringify({ segments }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to generate closing');
  return data.closing_text;
}

export async function generateAllExplanationTTS(
  explanation_id: number,
  voice_id: string,
): Promise<{ generated: number; total: number; status: string }> {
  const res = await authFetch(`${BASE}/explanation-generate-all-tts`, {
    method: 'POST',
    body: JSON.stringify({ explanation_id, voice_id }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to generate TTS');
  return data;
}

export async function startExplanationVideoGeneration(params: {
  explanation_id: number;
  format: 'short' | 'regular';
  resource_id: number;
  music_id?: number;
}): Promise<{ id: number; status: string }> {
  const res = await authFetch(`${BASE}/generate-explanation-video`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to start generation');
  return data;
}

// --------------- Pipelines ---------------

export interface Pipeline {
  id: number;
  name: string;
  language: 'english' | 'arabic' | string;
  resource_id: number;
  voice_id: string;
  reciter_id: number | null;
  show_bands: number;
  random_resource: number;
  music_id: number | null;
  video_count?: number;
  created_at: string;
  updated_at: string;
}

export interface PipelineVideo {
  id: number;
  pipeline_id: number;
  verse_data: string;
  status: string;
  progress: string;
  filename: string | null;
  file_size: number | null;
  error_message: string | null;
  youtube_title: string | null;
  youtube_description: string | null;
  youtube_tags: string | null;           // JSON string of tag array
  youtube_video_id: string | null;
  triggered_by: 'manual' | 'scheduler' | string;
  uploaded_to_youtube: number;
  uploaded_to_tiktok?: number;
  tiktok_video_id?: string | null;
  tiktok_caption?: string | null;
  created_at: string;
  completed_at: string | null;
}

export async function createPipeline(params: {
  name: string;
  language?: 'english' | 'arabic';
  resource_id: number;
  voice_id?: string;
  reciter_id?: number | null;
  show_bands: boolean;
  random_resource?: boolean;
  music_id?: number | null;
}): Promise<Pipeline> {
  const res = await authFetch(`${BASE}/pipelines`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to create pipeline');
  return data;
}

export async function getPipelines(): Promise<Pipeline[]> {
  const res = await authFetch(`${BASE}/pipelines`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch pipelines');
  return data;
}

export async function getPipeline(id: number): Promise<Pipeline> {
  const res = await authFetch(`${BASE}/pipelines/${id}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch pipeline');
  return data;
}

export async function updatePipeline(id: number, params: {
  name?: string;
  resource_id?: number;
  voice_id?: string;
  reciter_id?: number | null;
  show_bands?: boolean;
  random_resource?: boolean;
  music_id?: number | null;
}): Promise<Pipeline> {
  const res = await authFetch(`${BASE}/pipelines/${id}`, {
    method: 'PUT',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to update pipeline');
  return data;
}

export async function deletePipeline(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/pipelines/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete pipeline');
  }
}

export interface ManualGenerateParams {
  chapter?: number;
  ayah_start?: number;
  ayah_end?: number;
  youtube_title?: string;
  youtube_description?: string;
}

export async function generatePipelineVideo(
  pipelineId: number,
  manual?: ManualGenerateParams,
): Promise<{ id: number; status: string }> {
  const res = await authFetch(`${BASE}/pipelines/${pipelineId}/generate`, {
    method: 'POST',
    body: JSON.stringify(manual || {}),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to start generation');
  return data;
}

export async function getPipelineVideos(pipelineId?: number): Promise<PipelineVideo[]> {
  const url = pipelineId ? `${BASE}/pipeline-videos?pipeline_id=${pipelineId}` : `${BASE}/pipeline-videos`;
  const res = await authFetch(url);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch pipeline videos');
  return data;
}

export async function deletePipelineVideo(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/pipeline-videos/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json();
    throw new Error(data.error || 'Failed to delete');
  }
}

export function pipelineVideoDownloadUrl(id: number): string {
  return `${BASE}/pipeline-videos/${id}/download`;
}

export async function setPipelineVideoUploaded(
  id: number,
  uploaded: boolean,
): Promise<{ id: number; uploaded_to_youtube: boolean }> {
  const res = await authFetch(`${BASE}/pipeline-videos/${id}/uploaded`, {
    method: 'PUT',
    body: JSON.stringify({ uploaded }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to update upload flag');
  return data;
}

export interface YoutubeUploadResult {
  video_id: number;
  youtube_video_id: string;
  youtube_url: string;
  privacy: 'public' | 'unlisted' | 'private';
}

export async function uploadPipelineVideoToYouTube(
  id: number,
  params: { title: string; description: string; tags: string[]; privacy?: 'public' | 'unlisted' | 'private' },
): Promise<YoutubeUploadResult> {
  const res = await authFetch(`${BASE}/pipeline-videos/${id}/upload`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'YouTube upload failed');
  return data;
}

/* ---------------- TikTok ---------------- */

export interface TiktokStatus {
  has_client_key: boolean;
  has_client_secret: boolean;
  connected: boolean;
  open_id: string | null;
  connected_at: string | null;
  redirect_uri: string;
  scopes: string;
}

export async function getTiktokStatus(): Promise<TiktokStatus> {
  const res = await authFetch(`${BASE}/tiktok/status`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch TikTok status');
  return data;
}

export async function startTiktokAuth(): Promise<{ authorize_url: string }> {
  const res = await authFetch(`${BASE}/tiktok/auth-start`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to start TikTok auth');
  return data;
}

export async function disconnectTiktok(): Promise<{ ok: true }> {
  const res = await authFetch(`${BASE}/tiktok/disconnect`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to disconnect TikTok');
  return data;
}

export interface TiktokUploadResult {
  ok: true;
  video_id: number;
  tiktok_video_id: string | null;
  publish_id: string;
  privacy_level: 'SELF_ONLY' | 'MUTUAL_FOLLOW_FRIENDS' | 'PUBLIC_TO_EVERYONE';
  note: string;
}

export async function uploadPipelineVideoToTiktok(
  id: number,
  params: { caption: string; privacy_level?: 'SELF_ONLY' | 'MUTUAL_FOLLOW_FRIENDS' | 'PUBLIC_TO_EVERYONE' },
): Promise<TiktokUploadResult> {
  const res = await authFetch(`${BASE}/pipeline-videos/${id}/upload-to-tiktok`, {
    method: 'POST',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'TikTok upload failed');
  return data;
}

export interface RegeneratedMetadata {
  video_id: number;
  title: string;
  description: string;
  tags: string[];
}

// Async regenerate with polling. The backend kicks off a thread and we
// poll every 3 seconds until it's done or errors out. Works even when
// the total wall-time exceeds proxy read timeouts.
export async function regeneratePipelineVideoMetadata(
  id: number,
  opts: { onProgress?: (elapsedSeconds: number) => void; signal?: AbortSignal } = {},
): Promise<RegeneratedMetadata> {
  async function readJsonOrFail(res: Response, fallbackMsg: string) {
    // Some proxies return HTML error pages — detect and surface a useful error
    // instead of letting JSON.parse explode with "Unexpected token '<'".
    const text = await res.text();
    if (!text) {
      throw new Error(res.ok ? 'Empty response from server' : `${fallbackMsg} (HTTP ${res.status})`);
    }
    try {
      return JSON.parse(text);
    } catch {
      if (text.trimStart().startsWith('<')) {
        throw new Error(`${fallbackMsg} (server returned HTML — likely a proxy timeout or server error)`);
      }
      throw new Error(`${fallbackMsg}: ${text.slice(0, 200)}`);
    }
  }

  // Kick off
  const start = Date.now();
  const kickoff = await authFetch(`${BASE}/pipeline-videos/${id}/regenerate-metadata`, {
    method: 'POST',
    signal: opts.signal,
  });
  const kickoffData = await readJsonOrFail(kickoff, 'Failed to start regeneration');
  if (!kickoff.ok) throw new Error(kickoffData.error || 'Failed to start regeneration');

  // Poll
  while (true) {
    if (opts.signal?.aborted) throw new Error('Cancelled');
    await new Promise((r) => setTimeout(r, 3000));
    const statusRes = await authFetch(`${BASE}/pipeline-videos/${id}/regenerate-metadata-status`, {
      signal: opts.signal,
    });
    const data = await readJsonOrFail(statusRes, 'Status poll failed');
    if (!statusRes.ok) throw new Error(data.error || 'Status poll failed');

    opts.onProgress?.(Math.round((Date.now() - start) / 1000));

    if (data.status === 'done') {
      return {
        video_id: id,
        title: data.title || '',
        description: data.description || '',
        tags: Array.isArray(data.tags) ? data.tags : [],
      };
    }
    if (data.status === 'error') {
      throw new Error(data.error || 'Metadata regeneration failed');
    }
    // status === 'running' or 'idle' → keep polling
    // Safety cap at 10 minutes — way longer than any reasonable model call
    if (Date.now() - start > 10 * 60 * 1000) {
      throw new Error('Timed out waiting for metadata regeneration');
    }
  }
}

// --------------- Pipeline scheduler ---------------

export interface PipelineSchedule {
  pipeline_id: number;
  pipeline_name: string;
  pipeline_language: 'english' | 'arabic' | string;
  times: string[];            // ["HH:MM", ...] in server local time
  max_runs_per_day: number;
  enabled: boolean;
  grace_minutes: number;
  updated_at: string | null;
}

export interface PipelineScheduleRun {
  id: number;
  pipeline_id: number;
  pipeline_name: string;
  pipeline_language: string;
  scheduled_time: string;
  fired_at: string;
  video_id: number | null;
  /** YouTube title of the produced video, when the run created one.
   *  NULL for skipped/errored runs that never created a video. */
  video_title: string | null;
  /** Downstream lifecycle status of the produced video (NULL when
   *  the run was skipped). e.g. 'rendered', 'uploaded', 'failed'. */
  video_status: string | null;
  status: 'fired' | 'skipped_cap' | 'skipped_active' | 'skipped_grace' | 'error' | string;
  note: string | null;
}

export async function getPipelineSchedules(): Promise<PipelineSchedule[]> {
  const res = await authFetch(`${BASE}/pipeline-schedules`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch schedules');
  return data;
}

export async function savePipelineSchedule(
  pipeline_id: number,
  params: {
    times: string[];
    max_runs_per_day: number;
    enabled: boolean;
    grace_minutes: number;
  },
): Promise<PipelineSchedule> {
  const res = await authFetch(`${BASE}/pipeline-schedules/${pipeline_id}`, {
    method: 'PUT',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to save schedule');
  return data;
}

export async function getPipelineScheduleRuns(opts: {
  limit?: number;
  pipeline_id?: number;
} = {}): Promise<PipelineScheduleRun[]> {
  const params = new URLSearchParams();
  if (opts.limit) params.set('limit', String(opts.limit));
  if (opts.pipeline_id) params.set('pipeline_id', String(opts.pipeline_id));
  const qs = params.toString();
  const res = await authFetch(`${BASE}/pipeline-schedule-runs${qs ? '?' + qs : ''}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch schedule runs');
  return data;
}

// --------------- YouTube upload scheduler ---------------

export interface YoutubeUploadSchedule {
  enabled: boolean;
  times: string[];
  grace_minutes: number;
  sanity_check_enabled: boolean;
  privacy: 'public' | 'unlisted' | 'private';
  updated_at: string | null;
  /** OAuth circuit-breaker state. open=true means consecutive OAuth
   *  failures crossed the threshold and the upload tick is pausing
   *  all slots until the operator fixes credentials and the breaker
   *  resets (auto on next successful token fetch, or via the manual
   *  reset endpoint). */
  oauth_circuit_breaker?: {
    open: boolean;
    consecutive_failures: number;
    last_failure: string | null;
  };
}

/** Run an OAuth token exchange right now and return the result. Used
 *  by the "Test OAuth" button on the YouTube schedule page. */
export async function testYoutubeOAuth(): Promise<{
  ok: boolean;
  message?: string;
  error?: string;
  access_token_prefix?: string;
}> {
  const res = await authFetch(`${BASE}/youtube-upload-schedule/test-oauth`, {
    method: 'POST',
  });
  return res.json();
}

/** Manually clear the OAuth failure counter without retrying — useful
 *  when the operator just fixed the credentials and wants to resume
 *  the schedule without burning a token-exchange call. */
export async function resetYoutubeOAuthCircuitBreaker(): Promise<{ ok: true }> {
  const res = await authFetch(
    `${BASE}/youtube-upload-schedule/reset-circuit-breaker`,
    { method: 'POST' },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Reset failed');
  return data;
}

export interface YoutubeUploadRun {
  id: number;
  scheduled_time: string;
  fired_at: string;
  video_id: number | null;
  youtube_video_id: string | null;
  /** Title of the published video. NULL when the run skipped/errored
   *  and didn't produce a YouTube video. */
  video_title: string | null;
  status: 'uploaded' | 'skipped_no_videos' | 'skipped_sanity'
        | 'skipped_grace' | 'error' | string;
  note: string | null;
}

export async function getYoutubeUploadSchedule(): Promise<YoutubeUploadSchedule> {
  const res = await authFetch(`${BASE}/youtube-upload-schedule`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch YouTube upload schedule');
  return data;
}

export async function saveYoutubeUploadSchedule(
  params: {
    enabled: boolean;
    times: string[];
    grace_minutes: number;
    sanity_check_enabled: boolean;
    privacy: 'public' | 'unlisted' | 'private';
  },
): Promise<YoutubeUploadSchedule> {
  const res = await authFetch(`${BASE}/youtube-upload-schedule`, {
    method: 'PUT',
    body: JSON.stringify(params),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to save schedule');
  return data;
}

export async function getYoutubeUploadRuns(limit = 50): Promise<YoutubeUploadRun[]> {
  const res = await authFetch(`${BASE}/youtube-upload-runs?limit=${limit}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch runs');
  return data;
}

// --------------- Auth ---------------

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  const res = await authFetch(`${BASE}/change-password`, {
    method: 'POST',
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to change password');
  // Save the fresh token (old tokens are invalidated by password change)
  if (data.token) setToken(data.token);
}

// --------------- Educational pipeline (Phase 1) ---------------

export type EducationalType = 'word_origins' | 'translation_hides' | 'grammar_insights';

export interface EducationalPool {
  word_origins: number;
  translation_hides: number;
  grammar_insights: number;
}

/** Candidates have a slightly different shape per type — anything not
 *  guaranteed across all three types is optional. */
export interface EducationalCandidate {
  chapter: number;
  verse: number;
  word_pos?: number | null;
  insight_id?: string | null;
  // Word Origins
  root_bw?: string;
  root_ar?: string;
  lemma_bw?: string;
  lang_count?: number;
  deriv_count?: number;
  // Translation Hides
  departure_notes?: string;
  // Composite-score signals surfaced on the candidate row so the
  // operator can scan ranking at a glance. Both come from the backend's
  // SQL scorer (ai_word_meanings + verse_grammar_insights joins).
  ai_word_count?: number;  // count of words with preferred_source IN ('ai', 'judge')
  has_v7?: number;         // 1 if the verse carries an eligible V7 insight
  // AI judge fields (translation_hides_signals table). Present when
  // translation_hides_ai.py has scored this verse. When present, the
  // candidate UI shows the judged headline as the primary scan-line
  // and the departure_notes excerpt drops to a secondary drawer.
  judge_score?: number | null;          // 0-10 video-worthiness
  judge_headline?: string | null;       // ≤80 chars, "<conv> / <actual>"
  judge_evidence_kind?: 'morphology' | 'lexical' | 'grammar' | 'context' | 'cognate' | null;
  judge_primary_word_pos?: number | null;
  judge_primary_arabic?: string | null;
  judge_conventional_gloss?: string | null;
  judge_hidden_gloss?: string | null;
  // Grammar Insights
  category?: string;
  title?: string;
  confidence?: number;
  has_counterfactual?: boolean;
  // 'A' (counterfactual + video-shaped category, × 2.0)
  // 'B' (counterfactual, other categories, × 1.5)
  // 'C' (no counterfactual, baseline)
  tier?: 'A' | 'B' | 'C';
  // Surfaced for the candidate preview drawer.
  claim_observation?: string;
  counterfactual_text?: string;
  payoff_text?: string;
  // Common
  score: number;
  text_uthmani?: string;
  translation?: string;
  /** Cached content-safety screen result for this verse. Present
   * only when the verse has been screened (either by the automated
   * pipeline path, or at queue-time by a prior manual queue). When
   * status === 'controversial', the candidate row should render a
   * warning badge and the Queue action should prompt to override. */
  safety_status?: {
    status: 'safe' | 'controversial' | 'unknown';
    reason?: string;
    model?: string | null;
    checked_at?: string;
  };
}

/** Error type thrown by queueEducationalCandidate when the backend
 * blocks the queue because the verse is flagged controversial. The
 * caller can prompt the operator and retry with `force: true`. */
export class EducationalSafetyBlockedError extends Error {
  status: 'controversial' | 'unknown';
  reason: string;
  constructor(safety: { status: string; reason: string }) {
    super(`verse flagged: ${safety.reason || safety.status}`);
    this.name = 'EducationalSafetyBlockedError';
    this.status = (safety.status as 'controversial' | 'unknown') || 'controversial';
    this.reason = safety.reason || '';
  }
}

export interface EducationalVideo {
  id: number;
  type: EducationalType;
  chapter: number;
  verse: number;
  anchor_word_pos: number | null;
  anchor_insight_id: string | null;
  status:
    | 'candidate'
    | 'script_ready'
    | 'rendering'
    | 'rendered'
    | 'uploaded'
    | 'failed'
    | 'rejected_uninteresting';
  format: string | null;
  filename: string | null;
  file_size: number | null;
  youtube_video_id: string | null;
  tiktok_video_id: string | null;
  /** YouTube metadata generated post-render via Ollama. */
  youtube_title?: string | null;
  youtube_description?: string | null;
  /** JSON-encoded array of tag strings. */
  youtube_tags?: string | null;
  pipeline_id?: number | null;
  triggered_by?: string | null;
  score: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
  /** Interestingness-judge verdict columns (set after script gen). */
  interestingness_score?: number | null;
  interestingness_verdict?: 'interesting' | 'skip' | 'unknown' | null;
  interestingness_reason?: string | null;
}

/**
 * Operator override: flip a rejected_uninteresting row back to
 * script_ready so it can be rendered. The judge's verdict stays on
 * the row for auditing.
 */
export async function overrideEducationalJudge(
  videoId: number,
): Promise<{ ok: true; id: number; status: string }> {
  const res = await authFetch(
    `${BASE}/educational/${videoId}/override-judge`,
    { method: 'POST' },
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Override failed');
  return data;
}

export async function getEducationalPool(): Promise<EducationalPool> {
  const res = await authFetch(`${BASE}/educational/pool`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch pool');
  return data;
}

export async function getEducationalCandidates(
  type: EducationalType,
  limit = 25,
): Promise<EducationalCandidate[]> {
  const res = await authFetch(
    `${BASE}/educational/candidates?type=${type}&limit=${limit}`,
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch candidates');
  return data.candidates as EducationalCandidate[];
}

export async function queueEducationalCandidate(
  type: EducationalType,
  c: EducationalCandidate,
  opts?: { force?: boolean },
): Promise<void> {
  const res = await authFetch(`${BASE}/educational/queue`, {
    method: 'POST',
    body: JSON.stringify({
      type,
      chapter: c.chapter,
      verse: c.verse,
      word_pos: c.word_pos ?? null,
      insight_id: c.insight_id ?? null,
      score: c.score,
      // When `force` is set, the backend skips the content-safety
      // gate and stamps `safety_override: true` on the payload so
      // the audit trail records the deliberate bypass. The caller
      // (admin UI) only sets `force` after the operator confirms a
      // controversial-flag warning.
      force: !!opts?.force,
      // Pass the structured payload so Phase 2 has what it needs to
      // ground the script. Type-specific fields are bundled together;
      // generators consume only the keys relevant to their type.
      payload: {
        root_bw: c.root_bw,
        root_ar: c.root_ar,
        lemma_bw: c.lemma_bw,
        lang_count: c.lang_count,
        deriv_count: c.deriv_count,
        departure_notes: c.departure_notes,
        category: c.category,
        title: c.title,
        confidence: c.confidence,
        has_counterfactual: c.has_counterfactual,
      },
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    // 409 with a safety_status block means the content-safety gate
    // refused. Raise a typed error so the UI can prompt the operator
    // to review the reason and choose whether to retry with force.
    if (res.status === 409 && data?.safety_status) {
      throw new EducationalSafetyBlockedError({
        status: data.safety_status.status,
        reason: data.safety_status.reason || '',
      });
    }
    throw new Error(data.error || 'Failed to queue candidate');
  }
}

export interface EducationalScript {
  hook: string;
  verse_intro: string;
  insight: string;
  close: string;
  voiceover_long: string;
  voiceover_short: string;
  /** Pre-sanitization voiceover bodies — the raw LLM output before
   *  IPA marks / Arabic script were stripped. Useful for verifying
   *  the sanitizer didn't garble anything. Only set when the
   *  sanitized version differs. */
  voiceover_long_raw?: string;
  voiceover_short_raw?: string;
  languages_referenced: string[];
  notes?: string;
}

export interface EducationalVideoDetail extends EducationalVideo {
  payload_json: string | null;
  script_json: string | null;
  voiceover_text: string | null;
  /** Convenience — backend parses script_json for the UI. */
  script?: EducationalScript | null;
}

export async function getEducationalVideoDetail(id: number): Promise<EducationalVideoDetail> {
  const res = await authFetch(`${BASE}/educational/${id}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch video');
  return data;
}

export async function generateEducationalScript(id: number): Promise<EducationalScript> {
  const res = await authFetch(`${BASE}/educational/${id}/generate-script`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to generate script');
  return data.script;
}

export interface ScriptEdits {
  hook?: string;
  verse_intro?: string;
  insight?: string;
  close?: string;
  voiceover_long?: string;
  voiceover_short?: string;
}

/** Kick off Phase 3 rendering for one variant. Returns 202 — the
 *  render runs in a background thread on the server; poll
 *  getEducationalVideoDetail() to watch the status transition
 *  rendering → rendered (or failed). */
export async function renderEducationalVideo(
  id: number,
  format: 'long' | 'short',
): Promise<void> {
  const res = await authFetch(`${BASE}/educational/${id}/render`, {
    method: 'POST',
    body: JSON.stringify({ format }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Failed to start render');
}

/** Save operator edits to a generated script. The backend sanitizes
 *  voiceover bodies and re-validates length / TTS-friendliness /
 *  language grounding. On validation failure throws an Error whose
 *  .message is "validation failed: <issue>; <issue>". */
export async function editEducationalScript(
  id: number,
  edits: ScriptEdits,
): Promise<EducationalScript> {
  const res = await authFetch(`${BASE}/educational/${id}/script`, {
    method: 'PATCH',
    body: JSON.stringify(edits),
  });
  const data = await res.json();
  if (!res.ok) {
    const issues = (data.issues as string[] | undefined)?.join('; ');
    throw new Error(issues ? `validation failed: ${issues}` : data.error || 'Failed to save');
  }
  return data.script;
}

export interface UploadYouTubeResult {
  ok: true;
  video_id: number;
  youtube_video_id: string;
  youtube_url: string;
  privacy: 'public' | 'unlisted' | 'private';
  playlist_note?: string | null;
}

/** Upload a rendered educational video to YouTube. Synchronous on
 *  the server (the mp4 body posts inside the request), so this
 *  call typically takes 10–30s. Returns the YouTube URL + a note
 *  on whether the per-series playlist add succeeded. */
export async function uploadEducationalVideoToYouTube(
  id: number,
  opts: { privacy?: 'public' | 'unlisted' | 'private' } = {},
): Promise<UploadYouTubeResult> {
  const res = await authFetch(`${BASE}/educational/${id}/upload-youtube`, {
    method: 'POST',
    body: JSON.stringify({ privacy: opts.privacy ?? 'public' }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Upload failed');
  return data as UploadYouTubeResult;
}

export interface YouTubeVideoStats {
  youtube_video_id: string;
  title: string | null;
  published_at: string | null;
  views: number;
  likes: number;
  comments: number;
}

/** Live stats fetch for an uploaded educational video. Calls
 *  YouTube Data API videos.list?part=statistics. Requires the
 *  broad 'youtube' OAuth scope on the refresh token; 403 from
 *  here is the same root cause as the 403 on playlistItems.insert
 *  ("insufficient authentication scopes" — the token was minted
 *  with youtube.upload only). */
export async function getEducationalYouTubeStats(
  id: number,
): Promise<YouTubeVideoStats> {
  const res = await authFetch(`${BASE}/educational/${id}/youtube-stats`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Stats fetch failed');
  return data as YouTubeVideoStats;
}


/** Retry the per-series playlist add for an already-uploaded video.
 *  Re-reads the playlist preference and calls YouTube's
 *  playlistItems.insert. Useful when the original upload's playlist
 *  add failed (wrong channel selected, transient error) or when the
 *  operator filled in the playlist ID after upload. */
export async function retryEducationalPlaylistAdd(
  id: number,
): Promise<{ ok: boolean; playlist_id: string; message: string }> {
  const res = await authFetch(`${BASE}/educational/${id}/add-to-playlist`, {
    method: 'POST',
  });
  const data = await res.json();
  if (!res.ok && res.status !== 502) {
    // 502 = playlist API error; we still want to surface its message.
    throw new Error(data.error || 'Retry failed');
  }
  return data as { ok: boolean; playlist_id: string; message: string };
}


/** Hard-delete a generated video — drops the DB row and removes the
 *  rendered mp4 on disk. Refuses (409) if status is 'rendering' so
 *  we don't yank a file out from under in-flight ffmpeg. */
export async function deleteEducationalVideo(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/educational/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Failed to delete video');
  }
}


export async function getEducationalVideos(
  type?: EducationalType,
): Promise<EducationalVideo[]> {
  const url = type
    ? `${BASE}/educational/videos?type=${type}`
    : `${BASE}/educational/videos`;
  const res = await authFetch(url);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch videos');
  return data.videos as EducationalVideo[];
}

// --------------- Educational pipelines ---------------

export interface EducationalPipeline {
  id: number;
  name: string;
  type: EducationalType;
  voice_id: string;
  format: 'short' | 'long';
  show_dim_background: number;  // 0 | 1 — sqlite bool
  music_id: number | null;
  /** When set, the renderer plays this sound bite during the
   *  al-nuqta outro splash and extends the outro window so the
   *  audio finishes before the video does. */
  outro_audio_filename?: string | null;
  enabled: number;              // 0 | 1
  created_at: string;
  updated_at: string;
}

export interface EducationalPipelineDetail extends EducationalPipeline {
  videos: EducationalVideo[];
}

export interface EducationalPipelineInput {
  name: string;
  type: EducationalType;
  voice_id: string;
  format: 'short' | 'long';
  show_dim_background?: boolean;
  music_id?: number | null;
  enabled?: boolean;
}

export async function getEducationalPipelines(
  type?: EducationalType,
): Promise<EducationalPipeline[]> {
  const url = type
    ? `${BASE}/educational/pipelines?type=${type}`
    : `${BASE}/educational/pipelines`;
  const res = await authFetch(url);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch pipelines');
  return data.pipelines as EducationalPipeline[];
}

export async function getEducationalPipeline(
  id: number,
): Promise<EducationalPipelineDetail> {
  const res = await authFetch(`${BASE}/educational/pipelines/${id}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch pipeline');
  return data;
}

export async function createEducationalPipeline(
  input: EducationalPipelineInput,
): Promise<EducationalPipeline> {
  const res = await authFetch(`${BASE}/educational/pipelines`, {
    method: 'POST',
    body: JSON.stringify(input),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to create pipeline');
  return data;
}

export async function updateEducationalPipeline(
  id: number,
  patch: Partial<EducationalPipelineInput>,
): Promise<EducationalPipeline> {
  const res = await authFetch(`${BASE}/educational/pipelines/${id}`, {
    method: 'PUT',
    body: JSON.stringify(patch),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to update pipeline');
  return data;
}

export async function deleteEducationalPipeline(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/educational/pipelines/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Failed to delete pipeline');
  }
}

/** Upload (or replace) a pipeline's outro sound bite. Server caps
 *  duration at 30s and file size at 10 MB; reject reasons surface
 *  through the thrown Error. */
export async function uploadEducationalOutroAudio(
  pipelineId: number,
  file: File,
): Promise<{ filename: string; size_bytes: number; duration_seconds: number }> {
  const fd = new FormData();
  fd.append('audio', file);
  const res = await authFetch(
    `${BASE}/educational/pipelines/${pipelineId}/outro-audio`,
    { method: 'POST', body: fd },
  );
  const text = await res.text();
  let data: Record<string, unknown>;
  try { data = JSON.parse(text); }
  catch {
    throw new Error(res.status === 413
      ? 'Upload rejected by reverse proxy (HTTP 413).'
      : `Upload failed (${res.status})`);
  }
  if (!res.ok) throw new Error((data.error as string) || 'Upload failed');
  return data as unknown as { filename: string; size_bytes: number; duration_seconds: number };
}

export async function deleteEducationalOutroAudio(pipelineId: number): Promise<void> {
  const res = await authFetch(
    `${BASE}/educational/pipelines/${pipelineId}/outro-audio`,
    { method: 'DELETE' },
  );
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error((data as Record<string, unknown>).error as string || 'Delete failed');
  }
}

/** Constructs the streamable URL for the outro audio (auth via
 *  query-string token). Returns empty string when no audio is set. */
export function educationalOutroAudioUrl(pipelineId: number): string {
  const token = localStorage.getItem('admin_token') || '';
  return `${BASE}/educational/pipelines/${pipelineId}/outro-audio`
    + `?token=${encodeURIComponent(token)}`;
}


export async function runEducationalPipeline(
  id: number,
): Promise<{ pipeline_id: number; video_id: number; status: string }> {
  const res = await authFetch(`${BASE}/educational/pipelines/${id}/run`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to start pipeline run');
  return data;
}

// --------------- Educational pipeline schedules ---------------

export interface EducationalSchedule {
  pipeline_id: number;
  times: string[];
  max_runs_per_day: number;
  enabled: boolean;
  grace_minutes: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface EducationalScheduleRun {
  id: number;
  pipeline_id: number;
  scheduled_time: string;
  fired_at: string;
  video_id: number | null;
  status: 'fired' | 'skipped_grace' | 'skipped_cap' | 'skipped_active' | 'error';
  note: string | null;
}

export async function getEducationalSchedule(
  pipelineId: number,
): Promise<EducationalSchedule> {
  const res = await authFetch(`${BASE}/educational/pipelines/${pipelineId}/schedule`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch schedule');
  return data;
}

export async function upsertEducationalSchedule(
  pipelineId: number,
  patch: Pick<EducationalSchedule, 'times' | 'max_runs_per_day' | 'enabled' | 'grace_minutes'>,
): Promise<EducationalSchedule> {
  const res = await authFetch(`${BASE}/educational/pipelines/${pipelineId}/schedule`, {
    method: 'PUT',
    body: JSON.stringify(patch),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to save schedule');
  return data;
}

export async function getEducationalScheduleRuns(
  pipelineId: number,
  limit = 50,
): Promise<EducationalScheduleRun[]> {
  const res = await authFetch(
    `${BASE}/educational/pipelines/${pipelineId}/schedule/runs?limit=${limit}`,
  );
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch runs');
  return data.runs as EducationalScheduleRun[];
}

// Aggregated views for the Scheduler page so it can render every
// educational pipeline's schedule in one section (mirrors the
// recitation getPipelineSchedules / getPipelineScheduleRuns shape).

export interface EducationalScheduleListItem {
  pipeline_id: number;
  pipeline_name: string;
  pipeline_type: 'word_origins' | 'translation_hides' | 'grammar_insights' | string;
  pipeline_enabled: boolean;
  times: string[];
  max_runs_per_day: number;
  enabled: boolean;
  grace_minutes: number;
  updated_at: string | null;
}

export interface EducationalScheduleRunGlobal {
  id: number;
  pipeline_id: number;
  pipeline_name: string;
  pipeline_type: string;
  scheduled_time: string;
  fired_at: string;
  video_id: number | null;
  /** Title of the produced educational video. NULL for skipped runs. */
  video_title: string | null;
  /** Downstream video state ('script_ready', 'rendered', 'uploaded',
   *  'failed', etc.) so the audit log can show why a "fired" run has
   *  no title. NULL when there is no video row. */
  video_status: string | null;
  /** Last error message from the failed pipeline step, when status
   *  is 'failed'. Used to render a tooltip on the failure chip. */
  video_error: string | null;
  status: string;
  note: string | null;
}

export async function getAllEducationalSchedules(): Promise<EducationalScheduleListItem[]> {
  const res = await authFetch(`${BASE}/educational/schedules`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch educational schedules');
  return data as EducationalScheduleListItem[];
}

export async function getAllEducationalScheduleRuns(
  limit = 50,
): Promise<EducationalScheduleRunGlobal[]> {
  const res = await authFetch(`${BASE}/educational/schedule-runs?limit=${limit}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch educational schedule runs');
  return data as EducationalScheduleRunGlobal[];
}

// --------------- Server time ---------------

/** Snapshot of the server's local clock + timezone. The Scheduler
 *  page anchors its countdown on this so the operator's timer
 *  matches what the scheduler is actually using to decide when
 *  to fire — independent of browser timezone. */
export interface ServerTime {
  now_iso: string;        // ISO-8601 with offset
  now_epoch_ms: number;   // server's epoch in ms
  tz_offset_minutes: number;
  tz_name: string;
}

export async function getServerTime(): Promise<ServerTime> {
  const res = await authFetch(`${BASE}/server-time`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch server time');
  return data as ServerTime;
}

/* =================================================================== */
/*  Verse of the Day pool                                              */
/* =================================================================== */

// One row in the homepage's verse-of-the-day rotation. Backend
// enriches each row with the surah name + 60-char Arabic preview +
// 140-char translation preview so the admin UI can render rich rows
// without a per-row /api/verse fetch.
export interface VerseOfTheDayPoolItem {
  id: number;
  chapter: number;
  verse: number;
  position: number;
  created_at: string;
  /** Full Arabic verse text (Uthmani script). Backwards-compatible
   *  alias `arabic_preview` is also populated. */
  arabic?: string;
  /** Full English translation. Alias: `translation_en`. */
  translation_en?: string;
  /** @deprecated use `arabic` — kept for back-compat with old bundles. */
  arabic_preview: string;
  /** @deprecated use `translation_en` — kept for back-compat. */
  translation_preview: string;
  /** @deprecated removed in May 2026 — DB has no surahs table. */
  surah_name?: string;
}

export interface VerseOfTheDayPoolList {
  items: VerseOfTheDayPoolItem[];
  // Today's deterministic pick (day-of-year mod pool size). null only
  // if the pool is empty.
  today: { chapter: number; verse: number } | null;
}

export async function getVerseOfTheDayPool(): Promise<VerseOfTheDayPoolList> {
  const res = await authFetch(`${BASE}/verse-of-the-day-pool`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to fetch pool');
  return data as VerseOfTheDayPoolList;
}

export async function addVerseOfTheDay(
  chapter: number,
  verse: number,
): Promise<VerseOfTheDayPoolItem> {
  const res = await authFetch(`${BASE}/verse-of-the-day-pool`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ chapter, verse }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to add verse');
  return data as VerseOfTheDayPoolItem;
}

export async function deleteVerseOfTheDay(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/verse-of-the-day-pool/${id}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Failed to delete');
  }
}

// ===========================================================================
// Stats — website + YouTube analytics for the /admin/stats page and the
// summary tiles on the admin dashboard.
// ===========================================================================
export type StatsRange = '7d' | '30d';

export interface WebsiteStatsTotals {
  page_views: number;
  unique_visitors: number;
  page_views_prior: number;
  unique_visitors_prior: number;
}

export interface WebsiteStatsDailyPoint {
  date: string;
  page_views: number;
  unique_visitors: number;
}

export interface WebsiteStatsTopPage {
  path: string;
  page_views: number;
  unique_visitors: number;
}

export interface WebsiteStatsTopReferrer {
  referrer: string;
  page_views: number;
}

export interface WebsiteStats {
  range: string;
  since: string;
  until: string;
  totals: WebsiteStatsTotals;
  daily: WebsiteStatsDailyPoint[];
  top_pages: WebsiteStatsTopPage[];
  top_referrers: WebsiteStatsTopReferrer[];
  live: { active_last_5min: number };
}

export async function getWebsiteStats(range: StatsRange): Promise<WebsiteStats> {
  const res = await authFetch(`${BASE}/stats/website?range=${range}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load website stats');
  return data as WebsiteStats;
}

export interface YoutubeStatsVideo {
  youtube_video_id: string;
  url: string;
  title: string | null;
  published_at: string | null;
  current_views: number;
  current_likes: number;
  current_comments: number;
  views_gain: number;
  likes_gain: number;
  source_table: string;
  source_id: number;
}

export interface YoutubeChannelDailyPoint {
  date: string;
  subscribers: number;
}

export interface YoutubeChannelStats {
  channel_id: string;
  title: string | null;
  current_subscribers: number;
  current_view_count: number;
  current_video_count: number;
  subscribers_gain: number;
  subscribers_daily: YoutubeChannelDailyPoint[];
}

export interface YoutubeStats {
  range: string;
  totals: {
    videos: number;
    total_views: number;
    total_likes: number;
    views_gain_period: number;
    likes_gain_period: number;
  };
  videos: YoutubeStatsVideo[];
  // null until the first refresh succeeds with channels.list permission
  channel: YoutubeChannelStats | null;
  last_refresh: string | null;
  snapshot_count: number;
  /** Channel ID we expect every refresh to belong to. Set on first
   *  successful refresh; the operator can change it via the repin
   *  endpoint when intentionally switching channels. */
  pinned_channel_id?: string | null;
  /** Set when the most-recent refresh saw a DIFFERENT channel_id
   *  than the pinned one. The refresh REFUSES to overwrite stats
   *  in that case — operator must re-OAuth from the right account
   *  OR explicitly repin to the new channel. */
  channel_mismatch?: {
    pinned_channel_id: string | null;
    connected_channel_id: string;
    connected_title: string | null;
    detected_at: string | null;
  } | null;
}

/** Accept the currently-connected OAuth channel as the pinned one.
 *  Used when the operator intentionally switches channels and wants
 *  the dashboard to follow. */
export async function repinYoutubeChannel(): Promise<{
  ok: boolean;
  channel_id?: string;
  title?: string;
  error?: string;
}> {
  const res = await authFetch(`${BASE}/stats/youtube/repin`, { method: 'POST' });
  return res.json();
}

export async function getYoutubeStats(range: StatsRange): Promise<YoutubeStats> {
  const res = await authFetch(`${BASE}/stats/youtube?range=${range}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load YouTube stats');
  return data as YoutubeStats;
}

export interface YoutubeRefreshResult {
  ok: boolean;
  videos_refreshed?: number;
  fetched_at?: string;
  error?: string;
}

export async function refreshYoutubeStats(): Promise<YoutubeRefreshResult> {
  const res = await authFetch(`${BASE}/stats/youtube/refresh`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Refresh failed');
  return data as YoutubeRefreshResult;
}

// --------------- Ask the Quran — Q&A moderation ---------------

/** One saved "Ask the Quran" thread (a synthesized question + its latest
 *  answer), anchored to a verse/word/root page. Shown publicly until an
 *  admin hides or deletes it. */
export interface AdminQAItem {
  id: number;
  page_type: string;       // 'verse' | 'word' | 'root' | …
  page_key: string;        // e.g. '2:255' for a verse
  question: string;
  answer: string;
  context_summary: string | null;
  context_range: string | null;   // 'S:V1-V2' when asked from a reader window
  model_used: string | null;
  response_time_ms: number | null;
  created_at: string;      // UTC, no 'Z' suffix
  edited_at: string | null;
  hidden: boolean;
  session_short: string;   // first 8 chars of the asker's session id
  // AI-drafted Q&A (pre-populated via the /loop generator); 'user' on
  // user-asked rows.
  source: string;          // 'user' | 'ai'
  review_status: string | null;   // 'pending' | 'approved' | 'rejected'
  category: string | null;        // question archetype
  quality_score: number | null;   // 1–5 generator confidence
  generation_meta: { source_notes?: string; cited_refs?: string[]; flags?: string[] } | null;
}

export interface AdminQAListResponse {
  items: AdminQAItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface AdminQAStats {
  total: number;
  visible: number;
  hidden: number;
  edited: number;
  ai_total: number;
  ai_pending: number;
  ai_approved: number;
  ai_rejected: number;
  pages: number;
  sessions: number;
  last_7_days: number;
  last_24_hours: number;
  by_type: { page_type: string; count: number }[];
  by_model: { model: string; count: number }[];
  by_score: { score: number; count: number }[];
  top_pages: { page_type: string; page_key: string; count: number }[];
}

export type AdminQAStatus = 'all' | 'visible' | 'hidden';
export type AdminQASort = 'recent' | 'oldest' | 'slowest' | 'longest';

export interface AdminQAQuery {
  q?: string;
  page_type?: string;
  model?: string;
  source?: string;          // 'user' | 'ai'
  review_status?: string;   // 'pending' | 'approved' | 'rejected'
  score?: string;           // '1'–'5' quality grade
  status?: AdminQAStatus;
  sort?: AdminQASort;
  limit?: number;
  offset?: number;
}

export async function getAdminQA(query: AdminQAQuery = {}): Promise<AdminQAListResponse> {
  const params = new URLSearchParams();
  if (query.q) params.set('q', query.q);
  if (query.page_type) params.set('page_type', query.page_type);
  if (query.model) params.set('model', query.model);
  if (query.source) params.set('source', query.source);
  if (query.review_status) params.set('review_status', query.review_status);
  if (query.score) params.set('score', query.score);
  if (query.status && query.status !== 'all') params.set('status', query.status);
  if (query.sort) params.set('sort', query.sort);
  params.set('limit', String(query.limit ?? 25));
  params.set('offset', String(query.offset ?? 0));
  const res = await authFetch(`${BASE}/assistant/qa?${params}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load Q&A');
  return data as AdminQAListResponse;
}

export async function getAdminQAStats(): Promise<AdminQAStats> {
  const res = await authFetch(`${BASE}/assistant/qa/stats`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load Q&A stats');
  return data as AdminQAStats;
}

/** Hide/unhide, or correct the stored question/answer. Returns the fresh row. */
export async function updateAdminQA(
  id: number,
  patch: { hidden?: boolean; answer?: string; question?: string; review_status?: string },
): Promise<AdminQAItem> {
  const res = await authFetch(`${BASE}/assistant/qa/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Update failed');
  return data.item as AdminQAItem;
}

/** Permanent delete. Prefer updateAdminQA({hidden:true}) for reversible removal. */
export async function deleteAdminQA(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/assistant/qa/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Delete failed');
  }
}

export type AdminQABulkOp = 'approve' | 'reject' | 'pending' | 'hide' | 'unhide' | 'delete';

/** Apply one moderation op to many rows at once (review-queue triage). */
export async function bulkAdminQA(ids: number[], op: AdminQABulkOp): Promise<{ affected: number }> {
  const res = await authFetch(`${BASE}/assistant/qa/bulk`, {
    method: 'POST',
    body: JSON.stringify({ ids, op }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Bulk action failed');
  return data;
}

/* ---------------------------------------------------------------- */
/*  Verse exegesis — teacher-voice commentary distilled from Q&A    */
/* ---------------------------------------------------------------- */

export interface AdminExegesisItem {
  id: number;
  chapter: number;
  verse: number;
  page_key: string;               // 'C:V'
  exegesis_markdown: string;
  source_gem_ids: number[] | null;
  source_scores: number[] | null;
  model_used: string | null;
  review_status: string | null;   // 'pending' | 'approved' | 'rejected'
  hidden: boolean;
  template_version: string | null;
  generation_meta: { source_notes?: string; flags?: string[]; [k: string]: unknown } | null;
  created_at: string;
  edited_at: string | null;
}

export interface AdminExegesisStats {
  total: number;
  visible: number;
  hidden: number;
  pending: number;
  approved: number;
  rejected: number;
  verses: number;
  edited: number;
}

export type AdminExegesisSort = 'recent' | 'oldest' | 'verse' | 'longest';
export type AdminExegesisBulkOp = AdminQABulkOp;

export interface AdminExegesisQuery {
  q?: string;
  review_status?: string;
  status?: AdminQAStatus;
  sort?: AdminExegesisSort;
  limit?: number;
  offset?: number;
}

export interface AdminExegesisListResponse {
  items: AdminExegesisItem[];
  total: number;
  limit: number;
  offset: number;
}

export async function getAdminExegesis(query: AdminExegesisQuery = {}): Promise<AdminExegesisListResponse> {
  const params = new URLSearchParams();
  if (query.q) params.set('q', query.q);
  if (query.review_status) params.set('review_status', query.review_status);
  if (query.status && query.status !== 'all') params.set('status', query.status);
  if (query.sort) params.set('sort', query.sort);
  params.set('limit', String(query.limit ?? 25));
  params.set('offset', String(query.offset ?? 0));
  const res = await authFetch(`${BASE}/exegesis?${params}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load exegesis');
  return data as AdminExegesisListResponse;
}

export async function getAdminExegesisStats(): Promise<AdminExegesisStats> {
  const res = await authFetch(`${BASE}/exegesis/stats`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load exegesis stats');
  return data as AdminExegesisStats;
}

export async function updateAdminExegesis(
  id: number,
  patch: { hidden?: boolean; exegesis_markdown?: string; review_status?: string },
): Promise<AdminExegesisItem> {
  const res = await authFetch(`${BASE}/exegesis/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Update failed');
  return data.item as AdminExegesisItem;
}

export async function deleteAdminExegesis(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/exegesis/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Delete failed');
  }
}

export async function bulkAdminExegesis(ids: number[], op: AdminExegesisBulkOp): Promise<{ affected: number }> {
  const res = await authFetch(`${BASE}/exegesis/bulk`, {
    method: 'POST',
    body: JSON.stringify({ ids, op }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Bulk action failed');
  return data;
}

/* ---------------------------------------------------------------- */
/*  Pre-Islamic poetry — root comparisons + verse notes review      */
/* ---------------------------------------------------------------- */

export type PoetryKind = 'root' | 'verse' | 'lexicon';

export interface AdminPoetryItem {
  id: number;
  kind: PoetryKind;
  label: string;                  // 'ك ف ر' (root) or '45:24' (verse)
  link: string;                   // '/root/kfr' or '/verse/45:24'
  markdown: string;
  verdict: string | null;         // 'continuity' | shift_type | 'contrast' | relation_to_quran
  continuity: boolean;
  confidence: number | null;
  auth_tier_max: string | null;
  quoted_count: number;
  review_status: string | null;   // 'pending' | 'approved' | 'rejected'
  hidden: boolean;
  created_at: string;
  edited_at: string | null;
  // lexicon-only
  attestation_strength?: string;  // rich | moderate | thin | unattested
  sense_count?: number;
  poetry_occurrences?: number;
  relation_to_quran?: string | null;
}

export interface AdminPoetryKindStats {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  hidden: number;
}

export interface AdminPoetryStats extends AdminPoetryKindStats {
  roots: number;
  verses: number;
  lexicons: number;
  root: AdminPoetryKindStats;
  verse: AdminPoetryKindStats;
  lexicon: AdminPoetryKindStats;
}

export type AdminPoetrySort = 'recent' | 'oldest' | 'longest';

export interface AdminPoetryQuery {
  kind: PoetryKind;
  q?: string;
  review_status?: string;
  status?: AdminQAStatus;
  sort?: AdminPoetrySort;
  limit?: number;
  offset?: number;
}

export interface AdminPoetryListResponse {
  items: AdminPoetryItem[];
  total: number;
  limit: number;
  offset: number;
  kind: PoetryKind;
}

export async function getAdminPoetry(query: AdminPoetryQuery): Promise<AdminPoetryListResponse> {
  const params = new URLSearchParams();
  params.set('kind', query.kind);
  if (query.q) params.set('q', query.q);
  if (query.review_status) params.set('review_status', query.review_status);
  if (query.status && query.status !== 'all') params.set('status', query.status);
  if (query.sort) params.set('sort', query.sort);
  params.set('limit', String(query.limit ?? 25));
  params.set('offset', String(query.offset ?? 0));
  const res = await authFetch(`${BASE}/poetry?${params}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load poetry');
  return data as AdminPoetryListResponse;
}

export async function getAdminPoetryStats(): Promise<AdminPoetryStats> {
  const res = await authFetch(`${BASE}/poetry/stats`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load poetry stats');
  return data as AdminPoetryStats;
}

export async function updateAdminPoetry(
  kind: PoetryKind,
  id: number,
  patch: { hidden?: boolean; markdown?: string; review_status?: string },
): Promise<AdminPoetryItem> {
  const res = await authFetch(`${BASE}/poetry/${kind}/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(patch),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Update failed');
  return data.item as AdminPoetryItem;
}

export async function deleteAdminPoetry(kind: PoetryKind, id: number): Promise<void> {
  const res = await authFetch(`${BASE}/poetry/${kind}/${id}`, { method: 'DELETE' });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.error || 'Delete failed');
  }
}

export async function bulkAdminPoetry(
  kind: PoetryKind,
  ids: number[],
  op: AdminExegesisBulkOp,
): Promise<{ affected: number }> {
  const res = await authFetch(`${BASE}/poetry/bulk`, {
    method: 'POST',
    body: JSON.stringify({ kind, ids, op }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Bulk action failed');
  return data;
}

// ---------------------------------------------------------------------------
// Q&A video script bank (pre-generated shorts)
// ---------------------------------------------------------------------------

export interface QaVideoBeat {
  kind: string;
  narration: string;
  verse?: { ref: string; highlight_phrase_en?: string; highlight_words_ar?: string[] };
}

export interface QaVideoItem {
  id: number;
  qa_id: number;
  anchor_ref: string;
  title: string;
  theme: string | null;
  status: string;
  filename: string | null;
  file_size: number | null;
  punch_ok: number | null;
  match_ok: number | null;
  error_message: string | null;
  rendering: number;
  source_type: string;
  source_key: string | null;
  angle: string | null;
  self_score: number | null;
  quality_report: string | null;
  youtube_video_id: string | null;
  uploaded_to_youtube: number;
  created_at: string;
  completed_at: string | null;
  beats: QaVideoBeat[];
}

export interface QaPublishSchedule {
  enabled: boolean;
  days: number[];
  time: string;
  grace_minutes?: number;
  privacy: string;
  voice_id?: string | null;
  last_fired_date?: string | null;
}

export interface QaVoice {
  id: number;
  name: string;
  voice_id: string;
}

export interface QaCandidate {
  id: number;
  source_type: string;
  source_key: string;
  anchor_ref: string | null;
  angle: string | null;
  hook_sketch: string | null;
  self_score: number | null;
  status: string;
}

export async function getQaVideos(): Promise<{
  videos: QaVideoItem[];
  publish_schedule: QaPublishSchedule;
  voices: QaVoice[];
  candidates: QaCandidate[];
}> {
  const res = await authFetch(`${BASE}/qa-videos`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Failed to load videos');
  return data;
}

export async function renderQaVideo(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/qa-videos/${id}/render`, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Render failed to start');
}

export async function approveQaVideo(id: number): Promise<void> {
  const res = await authFetch(`${BASE}/qa-videos/${id}/approve`, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Approve failed');
}

export async function rejectQaVideo(id: number, reason?: string): Promise<void> {
  const res = await authFetch(`${BASE}/qa-videos/${id}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason: reason || '' }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || 'Reject failed');
}

export async function saveQaPublishSchedule(
  patch: Partial<QaPublishSchedule>,
): Promise<QaPublishSchedule> {
  const res = await authFetch(`${BASE}/qa-videos/publish-schedule`, {
    method: 'PUT',
    body: JSON.stringify(patch),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Save failed');
  return data;
}

/** Fetch the rendered MP4 with auth and return an object URL for <video>.
 *  (A bare <video src> can't send the Bearer header.) Caller must
 *  URL.revokeObjectURL when done. */
export async function fetchQaVideoObjectUrl(id: number): Promise<string> {
  const res = await authFetch(`${BASE}/qa-videos/${id}/video`);
  if (!res.ok) throw new Error('Video not available');
  const blob = await res.blob();
  return URL.createObjectURL(blob);
}

/** Inline script edit — the server re-runs ALL gates on the edited script
 *  and rejects with {issues} if anything fails. Only title/theme/beats are
 *  editable; a successful edit clears any stale rendered file. */
export async function editQaVideoScript(
  id: number,
  patch: { title?: string; theme?: string; beats?: QaVideoBeat[] },
): Promise<{ ok: boolean; status: string }> {
  const res = await authFetch(`${BASE}/qa-videos/${id}/script`, {
    method: 'PUT',
    body: JSON.stringify(patch),
  });
  const data = await res.json();
  if (!res.ok) {
    const issues = Array.isArray(data.issues) ? `\n• ${data.issues.join('\n• ')}` : '';
    throw new Error((data.error || 'Edit failed') + issues);
  }
  return data;
}

/** Mint a 24h edit token for the "Ask AI to Edit" handoff (returned once). */
export async function mintQaEditToken(
  id: number,
): Promise<{ token: string; expires: string; id: number }> {
  const res = await authFetch(`${BASE}/qa-videos/${id}/edit-token`, { method: 'POST' });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || 'Token mint failed');
  return data;
}


/** Backlog panel: star an idea (drafted next) or kill it (never re-proposed). */
export async function patchVideoCandidate(
  id: number,
  status: 'starred' | 'rejected_score' | 'proposed',
  reason?: string,
): Promise<void> {
  const res = await authFetch(`${BASE}/video-candidates/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ status, reason }),
  });
  if (!res.ok) throw new Error((await res.json()).error || 'Update failed');
}
