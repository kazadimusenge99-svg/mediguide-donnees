# Rend les SVG en WebP (Chromium via Playwright, puis Pillow).
import sys, os, io, importlib
sys.path.insert(0, os.path.dirname(__file__))
from playwright.sync_api import sync_playwright
from PIL import Image
OUT = os.path.join(os.path.dirname(__file__), "out")
mods = sys.argv[1:] or ["ecg", "radio"]
figs = {}
for m in mods:
    figs.update(importlib.import_module(m).FIGURES)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(device_scale_factor=1)
    for nom, f in figs.items():
        s = f()
        open(os.path.join(OUT, nom + ".svg"), "w").write(s)
        pg.set_content(f'<html><body style="margin:0;background:#fff">{s}</body></html>')
        png = pg.locator("svg").screenshot()
        Image.open(io.BytesIO(png)).convert("RGB").save(os.path.join(OUT, nom + ".webp"), "WEBP", quality=82, method=6)
        print(nom, os.path.getsize(os.path.join(OUT, nom + ".webp")))
    b.close()
