import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { S } from '../strings';
import { Icon } from './Icon';

interface Props {
  onClose: () => void;
  onStartOver: () => void;
  onResults: (() => void) | null;
  onMethodology: () => void;
}

/**
 * Figma «Menu» (frame «11 — Menu open»): a drawer from the left over a dimmed page. It slides in and out from the edge of
 * the app — the screen on a phone, the card in card mode, which behaves as the phone (customer 2026-10-18): the drawer and
 * its dim sit in a frame over the visible part of .app, clipped by its rounded corners, so the close button is always
 * where the burger is (even on a scrolled long screen). The page does not scroll while the menu is open.
 */
export function Menu({ onClose, onStartOver, onResults, onMethodology }: Props) {
  const layerRef = useRef<HTMLDivElement>(null);
  const dimRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const closing = useRef(false);
  const [frame, setFrame] = useState<CSSProperties>();

  // The frame = the part of .app inside the window; a corner keeps .app's radius only where .app's own corner is visible.
  useLayoutEffect(() => {
    const app = layerRef.current?.closest('.app');
    if (!app) return;
    const place = () => {
      const r = app.getBoundingClientRect();
      const radius = getComputedStyle(app).borderTopLeftRadius;
      const top = r.top >= 0 ? radius : 0;
      const bottom = r.bottom <= window.innerHeight ? radius : 0;
      setFrame({
        top: Math.max(r.top, 0),
        bottom: Math.max(window.innerHeight - r.bottom, 0),
        left: r.left,
        right: 'auto',
        width: r.width,
        borderRadius: `${top} ${top} ${bottom} ${bottom}`,
      });
    };
    place();
    window.addEventListener('resize', place);
    window.addEventListener('scroll', place);
    return () => {
      window.removeEventListener('resize', place);
      window.removeEventListener('scroll', place);
    };
  }, []);

  // Slide out, then unmount; an item's action runs at once, so its screen is already behind the closing drawer.
  // No animation (reduced motion, or no Web Animations as in tests) — close at once.
  const close = useCallback((action?: () => void) => {
    if (closing.current) return;
    closing.current = true;
    action?.();
    const panel = panelRef.current;
    const dim = dimRef.current;
    if (!panel?.animate || !dim || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      onClose();
      return;
    }
    const exit: KeyframeAnimationOptions = { duration: 200, easing: 'cubic-bezier(0.3, 0, 0.8, 0.15)', fill: 'forwards' };
    Promise.all([
      panel.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-100%)' }], exit).finished,
      dim.animate([{ opacity: 1 }, { opacity: 0 }], exit).finished,
    ]).then(onClose, onClose);
  }, [onClose]);

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    // Focus goes to the dialog itself (WAI-ARIA APG), not to Close: a focused button gets the keyboard focus ring, and
    // Safari shows it even after a click (customer 2026-10-18: no ring around the X). Tab reaches Close, with its ring.
    panelRef.current?.focus({ preventScroll: true });
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && close();
    document.addEventListener('keydown', onKey);
    const root = document.documentElement;
    const overflow = root.style.overflow;
    root.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      root.style.overflow = overflow;
      opener?.focus?.();
    };
  }, [close]);

  const item = (icon: 'restart' | 'results' | 'info', label: string, run: (() => void) | null) => (
    <li>
      <button type="button" className="menu-item" disabled={!run} onClick={() => close(run ?? undefined)}>
        <Icon name={icon} />
        {label}
      </button>
    </li>
  );
  return (
    // Outside the frame (the page around the card) a click closes the menu too.
    <div ref={layerRef} className="menu-layer" onClick={(e) => e.target === e.currentTarget && close()}>
      <div className="menu-frame" style={frame}>
        <div ref={dimRef} className="menu-dim" onClick={() => close()} aria-hidden="true" />
        <div ref={panelRef} className="menu" role="dialog" aria-modal="true" aria-label={S.menu.title} tabIndex={-1}>
          <button type="button" className="icon-btn" aria-label={S.menu.close} onClick={() => close()}>
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
    </div>
  );
}
