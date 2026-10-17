import { useEffect, useRef } from 'react';
import { S } from '../strings';
import { Icon } from './Icon';

interface Props {
  onClose: () => void;
  onStartOver: () => void;
  onResults: (() => void) | null;
  onMethodology: () => void;
}

/** Figma «Menu» (frame «11 — Menu open»): a drawer from the left over a dimmed page. */
export function Menu({ onClose, onStartOver, onResults, onMethodology }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      opener?.focus?.();
    };
  }, [onClose]);
  const item = (icon: 'restart' | 'results' | 'info', label: string, run: (() => void) | null) => (
    <li>
      <button type="button" className="menu-item" disabled={!run} onClick={() => { onClose(); run?.(); }}>
        <Icon name={icon} />
        {label}
      </button>
    </li>
  );
  return (
    <div className="menu-layer">
      <div className="menu-dim" onClick={onClose} aria-hidden="true" />
      <div className="menu" role="dialog" aria-modal="true" aria-label={S.menu.title}>
        <button ref={closeRef} type="button" className="icon-btn" aria-label={S.menu.close} onClick={onClose}>
          <Icon name="close" />
        </button>
        <div className="menu-title">
          <p className="eyebrow">{S.eyebrow}</p>
          <p className="title-lg">{S.menu.title}</p>
        </div>
        <hr className="menu-divider" />
        <ul className="plain-list menu-items">
          {item('restart', S.menu.startOver, onStartOver)}
          {item('results', S.menu.results, onResults)}
          {item('info', S.menu.methodology, onMethodology)}
        </ul>
      </div>
    </div>
  );
}
