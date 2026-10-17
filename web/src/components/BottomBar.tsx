import roundBack from '../assets/figma/round-back.svg';
import { S } from '../strings';

/** Figma «Frame 2»: Round Button (back) + Action «Next» (inactive until something is chosen). */
export function BottomBar({ onBack, onNext, canNext }: { onBack: () => void; onNext: () => void; canNext: boolean }) {
  return (
    <div className="bottom-bar">
      <button type="button" className="round-btn" aria-label={S.nav.back} onClick={onBack}>
        <img src={roundBack} alt="" width={56} height={56} />
      </button>
      <button type="button" className="btn btn-primary grow" disabled={!canNext} onClick={onNext}>
        {S.nav.next}
      </button>
    </div>
  );
}
