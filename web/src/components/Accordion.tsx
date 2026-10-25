import { useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { collapse, expand } from '../expandMotion';

interface Props {
  title: ReactNode;
  /** Rendered only while open or closing (keeps long content such as bill lists out of the DOM). */
  children: () => ReactNode;
  initiallyOpen?: boolean;
  /**
   * Closed, the body stays in the page, `hidden="until-found"`: in the prerendered HTML for search engines, and the
   * browser's find in page opens it (`beforematch`). The usual pattern for an accordion; nothing is shown that a reader
   * cannot open (How it works, customer 2026-10-25).
   */
  findable?: boolean;
}

/**
 * The body opens and closes with expandMotion.ts. On close it stays mounted until the motion ends, inert and hidden
 * from screen readers from the moment closing starts.
 */
export function Accordion({ title, children, initiallyOpen = false, findable = false }: Props) {
  const [open, setOpen] = useState(initiallyOpen);
  const [mounted, setMounted] = useState(initiallyOpen);
  const id = useId();
  const body = useRef<HTMLDivElement>(null);
  const first = useRef(true);

  // Before paint: a just-mounted body starts growing; a closing one starts shrinking, then unmounts.
  useLayoutEffect(() => {
    const initial = first.current;
    first.current = false;
    if (initial) return; // the first render already shows the initial state
    if (open && !mounted) {
      setMounted(true);
      return;
    }
    const el = body.current;
    if (!el) return;
    return open ? expand(el) : collapse(el, () => setMounted(false));
  }, [open, mounted]);

  // Closed and findable: React writes `hidden` (it has no «until-found»), the attribute is set here before the paint;
  // a match of find in page opens the band.
  const shut = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = shut.current;
    if (!el) return;
    el.setAttribute('hidden', 'until-found');
    const onMatch = () => setOpen(true);
    el.addEventListener('beforematch', onMatch);
    return () => el.removeEventListener('beforematch', onMatch);
  }, [mounted]);

  const leaving = mounted && !open;
  return (
    <div className="accordion">
      <button type="button" className="accordion-head" aria-expanded={open}
        aria-controls={open || findable ? id : undefined}
        onClick={() => setOpen(!open)}>
        <span>{title}</span>
      </button>
      {mounted ? (
        <div key="open" ref={body} className="accordion-body" id={id} inert={leaving || undefined}
          aria-hidden={leaving || undefined}>
          {children()}
        </div>
      ) : findable && (
        <div key="shut" ref={shut} className="accordion-body" id={id} hidden>
          {children()}
        </div>
      )}
    </div>
  );
}
