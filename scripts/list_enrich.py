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
REG_HOSTS = re.compile(r'(lu\.ma|luma\.com|eventbrite\.|partiful\.com|meetup\.com|ti\.to|tito\.io|posh\.vip|dice\.fm)', re.I)
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
        if REG_HOSTS.search(urlsplit(ev_url).netloc):        # a direct registration link
            reg = clean(ev_url)
            if re.search(r'(lu\.ma|luma\.com)', urlsplit(reg).netloc): info = luma_event(reg)
            else:
                r, rp = get(ev_url); reg = clean(r)
                info = ld_event(rp) or {"title": meta(rp, "og:title"), "desc": short(meta(rp, "og:description", "description")), "photo": photo_from(r, rp)}
            return finish(info or {}, reg, hub)
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
        return finish(info, reg, hub)
    except Exception: return None

def finish(info, reg, hub):
    try:
        if not info.get("title") or not info.get("start"): return None
        tz = hub_tz(hub); date, start = to_local(info["start"], tz)
        if not date: return None
        end = to_local(info["end"], tz) if info.get("end") else (None, None)
        return {"title": re.sub(r'\s*[|·-]\s*(Luma|Eventbrite|Meetup|Partiful)\s*$', '', info["title"]).strip(), "hub": hub, "date": date,
                "start": start, "end": end[1] if end[0] == date else None, "venue": info.get("venue", ""), "host": info.get("host", ""),
                "link": reg, "desc": info.get("desc", ""), "_photo": info.get("photo", ""), "_city": info.get("city", "")}
    except Exception: return None

REPORT = []
def import_cities():
    pc_p = f"{REPO}/list/data/pending-cities.json"; cities = load(pc_p, [])
    if not cities: return {}
    jobs = []
    for c in cities:
        try:
            final, page = get(c["url"])
            hrefs = [html.unescape(urljoin(final, h)) for h in re.findall(r'href=["\']([^"\']+)["\']', page)]
            urls = sorted({h.split("?")[0] for h in hrefs if "/events/" in urlsplit(h).path and urlsplit(h).netloc == urlsplit(final).netloc})
            raw = re.findall(r'https?:(?:\\?/){2}(?:www\.)?eventbrite\.[a-z.]+(?:\\?/)e(?:\\?/)[A-Za-z0-9-]+', page)   # links inside page data
            hrefs += [r.replace("\\/", "/") for r in raw]
            direct = sorted({clean(h) for h in hrefs if h.startswith("http") and REG_HOSTS.search(urlsplit(h).netloc)
                             and not re.search(r'eventbrite\.[a-z.]+/(?!e/)', h)})
            jobs += [(u, c["hub"]) for u in urls + direct]
            REPORT.append({"source": c["url"], "hub": c["hub"], "event_pages": len(urls), "direct_links": len(direct), "page_bytes": len(page)})
            print(f"city {c['hub']}: {len(urls)} event pages, {len(direct)} direct links")
        except Exception as ex: print(f"city {c['hub']}: failed {ex}"); REPORT.append({"source": c["url"], "hub": c["hub"], "error": str(ex)[:200]})
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
        r.pop("_photo", None); r.pop("_city", None)
        if not r.get("desc"): r["desc"] = "Details and registration on the event page."
        events.append(r); added += 1
    json.dump(events, open(f"{REPO}/list/events.json", "w"), ensure_ascii=False, indent=1)
    json.dump([], open(pc_p, "w"))
    print(f"cities import: {added} new events from {len(jobs)} pages")
    REPORT.append({"cities_import_new_events": added, "jobs": len(jobs), "resolved": len(res), "by_hub": dict(__import__("collections").Counter(r["hub"] for r in res))})
    return photos

