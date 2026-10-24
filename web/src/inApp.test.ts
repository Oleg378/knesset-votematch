import { describe, expect, it } from 'vitest';
import { isInAppViewer } from './inApp';

const IOS = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko)';
const ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8';

describe('isInAppViewer: browsers scroll the window, app viewers get the frame', () => {
  it.each([
    ['Safari, iPhone', `${IOS} Version/18.1 Mobile/15E148 Safari/604.1`],
    ['Chrome, iPhone', `${IOS} CriOS/130.0.6723.90 Mobile/15E148 Safari/604.1`],
    ['Firefox, iPhone', `${IOS} FxiOS/132.0 Mobile/15E148 Safari/605.1.15`],
    ['Chrome, Android', `${ANDROID}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36`],
    ['Chrome, Mac', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'],
  ])('%s: a browser', (_, ua) => {
    expect(isInAppViewer(ua, {})).toBe(false);
  });

  it.each([
    ['LinkedIn, iPhone', `${IOS} Mobile/15E148 [LinkedInApp]/9.30.1234`],
    ['Facebook, iPhone', `${IOS} Mobile/15E148 [FBAN/FBIOS;FBAV/490.0.0.40.107;FBBV/123]`],
    ['Instagram, iPhone', `${IOS} Mobile/15E148 Instagram 350.0.0.0 (iPhone16,2; iOS 18_1; en_US)`],
    ['any app, iPhone (no «Safari/»)', `${IOS} Mobile/15E148`],
    ['an app, Android', `${ANDROID} Build/AP2A; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0.0.0 Mobile Safari/537.36`],
  ])('%s: a viewer', (_, ua) => {
    expect(isInAppViewer(ua, {})).toBe(true);
  });

  it('Telegram keeps Safari\'s user agent: known by the object it puts on the page', () => {
    const safari = `${IOS} Version/18.1 Mobile/15E148 Safari/604.1`;
    expect(isInAppViewer(safari, { TelegramWebviewProxy: {} })).toBe(true);
    expect(isInAppViewer(safari, { TelegramWebview: {} })).toBe(true);
  });
});
