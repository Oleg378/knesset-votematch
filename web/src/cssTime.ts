/**
 * A CSS time token read from JavaScript, in milliseconds. The minifier of the production build writes `200ms` as `.2s`,
 * so `parseFloat` alone read 0.2 ms there and the menu closed with no motion (2026-10-24): every token that names a time
 * goes through here.
 */
export function cssTime(value: string): number {
  const v = value.trim();
  if (!v) return 0;
  const n = parseFloat(v);
  if (Number.isNaN(n)) return 0;
  return v.endsWith('ms') ? n : n * 1000;
}

/** The time token `name` of the root element (`--menu-out-time`), in milliseconds; 0 when it is not set. */
export function rootTime(name: string): number {
  return cssTime(getComputedStyle(document.documentElement).getPropertyValue(name));
}
