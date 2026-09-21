#!/usr/bin/env python3
"""
download_assets.py - High-speed parallel downloader for Google 3D Emoji PNGs.
Designed for GitHub Actions cloud runners to fetch assets without burdening local machines.
"""

import argparse
import asyncio
import json
import os
import shutil
import sys
from io import BytesIO

try:
    import aiohttp
    from PIL import Image
except ImportError:
    print("[-] Missing dependencies. Install with: pip install aiohttp pillow")
    sys.exit(1)

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METADATA_FILE = os.path.join(PROJECT_ROOT, "data", "emojis_metadata.json")
OUTPUT_PNG_DIR = os.path.join(PROJECT_ROOT, "output", "png")
CATEGORIZED_DIR = os.path.join(PROJECT_ROOT, "output", "categorized")

async def download_single_emoji(session, emoji, target_res, semaphore, progress_state):
    codepoint = emoji["codepoint"]
    filename = f"emoji_u{codepoint}.png"
    target_path = os.path.join(OUTPUT_PNG_DIR, filename)

    if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
        progress_state["skipped"] += 1
        return True

    # Candidate URLs:
    # 1. GitHub noto-emoji 3D png at target resolution
    # 2. GitHub noto-emoji 3D png 512
    # 3. Google Fonts CDN 512
    urls = [
        f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/3D/png/{target_res}/emoji_u{codepoint}.png",
        f"https://raw.githubusercontent.com/googlefonts/noto-emoji/main/3D/png/512/emoji_u{codepoint}.png",
        f"https://fonts.gstatic.com/s/e/noto3demoji/latest/{codepoint}/512.png"
    ]

    async with semaphore:
        for url in urls:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        if len(content) < 100:
                            continue
                        
                        # Process image: ensure RGBA and correct size
                        img = Image.open(BytesIO(content)).convert("RGBA")
                        if img.size != (target_res, target_res):
                            img = img.resize((target_res, target_res), Image.Resampling.LANCZOS)
                        
                        img.save(target_path, format="PNG", optimize=True)
                        progress_state["downloaded"] += 1
                        
                        current = progress_state["downloaded"] + progress_state["skipped"]
                        if current % 100 == 0 or current == progress_state["total"]:
                            print(f"[*] Progress: {current}/{progress_state['total']} "
                                  f"({progress_state['downloaded']} downloaded, {progress_state['skipped']} cached, {progress_state['failed']} failed)")
                        return True
            except Exception:
                continue

    progress_state["failed"] += 1
    # print(f"[-] Failed to fetch 3D asset for: {emoji['name']} ({codepoint})")
    return False

async def download_all(emojis, target_res, concurrency, categorize=True):
    os.makedirs(OUTPUT_PNG_DIR, exist_ok=True)
    if categorize:
        os.makedirs(CATEGORIZED_DIR, exist_ok=True)

    semaphore = asyncio.Semaphore(concurrency)
    progress_state = {
        "total": len(emojis),
        "downloaded": 0,
        "skipped": 0,
        "failed": 0
    }

    connector = aiohttp.TCPConnector(limit=concurrency, ttl_dns_cache=300)
    headers = {"User-Agent": "Google-Emoji-3D-Builder/1.0"}

    print(f"[*] Starting parallel download for {len(emojis)} emojis at {target_res}x{target_res}...")
    print(f"[*] Concurrency limit: {concurrency}")

    async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
        tasks = [
            download_single_emoji(session, emoji, target_res, semaphore, progress_state)
            for emoji in emojis
        ]
        await asyncio.gather(*tasks)

    print("\n" + "=" * 50)
    print("DOWNLOAD SUMMARY")
    print("=" * 50)
    print(f"Total Emojis:     {progress_state['total']}")
    print(f"Downloaded:       {progress_state['downloaded']}")
    print(f"Cached/Existing:  {progress_state['skipped']}")
    print(f"Failed/Missing:   {progress_state['failed']}")
    print("=" * 50)

    if categorize:
        print("[*] Organizing PNGs into categorized directory tree...")
        cat_count = 0
        for emoji in emojis:
            src_file = os.path.join(OUTPUT_PNG_DIR, f"emoji_u{emoji['codepoint']}.png")
            if not os.path.exists(src_file):
                continue
            
            clean_category = emoji.get("category", "Other").replace("&", "and").replace("/", "-")
            clean_subgroup = emoji.get("subgroup", "general").replace("&", "and").replace("/", "-")
            
            dest_folder = os.path.join(CATEGORIZED_DIR, clean_category, clean_subgroup)
            os.makedirs(dest_folder, exist_ok=True)
            
            dest_file = os.path.join(dest_folder, f"{emoji['codepoint']}_{emoji.get('cldrName', 'emoji').replace(' ', '_')}.png")
            shutil.copy2(src_file, dest_file)
            cat_count += 1
        print(f"[+] Categorized {cat_count} PNG assets in {CATEGORIZED_DIR}")

def main():
    parser = argparse.ArgumentParser(description="Download Google 3D Emoji PNGs")
    parser.add_argument("--resolution", type=int, default=128, choices=[32, 72, 128, 160, 512],
                        help="Target PNG resolution for TTF glyphs (default: 128)")
    parser.add_argument("--concurrency", type=int, default=40,
                        help="Parallel download concurrency (default: 40)")
    parser.add_argument("--no-categorize", action="store_true",
                        help="Skip organizing into categorized directory tree")
    args = parser.parse_args()

    if not os.path.exists(METADATA_FILE):
        print("[-] Metadata file not found! Running fetch_metadata.py first...")
        from fetch_metadata import main as fetch_main
        fetch_main()

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        emojis = json.load(f)

    asyncio.run(download_all(emojis, args.resolution, args.concurrency, not args.no_categorize))

if __name__ == "__main__":
    main()
