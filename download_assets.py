"""
Downloads IPL team logos + hero/background images into frontend/public/
Run once after setup: python download_assets.py
"""

import requests
import time
from pathlib import Path

LOGOS_DIR  = Path("frontend/public/logos")
IMAGES_DIR = Path("frontend/public/images")
LOGOS_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://seeklogo.com/",
}

TEAM_LOGOS = {
    "MI":   [
        "https://images.seeklogo.com/logo-png/30/1/mi-mumbai-indians-logo-png_seeklogo-304945.png",
        "https://upload.wikimedia.org/wikipedia/en/c/cd/Mumbai_Indians_Logo.png",
    ],
    "CSK":  [
        "https://images.seeklogo.com/logo-png/19/1/ipl-chennai-super-kings-logo-png_seeklogo-196613.png",
        "https://upload.wikimedia.org/wikipedia/en/2/2b/Chennai_Super_Kings_Logo.png",
    ],
    "RCB":  [
        "https://images.seeklogo.com/logo-png/34/1/royal-challengers-bengaluru-logo-png_seeklogo-349568.png",
        "https://upload.wikimedia.org/wikipedia/en/4/4f/Royal_Challengers_Bangalore_Logo.svg",
    ],
    "KKR":  [
        "https://images.seeklogo.com/logo-png/30/1/kolkata-knight-riders-logo-png_seeklogo-307143.png",
        "https://upload.wikimedia.org/wikipedia/en/4/4c/Kolkata_Knight_Riders_Logo.png",
    ],
    "SRH":  [
        "https://images.seeklogo.com/logo-png/35/1/sunrisers-hyderabad-logo-png_seeklogo-352074.png",
        "https://upload.wikimedia.org/wikipedia/en/d/de/Sunrisers_Hyderabad.png",
    ],
    "DC":   [
        "https://images.seeklogo.com/logo-png/35/1/delhi-capitals-logo-png_seeklogo-352073.png",
        "https://upload.wikimedia.org/wikipedia/en/0/0e/Delhi_Capitals_Logo.png",
    ],
    "PBKS": [
        "https://images.seeklogo.com/logo-png/43/1/punjab-kings-logo-png_seeklogo-430712.png",
        "https://upload.wikimedia.org/wikipedia/en/d/d4/Punjab_Kings_Logo.png",
    ],
    "RR":   [
        "https://images.seeklogo.com/logo-png/47/1/rajasthan-royals-logo-png_seeklogo-477274.png",
        "https://upload.wikimedia.org/wikipedia/en/6/60/Rajasthan_Royals_Logo.png",
    ],
    "LSG":  [
        "https://images.seeklogo.com/logo-png/46/1/lucknow-super-giants-logo-png_seeklogo-465449.png",
        "https://upload.wikimedia.org/wikipedia/en/5/5d/Lucknow_Super_Giants_Logo.png",
    ],
    "GT":   [
        "https://images.seeklogo.com/logo-png/43/1/gujarat-titans-ipl-logo-png_seeklogo-431226.png",
        "https://upload.wikimedia.org/wikipedia/en/0/09/Gujarat_Titans_Logo.png",
    ],
}

BACKGROUND_IMAGES = {
    "stadium": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e3/Eden_Gardens_stadium_IPL_2008.jpg/1280px-Eden_Gardens_stadium_IPL_2008.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Wankhede_Stadium_2016.jpg/1280px-Wankhede_Stadium_2016.jpg",
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/af/2015_Cricket_World_Cup_Final.jpg/1280px-2015_Cricket_World_Cup_Final.jpg",
    ],
    "ipl_logo": [
        "https://upload.wikimedia.org/wikipedia/en/8/8c/Tata_IPL_2024_Logo.png",
        "https://upload.wikimedia.org/wikipedia/en/8/8c/Indian_Premier_League_Logo.png",
        "https://upload.wikimedia.org/wikipedia/commons/3/3b/IPL_Logo.png",
    ],
    "trophy": [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/3/33/IPL_Trophy.jpg/400px-IPL_Trophy.jpg",
    ],
}


def download_file(urls: list[str], dest: Path, label: str) -> bool:
    for url in urls:
        try:
            ext = url.rsplit(".", 1)[-1].split("?")[0].lower()
            if ext not in ("png", "jpg", "jpeg", "svg", "webp"):
                ext = "png"
            out = dest.with_suffix(f".{ext}")
            r = requests.get(url, headers=HEADERS, timeout=15)
            ct = r.headers.get("content-type", "")
            if r.status_code == 200 and ("image" in ct or r.content[:4] in (b"\x89PNG", b"\xff\xd8\xff", b"<svg")):
                out.write_bytes(r.content)
                print(f"  [OK]  {label:10s}  {url[:70]}")
                return True
            else:
                print(f"  [--]  {label:10s}  HTTP {r.status_code}  {url[:60]}")
        except Exception as e:
            print(f"  [ERR] {label:10s}  {e}  {url[:60]}")
        time.sleep(0.4)
    return False


def main():
    print("Downloading team logos...")
    for team, urls in TEAM_LOGOS.items():
        download_file(urls, LOGOS_DIR / team, team)

    print("\nDownloading background images...")
    for name, urls in BACKGROUND_IMAGES.items():
        download_file(urls, IMAGES_DIR / name, name)

    # Summary
    logos_found = list(LOGOS_DIR.glob("*.*"))
    print(f"\nLogos saved   : {len(logos_found)}/{len(TEAM_LOGOS)}  -> {LOGOS_DIR}")
    print(f"Images saved  : {len(list(IMAGES_DIR.glob('*.*')))}         -> {IMAGES_DIR}")

    # Write a manifest JSON for the frontend
    manifest = {}
    for team in TEAM_LOGOS:
        files = list(LOGOS_DIR.glob(f"{team}.*"))
        if files:
            manifest[team] = f"/logos/{files[0].name}"

    for name in BACKGROUND_IMAGES:
        files = list(IMAGES_DIR.glob(f"{name}.*"))
        if files:
            manifest[f"bg_{name}"] = f"/images/{files[0].name}"

    import json
    (Path("frontend/public") / "asset_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nManifest written to frontend/public/asset_manifest.json")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
