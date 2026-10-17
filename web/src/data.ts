import raw from '@export/quiz_data.v1.json';
import type { QuizData } from './engine/types';

/** The data contract (export/quiz_data.v1.json), bundled at build time. Its shape is checked by the schema test. */
export const data = raw as QuizData;
