import { Counter } from './Header';

interface Props {
  value: number;
  max: number;
  text: string;
  label: string;
}

/** Figma «Track» + counter («1/10»), inside the header. */
export function ProgressBar({ value, max, text, label }: Props) {
  return (
    <>
      <div className="progress-track" role="progressbar" aria-label={label} aria-valuemin={0} aria-valuemax={max}
        aria-valuenow={value} aria-valuetext={text}>
        <div className="progress-fill" style={{ width: `${(100 * value) / max}%` }} />
      </div>
      <Counter text={text} />
    </>
  );
}
