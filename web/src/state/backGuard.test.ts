import { describe, expect, it } from 'vitest';
import { core, data } from '../testSources';
import { createBackGuard, type HistoryLike } from './backGuard';
import { createReducer, initialState, type State } from './reducer';

/** A browser history stub: a stack of entries; back() pops and fires popstate synchronously. */
function fakeHistory() {
  const h = {
    depth: 1,
    onpop: () => {},
    pushState() {
      h.depth += 1;
    },
    back() {
      h.depth -= 1;
      h.onpop();
    },
  };
  return h satisfies HistoryLike;
}

/** Wires guard + reducer as App does. */
function setup() {
  const reducer = createReducer({ core, data });
  const h = fakeHistory();
  const guard = createBackGuard(h);
  let state: State = initialState;
  const dispatch = (a: Parameters<typeof reducer>[1]) => {
    state = reducer(state, a);
    guard.sync(state.screen.name === 'start');
  };
  h.onpop = () => {
    if (guard.onPop()) dispatch({ type: 'BACK' });
  };
  return { h, get state() { return state; }, dispatch };
}

describe('system back', () => {
  it('start screen keeps no extra entry', () => {
    const t = setup();
    t.dispatch({ type: 'OPEN_METHODOLOGY' });
    expect(t.h.depth).toBe(2);
    t.h.back();
    expect(t.state.screen.name).toBe('start');
    expect(t.h.depth).toBe(1);
  });

  it('back goes to the previous statement and the entry is re-armed', () => {
    const t = setup();
    t.dispatch({ type: 'START' });
    t.dispatch({ type: 'ANSWER', value: 2 });
    t.dispatch({ type: 'NEXT' });
    t.dispatch({ type: 'ANSWER', value: -1 });
    t.dispatch({ type: 'NEXT' });
    expect(t.state.screen).toEqual({ name: 'question', i: 2 });
    t.h.back();
    expect(t.state.screen).toEqual({ name: 'question', i: 1 });
    expect(t.h.depth).toBe(2);
    t.h.back();
    t.h.back();
    expect(t.state.screen.name).toBe('start');
    expect(t.h.depth).toBe(1);
  });

  it('bills → details → results; on results back stays (answers are not lost)', () => {
    const t = setup();
    t.dispatch({ type: 'START' });
    t.dispatch({ type: 'ANSWER', value: 2 });
    t.dispatch({ type: 'NEXT' });
    t.dispatch({ type: 'ANSWER', value: -2 });
    t.dispatch({ type: 'FINISH' });
    while (t.state.screen.name === 'tradeoff') t.dispatch({ type: 'TRADE', choice: '=' });
    expect(t.state.screen.name).toBe('results');
    const list = data.lists[0]!.id;
    t.dispatch({ type: 'OPEN_DETAILS', list });
    t.dispatch({ type: 'OPEN_BILLS', q: data.statements[0]!.q });
    t.h.back();
    expect(t.state.screen).toEqual({ name: 'details', list });
    t.h.back();
    expect(t.state.screen.name).toBe('results');
    t.h.back();
    expect(t.state.screen.name).toBe('results');
    expect(t.h.depth).toBe(2);
  });

  it('on a trade-off back undoes the previous one', () => {
    const t = setup();
    t.dispatch({ type: 'START' });
    for (let i = 0; i < 30; i++) {
      t.dispatch({ type: 'ANSWER', value: i % 2 ? 2 : -2 });
      t.dispatch({ type: 'NEXT' });
    }
    t.dispatch({ type: 'FINISH' });
    expect(t.state.screen.name).toBe('tradeoff');
    const first = t.state.screen;
    t.dispatch({ type: 'TRADE', choice: 'A' });
    t.h.back();
    expect(t.state.screen).toEqual(first);
    expect(t.state.mult).toEqual({});
  });

  it('start over drops the entry', () => {
    const t = setup();
    t.dispatch({ type: 'START' });
    t.dispatch({ type: 'ANSWER', value: 1 });
    t.dispatch({ type: 'START_OVER' });
    expect(t.state.screen.name).toBe('start');
    expect(t.h.depth).toBe(1);
  });
});
