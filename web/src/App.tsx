import { useCallback, useEffect, useMemo, useReducer, useRef, useState, useSyncExternalStore } from 'react';
import { flushSync } from 'react-dom';
import { track } from './analytics';
import { screenScroller } from './scroller';
import { watchShortScroll } from './shortScroll';
import { isCardChange, slideCard } from './cardTransition';
import { Counter, Header } from './components/Header';
import { Loading, LoadError } from './components/Loading';
import { Menu } from './components/Menu';
import { ProgressBar } from './components/ProgressBar';
import type { Loader } from './data';
import { plannedQuestions } from './engine/flow';
import { DetailsScreen } from './screens/DetailsScreen';
import { MethodologyScreen } from './screens/MethodologyScreen';
import { QuestionScreen } from './screens/QuestionScreen';
import { ResultsScreen } from './screens/ResultsScreen';
import { StartScreen } from './screens/StartScreen';
import { TradeoffScreen } from './screens/TradeoffScreen';
import { createBackGuard } from './state/backGuard';
import { createReducer, hasComputableAnswers, initialState, type Action, type State } from './state/reducer';
import { S } from './strings';

function focusHeading() {
  const h = document.querySelector<HTMLElement>('main h1, main h2');
  if (!h) return;
  h.tabIndex = -1;
  h.focus({ preventScroll: true });
}

