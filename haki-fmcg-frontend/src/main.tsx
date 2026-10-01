import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

// Handle dynamic import failures when a new Vercel build is deployed with new chunk hashes
window.addEventListener('vite:preloadError', (event) => {
  event.preventDefault();
  // Prevent infinite reload loops with a session flag
  const hasRefreshed = sessionStorage.getItem('haki_chunk_reload');
  if (!hasRefreshed) {
    sessionStorage.setItem('haki_chunk_reload', 'true');
    window.location.reload();
  }
});

// Clear reload flag after successful startup
sessionStorage.removeItem('haki_chunk_reload');

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)

