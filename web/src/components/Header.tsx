import type { ReactNode } from 'react';
import { S } from '../strings';
import { Icon } from './Icon';

/**
 * Top bar of every screen (Figma «Frame 4»): menu button, then the screen's progress or counter; on Results, at the
 * right end instead, Start over: the icon of the menu's item, no text; it starts the quiz again at the first question,
 * as Start on Home (customer 2026-10-22). A screen's title can stand in the middle, pinned with the bar (Results,
 * customer 2026-10-23; How it works, 2026-10-24); it is a picture of the screen's own heading, which stays in the page
 * for screen readers. On an inner page (List details) «Back» stands in the menu's place: the chevron, no text, its label
 * for screen readers (customer 2026-10-24: «на всех внутренних страницах… убери бургер и добавь назад»; How it works is a
 * page of its own and keeps the menu).
 */
export function Header({ onMenu, back, onStartOver, title, children }:
  { onMenu: () => void; back?: { label: string; onClick: () => void }; onStartOver?: () => void; title?: string;
    children?: ReactNode }) {
  return (
    <header className="header">
      {back ? (
        <button type="button" className="icon-btn" aria-label={back.label} onClick={back.onClick}>
          <Icon name="back" />
        </button>
      ) : (
        <button type="button" className="icon-btn" aria-label={S.menu.open} aria-haspopup="dialog" onClick={onMenu}>
          <Icon name="menu" />
        </button>
      )}
      {title && <span className="header-title" aria-hidden="true">{title}</span>}
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
