import type { Dispatch } from 'react';
import hero from '../assets/figma/hero.svg';
import { Button } from '../components/Button';
import { plannedQuestions } from '../engine/flow';
import type { QuizCore } from '../engine/types';
import type { Action } from '../state/reducer';
import { S } from '../strings';

/**
 * Figma «Home». Renders at once, before any data: the number of statements (core + clarifying, customer 2026-10-18:
 * «15 statements») appears as soon as quiz_core (~1 KB) has arrived.
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
        {n !== null && <li className="chip">{S.start.chipStatements(n)}</li>}
        <li className="chip">{S.start.chipTime}</li>
        <li className="chip">{S.start.chipAnonymous}</li>
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
        <Button variant="link" onClick={() => dispatch({ type: 'OPEN_METHODOLOGY' })}>
          {S.start.howItWorks}
        </Button>
      </div>
    </section>
  );
}
