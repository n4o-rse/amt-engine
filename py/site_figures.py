"""
Figures of the vocabulary and ontology pages, drawn from code.

Every figure is a small *scene* (circles, boxes, arrows, islands) that is
rendered twice: as SVG (vector, themeable through CSS variables, inlined into
the pages) and as PNG (three times the SVG size, transparent, for slides and
papers). The look follows the 2018 diagrams: green circles, black arrows,
a red dashed arc for what is inferred, white islands for disjoint roles.

The overview of the vocabulary is not drawn by hand: its boxes and arrows come
from ``ontology/amt.ttl`` (classes, ``rdfs:subClassOf``, domain and range of
the properties). Only the *position* of each box is fixed in ``POSITIONS``;
a class without a position makes the build fail, so the figure cannot silently
fall behind the ontology.

Determinism
-----------
The SVG files are plain text from fixed numbers and are compared byte for
byte. The PNG files depend on the Pillow/FreeType build, so they are not
compared: ``figures.json`` records the SHA-256 of every SVG (plus the font files), and a PNG is
redrawn only when its SVG or the fonts changed or the PNG is missing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from html import escape
from pathlib import Path

AMT = "http://academic-meta-tool.xyz/vocab#"
PNG_SCALE = 3      # PNG pixels per SVG unit
_SS = 2            # supersampling for the antialiasing of the PNG

# Light-theme fallbacks, from design/palette.yaml (the single source of the
# colours). In the pages, assets/palette.css defines the same names for the
# light and the dark theme; a standalone SVG or PNG uses these values.
try:
    from site_fonts import pil_font
    from site_palette import figure_tokens
except ImportError:
    from py.site_fonts import pil_font
    from py.site_palette import figure_tokens
TOKENS = figure_tokens()


def tok(name: str) -> str:
    return TOKENS[name]


def var(name: str) -> str:
    """CSS value for a token: the page variable with the light value as fallback."""
    return f"var(--fig-{name},{TOKENS[name]})"


def _hex(c: str) -> tuple[int, int, int]:
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


# --------------------------------------------------------------------------- #
# Scene
# --------------------------------------------------------------------------- #
@dataclass
class Node:
    kind: str                 # circle | box | ellipse
    cx: float
    cy: float
    w: float                  # box/ellipse width, circle diameter
    h: float
    style: str = "plain"      # circle: green|white; box: plain|core|axiom|logic|rule|ext|lit
    runs: list = field(default_factory=list)   # [(text, size_factor, dy_factor)]
    lines: list = field(default_factory=list)  # extra small lines under the title (boxes)
    dashed: bool = False


def runs(text: str) -> list:
    """'R_1' becomes R with a small, lowered 1. A plain string stays one run."""
    if "_" in text:
        base, sub = text.split("_", 1)
        return [(base, 1.0, 0.0), (sub, 0.55, 0.28)]
    return [(text, 1.0, 0.0)]


class Scene:
    def __init__(self, name: str, w: int, h: int, title: str) -> None:
        self.name, self.w, self.h, self.title = name, w, h, title
        self.nodes: dict[str, Node] = {}
        self.ops: list[tuple] = []          # drawing order

    # -- nodes ------------------------------------------------------------- #
    def circle(self, key, cx, cy, label, d=110, style="green"):
        n = Node("circle", cx, cy, d, d, style, runs(label))
        self.nodes[key] = n
        self.ops.append(("node", key))
        return n

    def box(self, key, cx, cy, w, h, label, style="plain", lines=(), dashed=False):
        n = Node("box", cx, cy, w, h, style, [(label, 1.0, 0.0)], list(lines), dashed)
        self.nodes[key] = n
        self.ops.append(("node", key))
        return n

    def ellipse(self, key, cx, cy, w, h, label="", style="white"):
        n = Node("ellipse", cx, cy, w, h, style, runs(label) if label else [])
        self.nodes[key] = n
        self.ops.append(("node", key))
        return n

    def island(self, cx, cy, rx, ry, seed=0):
        self.ops.append(("island", cx, cy, rx, ry, seed))

    # -- edges and text ---------------------------------------------------- #
    def edge(self, a, b, label="", style="solid", color="line", head=True,
             bend=0.0, label_at=0.5, label_dy=-12, gap=3):
        self.ops.append(("edge", a, b, label, style, color, head, bend, label_at, label_dy, gap))

    def loop(self, key, label, color="line", side="top"):
        self.ops.append(("loop", key, label, color, side))

    def text(self, x, y, text, size=16, anchor="middle", color="muted", bold=False):
        self.ops.append(("text", x, y, text, size, anchor, color, bold))

    def symbol(self, kind, x, y, size=40, color="node-edge"):
        """``notin`` and ``subeq`` are drawn as lines, so no font has to contain them."""
        h = size / 2
        if kind == "notin":      # the element sign with a slash
            lines = [[(x + .6 * h, y - h), (x - .4 * h, y - h), (x - .8 * h, y - .5 * h), (x - .8 * h, y + .5 * h),
                      (x - .4 * h, y + h), (x + .6 * h, y + h)],
                     [(x - .8 * h, y), (x + .6 * h, y)],
                     [(x - .9 * h, y + 1.2 * h), (x + .9 * h, y - 1.2 * h)]]
        elif kind == "subeq":    # a square subset sign with an underline
            lines = [[(x + .7 * h, y - .8 * h), (x - .7 * h, y - .8 * h), (x - .7 * h, y + .5 * h), (x + .7 * h, y + .5 * h)],
                     [(x - .7 * h, y + h), (x + .7 * h, y + h)]]
        else:
            raise ValueError(kind)
        self.ops.append(("lines", lines, color))


# -- geometry ---------------------------------------------------------------- #
def _boundary(n: Node, tx: float, ty: float, gap: float) -> tuple[float, float]:
    """Point where the ray from the centre of ``n`` towards (tx, ty) leaves it."""
    dx, dy = tx - n.cx, ty - n.cy
    dist = math.hypot(dx, dy) or 1.0
    ux, uy = dx / dist, dy / dist
    if n.kind == "circle":
        t = n.w / 2
    elif n.kind == "ellipse":
        a, b = n.w / 2, n.h / 2
        t = 1.0 / math.sqrt((ux / a) ** 2 + (uy / b) ** 2)
    else:
        hw, hh = n.w / 2, n.h / 2
        t = min(hw / abs(ux) if ux else 1e9, hh / abs(uy) if uy else 1e9)
    t += gap
    return n.cx + ux * t, n.cy + uy * t


def _edge_points(sc: Scene, op) -> tuple:
    _, a, b, label, style, color, head, bend, label_at, label_dy, gap = op
    na, nb = sc.nodes[a], sc.nodes[b]
    # control point of the quadratic curve; bend 0 gives a straight line
    mx, my = (na.cx + nb.cx) / 2, (na.cy + nb.cy) / 2
    dx, dy = nb.cx - na.cx, nb.cy - na.cy
    dist = math.hypot(dx, dy) or 1.0
    cx, cy = mx - dy / dist * bend, my + dx / dist * bend
    p0 = _boundary(na, cx, cy, gap)
    p1 = _boundary(nb, cx, cy, gap + (2 if head else 0))
    return p0, (cx, cy), p1


def _bez(p0, c, p1, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * c[0] + t * t * p1[0],
            u * u * p0[1] + 2 * u * t * c[1] + t * t * p1[1])


def _bez_tangent(p0, c, p1, t):
    return (2 * (1 - t) * (c[0] - p0[0]) + 2 * t * (p1[0] - c[0]),
            2 * (1 - t) * (c[1] - p0[1]) + 2 * t * (p1[1] - c[1]))


def _island_points(cx, cy, rx, ry, seed):
    """A fixed, irregular outline. No random numbers: a table of radii."""
    table = [1.00, 0.86, 1.04, 0.92, 1.08, 0.88, 0.97, 1.05, 0.84, 1.02, 0.93, 1.06]
    n = len(table)
    pts = []
    for i in range(n * 3):                      # three points per table step, smoothed
        a = 2 * math.pi * i / (n * 3)
        k = i / 3
        r0, r1 = table[(int(k) + seed) % n], table[(int(k) + 1 + seed) % n]
        r = r0 + (r1 - r0) * (k - int(k))
        pts.append((cx + rx * r * math.cos(a), cy + ry * r * math.sin(a)))
    return pts


def _fmt(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def _text_w(text: str, size: float) -> float:
    return len(text) * size * 0.56


# --------------------------------------------------------------------------- #
# SVG renderer
# --------------------------------------------------------------------------- #
def _svg_runs(x, y, rs, size, fill, bold=False, anchor="middle") -> str:
    parts = []
    for text, f, dy in rs:
        parts.append(f'<tspan font-size="{_fmt(size * f)}" dy="{_fmt(size * dy)}">{escape(text)}</tspan>')
    weight = ' font-weight="700"' if bold else ""
    return (f'<text x="{_fmt(x)}" y="{_fmt(y + size * 0.35)}" text-anchor="{anchor}" '
            f'font-size="{_fmt(size)}"{weight} fill="{fill}">{"".join(parts)}</text>')


def _dash(style: str) -> str:
    return {"solid": "", "dotted": ' stroke-dasharray="2 5" stroke-linecap="round"',
            "dashed": ' stroke-dasharray="11 7"'}[style]


def _head_pts(p, tx, ty, size=12):
    """Triangle at ``p`` pointing along the tangent (tx, ty)."""
    n = math.hypot(tx, ty) or 1.0
    ux, uy = tx / n, ty / n
    bx, by = p[0] - ux * size, p[1] - uy * size
    return [p, (bx - uy * size * 0.42, by + ux * size * 0.42), (bx + uy * size * 0.42, by - ux * size * 0.42)]


def _node_style(n: Node):
    if n.kind == "circle":
        return ("grad", "node-text") if n.style == "green" else (var("white-fill"), "white-text")
    if n.kind == "ellipse":
        return var("white-fill"), "white-text"
    fills = {"plain": "box-fill", "core": "node-bottom", "axiom": "axiom-fill",
             "logic": "logic-fill", "rule": "rule-fill", "ext": "ext-fill", "lit": "lit-fill"}
    text = "node-text" if n.style == "core" else "box-text"
    return var(fills[n.style]), text


def render_svg(sc: Scene) -> str:
    gid = f"g-{sc.name}"
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {sc.w} {sc.h}" role="img" '
        f'aria-labelledby="t-{sc.name}" font-family="Roboto, system-ui, -apple-system, Segoe UI, sans-serif">',
        f'<title id="t-{sc.name}">{escape(sc.title)}</title>',
        f'<defs><linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" style="stop-color:{var("node-top")}"/>'
        f'<stop offset="1" style="stop-color:{var("node-bottom")}"/></linearGradient></defs>',
    ]
    for op in sc.ops:
        kind = op[0]
        if kind == "island":
            _, cx, cy, rx, ry, seed = op
            pts = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in _island_points(cx, cy, rx, ry, seed))
            out.append(f'<polygon points="{pts}" fill="{var("island-fill")}" stroke="{var("island-edge")}" '
                       f'stroke-width="2" stroke-linejoin="round"/>')
        elif kind == "node":
            n = sc.nodes[op[1]]
            fill, tcolor = _node_style(n)
            if fill == "grad":
                fill = f"url(#{gid})"
            stroke = var("node-edge")
            dash = ' stroke-dasharray="7 5"' if n.dashed else ""
            if n.kind == "circle":
                out.append(f'<circle cx="{_fmt(n.cx)}" cy="{_fmt(n.cy)}" r="{_fmt(n.w / 2)}" fill="{fill}" '
                           f'stroke="{stroke}" stroke-width="2"/>')
                size = n.w * 0.46
                out.append(_svg_runs(n.cx, n.cy, n.runs, size, var(tcolor), bold=True))
            elif n.kind == "ellipse":
                out.append(f'<ellipse cx="{_fmt(n.cx)}" cy="{_fmt(n.cy)}" rx="{_fmt(n.w / 2)}" ry="{_fmt(n.h / 2)}" '
                           f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
                if n.runs:
                    out.append(_svg_runs(n.cx, n.cy, n.runs, n.h * 0.42, var(tcolor), bold=True))
            else:
                x, y = n.cx - n.w / 2, n.cy - n.h / 2
                out.append(f'<rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(n.w)}" height="{_fmt(n.h)}" rx="9" '
                           f'fill="{fill}" stroke="{stroke if n.style != "ext" else var("muted")}" '
                           f'stroke-width="2"{dash}/>')
                ty = n.cy - (len(n.lines) * 7 if n.lines else 0)
                out.append(_svg_runs(n.cx, ty, n.runs, 17, var(tcolor), bold=True))
                for i, line in enumerate(n.lines):
                    out.append(_svg_runs(n.cx, ty + 21 + i * 15, [(line, 1.0, 0.0)], 11.5, var("muted")))
        elif kind == "edge":
            p0, c, p1 = _edge_points(sc, op)
            _, a, b, label, style, color, head, bend, label_at, label_dy, gap = op
            col = var(color)
            if bend:
                path = f"M{_fmt(p0[0])},{_fmt(p0[1])} Q{_fmt(c[0])},{_fmt(c[1])} {_fmt(p1[0])},{_fmt(p1[1])}"
            else:
                path = f"M{_fmt(p0[0])},{_fmt(p0[1])} L{_fmt(p1[0])},{_fmt(p1[1])}"
            width = 3.5 if style == "dashed" else 2.2
            out.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="{width}"{_dash(style)}/>')
            if head:
                tx, ty = _bez_tangent(p0, c, p1, 1.0) if bend else (p1[0] - p0[0], p1[1] - p0[1])
                hp = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in _head_pts(p1, tx, ty))
                out.append(f'<polygon points="{hp}" fill="{col}"/>')
            if label:
                lx, ly = _bez(p0, c, p1, label_at) if bend else (p0[0] + (p1[0] - p0[0]) * label_at,
                                                                 p0[1] + (p1[1] - p0[1]) * label_at)
                tw = _text_w(label, 15) + 10
                out.append(f'<rect x="{_fmt(lx - tw / 2)}" y="{_fmt(ly + label_dy - 10)}" width="{_fmt(tw)}" height="20" '
                           f'rx="4" fill="{var("bg")}" fill-opacity="0.9"/>')
                out.append(_svg_runs(lx, ly + label_dy, runs(label), 15, col if color == "red" else var("box-text")))
        elif kind == "loop":
            _, key, label, color, side = op
            n = sc.nodes[key]
            sg = -1 if side == "top" else 1
            x0, y0 = n.cx - n.w * 0.22, n.cy + sg * n.h / 2
            x1, y1 = n.cx + n.w * 0.22, n.cy + sg * n.h / 2
            top = y0 + sg * 46
            out.append(f'<path d="M{_fmt(x0)},{_fmt(y0)} C{_fmt(x0 - 26)},{_fmt(top)} {_fmt(x1 + 26)},{_fmt(top)} '
                       f'{_fmt(x1)},{_fmt(y1 + sg * 3)}" fill="none" stroke="{var(color)}" stroke-width="2.2"/>')
            hp = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in _head_pts((x1, y1 + sg), 0, -sg, 11))
            out.append(f'<polygon points="{hp}" fill="{var(color)}"/>')
            out.append(_svg_runs(n.cx, top + sg * 10, [(label, 1.0, 0.0)], 14, var("box-text")))
        elif kind == "lines":
            _, lines, color = op
            for ln in lines:
                d = "M" + " L".join(f"{_fmt(x)},{_fmt(y)}" for x, y in ln)
                out.append(f'<path d="{d}" fill="none" stroke="{var(color)}" stroke-width="3.2" '
                           f'stroke-linecap="round" stroke-linejoin="round"/>')
        elif kind == "text":
            _, x, y, text, size, anchor, color, bold = op
            out.append(_svg_runs(x, y, runs(text), size, var(color), bold=bold, anchor=anchor))
    out.append("</svg>")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------- #
# PNG renderer (Pillow)
# --------------------------------------------------------------------------- #
def render_png(sc: Scene, path: Path) -> None:
    from PIL import Image, ImageDraw, ImageFilter

    K = PNG_SCALE * _SS
    W, H = sc.w * K, sc.h * K
    img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    def font(px: float, bold: bool = False):
        return pil_font(max(6, int(round(px))), bold)

    def draw_runs(x, y, rs, size, color, bold=False, anchor="m"):
        # total width first, then draw the runs left to right
        widths = [d.textlength(t, font=font(size * f * K, bold)) for t, f, _ in rs]
        total = sum(widths)
        cx = x * K - (total / 2 if anchor == "m" else 0)
        for (t, f, dy), w in zip(rs, widths):
            d.text((cx, (y + size * dy) * K), t, font=font(size * f * K, bold), fill=_hex(color) + (255,),
                   anchor="lm")
            cx += w

    def poly(pts, fill=None, outline=None, width=0):
        d.polygon([(x * K, y * K) for x, y in pts], fill=fill, outline=outline, width=width)

    def line(pts, color, width, style="solid"):
        col = _hex(tok(color)) + (255,)
        flat = [(x * K, y * K) for x, y in pts]
        if style == "solid":
            d.line(flat, fill=col, width=int(width * K), joint="curve")
            return
        on, off = (12, 7) if style == "dashed" else (0.1, 5)
        on, off = on * K, off * K
        acc, drawing = 0.0, True
        for (x0, y0), (x1, y1) in zip(flat, flat[1:]):
            seg = math.hypot(x1 - x0, y1 - y0)
            pos = 0.0
            while pos < seg:
                step = min((on if drawing else off) - acc, seg - pos)
                if drawing:
                    a = (x0 + (x1 - x0) * pos / seg, y0 + (y1 - y0) * pos / seg)
                    b = (x0 + (x1 - x0) * (pos + step) / seg, y0 + (y1 - y0) * (pos + step) / seg)
                    if style == "dotted":
                        r = width * K * 0.55
                        d.ellipse([a[0] - r, a[1] - r, a[0] + r, a[1] + r], fill=col)
                    else:
                        d.line([a, b], fill=col, width=int(width * K))
                pos += step
                acc += step
                if acc >= (on if drawing else off) - 1e-9:
                    drawing, acc = not drawing, 0.0

    def gradient_circle(n: Node):
        r = n.w / 2 * K
        size = int(2 * r) + 2
        top, bot = _hex(tok("node-top")), _hex(tok("node-bottom"))
        grad = Image.new("RGBA", (size, size))
        gd = ImageDraw.Draw(grad)
        for yy in range(size):
            t = yy / (size - 1)
            gd.line([(0, yy), (size, yy)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)) + (255,))
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([1, 1, size - 2, size - 2], fill=255)
        x0, y0 = int(n.cx * K - size / 2), int(n.cy * K - size / 2)
        # a soft shadow below the circle, as in the 2018 diagrams
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse([x0 + 4 * K, y0 + 6 * K, x0 + size - 4 * K, y0 + size + 4 * K], fill=(0, 0, 0, 55))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5 * K)))
        img.paste(grad, (x0, y0), mask)

    fill_of = {"plain": "box-fill", "core": "node-bottom", "axiom": "axiom-fill", "logic": "logic-fill",
               "rule": "rule-fill", "ext": "ext-fill", "lit": "lit-fill"}
    for op in sc.ops:
        kind = op[0]
        if kind == "island":
            _, cx, cy, rx, ry, seed = op
            poly(_island_points(cx, cy, rx, ry, seed), fill=_hex(tok("island-fill")) + (255,),
                 outline=_hex(tok("island-edge")) + (255,), width=2 * K)
        elif kind == "node":
            n = sc.nodes[op[1]]
            ecol = _hex(tok("node-edge")) + (255,)
            if n.kind == "circle":
                if n.style == "green":
                    gradient_circle(n)
                    tcol = tok("node-text")
                else:
                    r = n.w / 2 * K
                    d.ellipse([n.cx * K - r, n.cy * K - r, n.cx * K + r, n.cy * K + r],
                              fill=_hex(tok("white-fill")) + (255,), outline=ecol, width=2 * K)
                    tcol = tok("white-text")
                draw_runs(n.cx, n.cy, n.runs, n.w * 0.46, tcol, bold=True)
            elif n.kind == "ellipse":
                d.ellipse([(n.cx - n.w / 2) * K, (n.cy - n.h / 2) * K, (n.cx + n.w / 2) * K, (n.cy + n.h / 2) * K],
                          fill=_hex(tok("white-fill")) + (255,), outline=ecol, width=2 * K)
                if n.runs:
                    draw_runs(n.cx, n.cy, n.runs, n.h * 0.42, tok("white-text"), bold=True)
            else:
                box = [(n.cx - n.w / 2) * K, (n.cy - n.h / 2) * K, (n.cx + n.w / 2) * K, (n.cy + n.h / 2) * K]
                outline = _hex(tok("muted")) + (255,) if n.style == "ext" else ecol
                d.rounded_rectangle(box, radius=9 * K, fill=_hex(tok(fill_of[n.style])) + (255,),
                                    outline=outline, width=2 * K)
                tcol = tok("node-text") if n.style == "core" else tok("box-text")
                ty = n.cy - (len(n.lines) * 7 if n.lines else 0)
                draw_runs(n.cx, ty, n.runs, 17, tcol, bold=True)
                for i, ln in enumerate(n.lines):
                    draw_runs(n.cx, ty + 21 + i * 15, [(ln, 1.0, 0.0)], 11.5, tok("muted"))
        elif kind == "edge":
            p0, c, p1 = _edge_points(sc, op)
            _, a, b, label, style, color, head, bend, label_at, label_dy, gap = op
            pts = [_bez(p0, c, p1, i / 40) for i in range(41)] if bend else [p0, p1]
            line(pts, color, 3.5 if style == "dashed" else 2.2, style)
            if head:
                tx, ty = _bez_tangent(p0, c, p1, 1.0) if bend else (p1[0] - p0[0], p1[1] - p0[1])
                poly(_head_pts(p1, tx, ty), fill=_hex(tok(color)) + (255,))
            if label:
                lx, ly = _bez(p0, c, p1, label_at) if bend else (p0[0] + (p1[0] - p0[0]) * label_at,
                                                                 p0[1] + (p1[1] - p0[1]) * label_at)
                tw = _text_w(label, 15) + 10
                d.rounded_rectangle([(lx - tw / 2) * K, (ly + label_dy - 10) * K, (lx + tw / 2) * K, (ly + label_dy + 10) * K],
                                    radius=4 * K, fill=_hex(tok("bg")) + (230,))
                draw_runs(lx, ly + label_dy, runs(label), 15, tok("red") if color == "red" else tok("box-text"))
        elif kind == "loop":
            _, key, label, color, side = op
            n = sc.nodes[key]
            sg = -1 if side == "top" else 1
            x0, y0 = n.cx - n.w * 0.22, n.cy + sg * n.h / 2
            x1, y1 = n.cx + n.w * 0.22, n.cy + sg * n.h / 2
            top = y0 + sg * 46
            pts = []
            for i in range(41):
                t, u = i / 40, 1 - i / 40
                pts.append((u ** 3 * x0 + 3 * u * u * t * (x0 - 26) + 3 * u * t * t * (x1 + 26) + t ** 3 * x1,
                            u ** 3 * y0 + 3 * u * u * t * top + 3 * u * t * t * top + t ** 3 * (y1 + sg * 3)))
            line(pts, color, 2.2)
            poly(_head_pts((x1, y1 + sg), 0, -sg, 11), fill=_hex(tok(color)) + (255,))
            draw_runs(n.cx, top + sg * 10, [(label, 1.0, 0.0)], 14, tok("box-text"))
        elif kind == "lines":
            _, lines, color = op
            for ln in lines:
                line(ln, color, 3.2)
        elif kind == "text":
            _, x, y, text, size, anchor, color, bold = op
            draw_runs(x, y, runs(text), size, tok(color), bold=bold, anchor="m" if anchor == "middle" else "l")
    img = img.resize((sc.w * PNG_SCALE, sc.h * PNG_SCALE), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=False)


# --------------------------------------------------------------------------- #
# The small figures (the 2018 set, redrawn, plus the ones that are new)
# --------------------------------------------------------------------------- #
def fig_concept() -> Scene:
    s = Scene("concept", 760, 190, "A Concept: an individual is an instance of a node that has the type amt:Concept")
    s.circle("i", 90, 95, "n", d=100, style="white")
    s.circle("c", 330, 95, "C")
    s.box("t", 620, 95, 170, 54, "amt:Concept")
    s.edge("i", "c", "amt:instanceOf", label_dy=-20)
    s.edge("c", "t", "rdf:type", style="dotted", color="muted", label_dy=-20)
    return s


def fig_role() -> Scene:
    s = Scene("role", 760, 300, "A Role relates two Concepts; it has the type amt:Role")
    s.circle("c1", 90, 80, "C_1", d=100)
    s.circle("c2", 90, 230, "C_2", d=100)
    s.circle("r", 340, 155, "R")
    s.box("t", 620, 155, 170, 54, "amt:Role")
    s.edge("r", "c1", "rdfs:domain", color="muted", style="dotted", label_dy=-8)
    s.edge("r", "c2", "rdfs:range", color="muted", style="dotted", label_dy=14)
    s.edge("r", "t", "rdf:type", style="dotted", color="muted", label_dy=-20)
    return s


def fig_quadruple() -> Scene:
    s = Scene("quadruple", 900, 380, "A weighted edge: a quadruple of subject, role, object and a weight in [0;1]")
    s.ellipse("e", 450, 70, 260, 74, "edge")
    s.circle("a", 130, 290, "C_1", d=110)
    s.circle("r", 370, 290, "R", d=110)
    s.circle("b", 610, 290, "C_2", d=110)
    s.circle("w", 810, 290, "[0;1]", d=100, style="white")
    s.edge("e", "a", "rdf:subject", label_at=0.5, label_dy=-6)
    s.edge("e", "r", "rdf:predicate", label_at=0.5, label_dy=-6)
    s.edge("e", "b", "rdf:object", label_at=0.5, label_dy=-6)
    s.edge("e", "w", "amt:weight", label_at=0.5, label_dy=-6)
    return s


def fig_rca() -> Scene:
    s = Scene("rca", 900, 250, "Role chain: C1 to C2 by the first antecedent, C2 to C3 by the second; the consequent holds between C1 and C3")
    s.circle("a", 100, 150, "C_1", d=120)
    s.circle("b", 450, 150, "C_2", d=120)
    s.circle("c", 800, 150, "C_3", d=120)
    s.edge("a", "b", "antecedent1", label_dy=-18)
    s.edge("b", "c", "antecedent2", label_dy=-18)
    s.edge("a", "c", "consequent, logic", style="dashed", color="red", bend=-160, label_at=0.5, label_dy=-16)
    return s


def fig_rca_nary() -> Scene:
    s = Scene("rca-nary", 1000, 270, "Role chain of n steps: antecedents is an RDF list of roles")
    xs = [90, 340, 590, 910]
    names = ["C_1", "C_2", "C_3", "C_n"]
    for i, (x, nm) in enumerate(zip(xs, names)):
        s.circle(f"c{i}", x, 150, nm, d=110)
    s.edge("c0", "c1", "R_1", label_dy=-18)
    s.edge("c1", "c2", "R_2", label_dy=-18)
    s.edge("c2", "c3", "R_n", style="dotted", label_dy=-18)
    s.edge("c0", "c3", "consequent, logic", style="dashed", color="red", bend=-170, label_at=0.5, label_dy=-16)
    s.text(500, 250, "amt:antecedents ( R1  R2  ...  Rn )", 15)
    return s


def fig_inverse() -> Scene:
    s = Scene("ia", 760, 250, "Inverse axiom: an edge with the antecedent role implies the reverse edge with the inverse role")
    s.circle("a", 110, 100, "R_1", d=120)
    s.circle("b", 650, 100, "R_2", d=120)
    s.edge("a", "b", "amt:antecedent", bend=-70, label_dy=-14)
    s.edge("b", "a", "amt:inverse", bend=-70, label_dy=16)
    return s


def fig_disjoint() -> Scene:
    s = Scene("da", 760, 340, "Disjoint axiom: two roles that must not hold between the same pair of nodes")
    s.island(170, 165, 135, 125, seed=0)
    s.island(590, 165, 135, 125, seed=5)
    s.circle("r1", 170, 165, "R_1", d=140)
    s.circle("r2", 590, 165, "R_2", d=140)
    s.symbol("notin", 380, 175, 50)
    return s


def fig_self_disjoint() -> Scene:
    s = Scene("sda", 760, 340, "Self-disjoint axiom: a role must not hold between a node and itself")
    s.island(170, 165, 135, 125, seed=3)
    s.island(590, 165, 135, 125, seed=8)
    s.circle("r1", 170, 165, "R_1", d=140)
    s.circle("r2", 590, 165, "R_1", d=140)
    s.symbol("notin", 380, 175, 50)
    return s


def fig_subsumption() -> Scene:
    s = Scene("sda-sub", 760, 340, "Subsumption axiom: every edge with the sub-role also carries the super-role")
    s.island(380, 170, 330, 150, seed=2)
    s.circle("sub", 290, 175, "R_sub", d=140)
    s.text(575, 105, "R_super", 30, color="node-edge", bold=True)
    s.symbol("subeq", 445, 180, 46)
    return s


SMALL_FIGURES = {
    "concept": fig_concept, "role": fig_role, "quadruple": fig_quadruple, "rca": fig_rca,
    "rca-nary": fig_rca_nary, "ia": fig_inverse, "da": fig_disjoint, "sda": fig_self_disjoint,
    "subsumption": fig_subsumption,
}


# --------------------------------------------------------------------------- #
# The overview, drawn from ontology/amt.ttl
# --------------------------------------------------------------------------- #
# Centre of every box. The *content* (which boxes, which arrows) comes from the
# ontology; this table only says where to put each one.
POSITIONS = {
    "rdfs:Class": (640, 60), "rdf:Property": (1250, 830), "rdf:List": (110, 740),
    "rdfs:Literal": (170, 70), "xsd:decimal": (460, 300),
    "Concept": (190, 240), "Logic": (190, 440), "Axiom": (640, 230), "ReasoningRule": (1250, 240),
    "InferenceAxiom": (480, 400), "IntegrityAxiom": (940, 400),
    "RoleChainAxiom": (260, 610), "InverseAxiom": (500, 610), "SubsumptionAxiom": (740, 610),
    "DisjointAxiom": (990, 610), "SelfDisjointAxiom": (1230, 610), "Role": (740, 830),
}
# Where on the arrow the label sits (default 0.5), so that the five arrows into Role do not share a spot.
LABEL_AT = {("RoleChainAxiom", "Role"): 0.22, ("InverseAxiom", "Role"): 0.5, ("SubsumptionAxiom", "Role"): 0.65,
            ("SelfDisjointAxiom", "Role"): 0.4}
_EXTERNAL = {"rdfs:Class", "rdf:Property", "rdf:List"}
_LITERAL = {"rdfs:Literal", "xsd:decimal"}
_STYLE = {"Concept": "core", "Role": "core", "Axiom": "axiom", "InferenceAxiom": "axiom",
          "IntegrityAxiom": "axiom", "RoleChainAxiom": "axiom", "InverseAxiom": "axiom",
          "SubsumptionAxiom": "axiom", "DisjointAxiom": "axiom", "SelfDisjointAxiom": "axiom",
          "Logic": "logic", "ReasoningRule": "rule"}
_CURIE = {
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs:", "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf:",
    "http://www.w3.org/2001/XMLSchema#": "xsd:",
}


def _short(iri: str) -> str:
    if iri.startswith(AMT):
        return iri[len(AMT):]
    for ns, pre in _CURIE.items():
        if iri.startswith(ns):
            return pre + iri[len(ns):]
    return iri


def _wrap(words: list[str], limit: int) -> list[str]:
    """Join words with commas into lines of at most ``limit`` characters."""
    out, cur = [], ""
    for w in words:
        nxt = f"{cur}, {w}" if cur else w
        if len(nxt) > limit and cur:
            out.append(cur + ",")
            cur = w
        else:
            cur = nxt
    if cur:
        out.append(cur)
    return out


def overview_scene(graph) -> Scene:
    """Build the overview from the ontology graph. Raises if a box has no position."""
    from rdflib import RDF, RDFS, URIRef

    s = Scene("overview", 1400, 910, "The Academic Meta Tool vocabulary: classes, subclass links and the properties between them")
    classes = sorted(str(c)[len(AMT):] for c in graph.subjects(RDF.type, RDFS.Class) if str(c).startswith(AMT))
    missing = [c for c in classes if c not in POSITIONS]
    if missing:
        raise SystemExit(f"figure 'overview': no position for class(es) {missing}; add them to POSITIONS in py/site_figures.py")

    # properties: collapse literal-valued ones on Logic and ReasoningRule into the box
    extra: dict[str, list[str]] = {}
    edges: dict[tuple[str, str], list[str]] = {}
    loops: list[tuple[str, str]] = []
    used = set(classes)
    for p in sorted(graph.subjects(RDF.type, RDF.Property), key=str):
        if not str(p).startswith(AMT):
            continue
        name = str(p)[len(AMT):]
        dom = graph.value(p, RDFS.domain)
        rng = graph.value(p, RDFS.range)
        if rng is None:
            continue
        dname = _short(str(dom)) if dom is not None else None
        rname = _short(str(rng))
        if dname is None:
            if rname in classes:                    # e.g. instanceOf: points back at its range
                loops.append((rname, name))
            continue                                # e.g. weight: drawn in the quadruple figure
        if dname in ("Logic", "ReasoningRule") and rname in ("xsd:string", "xsd:boolean"):
            extra.setdefault(dname, []).append(name)
            continue
        if rname not in POSITIONS:
            raise SystemExit(f"figure 'overview': no position for range {rname} of {name}")
        edges.setdefault((dname, rname), []).append(name)
        used.add(rname)

    # subclass links
    subs: list[tuple[str, str]] = []
    for c in classes:
        for sup in sorted(graph.objects(URIRef(AMT + c), RDFS.subClassOf), key=str):
            sname = _short(str(sup))
            if sname not in POSITIONS:
                raise SystemExit(f"figure 'overview': no position for superclass {sname} of {c}")
            subs.append((c, sname))
            used.add(sname)

    for key in sorted(used, key=lambda k: (POSITIONS[k][1], POSITIONS[k][0])):
        x, y = POSITIONS[key]
        if key in _EXTERNAL:
            s.box(key, x, y, 150, 44, key, style="ext", dashed=True)
        elif key in _LITERAL:
            s.box(key, x, y, 140, 40, key, style="lit")
        else:
            lines = _wrap(sorted(extra.get(key, [])), 30)
            h = 50 + 15 * len(lines) if lines else 50
            s.box(key, x, y, 215 if lines else 190, h, key, style=_STYLE.get(key, "plain"), lines=lines)
    for c, sup in subs:
        s.edge(c, sup, "", style="dotted", color="muted")
    for (d, r), names in sorted(edges.items()):
        s.edge(d, r, ", ".join(sorted(names)), label_at=LABEL_AT.get((d, r), 0.5), label_dy=0)
    for key, name in loops:
        s.loop(key, name, side="bottom")
    s.text(700, 893, "dotted: rdfs:subClassOf   |   solid: property from domain to range   |   dashed outline: defined elsewhere", 13)
    return s
