// Mirror of the backend METER_REGISTRY: maps a raw poetry_poems.meter string
// (الطويل, مجزوء الكامل, …) to the Latin slug of the base meter whose teaching
// page it belongs on. One page per base meter; variants fold in. Kept in sync
// with roots/backend/app.py by hand (small, static).
export interface MeterRegistryEntry {
  key: string;
  ar: string;
  en: string;
  variants: string[];
}

export const METER_REGISTRY: MeterRegistryEntry[] = [
  { key: 'tawil', ar: 'الطويل', en: 'Ṭawīl', variants: ['مجزوء الطويل'] },
  { key: 'wafir', ar: 'الوافر', en: 'Wāfir', variants: ['مجزوء الوافر'] },
  { key: 'basit', ar: 'البسيط', en: 'Basīṭ', variants: ['مجزوء البسيط', 'مخلع البسيط'] },
  { key: 'kamil', ar: 'الكامل', en: 'Kāmil', variants: ['مجزوء الكامل', 'أحذ الكامل'] },
  { key: 'mutaqarib', ar: 'المتقارب', en: 'Mutaqārib', variants: [] },
  { key: 'khafif', ar: 'الخفيف', en: 'Khafīf', variants: ['مجزوء الخفيف'] },
  { key: 'rajaz', ar: 'الرجز', en: 'Rajaz', variants: ['مجزوء الرجز', 'مشطور الرجز'] },
  { key: 'ramal', ar: 'الرمل', en: 'Ramal', variants: ['مجزوء الرمل'] },
  { key: 'sari', ar: 'السريع', en: 'Sarīʿ', variants: [] },
  { key: 'munsarih', ar: 'المنسرح', en: 'Munsariḥ', variants: [] },
  { key: 'madid', ar: 'المديد', en: 'Madīd', variants: [] },
  { key: 'hazaj', ar: 'الهزج', en: 'Hazaj', variants: [] },
  { key: 'mujtathth', ar: 'المجتث', en: 'Mujtathth', variants: [] },
];

const VALUE_TO_KEY = new Map<string, string>();
for (const m of METER_REGISTRY) {
  VALUE_TO_KEY.set(m.ar, m.key);
  for (const v of m.variants) VALUE_TO_KEY.set(v, m.key);
}

/** The base-meter slug for a raw meter string, or null if unrecognised. */
export function meterKeyForArabic(value?: string | null): string | null {
  if (!value) return null;
  return VALUE_TO_KEY.get(value.trim()) ?? null;
}
