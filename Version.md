# Version History & Project Evolution

## Libraries & Tools
- Python: 3.11+
- fontTools: 4.48.0+
- Pillow: 10.2.0+
- aiohttp: 3.9.3+
- requests: 2.31.0+
- Target Font: GoogleEmoji3D.ttf (OpenType TrueType with sbix color bitmap strikes, cmap Format 12, GSUB ligatures)

---

## Log Entries

### [2026-09-21 18:59:30] Project Inception & Pipeline Architecture
- **Status:** Initialized & Implemented
- **Repository:** `https://github.com/mrdarksidetm/Google-Emoji-3D`
- **Summary:**
  - Designed and constructed the complete project architecture for **Google Emoji 3D**, compiling Google's upcoming Android 17 volumetric 3D emoji assets into an installable TrueType (`.ttf`) color font.
  - Implemented zero-local-footprint asset fetching and compilation: designed specifically to execute within GitHub Actions cloud runners without downloading heavy PNGs to the local machine.
  - Built Python toolchain:
    - `scripts/fetch_metadata.py`: Fetches and processes `emojis_data.js` from `https://googlefonts.github.io/noto-emoji-files/`, categorizing 3,988 emojis across 9 standard Unicode categories with proposal and CLDR metadata.
    - `scripts/download_assets.py`: High-concurrency async parallel downloader for GitHub Actions with automated sizing and categorized directory structuring.
    - `scripts/build_font.py`: OpenType compiler that creates `GoogleEmoji3D.ttf` with standard tables (`head`, `hhea`, `maxp`, `OS/2`, `name`, `post`, `glyf`, `loca`, `hmtx`), Unicode `cmap` (Format 12 UCS-4 and Format 4 BMP), `GSUB` multiple ligature substitution for multi-codepoint sequences, and `sbix` color bitmap strikes.
    - `scripts/verify_font.py`: Automated font validator that inspects table presence, naming records, cmap mappings, GSUB ligatures, and bitmap strike integrity.
  - Configured GitHub Actions automation:
    - `.github/workflows/build-and-release.yml`: Runs on `workflow_dispatch` and `v*` tags, sets up Python 3.11, caches PNGs, runs the parallel download, compiles `GoogleEmoji3D.ttf`, verifies the font, and publishes automated GitHub Releases.
  - Created documentation:
    - `README.md`: Overview, category breakdown table, Gboard installation walkthrough, and build instructions.
    - `LICENSE`: Apache 2.0 and SIL Open Font License 1.1 notices.
- **Files Created:**
  - `requirements.txt` (Created)
  - `scripts/fetch_metadata.py` (Created)
  - `scripts/download_assets.py` (Created)
  - `scripts/build_font.py` (Created)
  - `scripts/verify_font.py` (Created)
  - `.github/workflows/build-and-release.yml` (Created)
  - `README.md` (Created)
  - `.gitignore` (Created)
  - `LICENSE` (Created)
  - `Version.md` (Created)

### [2026-09-21 20:43:00 IST] Fix Font Compiler Sbix Import Bug, Autonomous Sync Schedule & Overwriting Rolling Release
- **Status:** Completed & Ready for Remote Verification
- **Repository:** `https://github.com/mrdarksidetm/Google-Emoji-3D`
- **Summary:**
  - Resolved workflow run `35608297473` failure where `scripts/build_font.py` erroneously reported missing fontTools/Pillow due to improper sub-table import paths (`Strike` and `SbixGlyph` now imported from `fontTools.ttLib.tables.sbixStrike` and `fontTools.ttLib.tables.sbixGlyph`).
  - Corrected constructor parameter passing for `Strike(ppem=strike_res, resolution=72)` and `SbixGlyph(glyphName=..., originOffsetX=..., originOffsetY=..., graphicType="png ", imageData=...)` to match standard fontTools keyword signatures.
  - Updated `scripts/verify_font.py` to accept both string and byte graphicType identifiers (`b"png "` and `"png "`).
  - Implemented Autonomous Sync: Configured recurring cron trigger (`cron: '0 0 * * 0'`) in `.github/workflows/build-and-release.yml` to automatically download new PNG assets as Google releases them, patch the font, and publish.
  - Implemented Single Rolling Release Overwrite: Configured `softprops/action-gh-release@v2` with `overwrite: true` and `make_latest: true` targeting rolling release `v1.0.0` so that any updated compilation continuously overwrites the previous `GoogleEmoji3D.ttf` and asset package in place.
- **Files Modified:**
  - `scripts/build_font.py` (Modified)
  - `scripts/verify_font.py` (Modified)
  - `.github/workflows/build-and-release.yml` (Modified)
  - `Version.md` (Appended)
