import type { AnchorHTMLAttributes, ButtonHTMLAttributes, MouseEvent } from 'react';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'link';
  block?: boolean;
};

export function Button({ variant = 'secondary', block = false, className = '', type = 'button', ...rest }: Props) {
  return <button type={type} className={`btn btn-${variant}${block ? ' btn-block' : ''} ${className}`.trim()} {...rest} />;
}

type LinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'onClick'> & {
  variant?: 'primary' | 'secondary' | 'link';
  block?: boolean;
  /** The page's address (a real link for crawlers and for «open in a new tab»). */
  href: string;
  /** What a click does in the app instead of loading the page. */
  onClick: () => void;
};

/**
 * A button that is also a link (DECISIONS.md H10): the same look and the same in-app action as <Button>, but an <a href>
 * underneath, so a search engine finds the page it leads to and a reader can open it in a new tab. A plain click stays
 * in the app (no reload); a modified click (new tab, middle button) is left to the browser.
 */
export function LinkButton({ variant = 'secondary', block = false, className = '', href, onClick, ...rest }: LinkProps) {
  const click = (e: MouseEvent<HTMLAnchorElement>) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    e.preventDefault();
    onClick();
  };
  return <a className={`btn btn-${variant}${block ? ' btn-block' : ''} ${className}`.trim()} href={href} onClick={click} {...rest} />;
}
