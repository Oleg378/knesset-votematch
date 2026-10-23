import type { CSSProperties } from 'react';
import { formatCloseness, roundCloseness } from '../engine/format';
import { S } from '../strings';
import { Note } from './Note';

interface Props {
  rank: number | null;
  name: string;
  closeness: number | null;
  note: string;
  onClick?: () => void;
}

/**
 * A list on the Results scale (customer 2026-10-22): rank, name, closeness, and a dot on the −100%…+100% line under them.
 * Every row's line is the same width, so the dots of all lists read as one scale. A row that opens List details ends with
 * a round arrow button after the closeness, the same on every such row (customer 2026-10-23).
 */
export function ListRow({ rank, name, closeness, note, onClick }: Props) {
  const at = closeness === null ? null : (roundCloseness(closeness) + 1) / 2; // the dot stands at the value shown
  const content = (
    <>
      <span className="list-row-rank">{rank === null ? '' : <span>{S.results.rank(rank)}</span>}</span>
      <span className="list-row-name">{name}</span>
      <span className="list-row-value">
        <span className="visually-hidden">{S.results.closenessLabel} </span>
        {closeness === null ? S.results.notComputable : formatCloseness(closeness)}
        {onClick && <span className="list-row-go" aria-hidden="true" />}
      </span>
      {at !== null && (
        <span className="scale-line" aria-hidden="true">
          <span className="scale-dot" style={{ '--at': at } as CSSProperties} />
        </span>
      )}
      {note && <Note>{note}</Note>}
    </>
  );
  return onClick ? (
    <button type="button" className="list-row" onClick={onClick}>
      {content}
    </button>
  ) : (
    <div className="list-row">{content}</div>
  );
}
