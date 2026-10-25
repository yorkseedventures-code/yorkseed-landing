"""Quick one-off: upcoming events from the given Meetup groups' public iCal feeds -> list/data/meetup-import.json.
Usage: python3 scripts/import_meetup_quick.py group:hub [group:hub ...]   (or --hub par to take every group mapped to that city)"""
import sys, json, re, time, datetime as dt, importlib.util
from zoneinfo import ZoneInfo
spec = importlib.util.spec_from_file_location("le", __file__.replace("import_meetup_quick.py", "list_enrich.py"))
le = importlib.util.module_from_spec(spec); ARGS = sys.argv[1:]; sys.argv = sys.argv[:1]; spec.loader.exec_module(le)
groups = le.load(f"{le.REPO}/list/data/meetup-groups.json", {})
pairs = ([(g, h) for g, h in groups.items() if h == ARGS[1]] if ARGS[:1] == ["--hub"] else
         [tuple(a.split(":")) for a in open(ARGS[1]).read().split()] if ARGS[:1] == ["--file"] else [tuple(a.split(":")) for a in ARGS])
out = []; horizon = (dt.date.today() + dt.timedelta(days=120)).isoformat()
for g, hub in pairs:
    try: text = le.urlopen(le.Request(f"https://www.meetup.com/{g}/events/ical/", headers=le.UA), timeout=20).read().decode("utf-8", "ignore")
    except Exception as ex: print(g, ex); continue
    n = 0
    for f in sorted(le._ics_events(text), key=lambda f: (f.get("DTSTART") or ("", ""))[0]):
        if n >= 4: break
        title = (f.get("SUMMARY") or ("", ""))[0]; url = (f.get("URL") or ("", ""))[0].split("?")[0].rstrip("/")
        loc = (f.get("LOCATION") or ("", ""))[0]; ds, params = f.get("DTSTART") or ("", "")
        if not title or not url or not ds or not le.TECH.search(title) or le.NOT.search(title) or re.search(r"\bonline\b|virtual|zoom", loc + " " + title, re.I): continue
        try:
            src_tz = re.search(r"TZID=([^;:]+)", params).group(1) if "TZID=" in params else "UTC"
            d = dt.datetime.strptime(ds.rstrip("Z")[:15], "%Y%m%dT%H%M%S").replace(tzinfo=ZoneInfo(src_tz)).astimezone(ZoneInfo(le.hub_tz(hub)))
        except Exception: continue
        date = d.date().isoformat()
        if date < le.TODAY or date > horizon: continue
        out.append({"title": title[:200], "hub": hub, "date": date, "start": d.strftime("%H:%M"), "venue": loc[:200],
                    "host": g.replace("-", " ").title(), "link": url + "/", "desc": "Details and registration on the event page.", "src": "meetup"}); n += 1
    print(g, n); time.sleep(0.8)
json.dump(out, open(f"{le.REPO}/list/data/meetup-import.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "events")
