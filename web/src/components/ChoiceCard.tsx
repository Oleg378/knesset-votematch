import { Icon } from './Icon';

interface Props {
  /** «A», «B», or null for the «equal» card. */
  letter: string | null;
  title: string;
  subtitle: string;
  selected: boolean;
  onClick: () => void;
}

/** Figma «Answer card» (Kind = Letter | Equal, State = Default | Selected). */
export function ChoiceCard({ letter, title, subtitle, selected, onClick }: Props) {
  return (
    <button type="button" className={`choice${letter === null ? ' choice-equal' : ''}`} aria-pressed={selected}
      onClick={onClick}>
      <span className="choice-badge" aria-hidden="true">
        {letter ?? <Icon name={selected ? 'equalSelected' : 'equalDefault'} size={12} />}
      </span>
      <span className="choice-text">
        <span className="choice-title">{title}</span>
        <span className="choice-sub">{subtitle}</span>
      </span>
    </button>
  );
}
