#!/usr/bin/env python3
"""Ink and Bone Phase D rollout.

Applies the approved mark system to every personal repo working tree.
Does NOT touch git: branching, committing, pushing and PRs happen
separately so every change is reviewable before it lands anywhere.

Per repo:
  1. design/marks/            full export tree from marks/out plus pipeline
  2. design/github/           README banners and social preview, new palette
  3. README.md                badge hexes swapped
  4. design/tokens.json       values moved to Ink and Bone, keys unchanged
  5. design/BRAND.md          superseded notice pointing at the new system
  6. design/logo (and helios design/brand) same-named SVGs regenerated
  7. app code hex swaps       Theme.swift, web css and tsx, widget coffee
  8. Xcode catalogues         AppIcon pngs regenerated, AccentColor set
Profile repo: both banner SVGs rebuilt from the new marks.
"""

import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "out")

sys.path.insert(0, HERE)
import generate_marks as gm

IB_D = dict(page="#0B0C0D", card="#171614", raised="#201E1B", edge="#292826",
            edgeS="#3A3833", text="#F3F1EB", quiet="#8F8C85", copper="#B17E51",
            brass="#BFB287", mist="#CFDFE8", good="#4FC4A6", watch="#E0B93A",
            problem="#CB5B45")
IB_L = dict(page="#F5F5F3", card="#FFFFFF", raised="#EDEBE6", edge="#E2E0DA",
            edgeS="#CDCAC2", text="#1A1917", quiet="#5A5852", copper="#99612F",
            brass="#4D4323", mist="#2D647F", good="#307A64", watch="#695725",
            problem="#C73C20")

README_MAP = {"BD4753": "99612F", "E78892": "B17E51",
              "1B7A55": "4D4323", "7EE0B1": "BFB287",
              "0F7D74": "2D647F", "2FD4C4": "CFDFE8",
              "1C1B1D": "1A1917"}

UI_MAP_COMMON = {
    "#0B0D0C": IB_D["page"], "#151917": IB_D["card"], "#232826": IB_D["edge"],
    "#E8ECE9": IB_D["text"], "#9AA49E": IB_D["quiet"],
    "#7EE0B1": IB_D["brass"], "#1B7A55": IB_L["brass"],
    "#5F6B65": IB_L["quiet"], "#2FD4C4": IB_D["mist"], "#0F7D74": IB_L["mist"],
    "#BD4753": IB_L["copper"], "#E78892": IB_D["copper"],
    "#A33843": "#7D4F26", "#EFA9B0": "#C89A73",
    "#1C1B1D": IB_D["page"], "#F7F5F2": IB_D["text"],
    "#FCFBF8": IB_L["card"], "#F0ECE5": IB_L["raised"],
    "#28272A": IB_D["card"], "#211F23": IB_D["raised"],
    "#383638": IB_D["edge"], "#E3DDE1": IB_L["edge"],
    "#FBBF24": IB_D["watch"], "#E8B13B": IB_D["watch"], "#C28A0F": IB_L["watch"],
    "#367B23": IB_L["good"], "#A0D392": IB_D["good"],
}

PROJECTS = ["ledge", "content-digest-app", "helios", "zest", "switchdeck",
            "uebersicht-claude-tokens", "claude-bridge", "claude-burnrate",
            "claude-skills-workspace"]

LOG = []

def log(msg):
    LOG.append(msg)
    print(msg)

def swap_in_file(path, mapping, also_lower=True):
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        s = f.read()
    orig = s
    for old, new in mapping.items():
        s = s.replace(old, new)
        if also_lower:
            s = s.replace(old.lower(), new.lower())
    if s != orig:
        with open(path, "w", encoding="utf-8") as f:
            f.write(s)
        log("  swapped hexes: %s" % os.path.relpath(path, ROOT))
        return True
    return False

def copy_marks(project, repo_dir):
    src = os.path.join(OUT, project)
    dst = os.path.join(repo_dir, "design", "marks")
    shutil.copytree(src, dst, dirs_exist_ok=True)
    for f in ("generate_marks.py", "README.md"):
        shutil.copy(os.path.join(HERE, f), os.path.join(dst, f))
    for stale in ("contact-sheet.png",):
        p = os.path.join(dst, stale)
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
    log("  design/marks written (%s)" % project)

