import type { Dispatch } from 'react';
import type { CoreFile } from '../engine/types';
import type { Action, State } from '../state/reducer';

/** quiz_core is bundled; quiz_data and quiz_bills are in the state once loaded (state.data, state.bills). */
export interface ScreenProps {
  core: CoreFile;
  state: State;
  dispatch: Dispatch<Action>;
}
