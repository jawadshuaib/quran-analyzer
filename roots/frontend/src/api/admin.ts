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
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
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
