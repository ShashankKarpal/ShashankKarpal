#!/usr/bin/env python3
"""Verify the Ink and Bone palette: WCAG AA contrast plus colour blindness separation.
Standalone, no dependencies. Run: python3 verify-palette.py [-v]
Exits 1 if any required check fails."""
import math, sys, itertools

DARK = {
 "page":"#0B0C0D","card":"#171614","raised":"#201E1B","edge":"#292826","edge_strong":"#3A3833",
 "text":"#F3F1EB","quiet":"#8F8C85",
 "copper":"#B17E51","brass":"#BFB287","mist":"#CFDFE8",
 "good":"#4FC4A6","watch":"#E0B93A","problem":"#CB5B45","info":"#4681D0","neutral":"#7F8B85"}
LIGHT = {
 "page":"#F5F5F3","card":"#FFFFFF","raised":"#EDEBE6","edge":"#E2E0DA","edge_strong":"#CDCAC2",
 "text":"#1A1917","quiet":"#5A5852",
 "copper":"#99612F","brass":"#4D4323","mist":"#2D647F",
 "good":"#307A64","watch":"#695725","problem":"#C73C20","info":"#3A659D","neutral":"#3B413E"}
CATEGORY = ["copper","brass","mist"]
STATUS   = ["good","watch","problem","info","neutral"]
FOREGROUND = ["text","quiet"] + CATEGORY + STATUS

MIN_TEXT_ON_PAGE = 4.5      # AA body text
MIN_LABEL_ON_FILL = 4.5     # label sitting on a colour fill
MIN_CATEGORY_CVD = 25.0     # category colours must stay plainly different
MIN_STATUS_CVD = 15.0       # status colours, backed up by a word
MIN_GOOD_PROBLEM_CVD = 30.0 # the pair that must never merge

def hex2rgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i+2],16) for i in (0,2,4))
def rgb2hex(r):
    return "#%02X%02X%02X" % tuple(max(0,min(255,int(round(c)))) for c in r)
def lin(c):
    c /= 255.0
    return c/12.92 if c <= 0.04045 else ((c+0.055)/1.055)**2.4
def delin(c):
    c = max(0.0,min(1.0,c))
    return 12.92*c if c <= 0.0031308 else 1.055*c**(1/2.4)-0.055
def relL(h):
    r,g,b = [lin(x) for x in hex2rgb(h)]
    return 0.2126*r + 0.7152*g + 0.0722*b
def contrast(a,b):
    la,lb = relL(a),relL(b); hi,lo = max(la,lb),min(la,lb)
    return (hi+0.05)/(lo+0.05)

M_RGB_LMS = [[0.31399022,0.63951294,0.04649755],
             [0.15537241,0.75789446,0.08670142],
             [0.01775239,0.10944209,0.87256922]]
M_LMS_RGB = [[ 5.47221206,-4.64196010, 0.16963708],
             [-1.12524190, 2.29317094,-0.16789520],
             [ 0.02980165,-0.19318073, 1.16364789]]
def mul(M,v): return [sum(M[i][j]*v[j] for j in range(3)) for i in range(3)]
def simulate(h,kind):
    rgb = [lin(x) for x in hex2rgb(h)]
    l,m,s = mul(M_RGB_LMS,rgb)
    if kind == "deuteranopia": lms = [l, 0.494207*l + 1.24827*s, s]
    elif kind == "protanopia": lms = [2.02344*m - 2.52581*s, m, s]
    elif kind == "tritanopia": lms = [l, m, -0.395913*l + 0.801109*m]
    else: lms = [l,m,s]
    return rgb2hex([delin(c)*255 for c in mul(M_LMS_RGB,lms)])
def rgb2lab(h):
    r,g,b = [lin(x) for x in hex2rgb(h)]
    X = r*0.4124564 + g*0.3575761 + b*0.1804375
    Y = r*0.2126729 + g*0.7151522 + b*0.0721750
    Z = r*0.0193339 + g*0.1191920 + b*0.9503041
    def f(t): return t**(1/3) if t > 0.008856 else 7.787*t + 16/116
    fx,fy,fz = f(X/0.95047), f(Y/1.0), f(Z/1.08883)
    return (116*fy-16, 500*(fx-fy), 200*(fy-fz))
def de76(a,b):
    la,lb = rgb2lab(a),rgb2lab(b)
    return math.sqrt(sum((la[i]-lb[i])**2 for i in range(3)))

verbose = "-v" in sys.argv
fails = []
for tname, T in (("dark",DARK),("light",LIGHT)):
    label_on_fill = T["page"] if tname == "dark" else "#FFFFFF"
    print("=" * 62); print(tname.upper(), "theme")
    print("-- text on page (AA 4.5) --")
    for k in FOREGROUND:
        c = contrast(T[k], T["page"])
        ok = c >= MIN_TEXT_ON_PAGE
        print(f"   {k:8s} {T[k]}  {c:5.2f}  {'ok' if ok else 'FAIL'}")
        if not ok: fails.append(f"{tname}: {k} on page {c:.2f}")
    print(f"-- label {label_on_fill} on fills (AA 4.5) --")
    for k in CATEGORY + STATUS:
        c = contrast(T[k], label_on_fill)
        ok = c >= MIN_LABEL_ON_FILL
        print(f"   {k:8s} {T[k]}  {c:5.2f}  {'ok' if ok else 'FAIL'}")
        if not ok: fails.append(f"{tname}: label on {k} {c:.2f}")
    for kind in ("deuteranopia","protanopia","tritanopia"):
        req_cat = MIN_CATEGORY_CVD if kind != "tritanopia" else 20.0
        req_st  = MIN_STATUS_CVD  if kind != "tritanopia" else 4.0
        sims = {k: simulate(T[k],kind) for k in CATEGORY + STATUS}
        print(f"-- {kind} --")
        for a,b in itertools.combinations(CATEGORY,2):
            d = de76(sims[a],sims[b]); ok = d >= req_cat
            print(f"   category {a}/{b}: {d:5.1f}  {'ok' if ok else 'FAIL'}")
            if not ok: fails.append(f"{tname}/{kind}: category {a}/{b} {d:.1f}")
        wst = min(de76(sims[a],sims[b]) for a,b in itertools.combinations(STATUS,2))
        gp  = de76(sims["good"],sims["problem"])
        print(f"   status worst pair: {wst:5.1f}  {'ok' if wst >= req_st else 'FAIL'}")
        print(f"   good/problem:      {gp:5.1f}  {'ok' if gp >= MIN_GOOD_PROBLEM_CVD else 'FAIL'}")
        if wst < req_st: fails.append(f"{tname}/{kind}: status worst {wst:.1f}")
        if gp < MIN_GOOD_PROBLEM_CVD: fails.append(f"{tname}/{kind}: good/problem {gp:.1f}")
        if verbose:
            cross = sorted(((f"{a}/{b}", de76(sims[a],sims[b])) for a in CATEGORY for b in STATUS), key=lambda x: x[1])
            print("   known cross collisions (safe by the slot rule): " +
                  "  ".join(f"{n} {d:.1f}" for n,d in cross[:3]))
print("=" * 62)
if fails:
    print("FAILED", len(fails), "checks:"); [print("  -", f) for f in fails]; sys.exit(1)
print("All required checks pass.")
print("Cross collisions between a category colour and a status colour are expected and are")
print("resolved structurally: category on the rail or mark, status in a chip that carries a word.")
