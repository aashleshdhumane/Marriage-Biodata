# generate_biodata.py
# Data-driven biodata renderer.
# - Add/edit fields in YAML; they appear automatically (no code changes).
# - Preferred "sections:" YAML lets you define any headings and fields in order.
# - If "sections:" not provided, all non-style keys render as a single "DETAILS" section.
# - Borders: image-only (fit|stretch|tile). No fallback vector pattern, no hairline.
# - Ganesha emblem: PNG or "ॐ" (GaneshaMode: image | om | auto)
# - Robust word-wrap; rounded photo (no border)
# - Font sizes + .ttf files configurable in YAML

from __future__ import annotations
import argparse, os
from typing import Dict, Tuple, Any, Optional, Iterable
from PIL import Image, ImageDraw, ImageFont

try:
    import yaml
except ModuleNotFoundError as e:
    raise SystemExit("PyYAML is not installed. Run:  pip install -r requirements.txt") from e


# ----------------------------
# Font helpers
# ----------------------------
def _font_search_paths() -> list[str]:
    paths = []
    paths += [r"C:\Windows\Fonts"]  # Windows
    paths += [  # Linux
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/truetype/noto",
        "/usr/share/fonts/truetype/freefont",
        "/usr/share/fonts/truetype",
        "/usr/share/fonts",
    ]
    paths += ["/System/Library/Fonts", "/System/Library/Fonts/Supplemental", "/Library/Fonts"]  # macOS
    return [p for p in paths if os.path.isdir(p)]


def load_font(font_paths: tuple[str, ...] = (),
              size: int = 32,
              family_fallbacks: tuple[str, ...] = ("DejaVuSans.ttf",)) -> ImageFont.FreeTypeFont:
    expanded: list[str] = []
    for p in font_paths or ():
        if not p:
            continue
        if os.path.isabs(p) or (os.sep in p) or ("/" in p):
            expanded.append(p)
        else:
            for d in _font_search_paths():
                expanded.append(os.path.join(d, p))

    for p in list(font_paths or ()) + expanded:
        if p and os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass

    for fam in family_fallbacks:
        try:
            return ImageFont.truetype(fam, size)
        except Exception:
            pass

    print(f"[WARN] Using ImageFont.load_default() at size={size}. Text size may not change. "
          f"Set FontRegular/FontBold/FontDevanagari in your YAML to real .ttf files.")
    return ImageFont.load_default()


def text_wh(font: ImageFont.FreeTypeFont, text: str) -> tuple[int, int]:
    bb = font.getbbox(text or "")
    return bb[2] - bb[0], bb[3] - bb[1]


