"""Turn the raw captures (tools/shots.py, tools/looks.py) into the site's images.

    py -3.11 tools/make_assets.py <captures dir> <looks dir>
"""
import os
import sys
import zipfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
IMG = os.path.join(SITE, "src", "assets", "img")
SHOTS, LOOKS = (os.path.abspath(p) for p in sys.argv[1:3])


def webp(image, path, quality=84):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path, "WEBP", quality=quality, method=6)
    return os.path.getsize(path) // 1024


def two_sizes(image, stem, quality=84):
    """<stem>@2x.webp as captured and <stem>.webp at half size."""
    half = image.resize((image.width // 2, image.height // 2), Image.LANCZOS)
    a = webp(image, stem + "@2x.webp", quality - 6)
    b = webp(half, stem + ".webp", quality)
    print(f"{os.path.basename(stem):24s} {half.size} {b} KB   2x {a} KB")


# full-window screenshots
for name in ("develop", "presets", "mask", "lens-blur", "depth", "colour", "cull", "library"):
    two_sizes(Image.open(os.path.join(SHOTS, name + ".png")).convert("RGB"), os.path.join(IMG, "shots", name))

# details, cropped from the 2x captures (left, top, right, bottom)
crops = {
    "detail-presets": ("presets", (0, 109, 1500, 1389)),
    "detail-controls": ("develop", (1500, 109, 3000, 1389)),
    "detail-history": ("develop", (504, 109, 2004, 1109)),
    "detail-mask": ("mask", (938, 240, 2316, 1420)),
    "detail-depth": ("depth", (938, 109, 3000, 1500)),
    "detail-colour": ("colour", (1500, 109, 3000, 1500)),
}
for out, (source, box) in crops.items():
    two_sizes(Image.open(os.path.join(SHOTS, source + ".png")).convert("RGB").crop(box), os.path.join(IMG, "shots", out))
two_sizes(Image.open(os.path.join(SHOTS, "export-dialog.png")).convert("RGB"), os.path.join(IMG, "shots", "detail-export"))

# before / after
for file in sorted(os.listdir(LOOKS)):
    if file.endswith(".png") and file.startswith("estuary__"):
        image = Image.open(os.path.join(LOOKS, file)).convert("RGB").resize((1600, 1067), Image.LANCZOS)
        name = file[len("estuary__"):-4]
        kb = webp(image, os.path.join(IMG, "looks", name + ".webp"), 82)
        print(f"look {name:20s} {kb} KB")

# brand: icons and the mark
brand = os.path.join(IMG, "brand")
os.makedirs(brand, exist_ok=True)
logo = Image.open(os.path.join(SHOTS, "logo-1024.png")).convert("RGBA")
for size, name in ((512, "icon-512.png"), (192, "icon-192.png"), (180, "apple-touch-icon.png"), (32, "favicon-32.png")):
    logo.resize((size, size), Image.LANCZOS).save(os.path.join(brand, name))
logo.save(os.path.join(brand, "vetra-logo-1024.png"))
logo.save(os.path.join(SITE, "src", "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])
Image.open(os.path.join(SHOTS, "mark-512.png")).save(os.path.join(brand, "vetra-mark-512.png"))


def font(names, size):
    for name in names:
        try:
            return ImageFont.truetype(os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", name), size)
        except OSError:
            continue
    return ImageFont.load_default()


# the card shown when a link to the site is shared (1200 x 630)
card = Image.new("RGB", (1200, 630), "#0b0b0a")
glow = Image.new("RGB", (1200, 630), "#0b0b0a")
ImageDraw.Draw(glow).ellipse((500, 140, 1500, 900), fill="#3a2c16")
card = Image.blend(card, glow.filter(ImageFilter.GaussianBlur(160)), 0.9)
shot = Image.open(os.path.join(SHOTS, "develop.png")).convert("RGB").resize((1050, 658), Image.LANCZOS)
frame = Image.new("RGB", (shot.width + 2, shot.height + 2), "#3a3530")
frame.paste(shot, (1, 1))
card.paste(frame, (640, 250))
draw = ImageDraw.Draw(card)
mark = logo.resize((72, 72), Image.LANCZOS)
card.paste(mark, (70, 66), mark)
draw.text((160, 82), "V E T R A", font=font(["segoeuib.ttf", "arialbd.ttf"], 34), fill="#ece8e1")
serif = font(["palab.ttf", "georgiab.ttf"], 66)
draw.text((70, 190), "The photo editor", font=serif, fill="#ece8e1")
draw.text((70, 268), "that stays on", font=serif, fill="#ece8e1")
draw.text((70, 346), "your computer.", font=serif, fill="#e2c68f")
draw.text((72, 460), "Free for Windows 10 & 11", font=font(["segoeui.ttf", "arial.ttf"], 26), fill="#a7a198")
card.save(os.path.join(IMG, "og-card.jpg"), quality=88)
print("og-card.jpg", os.path.getsize(os.path.join(IMG, "og-card.jpg")) // 1024, "KB")

# press kit: the mark and four full-size screenshots
press = os.path.join(SITE, "src", "press")
os.makedirs(press, exist_ok=True)
with zipfile.ZipFile(os.path.join(press, "vetra-press-kit.zip"), "w", zipfile.ZIP_DEFLATED) as kit:
    kit.write(os.path.join(brand, "vetra-logo-1024.png"), "logo/vetra-logo-1024.png")
    kit.write(os.path.join(brand, "vetra-mark-512.png"), "logo/vetra-mark-512.png")
    kit.write(os.path.join(IMG, "brand", "vetra-mark.svg"), "logo/vetra-mark.svg")
    for name in ("develop", "presets", "mask", "depth", "cull", "library"):
        kit.write(os.path.join(SHOTS, name + ".png"), f"screenshots/vetra-{name}.png")
print("press kit", os.path.getsize(os.path.join(press, "vetra-press-kit.zip")) // 1024, "KB")
