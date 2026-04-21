/**
 * Convert an arbitrary title into a cross-OS-safe filename (without extension).
 *
 * Handles:
 * - Characters forbidden on Windows:  < > : " / \ | ? *
 * - Forward slash on Unix
 * - Control characters (0x00-0x1F)
 * - Leading/trailing whitespace and dots (Windows strips trailing dots)
 * - Collapses runs of separators
 * - Reserved Windows device names (CON, PRN, AUX, NUL, COM1-9, LPT1-9)
 * - Length cap (conservative: many filesystems allow 255, but we stay shorter)
 *
 * Returns a non-empty string; falls back to "video" if input reduces to nothing.
 */
export function safeFilename(title: string, maxLength = 120): string {
  if (!title) return 'video';

  let s = title;

  // Replace forbidden characters with space
  s = s.replace(/[<>:"/\\|?*\x00-\x1F]/g, ' ');
  // Replace smart quotes and other tricky Unicode punctuation with safe equivalents
  s = s.replace(/[\u2018\u2019\u2032]/g, "'");
  s = s.replace(/[\u201C\u201D\u2033]/g, '"').replace(/"/g, ''); // drop doublequotes entirely after normalizing
  s = s.replace(/[\u2013\u2014]/g, '-'); // en dash / em dash
  s = s.replace(/[\u2026]/g, '...'); // ellipsis

  // Collapse whitespace
  s = s.replace(/\s+/g, ' ').trim();

  // Strip leading/trailing dots (Windows strips trailing dots silently)
  s = s.replace(/^\.+|\.+$/g, '').trim();

  // Reserved Windows device names — prefix with underscore to neutralize
  const reserved = /^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i;
  if (reserved.test(s)) s = `_${s}`;

  // Truncate
  if (s.length > maxLength) {
    s = s.slice(0, maxLength).trim().replace(/[\s.-]+$/, '');
  }

  return s || 'video';
}
