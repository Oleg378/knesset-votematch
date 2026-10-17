/**
 * Product metrics: events only, never answers, results or list ids. No third-party trackers, no cookies.
 * No-op until the customer picks a backend (web/SPEC.md «Metrics and privacy»).
 */
export type AnalyticsEvent = 'started' | 'finished';

export function track(_event: AnalyticsEvent): void {
  // intentionally empty
}
