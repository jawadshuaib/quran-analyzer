import type { SM2State, RootProgress, ReviewItem } from '../types/learning';

/**
 * SM-2 spaced repetition algorithm.
 *
 * quality: 0 = Again, 3 = Hard, 4 = Good, 5 = Easy
 */
export function updateSM2(sm2: SM2State, quality: number): SM2State {
  const next = { ...sm2 };

  if (quality >= 3) {
    // Successful review
    if (next.repetition === 0) {
      next.interval = 1;
    } else if (next.repetition === 1) {
      next.interval = 6;
    } else {
      next.interval = Math.round(next.interval * next.easeFactor);
    }
    next.repetition += 1;
    next.easeFactor = Math.max(
      1.3,
      next.easeFactor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    );
  } else {
    // Failed review — reset
    next.repetition = 0;
    next.interval = 1;
    // Don't change easeFactor on failure (SM-2 spec)
  }

  return next;
}

export function createInitialSM2(): SM2State {
  return { interval: 1, repetition: 0, easeFactor: 2.5 };
}

export function createInitialRootProgress(): RootProgress {
  return {
    status: 'unseen',
    firstSeen: '',
    lastReviewed: '',
    versesExposed: [],
    selfRating: 0,
    sm2: createInitialSM2(),
  };
}

/**
 * Calculate the next due date for a review item.
 */
export function nextDueDate(sm2: SM2State, fromDate?: string): string {
  const base = fromDate ? new Date(fromDate) : new Date();
  base.setDate(base.getDate() + sm2.interval);
  return base.toISOString().split('T')[0]; // YYYY-MM-DD
}

/**
 * Check if a review item is due today or earlier.
 */
export function isDue(item: ReviewItem): boolean {
  const today = new Date().toISOString().split('T')[0];
  return item.dueDate <= today;
}

/**
 * Check if a root is "mastered" (5+ successful reviews with good ease factor).
 */
export function isMastered(progress: RootProgress): boolean {
  return progress.sm2.repetition >= 5 && progress.sm2.easeFactor >= 2.0;
}

/**
 * Get the count of roots due for review today.
 */
export function getDueCount(queue: ReviewItem[]): number {
  return queue.filter(isDue).length;
}

/**
 * Quality rating from self-assessment labels.
 */
export function selfAssessmentToQuality(label: 'new' | 'recognized' | 'knew'): number {
  switch (label) {
    case 'new': return 1;
    case 'recognized': return 3;
    case 'knew': return 5;
  }
}

export function reviewRatingToQuality(label: 'again' | 'hard' | 'good' | 'easy'): number {
  switch (label) {
    case 'again': return 0;
    case 'hard': return 3;
    case 'good': return 4;
    case 'easy': return 5;
  }
}
