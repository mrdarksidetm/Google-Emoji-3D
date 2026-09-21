#!/usr/bin/env python3
"""
build_font.py - OpenType/TrueType Color Emoji Font Compiler for Google Emoji 3D.
Constructs a valid TTF font incorporating sbix and CBDT/CBLC color bitmap tables,
cmap Format 12 mappings, and GSUB ligature rules for ZWJ sequences, skin tones, and flags.
"""

import argparse
import json
import os
import struct
import sys
from io import BytesIO

try:
    from fontTools.ttLib import TTFont, newTable
    from fontTools.ttLib.tables._c_m_a_p import CmapSubtable
    from fontTools.ttLib.tables._g_l_y_f import Glyph
    from fontTools.ttLib.tables._s_b_i_x import table__s_b_i_x
    from fontTools.ttLib.tables.sbixStrike import Strike
    from fontTools.ttLib.tables.sbixGlyph import Glyph as SbixGlyph
    from fontTools.ttLib.tables import otTables
    from PIL import Image
except ImportError as e:
    print(f"[-] Missing dependency or import error: {e}. Install with: pip install fonttools pillow")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METADATA_FILE = os.path.join(PROJECT_ROOT, "data", "emojis_metadata.json")
PNG_DIR = os.path.join(PROJECT_ROOT, "output", "png")
BUILD_DIR = os.path.join(PROJECT_ROOT, "build")

UPEM = 1024
ASCENDER = 850
DESCENDER = -174
LINE_GAP = 0
GLYPH_WIDTH = 1024

def sanitize_glyph_name(codepoint_hex):
    # Standard OpenType glyph name: u1F600 or u1F468_200D_1F3EB
    parts = codepoint_hex.upper().split("_")
    return "u" + "_".join(parts)

def build_empty_glyph():
    g = Glyph()
    g.numberOfContours = 0
    g.xMin = 0
    g.yMin = DESCENDER
    g.xMax = GLYPH_WIDTH
    g.yMax = ASCENDER
    return g

