import { useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { collapse, expand } from '../expandMotion';

interface Props {
  title: ReactNode;
  /** Rendered only while open or closing (keeps long content such as bill lists out of the DOM). */
  children: () => ReactNode;
  initiallyOpen?: boolean;
}

/**
 * The body opens and closes with expandMotion.ts. On close it stays mounted until the motion ends, inert and hidden
 * from screen readers from the moment closing starts.
 */
export function Accordion({ title, children, initiallyOpen = false }: Props) {
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

  const leaving = mounted && !open;
  return (
    <div className="accordion">
      <button type="button" className="accordion-head" aria-expanded={open} aria-controls={open ? id : undefined}
        onClick={() => setOpen(!open)}>
        <span>{title}</span>
      </button>
      {mounted && (
        <div ref={body} className="accordion-body" id={id} inert={leaving || undefined}
          aria-hidden={leaving || undefined}>
          {children()}
        </div>
      )}
    </div>
  );
}
