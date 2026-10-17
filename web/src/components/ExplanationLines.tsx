/** The explanation lines of quiz_report.explain(); the first one is the quoted statement. */
export function ExplanationLines({ lines }: { lines: string[] }) {
  return (
    <div className="lines">
      {lines.map((l, i) => (
        <p key={i} className={i === 0 ? 'quote' : 'small'}>
          {l}
        </p>
      ))}
    </div>
  );
}
