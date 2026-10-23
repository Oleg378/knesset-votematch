import type { Dispatch } from 'react';
import type { QuizData } from '../engine/types';
import type { Action, State } from '../state/reducer';

export interface ScreenProps {
  data: QuizData;
  state: State;
  dispatch: Dispatch<Action>;
}