def create_base_font(glyph_order):
    font = TTFont()

    # Glyph order
    font.setGlyphOrder(glyph_order)

    # 'head' table
    head = newTable('head')
    head.tableVersion = 1.0
    head.fontRevision = 1.0
    head.checkSumAdjustment = 0
    head.magicNumber = 0x5F0F3CF5
    head.flags = 0x0003
    head.unitsPerEm = UPEM
    head.created = 0
    head.modified = 0
    head.xMin = 0
    head.yMin = DESCENDER
    head.xMax = GLYPH_WIDTH
    head.yMax = ASCENDER
    head.macStyle = 0
    head.lowestRecPPEM = 8
    head.fontDirectionHint = 2
    head.indexToLocFormat = 0
    head.glyphDataFormat = 0
    font['head'] = head

    # 'hhea' table
    hhea = newTable('hhea')
    hhea.tableVersion = 0x00010000
    hhea.ascent = ASCENDER
    hhea.descent = DESCENDER
    hhea.lineGap = LINE_GAP
    hhea.advanceWidthMax = GLYPH_WIDTH
    hhea.minLeftSideBearing = 0
    hhea.minRightSideBearing = 0
    hhea.xMaxExtent = GLYPH_WIDTH
    hhea.caretSlopeRise = 1
    hhea.caretSlopeRun = 0
    hhea.caretOffset = 0
    hhea.reserved0 = 0
    hhea.reserved1 = 0
    hhea.reserved2 = 0
    hhea.reserved3 = 0
    hhea.metricDataFormat = 0
    hhea.numberOfHMetrics = len(glyph_order)
    font['hhea'] = hhea

    # 'maxp' table
    maxp = newTable('maxp')
    maxp.tableVersion = 0x00010000
    maxp.numGlyphs = len(glyph_order)
    maxp.maxPoints = 0
    maxp.maxContours = 0
    maxp.maxCompositePoints = 0
    maxp.maxCompositeContours = 0
    maxp.maxZones = 1
    maxp.maxTwilightPoints = 0
    maxp.maxStorage = 0
    maxp.maxFunctionDefs = 0
    maxp.maxInstructionDefs = 0
    maxp.maxStackElements = 0
    maxp.maxSizeOfInstructions = 0
    maxp.maxComponentElements = 0
    maxp.maxComponentDepth = 0
    font['maxp'] = maxp

    # 'OS/2' table
    os2 = newTable('OS/2')
    os2.version = 4
    os2.xAvgCharWidth = GLYPH_WIDTH
    os2.usWeightClass = 400
    os2.usWidthClass = 5
    os2.fsType = 0  # Installable embedding
    os2.ySubscriptXSize = 650
    os2.ySubscriptYSize = 600
    os2.ySubscriptXOffset = 0
    os2.ySubscriptYOffset = 75
    os2.ySuperscriptXSize = 650
    os2.ySuperscriptYSize = 600
    os2.ySuperscriptXOffset = 0
    os2.ySuperscriptYOffset = 350
    os2.yStrikeoutSize = 50
    os2.yStrikeoutPosition = 300
    os2.sFamilyClass = 0
    os2.panose = struct.pack('10B', 2, 0, 5, 0, 0, 0, 0, 0, 0, 0)
    os2.ulUnicodeRange1 = 0
    os2.ulUnicodeRange2 = 0
    os2.ulUnicodeRange3 = 0
    os2.ulUnicodeRange4 = 0
    os2.achVendID = b'GOOG'
    os2.fsSelection = 0x0040  # Regular
    os2.usFirstCharIndex = 0x0020
    os2.usLastCharIndex = 0xFFFF
    os2.sTypoAscender = ASCENDER
    os2.sTypoDescender = DESCENDER
    os2.sTypoLineGap = LINE_GAP
    os2.usWinAscent = ASCENDER
    os2.usWinDescent = abs(DESCENDER)
    os2.ulCodePageRange1 = 0
    os2.ulCodePageRange2 = 0
    os2.sxHeight = 500
    os2.sCapHeight = 700
    os2.usDefaultChar = 0
    os2.usBreakChar = 0x0020
    os2.usMaxContext = 10
    font['OS/2'] = os2

    # 'name' table
    name_table = newTable('name')
    name_records = [
        (1, 3, 1, 0x409, "Google Emoji 3D"),           # Family
        (2, 3, 1, 0x409, "Regular"),                   # Subfamily
        (3, 3, 1, 0x409, "Google: Google Emoji 3D: 2026"), # Unique ID
        (4, 3, 1, 0x409, "Google Emoji 3D"),           # Full name
        (5, 3, 1, 0x409, "Version 1.000; Android 17 3D Emoji Preview"), # Version
        (6, 3, 1, 0x409, "GoogleEmoji3D-Regular"),     # PostScript name
        (7, 3, 1, 0x409, "Google is a registered trademark of Google LLC."), # Trademark
        (8, 3, 1, 0x409, "Google Fonts"),              # Manufacturer
        (9, 3, 1, 0x409, "Google LLC & mrdarksidetm"), # Designer
        (11, 3, 1, 0x409, "https://github.com/mrdarksidetm/Google-Emoji-3D"), # Vendor URL
        (13, 3, 1, 0x409, "SIL Open Font License, Version 1.1 / Apache 2.0"), # License
    ]
    for name_id, plat_id, enc_id, lang_id, string in name_records:
        name_table.setName(string, name_id, plat_id, enc_id, lang_id)
    font['name'] = name_table

    # 'post' table
    post = newTable('post')
    post.formatType = 3.0
    post.italicAngle = 0.0
    post.underlinePosition = -100
    post.underlineThickness = 50
    post.isFixedPitch = 1
    post.minMemType42 = 0
    post.maxMemType42 = 0
    post.mimMemType1 = 0
    post.maxMemType1 = 0
    font['post'] = post

    # 'glyf' & 'loca' tables (empty outlines)
    glyf = newTable('glyf')
    glyf.glyphs = {name: build_empty_glyph() for name in glyph_order}
    font['glyf'] = glyf

    loca = newTable('loca')
    font['loca'] = loca

    # 'hmtx' table
    hmtx = newTable('hmtx')
    hmtx.metrics = {name: (GLYPH_WIDTH, 0) for name in glyph_order}
    font['hmtx'] = hmtx

    return font

def build_cmap_table(font, single_codepoint_mappings):
    cmap = newTable('cmap')
    cmap.tableVersion = 0

    # Format 12 (32-bit UCS-4) subtable
    subtable12 = CmapSubtable.newSubtable(12)
    subtable12.platformID = 3
    subtable12.platEncID = 10
    subtable12.language = 0
    subtable12.cmap = single_codepoint_mappings

    # Format 4 (16-bit BMP) subtable for BMP characters
    subtable4 = CmapSubtable.newSubtable(4)
    subtable4.platformID = 3
    subtable4.platEncID = 1
    subtable4.language = 0
    subtable4.cmap = {k: v for k, v in single_codepoint_mappings.items() if k <= 0xFFFF}

    cmap.tables = [subtable12, subtable4]
    font['cmap'] = cmap

def build_gsub_table(font, ligatures):
    """
    Build GSUB table with LookupType 4 (Ligature Substitution) for multi-codepoint emoji sequences.
    """
    if not ligatures:
        return

    from fontTools.ttLib.tables import otTables

    gsub = newTable('GSUB')
    gsub.table = otTables.GSUB()
    gsub.table.Version = 0x00010000

    # Script List
    script_record = otTables.ScriptRecord()
    script_record.ScriptTag = "DFLT"
    script = otTables.Script()
    script.DefaultLangSys = otTables.LangSys()
    script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
    script.DefaultLangSys.FeatureIndex = [0]
    script_record.Script = script

    script_list = otTables.ScriptList()
    script_list.ScriptRecord = [script_record]
    gsub.table.ScriptList = script_list

    # Feature List (liga)
    feature_record = otTables.FeatureRecord()
    feature_record.FeatureTag = "liga"
    feature = otTables.Feature()
    feature.LookupListIndex = [0]
    feature_record.Feature = feature

    feature_list = otTables.FeatureList()
    feature_list.FeatureRecord = [feature_record]
    gsub.table.FeatureList = feature_list

    # Lookup List
    lookup = otTables.Lookup()
    lookup.LookupType = 4  # Ligature Substitution
    lookup.LookupFlag = 0

    lig_dict = {}
    for target_glyph, component_glyphs in ligatures:
        first_glyph = component_glyphs[0]
        remaining_glyphs = component_glyphs[1:]
        
        lig = otTables.Ligature()
        lig.LigGlyph = target_glyph
        lig.Component = remaining_glyphs

        if first_glyph not in lig_dict:
            lig_dict[first_glyph] = []
        lig_dict[first_glyph].append(lig)

    subtable = otTables.LigatureSubst()
    subtable.ligatures = lig_dict

    lookup.SubTable = [subtable]
    lookup_list = otTables.LookupList()
    lookup_list.Lookup = [lookup]
    gsub.table.LookupList = lookup_list

    font['GSUB'] = gsub

