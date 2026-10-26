#!/usr/bin/env python3
"""Turn a JSON idea tree into Canvas Composer SVG for a Miro mind map.

Usage: mindmap_svg.py tree.json > map.svg

tree.json: {"title": "...", "root": "...", "branches": [
              {"label": "...", "children": [{"label": "...", "children": [{"label": "..."}]}]}]}
Optional top-level keys: "families" (ordered list of colour families), "origin" ([x, y]).
"""
import json
import sys
from xml.sax.saxutils import escape

FAMILIES = {
    "blue": ("#f0f5fd", "#c6dcff", "#659df2", "#305bab"),
    "purple": ("#f4f2fd", "#dedaff", "#8f7fee", "#6631d7"),
    "orange": ("#fff5ed", "#f8d3af", "#fe9f4d", "#9b4a08"),
    "green": ("#eaf9ef", "#adf0c7", "#2dc75c", "#067429"),
    "yellow": ("#fffbed", "#fff6b6", "#ffdc4a", "#af7e04"),
    "red": ("#fff0f0", "#ffc6c6", "#ff6464", "#bd0a0a"),
}
DEFAULT_ORDER = ["blue", "purple", "orange", "green", "yellow", "red"]
INK, BODY = "#1a1a1a", "#595959"

# level: (min width, height, font size, bold, corner radius, sibling gap, gap to parent)
LEVELS = {
    1: (280, 72, 22, True, 36, 64, 160),
    2: (240, 56, 18, False, 28, 32, 64),
    3: (200, 48, 13, False, 24, 10, 64),
}
ROOT_W, ROOT_H, ROOT_FONT = 360, 120, 33
PAD_X = 64  # horizontal text padding inside a node
GLYPH = 0.62  # average glyph width / font size for Noto Sans


def leaves(n):
    kids = n.get("children", [])
    return sum(leaves(k) for k in kids) if kids else 1


def level_widths(branches):
    widths = {lv: LEVELS[lv][0] for lv in LEVELS}

    def walk(nodes, lv):
        if lv > 3:
            return
        for n in nodes:
            need = int(len(n["label"]) * LEVELS[lv][2] * GLYPH) + PAD_X
            widths[lv] = max(widths[lv], -(-need // 20) * 20)  # round up to 20
            walk(n.get("children", []), lv + 1)

    walk(branches, 1)
    return widths


def span(n, lv):
    h = LEVELS[lv][1]
    kids = n.get("children", []) if lv < 3 else []
    if not kids:
        return h
    gap = LEVELS[lv + 1][5]
    return max(h, sum(span(k, lv + 1) for k in kids) + gap * (len(kids) - 1))


def split(branches):
    total = sum(leaves(b) for b in branches)
    right, acc = [], 0
    for b in branches:
        if acc < total / 2 or not right:
            right.append(b)
            acc += leaves(b)
    return right, branches[len(right):]


def main(path):
    tree = json.load(open(path, encoding="utf-8"))
    branches = tree["branches"]
    order = tree.get("families", DEFAULT_ORDER)
    widths = level_widths(branches)
    out, links, counter = [], [], [0]

    def nid():
        counter[0] += 1
        return f"n{counter[0]}"

    def node(i, x, y, w, h, fill, stroke, text, label, size, bold, rx, sw=2):
        weight = ' data-font-weight="bold"' if bold else ""
        out.append(
            f'<rect id="{i}" x="{int(x)}" y="{int(y)}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}" data-content="{escape(label)}" '
            f'data-text-color="{text}" data-font-size="{size}" data-font-family="noto_sans"{weight}/>'
        )

    def link(a, b, side, color, sw, pt1, pt2):
        s, e = ("right", "left") if side > 0 else ("left", "right")
        links.append(
            f'<line x1="{int(pt1[0])}" y1="{int(pt1[1])}" x2="{int(pt2[0])}" y2="{int(pt2[1])}" stroke="{color}" '
            f'stroke-width="{sw}" data-shape="elbowed" data-start="{a}" data-end="{b}" '
            f'data-start-side="{s}" data-end-side="{e}"/>'
        )

    def place(n, lv, side, edge_x, top, parent, fam, parent_pt):
        faint, light, medium, dark = FAMILIES[fam]
        w, h, size, bold, rx, _, _ = LEVELS[lv]
        w = widths[lv]
        sp = span(n, lv)
        cy = top + sp / 2
        x = edge_x if side > 0 else edge_x - w
        fill, text = {1: (medium, INK), 2: (light, dark), 3: (faint, dark)}[lv]
        i = nid()
        node(i, x, round(cy - h / 2), w, h, fill, dark, text, n["label"], size, bold, rx)
        near = (x if side > 0 else x + w, round(cy))
        link(parent, i, side, medium, 3 if lv == 1 else 2, parent_pt, near)
        kids = n.get("children", []) if lv < 3 else []
        if kids:
            gap = LEVELS[lv + 1][5]
            total = sum(span(k, lv + 1) for k in kids) + gap * (len(kids) - 1)
            t = cy - total / 2
            far = (x + w if side > 0 else x)
            child_edge = far + LEVELS[lv + 1][6] * side
            for k in kids:
                place(k, lv + 1, side, child_edge, t, i, fam, (far, round(cy)))
                t += span(k, lv + 1) + gap

    right, left = split(branches)
    fam_of = {id(b): order[i % len(order)] for i, b in enumerate(branches)}

    def stack(bs):
        return sum(span(b, 1) for b in bs) + LEVELS[1][5] * max(len(bs) - 1, 0)

    root_id = "root"
    out.append("")  # placeholder for root, filled after bounds are known
    for side, bs in ((1, right), (-1, left)):
        if not bs:
            continue
        t = -stack(bs) / 2
        edge = ROOT_W / 2 + LEVELS[1][6]
        for b in bs:
            place(b, 1, side, edge * side, t, root_id, fam_of[id(b)],
                  (round(ROOT_W / 2 * side), 0))
            t += span(b, 1) + LEVELS[1][5]
    out[0] = (
        f'<rect id="root" x="{-ROOT_W // 2}" y="{-ROOT_H // 2}" width="{ROOT_W}" height="{ROOT_H}" rx="62" '
        f'fill="#ffffff" stroke="{INK}" stroke-width="3" data-content="{escape(tree["root"])}" '
        f'data-text-color="{INK}" data-font-size="{ROOT_FONT}" data-font-weight="bold" data-font-family="noto_sans"/>'
    )
    top_y = -max(stack(right), stack(left)) / 2
    title = (
        f'<textArea id="title" x="{-ROOT_W // 2}" y="{round(top_y - 64 - 48)}" width="900" font-size="33" '
        f'font-weight="bold" font-family="noto_sans" fill="{INK}">{escape(tree["title"])}</textArea>'
    )
    ox, oy = tree.get("origin", [0, 0])
    body = "\n  ".join([title] + out + links)
    sys.stdout.write(f'<svg xmlns="http://www.w3.org/2000/svg">\n<g transform="translate({ox},{oy})">\n  {body}\n</g>\n</svg>\n')


if __name__ == "__main__":
    main(sys.argv[1])
