/**
 * An app's built-in viewer, not a browser (customer 2026-10-24: «надо отличать норм браузеры от просмотрщиков»): there
 * the page uses the frame (app.css: the header outside the scroll), in a browser the window scrolls and the browser's
 * bars hide. The test is inapp-spy's (5.0.10, MIT, github.com/shalanah/inapp-spy; copied, not a dependency — the
 * package also carries code that touches IndexedDB): a known app in the user agent; any iOS web view (an Apple device
 * whose user agent has no «Safari/», which Safari, Chrome and Firefox on iOS all have); an Android web view («wv)»);
 * and Telegram, which keeps Safari's user agent and is known by the object it puts on the page.
 */
const APPS =
  /FB_IAB|FBAN|\bFB[\w_]+\/|\bFacebook|\bInstagram|\bTwitter|\bLine\/|\bMicroMessenger\/|\bBarcelona|musical_ly|Bytedance|Snapchat|LinkedInApp|GSA|\b(WAiOS|WA4A)\/|\bReddit\//i;
const WEB_VIEW = /WebView|(iPhone|iPod|iPad)(?!.*Safari\/)|Android.*wv\)/i;
const TELEGRAM = ['TelegramWebview', 'TelegramWebviewProxy', 'TelegramWebviewProxyProto'];

export function isInAppViewer(ua: string = navigator.userAgent, w: object = window): boolean {
  return APPS.test(ua) || WEB_VIEW.test(ua) || TELEGRAM.some((name) => name in w);
}

/**
 * Sets data-frame on <html> in an app's viewer (or with ?frame, to check the frame in a browser). Checked again when
 * the page has loaded: a viewer may put its object on the page late; the page is still at its top then.
 */
export function chooseScrolling(): void {
  const set = () => document.documentElement.toggleAttribute('data-frame',
    isInAppViewer() || new URLSearchParams(location.search).has('frame'));
  set();
  if (document.readyState !== 'complete') window.addEventListener('load', set, { once: true });
}
