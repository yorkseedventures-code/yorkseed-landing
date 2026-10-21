// Locks the Event Manager behind a browser login. Only someone with ADMIN_USER / ADMIN_PASS
// (set in Netlify > Site configuration > Environment variables) can even load the page.
export default async (request, context) => {
  const user = Netlify.env.get("ADMIN_USER");
  const pass = Netlify.env.get("ADMIN_PASS");
  if (!user || !pass) return new Response("Admin login is not configured.", { status: 503, headers: { "Cache-Control": "no-store" } });
  const auth = request.headers.get("authorization") || "";
  if (auth.startsWith("Basic ")) {
    let decoded = "";
    try { decoded = atob(auth.slice(6)); } catch (_) {}
    const i = decoded.indexOf(":");
    if (i > -1 && decoded.slice(0, i) === user && decoded.slice(i + 1) === pass) {
      const res = await context.next();
      res.headers.set("Cache-Control", "no-store");
      res.headers.set("X-Robots-Tag", "noindex, nofollow");
      return res;
    }
  }
  return new Response("Login required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="Yorkseed team", charset="UTF-8"', "Cache-Control": "no-store" },
  });
};
export const config = { path: ["/event-admin", "/event-admin.html", "/event-admin/*"] };