export default function App({ loader, initial = initialState }: { loader: Loader; initial?: State }) {
  const src = useSyncExternalStore(loader.subscribe, loader.get);
  const { core, data, bills } = src;
  const reducer = useMemo(() => createReducer({ core, data }), [core, data]);
  // In memory only [У 2026-10-17]: no storage, a reload starts over; nothing goes into the URL.
  const [state, dispatch] = useReducer(reducer, initial);
  const sc = state.screen;

  // A data file arrived: resume a screen that was waiting for it.
  useEffect(() => {
    dispatch({ type: 'DATA_READY' });
  }, [core, data, bills]);

  // System Back = in-app Back (no router, URL untouched).
  const guard = useMemo(() => createBackGuard(window.history), []);
  const stateRef = useRef(state);
  stateRef.current = state;
  const reducerRef = useRef(reducer);
  reducerRef.current = reducer;
  // One quiz card replacing another slides (cardTransition.ts); the DOM must change inside the transition: flushSync.
  const send = useCallback((action: Action) => {
    const next = reducerRef.current(stateRef.current, action);
    if (!isCardChange(stateRef.current.screen, next.screen)) dispatch(action);
    else slideCard(() => {
      flushSync(() => dispatch(action));
      // Where the screen scrolls inside the page (the frame in an app's viewer, a short page in a browser): the new card
      // starts at its top, set here, before the browser takes its picture — so nothing scrolls on screen; the old card
      // leaves as it was. The window is never scrolled around the transition (cardTransition.ts).
      const inner = screenScroller();
      if (inner) inner.scrollTop = 0;
    }, action.type === 'BACK');
  }, []);

  useEffect(() => {
    const onPop = (e: PopStateEvent) => {
      if (!guard.onPop()) return;
      // Re-arm here too: when BACK changes nothing (results, trade-off) there is no re-render.
      const next = reducerRef.current(stateRef.current, { type: 'BACK' });
      // A back swipe already animated by the browser (Safari) does not slide the card again.
      if (e.hasUAVisualTransition) dispatch({ type: 'BACK' });
      else send({ type: 'BACK' });
      guard.sync(next.screen.name === 'start');
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, [guard, send]);

  const prev = useRef(sc.name);
  const mounted = useRef(false);
  const key = JSON.stringify(sc);
  useEffect(() => {
    const from = prev.current;
    if (from === 'start' && (sc.name === 'question' || sc.name === 'wait')) track('started');
    if ((from === 'question' || from === 'tradeoff' || from === 'wait') && sc.name === 'results') track('finished');
    // Screen readers: announce the new screen by moving focus to its heading (not on the first render).
    if (mounted.current) focusHeading();
    mounted.current = true;
    prev.current = sc.name;
    guard.sync(sc.name === 'start');
    // «How it works» is the one screen with an address of its own (/how-it-works, prerendered: src/prerender.tsx); the
    // address follows it and comes back to / on any other screen. Nothing else is ever in the URL (no answers, no result).
    const page = sc.name === 'methodology' ? '/how-it-works' : '/';
    if (location.pathname !== page) history.replaceState(history.state, '', page);
    // During a card change the page must not scroll: cardTransition.ts scrolls to the top when it ends.
    if (!document.documentElement.dataset.card) {
      window.scrollTo(0, 0);
      const inner = screenScroller(); // the frame's area, or .app for a short page (shortScroll.ts)
      if (inner) inner.scrollTop = 0;
    }
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

  // Short scrolls (shortScroll.ts): in a browser, a page a little longer than the window scrolls inside .app.
  const appRef = useRef<HTMLElement>(null);
  useEffect(() => (appRef.current ? watchShortScroll(appRef.current) : undefined), []);

  const [menu, setMenu] = useState(false);
  const closeMenu = useCallback(() => setMenu(false), []);

  // The counter: n / (core + clarify) while the fixed number is used; with «Answer more» — out of all statements.
  let header = null;
  if (sc.name === 'question' && core) {
    const total = state.more && data ? data.statements.length
      : core.flow.stop_gap === null ? plannedQuestions(core.flow) : core.flow.max_questions;
    header = <ProgressBar value={sc.i + 1} max={Math.max(total, sc.i + 1)} label={S.question.progressLabel}
      text={S.question.progress(sc.i + 1, Math.max(total, sc.i + 1))} />;
  } else if (sc.name === 'tradeoff' && data) {
    header = <Counter text={S.trade.counter(state.done.length + 1, data.flow.trade)} />;
  }

  // An inner page, opened from another page (List details): «Back» in the header instead of the menu (customer
  // 2026-10-24). How it works is a page of its own: the menu stays, and no Back (DECISIONS.md G24).
  const back = sc.name === 'details' ? S.details.back : null;

  // A screen is shown only when its file has arrived; otherwise a loader for this screen only.
  const wait = src.failed ? <LoadError /> : <Loading />;
  const props = { state, dispatch: send };
  const statements = data?.statements ?? core?.statements;
  const texts = useMemo(() => (statements ?? []).map((s) => s.statement_en), [statements]);
  const statement = sc.name === 'question' ? statements?.find((s) => s.q === state.shown[sc.i]) : undefined;
  let body;
  switch (sc.name) {
    case 'start':
      body = <StartScreen core={core} dispatch={send} />;
      break;
    case 'question':
      body = statement ? <QuestionScreen key={sc.i} statement={statement} texts={texts} {...props} /> : wait;
      break;
    case 'wait':
      body = wait;
      break;
    case 'tradeoff':
      body = data ? <TradeoffScreen key={sc.pair.join('/')} data={data} {...props} /> : wait;
      break;
    case 'results':
      body = data ? <ResultsScreen data={data} {...props} /> : wait;
      break;
    case 'details':
      body = data && bills ? <DetailsScreen key={sc.list} data={data} bills={bills} {...props} /> : wait;
      break;
    case 'methodology':
      body = data && bills ? <MethodologyScreen data={data} bills={bills} {...props} /> : wait;
      break;
  }

  return (
    <main ref={appRef} className="app">
      <Header onMenu={() => setMenu(true)} back={back ? { label: back, onClick: () => send({ type: 'BACK' }) } : undefined}
        title={sc.name === 'results' ? S.results.heading : sc.name === 'methodology' ? S.methodology.heading : undefined}
        onStartOver={sc.name === 'results' ? () => send({ type: 'RESTART' }) : undefined}>{header}</Header>
      {menu && (
        <Menu onClose={closeMenu} onStartOver={() => dispatch({ type: 'START_OVER' })}
          onResults={hasComputableAnswers(state.answers) || sc.name === 'question' || sc.name === 'wait'
            ? () => dispatch({ type: 'SHOW_RESULTS' }) : null}
          onMethodology={() => sc.name !== 'methodology' && dispatch({ type: 'OPEN_METHODOLOGY' })} />
      )}
      <div className="app-scroll">{body}</div>
    </main>
  );
}
