import { useMemo, type CSSProperties } from 'react';
import { Accordion } from '../components/Accordion';
import { BillLists } from '../components/BillLists';
import { ExplanationLines } from '../components/ExplanationLines';
import { Note } from '../components/Note';
import { formatCloseness, roundCloseness } from '../engine/format';
import { match } from '../engine/match';
import { contributions, explain, type Contribution } from '../engine/report';
import type { Mult, QuizBills, QuizData } from '../engine/types';
import { renderLinesDetails, renderNotePart, S } from '../strings';
import type { BillsScreenProps } from './types';

/**
 * One section of List details: every topic a collapsed line, as the statements on Methodology; open, it shows the
 * explanation and the bills behind it (customer 2026-10-23: List details and the bills page made one page).
 */
function Section(props: { data: QuizData; bills: QuizBills; list: string; mult: Mult; head: string;
  items: Contribution[] }) {
  const { data, bills, list, mult, head, items } = props;
  return (
    <div className="stack details-group">
      {/* the words only, no count (customer 2026-10-24: «убери matches вообще») */}
      <h2 className="details-section">{head}</h2>
      {items.length === 0 && <p className="small muted">{S.details.none}</p>}
      {items.map((x) => (
        <Accordion key={x.statement.q} title={x.statement.title_en}>
          {() => {
            const { lines, evidence } = explain(data, bills, list, x.statement, x.a, x.p, x.c, mult);
            return (
              <>
                {/* the «price» caveat is said once for the page, under the closeness; the rest as short facts */}
                <ExplanationLines lines={renderLinesDetails(lines.filter((l) => l.key !== 'caveatPrice'))} />
                <BillLists data={data} bills={bills} evidence={evidence} />
              </>
            );
          }}
        </Accordion>
      ))}
    </div>
  );
}

export function DetailsScreen({ data, bills, state }: BillsScreenProps) {
  const list = state.screen.name === 'details' ? state.screen.list : '';
  const all = useMemo(() => match(data, state.answers, state.mult), [data, state.answers, state.mult]);
  const row = all.find((r) => r.id === list);
  const rank = all.filter((r) => r.ranked).findIndex((r) => r.id === list) + 1; // 0: not ranked
  const rows = useMemo(() => contributions(data, list, state.answers, state.mult),
    [data, list, state.answers, state.mult]);
  if (!row) return null;
  const plus = rows.filter((x) => x.c > 0);
  const minus = [...rows].reverse().filter((x) => x.c < 0);
  return (
    <section className="screen">
      <div className="stack details-head">
        <h1 className="title-lg details-title">{row.name_en}</h1>
        {/* Under the name a line, then the caveat, then the closeness (customer 2026-10-24: «после названия партии линия
            и надпись Shows, потом уже линия 70 %»); the caveat once for every topic (customer 2026-10-23), the
            explanation lines in the topics leave it out */}
        <div className="details-rule" role="presentation" />
        <p className="small details-caveat">{S.details.priceNote}</p>
        {/* Closeness as a Results row without its band (customer 2026-10-23): «Closeness to you» above the scale's line
            with the list's dot — light blue on the page — and on the line's row the rank in its circle and the percent */}
        {row.closeness !== null && (
          <div className="list-row details-row">
            <span className="list-row-rank">{rank > 0 && <span>{S.results.rank(rank)}</span>}</span>
            <span className="list-row-name">{S.details.closenessTitle}</span>
            <span className="scale-line details-scale" aria-hidden="true">
              <span className="scale-dot" style={{ '--at': (roundCloseness(row.closeness) + 1) / 2 } as CSSProperties} />
            </span>
            <span className="list-row-value">{formatCloseness(row.closeness)}</span>
          </div>
        )}
        {/* each note on its own line in the one band, not joined by «; » (customer 2026-10-25) */}
        {row.notes.length > 0 && (
          <Note>{row.notes.map((p) => <span key={p.key} className="note-line">{renderNotePart(p)}</span>)}</Note>
        )}
      </div>
      <Section data={data} bills={bills} list={list} mult={state.mult} head={S.details.fits(plus.length)} items={plus} />
      <Section data={data} bills={bills} list={list} mult={state.mult} head={S.details.misfits(minus.length)}
        items={minus} />
    </section>
  );
}
