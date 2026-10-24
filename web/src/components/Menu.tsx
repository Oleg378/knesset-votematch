import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from 'react';
import { PAGE_PATHS } from '../state/reducer';
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
    // The page does not scroll while the menu is open; the window or the card can still change size (rotation, a
    // desktop window resized): ResizeObserver, no resize or scroll handlers (react-ui-mobile skill).
    if (typeof ResizeObserver !== 'function') return;
    const sizes = new ResizeObserver(place);
    sizes.observe(document.documentElement);
    sizes.observe(app);
    return () => sizes.disconnect();
  }, []);

  // Slide out, then unmount; an item's action runs at once, so its screen is already behind the closing drawer. The
  // moment closing starts, the menu takes no taps and no focus and leaves the accessibility tree, and the focus goes
  // back to the opener (react-ui-mobile skill, «Exit and unmount»). Unmount on the first of: the animations finished,
  // their duration + 50 ms. No animation (reduced motion, or no Web Animations as in tests) — close at once.
  const close = useCallback((action?: () => void) => {
    if (closing.current) return;
    closing.current = true;
    action?.();
    const layer = layerRef.current;
    layer?.setAttribute('inert', '');
    layer?.setAttribute('aria-hidden', 'true');
    release.current();
    const panel = panelRef.current;
    const dim = dimRef.current;
    const css = getComputedStyle(document.documentElement);
    const duration = parseFloat(css.getPropertyValue('--menu-out-time')) || 0;
    if (!panel?.animate || !dim || !duration || window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      onClose();
      return;
    }
    const exit: KeyframeAnimationOptions = { duration, easing: css.getPropertyValue('--menu-out-ease').trim(), fill: 'forwards' };
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      onClose();
    };
    Promise.all([
      panel.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-100%)' }], exit).finished,
      dim.animate([{ opacity: 1 }, { opacity: 0 }], exit).finished,
    ]).then(finish, finish);
    setTimeout(finish, duration + 50);
  }, [onClose]);

  // Everything else on the page is inert while the menu is open (not only aria-modal); undone, and the focus given
  // back, once — when closing starts, or on unmount.
  const release = useRef<() => void>(() => {});
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    const layer = layerRef.current;
    const others = [...(layer?.parentElement?.children ?? [])].filter((el) => el !== layer && !el.hasAttribute('inert'));
    others.forEach((el) => el.setAttribute('inert', ''));
    let released = false;
    release.current = () => {
      if (released) return;
      released = true;
      others.forEach((el) => el.removeAttribute('inert'));
      opener?.focus?.();
    };
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
      release.current();
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
  // «Methodology» is a page with an address: a real link (crawlers, «open in a new tab»); a plain click stays in the app.
  const pageItem = (icon: 'info', label: string, href: string, run: () => void) => (
    <li>
      <a className="menu-item" href={href} onClick={(e) => {
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        e.preventDefault();
        close(run);
      }}>
        <Icon name={icon} />
        {label}
      </a>
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
            {pageItem('info', S.menu.methodology, PAGE_PATHS.methodology, onMethodology)}
          </ul>
        </div>
      </div>
    </div>
  );
}
