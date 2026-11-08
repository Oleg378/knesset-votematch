import type { Dispatch } from 'react';
import hero from '../assets/figma/hero.svg';
import stats from '../../../export/stats.json' with { type: 'json' };
import { Button, LinkButton } from '../components/Button';
import { plannedQuestions } from '../engine/flow';
import type { QuizCore } from '../engine/types';
import { PAGE_PATHS, type Action } from '../state/reducer';
import { S } from '../strings';

/**
 * Figma «Home». Renders at once, before any data: the steps (with the number of statements — core + clarifying) appear as
 * soon as quiz_core (~1 KB) has arrived; the chips need no data.
 */
export function StartScreen({ core, dispatch }: { core: QuizCore | null; dispatch: Dispatch<Action> }) {
  const n = core ? plannedQuestions(core.flow) : null;
  const steps = n === null ? null : S.start.steps(n);
  return (
    <section className="screen start">
      <div className="hero">
        <div className="stack">
          <p className="eyebrow">{S.eyebrow}</p>
          <h1 className="title-xl">{S.start.title}</h1>
        </div>
        <img className="hero-graphic" src={hero} alt="" width={150} height={150} />
      </div>
      <p className="tagline">{S.start.tagline}</p>
      <ul className="chips">
        {/* the numbers of bills and former members come with the build (export/stats.json), so the chips need no data (customer 2026-11-08) */}
        <li className="chip">{S.start.chipMembers(stats.mks)}</li>
        <li className="chip">{S.start.chipBills(stats.bills)}</li>
        <li className="chip">{S.start.chipRealVotes}</li>
        <li className="chip">{S.start.chipEveryBill}</li>
        <li className="chip">{S.start.chipNonPartisan}</li>
        <li className="chip">{S.start.chipOpenMethod}</li>
        <li className="chip">{S.start.chipOfficial}</li>
      </ul>
      {steps && (
        <ol className="steps panel">
          {steps.map((t, i) => (
            <li key={i} className="step">
              <span className="step-number" aria-hidden="true">{i + 1}</span>
              {t}
            </li>
          ))}
        </ol>
      )}
      <div className="sticky-actions push-down">
        <Button variant="primary" block onClick={() => dispatch({ type: 'START' })}>
          {S.start.button}
        </Button>
        <LinkButton variant="link" href={PAGE_PATHS.methodology} onClick={() => dispatch({ type: 'OPEN_METHODOLOGY' })}>
          {S.start.howItWorks}
        </LinkButton>
      </div>
    </section>
  );
}
