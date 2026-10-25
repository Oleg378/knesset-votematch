import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
// Figma fonts, bundled (no third-party requests); Latin only — Hebrew falls back to system fonts (DECISIONS.md B.1).
import '@fontsource/plus-jakarta-sans/latin-400.css';
import '@fontsource/plus-jakarta-sans/latin-500.css';
import '@fontsource/plus-jakarta-sans/latin-600.css';
// Not in Figma: ExtraBold for the Results rank numbers only (customer 2026-10-23); fetched only when that screen draws.
import '@fontsource/plus-jakarta-sans/latin-800.css';
// Not in Figma: Regular Italic for the Results hint «Tap › for details» only (customer 2026-10-23).
import '@fontsource/plus-jakarta-sans/latin-400-italic.css';
import './styles/fonts.css';
import './styles/tokens.css';
import './styles/app.css';
import App from './App';
import { watchBottomFade } from './bottomFade';
import { createLoader } from './data';
import { showViewportNumbers } from './debugViewport';
import { chooseScrolling } from './inApp';
import { initialStateFor } from './state/reducer';

// The data files are fetched from page load, in order (core, data, bills); the start page does not wait for them.
const loader = createLoader();
loader.start();
chooseScrolling(); // an app's viewer: the frame; a browser: the window scrolls (app.css)
watchBottomFade();
if (location.search.includes('debug')) showViewportNumbers(); // the window's numbers on screen, for checks on a phone

// The page's HTML already holds its screen (src/prerender.tsx); React draws the same markup in its place. The page's
// path picks the screen: «/how-it-works» opens the methodology. Dev server only: `?demo` opens List details (devDemo.ts).
const demo = import.meta.env.DEV ? new URLSearchParams(location.search).get('demo') : null;
const initial = demo !== null
  ? await import('./devDemo').then((m) => { m.openFirstTopic(); return m.demoState(demo); })
  : initialStateFor(location.pathname);
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App loader={loader} initial={initial} />
  </StrictMode>,
);