# ----------------------------
# Wrapping helpers
# ----------------------------
def wrap_lines(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = str(text).split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip() if line else w
        if text_wh(font, test)[0] > max_w and line:
            lines.append(line)
            line = w
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def draw_label_value_block(draw: ImageDraw.ImageDraw,
                           x_label: int, x_value: int, y: int,
                           label: str, value: str,
                           label_font: ImageFont.FreeTypeFont,
                           value_font: ImageFont.FreeTypeFont,
                           fill_label, fill_value,
                           max_value_w: int, line_space: int) -> int:
    draw.text((x_label, y), label, font=label_font, fill=fill_label)
    lines = wrap_lines(value, value_font, max_value_w)
    line_h = value_font.size
    used_h = max(label_font.size, len(lines) * line_h + (len(lines) - 1) * line_space)
    vy = y
    for i, ln in enumerate(lines):
        draw.text((x_value, vy), ln, font=value_font, fill=fill_value)
        if i < len(lines) - 1:
            vy += line_h + line_space
    return y + used_h + line_space


# ----------------------------
# YAML parsing
# ----------------------------
META_PREFIXES = (
    "Border", "Font", "HeadingSize", "SubheadingSize", "LabelSize",
    "SectionSize", "OmSize", "Ganesha", "__CONTENT_DIR__", "Photo",
)

def parse_yaml(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("Top-level YAML must be a mapping (key: value).")

    # normalize Contact No
    if "Contact No" in data and "Contact No." not in data:
        data["Contact No."] = data.pop("Contact No")

    return data


# ----------------------------
# Borders
# ----------------------------
def _resolve_path(base_dir: str, maybe_path: Optional[str]) -> Optional[str]:
    if not maybe_path:
        return None
    p = str(maybe_path)
    if base_dir and not os.path.isabs(p):
        p = os.path.join(base_dir, p)
    return p


def compute_border_height(img_path: Optional[str], mode: str, height_px: int, canvas_width: int) -> int:
    if not img_path or not os.path.exists(img_path):
        return 0
    mode = (mode or "fit").lower()
    try:
        with Image.open(img_path) as im:
            sw, sh = im.size
    except Exception:
        return 0
    if sh == 0 or sw == 0:
        return 0
    if mode == "fit":
        return max(1, int(sh * (canvas_width / sw)))   # full-width, preserve AR
    return height_px


def draw_border_image(canvas: Image.Image, y: int, img_path: str, height_px: int,
                      mode: str = "fit", flip_vertical: bool = False) -> int:
    if not os.path.exists(img_path):
        return 0
    strip = Image.open(img_path).convert("RGBA")
    if flip_vertical:
        strip = strip.transpose(Image.FLIP_TOP_BOTTOM)

    W, _ = canvas.size
    sw, sh = strip.size
    if sh == 0 or sw == 0:
        return 0

    mode = (mode or "fit").lower()
    if mode == "fit":
        new_h = max(1, int(sh * (W / sw)))
        strip_resized = strip.resize((W, new_h), Image.LANCZOS)
        canvas.paste(strip_resized, (0, y), strip_resized)
        return new_h
    elif mode == "stretch":
        strip_resized = strip.resize((W, height_px), Image.LANCZOS)
        canvas.paste(strip_resized, (0, y), strip_resized)
        return height_px
    else:  # tile
        scale = height_px / sh
        strip_resized = strip.resize((max(1, int(sw * scale)), height_px), Image.LANCZOS)
        x = 0
        while x < W:
            canvas.paste(strip_resized, (x, y), strip_resized)
            x += strip_resized.width
        return height_px


# ----------------------------
# Main drawing
# ----------------------------
def draw_section(draw: ImageDraw.ImageDraw,
                 title: str,
                 fields: Iterable[tuple[str, Any]],
                 x_label: int, x_value: int, y: int,
                 label_font, value_font, section_font,
                 colors, max_value_w: int, line_space: int) -> int:
    c_primary, c_section, c_body = colors
    # Title
    if title:
        draw.text((x_label, y), title, font=section_font, fill=c_section)
        y += section_font.size + int(line_space * 1.5)
    # Fields
    for key, val in fields:
        if val is None:
            continue
        lbl = f"{key} :"
        y = draw_label_value_block(draw, x_label, x_value, y,
                                   lbl, str(val), label_font, value_font,
                                   c_primary, c_body, max_value_w, line_space)
    return y


def draw_biodata(data: Dict[str, Any], output_path: str, image_size: Tuple[int, int]) -> None:
    W, H = image_size
    img = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(img)

    base_h = 1000
    S = max(1.0, H / base_h)

    c_primary = (4, 109, 100)
    c_section = (11, 102, 35)
    c_body = (0, 0, 0)

    content_dir = str(data.get("__CONTENT_DIR__", ""))

    requested_height = int((data.get("BorderHeight") or (56 * S)))
    border_mode = str(data.get("BorderMode") or "fit").lower()
    border_flip_bottom = bool(data.get("BorderFlipBottom") or False)
    border_top_path = _resolve_path(content_dir, data.get("BorderTop"))
    border_bottom_path = _resolve_path(content_dir, data.get("BorderBottom")) or border_top_path

    top_h = compute_border_height(border_top_path, border_mode, requested_height, W)
    bottom_h = compute_border_height(border_bottom_path, border_mode, requested_height, W)

    if top_h > 0:
        draw_border_image(img, 0, border_top_path, requested_height, mode=border_mode, flip_vertical=False)
    if bottom_h > 0:
        draw_border_image(img, H - bottom_h, border_bottom_path, requested_height,
                          mode=border_mode, flip_vertical=border_flip_bottom)

    # Font sizes (YAML overrides)
    HEADING_SZ   = int((data.get("HeadingSize") or 72) * S)
    SUBHEAD_SZ   = int((data.get("SubheadingSize") or 48) * S)
    LABEL_SZ     = int((data.get("LabelSize") or 42) * S)
    SECTION_SZ   = int((data.get("SectionSize") or 48) * S)
    OM_SZ        = int((data.get("OmSize") or 56) * S)
    VALUE_SZ     = LABEL_SZ

    # Optional font files (YAML)
    FR_paths = (str(data.get("FontRegular")),) if data.get("FontRegular") else ()
    FB_paths = (str(data.get("FontBold")),) if data.get("FontBold") else ()
    FD_paths = (str(data.get("FontDevanagari")),) if data.get("FontDevanagari") else ()

    heading_font    = load_font(FB_paths, HEADING_SZ,   ("DejaVuSerif-Bold.ttf","Arial Bold.ttf","DejaVuSans-Bold.ttf"))
    subheading_font = load_font(FR_paths, SUBHEAD_SZ,   ("DejaVuSans.ttf","Arial.ttf","Helvetica.ttc"))
    label_font      = load_font(FR_paths, LABEL_SZ,     ("DejaVuSans.ttf","Arial.ttf","Helvetica.ttc"))
    value_font      = load_font(FR_paths, VALUE_SZ,     ("DejaVuSans.ttf","Arial.ttf","Helvetica.ttc"))
    section_font    = load_font(FB_paths, SECTION_SZ,   ("DejaVuSans-Bold.ttf","Arial Bold.ttf","DejaVuSans.ttf"))
    om_font         = load_font(FD_paths, OM_SZ,        ("NotoSansDevanagari-Regular.ttf","Nirmala.ttf","Mangal.ttf","DejaVuSans.ttf"))

    # Ganesha emblem
    y = top_h + int(12 * S)
    badge_d = int(160 * S)
    cx = W // 2
    cy = y + badge_d // 2

    gm = str(data.get("GaneshaMode") or "auto").lower()  # om | image | auto
    placed_ganesha = False
    if gm in ("image", "auto"):
        if data.get("GaneshaImage"):
            path = _resolve_path(content_dir, data["GaneshaImage"])
            if path and os.path.exists(path):
                try:
                    g_im = Image.open(path).convert("RGBA").resize((badge_d, badge_d), Image.LANCZOS)
                    bg = Image.new("RGBA", (badge_d, badge_d), "WHITE")
                    bg.paste(g_im, (0, 0), g_im)
                    img.paste(bg, (cx - badge_d // 2, cy - badge_d // 2), bg)
                    placed_ganesha = True
                except Exception:
                    placed_ganesha = False
    if (gm == "om") or (not placed_ganesha):
        om = "ॐ"
        ow, oh = text_wh(om_font, om)
        draw.text((cx - ow // 2, cy - oh // 2), om, font=om_font, fill=(226, 108, 10))

    # Headings
    y = cy + badge_d // 2 + int(6 * S)
    title = "|| SHREE GANESHAYA NAMAH ||"
    tw, th = text_wh(heading_font, title)
    draw.text((W / 2 - tw / 2, y), title, font=heading_font, fill=c_primary)
    y += th + int(6 * S)
    sub = "BIODATA"
    sw, sh = text_wh(subheading_font, sub)
    draw.text((W / 2 - sw / 2, y), sub, font=subheading_font, fill=c_primary)
    y += sh + int(18 * S)

    # Layout
    margin_x = int(44 * S)
    col_gap  = int(22 * S)
    photo_w  = int(210 * S)
    photo_h  = int(260 * S)
    text_w   = W - margin_x * 2 - col_gap - photo_w
    photo_x  = margin_x + text_w + col_gap
    photo_y  = y

    x_label = margin_x
    line_space = int(8 * S)

    # Compute max label width by looking at keys that will be rendered
    # Gather fields by section order
    sections = data.get("sections")
    field_groups: list[tuple[str, list[tuple[str, Any]]]] = []

    meta_keys = {k for k in data.keys() if k.startswith(META_PREFIXES)}
    meta_keys.update({"sections"})  # reserved

    if isinstance(sections, dict) and sections:
        # preserve YAML order
        for sec_title, mapping in sections.items():
            if not isinstance(mapping, dict) or not mapping:
                continue
            # list of (key, value) preserving YAML order
            items = [(k, v) for k, v in mapping.items()]
            field_groups.append((str(sec_title), items))
    else:
        # flat mode: everything not meta goes into one section
        items = [(k, v) for k, v in data.items() if k not in meta_keys]
        field_groups.append(("DETAILS", items))

    # compute label width across all fields
    all_labels = []
    for _, items in field_groups:
        for k, v in items:
            all_labels.append(f"{k} :")
    max_label = max((text_wh(label_font, l)[0] for l in all_labels), default=0)
    x_value = x_label + max_label + int(14 * S)
    max_value_w = W - x_value - margin_x

    # Render sections
    colors = (c_primary, c_section, c_body)
    yt = y
    for i, (sec_title, items) in enumerate(field_groups):
        # add top padding between sections (except first)
        if i > 0:
            yt += int(12 * S)
        yt = draw_section(draw, sec_title if sec_title else "", items,
                          x_label, x_value, yt, label_font, value_font, section_font,
                          colors, max_value_w, line_space)

    # Photo
    photo = None
    if data.get("Photo"):
        p = _resolve_path(content_dir, data["Photo"])
        if p and os.path.exists(p):
            try:
                photo = Image.open(p).convert("RGB")
            except Exception:
                photo = None

    if photo:
        pw, ph = photo.size
        scale = min(photo_w / pw, photo_h / ph)
        nw, nh = int(pw * scale), int(ph * scale)
        photo = photo.resize((nw, nh), Image.LANCZOS)
        px = photo_x + (photo_w - nw) // 2
        py = photo_y + (photo_h - nh) // 2
        radius = max(10, int(14 * S))
        mask = Image.new("L", (nw, nh), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, nw, nh], radius=radius, fill=255)
        img.paste(photo, (px, py), mask)

    img.save(output_path)


# ----------------------------
# CLI
# ----------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Generate a decorative biodata card from a YAML file.")
    ap.add_argument("--content", required=True, help="Path to YAML (e.g., my_biodata.yaml).")
    ap.add_argument("--output", default="my_biodata.png", help="Output image filename.")
    ap.add_argument("--size", default="900x1275", help="WIDTHxHEIGHT (e.g., 794x1123, 1240x1754, 2480x3508).")
    args = ap.parse_args()

    try:
        w_str, h_str = args.size.lower().split("x")
        size = (int(w_str), int(h_str))
    except Exception:
        raise ValueError("Invalid --size. Use WIDTHxHEIGHT, e.g., 1240x1754")

    content_path = os.path.abspath(args.content)
    data = parse_yaml(content_path)
    data["__CONTENT_DIR__"] = os.path.dirname(content_path)

    draw_biodata(data, args.output, image_size=size)


if __name__ == "__main__":
    main()
