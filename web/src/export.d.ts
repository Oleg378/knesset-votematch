// The data contract is imported through the '@export' alias (vite.config.ts). Typed here as unknown on purpose:
// TypeScript must not infer types from multi-megabyte JSON; src/data.ts casts the files to their types (validated by the
// schema test). quiz_core is bundled; quiz_data and quiz_bills are fetched by their hashed asset URLs (`?url`).
declare module '@export/quiz_data.v1.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_data.v1.schema.json' {
  const value: unknown;
  export default value;
}
declare module '@export/golden.v1.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_core.v2.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_data.v2.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_bills.v2.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_data.v2.json?url' {
  const value: string;
  export default value;
}
declare module '@export/quiz_bills.v2.json?url' {
  const value: string;
  export default value;
}
declare module '@export/quiz_data.v2.schema.json' {
  const value: unknown;
  export default value;
}
declare module '@export/golden.v2.json' {
  const value: unknown;
  export default value;
}
