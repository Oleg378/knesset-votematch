import { useId, useState, type ReactNode } from 'react';
import { Accordion } from '../components/Accordion';
import { Button } from '../components/Button';
import { DropDown } from '../components/DropDown';
import { ExternalLink } from '../components/ExternalLink';
import { HebrewTitle } from '../components/HebrewTitle';
import { billUrl } from '../engine/report';
import type { BillRef, QuizBills, QuizData, Statement } from '../engine/types';
import { dataValues, fill, listsOf, T, type Texts } from '../texts';
import { CARD_COLLAPSE_OVER, CARD_PREVIEW } from '../uiConstants';
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

/** One item of a card: a bullet, a name of a list, a statement row or a paragraph (a section's `after`). */
interface Item {
  key: string;
  kind: 'bullet' | 'name' | 'row' | 'para';
  node: ReactNode;
}

/** Items in their blocks: bullets in one list, names in one list of bands, rows in one stack; a paragraph alone. */
function renderItems(items: Item[], namesLabel: string): ReactNode[] {
  const groups: Item[][] = [];
  for (const it of items) {
    const last = groups.at(-1);
    if (last && last[0]!.kind === it.kind && it.kind !== 'para') last.push(it);
    else groups.push([it]);
  }
  return groups.map((g) => {
    const { key, kind } = g[0]!;
    const nodes = g.map((i) => i.node);
    if (kind === 'bullet') return <ul key={key} className="method-bullets">{nodes}</ul>;
    if (kind === 'name') return <ul key={key} className="list-names-rows" aria-labelledby={namesLabel}>{nodes}</ul>;
    if (kind === 'row') return <div key={key} className="stack method-rows">{nodes}</div>;
    return nodes[0];
  });
}

/**
 * A card of the page (the panel of the question card; customer 2026-10-24): its title (with the text, for a section),
 * then its items. One rule for every card (uiConstants.ts): with more than CARD_COLLAPSE_OVER items only the first
 * CARD_PREVIEW are shown, the rest drop down inside the card with «See all», «Show less» at their end
 * (DropDown.tsx: it scrolls back to the title, then closes).
 */
function MethodCard({ head, items, namesLabel }: { head: (id: string) => ReactNode; items: Item[];
  namesLabel?: string }) {
  const id = useId();
  const fold = items.length > CARD_COLLAPSE_OVER;
  const label = namesLabel ?? id;
  return (
    <div className="panel method-card">
      {head(id)}
      {renderItems(fold ? items.slice(0, CARD_PREVIEW) : items, label)}
      {fold && (
        <DropDown backTo={id} className="fold" dropClassName="fold-body">
          {() => renderItems(items.slice(CARD_PREVIEW), label)}
        </DropDown>
      )}
    </div>
  );
}

/**
 * A section as a card: the bold run-in title and the text, then its items — the bullets with an italic lead, the names
 * of its `lists` (after the line `lists.title` as the last bullet, if given; else right after the text) on bands, the
 * closing paragraph.
 */
function MethodSection({ data, s, v }: { data: QuizData; s: Section; v: ReturnType<typeof dataValues> }) {
  const lineId = useId();
  const lists = s.lists ? listsOf(data, s.lists.of) : [];
  const line = s.lists?.title !== undefined && lists.length > 0 ? fill(s.lists.title, { n: lists.length }) : undefined;
  const items: Item[] = [
    ...(s.bullets ?? []).map((b, i): Item => ({ key: `b${i}`, kind: 'bullet',
      node: <li key={`b${i}`}><em>{fill(b.lead, v)}</em> {fill(b.text, v)}</li> })),
    ...(line !== undefined ? [{ key: 'line', kind: 'bullet', node: <li key="line" id={lineId}><em>{line}</em></li> } as Item] : []),
    // Keys by place: a list of names is fixed for the page, and two lists could share an English name.
    ...lists.map((l, i): Item => ({ key: `n${i}`, kind: 'name', node: <li key={`n${i}`}>{l.name_en}</li> })),
    ...(s.after !== undefined ? [{ key: 'after', kind: 'para', node: <p key="after">{fill(s.after, v)}</p> } as Item] : []),
  ];
  return (
    <MethodCard items={items} namesLabel={line !== undefined ? lineId : undefined} head={(id) => (
      <p id={id}>
        <strong>{s.title}</strong>{s.text !== undefined && <> {fill(s.text, v)}</>}
      </p>
    )} />
  );
}

/**
 * Every text here comes from `methodology` in quiz_texts.json (export/WEB_CONTRACT.md §7): the heading, the sections
 * (each a card: bold run-in title, text, bullets with an italic lead, the names of some lists, a closing paragraph)
 * and the labels of the statements block (a card too: its title in the same style, then a row per statement). Long
 * cards collapse by one rule (MethodCard). The numbers are filled from quiz_data (texts.ts).
 */
export function MethodologyScreen({ data, bills, dispatch }: BillsScreenProps) {
  const methodology = T.methodology;
  const names = new Map(data.lists.map((l) => [l.id, l.name_en]));
  const v = dataValues(data);
  const t = methodology.statements;
  const heading = fill(t.heading, { statements: data.statements.length });
  const rows = data.statements.map((st): Item => ({ key: `q${st.q}`, kind: 'row', node: (
    <Accordion key={`q${st.q}`} title={st.title_en}>
      {() => <StatementBody data={data} bills={bills} st={st} names={names} t={t} />}
    </Accordion>
  ) }));
  return (
    <section className="screen">
      <Button variant="link" onClick={() => dispatch({ type: 'BACK' })}>
        {methodology.back}
      </Button>
      <h1 className="title-lg">{methodology.heading}</h1>
      <div className="stack-lg">
        {methodology.sections.map((s) => <MethodSection key={s.title} data={data} s={s} v={v} />)}
      </div>
      <MethodCard items={rows} head={(id) => <h2 id={id} className="method-title">{heading}</h2>} />
      <p className="xsmall muted">{fill(t.dataVersion, { generated: data.generated, commit: data.source_commit })}</p>
    </section>
  );
}
