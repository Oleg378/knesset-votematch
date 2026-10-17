import type { ReactNode } from 'react';

interface Props {
  children: ReactNode;
  onClick?: () => void;
}

/** A surface; tappable (rendered as a button) when onClick is given. */
export function Card({ children, onClick }: Props) {
  return onClick ? (
    <button type="button" className="card" onClick={onClick}>
      {children}
    </button>
  ) : (
    <div className="card">{children}</div>
  );
}
