"""Network step for The Yorkseed List. Runs in GitHub Actions only (YS_NETWORK=1), never on Netlify.

1. Imports queued events from list/data/pending-import.json: resolves each one's own registration
   link (stripping other sites' referral/tracking parameters), takes the organizer's description,
   and adds it to list/events.json.
2. Finds the real cover photo for every upcoming event and caches it in list/data/photos.json,
   which the List and the city pages use instead of the placeholder images.
"""
import json, os, re, html, datetime as dt
from urllib.request import Request, urlopen
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode, urljoin
from concurrent.futures import ThreadPoolExecutor

REPO = os.environ.get("YS_REPO", ".")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml", "Accept-Language": "en-US,en;q=0.9"}
TODAY = dt.date.today().isoformat()
DROP_KEYS = re.compile(r'^(utm_.*|ref|ref_src|source|src|via|aff|affiliate|fbclid|gclid|mc_[a-z]+|_gl|tk|lu_ref)$', re.I)
SKIP_HOSTS = re.compile(r'(foundercal\.com|side-events-guide\.com|sobremesa[a-z.-]*|google\.[a-z.]+|goo\.gl|maps\.|facebook\.com|instagram\.com|twitter\.com|x\.com|linkedin\.com|tiktok\.com|youtube\.com|apple\.com|play\.google)', re.I)

def get(url, timeout=15):
    r = urlopen(Request(url, headers=UA), timeout=timeout)
    return r.geturl(), r.read(1_500_000).decode("utf-8", "ignore")

def clean(url):
    p = urlsplit(url)
    q = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if not DROP_KEYS.match(k) and "foundercal" not in v.lower()]
    return urlunsplit((p.scheme, p.netloc, p.path, urlencode(q), ""))

def meta(page, *names):
    for n in names:
        m = re.search(r'<meta[^>]+(?:property|name)=["\']%s["\'][^>]*content=["\']([^"\']+)' % re.escape(n), page, re.I) or \
            re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]*(?:property|name)=["\']%s["\']' % re.escape(n), page, re.I)
        if m: return html.unescape(m.group(1)).strip()
    return ""

def photo_from(url, page):
    m = re.search(r'https://images\.lumacdn\.com/[^"\'\s)]*event-covers/[^"\'\s)\\]+', page)
    if m: return m.group(0)
    img = meta(page, "og:image", "og:image:url", "twitter:image", "twitter:image:src")
    return urljoin(url, img) if img else ""

def short(text, n=260):
    t = re.sub(r'\s+', ' ', text or "").strip()
    if len(t) <= n: return t
    cut = t[:n]; i = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return (cut[:i + 1] if i > 80 else cut.rsplit(" ", 1)[0] + "…")

def load(path, default):
    try: return json.load(open(path))
    except Exception: return default

# ---------- 1. import queued events ----------
def resolve(item):
    src = item.get("src", "")
    try:
        final, page = get(src)
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', page)
        cands = [urljoin(final, h) for h in hrefs]
        out = [c for c in cands if "/out/" in c] + [c for c in cands if c.startswith("http") and not SKIP_HOSTS.search(urlsplit(c).netloc)]
        for c in out:
            try:
                reg, rp = get(c)
                if SKIP_HOSTS.search(urlsplit(reg).netloc): continue
                return {**item, "link": clean(reg), "desc": short(meta(rp, "og:description", "description", "twitter:description")),
                        "photo": photo_from(reg, rp)}
            except Exception: continue
    except Exception: pass
    return None

def import_pending():
    pend_p, ev_p, mas_p = f"{REPO}/list/data/pending-import.json", f"{REPO}/list/events.json", f"{REPO}/list/data/master.json"
    pend = load(pend_p, [])
    if not pend: return {}
    events = load(ev_p, []); master = load(mas_p, {"events": []})
    norm = lambda s: re.sub(r'[^a-z0-9]+', '', (s or '').lower())[:40]
    seen_l = {(e.get("link") or "").split("?")[0].rstrip("/") for e in events + master["events"]}
    seen_t = {(norm(e.get("title")), e.get("date")) for e in events + master["events"]}
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(resolve, pend))
    added, left, photos = 0, [], {}
    for item, r in zip(pend, res):
        if not r: left.append(item); continue
        key = r["link"].split("?")[0].rstrip("/")
        if key in seen_l or (norm(r["title"]), r["date"]) in seen_t: continue
        seen_l.add(key); seen_t.add((norm(r["title"]), r["date"]))
        if r.get("photo"): photos[r["link"]] = r["photo"]
        r.pop("photo", None); r.pop("src", None)
        if not r.get("desc"): r["desc"] = f"{r.get('host') or 'A community'} event in New York. Details and registration on the event page."
        events.append(r); added += 1
    json.dump(events, open(ev_p, "w"), ensure_ascii=False, indent=1)
    json.dump(left, open(pend_p, "w"), ensure_ascii=False, indent=1)
    print(f"import: {added} added, {len(left)} still unresolved")
    return photos

