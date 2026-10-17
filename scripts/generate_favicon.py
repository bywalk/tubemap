#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TubeMap Travel - Favicon & App Icon Generator
Generates:
  - favicon.svg
  - apple-touch-icon.png (180x180)
  - favicon-32x32.png (32x32)
  - favicon-16x16.png (16x16)
  - favicon.ico (multi-res 16, 32, 48)
  - site.webmanifest
"""

import os
import shutil
import struct
import subprocess

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG_PATH = os.path.join(ROOT_DIR, "favicon.svg")

SVG_CONTENT = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="tubeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF1A1A" />
      <stop offset="100%" stop-color="#CC0000" />
    </linearGradient>
    <linearGradient id="pinGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#FFFFFF" />
      <stop offset="100%" stop-color="#F1F5F9" />
    </linearGradient>
    <filter id="pinShadow" x="-20%" y="-15%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="14" flood-color="#7F0000" flood-opacity="0.45" />
    </filter>
  </defs>

  <!-- Background Squircle (YouTube Red) -->
  <rect width="512" height="512" rx="116" fill="url(#tubeGrad)" />

  <!-- Subtle Top Highlight Border -->
  <rect x="4" y="4" width="504" height="504" rx="112" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-opacity="0.15" />

  <!-- Map Pin Body (Teardrop) with Soft Shadow -->
  <path filter="url(#pinShadow)" 
        d="M 256 428 C 176 322 138 254 138 188 A 118 118 0 1 1 374 188 C 374 254 336 322 256 428 Z" 
        fill="url(#pinGrad)" />

  <!-- YouTube Red Play Button Inside Pin Center (Centered at 256, 188) -->
  <path d="M 232 145 C 224 140 216 145 216 154 L 216 222 C 216 231 224 236 232 231 L 292 197 C 300 192 300 184 292 179 Z" 
        fill="url(#tubeGrad)" />
</svg>'''

def run_cmd(cmd):
    subprocess.run(cmd, shell=True, check=True)

def create_ico(png_files_and_sizes, output_path):
    num_images = len(png_files_and_sizes)
    header = struct.pack('<HHH', 0, 1, num_images)
    entries = []
    offset = 6 + 16 * num_images
    data_blobs = []
    for png_data, w, h in png_files_and_sizes:
        data_blobs.append(png_data)
        b_w = 0 if w >= 256 else w
        b_h = 0 if h >= 256 else h
        size = len(png_data)
        entry = struct.pack('<BBBBHHII', b_w, b_h, 0, 0, 1, 32, size, offset)
        entries.append(entry)
        offset += size
    with open(output_path, 'wb') as f:
        f.write(header + b''.join(entries) + b''.join(data_blobs))

def main():
    print("1. Writing favicon.svg...")
    with open(SVG_PATH, "w", encoding="utf-8") as f:
        f.write(SVG_CONTENT)

    tmp_dir = "/tmp/tubemap_favicons"
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_master_png = os.path.join(tmp_dir, "master.png")

    print("2. Rendering 512x512 Master PNG via qlmanage...")
    run_cmd(f"qlmanage -t -s 512 -o '{tmp_dir}' '{SVG_PATH}' >/dev/null 2>&1")
    rendered_thumb = os.path.join(tmp_dir, "favicon.svg.png")
    if os.path.exists(rendered_thumb):
        shutil.move(rendered_thumb, tmp_master_png)

    # Sizes to generate
    sizes = {
        "apple-touch-icon.png": 180,
        "favicon-32x32.png": 32,
        "favicon-16x16.png": 16,
    }

    print("3. Resizing PNG assets via sips...")
    ico_sources = []
    for filename, sz in sizes.items():
        out_path = os.path.join(ROOT_DIR, filename)
        run_cmd(f"sips -z {sz} {sz} '{tmp_master_png}' --out '{out_path}' >/dev/null 2>&1")
        print(f"   -> {filename} ({sz}x{sz})")

    # Generate 48x48 for ICO inclusion
    tmp_48 = os.path.join(tmp_dir, "icon-48.png")
    run_cmd(f"sips -z 48 48 '{tmp_master_png}' --out '{tmp_48}' >/dev/null 2>&1")

    print("4. Building multi-resolution favicon.ico (16, 32, 48)...")
    png_16 = open(os.path.join(ROOT_DIR, "favicon-16x16.png"), "rb").read()
    png_32 = open(os.path.join(ROOT_DIR, "favicon-32x32.png"), "rb").read()
    png_48 = open(tmp_48, "rb").read()

    ico_path = os.path.join(ROOT_DIR, "favicon.ico")
    create_ico([
        (png_16, 16, 16),
        (png_32, 32, 32),
        (png_48, 48, 48)
    ], ico_path)
    print("   -> favicon.ico (16px, 32px, 48px)")

    # Cleanup temp dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print("5. Writing site.webmanifest...")
    manifest_content = '''{
  "name": "TubeMap Travel",
  "short_name": "TubeMap",
  "description": "한국 대표 여행 유튜버들의 실제 여행 코스 & 추천 맛집 지도",
  "start_url": "./",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#ff0000",
  "icons": [
    {
      "src": "favicon-32x32.png",
      "sizes": "32x32",
      "type": "image/png"
    },
    {
      "src": "apple-touch-icon.png",
      "sizes": "180x180",
      "type": "image/png"
    },
    {
      "src": "favicon.svg",
      "sizes": "any",
      "type": "image/svg+xml"
    }
  ]
}
'''
    manifest_path = os.path.join(ROOT_DIR, "site.webmanifest")
    with open(manifest_path, "w", encoding="utf-8") as f:
        f.write(manifest_content)
    print("   -> site.webmanifest")

    print("🎉 All favicon assets generated successfully!")

if __name__ == "__main__":
    main()
