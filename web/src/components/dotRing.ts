/**
 * The loading picture (customer 2026-10-18): the hero's dot rings as a full circle (Figma «Frame 9»: radii 34…66, dots 6,
 * ~7 px apart, Brand/Primary at 40 / 28 / 18 / 10 / 4.8 %) and a blue dot (9.6) running along the middle ring.
 * Every ring is uniform: the Figma frame lightens the dots around its blue dot, which would read as a glare here.
 * Drawn by <Loading/> (src/components/Loading.tsx).
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
