import hero from '../assets/figma/hero.svg';
import { Button } from '../components/Button';
import { S } from '../strings';
import type { ScreenProps } from './types';

/** Figma «Home». The statement count is the number a user answers: core + clarifying (flow, from the export). */
export function StartScreen({ core, dispatch }: ScreenProps) {
  const n = core.flow.core + core.flow.clarify;
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
        <li className="chip">{S.start.chipStatements(n)}</li>
        <li className="chip">{S.start.chipTime}</li>
        <li className="chip">{S.start.chipAnonymous}</li>
      </ul>
      <ol className="steps panel">
        {S.start.steps(n).map((t, i) => (
          <li key={i} className="step">
            <span className="step-number" aria-hidden="true">{i + 1}</span>
            {t}
          </li>
        ))}
      </ol>
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
