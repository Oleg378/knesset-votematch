import { useId, useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { collapse, expand, scrollBackTo } from '../expandMotion';
import { S } from '../strings';
import { HIGHLIGHT } from '../uiConstants';

interface Props {
  /** Already filled («No record in the Knesset (22)»). */
  title: string;
  names: string[];
}

/**
 * Names of lists in a panel, as the Results panel (ResultsScreen.tsx) — Methodology, a section's `lists`: the title
 * line and the first HIGHLIGHT names, the rest drop down from the panel with «See all» and go back into it with «Show
 * less» at their end, the same motion and the same lid (expandMotion.ts, app.css «Results» and «Names of lists»).
 * A row is the name only: nothing to press. With HIGHLIGHT names or fewer, all are in the panel and there is no button.
 */
export function ListNames({ title, names }: Props) {
  const id = useId();
  const top = names.slice(0, HIGHLIGHT);
  const rest = names.slice(HIGHLIGHT);
  const [all, setAll] = useState(false);
  const [closing, setClosing] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  const drop = useRef<HTMLDivElement>(null);
  const showAll = (on: boolean) => {
    if (on) {
      flushSync(() => setAll(true));
      if (drop.current) expand(drop.current);
      // «See all» is gone: the focus goes to the names that dropped down, without scrolling the page.
      drop.current?.querySelector<HTMLElement>('ul')?.focus({ preventScroll: true });
      return;
    }
    const lists = drop.current;
    const panel = lists?.previousElementSibling;
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
  // Keys by place: a list of names is fixed for the page, and two lists could share an English name.
  const row = (name: string, i: number) => <li key={i}>{name}</li>;
  return (
    <div className="list-names">
      <div className={all || closing ? 'panel scale-top open' : 'panel scale-top'}>
        <p className="title-sm list-names-title" id={id}>{title}</p>
        <ul className="list-names-rows" aria-labelledby={id}>{top.map(row)}</ul>
        {rest.length > 0 && !all && (
          <div className="see-all">
            <button type="button" ref={toggle} className="btn btn-link skip" aria-expanded="false"
              onClick={() => showAll(true)}>
              {S.results.seeAll}
            </button>
          </div>
        )}
      </div>
      {(all || closing) && rest.length > 0 && (
        <div className="scale-drop" ref={drop} inert={closing || undefined} aria-hidden={closing || undefined}>
          <ul className="list-names-rows" aria-labelledby={id} tabIndex={-1}>{rest.map(row)}</ul>
          <div className="see-all">
            <button type="button" className="btn btn-link skip" aria-expanded="true" onClick={() => showAll(false)}>
              {S.results.seeLess}
            </button>
          </div>
        </div>
      )}
      {closing && (
        <div className="see-all scale-lid" aria-hidden="true">
          <span className="btn btn-link skip">{S.results.seeAll}</span>
        </div>
      )}
    </div>
  );
}
