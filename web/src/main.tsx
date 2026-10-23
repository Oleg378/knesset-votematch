import { lazy, StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { S } from './strings';
// Figma fonts, bundled (no third-party requests); Latin only — Hebrew falls back to system fonts (DECISIONS.md B.1).
import '@fontsource/plus-jakarta-sans/latin-400.css';
import '@fontsource/plus-jakarta-sans/latin-500.css';
import '@fontsource/plus-jakarta-sans/latin-600.css';
import '@fontsource/fraunces/latin-400.css';
import './styles/tokens.css';
import './styles/app.css';

// The app chunk (with the ~2 KB quiz_core) loads behind a light fallback; the bigger data files are fetched by the app.
const App = lazy(() => import('./App'));

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Suspense fallback={<main className="app"><p className="muted">{S.loading}</p></main>}>
      <App />
    </Suspense>
  </StrictMode>,
);
