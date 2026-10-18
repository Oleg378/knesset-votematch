// The data contract is imported through the '@export' alias (vite.config.ts). The app imports only the URLs of the three
// v2 files (fetched at run time, src/data.ts); the JSON itself is imported by the tests only. Typed as unknown on purpose:
// TypeScript must not infer types from multi-megabyte JSON; the schema test checks the shape.
declare module '@export/quiz_core.v2.json?url' {
  const url: string;
  export default url;
}
declare module '@export/quiz_data.v2.json?url' {
  const url: string;
  export default url;
}
declare module '@export/quiz_bills.v2.json?url' {
  const url: string;
  export default url;
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
declare module '@export/quiz_data.v2.schema.json' {
  const value: unknown;
  export default value;
}
declare module '@export/golden.v2.json' {
  const value: unknown;
  export default value;
}
