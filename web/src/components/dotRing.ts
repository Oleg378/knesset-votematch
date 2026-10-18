/**
 * The loading picture (customer 2026-10-18): the hero's dot rings as a full circle (Figma «Frame 9»: radii 34…66, dots 6,
 * ~7 px apart, Brand/Primary at 40 / 28 / 18 / 10 / 4.8 %) and a blue dot (9.6) running along the middle ring.
 * Every ring is uniform: the Figma frame lightens the dots around its blue dot, which would read as a glare here.
 * Two renderers share it: index.html until the JS has run (dotRingSvg, bootLoader in vite.config.ts) and <Loading/>.
 * Colour is currentColor, set by .dot-ring in app.css; the animation is there too.
 */
export const DOT_RING_SIZE = 138;
export const DOT_RING_VIEWBOX = `${-DOT_RING_SIZE / 2} ${-DOT_RING_SIZE / 2} ${DOT_RING_SIZE} ${DOT_RING_SIZE}`;
export const DOT_R = 3;
export const RUNNER = { ring: 50, r: 4.8 };

const RINGS: [radius: number, dots: number, opacity: number][] = [[34, 30, 0.4], [42, 38, 0.28], [50, 46, 0.18], [58, 54, 0.1], [66, 62, 0.048]];
const r2 = (x: number) => +x.toFixed(2);

export const dotRings = RINGS.map(([radius, n, opacity]) => ({
  opacity,
  dots: Array.from({ length: n }, (_, i): [number, number] => {
    const a = (2 * Math.PI * i) / n;
    return [r2(radius * Math.cos(a)), r2(radius * Math.sin(a))];
  }),
}));

/** The same picture as markup, for index.html (no React there yet). */
export function dotRingSvg(label: string): string {
  const rings = dotRings
    .map((g) => `<g fill-opacity="${g.opacity}">${g.dots.map(([x, y]) => `<circle cx="${x}" cy="${y}" r="${DOT_R}"/>`).join('')}</g>`)
    .join('');
  return `<svg class="dot-ring" width="${DOT_RING_SIZE}" height="${DOT_RING_SIZE}" viewBox="${DOT_RING_VIEWBOX}" fill="currentColor" role="img" aria-label="${label}">${rings}<circle class="dot-ring-runner" cx="${RUNNER.ring}" cy="0" r="${RUNNER.r}"/></svg>`;
}