# ---------- 1b. import whole city calendars (list/data/pending-cities.json) ----------
from zoneinfo import ZoneInfo
_TZ = {}
def hub_tz(hub):
    if not _TZ:
        for h in load(f"{REPO}/list/data/master.json", {"hubs": []})["hubs"]: _TZ[h["id"]] = h["tz"]
    return _TZ.get(hub, "UTC")

def to_local(iso, tz):
    try:
        d = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if d.tzinfo is None: return d.date().isoformat(), d.strftime("%H:%M") if "T" in iso else None
        d = d.astimezone(ZoneInfo(tz)); return d.date().isoformat(), d.strftime("%H:%M")
    except Exception: return None, None

def luma_event(link):
    slug = urlsplit(link).path.strip("/").split("/")[0]
    try:
        r = urlopen(Request("https://api.lu.ma/url?url=" + slug, headers={**UA, "Accept": "application/json"}), timeout=15)
        d = json.loads(r.read().decode("utf-8", "ignore")).get("data") or {}; e = d.get("event") or {}
        if not e.get("name"): return None
        g = e.get("geo_address_info") or {}
        def txt(n):
            if isinstance(n, list): return " ".join(txt(x) for x in n)
            if isinstance(n, dict): return (n.get("text") or "") + " " + txt(n.get("content") or [])
            return ""
        return {"title": e["name"], "start": e.get("start_at"), "end": e.get("end_at"), "city": g.get("city", ""),
                "venue": (g.get("sublocality") if g.get("mode") == "obfuscated" else (g.get("address") or "")) or "",
                "host": " & ".join([h.get("name") for h in (d.get("hosts") or []) if h.get("name")][:2]),
                "desc": short(txt(d.get("description_mirror"))), "photo": e.get("cover_url") or ""}
    except Exception: return None

def ld_event(page):
    for b in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', page, re.S | re.I):
        try: data = json.loads(b.strip())
        except Exception: continue
        for it in (data.get("@graph") if isinstance(data, dict) and data.get("@graph") else (data if isinstance(data, list) else [data])):
            if isinstance(it, dict) and "Event" in str(it.get("@type", "")):
                loc = it.get("location") or {}; loc = loc[0] if isinstance(loc, list) and loc else loc
                addr = loc.get("address") if isinstance(loc, dict) else ""
                org = it.get("organizer") or {}; org = org[0] if isinstance(org, list) and org else org
                img = it.get("image"); img = img[0] if isinstance(img, list) and img else img
                return {"title": html.unescape(it.get("name") or ""), "start": it.get("startDate"), "end": it.get("endDate"),
                        "city": addr.get("addressLocality", "") if isinstance(addr, dict) else "",
                        "venue": ", ".join(x for x in [loc.get("name") if isinstance(loc, dict) else "", addr.get("streetAddress") if isinstance(addr, dict) else ""] if x),
                        "host": org.get("name", "") if isinstance(org, dict) else "", "desc": short(html.unescape(it.get("description") or "")),
                        "photo": img if isinstance(img, str) else ((img or {}).get("url") if isinstance(img, dict) else "")}
    return None

