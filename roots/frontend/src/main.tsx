import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { initPageTracking } from './api/track'

// Hook into history.pushState / popstate so the backend gets a pageview
// ping on every SPA route change. Admin pages and /api requests are
// skipped both client- and server-side.
initPageTracking()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
