/** Hebrew bill title: original only, never translated; direction from the text itself. */
export function HebrewTitle({ text, className = '' }: { text: string; className?: string }) {
  return (
    <span dir="auto" lang="he" className={`he ${className}`.trim()}>
      {text}
    </span>
  );
}