def write_banners(project, repo_dir, svg_names=None):
    gh = os.path.join(repo_dir, "design", "github")
    os.makedirs(gh, exist_ok=True)
    src = os.path.join(OUT, project, "web")
    for theme in ("dark", "light"):
        shutil.copy(os.path.join(src, "banner-%s-1400x400.png" % theme),
                    os.path.join(gh, "readme-banner-%s-1400x400.png" % theme))
        shutil.copy(os.path.join(src, "banner-%s-1400x400.svg" % theme),
                    os.path.join(gh, "readme-banner-%s-1400x400.svg" % theme))
        if svg_names:
            shutil.copy(os.path.join(src, "banner-%s-1400x400.svg" % theme),
                        os.path.join(gh, "readme-banner-%s.svg" % theme))
    shutil.copy(os.path.join(src, "social-preview-1280x640.png"),
                os.path.join(gh, "social-preview-1280x640.png"))
    log("  banners and social preview written")

def wordmark_text_svg(project, theme):
    disp = gm.MARKS[project].get("display", project)
    paths, tw = gm.text_paths(disp)
    ink = gm.PAL[theme]["ink"]
    pad = 20
    W, H = tw + 2 * pad, 68.8 + 22.4 + 2 * pad
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %.0f %.0f">'
            '<g fill="%s" transform="translate(%s,%.1f)">%s</g></svg>'
            % (W, H, ink, pad, pad + 68.8, "".join(paths)))

def regen_legacy_svgs(project, repo_dir):
    for folder in (os.path.join(repo_dir, "design", "logo"),
                   os.path.join(repo_dir, "design", "brand")):
        if not os.path.isdir(folder):
            continue
        for fn in os.listdir(folder):
            if not fn.endswith(".svg"):
                continue
            path = os.path.join(folder, fn)
            low = fn.lower()
            dark = "dark" in low and "light" not in low
            theme = "dark" if dark else "light"
            new = None
            if "lockup" in low and "mono" in low:
                layout = "stacked" if "stacked" in low else "horizontal"
                theme_m = "dark" if "white" in low else "light"
                new, _, _ = gm.wordmark_svg(project, theme_m, layout)
                tgt = "#FFFFFF" if "white" in low else "#000000"
                for c in list(gm.PAL[theme_m].values()):
                    new = new.replace('"%s"' % c, '"%s"' % tgt)
            elif "mono-black" in low:
                new = gm.mark_svg(project, "master", "dark", mono="#000000")
            elif "mono-white" in low:
                new = gm.mark_svg(project, "master", "dark", mono="#FFFFFF")
            elif "tile" in low:
                new = gm.mark_svg(project, "master", theme,
                                  ground=gm.PAL[theme]["page"])
            elif "symbol" in low:
                new = gm.mark_svg(project, "master", theme)
            elif "lockup" in low:
                layout = "stacked" if "stacked" in low else "horizontal"
                new, _, _ = gm.wordmark_svg(project, theme, layout)
            elif "wordmark" in low:
                new = wordmark_text_svg(project, theme)
            if new:
                with open(path, "w") as f:
                    f.write(new)
                log("  regenerated %s" % os.path.relpath(path, ROOT))
    fav = os.path.join(repo_dir, "design", "web", "favicon.svg")
    if os.path.exists(fav):
        with open(fav, "w") as f:
            f.write(gm.favicon_svg(project))
        log("  regenerated design/web/favicon.svg")

def regen_named_pngs(project, repo_dir):
    from PIL import Image
    for sub in ("menubar", "app-icons", os.path.join("logo",)):
        folder = os.path.join(repo_dir, "design", sub)
        if not os.path.isdir(folder):
            continue
        for fn in os.listdir(folder):
            if not fn.endswith(".png"):
                continue
            path = os.path.join(folder, fn)
            with Image.open(path) as im:
                w, h = im.size
            if "template" in fn.lower():
                gm.mono_mark_png(project, max(w, h)).resize((w, h)).save(path)
            else:
                img = gm.png_bytes_to_img(
                    gm.svg_to_png(gm.tile_svg(project, max(w, h)), max(w, h)))
                img.resize((w, h)).convert("RGBA").save(path)
            log("  regenerated %s" % os.path.relpath(path, ROOT))

