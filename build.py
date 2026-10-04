"""Build the VETRA website:  python build.py

Reads site.json, src/layout.html and src/pages/*.html and writes the finished
site to docs/ (the folder GitHub Pages serves). Standard library only.

A page starts with a few "key: value" lines, then a line of three dashes, then
its HTML. Inside any page or the layout:

    {{name}}          a value from site.json or the page's own keys
    {{icon:name}}     an inline SVG icon from ICONS below
    {{active:key}}    marks the navigation link of the current page
"""
import datetime
import hashlib
import html
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "docs")

# 24 x 24, drawn with a 1.6 px stroke
ICONS = {
    "download": '<path d="M12 4v11"/><path d="m7.5 10.5 4.5 4.5 4.5-4.5"/><path d="M5 19h14"/>',
    "arrow": '<path d="M5 12h14"/><path d="m13 6 6 6-6 6"/>',
    "lock": '<rect x="5" y="10.5" width="14" height="9.5" rx="2"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>',
    "layers": '<path d="m12 4 8.5 4.5L12 13 3.5 8.5z"/><path d="m3.5 12.5 8.5 4.5 8.5-4.5"/><path d="m3.5 16.5 8.5 4.5 8.5-4.5"/>',
    "history": '<path d="M4 12a8 8 0 1 0 2.6-5.9"/><path d="M4 4.5V9h4.5"/><path d="M12 8v4.5l3 1.8"/>',
    "sliders": '<path d="M4 7h9"/><path d="M17 7h3"/><circle cx="15" cy="7" r="2"/><path d="M4 17h3"/><path d="M11 17h9"/><circle cx="9" cy="17" r="2"/>',
    "wand": '<path d="m4 20 11-11"/><path d="m14 6 4 4"/><path d="M18 3v3"/><path d="M16.5 4.5h3"/><path d="M20 12v2"/><path d="M19 13h2"/><path d="M8 4v2"/><path d="M7 5h2"/>',
    "aperture": '<circle cx="12" cy="12" r="8.5"/><path d="m14.5 3.9-4.2 7.3"/><path d="M20.4 10.5h-8.4"/><path d="m18 18-4.2-7.3"/><path d="m9.5 20.1 4.2-7.3"/><path d="M3.6 13.5H12"/><path d="m6 6 4.2 7.3"/>',
    "mask": '<circle cx="12" cy="12" r="8.5" stroke-dasharray="2.4 2.4"/><circle cx="12" cy="12" r="3.5"/>',
    "raw": '<rect x="3.5" y="6.5" width="17" height="12" rx="2"/><circle cx="12" cy="12.5" r="3.2"/><path d="M8 6.5 9.2 4.5h5.6L16 6.5"/>',
    "flag": '<path d="M6 21V4"/><path d="M6 4.5h11l-2.2 3.7L17 12H6"/>',
    "grid": '<rect x="4" y="4" width="6.5" height="6.5" rx="1.2"/><rect x="13.5" y="4" width="6.5" height="6.5" rx="1.2"/><rect x="4" y="13.5" width="6.5" height="6.5" rx="1.2"/><rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.2"/>',
    "keyboard": '<rect x="3" y="6.5" width="18" height="11" rx="2"/><path d="M7 10.5h.01M10.5 10.5h.01M14 10.5h.01M17.5 10.5h.01M7.5 14h9"/>',
    "compass": '<circle cx="12" cy="12" r="8.5"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
    "offline": '<path d="M4.5 9.5a11 11 0 0 1 15 0"/><path d="M7.5 13a6.5 6.5 0 0 1 9 0"/><circle cx="12" cy="17" r="1.2"/><path d="m4 4 16 16"/>',
    "copy": '<rect x="8.5" y="8.5" width="11" height="11" rx="2"/><path d="M15.5 8.5V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7.5a2 2 0 0 0 2 2h2.5"/>',
    "histogram": '<path d="M4 20V10"/><path d="M8 20V6"/><path d="M12 20v-9"/><path d="M16 20V4"/><path d="M20 20v-7"/>',
    "split": '<rect x="3.5" y="5" width="17" height="14" rx="2"/><path d="M12 3v18"/>',
    "laptop": '<rect x="5" y="5" width="14" height="10" rx="1.5"/><path d="M3 19h18"/>',
    "export": '<path d="M12 15V4"/><path d="m7.5 8.5 4.5-4.5 4.5 4.5"/><path d="M5 13v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5"/>',
    "shield": '<path d="M12 3.5 5 6v5.5c0 4.2 2.9 7.6 7 9 4.1-1.4 7-4.8 7-9V6z"/><path d="m9 12 2.2 2.2L15 10.4"/>',
    "drive": '<rect x="3.5" y="13" width="17" height="6.5" rx="2"/><path d="M6 13 8 5h8l2 8"/><path d="M7.5 16.3h.01"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "menu": '<path d="M4 7h16"/><path d="M4 12h16"/><path d="M4 17h16"/>',
    "external": '<path d="M14 5h5v5"/><path d="m19 5-8 8"/><path d="M18 14v4a1.5 1.5 0 0 1-1.5 1.5h-10A1.5 1.5 0 0 1 5 18V7.5A1.5 1.5 0 0 1 6.5 6H10"/>',
    "crop": '<path d="M7 3v14h14"/><path d="M3 7h14v14"/>',
    "heal": '<circle cx="12" cy="12" r="8.5"/><path d="M12 8.5v7"/><path d="M8.5 12h7"/>',
    "curve": '<path d="M4 20V4"/><path d="M4 20h16"/><path d="M4 20c6-1 8-12 16-15"/>',
    "palette": '<path d="M12 3.5a8.5 8.5 0 1 0 0 17c1.4 0 2-1 2-2 0-1.6-1-2 0-3.2 1-1.1 6.500 .7 6.500-3.800A8.500 8.500 0 0 0 12 3.500z"/><circle cx="8" cy="11" r="1"/><circle cx="11" cy="7.500" r="1"/><circle cx="15.500" cy="8.500" r="1"/>',
    "backup": '<path d="M7 18.500a4.500 4.500 0 0 1-.6-8.960 6 6 0 0 1 11.500 1.500A3.800 3.800 0 0 1 17.500 18.500"/><path d="M12 12v8"/><path d="m9 15 3-3 3 3"/>',
    "star": '<path d="m12 4 2.400 5 5.500.700-4 3.800 1 5.500L12 16.300 7.100 19l1-5.500-4-3.800 5.500-.700z"/>',
}


