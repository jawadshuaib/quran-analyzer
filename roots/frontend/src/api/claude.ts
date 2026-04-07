/**
 * Claude API client for the "Ask the Quran" assistant.
 * Supports two modes:
 *   1. Free tier — proxied through the backend (server's API key, limited uses)
 *   2. Own key  — direct browser-to-Anthropic calls (unlimited)
 */

import { getApiKey, getModel } from '../utils/assistant-storage';
import { API_BASE } from './quran';

const ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages';
const FREE_MODEL = 'claude-sonnet-4-20250514';

export type PageType = 'verse' | 'root' | 'word';

export function buildSystemPrompt(pageType: PageType, context: string): string {
  return `You are a Quranic research assistant. You analyze the Quran exclusively from its own text — no hadith, tafsir, sectarian commentary, or later Islamic additions.

CORE PRINCIPLES:
1. Let the Quran speak for itself. Every claim must be grounded in Quranic text.
2. Never hallucinate or fabricate verse references. If you are uncertain, say so explicitly.
3. Never agree with the user just to be agreeable. If their premise contradicts the Quranic text, say so respectfully and clearly.
4. Cross-reference related verses to build understanding. The Quran interprets the Quran.
5. Pay attention to Arabic root words, morphology, and Semitic cognates — these reveal layers of meaning that translations miss.
6. Distinguish between what the text directly states and what requires interpretation. Label your reasoning clearly.
7. When multiple readings of a verse are linguistically valid, present them all rather than picking one.
8. Do NOT use words like "Islamic", "halal", "haram", "sunnah", or any terminology from post-Quranic religious tradition.

METHODOLOGY:
- Use the provided context (verse text, translations, root analysis, morphology, cognates, related verses, thematic context) as your primary source material.
- Cite specific verse references (e.g., 2:255) when making claims.
- When discussing word meanings, reference the root word analysis and cognate data provided.
- Be concise but thorough. Avoid filler.

Below is the detailed context for the ${pageType} the user is currently viewing. Use this as your primary reference material for answering questions.

---
${context}
---`;
}

export interface StreamCallbacks {
  onToken: (text: string) => void;
  onDone: (fullText: string, responseTimeMs: number) => void;
  onError: (error: string) => void;
}

/** Parse SSE stream from either source (proxy or direct) and invoke callbacks. */
async function consumeStream(
  reader: ReadableStreamDefaultReader<Uint8Array>,
  callbacks: StreamCallbacks,
  startTime: number,
) {
  const decoder = new TextDecoder();
  let fullText = '';
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') continue;
        try {
          const event = JSON.parse(data);
          if (event.type === 'content_block_delta' && event.delta?.text) {
            fullText += event.delta.text;
            callbacks.onToken(event.delta.text);
          } else if (event.type === 'error') {
            callbacks.onError(event.error?.message || 'Unknown streaming error');
            return;
          }
        } catch {
          // Skip unparseable lines
        }
      }
    }
  }

  callbacks.onDone(fullText, Date.now() - startTime);
}

/**
 * Send a question to Claude via the backend proxy (free tier).
 */
export function askClaudeProxy(
  pageType: PageType,
  context: string,
  question: string,
  sessionId: string,
  conversationHistory: Array<{ role: 'user' | 'assistant'; content: string }>,
  callbacks: StreamCallbacks,
): AbortController {
  const controller = new AbortController();
  const startTime = Date.now();

  const messages = [
    ...conversationHistory,
    { role: 'user' as const, content: question },
  ];

  (async () => {
    try {
      const response = await fetch(`${API_BASE}/api/assistant/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          system: buildSystemPrompt(pageType, context),
          messages,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({ message: 'Unknown error' }));
        if (errorBody.error === 'free_limit_reached') {
          callbacks.onError('FREE_LIMIT_REACHED');
        } else {
          callbacks.onError(errorBody.message || errorBody.error || `Error (${response.status})`);
        }
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError('Failed to read response stream.');
        return;
      }
      await consumeStream(reader, callbacks, startTime);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      callbacks.onError(err instanceof Error ? err.message : 'Network error');
    }
  })();

  return controller;
}

/**
 * Send a question to Claude directly from the browser (user's own API key).
 */
export function askClaudeDirect(
  pageType: PageType,
  context: string,
  question: string,
  conversationHistory: Array<{ role: 'user' | 'assistant'; content: string }>,
  callbacks: StreamCallbacks,
): AbortController {
  const apiKey = getApiKey();
  if (!apiKey) {
    callbacks.onError('No API key configured. Please add your Claude API key in Settings.');
    return new AbortController();
  }

  const model = getModel();
  const controller = new AbortController();
  const startTime = Date.now();

  const messages = [
    ...conversationHistory,
    { role: 'user' as const, content: question },
  ];

  (async () => {
    try {
      const response = await fetch(ANTHROPIC_API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-api-key': apiKey,
          'anthropic-version': '2023-06-01',
          'anthropic-dangerous-direct-browser-access': 'true',
        },
        body: JSON.stringify({
          model,
          max_tokens: 4096,
          temperature: 0.3,
          system: buildSystemPrompt(pageType, context),
          messages,
          stream: true,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorBody = await response.text();
        if (response.status === 401) {
          callbacks.onError('Invalid API key. Please check your Claude API key in Settings.');
        } else if (response.status === 429) {
          callbacks.onError('Rate limited. Please wait a moment and try again.');
        } else {
          callbacks.onError(`API error (${response.status}): ${errorBody.slice(0, 200)}`);
        }
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError('Failed to read response stream.');
        return;
      }
      await consumeStream(reader, callbacks, startTime);
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;
      callbacks.onError(err instanceof Error ? err.message : 'Network error');
    }
  })();

  return controller;
}

/** The model name tag stored with free-tier QA entries */
export const FREE_MODEL_TAG = `free:${FREE_MODEL}`;
