import type { ReactNode } from 'react';
import { S } from '../strings';
import { Icon } from './Icon';

/**
 * Top bar of every screen (Figma «Frame 4»): menu button, then the screen's progress or counter; on Results, at the
 * right end instead, Start over: the icon of the menu's item, no text; it starts the quiz again at the first question,
 * as Start on Home (customer 2026-10-22).
 */
export function Header({ onMenu, onStartOver, children }: { onMenu: () => void; onStartOver?: () => void; children?: ReactNode }) {
  return (
    <header className="header">
      <button type="button" className="icon-btn" aria-label={S.menu.open} aria-haspopup="dialog" onClick={onMenu}>
        <Icon name="menu" />
      </button>
      {onStartOver && (
        <button type="button" className="icon-btn header-restart" aria-label={S.menu.startOver} onClick={onStartOver}>
          <Icon name="restart" />
        </button>
      )}
      {children}
    </header>
  );
}

export function Counter({ text }: { text: string }) {
  return <span className="counter">{text}</span>;
}
