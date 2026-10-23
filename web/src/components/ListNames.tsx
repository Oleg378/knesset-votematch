import { useRef, useState } from 'react';
import { flushSync } from 'react-dom';
import { collapse, expand, scrollBackTo } from '../expandMotion';
import { S } from '../strings';
import { HIGHLIGHT } from '../uiConstants';

interface Props {
  /** Id of the line that names the lists («22 lists have no record…»), drawn by the caller as the last bullet. */
  labelledBy: string;
  names: string[];
}

/**
 * Names of lists inside a Methodology section card (a section's `lists`, customer 2026-10-24): the first HIGHLIGHT
 * names, the rest drop down inside the card with «See all» and go back with «Show less» at their end — the motion of
 * the Results panel (expandMotion.ts); while they close, a lid with «See all» stands under them where the button will
 * be. «Show less» first scrolls back to the line that names the lists. A row is the name only: nothing to press. With
 * HIGHLIGHT names or fewer, all are shown and there is no button. Styles: app.css «Names of lists».
 */
export function ListNames({ labelledBy, names }: Props) {
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
    const label = document.getElementById(labelledBy);
    if (closing) return;
    if (!lists || !label) {
      flushSync(() => setAll(false));
      toggle.current?.focus();
      return;
    }
    flushSync(() => setClosing(true));
    scrollBackTo(label, () => collapse(lists, () => {
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
      <ul className="list-names-rows" aria-labelledby={labelledBy}>{top.map(row)}</ul>
      {rest.length > 0 && !all && (
        <div className="see-all">
          <button type="button" ref={toggle} className="btn btn-link skip" aria-expanded="false"
            onClick={() => showAll(true)}>
            {S.results.seeAll}
          </button>
        </div>
      )}
      {all && rest.length > 0 && (
        <div className="list-names-drop" ref={drop} inert={closing || undefined} aria-hidden={closing || undefined}>
          <ul className="list-names-rows" aria-labelledby={labelledBy} tabIndex={-1}>{rest.map(row)}</ul>
          <div className="see-all">
            <button type="button" className="btn btn-link skip" aria-expanded="true" onClick={() => showAll(false)}>
              {S.results.seeLess}
            </button>
          </div>
        </div>
      )}
      {closing && (
        <div className="see-all" aria-hidden="true">
          <span className="btn btn-link skip">{S.results.seeAll}</span>
        </div>
      )}
    </div>
  );
}
