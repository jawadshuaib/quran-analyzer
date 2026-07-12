import type { VerseExegesisData } from '../types/index.ts';
import NoteMarkdown from './NoteMarkdown.tsx';

/**
 * Compact exegesis card for the extension popup — the approved teacher-voice
 * commentary the main site shows under a verse's translation notes. Violet
 * like the Translation Notes card so the two read as one family.
 */
export default function ExegesisSection({ data }: { data: VerseExegesisData }) {
  return (
    <div className="mt-2 rounded-lg bg-violet-50 border border-violet-100 p-3">
      <div className="text-xs font-medium text-violet-600 mb-1">Exegesis</div>
      <NoteMarkdown
        text={data.exegesis_markdown}
        className="text-xs text-violet-900/90 leading-relaxed"
      />
    </div>
  );
}
