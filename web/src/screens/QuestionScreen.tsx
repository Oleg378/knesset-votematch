import { AnswerButton } from '../components/AnswerButton';
import { BottomBar } from '../components/BottomBar';
import { Note } from '../components/Note';
import { OrDivider } from '../components/OrDivider';
import { S } from '../strings';
import type { ScreenProps } from './types';

/** Figma «Questions»: statement + four answers in a panel, «Not sure — skip», then Back / Next. */
export function QuestionScreen({ data, state, dispatch }: ScreenProps & { i: number }) {
  if (state.screen.name !== 'question') return null;
  const st = data.statements[state.screen.i]!;
  const current = state.answers[st.q];
  return (
    <section className="screen">
      {state.notice === 'noAnswers' && <Note>{S.question.noAnswers}</Note>}
      <div className="panel">
        <h2 className="statement-text statement">{st.statement_en}</h2>
        <div className="stack" role="group" aria-label={S.question.answersLabel}>
          {S.answerOrder.map((v) => (
            <AnswerButton key={v} selected={current === v} onClick={() => dispatch({ type: 'ANSWER', value: v })}>
              {S.answers[v]}
            </AnswerButton>
          ))}
        </div>
        <OrDivider />
        <button type="button" className="btn btn-link skip" onClick={() => dispatch({ type: 'SKIP' })}>
          {S.question.skip}
        </button>
      </div>
      <BottomBar onBack={() => dispatch({ type: 'BACK' })} onNext={() => dispatch({ type: 'NEXT' })}
        canNext={current !== undefined} />
    </section>
  );
}
