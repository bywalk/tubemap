#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TubeMap Travel - Batch Regional Discover Script
Runs discovery for Southeast Asia, Europe, Americas, and Middle East/Central Asia
"""

import sys
import os
import time

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from collector import discover_travel_vlogs

REGIONS = {
    "동남아": [
        "태국 여행 브이로그",
        "치앙마이 브이로그",
        "베트남 여행 브이로그",
        "발리 여행 브이로그",
        "보홀 세부 여행 브이로그",
        "라오스 여행 브이로그"
    ],
    "유럽": [
        "유럽 여행 브이로그",
        "스위스 여행 브이로그",
        "이탈리아 여행 브이로그",
        "스페인 여행 브이로그",
        "프랑스 파리 여행 브이로그",
        "동유럽 여행 브이로그"
    ],
    "미주 & 대양주": [
        "미국 여행 브이로그",
        "하와이 여행 브이로그",
        "호주 여행 브이로그",
        "캐나다 여행 브이로그"
    ],
    "중동 & 중앙아시아": [
        "튀르키예 여행 브이로그",
        "이집트 여행 브이로그",
        "두바이 여행 브이로그"
    ]
}

def main():
    target_region = sys.argv[1] if len(sys.argv) > 1 else None
    
    if target_region:
        queries = REGIONS.get(target_region, [target_region])
        print(f"🚀 [{target_region}] 권역 집중 수집 시작 ({len(queries)}개 키워드)...")
        for q in queries:
            print(f"\n▶ 검색 키워드: '{q}'")
            try:
                discover_travel_vlogs(q, is_auto=True, max_videos=20)
            except Exception as e:
                print(f"⚠️ '{q}' 수집 중 오류: {e}")
            time.sleep(1)
    else:
        for reg_name, queries in REGIONS.items():
            print(f"\n{'='*70}\n🌍 [{reg_name}] 권역 일괄 수집 시작 ({len(queries)}개 키워드)\n{'='*70}")
            for q in queries:
                print(f"\n▶ 검색 키워드: '{q}'")
                try:
                    discover_travel_vlogs(q, is_auto=True, max_videos=20)
                except Exception as e:
                    print(f"⚠️ '{q}' 수집 중 오류: {e}")
                time.sleep(1)

    print("\n🎉 모든 권역의 브이로그 발굴 및 수집이 완료되었습니다!")

if __name__ == "__main__":
    main()
