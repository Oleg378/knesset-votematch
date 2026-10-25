// @vitest-environment jsdom
/**
 * The prerendered pages (src/prerender.tsx) are what the app draws: the shell and the screen of each page, with the data
 * of the same export — otherwise the page would change under the reader when the JS takes over.
 */
import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from './App';
import { loadedSources } from './data';
import { PAGE_PATHS, render as prerender } from './prerender';
import { initialStateFor } from './state/reducer';
import { bills, core, data } from './testSources';
import { T } from './texts';

/**
 * The same DOM, whatever the serializer: tags, attributes (sorted) and text, element by element. useId differs between the
 * build-time renderer and the browser; those ids only tie labels to their controls, so they are levelled.
 */
const ID_ATTRS = new Set(['id', 'for', 'aria-controls', 'aria-labelledby', 'aria-describedby']);
function canon(html: string): string {
  const doc = new DOMParser().parseFromString(`<body>${html}</body>`, 'text/html');
  const out: string[] = [];
  const walk = (n: Node) => {
    if (n.nodeType === Node.TEXT_NODE) {
      out.push(`#${n.textContent}`);
      return;
    }
    if (n.nodeType !== Node.ELEMENT_NODE) return;
    const el = n as Element;
    const attrs = [...el.attributes].map((a) => `${a.name}=${ID_ATTRS.has(a.name) ? 'ID' : a.value}`).sort();
    out.push(`<${el.tagName} ${attrs.join(' ')}>`);
    el.childNodes.forEach(walk);
    out.push(`</${el.tagName}>`);
  };
  doc.body.childNodes.forEach(walk);
  return out.join('\n');
}

describe('prerendered pages', () => {
  it('the start page is what the app draws once quiz_core is there', () => {
    const { container } = render(<App loader={loadedSources(core, null as never, null as never)} />);
    expect(canon(container.innerHTML)).toBe(canon(prerender(PAGE_PATHS.start)));
  });

  it('«How it works» is what the app draws on /how-it-works', () => {
    const { container } = render(<App loader={loadedSources(core, data, bills)} initial={initialStateFor(PAGE_PATHS.methodology)} />);
    expect(canon(container.innerHTML)).toBe(canon(prerender(PAGE_PATHS.methodology)));
  });

  it('holds the text a search engine needs', () => {
    expect(prerender(PAGE_PATHS.start)).toContain(T.start.title);
    expect(prerender(PAGE_PATHS.methodology)).toContain('method-list');
  });

  it('an unknown path is an error', () => {
    expect(() => prerender('/results')).toThrow();
  });
});
