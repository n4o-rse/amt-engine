"""The typeface of the pages and figures: Roboto, the house typeface of mainzed.

The pages load it from ``docs/vendor/roboto/`` (see ``docs/assets/site.css``). The PNG
figures are drawn with Pillow and need the same face as a TrueType file, so
``design/fonts/`` holds the Regular and Bold cuts, converted without change from the
same Roboto files (SIL OFL 1.1, licence next to them). Drawing the PNGs with the font
that the pages use keeps the pictures and the text in step on every machine.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent.parent / "design" / "fonts"
REGULAR = FONT_DIR / "Roboto-Regular.ttf"
BOLD = FONT_DIR / "Roboto-Bold.ttf"


def fonts_digest() -> str:
    """SHA-256 of the font files: a changed typeface redraws the PNG figures."""
    import hashlib
    h = hashlib.sha256()
    for f in (REGULAR, BOLD):
        h.update(f.read_bytes())
    return h.hexdigest()


@lru_cache(maxsize=None)
def pil_font(px: int, bold: bool = False):
    """A Pillow font of ``px`` pixels: Roboto Regular or Bold."""
    from PIL import ImageFont
    return ImageFont.truetype(str(BOLD if bold else REGULAR), int(px))
