// Opens The Yorkseed List on the visitor's own city.
// Adds the visitor's approximate location (from Netlify, no browser prompt) to a short-lived cookie on the
// List's landing page. The page then opens the nearest city. Search engines and link previews are left alone.
const BOT = /(bot|crawl|spider|slurp|preview|facebookexternalhit|embedly|iframely|whatsapp|telegram|discord|slack|lighthouse|headless)/i;

export default async (request, context) => {
  const res = await context.next();
  try {
    const url = new URL(request.url);
    const isList = url.hostname.startsWith("list.") ? url.pathname === "/" : /^\/list\/?(index\.html)?$/.test(url.pathname);
    if (!isList || BOT.test(request.headers.get("user-agent") || "")) return res;
    const g = context.geo || {};
    if (typeof g.latitude !== "number" || typeof g.longitude !== "number") return res;
    const v = [g.latitude.toFixed(2), g.longitude.toFixed(2), g.country?.code || ""].join("|");
    res.headers.append("Set-Cookie", `ys_geo=${encodeURIComponent(v)}; Path=/; Max-Age=1800; SameSite=Lax; Secure`);
  } catch (_) {}
  return res;
};

export const config = { path: ["/", "/list", "/list/", "/list/index.html"] };
