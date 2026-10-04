"""Render VETRA's own interface for the website's screenshots.

Runs vetra.py in a sandbox profile (its own empty library, nothing from the
real one), drives it through its own methods and saves what its window draws.

    py -3.11 shots.py <vetra.py> <sandbox dir> <photo folder> <out dir> [scale] [only,names]
"""
import ctypes
import importlib.util
import json
import os
import sys
import time
import traceback
from ctypes import wintypes

SRC, SANDBOX, PHOTOS, OUT = (os.path.abspath(p) for p in sys.argv[1:5])
SCALE = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
ONLY = set(sys.argv[6].split(",")) if len(sys.argv) > 6 else None

os.makedirs(SANDBOX, exist_ok=True)
os.makedirs(OUT, exist_ok=True)
import glob
import shutil
for stale in glob.glob(os.path.join(PHOTOS, "*.vetra.json")):
    os.remove(stale)
for stale in ("catalog.json", "history", "inbox", "running.flag"):
    full = os.path.join(SANDBOX, ".vetra", stale)
    if os.path.isdir(full):
        shutil.rmtree(full, ignore_errors=True)
    elif os.path.exists(full):
        os.remove(full)
os.environ["USERPROFILE"] = SANDBOX          # "~" is the sandbox from here on
os.environ.pop("HOME", None)

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    ctypes.windll.user32.SetProcessDPIAware()

spec = importlib.util.spec_from_file_location("vetra", SRC)
v = importlib.util.module_from_spec(spec)
sys.modules["vetra"] = v
spec.loader.exec_module(v)
assert os.path.normcase(v.APP_DIR).startswith(os.path.normcase(SANDBOX)), v.APP_DIR

from PIL import Image, ImageGrab  # noqa: E402

user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
user32.GetParent.restype = wintypes.HWND
user32.GetParent.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC
user32.GetDC.argtypes = [wintypes.HWND]
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.PrintWindow.argtypes = [wintypes.HWND, wintypes.HDC, wintypes.UINT]
gdi32.CreateCompatibleDC.restype = wintypes.HDC
gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleBitmap.restype = wintypes.HBITMAP
gdi32.CreateCompatibleBitmap.argtypes = [wintypes.HDC, ctypes.c_int, ctypes.c_int]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteDC.argtypes = [wintypes.HDC]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG), ("biHeight", wintypes.LONG),
                ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, ctypes.c_void_p,
                            ctypes.POINTER(BITMAPINFOHEADER), wintypes.UINT]


