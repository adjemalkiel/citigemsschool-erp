"""ponytail: assert school logo PNG has color + transparency. Run: python _check_logo.py"""
from pathlib import Path

try:
	from PIL import Image
except ImportError:
	raise SystemExit("need Pillow: pip install pillow")

here = Path(__file__).resolve().parent
logo = Image.open(here / "citigems-logo.png")
assert logo.mode == "RGBA", logo.mode
px = logo.load()
w, h = logo.size
assert any(px[x, y][3] == 0 for x in range(0, w, 8) for y in range(0, h, 8)), "no transparent pixels"
assert any(px[x, y][3] > 200 and px[x, y][0] > 150 and px[x, y][1] < 100 for x in range(0, w, 4) for y in range(0, h, 4)), "no red"
assert any(px[x, y][3] > 200 and px[x, y][0] > 180 and px[x, y][1] > 140 for x in range(0, w, 4) for y in range(0, h, 4)), "no gold"
print("ok", logo.size)
