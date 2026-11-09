import type { Dispatch } from 'react';
import hero from '../assets/figma/hero.svg';

/** hero.svg geometry: the arc's centre, the middle ring the dot runs on, the dot's radius (Figma «Your seat», 9.6 px). */
const HERO = { cx: 75, cy: 122, ring: 50, r: 4.8, halo: 9.5 };
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
        {/* The arc (hero.svg) and, on top of it, the blue dot swinging along the middle ring (customer 2026-11-08); the SVG
            itself carries no dot. The dot's resting place, where reduced motion leaves it, is the seat of the Figma graphic. */}
        <span className="hero-art" aria-hidden="true">
          <img className="hero-graphic" src={hero} alt="" width={150} height={150} />
          <svg className="hero-dot" viewBox="0 0 150 150">
            <g>
              {/* The halo: in the Figma graphic the six seats around the dot were half as pale, so the dot stood out; it moves
                  with the dot as a half-transparent disc of the page colour (customer 2026-11-09). */}
              <circle className="hero-halo" cx={HERO.cx + HERO.ring} cy={HERO.cy} r={HERO.halo} />
              <circle cx={HERO.cx + HERO.ring} cy={HERO.cy} r={HERO.r} fill="currentColor" />
            </g>
          </svg>
        </span>
      </div>
      <p className="tagline">{S.start.tagline}</p>
      <ul className="chips">
        {/* the numbers of bills and former members come with the build (export/stats.json), so the chips need no data (customer 2026-11-08) */}
        <li className="chip">{S.start.chipBills(stats.bills)}</li>
        <li className="chip">{S.start.chipMembers(stats.mks)}</li>
        <li className="chip">{S.start.chipRealVotes}</li>
        <li className="chip">{S.start.chipEveryBill}</li>
        <li className="chip">{S.start.chipNonPartisan}</li>
        <li className="chip">{S.start.chipOfficial}</li>
        <li className="chip">{S.start.chipOpenMethod}</li>
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
