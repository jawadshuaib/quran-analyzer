import { useState, useEffect, useRef, useCallback } from 'react';
import { askClaudeDirect, askClaudeProxy, FREE_MODEL_TAG, type PageType } from '../api/claude';
import { saveQA, fetchHistory, fetchUsage, type QAEntry } from '../api/assistant';
import { getApiKey, getModel, getSessionId } from '../utils/assistant-storage';

interface Props {
  pageType: PageType;
  pageKey: string;
  contextGatherer: () => Promise<string>;
  /** Open the panel automatically on mount. Used by the reader-page
   *  flow on /read/<surah> — the user clicks an "Ask about <verse>"
   *  pill, the parent freezes the anchor verse into props, and we
   *  mount AskAssistant already-open so the user doesn't have to
   *  click a second time. */
  defaultOpen?: boolean;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

/** Max conversation turns (user+assistant pairs) to send to Claude to avoid exceeding context limits */
const MAX_HISTORY_TURNS = 10;

/** Auto-clear conversation after 1 hour of inactivity */
const THREAD_TIMEOUT_MS = 60 * 60 * 1000;

/** localStorage key for tracking which Q&A entries the user has seen */
function getSeenKey(pageType: string, pageKey: string): string {
  return `qa_seen_${pageType}_${pageKey}`;
}

function getLastSeenId(pageType: string, pageKey: string): number {
  try {
    return parseInt(localStorage.getItem(getSeenKey(pageType, pageKey)) || '0', 10);
  } catch { return 0; }
}

function markAsSeen(pageType: string, pageKey: string, latestId: number): void {
  try { localStorage.setItem(getSeenKey(pageType, pageKey), String(latestId)); } catch { /* ignore */ }
}

/** Strip HTML tags and script-like content from user input */
function sanitizeInput(text: string): string {
  return text
    .replace(/<[^>]*>/g, '')           // strip HTML tags
    .replace(/javascript\s*:/gi, '')   // strip javascript: URIs
    .replace(/on\w+\s*=/gi, '')        // strip event handlers like onclick=
    .trim();
}

export default function AskAssistant({
  pageType,
  pageKey,
  contextGatherer,
  defaultOpen = false,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);
  const [tab, setTab] = useState<'ask' | 'history'>('ask');
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [error, setError] = useState('');
  const [history, setHistory] = useState<QAEntry[]>([]);
  const [historyLoaded, setHistoryLoaded] = useState(false);
  const [expandedHistoryId, setExpandedHistoryId] = useState<number | null>(null);
  const [freeUsed, setFreeUsed] = useState(0);
  const [freeLimit, setFreeLimit] = useState(3);
  const [usageLoaded, setUsageLoaded] = useState(false);
  const [qaFlash, setQaFlash] = useState(false);
  const threadIdRef = useRef<number | null>(null);
  const inflightSaveRef = useRef<Promise<unknown> | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const contextRef = useRef<string>('');
  const streamingRef = useRef(false);
  const rafRef = useRef<number | null>(null);
  const latestStreamRef = useRef('');
  const lastMessageTimeRef = useRef<number>(0);

  const hasApiKey = !!getApiKey();
  const freeRemaining = freeLimit - freeUsed;
  const canAskFree = freeRemaining > 0;
  // User can ask if they have their own key OR if they have free questions left
  const canAsk = hasApiKey || canAskFree;

  // Clear stale conversation if last message was over 1 hour ago
  const clearIfStale = useCallback(() => {
    if (messages.length > 0 && lastMessageTimeRef.current > 0) {
      if (Date.now() - lastMessageTimeRef.current > THREAD_TIMEOUT_MS) {
        setMessages([]);
        setStreamText('');
        setError('');
        contextRef.current = '';
        threadIdRef.current = null;
        inflightSaveRef.current = null;

        lastMessageTimeRef.current = 0;
      }
    }
  }, [messages.length]);

  // Reset state when page changes
  useEffect(() => {
    contextRef.current = '';
    threadIdRef.current = null;
    inflightSaveRef.current = null;
    setMessages([]);
    setStreamText('');
    setError('');
    setHistoryLoaded(false);
    setExpandedHistoryId(null);
    setTab('ask');
    lastMessageTimeRef.current = 0;
  }, [pageType, pageKey]);

  // Load usage count on mount
  useEffect(() => {
    if (!usageLoaded) {
      fetchUsage(getSessionId()).then((u) => {
        setFreeUsed(u.used);
        setFreeLimit(u.limit);
        setUsageLoaded(true);
      });
    }
  }, [usageLoaded]);

  // Scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: messages.length > 0 && !streamingRef.current ? 'smooth' : 'auto' });
  }, [messages]);

  // Streaming scroll — throttled via RAF
  useEffect(() => {
    if (streamText && streamingRef.current) {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'auto' });
      });
    }
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [streamText]);

  // Auto-clear stale conversation when panel opens
  useEffect(() => {
    if (open) clearIfStale();
  }, [open, clearIfStale]);

  // Eagerly check if history exists (even when closed, to show glow indicator)
  useEffect(() => {
    if (!historyLoaded) {
      fetchHistory(pageType, pageKey)
        .then((h) => {
          setHistory(h);
          setHistoryLoaded(true);
        })
        .catch(() => {
          setHistory([]);
          setHistoryLoaded(true);
        });
    }
  }, [historyLoaded, pageType, pageKey]);

  const hasHistory = historyLoaded && history.length > 0;
  const latestQAId = hasHistory ? Math.max(...history.map(h => h.id)) : 0;
  const hasUnreadQA = hasHistory && latestQAId > getLastSeenId(pageType, pageKey);

  // Flash the Q&A tab when panel opens and there's unread content
  useEffect(() => {
    if (open && hasUnreadQA) {
      setQaFlash(true);
      const timer = setTimeout(() => setQaFlash(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [open, hasUnreadQA]);

  // Mark as read when user views the Q&A tab
  useEffect(() => {
    if (tab === 'history' && hasHistory && latestQAId > 0) {
      markAsSeen(pageType, pageKey, latestQAId);
    }
  }, [tab, hasHistory, latestQAId, pageType, pageKey]);

  const handleSubmit = useCallback(async () => {
    if (!input.trim() || streaming) return;

    // Auto-clear stale thread before submitting
    clearIfStale();

    const trimmed = sanitizeInput(input);

    // Silent input validation — only show error when hit
    const wordCount = trimmed.split(/\s+/).filter(Boolean).length;
    if (trimmed.length < 7 || wordCount < 2) {
      setError('Please enter a complete question.');
      return;
    }
    if (trimmed.length > 500) {
      setError('Your question is too long. Please keep it concise.');
      return;
    }

    // Determine mode: own key or free proxy
    const usingOwnKey = hasApiKey;
    if (!usingOwnKey && !canAskFree) {
      // Out of free questions — show prompt
      setError('FREE_LIMIT_REACHED');
      return;
    }

    const question = trimmed;
    setInput('');
    setError('');
    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setStreaming(true);
    streamingRef.current = true;
    setStreamText('');
    latestStreamRef.current = '';

    // Gather context on first question
    if (!contextRef.current) {
      try {
        contextRef.current = await contextGatherer();
      } catch {
        contextRef.current = `[Context for ${pageType} ${pageKey}]`;
      }
    }

    // Sliding window: only send the most recent turns
    const recentMessages = messages.slice(-(MAX_HISTORY_TURNS * 2));
    const conversationHistory = recentMessages
      .filter((m) => !m.content.endsWith('[cancelled]'))
      .map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }));

    const modelTag = usingOwnKey ? getModel() : FREE_MODEL_TAG;

    const callbacks = {
      onToken: (text: string) => {
        latestStreamRef.current += text;
        setStreamText(latestStreamRef.current);
      },
      onDone: (text: string, responseTimeMs: number) => {
        setStreaming(false);
        streamingRef.current = false;
        setStreamText('');
        latestStreamRef.current = '';
        setMessages((prev) => [...prev, { role: 'assistant', content: text }]);
        lastMessageTimeRef.current = Date.now();

        // Increment free usage counter locally
        if (!usingOwnKey) {
          setFreeUsed((prev) => prev + 1);
        }

        // Collect all user questions in this thread (previous + current)
        const allQuestions = [
          ...messages.filter((m) => m.role === 'user').map((m) => m.content),
          question,
        ];

        // Serialize saves: wait for any in-flight save to finish first (Fix 2)
        const contextSummary = contextRef.current.slice(0, 200) + '...';
        const doSave = async () => {
          if (inflightSaveRef.current) {
            try { await inflightSaveRef.current; } catch { /* ignore */ }
          }
          const result = await saveQA({
            pageType,
            pageKey,
            question,
            answer: text,
            contextSummary,
            modelUsed: modelTag,
            responseTimeMs,
            threadId: threadIdRef.current,  // read from ref, not closure (Fix 1)
            allQuestions,
          });
          if (result.ok && result.id) {
            threadIdRef.current = result.id;  // synchronous update (Fix 1)

          }
          // Refresh history list after every successful save (Fix 4)
          if (result.ok) {
            try {
              const h = await fetchHistory(pageType, pageKey);
              setHistory(h);
              setHistoryLoaded(true);
            } catch { /* ignore */ }
          }
        };
        const savePromise = doSave();
        inflightSaveRef.current = savePromise;
      },
      onError: (errMsg: string) => {
        setStreaming(false);
        streamingRef.current = false;
        setStreamText('');
        latestStreamRef.current = '';
        setError(errMsg);
      },
    };

    if (usingOwnKey) {
      abortRef.current = askClaudeDirect(
        pageType, contextRef.current, question, conversationHistory, callbacks,
      );
    } else {
      abortRef.current = askClaudeProxy(
        pageType, contextRef.current, question, getSessionId(), conversationHistory, callbacks,
      );
    }
  }, [input, streaming, hasApiKey, canAskFree, messages, pageType, pageKey, contextGatherer, clearIfStale]);

  const handleCancel = () => {
    abortRef.current?.abort();
    setStreaming(false);
    streamingRef.current = false;
    if (latestStreamRef.current) {
      setMessages((prev) => [...prev, { role: 'assistant', content: latestStreamRef.current + ' [cancelled]' }]);
      setStreamText('');
      latestStreamRef.current = '';
    }
  };

  const handleClearConversation = () => {
    setMessages([]);
    setStreamText('');
    setError('');
    contextRef.current = '';
    threadIdRef.current = null;
    inflightSaveRef.current = null;
  };

  // Auto-link verse references (only valid Quran ranges)
  function renderText(text: string) {
    const parts = text.split(/(\b\d{1,3}:\d{1,3}\b)/g);
    return parts.map((part, i) => {
      const match = part.match(/^(\d{1,3}):(\d{1,3})$/);
      if (match) {
        const s = parseInt(match[1], 10);
        const a = parseInt(match[2], 10);
        if (s >= 1 && s <= 114 && a >= 1 && a <= 286) {
          return (
            <a key={i} href={`/verse/${part}`} target="_blank" rel="noopener noreferrer"
              className="text-indigo-600 hover:text-indigo-800 font-medium hover:underline">
              {part}
            </a>
          );
        }
      }
      return <span key={i}>{part}</span>;
    });
  }

  function renderFormatted(text: string) {
    const lines = text.split('\n');
    return lines.map((line, li) => {
      if (/^#{2,3}\s/.test(line)) {
        const content = line.replace(/^#{2,3}\s+/, '');
        return <p key={li} className="font-semibold text-stone-900 mt-3 mb-1 text-sm">{renderText(content)}</p>;
      }
      if (/^[\-\*]\s/.test(line)) {
        const content = line.replace(/^[\-\*]\s+/, '');
        return (
          <div key={li} className="flex gap-1.5 ml-1 mt-0.5">
            <span className="text-stone-400 shrink-0">•</span>
            <span>{renderBold(content)}</span>
          </div>
        );
      }
      if (/^\d+\.\s/.test(line)) {
        const num = line.match(/^(\d+)\./)?.[1];
        const content = line.replace(/^\d+\.\s+/, '');
        return (
          <div key={li} className="flex gap-1.5 ml-1 mt-0.5">
            <span className="text-stone-400 shrink-0">{num}.</span>
            <span>{renderBold(content)}</span>
          </div>
        );
      }
      if (!line.trim()) return <div key={li} className="h-2" />;
      return <p key={li} className={li > 0 ? 'mt-0.5' : ''}>{renderBold(line)}</p>;
    });
  }

  function renderBold(text: string) {
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={i} className="font-semibold text-stone-900">{renderText(part.slice(2, -2))}</strong>;
      }
      return <span key={i}>{renderText(part)}</span>;
    });
  }

  function handleCopy(text: string) {
    navigator.clipboard.writeText(text).catch(() => {});
  }

  // --- Free limit reached banner ---
  const freeLimitBanner = (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm space-y-2">
      <p className="text-amber-800 font-medium">
        You've used all {freeLimit} free questions.
      </p>
      <p className="text-amber-700 text-xs">
        Add your own Claude API key to continue asking unlimited questions.
        Your key stays in your browser and is never sent to our servers.
      </p>
      <a
        href="/settings"
        className="inline-block mt-1 px-3 py-1.5 rounded-lg bg-violet-600 text-white text-xs font-medium
                   hover:bg-violet-700 transition-colors"
      >
        Add API Key in Settings
      </a>
    </div>
  );

  // Floating button
  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full
                   bg-violet-600 text-white shadow-lg shadow-violet-200
                   hover:bg-violet-700 hover:shadow-xl hover:shadow-violet-300
                   transition-all duration-200 group
                   px-4 py-3 sm:px-5 sm:py-3.5
                   ${hasUnreadQA ? 'ring-2 ring-yellow-300 ring-offset-2 shadow-[0_0_12px_rgba(253,224,71,0.5)]' : ''}`}
        title={hasUnreadQA ? 'Ask the Quran — new Q&A available' : 'Ask the Quran'}
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
            d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"
          />
        </svg>
        <span className="text-sm font-medium hidden sm:inline">Ask the Quran</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50 w-[calc(100vw-2rem)] sm:w-[420px] md:w-[460px]
                    rounded-2xl border border-violet-200 bg-white shadow-2xl shadow-violet-200/50
                    overflow-hidden flex flex-col"
         style={{ maxHeight: 'calc(100vh - 6rem)' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between bg-violet-50 px-4 py-3 border-b border-violet-200 shrink-0">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold text-violet-900">Ask the Quran</h3>
          {hasHistory && (
            <div className="flex rounded-lg bg-violet-100 p-0.5">
              <button
                onClick={() => setTab('ask')}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  tab === 'ask' ? 'bg-white text-violet-800 shadow-sm' : 'text-violet-600 hover:text-violet-800'
                }`}
              >
                Ask
              </button>
              <button
                onClick={() => setTab('history')}
                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                  tab === 'history' ? 'bg-white text-violet-800 shadow-sm' : 'text-violet-600 hover:text-violet-800'
                } ${qaFlash && tab !== 'history' ? 'animate-pulse bg-yellow-100 text-yellow-800 ring-1 ring-yellow-300' : ''}`}
              >
                Q&amp;A
                {hasUnreadQA && tab !== 'history' && (
                  <span className="ml-1 inline-block w-1.5 h-1.5 rounded-full bg-yellow-400" />
                )}
              </button>
            </div>
          )}
        </div>
        <div className="flex items-center gap-1">
          {tab === 'ask' && messages.length > 0 && (
            <button onClick={handleClearConversation}
              className="text-violet-400 hover:text-violet-600 transition-colors p-1"
              title="Clear conversation">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
          <button onClick={() => setOpen(false)}
            className="text-violet-400 hover:text-violet-600 transition-colors p-1">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {tab === 'ask' ? (
        <div className="flex flex-col flex-1 min-h-0">
          {/* Messages area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[120px]">
            {messages.length === 0 && !streaming && (
              <p className="text-sm text-stone-400 text-center py-6">
                Ask a question about this {pageType}. The assistant will use root-level analysis to provide an answer.
              </p>
            )}

            {messages.map((msg, i) => (
              <div
                key={i}
                className={`text-sm ${
                  msg.role === 'user'
                    ? 'text-stone-700 bg-stone-50 rounded-lg px-3 py-2'
                    : 'text-stone-800 leading-relaxed group/msg relative'
                }`}
              >
                {msg.role === 'user' ? (
                  <div className="flex items-start gap-2">
                    <span className="text-stone-400 text-xs mt-0.5 shrink-0">You:</span>
                    <span>{msg.content}</span>
                  </div>
                ) : (
                  <>
                    <div>{renderFormatted(msg.content)}</div>
                    <button onClick={() => handleCopy(msg.content)}
                      className="absolute top-0 right-0 opacity-0 group-hover/msg:opacity-100
                                 text-stone-300 hover:text-stone-500 transition-opacity p-1"
                      title="Copy response">
                      <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    </button>
                  </>
                )}
              </div>
            ))}

            {streaming && (
              <div className="text-sm text-stone-800 leading-relaxed">
                {streamText ? renderFormatted(streamText) : (
                  <span className="inline-flex items-center gap-1.5 text-violet-500">
                    <span className="w-1.5 h-1.5 bg-violet-400 rounded-full animate-pulse" />
                    Thinking...
                  </span>
                )}
              </div>
            )}

            {error && error !== 'FREE_LIMIT_REACHED' && (
              <div className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
                {error}
                {(error.toLowerCase().includes('api key') || error.toLowerCase().includes('settings')) && (
                  <a href="/settings" className="ml-1 underline font-medium">Go to Settings</a>
                )}
              </div>
            )}

            {error === 'FREE_LIMIT_REACHED' && freeLimitBanner}

            <div ref={chatEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-violet-100 p-3 shrink-0">
            {/* Free limit reached — show upgrade prompt instead of input */}
            {!canAsk ? (
              freeLimitBanner
            ) : (
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => { setInput(e.target.value); if (error) setError(''); }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit();
                    }
                  }}
                  placeholder={`Ask about this ${pageType}...`}
                  disabled={streaming}
                  maxLength={500}
                  className="flex-1 rounded-lg border border-stone-300 px-3 py-2 text-sm
                             focus:border-violet-400 focus:ring-1 focus:ring-violet-400 outline-none
                             disabled:bg-stone-50 disabled:text-stone-400"
                />
                {streaming ? (
                  <button onClick={handleCancel}
                    className="px-3 py-2 rounded-lg bg-stone-200 text-stone-600 text-sm hover:bg-stone-300 transition-colors">
                    Stop
                  </button>
                ) : (
                  <button onClick={handleSubmit} disabled={!input.trim()}
                    className="px-3 py-2 rounded-lg bg-violet-600 text-white text-sm font-medium
                               hover:bg-violet-700 disabled:bg-violet-300 disabled:cursor-not-allowed transition-colors">
                    Ask
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* History tab */
        <div className="p-4 flex-1 overflow-y-auto">
          {!historyLoaded ? (
            <div className="flex justify-center py-6">
              <div className="h-5 w-5 animate-spin rounded-full border-2 border-violet-200 border-t-violet-600" />
            </div>
          ) : history.length === 0 ? (
            <p className="text-sm text-stone-400 text-center py-6">
              No questions have been asked about this {pageType} yet.
            </p>
          ) : (
            <div className="space-y-4">
              {history.map((entry) => {
                const isExpanded = expandedHistoryId === entry.id;
                return (
                  <div key={entry.id}
                    className="border border-stone-200 rounded-lg p-3 cursor-pointer hover:border-stone-300 transition-colors"
                    onClick={() => setExpandedHistoryId(isExpanded ? null : entry.id)}>
                    <div className="flex items-start justify-between mb-1.5">
                      <span className="text-sm font-medium text-stone-700">{entry.question}</span>
                      <span className="text-xs text-stone-400 shrink-0 ml-2">
                        {new Date(entry.created_at + 'Z').toLocaleDateString()}
                      </span>
                    </div>
                    <div className={`text-sm text-stone-600 leading-relaxed ${isExpanded ? '' : 'line-clamp-3'}`}>
                      {renderFormatted(entry.answer)}
                    </div>
                    {!isExpanded && entry.answer.split('\n').length > 3 && (
                      <span className="text-xs text-violet-500 mt-1 inline-block">Click to expand</span>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
