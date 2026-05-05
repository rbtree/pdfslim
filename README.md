# pdfslim

macOS Finder Services that compress PDFs (especially iPhone Notes scans)
using Ghostscript. Free alternative to PDF Squeezer.

## Install (recommended)

Two double-clicks, no Terminal:

1. **Ghostscript**: download the signed [Ghostscript installer](https://pages.uoregon.edu/koch/Ghostscript-10.07.0.pkg) (47 MB; maintained by Richard Koch as part of MacTeX) and double-click.
2. **pdfslim**: download the latest `pdfslim-X.Y.Z.pkg` from [Releases](https://github.com/rbtree/pdfslim/releases/latest) and double-click.

Both installers are signed and notarized, so Gatekeeper accepts them without warnings.

## Install from source

```bash
brew install ghostscript
git clone git@github.com:rbtree/pdfslim.git
cd pdfslim
./install.sh
```

## Use

Right-click any PDF in Finder, choose **Services**:

- **PDF Slim - Light (Print, 300dpi)** - Ghostscript `/printer` preset; ~89% reduction, color preserved, archival quality
- **PDF Slim - Medium (eBook, 150dpi)** - Ghostscript `/ebook` preset; ~94% reduction, color preserved, sweet spot

The compressed file appears alongside the original with a `_light` or
`_medium` suffix. Original is never modified.

## Update

If you installed via `.pkg`, download the new release and double-click; the installer overwrites the previous version in place.

If you installed from source:

```bash
cd pdfslim
git pull
./install.sh
```

## Uninstall

If you installed via `.pkg`:

```bash
sudo pdfslim-uninstall
```

If you installed from source:

```bash
cd pdfslim
./uninstall.sh
```

## Requirements

- macOS 12 or later
- Ghostscript (`brew install ghostscript`)
- Python 3 (only for `install.sh`; ships with macOS)

## License

pdfslim is released under the [MIT License](LICENSE).

pdfslim invokes Ghostscript as a separate program via subprocess; it does
not bundle, link to, or distribute Ghostscript itself. Ghostscript is an
independent project licensed by Artifex Software under the
[AGPLv3](https://www.gnu.org/licenses/agpl-3.0.html) (free) or a
[commercial license](https://artifex.com/licensing/). When you install
Ghostscript via `brew install ghostscript` you agree to its license terms,
which apply to your use of `gs` regardless of pdfslim.
