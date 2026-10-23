// Writes export/quiz_methodology.schema.json from the zod schema in src/methodology.ts (the one source of the structure).
// `npm run schema:methodology` after changing the schema; src/methodology.test.ts fails while the file is stale.
import { writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { jsonSchema } from '../src/methodologyJsonSchema.ts';

const out = fileURLToPath(new URL('../../export/quiz_methodology.schema.json', import.meta.url));
writeFileSync(out, JSON.stringify(jsonSchema(), null, 1) + '\n');
console.log(`wrote ${out}`);