def update_xcassets(project, repo_dir):
    from PIL import Image
    for base, dirs, filesv in os.walk(repo_dir):
        if ".git" in base or "design" + os.sep + "marks" in base:
            continue
        if base.endswith("AppIcon.appiconset"):
            cj = os.path.join(base, "Contents.json")
            if not os.path.exists(cj):
                continue
            with open(cj) as f:
                data = json.load(f)
            for imgrec in data.get("images", []):
                fn = imgrec.get("filename")
                size = imgrec.get("size")
                scale = imgrec.get("scale", "1x")
                if not fn or not size:
                    continue
                pt = float(size.split("x")[0])
                px = int(round(pt * int(scale[0])))
                sq = px >= 1024
                img = gm.png_bytes_to_img(
                    gm.svg_to_png(gm.tile_svg(project, px, square=sq), px))
                if sq:
                    img = img.convert("RGB")
                img.save(os.path.join(base, fn))
            log("  appicon regenerated: %s" % os.path.relpath(base, ROOT))
        if base.endswith("AccentColor.colorset"):
            cj = os.path.join(base, "Contents.json")
            cat = gm.MARKS[project]["cat"]
            if cat == "ink":
                continue
            def comps(hexv):
                return {"red": "0x%s" % hexv[1:3], "green": "0x%s" % hexv[3:5],
                        "blue": "0x%s" % hexv[5:7], "alpha": "1.000"}
            light = IB_L[cat]
            dark = IB_D[cat]
            data = {"colors": [
                {"color": {"color-space": "srgb", "components": comps(light)},
                 "idiom": "universal"},
                {"appearances": [{"appearance": "luminosity", "value": "dark"}],
                 "color": {"color-space": "srgb", "components": comps(dark)},
                 "idiom": "universal"}],
                "info": {"author": "rollout.py", "version": 1}}
            with open(cj, "w") as f:
                json.dump(data, f, indent=2)
            log("  accentcolor set: %s" % os.path.relpath(base, ROOT))

def brand_md_notice(project, repo_dir):
    path = os.path.join(repo_dir, "design", "BRAND.md")
    if not os.path.exists(path):
        return
    disp = gm.MARKS[project].get("display", project)
    cat = gm.MARKS[project]["cat"]
    catline = {"copper": "Copper #B17E51 dark, #99612F light and badges: capture and keep.",
               "brass": "Brass #BFB287 dark, #4D4323 light and badges: read a signal against a baseline.",
               "mist": "Mist #CFDFE8 dark, #2D647F light and badges: Claude and AI tooling.",
               "ink": "Ink only. No accent, by decision."}[cat]
    with open(path, "w") as f:
        f.write("""# %s brand: Ink and Bone

This repo follows the shared personal system, Ink and Bone v1.0.0.
The canonical definition lives in the profile repo:
`ShashankKarpal/shashankkarpal` under `design/brand/` (tokens, rules,
accessibility report) and `design/marks/` (mark geometry and the
export pipeline).

Category: %s

The mark identifies the project, the colour identifies the group.
One accent per mark. Status colours never double as category colours.
Grain is the only texture. No italics, no underlines, no emoji, no
em dashes.

Everything in `design/marks/` here is generated by
`design/marks/generate_marks.py`. Do not hand-edit exports; change the
geometry or palette at the source and regenerate.

The pre-2026-08 system this file used to describe is retired.
""" % (disp, catline))
    log("  BRAND.md rewritten")

def tokens_json_update(project, repo_dir):
    path = os.path.join(repo_dir, "design", "tokens.json")
    if not os.path.exists(path):
        return
    swap_in_file(path, UI_MAP_COMMON)
    with open(path) as f:
        s = f.read()
    s = re.sub(r'"version":\s*"[^"]*"', '"version": "2.0 (Ink and Bone)"', s, count=1)
    with open(path, "w") as f:
        f.write(s)