# ---------- 1d. queued candidate links (list/data/pending-links.json) ----------
# Each item: {"url": organizer page (Luma, Eventbrite, Meetup...), "hub", "title", "date"} where title/date come from a
# listing we saw elsewhere. The organizer's own data decides: an item is added only when the page's real date matches
# "date", its title matches, and it is in the hub's city. Otherwise it is skipped and reported, never guessed.
def _toks(t): return {w for w in re.findall(r'[a-z0-9]+', (t or "").lower()) if len(w) > 2 and w not in {"the", "and", "for", "with", "nyc", "new", "york"}}
def import_links():
    pl_p = f"{REPO}/list/data/pending-links.json"; items = load(pl_p, [])
    if not items: return {}
    hubs = load(f"{REPO}/list/data/master.json", {"hubs": []})["hubs"]
    with ThreadPoolExecutor(3) as ex: res = list(ex.map(lambda it: (time.sleep(0.3), city_event((it["url"], it["hub"])))[1], items))
    events = load(f"{REPO}/list/events.json", []); master = load(f"{REPO}/list/data/master.json", {"events": []})
    norm = lambda s: re.sub(r'[^a-z0-9]+', '', (s or '').lower())[:40]
    seen_l = {(e.get("link") or "").split("?")[0].rstrip("/") for e in events + master["events"]}
    seen_t = {(norm(e.get("title")), e.get("date")) for e in events + master["events"]}
    photos, added, keep, out = {}, 0, [], []
    for it, r in zip(items, res):
        why = ""
        if not r: why = "could not read the page"
        elif r["date"] != it["date"]: why = f"page date {r['date']} is not {it['date']}"
        elif r["date"] < TODAY: why = "already happened"
        else:
            a, b = _toks(it.get("title")), _toks(r["title"])
            if a and b and len(a & b) / min(len(a), len(b)) < 0.5: why = f"title differs: {r['title']}"
            elif r.get("_city") and city_hub(r["_city"], "", hubs) not in (None, it["hub"]): why = f"city is {r['_city']}"
        if why:
            out.append({"url": it["url"], "title": it.get("title"), "skipped": why})
            if not r and it["date"] >= TODAY: keep.append(it)          # page didn't load: try again next run
            continue
        k = r["link"].split("?")[0].rstrip("/")
        if k in seen_l or (norm(r["title"]), r["date"]) in seen_t: out.append({"url": it["url"], "skipped": "already on the List"}); continue
        seen_l.add(k); seen_t.add((norm(r["title"]), r["date"]))
        if r.get("_photo"): photos[r["link"]] = r["_photo"]
        r.pop("_photo", None); r.pop("_city", None)
        if not r.get("desc"): r["desc"] = "Details and registration on the event page."
        events.append(r); added += 1; out.append({"url": it["url"], "added": r["title"], "date": r["date"]})
    json.dump(events, open(f"{REPO}/list/events.json", "w"), ensure_ascii=False, indent=1)
    json.dump(keep, open(pl_p, "w"), ensure_ascii=False, indent=1)
    print(f"links import: {added} added of {len(items)} queued, {len(keep)} kept for retry")
    REPORT.append({"links_import": out, "added": added})
    return photos

# ---------- 1e. approved List submissions (Yorkseed backend) ----------
# Events people submit on list.yorkseed.co and the team approves in the Event Manager. The List page already
# shows them live; copying them here gives each one its static city/event page and a cover photo.
def import_submissions():
    try:
        r = urlopen(Request("https://yorkseed-backend-production.up.railway.app/api/list-submissions/public", headers={**UA, "Accept": "application/json"}), timeout=20)
        subs = json.loads(r.read().decode("utf-8", "ignore")).get("events") or []
    except Exception as ex: print(f"submissions: skipped ({ex})"); return {}
    events = load(f"{REPO}/list/events.json", []); master = load(f"{REPO}/list/data/master.json", {"events": [], "hubs": []})
    hubs = {h["id"] for h in master.get("hubs", [])}
    norm = lambda s: re.sub(r'[^a-z0-9]+', '', (s or '').lower())[:40]
    seen_l = {(e.get("link") or "").split("?")[0].rstrip("/") for e in events + master["events"] if e.get("link")}
    seen_t = {(norm(e.get("title")), e.get("date")) for e in events + master["events"]}
    added, covers = 0, {}
    for d in subs:
        if d.get("hub") not in hubs or not d.get("date") or d["date"] < TODAY: continue
        if d.get("img") and d.get("link"): covers[d["link"]] = d["img"]      # the organizer's own upload beats a scraped photo
        k = (d.get("link") or "").split("?")[0].rstrip("/")
        if (k and k in seen_l) or (norm(d.get("title")), d["date"]) in seen_t: continue
        seen_l.add(k); seen_t.add((norm(d.get("title")), d["date"]))
        events.append({x: d.get(x) for x in ("title", "hub", "date", "start", "end", "venue", "host", "link", "desc", "type") if d.get(x)})
        added += 1
    if added: json.dump(events, open(f"{REPO}/list/events.json", "w"), ensure_ascii=False, indent=1)
    print(f"submissions: {added} approved events copied into events.json, {len(covers)} with an uploaded cover")
    return covers

