import type { ReactNode } from 'react';

export function Note({ children }: { children: ReactNode }) {
  return <span className="note">{children}</span>;
}
