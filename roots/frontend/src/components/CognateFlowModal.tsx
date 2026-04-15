import { useEffect, useRef } from 'react';
import type { CognateDerivative } from '../types';
import CognateFlowChart from './CognateFlowChart';

interface Props {
  derivatives: CognateDerivative[];
  rootTransliteration: string;
  concept: string;
  onClose: () => void;
}

export default function CognateFlowModal({
  derivatives,
  rootTransliteration,
  concept,
  onClose,
}: Props) {
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKey);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
      onClick={(e) => {
        if (e.target === backdropRef.current) onClose();
      }}
    >
      <div className="bg-white rounded-2xl shadow-2xl max-w-3xl max-h-[90vh] overflow-auto w-full">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between px-5 py-4 border-b border-stone-200 bg-white/95 backdrop-blur-sm rounded-t-2xl">
          <div>
            <h2 className="text-lg font-bold text-stone-800">
              Language Evolution: <span className="text-indigo-600">{rootTransliteration}</span>
            </h2>
            <p className="text-sm text-stone-500 mt-0.5">
              Tracing <span className="font-medium">"{concept}"</span> across Semitic languages
            </p>
          </div>
          <button
            onClick={onClose}
            className="ml-4 p-2 rounded-lg text-stone-400 hover:text-stone-600 hover:bg-stone-100 transition-colors cursor-pointer"
            aria-label="Close"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </button>
        </div>

        {/* Chart */}
        <div className="p-5">
          <CognateFlowChart derivatives={derivatives} />
        </div>
      </div>
    </div>
  );
}
