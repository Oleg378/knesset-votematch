import { useState } from 'react';
import { BottomBar } from '../components/BottomBar';
import { ChoiceCard } from '../components/ChoiceCard';
import { OrDivider } from '../components/OrDivider';
import type { AnswerValue } from '../engine/types';
import type { TradeChoice } from '../state/reducer';
import { S } from '../strings';
import type { ScreenProps } from './types';

/** Figma «Clarifying question — Equal as option»: choose A / B / equal, then Next. The list behind it is never named. */
export function TradeoffScreen({ data, state, dispatch }: ScreenProps) {
  const [choice, setChoice] = useState<TradeChoice | null>(null);
  if (state.screen.name !== 'tradeoff') return null;
  const [qa, qb] = state.screen.pair;
  const byQ = new Map(data.statements.map((s) => [s.q, s]));
  const card = (q: string, letter: 'A' | 'B') => (
    <ChoiceCard letter={letter} title={byQ.get(q)!.title_en}
      subtitle={S.trade.yourAnswer(S.answers[state.answers[q] as AnswerValue])}
      selected={choice === letter} onClick={() => setChoice(letter)} />
  );
  return (
    <section className="screen">
      <p className="lead">{S.trade.lead}</p>
      <div className="panel">
        <div className="stack statement">
          <h2 className="statement-text">{S.trade.title}</h2>
          <p className="explain">{S.trade.explain}</p>
        </div>
        <div className="stack" role="group" aria-label={S.trade.title}>
          {card(qa, 'A')}
          {card(qb, 'B')}
          <OrDivider />
          <ChoiceCard letter={null} title={S.trade.equalTitle} subtitle={S.trade.equalSub} selected={choice === '='}
            onClick={() => setChoice('=')} />
        </div>
      </div>
      <BottomBar onBack={() => dispatch({ type: 'BACK' })}
        onNext={() => choice && dispatch({ type: 'TRADE', choice })} canNext={choice !== null} />
    </section>
  );
}
