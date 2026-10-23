import { useState } from 'react';
import { Accordion } from '../components/Accordion';
import { Button } from '../components/Button';
import { ExternalLink } from '../components/ExternalLink';
import { HebrewTitle } from '../components/HebrewTitle';
import { billUrl, type BillRef, type BillsFile, type QuizData, type Statement } from '../engine/types';
import { S } from '../strings';
import type { ScreenProps } from './types';

const PAGE = 20;
const M = S.methodology;

function MethodBill({ data, bills, ref_: [id, sign, role], names }: { data: QuizData; bills: BillsFile; ref_: BillRef;
  names: Map<string, string> }) {
  const b = bills.bills[id]!;
  const order = new Map(data.lists.map((l, i) => [l.id, i]));
  // Sponsoring lists: sponsors -> mks[].list, in the order of data.lists.
  const lists = [...new Set(b.sponsors.map((m) => bills.mks[m]?.list).filter((x): x is string => !!x))]
    .sort((x, y) => (order.get(x) ?? 0) - (order.get(y) ?? 0));
  return (
    <li className="bill">
      <HebrewTitle text={b.name_he} className="bill-title" />
      <span className="small muted">{M.billMeta(b.knesset, role, sign > 0)}</span>
      <span className="small">
        {lists.length ? M.sponsoringLists(lists.map((l) => names.get(l) ?? l).join('; ')) : M.noSponsors}
      </span>
      <ExternalLink href={billUrl(data.params, id)}>{S.bills.link}</ExternalLink>
    </li>
  );
}

function StatementBody({ data, bills, st, names }: { data: QuizData; bills: BillsFile; st: Statement;
  names: Map<string, string> }) {
  const [n, setN] = useState(PAGE);
  const dir = data.directions[st.d];
  const refs = bills.by_direction[st.d] ?? [];
  return (
    <>
      <p>{`“${st.statement_en}”`}</p>
      {dir && (
        <div className="stack small">
          <span className="title-sm">{M.direction(dir.name_en)}</span>
          <span>{M.plus(dir.plus_en)}</span>
          <span>{M.minus(dir.minus_en)}</span>
          <span className="muted">{M.agreeMeans(st.key > 0)}</span>
        </div>
      )}
      <span className="title-sm">{M.billsCount(refs.length)}</span>
      <ul className="plain-list">
        {refs.slice(0, n).map((r) => (
          <MethodBill key={r[0]} data={data} bills={bills} ref_={r} names={names} />
        ))}
      </ul>
      {refs.length > n && (
        <Button variant="link" onClick={() => setN(n + PAGE)}>
          {M.showMore(refs.length - n)}
        </Button>
      )}
    </>
  );
}

export function MethodologyScreen({ state, dispatch }: ScreenProps) {
  const { data, bills } = state;
  if (!data || !bills) return null;
  const names = new Map(data.lists.map((l) => [l.id, l.name_en]));
  return (
    <section className="screen">
      <Button variant="link" onClick={() => dispatch({ type: 'BACK' })}>
        {M.back}
      </Button>
      <h1 className="title-lg">{M.heading}</h1>
      <div className="stack-lg">
        {M.paragraphs.map((p, i) => (
          <p key={i}>{p}</p>
        ))}
      </div>
      <h2 className="title-md">{M.statementsHeading(data.statements.length)}</h2>
      <div className="stack">
        {data.statements.map((st) => (
          <Accordion key={st.q} title={st.title_en}>
            {() => <StatementBody data={data} bills={bills} st={st} names={names} />}
          </Accordion>
        ))}
      </div>
      <p className="xsmall muted">{M.dataVersion(data.generated, data.source_commit)}</p>
    </section>
  );
}
