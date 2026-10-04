"""Before/after pairs straight from VETRA's own develop pipeline."""
import importlib.util, os, sys
import numpy as np
SRC, SANDBOX, PHOTOS, OUT = (os.path.abspath(p) for p in sys.argv[1:5])
os.environ["USERPROFILE"] = SANDBOX
spec = importlib.util.spec_from_file_location("vetra", SRC)
v = importlib.util.module_from_spec(spec); sys.modules["vetra"] = v; spec.loader.exec_module(v)
from PIL import Image
os.makedirs(OUT, exist_ok=True)

def render(photo, preset, amount=100.0, width=1800):
    im = Image.open(os.path.join(PHOTOS, photo)).convert("RGB")
    im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    arr = np.asarray(im)
    settings = v.preset_settings(v.new_settings(), v.PRESET_INDEX[preset][2], amount) if preset else v.new_settings()
    out = v.develop(arr, settings)
    out = np.asarray(out)
    if out.dtype != np.uint8:
        out = np.clip(out * (255.0 if out.max() <= 1.5 else 1.0), 0, 255).astype(np.uint8)
    return Image.fromarray(out)

pairs = [a.split("|") for a in sys.argv[5:]]
for photo, preset in pairs:
    name = os.path.splitext(photo)[0] + "__" + (preset.lower().replace(" ", "-").replace("&", "and") if preset else "original")
    render(photo, preset or None).save(os.path.join(OUT, name + ".png"))
    print(name, flush=True)