def city_event(args):
    ev_url, hub = args
    try:
        final, page = get(ev_url)
        base = ld_event(page) or {"title": meta(page, "og:title"), "start": "", "desc": "", "photo": meta(page, "og:image")}
        hrefs = [urljoin(final, h) for h in re.findall(r'href=["\']([^"\']+)["\']', page)]
        outs = [h for h in hrefs if "/out/" in h] + [h for h in hrefs if h.startswith("http") and not SKIP_HOSTS.search(urlsplit(h).netloc)]
        REG = re.compile(r'(lu\.ma|luma\.com|eventbrite\.|partiful\.com|meetup\.com|ti\.to|tito\.io|posh\.vip|dice\.fm|typeform\.com|forms\.gle|tally\.so|airtable\.com|hubspot|zoom\.us)', re.I)
        outs = sorted(dict.fromkeys(outs), key=lambda h: ("/out/" not in h and not REG.search(urlsplit(h).netloc)))
        reg, info = "", None
        for c in outs[:4]:
            try:
                r, rp = get(c)
                if SKIP_HOSTS.search(urlsplit(r).netloc): continue
                reg = clean(r)
                info = luma_event(reg) if re.search(r'(lu\.ma|luma\.com)', urlsplit(reg).netloc) else (ld_event(rp) or {"title": meta(rp, "og:title"), "desc": short(meta(rp, "og:description", "description")), "photo": photo_from(r, rp)})
                break
            except Exception: continue
        if not reg: return None
        info = {**{k: v for k, v in (base or {}).items() if v}, **{k: v for k, v in (info or {}).items() if v}}
        if not info.get("title") or not info.get("start"): return None
        tz = hub_tz(hub); date, start = to_local(info["start"], tz)
        if not date: return None
        end = to_local(info["end"], tz) if info.get("end") else (None, None)
        return {"title": re.sub(r'\s*[|·-]\s*(Luma|Eventbrite|Meetup|Partiful)\s*$', '', info["title"]).strip(), "hub": hub, "date": date,
                "start": start, "end": end[1] if end[0] == date else None, "venue": info.get("venue", ""), "host": info.get("host", ""),
                "link": reg, "desc": info.get("desc", ""), "_photo": info.get("photo", "")}
    except Exception: return None

def import_cities():
    pc_p = f"{REPO}/list/data/pending-cities.json"; cities = load(pc_p, [])
    if not cities: return {}
    jobs = []
    for c in cities:
        try:
            final, page = get(c["url"])
            urls = sorted({urljoin(final, h).split("?")[0] for h in re.findall(r'href=["\']([^"\']*/events/[^"\'#?]+)', page)})
            jobs += [(u, c["hub"]) for u in urls]
            print(f"city {c['hub']}: {len(urls)} event pages")
        except Exception as ex: print(f"city {c['hub']}: failed {ex}")
    with ThreadPoolExecutor(6) as ex: res = [r for r in ex.map(city_event, jobs) if r]
    events = load(f"{REPO}/list/events.json", []); master = load(f"{REPO}/list/data/master.json", {"events": []})
    norm = lambda s: re.sub(r'[^a-z0-9]+', '', (s or '').lower())[:40]
    seen_l = {(e.get("link") or "").split("?")[0].rstrip("/") for e in events + master["events"]}
    seen_t = {(norm(e.get("title")), e.get("date")) for e in events + master["events"]}
    photos, added = {}, 0
    for r in res:
        if r["date"] < TODAY: continue
        k = r["link"].split("?")[0].rstrip("/")
        if k in seen_l or (norm(r["title"]), r["date"]) in seen_t: continue
        seen_l.add(k); seen_t.add((norm(r["title"]), r["date"]))
        if r.get("_photo"): photos[r["link"]] = r["_photo"]
        r.pop("_photo", None)
        if not r.get("desc"): r["desc"] = "Details and registration on the event page."
        events.append(r); added += 1
    json.dump(events, open(f"{REPO}/list/events.json", "w"), ensure_ascii=False, indent=1)
    json.dump([], open(pc_p, "w"))
    print(f"cities import: {added} new events from {len(jobs)} pages")
    return photos

