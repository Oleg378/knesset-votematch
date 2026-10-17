/** Closeness on −1…+1, centered at 0. */
export function ClosenessBar({ value }: { value: number }) {
  const v = Math.max(-1, Math.min(1, value));
  const style = v >= 0 ? { left: '50%', width: `${v * 50}%` } : { left: `${50 + v * 50}%`, width: `${-v * 50}%` };
  return (
    <div className="closeness-bar" aria-hidden="true">
      <div className={`closeness-fill ${v >= 0 ? 'pos' : 'neg'}`} style={style} />
    </div>
  );
}
