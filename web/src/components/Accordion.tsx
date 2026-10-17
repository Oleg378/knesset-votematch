import { useId, useState, type ReactNode } from 'react';

interface Props {
  title: ReactNode;
  /** Rendered only while open (keeps long content such as bill lists out of the DOM). */
  children: () => ReactNode;
  initiallyOpen?: boolean;
}

export function Accordion({ title, children, initiallyOpen = false }: Props) {
  const [open, setOpen] = useState(initiallyOpen);
  const id = useId();
  return (
    <div className="accordion">
      <button type="button" className="accordion-head" aria-expanded={open} aria-controls={open ? id : undefined}
        onClick={() => setOpen(!open)}>
        <span>{title}</span>
      </button>
      {open && (
        <div className="accordion-body" id={id}>
          {children()}
        </div>
      )}
    </div>
  );
}
