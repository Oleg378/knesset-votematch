// Writes export/quiz_texts.schema.json from the zod schema in src/texts.ts (the one source of the structure).
// `npm run schema:texts` after changing the schema; src/texts.test.ts fails while the file is stale.
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { jsonSchema } from '../src/textsJsonSchema.ts';

const out = fileURLToPath(new URL('../../export/quiz_texts.schema.json', import.meta.url));
writeFileSync(out, JSON.stringify(jsonSchema(), null, 1) + '\n');
console.log(`wrote ${out}`);
