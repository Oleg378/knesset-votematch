import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
// Figma fonts, bundled (no third-party requests); Latin only — Hebrew falls back to system fonts (DECISIONS.md B.1).
import '@fontsource/plus-jakarta-sans/latin-400.css';
import '@fontsource/plus-jakarta-sans/latin-500.css';
import '@fontsource/plus-jakarta-sans/latin-600.css';
// Not in Figma: ExtraBold for the Results rank numbers only (customer 2026-10-23); fetched only when that screen draws.
import '@fontsource/plus-jakarta-sans/latin-800.css';
import './styles/fonts.css';
import './styles/tokens.css';
import './styles/app.css';
import App from './App';
import { createLoader } from './data';

// The data files are fetched from page load, in order (core, data, bills); the start page does not wait for them.
const loader = createLoader();
loader.start();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App loader={loader} />
  </StrictMode>,
);
