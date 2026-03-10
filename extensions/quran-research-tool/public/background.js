/* global chrome */

// Respond to website install-detection pings.
chrome.runtime.onMessageExternal.addListener((message, sender, sendResponse) => {
  if (!message || typeof message !== 'object') return;
  if (message.type !== 'QURAN_RESEARCH_TOOL_PING') return;

  sendResponse({
    type: 'QURAN_RESEARCH_TOOL_PONG',
    ok: true,
    installed: true,
    version: chrome.runtime.getManifest().version,
    extensionId: chrome.runtime.id,
    senderOrigin: sender?.origin || '',
  });
});