def icon(name):
    body = ICONS.get(name)
    if body is None:
        raise KeyError(f"no icon called {name!r}")
    return ('<svg class="icon" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{body}</svg>')


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def fill(text, values, page_key):
    def swap(match):
        token = match.group(1).strip()
        if token.startswith("icon:"):
            return icon(token[5:])
        if token.startswith("active:"):
            return ' aria-current="page"' if token[7:] == page_key else ""
        if token not in values:
            raise KeyError(f"{{{{{token}}}}} is not defined (page {page_key})")
        return str(values[token])
    previous = None
    while previous != text:                 # values may themselves contain tokens
        previous, text = text, re.sub(r"\{\{([^{}]+)\}\}", swap, text)
    return text


def parse_page(text):
    head, _, body = text.partition("\n---\n")
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


def main():
    config = json.loads(read(os.path.join(ROOT, "site.json")))
    config["site_url"] = config["site_url"].rstrip("/") + "/"
    config["year"] = datetime.date.today().year
    config["issues_url"] = config["repo_url"] + "/issues"
    config["new_issue_url"] = config["repo_url"] + "/issues/new"
    config["releases_url"] = config["repo_url"] + "/releases"

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(os.path.join(SRC, "assets"), os.path.join(OUT, "assets"))
    shutil.copytree(os.path.join(SRC, "press"), os.path.join(OUT, "press"))
    for name in ("favicon.ico", "third-party-notices.txt"):
        shutil.copy2(os.path.join(SRC, name), os.path.join(OUT, name))

    stamp = hashlib.sha1()
    for name in ("css/site.css", "js/site.js"):
        stamp.update(read(os.path.join(SRC, "assets", name)).encode("utf-8"))
    config["asset_version"] = stamp.hexdigest()[:8]
    config["notices_text"] = html.escape(read(os.path.join(SRC, "third-party-notices.txt")))

    layout = read(os.path.join(SRC, "layout.html"))
    pages = []
    for file in sorted(os.listdir(os.path.join(SRC, "pages"))):
        if not file.endswith(".html"):
            continue
        meta, body = parse_page(read(os.path.join(SRC, "pages", file)))
        key = file[:-5]
        values = dict(config)
        values.update(meta)
        values["page_file"] = "" if key == "index" else file
        values["canonical"] = config["site_url"] + values["page_file"]
        values["body_class"] = meta.get("body_class", "")
        values["og_title"] = meta.get("og_title", meta["title"])
        values["base_tag"] = ('<base href="' + config["site_url"] + '">\n') if meta.get("base") == "site" else ""
        values["content"] = body
        write(os.path.join(OUT, file), fill(layout, values, meta.get("nav", key)))
        if meta.get("index", "yes") != "no":
            pages.append((values["canonical"], meta.get("priority", "0.6")))

    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority in pages:
        sitemap.append(f"  <url><loc>{url}</loc><lastmod>{config['updated_iso']}</lastmod>"
                       f"<priority>{priority}</priority></url>")
    sitemap.append("</urlset>")
    write(os.path.join(OUT, "sitemap.xml"), "\n".join(sitemap) + "\n")
    write(os.path.join(OUT, "robots.txt"), f"User-agent: *\nAllow: /\n\nSitemap: {config['site_url']}sitemap.xml\n")
    write(os.path.join(OUT, ".nojekyll"), "")
    write(os.path.join(OUT, "site.webmanifest"), json.dumps({
        "name": "VETRA", "short_name": "VETRA", "description": config["tagline"],
        "start_url": "./", "display": "browser", "background_color": "#0b0b0a", "theme_color": "#0b0b0a",
        "icons": [{"src": "assets/img/brand/icon-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "assets/img/brand/icon-512.png", "sizes": "512x512", "type": "image/png"}],
    }, indent=2) + "\n")

    total = sum(os.path.getsize(os.path.join(folder, name))
                for folder, _, names in os.walk(OUT) for name in names)
    print(f"built {len(os.listdir(os.path.join(SRC, 'pages')))} pages into docs/  ({total / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
