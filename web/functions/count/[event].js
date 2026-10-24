// Cloudflare Pages Function: the metrics beacon of the site (src/analytics.ts). POST /count/started or /count/finished adds
// one data point to the Workers Analytics Engine dataset bound as COUNTS (wrangler.toml). Nothing else is read or kept:
// no body, no cookies, no address, no identifier. The counts: Cloudflare dashboard → Analytics Engine → SQL, e.g.
//   SELECT blob1 AS event, count() AS n FROM quiz_events GROUP BY event
const EVENTS = new Set(['started', 'finished']);

export async function onRequestPost({ params, env }) {
  const event = String(params.event);
  if (!EVENTS.has(event)) return new Response(null, { status: 404 });
  env.COUNTS?.writeDataPoint({ blobs: [event], doubles: [1], indexes: [event] });
  return new Response(null, { status: 204, headers: { 'Cache-Control': 'no-store' } });
}

export async function onRequest() {
  return new Response(null, { status: 405, headers: { Allow: 'POST' } });
}
