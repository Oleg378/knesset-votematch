import { useEffect, useRef, useState } from 'react';
import { S } from '../strings';
import { Button } from './Button';

/**
 * «Share this quiz» on Results (customer 2026-10-24, DECISIONS.md H): shares the site — its address and one sentence —
 * never the result (nothing of the result is in any URL). The system share sheet where there is one (phones); otherwise
 * the text and the address go to the clipboard and the button says so for a moment.
 */
export function ShareButton() {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);
  const share = async () => {
    const url = `${location.origin}/`;
    const data = { title: S.share.title, text: S.share.text, url };
    if (typeof navigator.share === 'function' && (!navigator.canShare || navigator.canShare(data))) {
      try {
        await navigator.share(data);
      } catch {
        // closed without sharing
      }
      return;
    }
    try {
      await navigator.clipboard.writeText(`${S.share.text} ${url}`);
      setCopied(true);
      clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(false), 2000);
    } catch {
      // no clipboard (an insecure context): nothing to do
    }
  };
  return (
    <Button variant="link" onClick={share} aria-live="polite">
      {copied ? S.share.copied : S.share.button}
    </Button>
  );
}
