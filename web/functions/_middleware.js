// Cloudflare Pages middleware (runs before every request, pages and functions alike): one address for the site —
// www.<domain> goes to <domain> with the same path and query, permanently. The _redirects file cannot match a host, so it is
// done here. Everything else passes through untouched.
export async function onRequest({ request, next }) {
  const url = new URL(request.url);
  if (url.hostname.startsWith('www.')) {
    url.hostname = url.hostname.slice(4);
    return Response.redirect(url.toString(), 301);
  }
  return next();
}
