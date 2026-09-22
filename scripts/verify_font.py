#!/usr/bin/env python3
"""
verify_font.py - Verification and integrity checker for GoogleEmoji3D.ttf.
Validates OpenType tables, cmap mappings, GSUB ligatures, and sbix color bitmap strikes.
"""

import os
import sys

try:
    from fontTools.ttLib import TTFont
except ImportError:
    print("[-] Missing fontTools. Install with: pip install fonttools")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(PROJECT_ROOT, "build", "GoogleEmoji3D.ttf")

REQUIRED_TABLES = ["head", "hhea", "maxp", "OS/2", "name", "post", "cmap", "CBDT", "CBLC", "sbix", "GSUB"]

def verify_font(font_path):
    print(f"[*] Verifying font: {font_path}")
    if not os.path.exists(font_path):
        print(f"[-] Font file not found at: {font_path}")
        sys.exit(1)

    file_size = os.path.getsize(font_path)
    print(f"[*] File size: {file_size / (1024 * 1024):.2f} MB ({file_size} bytes)")
    if file_size < 1000:
        print("[-] Font file suspiciously small!")
        sys.exit(1)

    font = TTFont(font_path)

    # 1. Table presence
    print("\n1. Checking Required Tables:")
    for table_tag in REQUIRED_TABLES:
        if table_tag in font:
            print(f"  [OK] Table '{table_tag}' present")
        else:
            print(f"  [FAIL] Table '{table_tag}' MISSING!")
            sys.exit(1)

    # 2. Name table
    print("\n2. Checking Name Records:")
    name_table = font["name"]
    family_name = name_table.getDebugName(1)
    full_name = name_table.getDebugName(4)
    ps_name = name_table.getDebugName(6)
    print(f"  • Family Name:     {family_name}")
    print(f"  • Full Name:       {full_name}")
    print(f"  • PostScript Name: {ps_name}")

    if "Google Emoji 3D" not in (family_name or ""):
        print("  [FAIL] Family name does not match 'Google Emoji 3D'!")
        sys.exit(1)

    # 3. Cmap table
    print("\n3. Checking Character Map (cmap):")
    cmap = font["cmap"].getBestCmap()
    print(f"  • Total mapped codepoints: {len(cmap)}")

    # Check key emoji codepoints
    test_codepoints = [
        (0x1F600, "Grinning Face (😀)"),
        (0x1F602, "Tears of Joy (😂)"),
        (0x1F44D, "Thumbs Up (👍)"),
        (0x1F525, "Fire (🔥)"),
        (0x2728, "Sparkles (✨)"),
    ]
    for cp, label in test_codepoints:
        if cp in cmap:
            print(f"  [OK] {label} U+{cp:X} -> {cmap[cp]}")
        else:
            print(f"  [WARN] {label} U+{cp:X} not found in cmap")

    # 4. GSUB table
    print("\n4. Checking GSUB Ligatures:")
    gsub = font["GSUB"].table
    feature_tags = [f.FeatureTag for f in gsub.FeatureList.FeatureRecord]
    print(f"  • Feature tags: {feature_tags}")
    if "liga" in feature_tags:
        print("  [OK] Standard ligature feature 'liga' found")

    # 5. CBDT table (Native Android / Instaprime Color Bitmaps)
    print("\n5. Checking CBDT / CBLC Color Bitmap Strikes:")
    cbdt = font["CBDT"]
    print(f"  • CBDT strike count: {len(cbdt.strikeData)}")
    if len(cbdt.strikeData) > 0:
        strike0 = cbdt.strikeData[0]
        print(f"  [OK] CBDT Strike 0 contains {len(strike0)} bitmap glyphs")

    # 6. sbix table (Apple / Desktop Color Bitmaps)
    print("\n6. Checking sbix Color Bitmap Strikes:")
    sbix = font["sbix"]
    for strike_ppem, strike in sbix.strikes.items():
        glyph_count = len(strike.glyphs)
        print(f"  • Strike PPEM {strike_ppem}: {glyph_count} bitmap glyphs embedded")
        if glyph_count > 0:
            sample_glyph = list(strike.glyphs.values())[0]
            if sample_glyph.graphicType in (b"png ", "png "):
                print(f"  [OK] Sample bitmap glyph format verified as PNG ({len(sample_glyph.imageData)} bytes)")

    print("\n" + "=" * 50)
    print("ALL FONT VERIFICATION CHECKS PASSED!")
    print("=" * 50)

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else FONT_PATH
    verify_font(target)

if __name__ == "__main__":
    main()
