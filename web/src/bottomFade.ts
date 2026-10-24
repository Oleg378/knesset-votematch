import { screenScroller } from './scroller';

/**
 * The fade above the bottom buttons (DECISIONS.md G13): on only while some of the page is under them — the page goes on
 * below the window. When everything fits, or the page is scrolled to its end, the card's bottom stays crisp (customer
 * 2026-10-22). Measured here, the same in every browser: a scroll-driven animation did this before, but Safari 18 has
 * none, and there the fade was always on.
 */
export function watchBottomFade(): () => void {
  const root = document.documentElement;
  let frame = 0;
  const update = () => {
    frame = 0;
    // On phones the area under the header scrolls, in card mode the window (app.css «The frame»).
    const el = screenScroller();
    const below = el ? el.scrollHeight - el.scrollTop - el.clientHeight
      : root.scrollHeight - window.scrollY - window.innerHeight;
    root.toggleAttribute('data-below', below > 1);
  };
  const schedule = () => {
    if (!frame) frame = requestAnimationFrame(update);
  };
  window.addEventListener('scroll', schedule, { passive: true, capture: true }); // capture: the scrolling area's too
  window.addEventListener('resize', schedule);
  // A new screen, the reserve, the font change the length: the page (card mode), the scrolling area and the screen in
  // it (phones; a new screen is a new element, so the targets are taken again whenever the page's elements change).
  const sizes = typeof ResizeObserver === 'function' ? new ResizeObserver(schedule) : null;
  const watch = () => {
    if (!sizes) return;
    sizes.disconnect();
    sizes.observe(document.body);
    const area = document.querySelector('.app-scroll');
    if (area) {
      sizes.observe(area);
      for (const child of area.children) sizes.observe(child);
    }
  };
  const tree = sizes && typeof MutationObserver === 'function' ? new MutationObserver(watch) : null;
  tree?.observe(document.body, { childList: true, subtree: true });
  watch();
  update();
  return () => {
    cancelAnimationFrame(frame);
    window.removeEventListener('scroll', schedule, { capture: true });
    window.removeEventListener('resize', schedule);
    tree?.disconnect();
    sizes?.disconnect();
    root.removeAttribute('data-below');
  };
}
