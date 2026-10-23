/**
 * The JSON Schema of export/quiz_texts.json, generated from the zod schema (texts.ts) — written to
 * export/quiz_texts.schema.json by scripts/texts-schema.ts and checked there by Python's `make check`.
 * Kept out of texts.ts so the app bundle never carries the generator.
 */
import * as z from 'zod/mini';
import { TextsSchema } from './texts.ts';

export function jsonSchema(): Record<string, unknown> {
  const s = z.toJSONSchema(TextsSchema, { target: 'draft-2020-12' }) as Record<string, unknown>;
  return {
    $schema: s.$schema,
    $id: 'quiz_texts.schema.json',
    title: 'Knesset 2026 quiz — texts of the site',
    description: 'Every text the user reads on the site (export/WEB_CONTRACT.md §7). Edited by hand; generated from ' +
      'web/src/texts.ts by `npm run schema:texts`, checked by `make check` and the web tests. Texts may use {name} and ' +
      '{name?one|many} with the names listed in each pattern (a text with no names takes no braces); the site fills them ' +
      'from quiz_data and the screen state.',
    ...Object.fromEntries(Object.entries(s).filter(([k]) => k !== '$schema')),
  };
}
