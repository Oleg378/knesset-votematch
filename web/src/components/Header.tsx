import type { ReactNode } from 'react';
import { S } from '../strings';
import { Icon } from './Icon';

/** Top bar of every screen (Figma «Frame 4»): menu button, then the screen's progress or counter. */
export function Header({ onMenu, children }: { onMenu: () => void; children?: ReactNode }) {
  return (
    <header className="header">
      <button type="button" className="icon-btn" aria-label={S.menu.open} aria-haspopup="dialog" onClick={onMenu}>
        <Icon name="menu" />
      </button>
      {children}
    </header>
  );
}

export function Counter({ text }: { text: string }) {
  return <span className="counter">{text}</span>;
}