def do_repo(project):
    repo_dir = os.path.join(ROOT, project)
    if not os.path.isdir(repo_dir):
        log("MISSING repo dir: %s" % project)
        return
    log("== %s" % project)
    copy_marks(project, repo_dir)
    priv = gm.MARKS[project]["private"]
    if not priv or project in ("claude-bridge", "claude-burnrate",
                               "claude-skills-workspace"):
        write_banners(project, repo_dir,
                      svg_names=(project == "uebersicht-claude-tokens"))
    swap_in_file(os.path.join(repo_dir, "README.md"), README_MAP)
    tokens_json_update(project, repo_dir)
    brand_md_notice(project, repo_dir)
    regen_legacy_svgs(project, repo_dir)
    regen_named_pngs(project, repo_dir)
    if project == "ledge":
        for p in ("apps/ios/Sources/Theme.swift", "apps/mac/Sources/Theme.swift",
                  "docs/spec.md"):
            swap_in_file(os.path.join(repo_dir, p), UI_MAP_COMMON)
        update_xcassets(project, repo_dir)
    if project == "helios":
        for base, dirs, filesv in os.walk(os.path.join(repo_dir, "web", "src")):
            for fn in filesv:
                if fn.endswith((".css", ".tsx", ".ts")):
                    swap_in_file(os.path.join(base, fn), UI_MAP_COMMON)
        for p in ("spec/architecture-and-spec.md", "HANDOFF.md", "design/BRAND.md"):
            swap_in_file(os.path.join(repo_dir, p), UI_MAP_COMMON)
    if project == "uebersicht-claude-tokens":
        swap_in_file(os.path.join(repo_dir, "claude-tokens.widget", "index.coffee"),
                     UI_MAP_COMMON)
        rd = os.path.join(repo_dir, "README.md")
        with open(rd) as f:
            s = f.read()
        s = s.replace("<h1 align=\"center\">uebersicht-claude-tokens</h1>",
                      "<h1 align=\"center\">claude-tokens</h1>")
        with open(rd, "w") as f:
            f.write(s)
    if project in ("zest", "switchdeck", "content-digest-app"):
        swap_in_file(os.path.join(repo_dir, "knowledge.html"), UI_MAP_COMMON)

def profile_banner(theme):
    p = gm.PAL[theme]
    order = ["ledge", "content-digest-app", "helios", "zest", "switchdeck",
             "uebersicht-claude-tokens"]
    W, H = 1400, 400
    parts = ['<rect width="%s" height="%s" fill="%s"/>' % (W, H, p["page"])]
    parts.append('<defs>%s</defs>' % (gm.GRAIN_FILTER % gm.GRAIN[theme]))
    parts.append('<rect width="%s" height="%s" fill="%s" filter="url(#gr)" '
                 'opacity="%s"/>' % (W, H, p["ink"], gm.GRAIN[theme]))
    cell = W / 6.0
    mark_h = 110
    for i, proj in enumerate(order):
        m = gm.MARKS[proj]
        cx = cell * (i + 0.5)
        mark = "".join(gm.el_svg(e, theme, m["cat"]) for e in m["master"])
        parts.append('<g transform="translate(%.1f,95) scale(%.4f)">%s</g>'
                     % (cx - mark_h / 2, mark_h / 96.0, mark))
        disp = m.get("display", proj)
        paths, tw = gm.text_paths(disp)
        ts = min(0.33, (cell - 24) / tw)
        parts.append('<g fill="%s" transform="translate(%.1f,%.1f) scale(%.4f)">%s</g>'
                     % (p["ink"], cx - tw * ts / 2, 285, ts, "".join(paths)))
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" '
            'width="%s" height="%s" role="img" '
            'aria-label="Six project marks with names">%s</svg>'
            % (W, H, W, H, "".join(parts)))

def do_profile():
    repo_dir = os.path.join(ROOT, "shashankkarpal")
    gh = os.path.join(repo_dir, "design", "github")
    log("== shashankkarpal (profile)")
    for theme in ("dark", "light"):
        path = os.path.join(gh, "profile-banner-%s.svg" % theme)
        with open(path, "w") as f:
            f.write(profile_banner(theme))
        log("  rebuilt %s" % os.path.relpath(path, ROOT))
    swap_in_file(os.path.join(repo_dir, "README.md"), README_MAP)

def main():
    targets = sys.argv[1:] or PROJECTS + ["profile"]
    for t in targets:
        if t == "profile":
            do_profile()
        else:
            do_repo(t)
    with open(os.path.join(HERE, "rollout-log.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")

if __name__ == "__main__":
    main()