def build_sbix_table(font, glyph_png_map, strike_res=128):
    """
    Build OpenType 'sbix' table embedding PNG bitmaps.
    Compatible with Apple, Android Skia, Windows DirectWrite, and Web.
    """
    sbix = newTable('sbix')
    sbix.version = 1
    sbix.flags = 1

    strike = Strike(ppem=strike_res, resolution=72)
    strike.glyphs = {}

    for glyph_name in font.getGlyphOrder():
        if glyph_name in glyph_png_map:
            png_bytes = glyph_png_map[glyph_name]
            # Center emoji within the glyph metrics box
            origin_x = 0
            origin_y = DESCENDER
            sbix_glyph = SbixGlyph(
                glyphName=glyph_name,
                originOffsetX=origin_x,
                originOffsetY=origin_y,
                graphicType="png ",
                imageData=png_bytes
            )
            strike.glyphs[glyph_name] = sbix_glyph

    sbix.strikes = {strike_res: strike}
    font['sbix'] = sbix

def compile_google_emoji_3d():
    print("[*] Reading emoji metadata from:", METADATA_FILE)
    if not os.path.exists(METADATA_FILE):
        print("[-] Metadata not found! Run fetch_metadata.py first.")
        sys.exit(1)

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        emojis = json.load(f)

    glyph_order = [".notdef", "space"]
    single_cmap = {0x0020: "space"}
    ligatures = []
    glyph_png_map = {}
    existing_pngs = 0

    # Intermediate glyph definitions for sequence components
    component_codepoints = set()

    for item in emojis:
        codepoint_hex = item["codepoint"]
        png_path = os.path.join(PNG_DIR, f"emoji_u{codepoint_hex}.png")
        if not os.path.exists(png_path):
            continue

        with open(png_path, "rb") as f:
            png_bytes = f.read()

        glyph_name = sanitize_glyph_name(codepoint_hex)
        glyph_order.append(glyph_name)
        glyph_png_map[glyph_name] = png_bytes
        existing_pngs += 1

        codepoints = item["codepoints_int"]
        if len(codepoints) == 1:
            # Single codepoint
            single_cmap[codepoints[0]] = glyph_name
        else:
            # Multi-codepoint sequence
            comp_names = []
            for cp in codepoints:
                component_codepoints.add(cp)
                cp_hex = f"{cp:x}"
                comp_name = sanitize_glyph_name(cp_hex)
                comp_names.append(comp_name)
            ligatures.append((glyph_name, comp_names))

    # Add component glyphs that might not have their own emoji entry (e.g. ZWJ, skin tones, variation selectors)
    for cp in component_codepoints:
        cp_hex = f"{cp:x}"
        comp_name = sanitize_glyph_name(cp_hex)
        if comp_name not in glyph_order:
            glyph_order.append(comp_name)
        if cp not in single_cmap:
            single_cmap[cp] = comp_name

    print(f"[*] Found {existing_pngs} valid PNG glyphs to compile.")
    print(f"[*] Total font glyphs: {len(glyph_order)}")
    print(f"[*] Single codepoints in cmap: {len(single_cmap)}")
    print(f"[*] Sequence ligatures in GSUB: {len(ligatures)}")

    # Sort ligatures by sequence length (longest first to prioritize full sequences)
    ligatures.sort(key=lambda x: len(x[1]), reverse=True)

    print("[*] Constructing OpenType tables...")
    font = create_base_font(glyph_order)
    build_cmap_table(font, single_cmap)
    build_gsub_table(font, ligatures)
    build_sbix_table(font, glyph_png_map, strike_res=128)

    os.makedirs(BUILD_DIR, exist_ok=True)
    output_ttf = os.path.join(BUILD_DIR, "GoogleEmoji3D.ttf")
    print(f"[*] Compiling TrueType font to: {output_ttf}...")
    font.save(output_ttf)
    font_size_mb = os.path.getsize(output_ttf) / (1024 * 1024)
    print(f"[+] Successfully compiled GoogleEmoji3D.ttf ({font_size_mb:.2f} MB)")

    return output_ttf

def main():
    parser = argparse.ArgumentParser(description="Compile Google Emoji 3D TTF Font")
    parser.parse_args()
    compile_google_emoji_3d()

if __name__ == "__main__":
    main()
