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

export async function login(username: string, password: string): Promise<{ token: string; username: string }> {
  const res = await fetch(`${BASE}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
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
    throw new Error(res.status === 413 ? 'File too large (max 500MB)' : `Upload failed (${res.status})`);
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

export async function updateResource(id: number, description: string): Promise<Resource> {
  const res = await authFetch(`${BASE}/resources/${id}`, {
    method: 'PUT',
    body: JSON.stringify({ description }),
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
    throw new Error(res.status === 413 ? 'File too large' : `Upload failed (${res.status})`);
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
