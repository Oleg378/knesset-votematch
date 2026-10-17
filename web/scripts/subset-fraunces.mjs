// Builds src/assets/fonts/fraunces-opsz.woff2 from @fontsource-variable/fraunces (Latin, all axes, 118 KB):
// keeps the opsz axis (Figma: optical size follows the font size), pins WONK 1, SOFT 0 and wght 400 (Figma «Colors & Typography»:
// every Fraunces style is Regular, WONK 1, SOFT 0) and keeps only the characters of the English UI and statements.
// Run after updating the package: node scripts/subset-fraunces.mjs
import { readFileSync, writeFileSync } from 'node:fs';
import subsetFont from 'subset-font';

const src = new URL('../node_modules/@fontsource-variable/fraunces/files/fraunces-latin-full-normal.woff2', import.meta.url);
const out = new URL('../src/assets/fonts/fraunces-opsz.woff2', import.meta.url);

let text = '';
const add = (from, to) => { for (let c = from; c <= to; c++) text += String.fromCodePoint(c); };
add(0x20, 0x7e); // ASCII
add(0xa0, 0xff); // Latin-1: ·, ×, nbsp
add(0x2010, 0x2027); // dashes, quotes, …
add(0x2030, 0x203a);
add(0x20aa, 0x20ac); // ₪, €
add(0x2212, 0x2212); // minus

const buf = await subsetFont(readFileSync(src), text, { targetFormat: 'woff2', variationAxes: { wght: 400, SOFT: 0, WONK: 1 } });
writeFileSync(out, buf);
console.log(`${out.pathname}: ${(buf.length / 1024).toFixed(1)} KB`);
