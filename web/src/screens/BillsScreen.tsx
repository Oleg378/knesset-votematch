import { useMemo, useState } from 'react';
import { Button } from '../components/Button';
import { ExplanationLines } from '../components/ExplanationLines';
import { ExternalLink } from '../components/ExternalLink';
import { HebrewTitle } from '../components/HebrewTitle';
import { contributions, explain, type Evidence } from '../engine/report';
import { billUrl, type BillsFile, type QuizData, type Statement } from '../engine/types';
import { S } from '../strings';
import type { ScreenProps } from './types';

const PAGE = 20;

function BillRow({ data, bills, q, e }: { data: QuizData; bills: BillsFile; q: Statement; e: Evidence }) {
  const b = bills.bills[e.bill]!;
  const direction = data.directions[q.d]?.name_en ?? q.d;
  // No per-bill English summary [У 2026-10-17]: the direction line is the English context.
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

function Group({ data, bills, q, head, items }: { data: QuizData; bills: BillsFile; q: Statement; head: string;
  items: Evidence[] }) {
  const [n, setN] = useState(PAGE);
  return (
    <div className="stack">
      <h2 className="title-md">{head}</h2>
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

export function BillsScreen({ state, dispatch }: ScreenProps) {
  const { data, bills } = state;
  const { list, q } = state.screen.name === 'bills' ? state.screen : { list: '', q: '' };
  const item = useMemo(() => data && contributions(data, list, state.answers, state.mult).find((x) => x.statement.q === q),
    [data, list, q, state.answers, state.mult]);
  if (!data || !bills || !item) return null;
  const { lines, evidence } = explain(data, bills, list, item.statement, item.a, item.p, item.c, state.mult);
  return (
    <section className="screen">
      <Button variant="link" onClick={() => dispatch({ type: 'BACK' })}>
        {S.bills.back}
      </Button>
      <div className="stack">
        <h1 className="title-lg">{item.statement.title_en}</h1>
        <ExplanationLines lines={lines} />
      </div>
      <Group data={data} bills={bills} q={item.statement} head={S.bills.yourWay(evidence.filter((e) => e.same).length)}
        items={evidence.filter((e) => e.same)} />
      <Group data={data} bills={bills} q={item.statement} head={S.bills.otherWay(evidence.filter((e) => !e.same).length)}
        items={evidence.filter((e) => !e.same)} />
    </section>
  );
}
