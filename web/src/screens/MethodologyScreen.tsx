import { useId, useState } from 'react';
import { Accordion } from '../components/Accordion';
import { Button } from '../components/Button';
import { ExternalLink } from '../components/ExternalLink';
import { HebrewTitle } from '../components/HebrewTitle';
import { ListNames } from '../components/ListNames';
import { billUrl } from '../engine/report';
import type { BillRef, QuizBills, QuizData, Statement } from '../engine/types';
import { dataValues, fill, listsOf, T, type Texts } from '../texts';
import type { BillsScreenProps } from './types';

const PAGE = 20;

type Labels = Texts['methodology']['statements'];

function MethodBill({ data, bills, ref_: [id, sign, role], names, t }: { data: QuizData; bills: QuizBills;
  ref_: BillRef; names: Map<string, string>; t: Labels }) {
  const b = bills.bills[id]!;
  const order = new Map(data.lists.map((l, i) => [l.id, i]));
  // Sponsoring lists: sponsors -> mks[].list, in the order of data.lists.
  const lists = [...new Set(b.sponsors.map((m) => bills.mks[m]?.list).filter((x): x is string => !!x))]
    .sort((x, y) => (order.get(x) ?? 0) - (order.get(y) ?? 0));
  return (
    <li className="bill">
      <HebrewTitle text={b.name_he} className="bill-title" />
      <span className="small muted">
        {fill(t.billMeta, { side: sign > 0 ? t.sideUp : t.sideDown, knesset: b.knesset,
          role: role === 'main' ? t.roleMain : t.roleSecondary })}
      </span>
      <span className="small">
        {lists.length ? fill(t.sponsors, { names: lists.map((l) => names.get(l) ?? l).join('; ') }) : t.noSponsors}
      </span>
      <ExternalLink href={billUrl(data.params, id)}>{t.billLink}</ExternalLink>
    </li>
  );
}

function StatementBody({ data, bills, st, names, t }: { data: QuizData; bills: QuizBills; st: Statement;
  names: Map<string, string>; t: Labels }) {
  const [n, setN] = useState(PAGE);
  const dir = data.directions[st.d];
  const refs = bills.by_direction[st.d] ?? [];
  return (
    <>
      <p>{fill(T.explain.quote, { text: st.statement_en })}</p>
      {dir && (
        <div className="stack small">
          <span className="title-sm">{fill(t.topic, { name: dir.name_en })}</span>
          <span>{fill(t.up, { text: dir.plus_en })}</span>
          <span>{fill(t.down, { text: dir.minus_en })}</span>
          <span className="muted">{st.key > 0 ? t.agreeCountsUp : t.agreeCountsDown}</span>
        </div>
      )}
      <span className="title-sm">{fill(t.billsCount, { n: refs.length })}</span>
      <ul className="plain-list">
        {refs.slice(0, n).map((r) => (
          <MethodBill key={r[0]} data={data} bills={bills} ref_={r} names={names} t={t} />
        ))}
      </ul>
      {refs.length > n && (
        <Button variant="link" onClick={() => setN(n + PAGE)}>
          {fill(t.showMore, { n: refs.length - n })}
        </Button>
      )}
    </>
  );
}

type Section = Texts['methodology']['sections'][number];

/**
 * A section as a card (the panel of the question card; customer 2026-10-24): the bold run-in title and the text, the
 * bullets with an italic lead, then the closing paragraph. A section's `lists` is the last line of its bullets (its
 * title, {n} = how many, read as a bullet lead) with the names under it, the rest of them dropping down inside the card;
 * none — no line.
 */
function MethodSection({ data, s, v }: { data: QuizData; s: Section; v: ReturnType<typeof dataValues> }) {
  const id = useId();
  const lists = s.lists ? listsOf(data, s.lists.of) : [];
  const listsLine = s.lists && lists.length > 0 ? fill(s.lists.title, { n: lists.length }) : undefined;
  return (
    <div className="panel method-card">
      <p>
        <strong>{s.title}</strong>{s.text !== undefined && <> {fill(s.text, v)}</>}
      </p>
      {(s.bullets || listsLine) && (
        <ul className="method-bullets">
          {s.bullets?.map((b) => (
            <li key={b.lead}>
              <em>{fill(b.lead, v)}</em> {fill(b.text, v)}
            </li>
          ))}
          {listsLine && <li id={id}><em>{listsLine}</em></li>}
        </ul>
      )}
      {listsLine && <ListNames labelledBy={id} names={lists.map((l) => l.name_en)} />}
      {s.after !== undefined && <p>{fill(s.after, v)}</p>}
    </div>
  );
}

/**
 * Every text here comes from `methodology` in quiz_texts.json (export/WEB_CONTRACT.md §7): the heading, the sections
 * (each a card: bold run-in title, text, bullets with an italic lead, the names of some lists, a closing paragraph)
 * and the labels of the statements block. The numbers are filled from quiz_data (texts.ts).
 */
export function MethodologyScreen({ data, bills, dispatch }: BillsScreenProps) {
  const methodology = T.methodology;
  const names = new Map(data.lists.map((l) => [l.id, l.name_en]));
  const v = dataValues(data);
  const t = methodology.statements;
  return (
    <section className="screen">
      <Button variant="link" onClick={() => dispatch({ type: 'BACK' })}>
        {methodology.back}
      </Button>
      <h1 className="title-lg">{methodology.heading}</h1>
      <div className="stack-lg">
        {methodology.sections.map((s) => <MethodSection key={s.title} data={data} s={s} v={v} />)}
      </div>
      <h2 className="title-md">{fill(t.heading, { statements: data.statements.length })}</h2>
      <div className="stack">
        {data.statements.map((st) => (
          <Accordion key={st.q} title={st.title_en}>
            {() => <StatementBody data={data} bills={bills} st={st} names={names} t={t} />}
          </Accordion>
        ))}
      </div>
      <p className="xsmall muted">{fill(t.dataVersion, { generated: data.generated, commit: data.source_commit })}</p>
    </section>
  );
}
