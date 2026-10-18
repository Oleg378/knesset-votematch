import { useMemo, useState } from 'react';
import { Button } from '../components/Button';
import { Card } from '../components/Card';
import { ExplanationLines } from '../components/ExplanationLines';
import { Note } from '../components/Note';
import { formatCloseness } from '../engine/format';
import { match } from '../engine/match';
import { contributions, explain, type Contribution } from '../engine/report';
import type { Mult, QuizBills, QuizData } from '../engine/types';
import { S } from '../strings';
import type { BillsScreenProps } from './types';

const PER = 5; // statements per section before «Show all» (quiz_cli.py SHOW)

function Section(props: { data: QuizData; bills: QuizBills; list: string; mult: Mult; head: string;
  items: Contribution[]; onOpen: (q: string) => void }) {
  const { data, bills, list, mult, head, items, onOpen } = props;
  const [all, setAll] = useState(false);
  const shown = all ? items : items.slice(0, PER);
  return (
    <div className="stack">
      <h2 className="title-md">{head}</h2>
      {items.length === 0 && <p className="small muted">{S.details.none}</p>}
      {shown.map((x) => (
        <Card key={x.statement.q} onClick={() => onOpen(x.statement.q)}>
          <span className="title-sm">{x.statement.title_en}</span>
          <ExplanationLines lines={explain(data, bills, list, x.statement, x.a, x.p, x.c, mult).lines} />
          <span className="small link-text">{S.details.openBills}</span>
        </Card>
      ))}
      {items.length > PER && (
        <Button variant="link" onClick={() => setAll(!all)}>
          {all ? S.details.showLess : S.details.showAll(items.length - PER)}
        </Button>
      )}
    </div>
  );
}

export function DetailsScreen({ data, bills, state, dispatch }: BillsScreenProps) {
  const list = state.screen.name === 'details' ? state.screen.list : '';
  const row = useMemo(() => match(data, state.answers, state.mult).find((r) => r.id === list),
    [data, state.answers, state.mult, list]);
  const rows = useMemo(() => contributions(data, list, state.answers, state.mult),
    [data, list, state.answers, state.mult]);
  if (!row) return null;
  const plus = rows.filter((x) => x.c > 0);
  const minus = [...rows].reverse().filter((x) => x.c < 0);
  const onOpen = (q: string) => dispatch({ type: 'OPEN_BILLS', q });
  return (
    <section className="screen">
      <Button variant="link" onClick={() => dispatch({ type: 'BACK' })}>
        {S.details.back}
      </Button>
      <div className="stack">
        <h1 className="title-lg">{row.name_en}</h1>
        {row.closeness !== null && <p className="muted">{S.details.closeness(formatCloseness(row.closeness))}</p>}
        {row.note && <Note>{row.note}</Note>}
      </div>
      <Section data={data} bills={bills} list={list} mult={state.mult} head={S.details.fits(plus.length)} items={plus}
        onOpen={onOpen} />
      <Section data={data} bills={bills} list={list} mult={state.mult} head={S.details.misfits(minus.length)}
        items={minus}
        onOpen={onOpen} />
    </section>
  );
}
