/**
 * Number formatting identical to Python's format spec (the reference prints with it):
 * Python rounds the exact binary value of the float, ties to even; JS toFixed rounds exact ties up. Both work on the
 * exact value, so we take the exact decimal expansion (toFixed(100)) and round it half-to-even ourselves.
 */

function roundHalfEven(abs: number, digits: number): string {
  const exact = abs.toFixed(100); // exact decimal expansion of the double (for |x| < 1e21 and any realistic value here)
  const dot = exact.indexOf('.');
  const intPart = exact.slice(0, dot);
  const frac = exact.slice(dot + 1);
  const kept = frac.slice(0, digits);
  const rest = frac.slice(digits);
  let n = BigInt(intPart + kept);
  const first = rest.charCodeAt(0) - 48;
  const tail = /[1-9]/.test(rest.slice(1));
  if (first > 5 || (first === 5 && tail) || (first === 5 && !tail && n % 2n === 1n)) n += 1n;
  let s = n.toString().padStart(digits + 1, '0');
  if (digits > 0) s = `${s.slice(0, s.length - digits)}.${s.slice(s.length - digits)}`;
  return s;
}

function isNegative(x: number): boolean {
  return x < 0 || Object.is(x, -0);
}

/** Python f"{x:.{digits}f}" (or f"{x:+.{digits}f}" when plus). */
export function pyFixed(x: number, digits: number, plus = false): string {
  if (Number.isNaN(x)) return plus ? '+nan' : 'nan';
  if (!Number.isFinite(x)) return `${isNegative(x) ? '-' : plus ? '+' : ''}inf`;
  const body = roundHalfEven(Math.abs(x), digits);
  return `${isNegative(x) ? '-' : plus ? '+' : ''}${body}`;
}

/** Python f"{x:.0%}": multiplies by 100 (as a float), then formats with 0 decimals. */
export function pyPercent0(x: number): string {
  return `${pyFixed(x * 100, 0)}%`;
}

/** Closeness as shown everywhere: Python f"{x:+.2f}", e.g. +0.35. */
export function formatCloseness(x: number): string {
  return pyFixed(x, 2, true);
}
