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
    "1. 아시아": [
        "도쿄 여행 브이로그",
        "오사카 교토 브이로그",
        "후쿠오카 여행 브이로그",
        "대만 타이베이 브이로그",
        "홍콩 여행 브이로그",
        "방콕 여행 브이로그",
        "치앙마이 여행 브이로그",
        "다낭 호이안 브이로그",
        "베트남 여행 브이로그",
        "발리 여행 브이로그",
        "세부 보홀 여행 브이로그"
    ],
    "2. 유럽": [
        "파리 여행 브이로그",
        "런던 여행 브이로그",
        "이탈리아 로마 브이로그",
        "스페인 바르셀로나 브이로그",
        "스위스 인터라켄 브이로그",
        "동유럽 프라하 부다페스트 브이로그"
    ],
    "3. 북아메리카": [
        "뉴욕 여행 브이로그",
        "LA 여행 브이로그",
        "샌프란시스코 여행 브이로그",
        "하와이 여행 브이로그",
        "캐나다 밴프 밴쿠버 브이로그"
    ],
    "4. 남아메리카": [
        "남미 배낭여행 브이로그",
        "페루 마추픽추 브이로그",
        "볼리비아 우유니 브이로그",
        "아르헨티나 여행 브이로그",
        "칠레 여행 브이로그"
    ],
    "5. 오세아니아": [
        "호주 시드니 여행 브이로그",
        "멜버른 여행 브이로그",
        "뉴질랜드 남섬 여행 브이로그",
        "괌 사이판 여행 브이로그"
    ],
    "6. 아프리카 & 중동": [
        "튀르키예 이스탄불 카파도키아 브이로그",
        "이집트 카이로 다합 브이로그",
        "두바이 여행 브이로그",
        "모로코 여행 브이로그"
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
