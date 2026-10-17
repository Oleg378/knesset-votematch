/**
 * The system/browser Back button as the in-app «Back», without a router and without touching the URL (results never go
 * into the URL). Off the start screen one extra history entry (same URL, no data) is kept; a pop of it is turned into a
 * BACK action and the entry is re-armed. On the start screen the entry is dropped, so Back leaves the site as usual.
 */
export interface HistoryLike {
  pushState(data: unknown, unused: string): void;
  back(): void;
}

export interface BackGuard {
  /** Call whenever the screen may have changed; `atStart` = the start screen is shown. */
  sync(atStart: boolean): void;
  /** popstate handler; true = the app should go back one screen. */
  onPop(): boolean;
}

export function createBackGuard(h: HistoryLike): BackGuard {
  let armed = false;
  let ignoreNextPop = false;
  return {
    sync(atStart) {
      if (!atStart && !armed) {
        h.pushState({ quizGuard: true }, '');
        armed = true;
      } else if (atStart && armed) {
        armed = false;
        ignoreNextPop = true;
        h.back();
      }
    },
    onPop() {
      if (ignoreNextPop) {
        ignoreNextPop = false;
        return false;
      }
      armed = false;
      return true;
    },
  };
}