# ---------- 1c. daily sources: Luma discover categories (list/data/sources.json) ----------
CITY_ALIAS = {"san francisco": "sf", "oakland": "sf", "berkeley": "sf", "palo alto": "sf", "mountain view": "sf", "san jose": "sf",
    "menlo park": "sf", "sunnyvale": "sf", "santa clara": "sf", "redwood city": "sf", "san mateo": "sf", "cupertino": "sf", "south san francisco": "sf",
    "new york": "nyc", "brooklyn": "nyc", "manhattan": "nyc", "queens": "nyc", "jersey city": "nyc", "hoboken": "nyc", "long island city": "nyc",
    "washington": "dc", "arlington": "dc", "abu dhabi": "dxb", "dubai": "dxb", "sao paulo": "sao", "rio de janeiro": "sao", "denver": "den",
    "boulder": "den", "cambridge|united states": "bos", "somerville": "bos", "santa monica": "la", "culver city": "la", "pasadena": "la",
    "venice": "la", "bangalore": "blr", "bengaluru": "blr", "mumbai": "bom", "navi mumbai": "bom", "tel aviv yafo": "tlv", "tel aviv": "tlv",
    "kowloon": "hkg", "shibuya": "tyo", "minato city": "tyo", "chiyoda city": "tyo", "shinjuku city": "tyo", "bellevue": "sea", "redmond": "sea",
    "kirkland": "sea", "vancouver|canada": "yvr", "burnaby": "yvr", "espoo": "hel", "london|united kingdom": "ldn", "ciudad de mexico": "mex", "mexico city": "mex"}
def _n(s): return re.sub(r'\s+', ' ', re.sub(r'[^a-z ]', ' ', __import__("unicodedata").normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower())).strip()
def city_hub(city, country, hubs):
    c, k = _n(city), _n(country)
    if not c: return None
    if f"{c}|{k}" in CITY_ALIAS: return CITY_ALIAS[f"{c}|{k}"]
    if c in CITY_ALIAS and "|" not in c: return CITY_ALIAS[c]
    for h in hubs:
        if h["id"] != "virtual" and _n(h["name"]) == c: return h["id"]
    return None

def import_sources():
    srcs = load(f"{REPO}/list/data/sources.json", [])
    if not srcs: return {}
    master = load(f"{REPO}/list/data/master.json", {"events": [], "hubs": []}); hubs = master["hubs"]
    events = load(f"{REPO}/list/events.json", [])
    norm = lambda s: re.sub(r'[^a-z0-9]+', '', (s or '').lower())[:40]
    seen_l = {(e.get("link") or "").split("?")[0].rstrip("/") for e in events + master["events"]}
    seen_t = {(norm(e.get("title")), e.get("date")) for e in events + master["events"]}
    horizon = (dt.date.today() + dt.timedelta(days=120)).isoformat()
    photos, added = {}, 0
    for src in srcs:
        if src.get("type") != "luma_category": continue
        cursor, pages, kept = None, 0, 0
        while pages < int(src.get("max_pages", 60)):
            q = f"https://api.lu.ma/discover/get-paginated-events?category_api_id={src['id']}&pagination_limit=50" + (f"&pagination_cursor={cursor}" if cursor else "")
            try:
                r = urlopen(Request(q, headers={**UA, "Accept": "application/json"}), timeout=20); d = json.loads(r.read().decode("utf-8", "ignore"))
            except Exception as ex:
                code = getattr(ex, "code", 0)
                if code == 429: time.sleep(5); continue
                print(f"source {src['id']}: stopped ({ex})"); break
            pages += 1
            for en in d.get("entries") or []:
                e = en.get("event") or {}; g = e.get("geo_address_info") or {}
                if not e.get("name") or not e.get("start_at") or not e.get("url"): continue
                if e.get("location_type") == "online": continue          # in-person events only
                hub = city_hub(g.get("city"), g.get("country"), hubs)
                if not hub: continue
                tz = hub_tz(hub) if hub != "virtual" else "America/New_York"
                date, start = to_local(e["start_at"], tz)
                if not date or date < TODAY or date > horizon: continue
                link = "https://luma.com/" + e["url"]
                if link in seen_l or (norm(e["name"]), date) in seen_t: continue
                ed, et = to_local(e["end_at"], tz) if e.get("end_at") else (None, None)
                venue = (g.get("sublocality") if g.get("mode") == "obfuscated" else (g.get("address") or "")) or ""
                host = " & ".join([h.get("name") for h in (en.get("hosts") or []) if h.get("name")][:2]) or ((en.get("calendar") or {}).get("name") or "")
                events.append({"title": e["name"].strip(), "hub": hub, "date": date, "start": start, "end": et if ed == date else None,
                               "venue": venue, "host": host, "link": link, "desc": "Details and registration on the event page.", "src": "luma"})
                if e.get("cover_url"): photos[link] = e["cover_url"]
                seen_l.add(link); seen_t.add((norm(e["name"]), date)); added += 1; kept += 1
            if not d.get("has_more") or not d.get("next_cursor"): break
            cursor = d["next_cursor"]; time.sleep(0.4)
        print(f"source {src['id']}: {pages} pages, {kept} new events in List cities")
    json.dump(events, open(f"{REPO}/list/events.json", "w"), ensure_ascii=False, indent=1)
    return photos

