/**
 * The three v2 data files imported directly — for tests only (the app fetches them at run time, src/data.ts). Their shape is
 * checked by src/engine/schema.test.ts.
 */
import billsRaw from '@export/quiz_bills.v2.json';
import coreRaw from '@export/quiz_core.v2.json';
import dataRaw from '@export/quiz_data.v2.json';
import { loadedSources } from './data';
import type { QuizBills, QuizCore, QuizData } from './engine/types';

export const core = coreRaw as QuizCore;
export const data = dataRaw as QuizData;
export const bills = billsRaw as QuizBills;
export const loaded = () => loadedSources(core, data, bills);
