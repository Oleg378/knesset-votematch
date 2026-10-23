/**
 * The data files imported directly — for tests only (the app fetches them at run time, src/data.ts). The shape of the three
 * data files is checked by src/engine/schema.test.ts, the methodology file by src/methodology.test.ts.
 */
import billsRaw from '@export/quiz_bills.json';
import coreRaw from '@export/quiz_core.json';
import dataRaw from '@export/quiz_data.json';
import methodologyRaw from '@export/quiz_methodology.json';
import { loadedSources } from './data';
import type { QuizBills, QuizCore, QuizData } from './engine/types';
import { parseMethodology } from './methodology';

export const core = coreRaw as QuizCore;
export const data = dataRaw as QuizData;
export const bills = billsRaw as QuizBills;
export const methodology = parseMethodology(methodologyRaw);
export const loaded = () => loadedSources(core, data, bills, methodology);
