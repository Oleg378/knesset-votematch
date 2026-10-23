/**
 * Short scrolls (customer 2026-10-23): when a page has too little to scroll for the browser bars to hide smoothly, the
 * bars do not hide. Chrome on iOS hides its bars while the document scrolls and grows its window by as much; a page
 * only a little longer than the window runs out of scroll before they are gone, and they come back with a jerk. Three
 * cases, the same for every screen:
 * - the content fits the window with the bars shown (≤ 100svh): the page does not scroll;
 * - a little longer (under 100lvh + (lvh − svh)): .app scrolls inside itself, one window high (data-inner-scroll,
 *   app.css «Short scrolls»); the document does not scroll, so the bars stay;
 * - longer: the document scrolls and the bars hide, as on any long page.
 * svh and lvh come from registered custom properties (app.css), no measuring elements in the DOM.
 */
export function needsInnerScroll(content: number, svh: number, lvh: number): boolean {
  return content - svh > 0.5 && content < lvh + (lvh - svh);
}

/** --svh / --lvh / --dvh as px, or null where @property is not supported (the value stays «100svh»). */
export function readViewport(): { svh: number | null; lvh: number | null; dvh: number | null } {
  const css = getComputedStyle(document.documentElement);
  const px = (name: string) => {
    const v = css.getPropertyValue(name).trim();
    return v.endsWith('px') ? parseFloat(v) : null;
  };
  return { svh: px('--svh'), lvh: px('--lvh'), dvh: px('--dvh') };
}

/**
 * Watches .app and its children (ResizeObserver: the content, the statement reserve, the font, a rotation; a new
 * screen is a new child, MutationObserver) and switches the inner scroll. The content's own height is read with the
 * sizes from the stylesheet off and set back in the same callback, before the next paint.
 */
export function watchShortScroll(app: HTMLElement): () => void {
  if (typeof ResizeObserver !== 'function' || typeof MutationObserver !== 'function') return () => {};
  const root = document.documentElement;
  const update = () => {
    const { svh, lvh } = readViewport();
    app.style.height = 'auto';
    app.style.minHeight = '0px';
    const content = app.getBoundingClientRect().height;
    app.style.height = '';
    app.style.minHeight = '';
    const inner = svh !== null && lvh !== null && needsInnerScroll(content, svh, lvh);
    if (inner === root.hasAttribute('data-inner-scroll')) return;
    // The scroll position goes over to the new scroller, so nothing on screen moves (an accordion opened on a short
    // page makes it long).
    const at = inner ? window.scrollY : app.scrollTop;
    root.toggleAttribute('data-inner-scroll', inner);
    if (inner) {
      window.scrollTo(0, 0);
      app.scrollTop = at;
    } else {
      app.scrollTop = 0;
      window.scrollTo(0, at);
    }
  };
  const sizes = new ResizeObserver(update);
  const watch = () => {
    sizes.disconnect();
    sizes.observe(app);
    for (const child of app.children) sizes.observe(child);
  };
  const children = new MutationObserver(watch);
  children.observe(app, { childList: true });
  watch();
  return () => {
    sizes.disconnect();
    children.disconnect();
    root.removeAttribute('data-inner-scroll');
  };
}
