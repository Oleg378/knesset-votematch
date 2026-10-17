import { useMemo } from 'react';
import { Accordion } from '../components/Accordion';
import { Button } from '../components/Button';
import { ListRow } from '../components/ListRow';
import { match } from '../engine/match';
import { answeredCount } from '../state/reducer';
import { S } from '../strings';
import type { ScreenProps } from './types';

export function ResultsScreen({ data, state, dispatch }: ScreenProps) {
  const rows = useMemo(() => match(data, state.answers, state.mult), [data, state.answers, state.mult]);
  const ranked = rows.filter((r) => r.ranked);
  const low = rows.filter((r) => !r.ranked && r.evaluated);
  const none = rows.filter((r) => !r.evaluated);
  const open = (id: string) => () => dispatch({ type: 'OPEN_DETAILS', list: id });
  return (
    <section className="screen">
      <div className="stack">
        <h1 className="title-lg">{S.results.heading}</h1>
        <p>{S.results.intro}</p>
        <p className="small muted">
          {S.results.basedOn(answeredCount(state.answers), data.statements.length, Object.keys(state.mult).length > 0)}
        </p>
      </div>
      <ol className="list-rows">
        {ranked.map((r, i) => (
          <li key={r.id}>
            <ListRow rank={i + 1} name={r.name_en} closeness={r.closeness} note={r.note} onClick={open(r.id)} />
          </li>
        ))}
      </ol>
      {low.length > 0 && (
        <>
          <div className="divider">{S.results.notRanked}</div>
          <ul className="list-rows">
            {low.map((r) => (
              <li key={r.id}>
                <ListRow rank={null} name={r.name_en} closeness={r.closeness} note={r.note}
                  onClick={r.closeness === null ? undefined : open(r.id)} />
              </li>
            ))}
          </ul>
        </>
      )}
      {none.length > 0 && (
        <Accordion title={S.results.noRecord(none.length)}>
          {() => (
            <ul className="plain-list small">
              {none.map((r) => (
                <li key={r.id}>{r.name_en}</li>
              ))}
            </ul>
          )}
        </Accordion>
      )}
      <div className="sticky-actions">
        <Button block onClick={() => dispatch({ type: 'CHANGE_ANSWERS' })}>
          {S.results.changeAnswers}
        </Button>
        <Button block onClick={() => dispatch({ type: 'START_OVER' })}>
          {S.results.startOver}
        </Button>
        <Button variant="link" onClick={() => dispatch({ type: 'OPEN_METHODOLOGY' })}>
          {S.results.methodology}
        </Button>
      </div>
    </section>
  );
}
