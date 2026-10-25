import { useRef, useState } from 'react';
import { billUrl, type Evidence } from '../engine/report';
import type { QuizBills, QuizData } from '../engine/types';
import { scrollBackTo } from '../expandMotion';
import { S } from '../strings';
import { Button } from './Button';
import { ExternalLink } from './ExternalLink';
import { HebrewTitle } from './HebrewTitle';

const PAGE = 20;

function BillRow({ data, bills, e }: { data: QuizData; bills: QuizBills; e: Evidence }) {
  const b = bills.bills[e.bill]!;
  // No English summary [У 2026-10-17]; under the title only the Knesset and the sponsors, as facts in two columns (customer
  // 2026-10-25: no topic role, no direction — the topic's title and statement above say what the bills are about).
  return (
    <li className="bill">
      <HebrewTitle text={b.name_he} className="bill-title" />
      <p className="small fact">
        <span className="fact-label">{S.bills.knessetLabel}</span>
        <span className="fact-value">{b.knesset}</span>
      </p>
      <p className="small fact">
        <span className="fact-label">{S.bills.sponsoredByLabel}</span>
        <span>
          {e.authors.slice(0, 2).map(([p, name]) => (
            <span key={name} className="fact-value bill-sponsor">{name} {S.bills.sponsorPlace(p)}</span>
          ))}
        </span>
      </p>
      <ExternalLink href={billUrl(data.params, e.bill)}>{S.bills.link}</ExternalLink>
    </li>
  );
}

function Group({ data, bills, head, items }: { data: QuizData; bills: QuizBills; head: { words: string; n: number };
  items: Evidence[] }) {
  const [n, setN] = useState(PAGE);
  const list = useRef<HTMLUListElement>(null);
  // «Show less»: back up to where the hidden bills start (the 21st), then hide them, so «Show more» stands where they were
  const less = () => {
    const ul = list.current;
    const from = ul?.children[PAGE] as HTMLElement | undefined;
    if (!ul || !from) return setN(PAGE);
    scrollBackTo(from, () => setN(PAGE), ul.getBoundingClientRect().bottom - from.getBoundingClientRect().top);
  };
  return (
    <div className="stack">
      {/* the count in a light blue circle as the rank on top of the page, no brackets (customer 2026-10-25) */}
      <h3 className="title-sm bills-head">{head.words} <span className="count-badge"><span>{head.n}</span></span></h3>
      {items.length === 0 ? (
        <p className="small muted">{S.bills.none}</p>
      ) : (
        <ul ref={list} className="plain-list">
          {items.slice(0, n).map((e) => (
            <BillRow key={e.bill} data={data} bills={bills} e={e} />
          ))}
        </ul>
      )}
      {/* as «See all» / «Show less» on Results: centred, blue, a chevron down, up once all are shown; a line under it closes
          the list (customer 2026-10-25: «Show more» adds 20, «после ещё 20 — Show less») */}
      {items.length > PAGE && (
        <div className="see-all bills-more">
          {items.length > n ? (
            <Button variant="link" className="skip" aria-expanded={false} onClick={() => setN(n + PAGE)}>
              {S.bills.showMore}
            </Button>
          ) : (
            <Button variant="link" className="skip" aria-expanded onClick={less}>
              {S.results.seeLess}
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

/** The bills of one statement by the list's former MKs: the user's way, then the other way (it was the Bills screen). */
export function BillLists({ data, bills, evidence }: { data: QuizData; bills: QuizBills; evidence: Evidence[] }) {
  const same = evidence.filter((e) => e.same);
  const other = evidence.filter((e) => !e.same);
  return (
    <>
      <Group data={data} bills={bills} head={S.bills.yourWay(same.length)} items={same} />
      <Group data={data} bills={bills} head={S.bills.otherWay(other.length)} items={other} />
    </>
  );
}
