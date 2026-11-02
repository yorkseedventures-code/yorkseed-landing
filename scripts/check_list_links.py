"""Report-only link check for upcoming events in list/events.json and list/data/master.json.
Flags links that return 404/410 or fail to connect. Never edits data. Writes link-report.md."""
import json, datetime, concurrent.futures as cf, urllib.request, urllib.error
today = datetime.date.today().isoformat()
evs = []
for f in ("list/events.json", "list/data/master.json"):
    d = json.load(open(f)); evs += d if isinstance(d, list) else d.get("events", [])
up = [e for e in evs if (e.get("date") or "") >= today and (e.get("link") or "").startswith("http")]
def chk(e):
    for m in ("HEAD", "GET"):
        try:
            r = urllib.request.urlopen(urllib.request.Request(e["link"], method=m, headers={"User-Agent": "Mozilla/5.0 YorkseedLinkCheck"}), timeout=15)
            return e, r.status
        except urllib.error.HTTPError as x:
            if x.code in (404, 410): return e, x.code
            if m == "GET": return e, x.code   # 403/429 etc: bot-blocked, not proof of a dead link
        except Exception as x:
            if m == "GET": return e, "ERR " + type(x).__name__
    return e, None
with cf.ThreadPoolExecutor(12) as ex: res = list(ex.map(chk, up))
dead = [(e, s) for e, s in res if s in (404, 410) or str(s).startswith("ERR")]
out = [f"# Link check {today}", f"Checked {len(up)} upcoming events; {len(dead)} look dead (404/410/connection error).", ""]
out += [f"- {e['date']} | {e.get('hub')} | {e['title']} | {s} | {e['link']}" for e, s in sorted(dead, key=lambda t: t[0]['date'])]
open("link-report.md", "w").write("\n".join(out)); print("\n".join(out[:40]))
