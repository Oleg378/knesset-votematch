// The data contract is imported through the '@export' alias (vite.config.ts). The app imports only the URLs of the three
// The data files (fetched at run time, src/data.ts); the JSON itself is imported by the tests only. Typed as unknown on purpose:
// TypeScript must not infer types from multi-megabyte JSON; the schema test checks the shape.
declare module '@export/quiz_core.json?url' {
  const url: string;
  export default url;
}
declare module '@export/quiz_data.json?url' {
  const url: string;
  export default url;
}
declare module '@export/quiz_bills.json?url' {
  const url: string;
  export default url;
}
declare module '@export/quiz_core.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_data.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_bills.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_data.schema.json' {
  const value: unknown;
  export default value;
}
declare module '@export/golden.json' {
  const value: unknown;
  export default value;
}
