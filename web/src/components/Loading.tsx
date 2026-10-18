import { Button } from './Button';
import { S } from '../strings';

/** Shown only on a screen whose data file has not arrived yet (V2_HANDOFF.md «Loading»). */
export function Loading() {
  return (
    <section className="screen">
      <p className="muted" role="status">{S.loading}</p>
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
