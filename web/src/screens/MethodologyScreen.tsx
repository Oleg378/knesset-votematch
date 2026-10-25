import { useRef, useState } from 'react';
import { Accordion } from '../components/Accordion';
import { Button } from '../components/Button';
import { ExternalLink } from '../components/ExternalLink';
import { HebrewTitle } from '../components/HebrewTitle';
import { billUrl } from '../engine/report';
import { scrollBackTo } from '../expandMotion';
import type { BillRef, QuizBills, QuizData, Statement } from '../engine/types';
import { S } from '../strings';
import { dataDate, dataValues, fill, listsOf, T, type Texts } from '../texts';
import type { BillsScreenProps } from './types';

const PAGE = 20;

type Labels = Texts['methodology']['statements'];

/** A template's label: its text before «: » («Topic: {name}» → «Topic»), shown as a fact's label, as on List details. */
const labelOf = (template: string) => template.split(': ')[0]!;
const noPeriod = (text: string) => text.replace(/\.$/, '');
/** The first letter upper-case: a point's text under its label starts as a sentence of its own (customer 2026-10-25). */
const capFirst = (text: string) => text.replace(/\p{L}/u, (c) => c.toUpperCase());

/**
 * A bill as on List details (customer 2026-10-25: «исправь все расхождения со стилем»): the Hebrew title, then facts — the
 * side it pushes the topic, the Knesset, the lists of its sponsors one under another — then the link; no topic role.
 */
function MethodBill({ data, bills, ref_: [id, sign], names, t }: { data: QuizData; bills: QuizBills;
  ref_: BillRef; names: Map<string, string>; t: Labels }) {
  const b = bills.bills[id]!;
  const order = new Map(data.lists.map((l, i) => [l.id, i]));
  // Sponsoring lists: sponsors -> mks[].list, in the order of data.lists.
  const lists = [...new Set(b.sponsors.map((m) => bills.mks[m]?.list).filter((x): x is string => !!x))]
    .sort((x, y) => (order.get(x) ?? 0) - (order.get(y) ?? 0));
  return (
    <li className="bill">
      <HebrewTitle text={b.name_he} className="bill-title" />
      <p className="small fact">
        <span className="fact-label">{labelOf(t.topic)}</span>
        <span className="fact-value">{sign > 0 ? t.sideUp : t.sideDown}</span>
      </p>
      <p className="small fact">
        <span className="fact-label">{S.bills.knessetLabel}</span>
        <span className="fact-value">{b.knesset}</span>
      </p>
      {lists.length ? (
        <p className="small fact">
          <span className="fact-label">{labelOf(t.sponsors)}</span>
          <span>{lists.map((l) => <span key={l} className="fact-value bill-sponsor">{names.get(l) ?? l}</span>)}</span>
        </p>
      ) : (
        <p className="small fact"><span className="fact-value">{noPeriod(t.noSponsors)}</span></p>
      )}
      <ExternalLink href={billUrl(data.params, id)}>{t.billLink}</ExternalLink>
    </li>
  );
}

/**
 * An opened statement as a topic on List details: the statement without quotation marks and its period, the topic and
 * its two directions as facts, which way agreeing counts; then the bills, 20 at a time, «Show more» / «Show less» as
 * «See all» on Results under a line that closes the list.
 */
function StatementBody({ data, bills, st, names, t }: { data: QuizData; bills: QuizBills; st: Statement;
  names: Map<string, string>; t: Labels }) {
  const [n, setN] = useState(PAGE);
  const list = useRef<HTMLUListElement>(null);
  const dir = data.directions[st.d];
  const refs = bills.by_direction[st.d] ?? [];
  const less = () => {
    const ul = list.current;
    const from = ul?.children[PAGE] as HTMLElement | undefined;
    if (!ul || !from) return setN(PAGE);
    scrollBackTo(from, () => setN(PAGE), ul.getBoundingClientRect().bottom - from.getBoundingClientRect().top);
  };
  return (
    <>
      <div className="lines">
        <p className="quote">{noPeriod(st.statement_en)}</p>
        {dir && (
          <>
            <p className="small fact">
              <span className="fact-label">{labelOf(t.topic)}</span>
              <span className="fact-value">{dir.name_en}</span>
            </p>
            <p className="small fact">
              <span className="fact-label">{labelOf(t.up)}</span>
              <span className="fact-value">{noPeriod(dir.plus_en)}</span>
            </p>
            <p className="small fact">
              <span className="fact-label">{labelOf(t.down)}</span>
              <span className="fact-value">{noPeriod(dir.minus_en)}</span>
            </p>
            <p className="small fact">
              <span className="fact-value">{noPeriod(st.key > 0 ? t.agreeCountsUp : t.agreeCountsDown)}</span>
            </p>
          </>
        )}
      </div>
      <div className="stack">
        <h3 className="title-sm">{fill(t.billsCount, { n: refs.length })}</h3>
        <ul ref={list} className="plain-list">
          {refs.slice(0, n).map((r) => (
            <MethodBill key={r[0]} data={data} bills={bills} ref_={r} names={names} t={t} />
          ))}
        </ul>
        {refs.length > PAGE && (
          <div className="see-all bills-more">
            {refs.length > n ? (
              <Button variant="link" className="skip" aria-expanded={false} onClick={() => setN(n + PAGE)}>
                {t.showMore.split(' (')[0]}
              </Button>
            ) : (
              <Button variant="link" className="skip" aria-expanded onClick={less}>
                {S.results.seeLess}
              </Button>
            )}
          </div>
        )}
      </div>
    </>
  );
}

