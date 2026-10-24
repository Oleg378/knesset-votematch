import type { Dispatch } from 'react';
import type { QuizBills, QuizData } from '../engine/types';
import type { Action, State } from '../state/reducer';

/** Screens after the core questions: they need quiz_data (App shows a loader until it arrives). */
export interface ScreenProps {
  data: QuizData;
  state: State;
  dispatch: Dispatch<Action>;
}

/** List details and methodology: they also need quiz_bills. */
export interface BillsScreenProps extends ScreenProps {
  bills: QuizBills;
}
