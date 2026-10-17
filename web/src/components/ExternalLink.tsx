import type { ReactNode } from 'react';
import { S } from '../strings';

/** A link that opens in a new tab and says so to screen readers; no referrer goes to the other site. */
export function ExternalLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a className="small" href={href} target="_blank" rel="noopener noreferrer">
      {children}
      <span className="visually-hidden"> {S.a11y.newTab}</span>
    </a>
  );
}