# ---------- 1d. TechMeetups.io public API (free, no key, 60 requests/min): tech meetups by city ----------
# We keep only facts (title, date, venue, organizer) and link to the organizer's own registration page.
def import_techmeetups():
    try: ll = re.search(r"HUB_LL=\{(.*?)\}", open(f"{REPO}/list/index.html", encoding="utf-8").read(), re.S).group(1)
    except Exception: print("techmeetups: no hub coordinates"); return {}
    coords = {k: (float(a), float(b)) for k, a, b in re.findall(r"(\w+):\[(-?[\d.]+),(-?[\d.]+)\]", ll)}
    master = load(f"{REPO}/list/data/master.json", {"events": [], "hubs": []}); hubs = {h["id"] for h in master["hubs"]}
    events = load(f"{REPO}/list/events.json", [])
    norm = lambda s: re.sub(r'[^a-z0-9]+', '', (s or '').lower())[:40]
    canon = lambda u: re.sub(r'^https?://(www\.)?lu\.ma/', 'https://luma.com/', (u or '').split("?")[0].rstrip("/"))
    seen_l = {canon(e.get("link")) for e in events + master["events"] if e.get("link")}
    seen_t = {(norm(e.get("title")), e.get("date")) for e in events + master["events"]}
    calls = [0]
    def search(lat, lng, d0, d1):
        if calls[0] and calls[0] % 55 == 0: time.sleep(62)                 # stay under 60 requests a minute
        calls[0] += 1
        q = f"https://techmeetups.io/api/v1/events/search?lat={lat}&lng={lng}&radius_km=45&limit=50&date_from={d0}&date_to={d1}"
        for _ in range(3):
            try:
                r = urlopen(Request(q, headers={**UA, "Accept": "application/json"}), timeout=25); return json.loads(r.read().decode("utf-8", "ignore"))
            except Exception as ex:
                if getattr(ex, "code", 0) == 429: time.sleep(65); continue
                print(f"techmeetups: {ex}"); return None
        return None
    def window(lat, lng, d0, d1, out):                                     # the API returns at most 50, so split busy ranges in half
        d = search(lat, lng, d0.isoformat(), d1.isoformat())
        if not d: return
        if d.get("total_matches", 0) > 50 and d1 > d0:
            mid = d0 + (d1 - d0) // 2; window(lat, lng, d0, mid, out); window(lat, lng, mid + dt.timedelta(days=1), d1, out)
        else: out.extend(d.get("results") or [])
    start, end = dt.date.today(), dt.date.today() + dt.timedelta(days=90)
    added = 0
    for hub, (lat, lng) in coords.items():
        if hub not in hubs or hub == "virtual": continue
        found = []; window(lat, lng, start, end, found)
        kept = 0; tz = hub_tz(hub)
        for e in found:
            link = canon(e.get("registration_url"))
            if not e.get("title") or not e.get("start_time") or not re.match(r"https?://", link): continue
            if e.get("status") not in (None, "upcoming", "sold_out") or e.get("attendance_mode") == "online": continue
            date, st = to_local(e["start_time"], tz); ed, et = to_local(e["end_time"], tz) if e.get("end_time") else (None, None)
            if not date or date < TODAY: continue
            title = re.sub(r"\s+", " ", e["title"]).strip()
            if link in seen_l or (norm(title), date) in seen_t: continue
            v = e.get("venue") or {}; org = e.get("organizer") or {}
            venue = ", ".join(x for x in [v.get("name"), v.get("address")] if x and x.lower() not in ("online", "tba"))[:200]
            events.append({"title": title[:200], "hub": hub, "date": date, "start": st, "end": et if ed == date else None, "venue": venue,
                           "host": (org.get("name") or "")[:120], "link": link, "desc": "Details and registration on the event page.", "src": "techmeetups"})
            seen_l.add(link); seen_t.add((norm(title), date)); kept += 1
        if found: print(f"techmeetups {hub}: {len(found)} found, {kept} new"); REPORT.append({"source": "techmeetups.io", "hub": hub, "found": len(found), "added": kept})
        added += kept
    json.dump(events, open(f"{REPO}/list/events.json", "w"), ensure_ascii=False, indent=1)
    print(f"techmeetups: {added} new events, {calls[0]} API calls")
    return {}

