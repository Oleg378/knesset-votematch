import { lazy, StrictMode, Suspense } from 'react';
import { createRoot } from 'react-dom/client';
import { S } from './strings';
// Figma fonts, bundled (no third-party requests); Latin only — Hebrew falls back to system fonts (DECISIONS.md B.1).
import '@fontsource/plus-jakarta-sans/latin-400.css';
import '@fontsource/plus-jakarta-sans/latin-500.css';
import '@fontsource/plus-jakarta-sans/latin-600.css';
import './styles/fonts.css';
import './styles/tokens.css';
import './styles/app.css';

// The app chunk carries the bundled data (export/quiz_data.v1.json, ~1.8 MB); show a light fallback meanwhile.
const App = lazy(() => import('./App'));

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Suspense fallback={<main className="app"><p className="muted">{S.loading}</p></main>}>
      <App />
    </Suspense>
  </StrictMode>,
);