type Section = Texts['methodology']['sections'][number];

/**
 * A section opened, as an opened topic on List details (customer 2026-10-25: «внутри плашки сделай схожее»): its text as
 * the statement there (grey, justified), then each point as a fact — its lead as the small label over its text (the
 * leads are too long for a label column); a point whose lead runs on into its text is one line, no label; the names of
 * its `lists` one per line (after the line `lists.title`, if given); the closing paragraph as the text. No periods at
 * the ends, as there.
 */
function SectionBody({ data, s, v }: { data: QuizData; s: Section; v: ReturnType<typeof dataValues> }) {
  const lists = s.lists ? listsOf(data, s.lists.of) : [];
  const line = s.lists?.title !== undefined && lists.length > 0 ? fill(s.lists.title, { n: lists.length }) : undefined;
  const hasPoints = (s.bullets?.length ?? 0) > 0 || lists.length > 0;
  return (
    <div className="lines method-body">
      {/* the text leads into the points under it: it ends with «:» (customer 2026-10-25), as the file's first section's */}
      {s.text !== undefined && (
        <p className="quote">{hasPoints ? fill(s.text, v).replace(/[.:]?$/, ':') : noPeriod(fill(s.text, v))}</p>
      )}
      {(s.bullets ?? []).map((b, i) => {
        const lead = fill(b.lead, v);
        const text = noPeriod(fill(b.text, v));
        return /[.:]$/.test(lead) ? (
          <p key={i} className="small fact method-point">
            <span className="fact-label">{lead.replace(/[.:]$/, '')}</span>
            <span className="fact-value">{capFirst(text)}</span>
          </p>
        ) : (
          <p key={i} className="small fact method-point"><span className="fact-value">{lead} {text}</span></p>
        );
      })}
      {line !== undefined && <p className="small fact method-point"><span className="fact-label">{line}</span></p>}
      {/* Keys by place: a list of names is fixed for the page, and two lists could share an English name. */}
      {lists.length > 0 && (
        <p className="small fact method-point">
          {lists.map((l, i) => <span key={i} className="fact-value">{l.name_en}</span>)}
        </p>
      )}
      {s.after !== undefined && <p className="quote">{noPeriod(fill(s.after, v))}</p>}
    </div>
  );
}

/** «Made by A and B» with their links (customer 2026-10-24); nothing while the file names nobody. */
function Credits() {
  const c = T.methodology.credits;
  if (!c.people.length) return null;
  return (
    <p className="xsmall credits">
      {c.lead}{' '}
      {c.people.map((p, i) => (
        <span key={p.url}>
          {i > 0 && c.join}
          <ExternalLink href={p.url}>{p.name}</ExternalLink>
        </span>
      ))}
    </p>
  );
}

/**
 * Every text here comes from `methodology` in quiz_texts.json (export/WEB_CONTRACT.md §7). The page as the topics of
 * List details (customer 2026-10-25: «пункт — это Where a list's position comes from, он раскрывается, а пункты внутри
 * него»; they were cards with their text open): every section a band with its title (no period), opening to its text,
 * points, names and closing paragraph; the statements block the same, opening to its text and a row per statement, each
 * row opening to the statement's record. Closed bands keep their text in the page (Accordion `findable`): search
 * engines read it, find in page opens it. The numbers are filled from quiz_data (texts.ts).
 */
export function MethodologyScreen({ data, bills }: BillsScreenProps) {
  const methodology = T.methodology;
  const names = new Map(data.lists.map((l) => [l.id, l.name_en]));
  const v = dataValues(data);
  const t = methodology.statements;
  // The rows in the order of interest (statement_meta: how much a voter cares, 1–5), the most interesting first; equal interest
  // keeps the file order (customer 2026-10-25).
  const rows = [...data.statements].sort((a, b) => b.interest - a.interest);
  return (
    <section className="screen">
      {/* «How it works» is shown in the header (Header title), as on Results; here it stays for screen readers and the focus on a new screen */}
      <h1 className="visually-hidden">{methodology.heading}</h1>
      <div className="stack details-group method-list">
        {methodology.sections.map((s) => (
          <Accordion key={s.title} title={noPeriod(s.title)} findable>
            {() => <SectionBody data={data} s={s} v={v} />}
          </Accordion>
        ))}
        <Accordion title={noPeriod(t.title)} findable>
          {() => (
            <>
              <div className="lines">
                {/* leads into the rows: «:», as a section's text before its points */}
                <p className="quote">{fill(t.text, { statements: data.statements.length }).replace(/[.:]?$/, ':')}</p>
              </div>
              <div className="stack method-rows">
                {rows.map((st) => (
                  <Accordion key={st.q} title={st.title_en}>
                    {() => <StatementBody data={data} bills={bills} st={st} names={names} t={t} />}
                  </Accordion>
                ))}
              </div>
            </>
          )}
        </Accordion>
      </div>
      <Credits />
      <p className="xsmall data-version">
        {fill(t.dataVersion, { fetched: dataDate(data.fetched), generated: dataDate(data.generated), commit: data.source_commit })}
      </p>
    </section>
  );
}
