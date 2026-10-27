"""
The colour palette of AMT, from ``design/palette.yaml``.

One file, three outputs, so that the colours cannot drift apart:

* ``docs/assets/palette.css``  the CSS variables of every page (light and dark)
* ``docs/assets/img/palette.svg``  the palette as a picture (text, byte for byte
  reproducible) and ``palette.png`` drawn from it
* the light tokens of the figures (``figure_tokens``), which
  ``py/site_figures.py`` uses for standalone SVG and PNG files

Nothing here reads the clock; the output depends on the YAML alone. Like the
figures, the PNG depends on the Pillow build, so it is redrawn only when the SVG
changed (``assets/figures.json``) or the file is missing.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PALETTE_FILE = ROOT / "design" / "palette.yaml"

COLS, TILE_W, TILE_H, GAP, MARGIN = 4, 360, 112, 20, 40


def load(path: Path = PALETTE_FILE) -> dict:
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _ids(pal: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for g in pal["groups"]:
        for c in g["colours"]:
            if c["id"] in out:
                raise ValueError(f"duplicate colour id {c['id']!r} in palette.yaml")
            out[c["id"]] = c["hex"].lower()
    return out


def _resolve(value: str, ids: dict[str, str]) -> str:
    if value.startswith("#"):
        return value.lower()
    if value not in ids:
        raise KeyError(f"palette.yaml: unknown colour id {value!r}")
    return ids[value]


def tokens(pal: dict, theme: str) -> dict[str, str]:
    """All CSS tokens of a theme as name -> hex; the dark theme is the light one with overrides."""
    ids = _ids(pal)
    light = {k: _resolve(v, ids) for k, v in pal["tokens"]["light"].items()}
    if theme == "light":
        return light
    return {**light, **{k: _resolve(v, ids) for k, v in pal["tokens"]["dark"].items()}}


def figure_tokens(pal: dict | None = None) -> dict[str, str]:
    """Light values of the figure tokens, keyed without the ``fig-`` prefix."""
    t = tokens(pal or load(), "light")
    return {k[4:]: v for k, v in t.items() if k.startswith("fig-")}


def css(pal: dict | None = None) -> str:
    pal = pal or load()
    ids = _ids(pal)
    light, dark = tokens(pal, "light"), tokens(pal, "dark")
    changed = {k: v for k, v in dark.items() if light.get(k) != v}

    def block(selector: str, items: dict[str, str], scheme: str, indent: str = "") -> list[str]:
        lines = [f"{indent}{selector} {{"]
        lines += [f"{indent}  --{k}: {v};" for k, v in items.items()]
        lines += [f"{indent}  color-scheme: {scheme};", f"{indent}}}"]
        return lines

    out = ["/* Generated from design/palette.yaml by py/site_palette.py. Do not edit. */"]
    out += block(":root", {**{f"pal-{i}": h for i, h in ids.items()}, **light}, "light dark")
    out += [':root[data-theme="light"] { color-scheme: light; }']
    out += ["@media (prefers-color-scheme: dark) {"]
    out += block(':root:not([data-theme="light"])', changed, "dark", "  ")
    out += ["}"]
    out += block(':root[data-theme="dark"]', changed, "dark")
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- the picture
def _luma(hexcol: str) -> float:
    r, g, b = (int(hexcol[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b


def _layout(pal: dict):
    """Yield ('title', x, y, text) and ('tile', x, y, colour) items and the total size."""
    items = []
    y = 130
    for g in pal["groups"]:
        items.append(("group", MARGIN, y, g["name"]))
        y += 34
        for i, c in enumerate(g["colours"]):
            items.append(("tile", MARGIN + i * (TILE_W + GAP), y, c))
        y += TILE_H + 22
    return items, MARGIN * 2 + COLS * TILE_W + (COLS - 1) * GAP, y + 10


def svg(pal: dict | None = None) -> str:
    pal = pal or load()
    items, w, h = _layout(pal)
    bg, head, sub = _resolve("paper", _ids(pal)), _resolve("green-deep", _ids(pal)), "#55625d"
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
         f'role="img" aria-label="{escape(pal["title"], quote=True)}" '
         'font-family="Roboto, system-ui, -apple-system, Segoe UI, sans-serif">',
         f'<rect width="{w}" height="{h}" fill="{bg}"/>',
         f'<text x="{MARGIN}" y="62" font-size="34" font-weight="700" fill="{head}">{escape(pal["title"])}</text>',
         f'<text x="{MARGIN}" y="96" font-size="18" fill="{sub}">{escape(pal["subtitle"])}</text>']
    for kind, x, y, v in items:
        if kind == "group":
            p.append(f'<text x="{x}" y="{y + 18}" font-size="20" font-weight="700" fill="{head}">{escape(v)}</text>')
            continue
        fg = "#ffffff" if _luma(v["hex"]) < 140 else "#1b1b18"
        p += [f'<rect x="{x}" y="{y}" width="{TILE_W}" height="{TILE_H}" rx="10" fill="{v["hex"]}" '
              'stroke="#000000" stroke-opacity="0.19"/>',
              f'<text x="{x + 14}" y="{y + 32}" font-size="20" font-weight="700" fill="{fg}">{escape(v["name"])}</text>',
              f'<text x="{x + 14}" y="{y + 62}" font-size="18" fill="{fg}">{escape(v["hex"])}</text>',
              f'<text x="{x + 14}" y="{y + 92}" font-size="15" fill="{fg}">{escape(v["use"])}</text>']
    p.append("</svg>")
    return "\n".join(p) + "\n"


def render_png(path: Path, pal: dict | None = None) -> None:
    from PIL import Image, ImageDraw, ImageFont
    pal = pal or load()
    items, w, h = _layout(pal)
    ids = _ids(pal)
    im = Image.new("RGB", (w, h), _resolve("paper", ids))
    d = ImageDraw.Draw(im)
    fonts: dict[int, object] = {}
    font = lambda px: fonts.setdefault(px, ImageFont.load_default(size=px))
    head = _resolve("green-deep", ids)
    d.text((MARGIN, 28), pal["title"], font=font(34), fill=head)
    d.text((MARGIN, 76), pal["subtitle"], font=font(18), fill="#55625d")
    for kind, x, y, v in items:
        if kind == "group":
            d.text((x, y), v, font=font(20), fill=head)
            continue
        fg = "#ffffff" if _luma(v["hex"]) < 140 else "#1b1b18"
        d.rounded_rectangle((x, y, x + TILE_W, y + TILE_H), 10, fill=v["hex"], outline="#c9c9c2")
        d.text((x + 14, y + 12), v["name"], font=font(20), fill=fg)
        d.text((x + 14, y + 44), v["hex"], font=font(18), fill=fg)
        d.text((x + 14, y + 76), v["use"], font=font(15), fill=fg)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, optimize=True)


if __name__ == "__main__":
    import sys
    sys.stdout.write(css())
