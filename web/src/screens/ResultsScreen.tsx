import { useMemo, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { Button } from '../components/Button';
import { ListRow } from '../components/ListRow';
import { match } from '../engine/match';
import { answeredCount } from '../state/reducer';
import { S } from '../strings';
import type { ScreenProps } from './types';

/** How many of the closest lists stand out on the scale (customer 2026-10-22). */
const HIGHLIGHT = 5;

export function ResultsScreen({ data, state, dispatch }: ScreenProps) {
  const rows = useMemo(() => match(data, state.answers, state.mult), [data, state.answers, state.mult]);
  const ranked = rows.filter((r) => r.ranked);
  const top = ranked.slice(0, HIGHLIGHT);
  const rest = ranked.slice(HIGHLIGHT);
  const low = rows.filter((r) => !r.ranked && r.evaluated);
  // Lists with no record in the Knesset are not shown (customer 2026-10-22); Methodology counts them.
  const open = (id: string) => () => dispatch({ type: 'OPEN_DETAILS', list: id });
  // Only the closest lists are shown; the rest drop down from the panel with «See all» (customer 2026-10-22).
  const [all, setAll] = useState(false);
  const hidden = rest.length + low.length > 0;
  // No list ranked: no panel to drop from, everything is shown.
  const shown = all || top.length === 0;
  // «See all» is in the panel and «Show less» only at the end of the open list (customer 2026-10-22). Each one goes
  // away when pressed, so the focus moves on: to the first list that dropped down, back to «See all».
  const toggle = useRef<HTMLButtonElement>(null);
  const drop = useRef<HTMLDivElement>(null);
  const showAll = (on: boolean) => {
    flushSync(() => setAll(on));
    (on ? drop.current?.querySelector('button') : toggle.current)?.focus();
  };
  return (
    <section className="screen results">
      <div className="stack">
        <h1 className="title-lg">{S.results.heading}</h1>
        <p className="lead">
          {S.results.basedOn(answeredCount(state.answers), state.shown.length, Object.keys(state.mult).length > 0)}
        </p>
        {top.length > 0 && (
          <p className="lead hint">
            {S.results.hint[0]} <span className="list-row-go" aria-hidden="true" /> {S.results.hint[1]}
          </p>
        )}
      </div>
      <div className="rule" role="presentation" />
      <div className="scale-legend" aria-hidden="true">
        <span>{S.results.scaleFar}</span>
        <span>{S.results.scaleClose}</span>
      </div>
      {top.length > 0 && (
        <div className={all ? 'panel scale-top open' : 'panel scale-top'}>
          <ol className="scale-rows" aria-label={S.results.closest(top.length)}>
            {top.map((r, i) => (
              <li key={r.id}>
                <ListRow rank={i + 1} name={r.name_en} closeness={r.closeness} note={r.note} onClick={open(r.id)} />
              </li>
            ))}
          </ol>
          {hidden && !all && (
            <div className="see-all">
              <button type="button" ref={toggle} className="btn btn-link skip" aria-expanded="false"
                onClick={() => showAll(true)}>
                {S.results.seeAll}
              </button>
            </div>
          )}
        </div>
      )}
      {shown && hidden && (
        <div className="scale-drop" ref={drop}>
          {rest.length > 0 && (
            <ol className="scale-rows scale-rest" start={HIGHLIGHT + 1}>
              {rest.map((r, i) => (
                <li key={r.id}>
                  <ListRow rank={HIGHLIGHT + i + 1} name={r.name_en} closeness={r.closeness} note={r.note}
                    onClick={open(r.id)} />
                </li>
              ))}
            </ol>
          )}
          {low.length > 0 && (
            <>
              <div className="or-divider" role="presentation">
                <span>{S.results.notRanked}</span>
              </div>
              {/* One reason for all of them in the divider, no note on each (customer 2026-10-22); List details keeps it. */}
              <ul className="scale-rows scale-rest scale-low">
                {low.map((r) => (
                  <li key={r.id}>
                    <ListRow rank={null} name={r.name_en} closeness={r.closeness} note=""
                      onClick={r.closeness === null ? undefined : open(r.id)} />
                  </li>
                ))}
              </ul>
            </>
          )}
          {top.length > 0 && (
            <div className="see-all">
              <button type="button" className="btn btn-link skip" aria-expanded="true" onClick={() => showAll(false)}>
                {S.results.seeLess}
              </button>
            </div>
          )}
        </div>
      )}
      <div className="sticky-actions push-down">
        <Button block onClick={() => dispatch({ type: 'CHANGE_ANSWERS' })}>
          {S.results.changeAnswers}
        </Button>
      </div>
    </section>
  );
}
