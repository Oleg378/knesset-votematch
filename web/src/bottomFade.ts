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
    // A short page scrolls inside .app (shortScroll.ts).
    const app = root.hasAttribute('data-inner-scroll') ? document.querySelector('.app') : null;
    const below = app ? app.scrollHeight - app.scrollTop - app.clientHeight
      : root.scrollHeight - window.scrollY - window.innerHeight;
    root.toggleAttribute('data-below', below > 1);
  };
  const schedule = () => {
    if (!frame) frame = requestAnimationFrame(update);
  };
  window.addEventListener('scroll', schedule, { passive: true, capture: true }); // capture: .app's own scroll too
  window.addEventListener('resize', schedule);
  const sizes = typeof ResizeObserver === 'function' ? new ResizeObserver(schedule) : null;
  sizes?.observe(document.body); // a new screen, the reserve, the font
  update();
  return () => {
    cancelAnimationFrame(frame);
    window.removeEventListener('scroll', schedule, { capture: true });
    window.removeEventListener('resize', schedule);
    sizes?.disconnect();
    root.removeAttribute('data-below');
  };
}
