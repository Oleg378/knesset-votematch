import { Button } from './Button';
import { DOT_R, DOT_RING_SIZE, DOT_RING_VIEWBOX, dotRings, RUNNER } from './dotRing';
import { S } from '../strings';

/**
 * Shown only on a screen whose data file has not arrived yet (V2_HANDOFF.md «Loading»): the same dot ring as before the
 * JS has run (customer 2026-10-18), centred in the screen.
 */
export function Loading() {
  return (
    <section className="screen loader" role="status">
      <span className="visually-hidden">{S.loading}</span>
      <svg className="dot-ring" width={DOT_RING_SIZE} height={DOT_RING_SIZE} viewBox={DOT_RING_VIEWBOX} fill="currentColor"
        aria-hidden="true">
        {dotRings.map((g, k) => (
          <g key={k} fillOpacity={g.opacity}>
            {g.dots.map(([x, y], i) => <circle key={i} cx={x} cy={y} r={DOT_R} />)}
          </g>
        ))}
        <circle className="dot-ring-runner" cx={RUNNER.ring} cy={0} r={RUNNER.r} />
      </svg>
    </section>
  );
}

/** A data file failed to load, or the files come from different exports (a deploy mid-session). */
export function LoadError() {
  return (
    <section className="screen">
      <p role="alert">{S.loadError}</p>
      <Button variant="primary" block onClick={() => window.location.reload()}>
        {S.reload}
      </Button>
    </section>
  );
}
