import type {
  CurriculumResponse,
  LearningRootDetail,
  ReviewVersesResponse,
  AskResponse,
} from '../types/learning';

const BASE = '/api';

export async function fetchCurriculum(): Promise<CurriculumResponse> {
  const res = await fetch(`${BASE}/learning/curriculum`);
  if (!res.ok) throw new Error('Failed to load curriculum');
  return res.json();
}

export async function fetchLearningRoot(rootBw: string): Promise<LearningRootDetail> {
  const res = await fetch(`${BASE}/learning/root/${encodeURIComponent(rootBw)}`);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? 'Root not found in curriculum');
  }
  return res.json();
}

export async function fetchReviewVerses(
  rootBw: string,
  exclude: string[] = [],
): Promise<ReviewVersesResponse> {
  const params = exclude.length ? `?exclude=${exclude.join(',')}` : '';
  const res = await fetch(
    `${BASE}/learning/root/${encodeURIComponent(rootBw)}/review-verses${params}`,
  );
  if (!res.ok) throw new Error('Failed to load review verses');
  return res.json();
}

export async function askAboutRoot(
  rootBw: string,
  question: string,
): Promise<AskResponse> {
  const res = await fetch(`${BASE}/learning/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ root_bw: rootBw, question }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error ?? 'LLM unavailable');
  }
  return res.json();
}
