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
SKIP_HOSTS = re.compile(r'(foundercal\.com|google\.[a-z.]+|goo\.gl|maps\.|facebook\.com|instagram\.com|twitter\.com|x\.com|linkedin\.com|tiktok\.com|youtube\.com|apple\.com|play\.google)', re.I)

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
    if not pend: return []
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

# ---------- 2. real event photos ----------
def fetch_photo(link):
    try:
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
    week_ago = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    todo = [l for l in links if l not in cache or (not cache[l].get("img") and cache[l].get("t", "") < week_ago)][:500]
    with ThreadPoolExecutor(16) as ex:
        for link, img in ex.map(fetch_photo, todo): cache[link] = {"img": img or None, "t": TODAY}
    cache = {k: v for k, v in cache.items() if k in links}
    json.dump(cache, open(ph_p, "w"), ensure_ascii=False, indent=0)
    print(f"photos: {sum(1 for v in cache.values() if v.get('img'))} of {len(cache)} events have a real photo ({len(todo)} checked)")

if __name__ == "__main__":
    refresh_photos(import_pending())
