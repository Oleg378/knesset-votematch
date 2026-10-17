import type { ReactNode } from 'react';

interface Props {
  selected: boolean;
  secondary?: boolean;
  onClick: () => void;
  children: ReactNode;
}

export function AnswerButton({ selected, secondary = false, onClick, children }: Props) {
  return (
    <button type="button" className={`answer${secondary ? ' answer-secondary' : ''}`} aria-pressed={selected}
      onClick={onClick}>
      {children}
    </button>
  );
}
