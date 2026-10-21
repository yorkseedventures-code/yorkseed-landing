// Reads an event page (Luma, Eventbrite, Partiful, Meetup or any page with event data)
// and returns its details so the List's "Submit event" form can fill itself in.
// GET /.netlify/functions/extract?url=https://luma.com/abc123
const UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36";
const JSONH = { "content-type": "application/json; charset=utf-8", "cache-control": "public, max-age=600" };
const out = (obj, status = 200) => new Response(JSON.stringify(obj), { status, headers: JSONH });

const clean = (s) => (s || "").replace(/\s+/g, " ").trim();
const short = (s, n = 600) => { s = clean(s); return s.length > n ? s.slice(0, n).replace(/\s+\S*$/, "") + "…" : s; };
const decode = (s) => (s || "").replace(/&amp;/g, "&").replace(/&quot;/g, '"').replace(/&#39;|&#x27;/g, "'").replace(/&lt;/g, "<").replace(/&gt;/g, ">");
function meta(html, ...names) {
  for (const n of names) {
    const re1 = new RegExp(`<meta[^>]+(?:property|name)=["']${n}["'][^>]*content=["']([^"']+)`, "i");
    const re2 = new RegExp(`<meta[^>]+content=["']([^"']+)["'][^>]*(?:property|name)=["']${n}["']`, "i");
    const m = html.match(re1) || html.match(re2);
    if (m) return decode(m[1]);
  }
  return "";
}
function textOf(node) {
  if (!node) return "";
  if (typeof node === "string") return node;
  if (Array.isArray(node)) return node.map(textOf).join(" ");
  return [node.text || "", textOf(node.content)].join(node.type === "paragraph" ? " " : "");
}
async function luma(slug) {
  const r = await fetch("https://api.lu.ma/url?url=" + encodeURIComponent(slug), { headers: { "user-agent": UA, accept: "application/json" } });
  if (!r.ok) return null;
  const j = await r.json(); const d = j.data || {}; const e = d.event || {};
  if (!e.name) return null;
  const g = e.geo_address_info || {};
  return {
    title: e.name, start: e.start_at || d.start_at, end: e.end_at, tz: e.timezone,
    city: g.city || "", country: g.country || "",
    venue: clean(g.mode === "obfuscated" ? (g.sublocality || "") : (g.address || g.full_address || "")),
    host: clean((d.hosts || []).map((h) => h.name).filter(Boolean).slice(0, 2).join(" & ") || (d.calendar && d.calendar.name) || ""),
    desc: short(textOf(d.description_mirror)), image: e.cover_url || "", online: e.location_type === "online",
  };
}
function fromLd(html) {
  const blocks = [...html.matchAll(/<script[^>]+application\/ld\+json[^>]*>([\s\S]*?)<\/script>/gi)].map((m) => m[1]);
  for (const b of blocks) {
    let data; try { data = JSON.parse(b.trim()); } catch { continue; }
    const items = [].concat(data["@graph"] || data);
    for (const it of items) {
      const t = [].concat(it && it["@type"] || []).join(" ");
      if (!/Event/.test(t)) continue;
      const loc = [].concat(it.location || [])[0] || {}; const addr = loc.address || {};
      const org = [].concat(it.organizer || [])[0] || {};
      return {
        title: decode(it.name || ""), start: it.startDate, end: it.endDate, tz: "",
        city: typeof addr === "string" ? "" : (addr.addressLocality || ""), country: typeof addr === "string" ? "" : (addr.addressCountry && (addr.addressCountry.name || addr.addressCountry)) || "",
        venue: clean([loc.name, typeof addr === "string" ? addr : addr.streetAddress].filter(Boolean).join(", ")),
        host: clean(org.name || ""), desc: short(decode(it.description || "")),
        image: [].concat(it.image || [])[0] || "", online: /Online/.test(it.eventAttendanceMode || "") || loc["@type"] === "VirtualLocation",
      };
    }
  }
  return null;
}
export default async (req) => {
  const raw = new URL(req.url).searchParams.get("url") || "";
  let u; try { u = new URL(raw); } catch { return out({ error: "bad_url" }, 400); }
  if (!/^https?:$/.test(u.protocol) || /^(localhost|127\.|10\.|192\.168\.|169\.254\.|\[)/.test(u.hostname) || /^\d+\.\d+\.\d+\.\d+$/.test(u.hostname)) return out({ error: "bad_url" }, 400);
  try {
    if (/(^|\.)(lu\.ma|luma\.com)$/.test(u.hostname)) {
      const slug = u.pathname.replace(/^\/+|\/+$/g, "").split("/")[0];
      const r = slug && (await luma(slug));
      if (r) return out({ ok: true, source: "luma", ...r });
    }
    const res = await fetch(u.toString(), { headers: { "user-agent": UA, accept: "text/html" }, redirect: "follow" });
    const html = (await res.text()).slice(0, 2_000_000);
    const ld = fromLd(html) || {};
    const r = {
      title: ld.title || meta(html, "og:title", "twitter:title"),
      start: ld.start || meta(html, "event:start_time", "startDate"), end: ld.end || "", tz: ld.tz || "",
      city: ld.city || "", country: ld.country || "", venue: ld.venue || "", host: ld.host || "",
      desc: ld.desc || short(meta(html, "og:description", "description", "twitter:description")),
      image: ld.image || meta(html, "og:image", "twitter:image"), online: !!ld.online,
    };
    if (!r.title) return out({ ok: false, error: "no_details" }, 200);
    return out({ ok: true, source: ld.title ? "structured" : "meta", ...r });
  } catch (e) {
    return out({ ok: false, error: "fetch_failed" }, 200);
  }
};
