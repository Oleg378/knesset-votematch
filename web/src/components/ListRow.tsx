import { formatCloseness } from '../engine/format';
import { S } from '../strings';
import { ClosenessBar } from './ClosenessBar';
import { Note } from './Note';

interface Props {
  rank: number | null;
  name: string;
  closeness: number | null;
  note: string;
  onClick?: () => void;
}

export function ListRow({ rank, name, closeness, note, onClick }: Props) {
  const content = (
    <>
      <span className="list-row-rank">{rank === null ? '' : S.results.rank(rank)}</span>
      <span className="list-row-name">{name}</span>
      <span className="list-row-value">
        <span className="visually-hidden">{S.results.closenessLabel} </span>
        {closeness === null ? S.results.notComputable : formatCloseness(closeness)}
      </span>
      <span className="list-row-extra">
        {closeness !== null && <ClosenessBar value={closeness} />}
        {note && <Note>{note}</Note>}
      </span>
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
