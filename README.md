# VETRA website

The public site for VETRA: home, features, download, guide, release notes, support, about and press kit, privacy, terms and open-source licences. Static HTML, one stylesheet, one small script. No cookies, no trackers, no third-party requests.

```
site.json         version, download link, checksum, site and repository addresses
build.py          builds src/ into docs/  (Python 3, standard library only)
src/layout.html   header, navigation and footer shared by every page
src/pages/        one file per page
src/assets/       css, js, screenshots, logo
src/press/        the press kit ZIP
docs/             the built site. This is the folder that gets served
tools/            scripts that made the screenshots and images
```

## Change something

Edit a page in `src/pages/`, or a value in `site.json`, then build:

```bash
python build.py
```

To look at it before publishing:

```bash
python -m http.server 4173 --directory docs
```

and open http://localhost:4173.

## Publish it (GitHub Pages)

The site is set up for a public repository called `vetra` under the GitHub account `lucasbergstrom-prog`, which makes its address https://lucasbergstrom-prog.github.io/vetra/. To use a different account, repository or domain, change `site_url`, `repo_url` and `download_url` in `site.json` and build again.

1. On github.com create a new **public** repository named `vetra`, with no README.
2. Push this folder to it:

   ```bash
   git remote add origin https://github.com/lucasbergstrom-prog/vetra.git
   git push -u origin main
   ```

3. In the repository: **Settings > Pages > Build and deployment**. Source: *Deploy from a branch*. Branch: `main`, folder `/docs`. Save. The site is live a minute or two later.
4. The installer lives in this repository under `downloads/`, stored with Git LFS because it is over GitHub's 100 MB limit for ordinary files. The Download button on the site points at it:

   `https://github.com/lucasbergstrom-prog/vetra/raw/main/downloads/VETRA-7.0-test-Setup.exe`

Git LFS downloads count against the account's monthly LFS bandwidth allowance, and a free account's allowance is small. If the app gets popular, attach the installer to a GitHub release instead (**Releases > Edit**, drop the file on "Attach binaries", **Update release**), which has no such limit, and change `download_url` in `site.json` to:

   `https://github.com/lucasbergstrom-prog/vetra/releases/download/v7.0-test/VETRA-7.0-test-Setup.exe`

## Ship a new version

1. Put the new installer in `downloads/` (Git LFS picks it up), and publish a release on GitHub to announce it.
2. In `site.json` update `version`, `release_date`, `download_url`, `installer_file`, `installer_size`, `installer_bytes` and `installer_sha256`. The checksum comes from:

   ```powershell
   (Get-FileHash .\VETRA-<version>-Setup.exe -Algorithm SHA256).Hash.ToLower()
   ```

3. Add the release to the top of `src/pages/changelog.html`.
4. `python build.py`, commit, push.

## Screenshots

The screenshots are VETRA's own window, rendered at twice normal size from a sandbox profile that holds only stock photos, so nothing from a real library appears in them.

```bash
py -3.11 tools/shots.py <path to vetra.py> <empty sandbox folder> <folder of photos> <output folder> 2
py -3.11 tools/looks.py <path to vetra.py> <sandbox folder> <folder of photos> <looks folder> "estuary.jpg|" "estuary.jpg|Golden Hour"
py -3.11 tools/make_assets.py <output folder> <looks folder>
```

`shots.py` expects the photo names it was written for (`fjord.jpg`, `waterfall.jpg`, `lioness.jpg` and so on); change the names in its scenes to use other photos. The sample photographs are from Unsplash contributors via Lorem Picsum, under the Unsplash licence.

## Before relying on it

- `privacy.html` and `terms.html` are plain-language drafts written from how VETRA behaves. Have them checked before treating them as legal documents.
- "Contact" and "Report a problem" go to the repository's issue tracker. Add an email address in `src/layout.html` and `src/pages/support.html` if you want one.
