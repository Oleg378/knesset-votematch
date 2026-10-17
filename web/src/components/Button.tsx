import type { ButtonHTMLAttributes } from 'react';

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'secondary' | 'link';
  block?: boolean;
};

export function Button({ variant = 'secondary', block = false, className = '', type = 'button', ...rest }: Props) {
  return <button type={type} className={`btn btn-${variant}${block ? ' btn-block' : ''} ${className}`.trim()} {...rest} />;
}
