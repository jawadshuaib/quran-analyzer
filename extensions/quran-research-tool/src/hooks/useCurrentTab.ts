import { useState, useEffect } from 'react';

export function useCurrentTab() {
  const [url, setUrl] = useState<string | null>(null);

  useEffect(() => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      setUrl(tabs[0]?.url ?? null);
    });
  }, []);

  return url;
}
