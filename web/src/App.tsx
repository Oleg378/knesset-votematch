import { useCallback, useEffect, useMemo, useReducer, useRef, useState, useSyncExternalStore } from 'react';
import { flushSync } from 'react-dom';
import { track } from './analytics';
import { isCardChange, slideCard } from './cardTransition';
import { Counter, Header } from './components/Header';
import { Loading, LoadError } from './components/Loading';
import { Menu } from './components/Menu';
import { ProgressBar } from './components/ProgressBar';
import type { Loader } from './data';
import { plannedQuestions } from './engine/flow';
import { BillsScreen } from './screens/BillsScreen';
import { DetailsScreen } from './screens/DetailsScreen';
import { MethodologyScreen } from './screens/MethodologyScreen';
import { QuestionScreen } from './screens/QuestionScreen';
import { ResultsScreen } from './screens/ResultsScreen';
import { StartScreen } from './screens/StartScreen';
import { TradeoffScreen } from './screens/TradeoffScreen';
import { createBackGuard } from './state/backGuard';
import { createReducer, hasComputableAnswers, initialState, type Action } from './state/reducer';
import { S } from './strings';

function focusHeading() {
  const h = document.querySelector<HTMLElement>('main h1, main h2');
  if (!h) return;
  h.tabIndex = -1;
  h.focus({ preventScroll: true });
}

export default function App({ loader }: { loader: Loader }) {
  const src = useSyncExternalStore(loader.subscribe, loader.get);
  const { core, data, bills } = src;
  const reducer = useMemo(() => createReducer({ core, data }), [core, data]);
  // In memory only [У 2026-10-17]: no storage, a reload starts over; nothing goes into the URL.
  const [state, dispatch] = useReducer(reducer, initialState);
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
    else slideCard(() => flushSync(() => dispatch(action)), action.type === 'BACK');
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
    window.scrollTo(0, 0);
  }, [key]); // eslint-disable-line react-hooks/exhaustive-deps

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

  // A screen is shown only when its file has arrived; otherwise a loader for this screen only.
  const wait = src.failed ? <LoadError /> : <Loading />;
  const props = { state, dispatch: send };
  const statement = sc.name === 'question'
    ? (data?.statements ?? core?.statements ?? []).find((s) => s.q === state.shown[sc.i]) : undefined;
  let body;
  switch (sc.name) {
    case 'start':
      body = <StartScreen core={core} dispatch={send} />;
      break;
    case 'question':
      body = statement ? <QuestionScreen key={sc.i} statement={statement} {...props} /> : wait;
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
    case 'bills':
      body = data && bills ? <BillsScreen key={`${sc.list}/${sc.q}`} data={data} bills={bills} {...props} /> : wait;
      break;
    case 'methodology':
      body = data && bills ? <MethodologyScreen data={data} bills={bills} {...props} /> : wait;
      break;
  }

  return (
    <main className="app">
      <Header onMenu={() => setMenu(true)}>{header}</Header>
      {menu && (
        <Menu onClose={closeMenu} onStartOver={() => dispatch({ type: 'START_OVER' })}
          onResults={hasComputableAnswers(state.answers) || sc.name === 'question' || sc.name === 'wait'
            ? () => dispatch({ type: 'SHOW_RESULTS' }) : null}
          onMethodology={() => sc.name !== 'methodology' && dispatch({ type: 'OPEN_METHODOLOGY' })} />
      )}
      {body}
    </main>
  );
}
