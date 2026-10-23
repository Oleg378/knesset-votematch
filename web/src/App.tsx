import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { track } from './analytics';
import { Counter, Header } from './components/Header';
import { Menu } from './components/Menu';
import { ProgressBar } from './components/ProgressBar';
import { core, loadFiles } from './data';
import { BillsScreen } from './screens/BillsScreen';
import { DetailsScreen } from './screens/DetailsScreen';
import { MethodologyScreen } from './screens/MethodologyScreen';
import { QuestionScreen } from './screens/QuestionScreen';
import { ResultsScreen } from './screens/ResultsScreen';
import { StartScreen } from './screens/StartScreen';
import { TradeoffScreen } from './screens/TradeoffScreen';
import { createBackGuard } from './state/backGuard';
import { createReducer, hasComputableAnswers, initialState } from './state/reducer';
import { S } from './strings';

function focusHeading() {
  const h = document.querySelector<HTMLElement>('main h1, main h2');
  if (!h) return;
  h.tabIndex = -1;
  h.focus({ preventScroll: true });
}

export default function App() {
  const reducer = useMemo(() => createReducer(core), []);
  // In memory only [У 2026-10-17]: no storage, a reload starts over; nothing goes into the URL.
  const [state, dispatch] = useReducer(reducer, initialState);
  const props = { core, state, dispatch };
  const sc = state.screen;

  // The data files (export/WEB_CONTRACT.md §1): quiz_data, then quiz_bills, fetched once from page load.
  const loading = useRef(false);
  useEffect(() => {
    if (loading.current) return;
    loading.current = true;
    void loadFiles((f) => dispatch({ type: 'FILE_READY', ...f }), () => dispatch({ type: 'LOAD_ERROR' }));
  }, []);

  // System Back = in-app Back (no router, URL untouched).
  const guard = useMemo(() => createBackGuard(window.history), []);
  const stateRef = useRef(state);
  stateRef.current = state;
  useEffect(() => {
    const onPop = () => {
      if (!guard.onPop()) return;
      // Re-arm here too: when BACK changes nothing (results, trade-off) there is no re-render.
      const next = reducer(stateRef.current, { type: 'BACK' });
      dispatch({ type: 'BACK' });
      guard.sync(next.screen.name === 'start');
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [guard, reducer]);

  const prev = useRef(sc.name);
  const mounted = useRef(false);
  const key = JSON.stringify(sc);
  useEffect(() => {
    const from = prev.current;
    if (from === 'start' && sc.name === 'question') track('started');
    if ((from === 'question' || from === 'tradeoff') && sc.name === 'results') track('finished');
    // Screen readers: announce the new screen by moving focus to its heading (not on the first render).
    if (mounted.current) focusHeading();
    mounted.current = true;
    prev.current = sc.name;
    guard.sync(sc.name === 'start');
    window.scrollTo(0, 0);
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  const [menu, setMenu] = useState(false);
  const closeMenu = useCallback(() => setMenu(false), []);
  // Counter: n / (core + clarify) while the fixed number of questions is used; beyond it («Answer more questions») n alone.
  const total = core.flow.core + core.flow.clarify;
  const header =
    sc.name === 'question' ? (
      <ProgressBar value={sc.i + 1} max={Math.max(total, sc.i + 1)} label={S.question.progressLabel}
        text={sc.i + 1 <= total ? S.question.progress(sc.i + 1, total) : S.question.progressMore(sc.i + 1)} />
    ) : sc.name === 'tradeoff' ? (
      <Counter text={S.trade.counter(state.done.length + 1, core.flow.trade)} />
    ) : null;

  return (
    <main className="app">
      <Header onMenu={() => setMenu(true)}>{header}</Header>
      {menu && (
        <Menu onClose={closeMenu} onStartOver={() => dispatch({ type: 'START_OVER' })}
          onResults={hasComputableAnswers(state.answers) || sc.name === 'question'
            ? () => dispatch({ type: 'SHOW_RESULTS' }) : null}
          onMethodology={() => sc.name !== 'methodology' && dispatch({ type: 'OPEN_METHODOLOGY' })} />
      )}
      {sc.name === 'start' && <StartScreen {...props} />}
      {sc.name === 'question' && <QuestionScreen key={sc.i} i={sc.i} {...props} />}
      {sc.name === 'tradeoff' && <TradeoffScreen key={sc.pair.join('/')} {...props} />}
      {sc.name === 'results' && <ResultsScreen {...props} />}
      {sc.name === 'details' && <DetailsScreen key={sc.list} {...props} />}
      {sc.name === 'bills' && <BillsScreen key={`${sc.list}/${sc.q}`} {...props} />}
      {sc.name === 'methodology' && <MethodologyScreen {...props} />}
      {sc.name === 'loading' && (
        <section className="screen">
          <p className="muted" role="status">{state.loadFailed ? S.loadError : S.loading}</p>
        </section>
      )}
    </main>
  );
}
