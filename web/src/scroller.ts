/**
 * What scrolls the screen (app.css «Two ways to scroll»): in an app's viewer on a phone, the area under the header
 * (.app-scroll); in a browser, .app when a short page scrolls inside it (shortScroll.ts), otherwise the window (null).
 */
export function screenScroller(): HTMLElement | null {
  const area = document.querySelector<HTMLElement>('.app-scroll');
  if (area && /auto|scroll/.test(getComputedStyle(area).overflowY)) return area;
  return document.documentElement.hasAttribute('data-inner-scroll') ? document.querySelector<HTMLElement>('.app') : null;
}
