/** The data files and golden cases for tests, typed; and a quiz state with both fetched files already loaded. */
import goldenRaw from '@export/golden.v2.json';
import billsRaw from '@export/quiz_bills.v2.json';
import dataRaw from '@export/quiz_data.v2.json';
import { core } from '../data';
import type { Answers, BillsFile, DataFile, Mult, Role, Sign, TradePair } from '../engine/types';
import { initialState, type State } from '../state/reducer';

export { core };
export const data = dataRaw as DataFile;
export const bills = billsRaw as BillsFile;

export interface GoldenCase {
  name: string;
  answers: Answers;
  mult: Mult;
  ranking: { id: string; closeness: number | null; coverage: number; note: string; ranked: boolean }[];
  tradeoffs: { exclude: string[]; skip_lists: string[]; pairs: TradePair[] };
  details: {
    id: string;
    items: {
      q: string;
      contribution: number;
      p: number;
      lines: string[];
      evidence: { bill: string; sign: Sign; role: Role; same: boolean; authors: [number, string][] }[];
    }[];
  }[];
  flow?: { core: string[]; clarifying: string[] };
}

export const golden = goldenRaw as { version: number; tolerance: number; cases: GoldenCase[] };

/** The initial state once quiz_data and quiz_bills have arrived. */
export const loaded: State = { ...initialState, data, bills };
