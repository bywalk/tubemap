#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from collector import (
    load_channels, save_channels, load_existing_video_spots,
    fetch_channel_videos, extract_granular_locations, append_to_data_js
)

new_channels = [
    {'name': '오사카에사는사람들TV', 'handle': 'osaka544'},
    {'name': '뜨랑낄로', 'handle': 'trankilo'},
    {'name': '여락이들', 'handle': '여락이들'},
    {'name': '모칠레로', 'handle': 'Mochilero_korean'},
    {'name': '테디여행기', 'handle': 'TeddyTravelog'},
    {'name': '삐까뚱씨', 'handle': 'PKDC'},
    {'name': '신아로미', 'handle': 'sinaromi'},
    {'name': 'Joe튜브', 'handle': '조튜브'},
    {'name': '유이뿅', 'handle': '일본인_유이뿅'},
    {'name': '조조캠핑', 'handle': 'jojocamping'},
    {'name': '은하캠핑', 'handle': 'eunhacamping'},
]

channels = load_channels()
existing_handles = {c.get('handle', '').lower(): c for c in channels}
existing_spots = load_existing_video_spots()

total_spots = []
new_channels_added = []

for ch in new_channels:
    h = ch['handle'].lower()
    if h not in existing_handles:
        channels.append(ch)
        existing_handles[h] = ch
        new_channels_added.append(ch)

    videos = fetch_channel_videos(ch)
    ch_spots = []
    for v in videos:
        # 1년(365일) 이내 최신 영상만
        if v.get('days_ago', 0) > 365:
            continue
        extracted = extract_granular_locations(v['youtube_id'], v['title'], v.get('description', ''), ch['name'])
        for s in extracted:
            key = (v['youtube_id'], s['locationName'].strip().lower())
            if key not in existing_spots:
                s['publishedAt'] = v.get('published', '') or datetime.now().strftime('%Y-%m-%d')
                ch_spots.append(s)
                existing_spots.add(key)
    print(f'📍 [{ch["name"]}] 등록할 신규 스팟: {len(ch_spots)}곳')
    total_spots.extend(ch_spots)

if total_spots:
    append_to_data_js(total_spots)
    save_channels(channels)
    print(f"\n🎉 성공적으로 {len(new_channels_added)}개 채널 및 {len(total_spots)}개 신규 여행지 스팟이 등록되었습니다!")
else:
    save_channels(channels)
    print(f"\n💡 신규 스팟 없이 {len(new_channels_added)}개 채널이 등록되었습니다.")
