import { DropDown } from './DropDown';
import { HIGHLIGHT } from '../uiConstants';

interface Props {
  /** Id of the line that names the lists («22 lists have no record…»), drawn by the caller as the last bullet. */
  labelledBy: string;
  names: string[];
}

/**
 * Names of lists inside a Methodology section card (a section's `lists`, customer 2026-10-24): the first HIGHLIGHT
 * names, the rest drop down inside the card with «See all» and go back with «Show less» at their end (DropDown.tsx,
 * the same as a collapsed card). A row is the name only: nothing to press. With HIGHLIGHT names or fewer, all are shown
 * and there is no button. Styles: app.css «Names of lists».
 */
export function ListNames({ labelledBy, names }: Props) {
  const top = names.slice(0, HIGHLIGHT);
  const rest = names.slice(HIGHLIGHT);
  // Keys by place: a list of names is fixed for the page, and two lists could share an English name.
  const row = (name: string, i: number) => <li key={i}>{name}</li>;
  return (
    <div className="list-names">
      <ul className="list-names-rows" aria-labelledby={labelledBy}>{top.map(row)}</ul>
      {rest.length > 0 && (
        <DropDown backTo={labelledBy} className="list-names-more" dropClassName="list-names-drop">
          {() => <ul className="list-names-rows" aria-labelledby={labelledBy}>{rest.map(row)}</ul>}
        </DropDown>
      )}
    </div>
  );
}
