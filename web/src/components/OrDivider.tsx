import { S } from '../strings';

export function OrDivider() {
  return (
    <div className="or-divider" role="presentation">
      <span>{S.question.or}</span>
    </div>
  );
}
