import { useId, useRef, useState, type ReactNode } from 'react';
import { flushSync } from 'react-dom';
import { collapse, expand, foldLid, scrollBackTo } from '../expandMotion';
import { S } from '../strings';

interface Props {
  /** Id of the element «Show less» scrolls back to before closing (the line or title the content belongs to). */
  backTo: string;
  /** The content that drops down; rendered only while open or closing. */
  children: () => ReactNode;
  /** Class of the block (its «See all», the content and the lid) and of the content. */
  className: string;
  dropClassName: string;
  /** Told when the content has opened (true) and when it has closed, after the motion (false). */
  onOpenChange?: (open: boolean) => void;
}

/**
 * «See all» that drops content down in place, the same motion as the Results panel (expandMotion.ts): the rest of a
 * long Methodology card (MethodCard in MethodologyScreen.tsx; customer 2026-10-24). «See all» (aria-expanded false,
 * aria-controls the content) is gone once open, the focus goes to the content without scrolling; «Show less» at the
 * end of the content first scrolls back to `backTo`, then closes it; while it closes, a lid with «See all» stands under
 * it where the button will be, and the focus returns to «See all» at the end. Reduced motion or no layout: at once.
 */
export function DropDown({ backTo, children, className, dropClassName, onOpenChange }: Props) {
  const id = useId();
  const [all, setAll] = useState(false);
  const [closing, setClosing] = useState(false);
  // While the content opens, «See all» stays as a lid on its growing edge and folds away (expandMotion.ts foldLid, H15).
  const [opening, setOpening] = useState(false);
  const toggle = useRef<HTMLButtonElement>(null);
  const drop = useRef<HTMLDivElement>(null);
  const lid = useRef<HTMLDivElement>(null);
  const showAll = (on: boolean) => {
    if (on) {
      flushSync(() => {
        setAll(true);
        setOpening(true);
      });
      onOpenChange?.(true);
      if (drop.current) {
        expand(drop.current, () => setOpening(false));
        if (lid.current) foldLid(lid.current, drop.current);
      } else setOpening(false);
      drop.current?.focus({ preventScroll: true });
      return;
    }
    const content = drop.current;
    const back = document.getElementById(backTo);
    if (closing) return;
    if (!content || !back) {
      flushSync(() => setAll(false));
      toggle.current?.focus();
      onOpenChange?.(false);
      return;
    }
    flushSync(() => setClosing(true));
    scrollBackTo(back, () => collapse(content, () => {
      flushSync(() => {
        setClosing(false);
        setAll(false);
      });
      toggle.current?.focus({ preventScroll: true });
      onOpenChange?.(false);
    }));
  };
  return (
    <div className={className}>
      {!all && (
        <div className="see-all">
          <button type="button" ref={toggle} className="btn btn-link skip" aria-expanded="false" aria-controls={id}
            onClick={() => showAll(true)}>
            {S.results.seeAll}
          </button>
        </div>
      )}
      {all && (
        <div id={id} className={dropClassName} ref={drop} tabIndex={-1} inert={closing || undefined}
          aria-hidden={closing || undefined}>
          {children()}
          <div className="see-all">
            <button type="button" className="btn btn-link skip" aria-expanded="true" aria-controls={id}
              onClick={() => showAll(false)}>
              {S.results.seeLess}
            </button>
          </div>
        </div>
      )}
      {(closing || opening) && (
        <div ref={lid} className="see-all" aria-hidden="true">
          <span className="btn btn-link skip">{S.results.seeAll}</span>
        </div>
      )}
    </div>
  );
}
