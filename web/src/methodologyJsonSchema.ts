/**
 * The JSON Schema of export/quiz_methodology.json, generated from the zod schema (methodology.ts) — written to
 * export/quiz_methodology.schema.json by scripts/methodology-schema.ts and checked there by Python's `make check` (I8).
 * Kept out of methodology.ts so the app bundle never carries the generator.
 */
import * as z from 'zod/mini';
import { MethodologySchema } from './methodology.ts';

export function jsonSchema(): Record<string, unknown> {
  const s = z.toJSONSchema(MethodologySchema, { target: 'draft-2020-12' }) as Record<string, unknown>;
  return {
    $schema: s.$schema,
    $id: 'quiz_methodology.schema.json',
    title: 'Knesset 2026 quiz — methodology page',
    description: 'Every text of the methodology page (export/WEB_CONTRACT.md §7). Edited by hand; generated from ' +
      'web/src/methodology.ts by `npm run schema:methodology`, checked by `make check` and the web tests. Texts may use ' +
      '{name} and {name?one|many} with the names listed in the patterns; the page fills them from quiz_data.',
    ...Object.fromEntries(Object.entries(s).filter(([k]) => k !== '$schema')),
  };
}
