import type { LearningProgress, RootProgress } from '../types/learning';
import { createInitialRootProgress, nextDueDate, isMastered } from './spaced-repetition';

const STORAGE_KEY = 'quranExplorer.learning';

function defaultProgress(): LearningProgress {
  return {
    version: 1,
    currentUnit: 1,
    rootProgress: {},
    reviewQueue: [],
    stats: {
      totalRootsLearned: 0,
      totalReviewsDone: 0,
      currentStreak: 0,
      lastActivityDate: '',
    },
  };
}

export function loadProgress(): LearningProgress {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultProgress();
    const parsed = JSON.parse(raw) as LearningProgress;
    if (parsed.version !== 1) return defaultProgress();
    return parsed;
  } catch {
    return defaultProgress();
  }
}

export function saveProgress(progress: LearningProgress): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
  } catch {
    // localStorage full or disabled (e.g. private browsing) — silently fail
  }
}

export function getRootProgress(progress: LearningProgress, rootBw: string): RootProgress {
  return progress.rootProgress[rootBw] || createInitialRootProgress();
}

export function updateRootProgress(
  progress: LearningProgress,
  rootBw: string,
  updates: Partial<RootProgress>,
): LearningProgress {
  const existing = getRootProgress(progress, rootBw);
  const updated = { ...existing, ...updates };

  // Check mastery
  if (isMastered(updated) && updated.status !== 'mastered') {
    updated.status = 'mastered';
  }

  const next = {
    ...progress,
    rootProgress: {
      ...progress.rootProgress,
      [rootBw]: updated,
    },
  };

  return next;
}

export function markRootLearned(
  progress: LearningProgress,
  rootBw: string,
  quality: number,
  verseRef: string,
): LearningProgress {
  const rp = getRootProgress(progress, rootBw);
  const now = new Date().toISOString();
  const today = now.split('T')[0];

  const isNew = rp.status === 'unseen';

  // Update root progress
  let next = updateRootProgress(progress, rootBw, {
    status: quality >= 3 ? 'reviewing' : 'learning',
    firstSeen: rp.firstSeen || now,
    lastReviewed: now,
    versesExposed: [...new Set([...rp.versesExposed, verseRef])],
    selfRating: quality,
    sm2: {
      ...rp.sm2,
      interval: quality >= 3 ? 1 : 1,
      repetition: quality >= 3 ? 1 : 0,
      easeFactor: rp.sm2.easeFactor,
    },
  });

  // Add to review queue if not already there
  const inQueue = next.reviewQueue.some((r) => r.rootBw === rootBw);
  if (!inQueue) {
    const dueDate = nextDueDate(next.rootProgress[rootBw].sm2);
    next = {
      ...next,
      reviewQueue: [...next.reviewQueue, { rootBw, dueDate }],
    };
  }

  // Update stats
  const streak = next.stats.lastActivityDate === today
    ? next.stats.currentStreak
    : isConsecutiveDay(next.stats.lastActivityDate, today)
      ? next.stats.currentStreak + 1
      : 1;

  next = {
    ...next,
    stats: {
      ...next.stats,
      totalRootsLearned: isNew
        ? next.stats.totalRootsLearned + 1
        : next.stats.totalRootsLearned,
      lastActivityDate: today,
      currentStreak: streak,
    },
  };

  return next;
}

export function updateReviewResult(
  progress: LearningProgress,
  rootBw: string,
  newSM2: import('../types/learning').SM2State,
  verseRef: string,
): LearningProgress {
  const rp = getRootProgress(progress, rootBw);
  const now = new Date().toISOString();
  const today = now.split('T')[0];

  let next = updateRootProgress(progress, rootBw, {
    lastReviewed: now,
    versesExposed: [...new Set([...rp.versesExposed, verseRef])],
    sm2: newSM2,
  });

  // Update the review queue with new due date
  const dueDate = nextDueDate(newSM2);
  next = {
    ...next,
    reviewQueue: next.reviewQueue.map((r) =>
      r.rootBw === rootBw ? { ...r, dueDate } : r,
    ),
    stats: {
      ...next.stats,
      totalReviewsDone: next.stats.totalReviewsDone + 1,
      lastActivityDate: today,
      currentStreak: next.stats.lastActivityDate === today
        ? next.stats.currentStreak
        : isConsecutiveDay(next.stats.lastActivityDate, today)
          ? next.stats.currentStreak + 1
          : 1,
    },
  };

  return next;
}

/**
 * Get mastery percentage for a unit.
 */
export function getUnitMastery(
  progress: LearningProgress,
  rootBws: string[],
): number {
  if (rootBws.length === 0) return 0;
  const learned = rootBws.filter((r) => {
    const rp = progress.rootProgress[r];
    return rp && rp.status !== 'unseen';
  }).length;
  return Math.round((learned / rootBws.length) * 100);
}

function isConsecutiveDay(prev: string, current: string): boolean {
  if (!prev) return false;
  const p = new Date(prev);
  const c = new Date(current);
  const diff = c.getTime() - p.getTime();
  return diff > 0 && diff <= 86400000 * 1.5; // Within ~1.5 days
}
