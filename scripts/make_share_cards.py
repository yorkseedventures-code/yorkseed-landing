"""Make the WhatsApp/LinkedIn link-preview cards for each conference week's share link.

Run locally after scripts/build_list_pages.py (it writes list/data/share-weeks.json):
    pip install pillow
    python3 scripts/build_list_pages.py && python3 scripts/make_share_cards.py
Writes list/img/og-share-<hash>.jpg (1200x630). Weeks with a hand-made card (WEEK_OG) are skipped.
Set a number by hand with: python3 scripts/make_share_cards.py slush-helsinki=200 (kept in list/data/share-card-counts.json; the real count wins once it is higher).
Rerun when a week's count passes the next 10 so the "N+" on the card stays true.
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(REPO, "scripts", "fonts")
W, H = 1200, 630
BG, RED, INK, SUB = "#F5F1EA", "#B3261E", "#1A1714", "#3a3530"
DISPLAY = {"wef-davos": "WEF Davos", "aws-re-invent": "AWS re:Invent", "deeptech-week-tlv": "DeepTech Week TLV",
           "ces": "CES", "jpm-healthcare-week": "JPM Healthcare Week", "gitex-and-expand-north-star": "GITEX & Expand North Star"}
MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

def font(name, size): return ImageFont.truetype(os.path.join(FONTS, name), size)

def dates(a, b):
    ya, ma, da = map(int, a.split("-")); yb, mb, db = map(int, b.split("-"))
    return f"{MON[ma-1]} {da} to {db}" if ma == mb else f"{MON[ma-1]} {da} to {MON[mb-1]} {db}"

def wrap(d, words, f, maxw):
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if cur and d.textlength(t, font=f) > maxw: lines.append(cur); cur = w
        else: cur = t
    return lines + [cur]

def card(x, out):
    img = Image.new("RGB", (W, H), BG)
    photo = x.get("photo") and os.path.join(REPO, x["photo"].lstrip("/"))
    textw = 1056
    if photo and os.path.exists(photo):
        p = Image.open(photo).convert("RGB")
        pw, ph = 480, H
        s = max(pw / p.width, ph / p.height); p = p.resize((int(p.width * s) + 1, int(p.height * s) + 1))
        l, t = (p.width - pw) // 2, (p.height - ph) // 2
        img.paste(p.crop((l, t, l + pw, t + ph)), (W - pw, 0))
        g = Image.new("L", (140, H)); gd = ImageDraw.Draw(g)
        for i in range(140): gd.line([(i, 0), (i, H)], fill=int(255 * (1 - i / 139)))
        img.paste(Image.new("RGB", (140, H), BG), (W - pw, 0), g)
        textw = W - pw - 72 - 20
    d = ImageDraw.Draw(img)

    def spaced(x0, y, t, f, fill, sp):
        for ch in t: d.text((x0, y), ch, font=f, fill=fill); x0 += d.textlength(ch, font=f) + sp
        return x0

    spaced(72, 62, f"THE YORKSEED LIST  ·  {x['city'].upper()} {x['year']}", font("Inter-SemiBold.otf", 20), RED, 4)
    n = x["n"]; num = f"{n // 10 * 10}+ " if n >= 20 else ""
    name = DISPLAY.get(x["hash"], x["name"])
    sub = font("playfair-display-latin-400-normal.woff", 27)
    long_sub = f"Every party, dinner, investor lunch and founder meetup, {dates(x['start'], x['end'])}. Updated daily."
    subl = wrap(d, long_sub.split(), sub, textw)
    if len(subl) > 1: subl = wrap(d, f"{dates(x['start'], x['end'])}. Parties, dinners, founder meetups. Updated daily.".split(), sub, textw)
    if len(subl) > 1: subl = [f"{dates(x['start'], x['end'])}. Updated daily."]
    for size in (86, 78, 70, 62, 56, 50):
        big, bigi = font("playfair-display-latin-400-normal.woff", size), font("playfair-display-latin-400-italic.woff", size)
        lh = int(size * 1.12); lines = wrap(d, (num + name).split(), big, textw)
        if len(lines) <= 3 and 112 + (len(lines) + 1) * lh + 12 + len(subl) * 37 <= 438: break
    y = 112
    for ln in lines: d.text((70, y), ln, font=big, fill=INK); y += lh
    d.text((70, y - 8), "side events.", font=bigi, fill=RED); y += lh + 12
    for ln in subl: d.text((72, y), ln, font=sub, fill=SUB); y += 37
    b = font("Inter-Bold.otf", 17)

    def chip(x0, y0, t, bg):
        tw = sum(d.textlength(c, font=b) + 3 for c in t)
        d.rectangle([x0, y0, x0 + tw + 36, y0 + 44], fill=bg); spaced(x0 + 18, y0 + 13, t, b, BG, 3); return x0 + tw + 46
    x0 = chip(72, 450, "FREE TO BROWSE", INK); chip(x0, 450, "FREE TO ADD", INK); chip(72, 504, "FEATURE YOUR EVENT", RED)
    spaced(74, 575, f"LIST.YORKSEED.CO/{x['camel'].upper()}", font("Inter-SemiBold.otf", 18), INK, 3.5)
    img.save(out, quality=88)

if __name__ == "__main__":
    weeks = json.load(open(os.path.join(REPO, "list", "data", "share-weeks.json")))
    # args: optional week hashes to redo, and/or hash=N to put a set number on a card (e.g. slush-helsinki=200)
    only, fixed = set(), {}
    for a in sys.argv[1:]:
        if "=" in a: k, v = a.split("=", 1); fixed[k] = int(v); only.add(k)
        else: only.add(a)
    saved = os.path.join(REPO, "list", "data", "share-card-counts.json")
    try: fixed = {**json.load(open(saved)), **fixed}
    except Exception: pass
    json.dump(fixed, open(saved, "w"), indent=1)
    for x in weeks:
        if x["hash"] in fixed: x["n"] = max(x["n"], fixed[x["hash"]])
        if x.get("custom") or (only and x["hash"] not in only): continue
        out = os.path.join(REPO, "list", "img", f"og-share-{x['hash']}.jpg")
        card(x, out); print("wrote", out)
