import { useMemo, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { Button } from '../components/Button';
import { ListRow } from '../components/ListRow';
import { match } from '../engine/match';
import { collapse, expand, scrollBackTo } from '../expandMotion';
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
  // «See all» grows the dropped lists from the panel; the focus goes to the first of them without scrolling the page.
  // «Show less» (at the end of the lists): the page goes smoothly back to the panel, then the lists shrink into it
  // (customer 2026-10-23, option 1). The panel's bottom — «See all» and the rounded corners — rides up on the lists'
  // shrinking edge as a lid (.scale-lid, a picture: not a button) and ends exactly where the closed panel has it, so
  // swapping in the closed panel moves nothing. The lists stay mounted, inert, until they are gone. expandMotion.ts.
  const [closing, setClosing] = useState(false);
  const showAll = (on: boolean) => {
    if (on) {
      flushSync(() => setAll(true));
      if (drop.current) expand(drop.current);
      drop.current?.querySelector('button')?.focus({ preventScroll: true });
      return;
    }
    const lists = drop.current;
    const panel = lists?.previousElementSibling; // .scale-top: «See all» is not there while the lists are open
    if (closing) return;
    if (!lists || !(panel instanceof HTMLElement)) {
      flushSync(() => setAll(false));
      toggle.current?.focus();
      return;
    }
    flushSync(() => setClosing(true));
    scrollBackTo(panel, () => collapse(lists, () => {
      flushSync(() => {
        setClosing(false);
        setAll(false);
      });
      toggle.current?.focus({ preventScroll: true });
    }));
  };
  return (
    <section className="screen results">
      <div className="stack">
        {/* «Your result» is shown in the header (Header title); here it stays for screen readers and the focus on a new screen */}
        <h1 className="visually-hidden">{S.results.heading}</h1>
        <p className="lead">
          {S.results.basedOn(answeredCount(state.answers), state.shown.length, Object.keys(state.mult).length > 0)}
        </p>
        {/* A line between the summary and the hint, nearer the hint; the hint italic and lighter (customer 2026-10-23) */}
        {top.length > 0 && (
          <>
            <div className="rule" role="presentation" />
            <p className="lead hint">
              {S.results.hint[0]} <span className="list-row-go" aria-hidden="true" /> {S.results.hint[1]}
            </p>
          </>
        )}
      </div>
      <div className="scale-legend" aria-hidden="true">
        <span>{S.results.scaleFar}</span>
        <span>{S.results.scaleClose}</span>
      </div>
      {top.length > 0 && (
        <div className={all || closing ? 'panel scale-top open' : 'panel scale-top'}>
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
      {(shown || closing) && hidden && (
        <div className="scale-drop" ref={drop} inert={closing || undefined} aria-hidden={closing || undefined}>
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
      {closing && (
        <div className="see-all scale-lid" aria-hidden="true">
          <span className="btn btn-link skip">{S.results.seeAll}</span>
        </div>
      )}
      {/* At the bottom only «Change answers» (customer 2026-10-23), pinned to the bottom of the screen as on Home: Start
          over is in the header and the menu, Methodology in the menu; «Answer more questions» is gone. */}
      <div className="sticky-actions push-down">
        <Button block onClick={() => dispatch({ type: 'CHANGE_ANSWERS' })}>
          {S.results.changeAnswers}
        </Button>
      </div>
    </section>
  );
}
