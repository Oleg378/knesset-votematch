/**
 * Product metrics (customer 2026-10-24, DECISIONS.md H): two counts — how many start the quiz, how many reach the results —
 * sent as a beacon to the site's own address /count/<event>; on the hosting, functions/count/[event].js counts them.
 * Never answers, results or list ids; no cookies, no identifiers, no third party (the CSP allows the site's own address
 * only). The app never waits for the beacon: one lost to an ad blocker or an offline moment costs nothing.
 */
export type AnalyticsEvent = 'started' | 'finished';

/** The path of the beacon (robots.txt keeps crawlers away from it; the hosting answers it with a function). */
export const COUNT_PATH = '/count/';

export function track(event: AnalyticsEvent): void {
  try {
    navigator.sendBeacon?.(`${COUNT_PATH}${event}`);
  } catch {
    // a metric is never worth an error on screen
  }
}
