// The data contract is imported through the '@export' alias (vite.config.ts). Typed here as unknown on purpose:
// TypeScript must not infer types from multi-megabyte JSON; src/data.ts casts it to QuizData (validated by the schema test).
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
// v2 (order of questions port, src/engine/flow.ts + flow.test.ts; the rest of the web still reads v1)
declare module '@export/quiz_data.v2.json' {
  const value: unknown;
  export default value;
}
declare module '@export/quiz_core.v2.json' {
  const value: unknown;
  export default value;
}
declare module '@export/golden.v2.json' {
  const value: unknown;
  export default value;
}
