/**
 * Backend API calls for the "Ask the Quran" assistant Q&A history.
 */

import { API_BASE } from './quran';
import { getSessionId } from '../utils/assistant-storage';

export interface QAEntry {
  id: number;
  question: string;
  answer: string;
  model_used: string;
  created_at: string;
}

export interface SaveResult {
  ok: boolean;
  id?: number;
  moderated?: boolean;
  reworded_question?: string;
  answer?: string;
  reason?: string;
}

export async function saveQA(params: {
  pageType: string;
  pageKey: string;
  question: string;
  answer: string;
  contextSummary: string;
  modelUsed: string;
  responseTimeMs: number;
  threadId?: number | null;
  allQuestions?: string[];
}): Promise<SaveResult> {
  try {
    const body: Record<string, unknown> = {
      session_id: getSessionId(),
      page_type: params.pageType,
      page_key: params.pageKey,
      question: params.question,
      answer: params.answer,
      context_summary: params.contextSummary,
      model_used: params.modelUsed,
      response_time_ms: params.responseTimeMs,
    };
    if (params.threadId) {
      body.thread_id = params.threadId;
    }
    if (params.allQuestions && params.allQuestions.length > 1) {
      body.all_questions = params.allQuestions;
    }

    const res = await fetch(`${API_BASE}/api/assistant/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      return await res.json();
    }
    return { ok: false };
  } catch {
    // Silently fail — history saving is not critical
    return { ok: false };
  }
}

export interface UsageInfo {
  used: number;
  limit: number;
}

export async function fetchUsage(sessionId: string): Promise<UsageInfo> {
  try {
    const res = await fetch(`${API_BASE}/api/assistant/usage?session_id=${encodeURIComponent(sessionId)}`);
    if (!res.ok) return { used: 0, limit: 3 };
    return await res.json();
  } catch {
    return { used: 0, limit: 3 };
  }
}

export async function fetchHistory(
  pageType: string,
  pageKey: string,
  limit = 50,
): Promise<QAEntry[]> {
  try {
    const params = new URLSearchParams({
      page_type: pageType,
      page_key: pageKey,
      limit: String(limit),
    });
    const res = await fetch(`${API_BASE}/api/assistant/history?${params}`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.history || [];
  } catch {
    return [];
  }
}
