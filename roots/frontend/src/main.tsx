import { StrictMode, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initPageTracking } from './api/track'
import { initNavProgress } from './utils/nav-progress'

// Hook into history.pushState / popstate so the backend gets a pageview
// ping on every SPA route change. Admin pages and /api requests are
// skipped both client- and server-side.
initPageTracking()
initNavProgress()

// Same markup as the boot splash in index.html (styled there), shown while a
// page's code-split chunk loads, so the splash never flickers.
const bootSplash = (
  <div className="boot" role="status" aria-label="Loading">
    <div className="boot-bar" />
    <div className="boot-name">al-nuqta</div>
    <div className="boot-dot" />
  </div>
)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Suspense fallback={bootSplash}>
      <App />
    </Suspense>
  </StrictMode>,
)
