import { useState, useEffect } from 'react';
import { fetchSurahs } from '../../api/quran';
import {
  createExplanation, getExplanations, getExplanation, updateExplanation,
  deleteExplanation, generateClosingReflection, generateAllExplanationTTS,
  getVoices,
} from '../../api/admin';
import type { ExplanationSegment, ExplanationListItem, Voice } from '../../api/admin';
import type { SurahInfo } from '../../types';
import SuggestRelatedModal from './SuggestRelatedModal';

export default function ExplanationBuilder() {
  // Surah data
  const [surahs, setSurahs] = useState<SurahInfo[]>([]);

  // Saved explanations list
  const [savedList, setSavedList] = useState<ExplanationListItem[]>([]);

  // Current explanation being edited
  const [currentId, setCurrentId] = useState<number | null>(null);
  const [title, setTitle] = useState('');
  const [segments, setSegments] = useState<ExplanationSegment[]>([]);
  const [status, setStatus] = useState<'draft' | 'ready'>('draft');

  // Verse group adder
  const [addChapter, setAddChapter] = useState(1);
  const [addAyahStart, setAddAyahStart] = useState(1);
  const [addAyahEnd, setAddAyahEnd] = useState(1);

  // Voice / TTS
  const [voices, setVoices] = useState<Voice[]>([]);
  const [voiceId, setVoiceId] = useState('');

  // UI state
  const [saving, setSaving] = useState(false);
  const [generatingClosing, setGeneratingClosing] = useState(false);
  const [generatingTTS, setGeneratingTTS] = useState(false);
  const [error, setError] = useState('');
  const [showSuggestModal, setShowSuggestModal] = useState(false);

  useEffect(() => {
    fetchSurahs().then(setSurahs);
    getExplanations().then(setSavedList).catch(() => {});
    getVoices().then((v) => {
      setVoices(v);
      if (v.length > 0) setVoiceId(v[0].voice_id);
    }).catch(() => {});
  }, []);

  const maxAyah = surahs.find((s) => s.number === addChapter)?.verse_count ?? 286;
  useEffect(() => {
    if (addAyahStart > maxAyah) setAddAyahStart(1);
    if (addAyahEnd > maxAyah) setAddAyahEnd(1);
    if (addAyahEnd < addAyahStart) setAddAyahEnd(addAyahStart);
  }, [addChapter, maxAyah, addAyahStart, addAyahEnd]);

  // Extract verse groups from segments
  const verseSegments = segments.filter((s) => s.type === 'verses');

  function getClosingSegment(): ExplanationSegment | undefined {
    return segments.find((s) => s.type === 'closing');
  }

  async function handleAddVerseGroup() {
    setError('');
    const vg = { chapter: addChapter, ayah_start: addAyahStart, ayah_end: addAyahEnd };

    if (currentId) {
      // Add to existing: rebuild with new group
      const allGroups = [
        ...verseSegments.map((s) => ({
          chapter: s.chapter!, ayah_start: s.ayah_start!, ayah_end: s.ayah_end!,
        })),
        vg,
      ];
      try {
        // Create a fresh explanation with all groups to get proper translations
        const closingText = getClosingSegment()?.text || '';
        const temp = await createExplanation(title || 'Untitled', allGroups);
        // Preserve closing text
        const newSegments = temp.segments.map((s) =>
          s.type === 'closing' ? { ...s, text: closingText } : s
        );
        const updated = await updateExplanation(currentId, { segments: newSegments });
        setSegments(updated.segments);
        setStatus(updated.status);
        refreshList();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to add verse group');
      }
    } else {
      // Create new explanation
      try {
        const expl = await createExplanation(title || 'Untitled', [vg]);
        setCurrentId(expl.id);
        setTitle(expl.title);
        setSegments(expl.segments);
        setStatus(expl.status);
        refreshList();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create explanation');
      }
    }
  }

  async function handleAddSuggestedVerse(chapter: number, ayah: number) {
    setError('');
    const vg = { chapter, ayah_start: ayah, ayah_end: ayah };

    if (currentId) {
      const allGroups = [
        ...verseSegments.map((s) => ({
          chapter: s.chapter!, ayah_start: s.ayah_start!, ayah_end: s.ayah_end!,
        })),
        vg,
      ];
      try {
        const closingText = getClosingSegment()?.text || '';
        const temp = await createExplanation(title || 'Untitled', allGroups);
        const newSegments = temp.segments.map((s) =>
          s.type === 'closing' ? { ...s, text: closingText } : s
        );
        const updated = await updateExplanation(currentId, { segments: newSegments });
        setSegments(updated.segments);
        setStatus(updated.status);
        refreshList();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to add verse');
      }
    } else {
      try {
        const expl = await createExplanation(title || 'Untitled', [vg]);
        setCurrentId(expl.id);
        setTitle(expl.title);
        setSegments(expl.segments);
        setStatus(expl.status);
        refreshList();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to create explanation');
      }
    }
    setShowSuggestModal(false);
  }

  function handleRemoveVerseGroup(index: number) {
    // Remove the verse segment and its preceding transition
    const newSegments = [...segments];
    // Find the actual index in segments array for this verse group
    let verseIdx = -1;
    let count = 0;
    for (let i = 0; i < newSegments.length; i++) {
      if (newSegments[i].type === 'verses') {
        if (count === index) { verseIdx = i; break; }
        count++;
      }
    }
    if (verseIdx < 0) return;
    // Remove the verse and its preceding transition
    const transIdx = verseIdx > 0 && newSegments[verseIdx - 1].type === 'transition' ? verseIdx - 1 : -1;
    if (transIdx >= 0) {
      newSegments.splice(transIdx, 2);
    } else {
      newSegments.splice(verseIdx, 1);
    }
    // If first remaining segment is not a transition, that's fine
    setSegments(newSegments);
    if (currentId) {
      updateExplanation(currentId, { segments: newSegments }).then((u) => {
        setStatus(u.status);
        refreshList();
      }).catch(() => {});
    }
  }

  function handleTransitionEdit(segIdx: number, text: string) {
    const newSegments = [...segments];
    newSegments[segIdx] = { ...newSegments[segIdx], text };
    // Clear TTS since text changed
    newSegments[segIdx].tts_filename = null;
    setSegments(newSegments);
  }

  function handleClosingEdit(text: string) {
    const newSegments = segments.map((s) =>
      s.type === 'closing' ? { ...s, text, tts_filename: null } : s
    );
    setSegments(newSegments);
  }

  async function handleSave() {
    if (!currentId) return;
    setSaving(true);
    setError('');
    try {
      const updated = await updateExplanation(currentId, {
        title: title || 'Untitled',
        segments,
      });
      setSegments(updated.segments);
      setStatus(updated.status);
      refreshList();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Save failed');
    } finally {
      setSaving(false);
    }
  }

  async function handleGenerateClosing() {
    setGeneratingClosing(true);
    setError('');
    try {
      const text = await generateClosingReflection(segments);
      handleClosingEdit(text);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate closing');
    } finally {
      setGeneratingClosing(false);
    }
  }

  async function handleGenerateAllTTS() {
    if (!currentId || !voiceId) return;
    // Save first to ensure segments are up to date
    setGeneratingTTS(true);
    setError('');
    try {
      await updateExplanation(currentId, { title, segments });
      const result = await generateAllExplanationTTS(currentId, voiceId);
      // Reload to get updated tts_filenames
      const updated = await getExplanation(currentId);
      setSegments(updated.segments);
      setStatus(updated.status);
      refreshList();
      if (result.status !== 'ready') {
        setError(`Generated ${result.generated} of ${result.total} segments. Some may be empty.`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'TTS generation failed');
    } finally {
      setGeneratingTTS(false);
    }
  }

  async function handleLoadExplanation(id: number) {
    setError('');
    try {
      const expl = await getExplanation(id);
      setCurrentId(expl.id);
      setTitle(expl.title);
      setSegments(expl.segments);
      setStatus(expl.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load');
    }
  }

  async function handleDeleteExplanation(id: number) {
    setError('');
    try {
      await deleteExplanation(id);
      if (currentId === id) {
        setCurrentId(null);
        setTitle('');
        setSegments([]);
        setStatus('draft');
      }
      refreshList();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete');
    }
  }

  function handleNew() {
    setCurrentId(null);
    setTitle('');
    setSegments([]);
    setStatus('draft');
    setError('');
  }

  function refreshList() {
    getExplanations().then(setSavedList).catch(() => {});
  }

  // First verse group for suggesting related verses
  const firstVerse = verseSegments[0];

  return (
    <div>
      <h1 className="text-xl font-semibold text-stone-800 mb-6">Verse Explanations</h1>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Editor (2 cols) */}
        <div className="lg:col-span-2 space-y-5">
          {/* Title */}
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Explanation title..."
              className="flex-1 px-3 py-2 rounded-lg border border-stone-300 text-sm focus:outline-none focus:ring-2 focus:ring-stone-400"
            />
            <span className={`text-xs px-2 py-1 rounded-full ${
              status === 'ready'
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-amber-100 text-amber-700'
            }`}>
              {status}
            </span>
            {currentId && (
              <button onClick={handleNew} className="text-xs text-blue-500 hover:underline cursor-pointer">
                New
              </button>
            )}
          </div>

          {/* Segments display */}
          {segments.length > 0 && (
            <div className="space-y-2">
              {segments.map((seg, idx) => {
                if (seg.type === 'transition') {
                  return (
                    <div key={idx} className="flex items-center gap-2">
                      <span className="text-xs text-stone-400 w-16 flex-shrink-0">Transition</span>
                      <input
                        type="text"
                        value={seg.text || ''}
                        onChange={(e) => handleTransitionEdit(idx, e.target.value)}
                        className="flex-1 px-2 py-1.5 rounded border border-stone-200 text-sm text-stone-600 italic focus:outline-none focus:ring-1 focus:ring-stone-400"
                      />
                      {seg.tts_filename && <span className="text-xs text-emerald-500">TTS</span>}
                    </div>
                  );
                }
                if (seg.type === 'verses') {
                  const vIdx = verseSegments.indexOf(seg);
                  return (
                    <div key={idx} className="rounded-lg border border-stone-200 bg-white p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-stone-800">{seg.ref}</span>
                        <div className="flex items-center gap-2">
                          {seg.tts_filename && <span className="text-xs text-emerald-500">TTS</span>}
                          <button
                            onClick={() => handleRemoveVerseGroup(vIdx)}
                            className="text-xs text-red-400 hover:text-red-600 cursor-pointer"
                          >
                            Remove
                          </button>
                        </div>
                      </div>
                      <p className="text-sm text-stone-500 leading-relaxed">
                        {seg.translation}
                      </p>
                    </div>
                  );
                }
                if (seg.type === 'closing') {
                  return (
                    <div key={idx} className="mt-4">
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-sm font-medium text-stone-700">Closing Reflection</label>
                        <div className="flex items-center gap-2">
                          {seg.tts_filename && <span className="text-xs text-emerald-500">TTS</span>}
                          <button
                            onClick={handleGenerateClosing}
                            disabled={generatingClosing || verseSegments.length === 0}
                            className="text-xs text-indigo-600 hover:text-indigo-800 disabled:opacity-50 cursor-pointer"
                          >
                            {generatingClosing ? 'Generating...' : seg.text ? 'Regenerate' : 'Generate with AI'}
                          </button>
                        </div>
                      </div>
                      <textarea
                        value={seg.text || ''}
                        onChange={(e) => handleClosingEdit(e.target.value)}
                        placeholder="A profound closing reflection..."
                        rows={3}
                        className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-stone-400 resize-y"
                      />
                    </div>
                  );
                }
                return null;
              })}
            </div>
          )}

          {/* Add verse group */}
          <div className="rounded-lg border border-dashed border-stone-300 p-4">
            <p className="text-sm font-medium text-stone-700 mb-3">Add Verse Group</p>
            <div className="flex flex-wrap items-end gap-3">
              <div>
                <label className="block text-xs text-stone-500 mb-1">Surah</label>
                <select
                  value={addChapter}
                  onChange={(e) => setAddChapter(Number(e.target.value))}
                  className="px-2 py-1.5 rounded border border-stone-300 text-sm bg-white focus:outline-none"
                >
                  {surahs.map((s) => (
                    <option key={s.number} value={s.number}>
                      {s.number}. {s.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-stone-500 mb-1">From Ayah</label>
                <select
                  value={addAyahStart}
                  onChange={(e) => {
                    const v = Number(e.target.value);
                    setAddAyahStart(v);
                    if (addAyahEnd < v) setAddAyahEnd(v);
                  }}
                  className="px-2 py-1.5 rounded border border-stone-300 text-sm bg-white focus:outline-none w-20"
                >
                  {Array.from({ length: maxAyah }, (_, i) => i + 1).map((a) => (
                    <option key={a} value={a}>{a}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs text-stone-500 mb-1">To Ayah</label>
                <select
                  value={addAyahEnd}
                  onChange={(e) => setAddAyahEnd(Number(e.target.value))}
                  className="px-2 py-1.5 rounded border border-stone-300 text-sm bg-white focus:outline-none w-20"
                >
                  {Array.from({ length: maxAyah - addAyahStart + 1 }, (_, i) => addAyahStart + i).map((a) => (
                    <option key={a} value={a}>{a}</option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleAddVerseGroup}
                className="px-4 py-1.5 rounded-lg bg-stone-800 text-white text-sm font-medium hover:bg-stone-700 transition-colors cursor-pointer"
              >
                Add
              </button>
              {firstVerse && (
                <button
                  onClick={() => setShowSuggestModal(true)}
                  className="px-4 py-1.5 rounded-lg bg-indigo-700 text-white text-sm font-medium hover:bg-indigo-600 transition-colors cursor-pointer"
                >
                  Suggest Related
                </button>
              )}
            </div>
          </div>

          {/* TTS Generation */}
          {currentId && segments.length > 0 && (
            <div className="flex items-center gap-3 pt-2 border-t border-stone-100">
              <select
                value={voiceId}
                onChange={(e) => setVoiceId(e.target.value)}
                className="px-2 py-1.5 rounded border border-stone-300 text-sm bg-white focus:outline-none"
              >
                {voices.map((v) => (
                  <option key={v.id} value={v.voice_id}>{v.name}</option>
                ))}
              </select>
              <button
                onClick={handleGenerateAllTTS}
                disabled={generatingTTS || !voiceId}
                className="px-4 py-1.5 rounded-lg bg-emerald-700 text-white text-sm font-medium hover:bg-emerald-600 disabled:opacity-50 transition-colors cursor-pointer"
              >
                {generatingTTS ? 'Generating TTS...' : 'Generate All TTS'}
              </button>
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-1.5 rounded-lg border border-stone-300 text-sm font-medium text-stone-700 hover:bg-stone-50 disabled:opacity-50 transition-colors cursor-pointer"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>
            </div>
          )}

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}
        </div>

        {/* Right: Saved explanations list */}
        <div>
          <h2 className="text-sm font-medium text-stone-700 mb-2">
            Saved Explanations ({savedList.length})
          </h2>
          {savedList.length === 0 ? (
            <p className="text-sm text-stone-400">No explanations yet.</p>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {savedList.map((item) => (
                <div
                  key={item.id}
                  className={`rounded-lg border p-3 cursor-pointer transition-colors ${
                    currentId === item.id
                      ? 'border-stone-800 bg-stone-50'
                      : 'border-stone-200 bg-white hover:border-stone-400'
                  }`}
                  onClick={() => handleLoadExplanation(item.id)}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-stone-800 truncate">{item.title}</p>
                    <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                      item.status === 'ready'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-amber-100 text-amber-700'
                    }`}>
                      {item.status}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-stone-400">
                      {item.verse_count} verse{item.verse_count !== 1 ? 's' : ''}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteExplanation(item.id); }}
                      className="text-xs text-red-400 hover:text-red-600 cursor-pointer"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Suggest Related Modal */}
      {showSuggestModal && firstVerse && (
        <SuggestRelatedModal
          seedChapter={firstVerse.chapter!}
          seedAyah={firstVerse.ayah_start!}
          onSelect={handleAddSuggestedVerse}
          onClose={() => setShowSuggestModal(false)}
        />
      )}
    </div>
  );
}
