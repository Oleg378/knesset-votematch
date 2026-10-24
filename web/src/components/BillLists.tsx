import { useState } from 'react';
import { billUrl, type Evidence } from '../engine/report';
import type { QuizBills, QuizData, Statement } from '../engine/types';
import { S } from '../strings';
import { Button } from './Button';
import { ExternalLink } from './ExternalLink';
import { HebrewTitle } from './HebrewTitle';

const PAGE = 20;

function BillRow({ data, bills, q, e }: { data: QuizData; bills: QuizBills; q: Statement; e: Evidence }) {
  const b = bills.bills[e.bill]!;
  const direction = data.directions[q.d]?.name_en ?? q.d;
  // No English summary [У 2026-10-17]: the direction line is the English context.
  return (
    <li className="bill">
      <HebrewTitle text={b.name_he} className="bill-title" />
      <span className="small muted">{S.bills.meta(b.knesset, e.role, e.sign > 0, direction)}</span>
      <span className="small">
        {S.bills.sponsoredBy(e.authors.slice(0, 2).map(([p, name]) => S.bills.sponsor(name, p)).join(', '))}
      </span>
      <ExternalLink href={billUrl(data.params, e.bill)}>{S.bills.link}</ExternalLink>
    </li>
  );
}

function Group({ data, bills, q, head, items }: { data: QuizData; bills: QuizBills; q: Statement; head: string;
  items: Evidence[] }) {
  const [n, setN] = useState(PAGE);
  return (
    <div className="stack">
      <h3 className="title-sm">{head}</h3>
      {items.length === 0 ? (
        <p className="small muted">{S.bills.none}</p>
      ) : (
        <ul className="plain-list">
          {items.slice(0, n).map((e) => (
            <BillRow key={e.bill} data={data} bills={bills} q={q} e={e} />
          ))}
        </ul>
      )}
      {items.length > n && (
        <Button variant="link" onClick={() => setN(n + PAGE)}>
          {S.bills.showMore(items.length - n)}
        </Button>
      )}
    </div>
  );
}

/** The bills of one statement by the list's former MKs: the user's way, then the other way (it was the Bills screen). */
export function BillLists({ data, bills, q, evidence }: { data: QuizData; bills: QuizBills; q: Statement;
  evidence: Evidence[] }) {
  const same = evidence.filter((e) => e.same);
  const other = evidence.filter((e) => !e.same);
  return (
    <>
      <Group data={data} bills={bills} q={q} head={S.bills.yourWay(same.length)} items={same} />
      <Group data={data} bills={bills} q={q} head={S.bills.otherWay(other.length)} items={other} />
    </>
  );
}
