import type { CSSProperties } from 'react';
import { Counter } from './Header';

interface Props {
  value: number;
  max: number;
  text: string;
  label: string;
}

/** Figma «Track» + counter («1/10»), inside the header. The fill moves to the new value (app.css .progress-fill). */
export function ProgressBar({ value, max, text, label }: Props) {
  return (
    <>
      <div className="progress-track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={max}
        aria-valuenow={value} aria-valuetext={text}>
        <div className="progress-fill" style={{ '--p': value / max } as CSSProperties} />
      </div>
      <Counter text={text} />
    </>
  );
}