def print_window(win):
    """What a Tk toplevel draws in its client area, straight from the window."""
    hwnd = user32.GetParent(win.winfo_id()) or win.winfo_id()
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = rect.right, rect.bottom
    hdc = user32.GetDC(hwnd)
    mdc = gdi32.CreateCompatibleDC(hdc)
    bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
    old = gdi32.SelectObject(mdc, bmp)
    ok = user32.PrintWindow(hwnd, mdc, 1 | 2)           # client only, full content
    header = BITMAPINFOHEADER(ctypes.sizeof(BITMAPINFOHEADER), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(mdc, bmp, 0, h, buf, ctypes.byref(header), 0)
    gdi32.SelectObject(mdc, old)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(mdc)
    user32.ReleaseDC(hwnd, hdc)
    image = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    return image if ok else None


def unhover(win):
    """The real pointer sits somewhere over the window: clear the hover state it causes."""
    try:
        widget = win.winfo_containing(*win.winfo_pointerxy())
    except Exception:
        widget = None
    while widget is not None:
        try:
            widget.event_generate("<Leave>")
        except Exception:
            pass
        widget = getattr(widget, "master", None)
    try:
        v.Tooltip.hide_all()
    except Exception:
        pass
    for _ in range(3):
        win.update_idletasks()
        win.update()


def print_tiled(win):
    """A window larger than the screen only draws the part that is on screen:
    slide it around, take what is drawn each time and stitch the pieces."""
    win.update()
    cw, ch = win.winfo_width(), win.winfo_height()
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    bx, by = win.winfo_rootx() - win.winfo_x(), win.winfo_rooty() - win.winfo_y()
    if cw + bx <= sw and ch + by <= sh:
        unhover(win)
        return print_window(win)
    home = (win.winfo_x(), win.winfo_y())
    full = Image.new("RGB", (cw, ch))
    step_x, step_y = sw - 160, sh - 200
    oy = 0
    while True:
        ox = 0
        while True:
            win.geometry(f"+{-ox - bx + 40}+{-oy - by + 40}")
            pump(0.5)
            unhover(win)
            tile = print_window(win)
            x0, y0 = win.winfo_rootx(), win.winfo_rooty()        # where the client area really landed
            box = (max(-x0, 0), max(-y0, 0), min(sw - x0, cw), min(sh - y0, ch))
            full.paste(tile.crop(box), (box[0], box[1]))
            if ox + step_x >= cw - 80:
                break
            ox = min(ox + step_x, cw - 80)
        if oy + step_y >= ch - 80:
            break
        oy = min(oy + step_y, ch - 80)
    win.geometry(f"+{home[0]}+{home[1]}")
    pump(0.3)
    return full


def is_blank(image):
    small = image.resize((64, 64))
    lo, hi = small.convert("L").getextrema()
    return hi - lo < 12


root = v.tk.Tk()
root.withdraw()
root.tk.call("tk", "scaling", SCALE * 96.0 / 72.0)
v.start_logging()
app = v.Vetra(root)
v.dark_title_bar(root)
W, H = int(1500 * SCALE), int(940 * SCALE)
root.maxsize(W + 400, H + 400)
root.geometry(f"{W}x{H}+0+0")
root.deiconify()
root.lift()
root.attributes("-topmost", True)


def pump(seconds, until=None):
    end = time.time() + seconds
    while time.time() < end:
        root.update()
        if until is not None and until():
            return True
        time.sleep(0.01)
    return until is None


def settle(seconds=2.5):
    pump(60, lambda: app.ready and not getattr(app, "_loading", False))
    pump(seconds)


def rect_of(widget):
    try:
        return [widget.winfo_rootx() - root.winfo_rootx(), widget.winfo_rooty() - root.winfo_rooty(),
                widget.winfo_width(), widget.winfo_height()]
    except Exception:
        return None


def save(name, win=None):
    win = win or root
    pump(0.4)
    image = print_tiled(win) if win is root else print_window(win)
    how = "PrintWindow"
    if image is None or is_blank(image):
        x, y = win.winfo_rootx(), win.winfo_rooty()
        image = ImageGrab.grab(bbox=(x, y, x + win.winfo_width(), y + win.winfo_height()), all_screens=True)
        how = "ImageGrab"
    path = os.path.join(OUT, name + ".png")
    image.save(path)
    if win is root:
        parts = {}
        for key in ("left_panel", "panel_scroll", "image_canvas", "timeline_canvas", "filmstrip_canvas",
                    "hist_canvas", "histogram", "preset_browser", "develop_view", "library_view"):
            widget = getattr(app, key, None)
            if widget is not None:
                parts[key] = rect_of(widget)
        with open(os.path.join(OUT, name + ".json"), "w") as f:
            json.dump({"size": image.size, "scale": SCALE, "parts": parts}, f, indent=1)
    print(f"saved {name}.png {image.size} via {how}", flush=True)


def photo(name):
    return v.canon(os.path.join(PHOTOS, name))


def slider(key, value):
    app.sliders[key].set(value)
    app._on_slider_change(key, value)
    app._on_slider_release()
    pump(0.3)


def open_groups(*names):
    app.preset_browser.open = set(names)
    app.preset_browser.redraw()


def develop(name):
    app.show_module("develop")
    app.select(photo(name))
    settle()
    app.zoom_fit()
    app.draw_rating()
    settle(1.0)


def scene(name):
    return ONLY is None or name in ONLY


def run(name, fn):
    if not scene(name):
        return
    try:
        fn()
    except Exception:
        print(f"!! {name} failed", flush=True)
        traceback.print_exc()


# ---------------------------------------------------------------- the library
pump(1.0)
app.set_pref("tour_done", True)
app.load_folder(PHOTOS)
pump(6.0)                                   # thumbnails
stars = {"fjord.jpg": 5, "waterfall.jpg": 5, "lioness.jpg": 4, "peaks.jpg": 4, "lighthouse.jpg": 3,
         "wheat.jpg": 4, "city-night.jpg": 5, "strawberries.jpg": 3, "bay.jpg": 3}
for file, rating in stars.items():
    app.set_rating([photo(file)], rating)
app.set_flag([photo(n) for n in ("fjord.jpg", "waterfall.jpg", "lioness.jpg", "city-night.jpg", "wheat.jpg")], 1)
app.set_flag([photo("beach.jpg")], -1)
pump(1.0)
print("categories:", sorted({c for c, _, _ in v.PRESET_INDEX.values()}), flush=True)
print("library:", len(app.view_paths), "photos; presets open:", sorted(app.preset_browser.open), flush=True)


def hero():
    develop("fjord.jpg")
    open_groups("Landscape")
    app._preset_clicked("Epic Landscape", 60.0)
    settle(2.0)
    slider("highlights", -24.0)
    slider("shadows", 18.0)
    slider("clarity", 8.0)
    settle(3.0)
    save("develop")


def presets():
    develop("wheat.jpg")
    open_groups("Film")
    names = [n for n in v.PRESET_INDEX if v.PRESET_INDEX[n][0] == "Film"] if isinstance(
        next(iter(v.PRESET_INDEX.values())), (list, tuple)) else []
    print("film presets:", names[:14], flush=True)
    app._preset_clicked(names[0] if names else "Golden Hour")
    settle(3.0)
    save("presets")


def mask():
    develop("lioness.jpg")
    open_groups("Portrait")
    slider("contrast", 10.0)
    app.add_mask("subject")
    pump(240, lambda: not app._detecting)
    settle(3.0)
    save("mask")
    current = app.find_mask(app.active_mask_id) if app.active_mask_id else None
    print("mask:", {k: current.get(k) for k in ("type", "detected", "found")} if current else None, flush=True)


def depth():
    develop("waterfall.jpg")
    open_groups("Landscape")
    app.expand_section("lensblur")
    app.apply_lens_blur_auto()
    pump(240, lambda: "__lens__" not in app._detecting)
    settle(3.0)
    app.expand_section("lensblur")
    save("lens-blur")
    app.lens_visual_toggle.set(True)
    app._set_lens_visualize(True)
    settle(3.0)
    save("depth")
    app.lens_visual_toggle.set(False)
    app._set_lens_visualize(False)
    pump(0.5)


def colour():
    develop("bay.jpg")
    open_groups("Cinematic")
    names = [n for n, e in v.PRESET_INDEX.items() if e[0] == "Cinematic"]
    app._preset_clicked(names[0], 80.0)
    settle(2.0)
    for key in ("basic", "crop", "heal", "lensblur", "masks", "detail", "effects"):
        section = app.sections.get(key)
        if section is not None:
            section.toggle(state=False)
    for key in ("curve", "mixer", "grading"):
        section = app.sections.get(key)
        if section is not None:
            section.toggle(state=True)
    pump(0.5)
    app.panel_scroll.canvas.yview_moveto(0.0)
    settle(2.0)
    save("colour")
    for key in ("curve", "mixer", "grading"):
        app.sections[key].toggle(state=False)
    app.sections["basic"].toggle(state=True)
    pump(0.5)


def cull():
    app.selection = [photo("city-night.jpg")]
    app.show_module("cull")
    pump(4.0)
    save("cull")


def library():
    app.selection = []
    app.show_module("library")
    pump(4.0)
    save("library")


def export():
    app.selection = [photo(n) for n in ("fjord.jpg", "waterfall.jpg", "lioness.jpg", "wheat.jpg", "city-night.jpg")]
    app.show_module("library")
    pump(1.0)

    def snap():
        for child in root.winfo_children():
            if isinstance(child, v.ExportDialog):
                pump(0.6)
                save("export-dialog", child)
                save("export")
                child.destroy()
                return
        root.after(300, snap)
    root.after(1200, snap)
    v.ExportDialog(root, len(app.selection), app.pref("export_options"), app.export_places(), False)


run("develop", hero)
run("presets", presets)
run("mask", mask)
run("depth", depth)
run("colour", colour)
run("cull", cull)
run("library", library)
run("export", export)

for size in (1024, 512, 192, 180, 64, 32):
    v.logo_image(size).save(os.path.join(OUT, f"logo-{size}.png"))
v.logo_image(512, tile=False).save(os.path.join(OUT, "mark-512.png"))
print("done", flush=True)
try:
    root.destroy()
except Exception:
    pass
os._exit(0)
