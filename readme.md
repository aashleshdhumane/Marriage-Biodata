# Biodata Generator

Create a clean, printable **biodata** image (PNG) from a single **YAML** file.
The layout supports your own top/bottom border strips, a Ganesha emblem (PNG or “ॐ”), a rounded-corner photo, and fully **data-driven sections** so you can add fields without touching Python.

---

## Features

* **Data-driven**: add/edit fields in `my_biodata.yaml`; they render automatically.
* **Sections**: define any number of sections in the order you want.
* **Borders**: use your own strip images top/bottom (`fit`, `tile`, or `stretch`).
* **Ganesha emblem**: choose PNG or the “ॐ” glyph (`GaneshaMode`).
* **Photo**: optional, pasted with rounded corners (no border).
* **Typography**: change text sizes in YAML; optionally supply your own TTF fonts.
* **No fallback art**: if you don’t provide border images, the page stays clean.

---

## Quick Start

1. **Install Python deps**

```bash
pip install -r requirements.txt
```

2. **Prepare inputs**

* `my_biodata.yaml` (see the example below)
* Optional images in the same folder:

  * `my_border.png` (and optionally `my_bottom.png`)
  * `ganesha.png`
  * `my_photo.jpg`

3. **Generate**

```bash
python generate_biodata.py --content my_biodata.yaml --output my_biodata.png --size 1240x1754
```

* `--size` is `WIDTHxHEIGHT` in **pixels**.
  Common choices:

  * A4 @ 96 DPI: `794x1123`
  * A4 @ 150 DPI: `1240x1754`
  * A4 @ 300 DPI (print-ready): `2480x3508`

---

## YAML: Recommended “sections” Mode

You control headings and fields (and their order) under `sections:`. Anything you put there appears in the final image—no code changes needed.

```yaml
sections:
  BASIC DETAILS:
    Name: Iron Man Goswami
    Date of Birth: 14/03/1998
    Time of Birth: 06:38 AM
    Place of Birth: Nagpur, MH, IND
    etc...
```

### Flat Mode (optional)

If you **omit** the entire `sections:` block, the script renders **all non-style keys** (everything except `Border*`, `Font*`, `Ganesha*`, `Photo`, and the size keys) as a single section named “DETAILS”.

---

## Command Examples

Generate an A4 @ 300 DPI image:

```bash
python generate_biodata.py --content my_biodata.yaml --output biodata_a4_300dpi.png --size 2480x3508
```

Use a different YAML:

```bash
python generate_biodata.py --content bride.yaml --output bride.png --size 1240x1754
```

---

## Requirements

`requirements.txt`:

```
Pillow>=10
PyYAML>=6
```

Install:

```bash
pip install -r requirements.txt
```

---

## Windows one-click (optional)

Create `run.bat` next to the script:

```bat
@echo off
REM Change these if you use different files
set CONTENT=my_biodata.yaml
set OUTPUT=my_biodata.png
set SIZE=1240x1754

python "%~dp0generate_biodata.py" --content "%CONTENT%" --output "%OUTPUT%" --size %SIZE%
pause
```

Double-click `run.bat`.

---

## Tips & Gotchas

* **Fonts not scaling?**
  If you see warnings like `Using ImageFont.load_default()…`, Pillow didn’t load a TTF.
  Set `FontRegular`, `FontBold`, and `FontDevanagari` in YAML to real `.ttf` files.

* **Borders look cropped left/right?**
  Use `BorderMode: fit`. It scales the strip proportionally to the full page width.

* **Bottom strip upside down?**
  Set `BorderFlipBottom: true`.

* **Always show “ॐ” instead of PNG?**
  Set `GaneshaMode: om` and ensure `FontDevanagari` points to a TTF with the Om glyph (e.g., `Nirmala.ttf` or `NotoSansDevanagari-Regular.ttf`).

* **Add new fields**
  Just place them under the section you want in YAML. They’ll appear automatically.

---

## License

Personal use permitted. Replace fonts and images with assets you have the rights to use.