# ---------- 1c. daily sources: Luma discover categories (list/data/sources.json) ----------
CITY_ALIAS = {"san francisco": "sf", "oakland": "sf", "berkeley": "sf", "palo alto": "sf", "mountain view": "sf", "san jose": "sf",
    "menlo park": "sf", "sunnyvale": "sf", "santa clara": "sf", "redwood city": "sf", "san mateo": "sf", "cupertino": "sf", "south san francisco": "sf",
    "new york": "nyc", "brooklyn": "nyc", "manhattan": "nyc", "queens": "nyc", "jersey city": "nyc", "hoboken": "nyc", "long island city": "nyc",
    "washington": "dc", "arlington": "dc", "abu dhabi": "dxb", "dubai": "dxb", "sao paulo": "sao", "rio de janeiro": "sao", "denver": "den",
    "boulder": "den", "cambridge|united states": "bos", "somerville": "bos", "santa monica": "la", "culver city": "la", "pasadena": "la",
    "venice": "la", "bangalore": "blr", "bengaluru": "blr", "mumbai": "bom", "navi mumbai": "bom", "tel aviv yafo": "tlv", "tel aviv": "tlv",
    "kowloon": "hkg", "shibuya": "tyo", "minato city": "tyo", "chiyoda city": "tyo", "shinjuku city": "tyo", "bellevue": "sea", "redmond": "sea",
    "kirkland": "sea", "vancouver|canada": "yvr", "burnaby": "yvr", "espoo": "hel", "london|united kingdom": "ldn", "ciudad de mexico": "mex", "mexico city": "mex",
    "delhi": "del", "gurugram": "del", "gurgaon": "del", "noida": "del", "raleigh": "rdu", "durham": "rdu", "chapel hill": "rdu", "cary": "rdu",
    "fort worth": "dal", "plano": "dal", "irving": "dal", "frisco": "dal", "sandton": "jnb", "makati": "mnl", "taguig": "mnl", "quezon city": "mnl",
    "thu duc": "sgn", "ho chi minh": "sgn", "lehi": "slc", "provo": "slc", "la jolla": "sdg", "cambridge|united kingdom": None}
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
    # a Luma city feed ("luma_place") mixes everything (run clubs, screenings...), so keep only events whose title reads startup/tech
    TECH = re.compile(r"\b(start-?ups?|founders?|co-?founders?|vcs?|venture|investors?|investing|angels?|pitch(es|ing)?|demo ?day|accelerator|incubator|"
        r"ai|genai|llms?|agents?|agentic|machine learning|ml|data|tech|technology|developers?|devs?|engineers?|engineering|hack(athon|night)s?|buildathon|"
        r"builders?|product|pms?|saas|fintech|crypto|web3|blockchain|defi|climate ?tech|healthtech|biotech|deep ?tech|robotics|quantum|cyber(security)?|cloud|"
        r"open[- ]source|coding|code|software|b2b|gtm|go-to-market|growth|operators?|entrepreneurs?|entrepreneurship|scale-?ups?|innovation|fundrais\w*|"
        r"api|devrel|ux|ui|design ?systems?|python|javascript|rust|kubernetes|openai|anthropic|nvidia|google|microsoft|aws)\b", re.I)
    NOT = re.compile(r"\b(dating|singles|speed ?dating|yoga|meditation|rave|comedy|stand-?up|karaoke|wine tasting|sound bath)\b", re.I)
    feeds = []
    for src in srcs:
        if src.get("type") == "luma_category":
            feeds.append((src["id"], f"category_api_id={src['id']}", None, int(src.get("max_pages", 60))))
        elif src.get("type") == "luma_place":
            for slug, hub_id in src.get("places", {}).items():
                try:
                    r = urlopen(Request(f"https://api.lu.ma/url?url={slug}", headers={**UA, "Accept": "application/json"}), timeout=20)
                    pid = ((json.loads(r.read().decode("utf-8", "ignore")).get("data") or {}).get("place") or {}).get("api_id")
                except Exception as ex: pid = None; print(f"place {slug}: lookup failed ({ex})")
                if pid: feeds.append((f"place:{slug}", f"discover_place_api_id={pid}", hub_id, int(src.get("max_pages", 20))))
                else: REPORT.append({"source": f"luma place {slug}", "hub": hub_id, "error": "place not found"})
                time.sleep(0.3)
    for name, qs, place_hub, max_pages in feeds:
        time.sleep(1.5)
        cursor, pages, kept, seen_n, retries, seen_cur = None, 0, 0, 0, 0, set()
        while pages < max_pages:
            q = f"https://api.lu.ma/discover/get-paginated-events?{qs}&pagination_limit=25" + (f"&pagination_cursor={cursor}" if cursor else "")
            try:
                r = urlopen(Request(q, headers={**UA, "Accept": "application/json"}), timeout=20); d = json.loads(r.read().decode("utf-8", "ignore"))
            except Exception as ex:
                code = getattr(ex, "code", 0)
                if code in (429, 403) and retries < 3: retries += 1; time.sleep(20 * retries); continue
                print(f"source {name}: stopped ({ex})"); break
            pages += 1
            if pages <= 2: print(f"  {name} page {pages}: {len(d.get('entries') or [])} entries, has_more={d.get('has_more')}, cursor={'yes' if d.get('next_cursor') else 'no'}")
            for en in d.get("entries") or []:
                e = en.get("event") or {}; g = e.get("geo_address_info") or {}
                if not e.get("name") or not e.get("start_at") or not e.get("url"): continue
                if e.get("location_type") == "online": continue          # in-person events only
                seen_n += 1
                if place_hub and (not TECH.search(e["name"]) or NOT.search(e["name"])): continue
                hub = city_hub(g.get("city"), g.get("country"), hubs) or place_hub
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
            if not d.get("entries") or not d.get("next_cursor") or d["next_cursor"] in seen_cur: break
            cursor = d["next_cursor"]; seen_cur.add(cursor); time.sleep(0.8)
        print(f"source {name}: {pages} pages, {seen_n} in-person events seen, {kept} new added")
        if place_hub: REPORT.append({"source": name, "hub": place_hub, "pages": pages, "seen": seen_n, "added": kept})
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
    for step in (import_pending, import_cities, import_links, import_submissions, import_sources, import_techmeetups):
        try: seed.update(step() or {})
        except Exception as ex: print(f"{step.__name__} failed: {ex}")
    try: fill_luma_descriptions()
    except Exception as ex: print(f"descriptions failed: {ex}")
    refresh_photos(seed)
    if REPORT: json.dump({"date": dt.date.today().isoformat(), "report": REPORT}, open(f"{REPO}/list/data/import-report.json", "w"), indent=1)