def fill_luma_descriptions(limit=250):
    """Add the organizer's own description to Luma-sourced events that only have the placeholder."""
    p = f"{REPO}/list/events.json"; events = load(p, [])
    todo = [e for e in events if e.get("src") == "luma" and e.get("desc", "").startswith("Details and registration") and e.get("date", "") >= TODAY][:limit]
    def one(e):
        info = luma_event(e["link"]); time.sleep(0.3)
        return e, info
    with ThreadPoolExecutor(3) as ex:
        for e, info in ex.map(one, todo):
            if info and info.get("desc"): e["desc"] = info["desc"]
            if info and info.get("venue") and not e.get("venue"): e["venue"] = info["venue"]
    json.dump(events, open(p, "w"), ensure_ascii=False, indent=1)
    print(f"descriptions: filled {sum(1 for e in todo if not e['desc'].startswith('Details and registration'))} of {len(todo)}")

# ---------- 2. real event photos ----------
import time
def luma_cover(link):
    p = urlsplit(link); slug = p.path.strip("/").split("/")[0]
    if not slug: return ""
    for attempt in range(4):
        try:
            r = urlopen(Request("https://api.lu.ma/url?url=" + slug, headers={**UA, "Accept": "application/json"}), timeout=15)
            d = json.loads(r.read().decode("utf-8", "ignore"))
            ev = (d.get("data") or {}).get("event") or {}
            return ev.get("cover_url") or ""
        except Exception as ex:
            code = getattr(ex, "code", 0)
            if code in (429, 500, 502, 503, 504) or not code: time.sleep(2 * (attempt + 1)); continue
            return ""
    return ""

def fetch_photo(link):
    try:
        if re.search(r'(^|\.)(lu\.ma|luma\.com)$', urlsplit(link).hostname or ""):
            img = luma_cover(link)
            if img: return link, img
        final, page = get(link)
        return link, photo_from(final, page)
    except Exception:
        return link, ""

def refresh_photos(seed):
    ph_p = f"{REPO}/list/data/photos.json"
    cache = load(ph_p, {})
    for k, v in seed.items(): cache[k] = {"img": v, "t": TODAY}
    master = load(f"{REPO}/list/data/master.json", {"events": []}); extra = load(f"{REPO}/list/events.json", [])
    links = sorted({e["link"] for e in master["events"] + extra if e.get("link") and e.get("date", "") >= TODAY})
    retry_after = (dt.date.today() - dt.timedelta(days=2)).isoformat()
    todo = [l for l in links if l not in cache or (not cache[l].get("img") and cache[l].get("t", "") < retry_after)][:600]
    luma = [l for l in todo if re.search(r'(lu\.ma|luma\.com)', l)]; other = [l for l in todo if l not in luma]
    with ThreadPoolExecutor(12) as ex:            # other sites: in parallel
        for link, img in ex.map(fetch_photo, other): cache[link] = {"img": img or None, "t": TODAY}
    with ThreadPoolExecutor(3) as ex:             # Luma: gently, to stay under its rate limit
        for link, img in ex.map(lambda l: (time.sleep(0.3), fetch_photo(l))[1], luma): cache[link] = {"img": img or None, "t": TODAY}
    cache = {k: v for k, v in cache.items() if k in links}
    json.dump(cache, open(ph_p, "w"), ensure_ascii=False, indent=0)
    print(f"photos: {sum(1 for v in cache.values() if v.get('img'))} of {len(cache)} events have a real photo ({len(todo)} checked)")

if __name__ == "__main__":
    seed = {}
    for step in (import_pending, import_cities, import_sources):
        try: seed.update(step() or {})
        except Exception as ex: print(f"{step.__name__} failed: {ex}")
    try: fill_luma_descriptions()
    except Exception as ex: print(f"descriptions failed: {ex}")
    refresh_photos(seed)
