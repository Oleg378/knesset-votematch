import { readViewport } from './shortScroll';

/** Only with ?debug (main.tsx): the numbers the browser gives for the window, in a corner of the screen. */
export function showViewportNumbers(): void {
  const box = document.createElement('div');
  box.style.cssText = 'position:fixed;top:50%;right:4px;z-index:99;padding:4px 6px;border-radius:6px;'
    + 'background:rgba(0,0,0,.75);color:#fff;font:11px/1.35 ui-monospace,monospace;white-space:pre;pointer-events:none';
  document.body.appendChild(box);
  const tick = () => {
    const root = document.documentElement;
    const { svh, lvh, dvh } = readViewport();
    box.textContent = [
      `inner  ${window.innerHeight}`,
      `svh ${svh}  lvh ${lvh}  dvh ${dvh}`,
      `scroll ${Math.round(window.scrollY)} / ${root.scrollHeight - window.innerHeight}  page ${root.scrollHeight}`,
      `inner scroll ${root.hasAttribute('data-inner-scroll') ? `on, ${Math.round(document.querySelector('.app')?.scrollTop ?? 0)}` : 'off'}`,
    ].join('\n');
    requestAnimationFrame(tick);
  };
  tick();
}
