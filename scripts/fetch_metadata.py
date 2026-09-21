#!/usr/bin/env python3
"""
fetch_metadata.py - Fetch and categorize Google 3D Emoji metadata from official Google Fonts Noto Emoji repository.
Extracts Unicode sequences, proposals, CLDR names, categories, and subgroups.
"""

import json
import os
import re
import sys
import urllib.request

DATA_URL = "https://googlefonts.github.io/noto-emoji-files/data/emojis_data.js"
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

def fetch_raw_data():
    print(f"[*] Fetching emoji metadata from: {DATA_URL}")
    req = urllib.request.Request(
        DATA_URL,
        headers={"User-Agent": "Google-Emoji-3D-Builder/1.0"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode("utf-8")
    return content

def parse_metadata(js_content):
    print("[*] Parsing emojis_data.js...")
    # Strip javascript assignment wrapper: window.__NOTO_EMOJIS_DATA__ = [...]
    cleaned = re.sub(r"^\s*window\.__NOTO_EMOJIS_DATA__\s*=\s*", "", js_content.strip())
    cleaned = re.sub(r";\s*$", "", cleaned)
    raw_list = json.loads(cleaned)
    print(f"[*] Found {len(raw_list)} raw emoji records.")
    return raw_list

def process_and_categorize(raw_list):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    categories = {}
    processed_emojis = []

    for item in raw_list:
        codepoint_str = item.get("codepoint", "")
        if not codepoint_str:
            continue
        
        # Split codepoints (handling underscores)
        parts = [p.lower() for p in codepoint_str.split("_") if p]
        codepoint_ints = [int(p, 16) for p in parts]
        formatted_hex = "_".join(parts)
        unicode_formatted = " ".join([f"U+{p.upper()}" for p in parts])

        category = item.get("category", "Uncategorized")
        subgroup = item.get("subgroup", "general")

        processed = {
            "id": item.get("id", f"emoji_u{formatted_hex}"),
            "codepoint": formatted_hex,
            "codepoints_hex": parts,
            "codepoints_int": codepoint_ints,
            "unicode_sequence": unicode_formatted,
            "is_sequence": len(parts) > 1,
            "char": item.get("char", ""),
            "name": item.get("name", ""),
            "cldrName": item.get("cldrName", ""),
            "category": category,
            "subgroup": subgroup,
            "shortcode": item.get("shortcode", ""),
            "dateAdded": item.get("dateAdded", ""),
            "utcProposal": {
                "doc": item.get("utcDoc", ""),
                "title": item.get("utcTitle", ""),
                "author": item.get("utcAuthor", ""),
                "url": item.get("utcUrl", "")
            },
            "cdn_url_512": f"https://fonts.gstatic.com/s/e/noto3demoji/latest/{formatted_hex}/512.png",
            "github_raw_128": f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/3D/png/128/emoji_u{formatted_hex}.png",
            "github_raw_512": f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/3D/png/512/emoji_u{formatted_hex}.png"
        }

        processed_emojis.append(processed)

        # Categorize
        if category not in categories:
            categories[category] = {
                "category_name": category,
                "count": 0,
                "subgroups": {}
            }
        categories[category]["count"] += 1
        
        if subgroup not in categories[category]["subgroups"]:
            categories[category]["subgroups"][subgroup] = []
        categories[category]["subgroups"][subgroup].append({
            "id": processed["id"],
            "codepoint": formatted_hex,
            "char": processed["char"],
            "name": processed["name"],
            "cldrName": processed["cldrName"]
        })

    # Save full metadata
    metadata_file = os.path.join(OUTPUT_DIR, "emojis_metadata.json")
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(processed_emojis, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved metadata for {len(processed_emojis)} emojis to {metadata_file}")

    # Save categorized manifest
    manifest_file = os.path.join(OUTPUT_DIR, "categories_manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2, ensure_ascii=False)
    print(f"[+] Saved categories manifest to {manifest_file}")

    # Print breakdown
    print("\n" + "=" * 50)
    print("CATEGORIES BREAKDOWN")
    print("=" * 50)
    for cat_name, cat_data in sorted(categories.items(), key=lambda x: -x[1]["count"]):
        sub_count = len(cat_data["subgroups"])
        print(f"  • {cat_name:<22}: {cat_data['count']:>4} emojis ({sub_count} subgroups)")
    print("=" * 50)
    print(f"Total Emojis: {len(processed_emojis)}")

    return processed_emojis, categories

def main():
    try:
        raw_content = fetch_raw_data()
        emojis, categories = process_and_categorize(parse_metadata(raw_content))
    except Exception as e:
        print(f"[-] Failed to fetch or process metadata: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
