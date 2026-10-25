import type { DetailsLine } from '../strings';

/**
 * A topic's explanation on List details: the quoted statement, then each fact as a small label over its value (customer
 * 2026-10-25, option 4 of 8: «Your answer» / «strongly agree», «Based on» / «25 bills they sponsored», «Weight ×2» / …).
 */
export function ExplanationLines({ lines }: { lines: DetailsLine[] }) {
  return (
    <div className="lines">
      {lines.map((l, i) => l.quote ? (
        <p key={i} className="quote">{l.text}</p>
      ) : (
        <p key={i} className="small fact">
          {l.label && <span className="fact-label">{l.label}</span>}
          <span className="fact-value">{l.text}</span>
        </p>
      ))}
    </div>
  );
}
