#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TubeMap Travel - 한국 대표 여행 유튜버 신규 영상 자동 수집기 (Collector)
=============================================================================
기능:
1. 구독자 5만~100만+ 한국 대표 여행 유튜버 13팀의 최신 영상 자동 수집 (무료/API 키 불필요)
2. 최근 1년(365일) 이내 업로드된 최신 영상만 선별 (오래된 과거 영상 자동 필터링)
3. 기존 js/data.js에 이미 등록된 영상은 자동으로 건너뜀 (중복 방지)
4. 제목/태그 기반 고정밀 위치 키워드 사전 및 정규식 분석으로 국가, 도시, 좌표, 꿀팁 추출
5. OpenStreetMap 지오코딩 폴백 지원
6. js/data.js에 새 여행지를 안전하게 업데이트
=============================================================================
"""

import os
import re
import sys
import json
import time
import ssl
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# =============================================================================
# 1. 수집 설정 및 모니터링 대상 한국 대표 여행 유튜버 (구독자 5만~100만+)
# =============================================================================
MAX_VIDEO_AGE_DAYS = 365  # 여행 정보 최신성 유지를 위해 1년(365일) 이내 영상만 수집
MIN_SUBSCRIBER_COUNT = 50000  # 최소 구독자 수 필터 (5만 명 이상 채널만 자동 수집)

CHANNELS = [
    # 1. 빠니보틀 (240만+)
    {
        "name": "빠니보틀",
        "handle": "PaniBottle",
        "channel_id": "UCNhofiqfw5nl-NeDJkXtPvw"
    },
    # 2. 곽튜브 (210만+)
    {
        "name": "곽튜브",
        "handle": "JBKWAK",
        "channel_id": "UC-7PJA1XKjPc5pIWKyEDx3Q"
    },
    # 3. 원지의 하루 (90만+)
    {
        "name": "원지의 하루",
        "handle": "im1G",
        "channel_id": "UC9gxOp_-R78phMHmv2bW_sg"
    },
    # 4. 채코제 (80만+)
    {
        "name": "채코제",
        "handle": "koreanjay",
        "channel_id": "UCaoqDZPllYXLAH_5OBRLLrw"
    },
    # 5. 여행가 제이 (70만+)
    {
        "name": "여행가 제이",
        "handle": "jayworldtraveler",
        "channel_id": "UCxU8QX7IRRIW0VLuoWWoxbw"
    },
    # 6. 잰잰바리 (60만+)
    {
        "name": "잰잰바리",
        "handle": "jaeye0nyy",
        "channel_id": "UCSxhYq6K0mxF24SmMGeNNQA"
    },
    # 7. 노마드션 (60만+)
    {
        "name": "노마드션",
        "handle": "NomadShaun",
        "channel_id": "UCfCOEG2kjX_x4KAdWX-YUcA"
    },
    # 8. 캡틴따거 (50만+)
    {
        "name": "캡틴따거",
        "handle": "captainbrother",
        "channel_id": "UCt_7uH4Igz0T_K3Qzbs1Wig"
    },
    # 9. 캐럿맨 여행기 (40만+)
    {
        "name": "캐럿맨 여행기",
        "handle": "carrotman1198",
        "channel_id": "UC_4hHKHUcs9bGpl_zDAOxvg"
    },
    # 10. 희철리즘 (100만+)
    {
        "name": "희철리즘",
        "handle": "HeechulismTV",
        "channel_id": "UCwjMQYL9vgbqGzxYW6dVhTw"
    },
    # 11. 또떠남 (30만+)
    {
        "name": "또떠남",
        "handle": "ddoddunam",
        "channel_id": "UCldwUablgk8KPcFPQlKnB-w"
    },
    # 12. 쏘이 The World (40만+)
    {
        "name": "쏘이 The World",
        "handle": "soy_the_world",
        "channel_id": "UCugz3-UlkX2P77PtK1Ju0RA"
    },
    # 13. 초마드 (80만+)
    {
        "name": "초마드",
        "handle": "CHOMAD",
        "channel_id": "UCvuwlY4fWkWMuzRkj5MAK9Q"
    }
]

# =============================================================================
# 2. 대표 여행지 키워드 사전 (120+ 주요 여행지 고정밀 좌표 매핑)
# =============================================================================
DESTINATION_DICTIONARY = {
    # --- 대한민국 국내 ---
    "제주": {"country": "대한민국", "city": "제주", "lat": 33.4996, "lng": 126.5312},
    "서귀포": {"country": "대한민국", "city": "서귀포", "lat": 33.2541, "lng": 126.5601},
    "부산": {"country": "대한민국", "city": "부산", "lat": 35.1796, "lng": 129.0756},
    "하동": {"country": "대한민국", "city": "하동", "lat": 35.0673, "lng": 127.7516},
    "강릉": {"country": "대한민국", "city": "강릉", "lat": 37.7519, "lng": 128.8761},
    "속초": {"country": "대한민국", "city": "속초", "lat": 38.2070, "lng": 128.5918},
    "경주": {"country": "대한민국", "city": "경주", "lat": 35.8562, "lng": 129.2247},
    "여수": {"country": "대한민국", "city": "여수", "lat": 34.7604, "lng": 127.6622},
    "전주": {"country": "대한민국", "city": "전주", "lat": 35.8242, "lng": 127.1480},
    "인천": {"country": "대한민국", "city": "인천", "lat": 37.4563, "lng": 126.7052},
    "서울": {"country": "대한민국", "city": "서울", "lat": 37.5665, "lng": 126.9780},

    # --- 일본 ---
    "도쿄": {"country": "일본", "city": "도쿄", "lat": 35.6762, "lng": 139.6503},
    "오사카": {"country": "일본", "city": "오사카", "lat": 34.6937, "lng": 135.5023},
    "후쿠오카": {"country": "일본", "city": "후쿠오카", "lat": 33.5904, "lng": 130.4017},
    "삿포로": {"country": "일본", "city": "삿포로", "lat": 43.0618, "lng": 141.3545},
    "교토": {"country": "일본", "city": "교토", "lat": 35.0116, "lng": 135.7681},
    "나고야": {"country": "일본", "city": "나고야", "lat": 35.1815, "lng": 136.9066},
    "오키나와": {"country": "일본", "city": "오키나와", "lat": 26.2124, "lng": 127.6809},
    "유후인": {"country": "일본", "city": "유후인", "lat": 33.2647, "lng": 131.3558},
    "홋카이도": {"country": "일본", "city": "삿포로", "lat": 43.0618, "lng": 141.3545},
    "일본": {"country": "일본", "city": "도쿄", "lat": 35.6762, "lng": 139.6503},

    # --- 대만 / 홍콩 / 마카오 / 중국 ---
    "타이베이": {"country": "대만", "city": "타이베이", "lat": 25.0330, "lng": 121.5654},
    "가오슝": {"country": "대만", "city": "가오슝", "lat": 22.6273, "lng": 120.3014},
    "대만": {"country": "대만", "city": "타이베이", "lat": 25.0330, "lng": 121.5654},
    "홍콩": {"country": "홍콩", "city": "홍콩", "lat": 22.3193, "lng": 114.1694},
    "마카오": {"country": "마카오", "city": "마카오", "lat": 22.1987, "lng": 113.5439},
    "하이난": {"country": "중국", "city": "하이난", "lat": 18.2528, "lng": 109.5119},
    "싼야": {"country": "중국", "city": "싼야", "lat": 18.2528, "lng": 109.5119},
    "상하이": {"country": "중국", "city": "상하이", "lat": 31.2304, "lng": 121.4737},
    "베이징": {"country": "중국", "city": "베이징", "lat": 39.9042, "lng": 116.4074},
    "칭다오": {"country": "중국", "city": "칭다오", "lat": 36.0671, "lng": 120.3826},

    # --- 동남아시아 ---
    "방콕": {"country": "태국", "city": "방콕", "lat": 13.7563, "lng": 100.5018},
    "치앙마이": {"country": "태국", "city": "치앙마이", "lat": 18.7883, "lng": 98.9853},
    "푸켓": {"country": "태국", "city": "푸켓", "lat": 7.8804, "lng": 98.3923},
    "파타야": {"country": "태국", "city": "파타야", "lat": 12.9276, "lng": 100.8771},
    "태국": {"country": "태국", "city": "방콕", "lat": 13.7563, "lng": 100.5018},
    "다낭": {"country": "베트남", "city": "다낭", "lat": 16.0544, "lng": 108.2022},
    "하노이": {"country": "베트남", "city": "하노이", "lat": 21.0285, "lng": 105.8542},
    "호치민": {"country": "베트남", "city": "호치민", "lat": 10.8231, "lng": 106.6297},
    "나트랑": {"country": "베트남", "city": "나트랑", "lat": 12.2388, "lng": 109.1967},
    "푸꾸옥": {"country": "베트남", "city": "푸꾸옥", "lat": 10.2899, "lng": 103.9840},
    "달랏": {"country": "베트남", "city": "달랏", "lat": 11.9404, "lng": 108.4583},
    "베트남": {"country": "베트남", "city": "다낭", "lat": 16.0544, "lng": 108.2022},
    "방비엥": {"country": "라오스", "city": "방비엥", "lat": 18.9224, "lng": 102.4475},
    "루앙프라방": {"country": "라오스", "city": "루앙프라방", "lat": 19.8893, "lng": 102.1340},
    "비엔티안": {"country": "라오스", "city": "비엔티안", "lat": 17.9757, "lng": 102.6331},
    "라오스": {"country": "라오스", "city": "방비엥", "lat": 18.9224, "lng": 102.4475},
    "발리": {"country": "인도네시아", "city": "발리", "lat": -8.4095, "lng": 115.1889},
    "인도네시아": {"country": "인도네시아", "city": "발리", "lat": -8.4095, "lng": 115.1889},
    "세부": {"country": "필리핀", "city": "세부", "lat": 10.3157, "lng": 123.8854},
    "보라카이": {"country": "필리핀", "city": "보라카이", "lat": 11.9674, "lng": 121.9248},
    "마닐라": {"country": "필리핀", "city": "마닐라", "lat": 14.5995, "lng": 120.9842},
    "필리핀": {"country": "필리핀", "city": "세부", "lat": 10.3157, "lng": 123.8854},
    "싱가포르": {"country": "싱가포르", "city": "싱가포르", "lat": 1.3521, "lng": 103.8198},
    "쿠알라룸푸르": {"country": "말레이시아", "city": "쿠알라룸푸르", "lat": 3.1390, "lng": 101.6869},
    "코타키나발루": {"country": "말레이시아", "city": "코타키나발루", "lat": 5.9804, "lng": 116.0735},
    "말레이시아": {"country": "말레이시아", "city": "쿠알라룸푸르", "lat": 3.1390, "lng": 101.6869},

    # --- 남아시아 ---
    "바라나시": {"country": "인도", "city": "바라나시", "lat": 25.3176, "lng": 82.9739},
    "뉴델리": {"country": "인도", "city": "뉴델리", "lat": 28.6139, "lng": 77.2090},
    "델리": {"country": "인도", "city": "뉴델리", "lat": 28.6139, "lng": 77.2090},
    "뭄바이": {"country": "인도", "city": "뭄바이", "lat": 19.0760, "lng": 72.8777},
    "자이푸르": {"country": "인도", "city": "자이푸르", "lat": 26.9124, "lng": 75.7873},
    "인도": {"country": "인도", "city": "바라나시", "lat": 25.3176, "lng": 82.9739},
    "방글라데시": {"country": "방글라데시", "city": "다카", "lat": 23.8103, "lng": 90.4125},
    "다카": {"country": "방글라데시", "city": "다카", "lat": 23.8103, "lng": 90.4125},
    "카트만두": {"country": "네팔", "city": "카트만두", "lat": 27.7172, "lng": 85.3240},
    "네팔": {"country": "네팔", "city": "카트만두", "lat": 27.7172, "lng": 85.3240},
    "스리랑카": {"country": "스리랑카", "city": "콜롬보", "lat": 6.9271, "lng": 79.8612},

    # --- 중앙아시아 & 몽골 ---
    "타슈켄트": {"country": "우즈베키스탄", "city": "타슈켄트", "lat": 41.2995, "lng": 69.2401},
    "사마르칸트": {"country": "우즈베키스탄", "city": "사마르칸트", "lat": 39.6548, "lng": 66.9757},
    "부하라": {"country": "우즈베키스탄", "city": "부하라", "lat": 39.7681, "lng": 64.4556},
    "우즈베키스탄": {"country": "우즈베키스탄", "city": "타슈켄트", "lat": 41.2995, "lng": 69.2401},
    "알마티": {"country": "카자흐스탄", "city": "알마티", "lat": 43.2389, "lng": 76.8897},
    "아스타나": {"country": "카자흐스탄", "city": "아스타나", "lat": 51.1694, "lng": 71.4491},
    "카자흐스탄": {"country": "카자흐스탄", "city": "알마티", "lat": 43.2389, "lng": 76.8897},
    "비슈케크": {"country": "키르기스스탄", "city": "비슈케크", "lat": 42.8746, "lng": 74.5698},
    "키르기스스탄": {"country": "키르기스스탄", "city": "비슈케크", "lat": 42.8746, "lng": 74.5698},
    "울란바토르": {"country": "몽골", "city": "울란바토르", "lat": 47.9212, "lng": 106.9186},
    "테를지": {"country": "몽골", "city": "울란바토르", "lat": 47.8864, "lng": 107.4258},
    "몽골": {"country": "몽골", "city": "울란바토르", "lat": 47.9212, "lng": 106.9186},

    # --- 코카서스 ---
    "바쿠": {"country": "아제르바이잔", "city": "바쿠", "lat": 40.4093, "lng": 49.8671},
    "아제르바이잔": {"country": "아제르바이잔", "city": "바쿠", "lat": 40.4093, "lng": 49.8671},
    "트빌리시": {"country": "조지아", "city": "트빌리시", "lat": 41.7151, "lng": 44.8271},
    "카즈베기": {"country": "조지아", "city": "카즈베기", "lat": 42.6587, "lng": 44.6417},
    "바투미": {"country": "조지아", "city": "바투미", "lat": 41.6168, "lng": 41.6367},
    "조지아": {"country": "조지아", "city": "트빌리시", "lat": 41.7151, "lng": 44.8271},
    "예레반": {"country": "아르메니아", "city": "예레반", "lat": 40.1792, "lng": 44.4991},
    "아르메니아": {"country": "아르메니아", "city": "예레반", "lat": 40.1792, "lng": 44.4991},

    # --- 중동 & 북아프리카 & 튀르키예 ---
    "이스탄불": {"country": "튀르키예", "city": "이스탄불", "lat": 41.0082, "lng": 28.9784},
    "카파도키아": {"country": "튀르키예", "city": "카파도키아", "lat": 38.6431, "lng": 34.8289},
    "안탈리아": {"country": "튀르키예", "city": "안탈리아", "lat": 36.8969, "lng": 30.7133},
    "튀르키예": {"country": "튀르키예", "city": "이스탄불", "lat": 41.0082, "lng": 28.9784},
    "터키": {"country": "튀르키예", "city": "이스탄불", "lat": 41.0082, "lng": 28.9784},
    "다합": {"country": "이집트", "city": "다합", "lat": 28.5097, "lng": 34.5136},
    "카이로": {"country": "이집트", "city": "카이로", "lat": 30.0444, "lng": 31.2357},
    "룩소르": {"country": "이집트", "city": "룩소르", "lat": 25.6872, "lng": 32.6396},
    "이집트": {"country": "이집트", "city": "카이로", "lat": 30.0444, "lng": 31.2357},
    "사하라": {"country": "모로코", "city": "사하라 사막", "lat": 31.0802, "lng": -4.0133},
    "마라케시": {"country": "모로코", "city": "마라케시", "lat": 31.6295, "lng": -7.9811},
    "카사블랑카": {"country": "모로코", "city": "카사블랑카", "lat": 33.5731, "lng": -7.5898},
    "모로코": {"country": "모로코", "city": "마라케시", "lat": 31.6295, "lng": -7.9811},
    "두바이": {"country": "아랍에미리트", "city": "두바이", "lat": 25.2048, "lng": 55.2708},
    "남아공": {"country": "남아프리카공화국", "city": "케이프타운", "lat": -33.9249, "lng": 18.4241},

    # --- 유럽 ---
    "파리": {"country": "프랑스", "city": "파리", "lat": 48.8566, "lng": 2.3522},
    "니스": {"country": "프랑스", "city": "니스", "lat": 43.7102, "lng": 7.2620},
    "프랑스": {"country": "프랑스", "city": "파리", "lat": 48.8566, "lng": 2.3522},
    "런던": {"country": "영국", "city": "런던", "lat": 51.5074, "lng": -0.1278},
    "영국": {"country": "영국", "city": "런던", "lat": 51.5074, "lng": -0.1278},
    "로마": {"country": "이탈리아", "city": "로마", "lat": 41.9028, "lng": 12.4964},
    "베네치아": {"country": "이탈리아", "city": "베네치아", "lat": 45.4408, "lng": 12.3155},
    "피렌체": {"country": "이탈리아", "city": "피렌체", "lat": 43.7696, "lng": 11.2558},
    "밀라노": {"country": "이탈리아", "city": "밀라노", "lat": 45.4642, "lng": 9.1900},
    "이탈리아": {"country": "이탈리아", "city": "로마", "lat": 41.9028, "lng": 12.4964},
    "바르셀로나": {"country": "스페인", "city": "바르셀로나", "lat": 41.3851, "lng": 2.1734},
    "마드리드": {"country": "스페인", "city": "마드리드", "lat": 40.4168, "lng": -3.7038},
    "세비야": {"country": "스페인", "city": "세비야", "lat": 37.3891, "lng": -5.9845},
    "스페인": {"country": "스페인", "city": "바르셀로나", "lat": 41.3851, "lng": 2.1734},
    "인터라켄": {"country": "스위스", "city": "인터라켄", "lat": 46.6863, "lng": 7.8632},
    "취리히": {"country": "스위스", "city": "취리히", "lat": 47.3769, "lng": 8.5417},
    "제네바": {"country": "스위스", "city": "제네바", "lat": 46.2044, "lng": 6.1432},
    "스위스": {"country": "스위스", "city": "인터라켄", "lat": 46.6863, "lng": 7.8632},
    "암스테르담": {"country": "네덜란드", "city": "암스테르담", "lat": 52.3676, "lng": 4.9041},
    "네덜란드": {"country": "네덜란드", "city": "암스테르담", "lat": 52.3676, "lng": 4.9041},
    "룩셈부르크": {"country": "룩셈부르크", "city": "룩셈부르크", "lat": 49.6116, "lng": 6.1319},
    "더블린": {"country": "아일랜드", "city": "더블린", "lat": 53.3498, "lng": -6.2603},
    "아일랜드": {"country": "아일랜드", "city": "더블린", "lat": 53.3498, "lng": -6.2603},
    "바르샤바": {"country": "폴란드", "city": "바르샤바", "lat": 52.2297, "lng": 21.0122},
    "크라쿠프": {"country": "폴란드", "city": "크라쿠프", "lat": 50.0647, "lng": 19.9450},
    "폴란드": {"country": "폴란드", "city": "바르샤바", "lat": 52.2297, "lng": 21.0122},
    "헬싱키": {"country": "핀란드", "city": "헬싱키", "lat": 60.1699, "lng": 24.9384},
    "핀란드": {"country": "핀란드", "city": "헬싱키", "lat": 60.1699, "lng": 24.9384},
    "프라하": {"country": "체코", "city": "프라하", "lat": 50.0755, "lng": 14.4378},
    "체코": {"country": "체코", "city": "프라하", "lat": 50.0755, "lng": 14.4378},
    "부다페스트": {"country": "헝가리", "city": "부다페스트", "lat": 47.4979, "lng": 19.0402},
    "헝가리": {"country": "헝가리", "city": "부다페스트", "lat": 47.4979, "lng": 19.0402},
    "비엔나": {"country": "오스트리아", "city": "비엔나", "lat": 48.2082, "lng": 16.3738},
    "오스트리아": {"country": "오스트리아", "city": "비엔나", "lat": 48.2082, "lng": 16.3738},
    "포르투": {"country": "포르투갈", "city": "포르투", "lat": 41.1579, "lng": -8.6291},
    "리스본": {"country": "포르투갈", "city": "리스본", "lat": 38.7223, "lng": -9.1393},
    "포르투갈": {"country": "포르투갈", "city": "리스본", "lat": 38.7223, "lng": -9.1393},
    "지중해": {"country": "남유럽", "city": "지중해", "lat": 35.0, "lng": 18.0},

    # --- 아메리카 & 오세아니아 ---
    "뉴욕": {"country": "미국", "city": "뉴욕", "lat": 40.7128, "lng": -74.0060},
    "로스앤젤레스": {"country": "미국", "city": "로스앤젤레스", "lat": 34.0522, "lng": -118.2437},
    "마이애미": {"country": "미국", "city": "마이애미", "lat": 25.7617, "lng": -80.1918},
    "하와이": {"country": "미국", "city": "하와이", "lat": 21.3069, "lng": -157.8583},
    "라스베이거스": {"country": "미국", "city": "라스베이거스", "lat": 36.1699, "lng": -115.1398},
    "샌프란시스코": {"country": "미국", "city": "샌프란시스코", "lat": 37.7749, "lng": -122.4194},
    "시드니": {"country": "호주", "city": "시드니", "lat": -33.8688, "lng": 151.2093},
    "멜버른": {"country": "호주", "city": "멜버른", "lat": -37.8136, "lng": 144.9631},
    "호주": {"country": "호주", "city": "시드니", "lat": -33.8688, "lng": 151.2093},
    "부에노스아이레스": {"country": "아르헨티나", "city": "부에노스아이레스", "lat": -34.6037, "lng": -58.3816},
    "파타고니아": {"country": "아르헨티나", "city": "파타고니아", "lat": -50.0, "lng": -70.0},
    "아르헨티나": {"country": "아르헨티나", "city": "부에노스아이레스", "lat": -34.6037, "lng": -58.3816},
    "리우데자네이루": {"country": "브라질", "city": "리우데자네이루", "lat": -22.9068, "lng": -43.1729},
    "브라질": {"country": "브라질", "city": "리우데자네이루", "lat": -22.9068, "lng": -43.1729},
    "리마": {"country": "페루", "city": "리마", "lat": -12.0464, "lng": -77.0428},
    "쿠스코": {"country": "페루", "city": "쿠스코", "lat": -13.5319, "lng": -71.9675},
    "페루": {"country": "페루", "city": "리마", "lat": -12.0464, "lng": -77.0428}
}

COUNTRY_FLAGS = {
    "🇨🇳": "중국", "🇯🇵": "일본", "🇮🇹": "이탈리아", "🇻🇳": "베트남",
    "🇰🇬": "키르기스스탄", "🇹🇷": "튀르키예", "🇵🇱": "폴란드", "🇮🇪": "아일랜드",
    "🇧🇩": "방글라데시", "🇨🇭": "스위스", "🇹🇭": "태국", "🇳🇱": "네덜란드",
    "🇱🇺": "룩셈부르크", "🇦🇷": "아르헨티나", "🇫🇮": "핀란드", "🇺🇸": "미국",
    "🇬🇧": "영국", "🇫🇷": "프랑스", "🇪🇸": "스페인", "🇲🇳": "몽골",
    "🇪🇬": "이집트", "🇮🇳": "인도", "🇬🇪": "조지아", "🇺🇿": "우즈베키스탄",
    "🇵🇭": "필리핀", "🇲🇾": "말레이시아", "🇸🇬": "싱가포르", "🇩🇪": "독일"
}

DATA_JS_PATH = os.path.join(os.path.dirname(__file__), "js", "data.js")
DATA_RECENT_PATH = os.path.join(os.path.dirname(__file__), "js", "data", "videos_recent.js")
DATA_ARCHIVE_PATH = os.path.join(os.path.dirname(__file__), "js", "data", "videos_archive.js")

# SSL 컨텍스트 준비 (macOS 및 호스트 인증서 오류 안전 방어)
def get_ssl_context():
    try:
        ctx = ssl.create_default_context()
        return ctx
    except Exception:
        return ssl._create_unverified_context()

SAFE_SSL_CONTEXT = ssl._create_unverified_context()

# =============================================================================
# 3. 헬퍼 및 크롤링 함수들
# =============================================================================

def parse_relative_time(rel_text):
    """
    유튜브 상대 시간 문자열('1개월 전', '2주 전', '5일 전' 등)을 일 단위와 YYYY-MM-DD 날짜로 변환
    """
    now = datetime.now()
    if not rel_text:
        return 0, now.strftime("%Y-%m-%d")
    
    rel = rel_text.strip()

    # 초, 분, 시간 전
    if re.search(r'초\s*전|분\s*전|시간\s*전|방금', rel):
        return 0, now.strftime("%Y-%m-%d")

    # 일 전
    m = re.search(r'(\d+)\s*일\s*전', rel)
    if m:
        days = int(m.group(1))
        d = now - timedelta(days=days)
        return days, d.strftime("%Y-%m-%d")

    # 주 전
    m = re.search(r'(\d+)\s*주\s*전', rel)
    if m:
        weeks = int(m.group(1))
        days = weeks * 7
        d = now - timedelta(days=days)
        return days, d.strftime("%Y-%m-%d")

    # 개월 전
    m = re.search(r'(\d+)\s*개월\s*전', rel)
    if m:
        months = int(m.group(1))
        days = months * 30
        d = now - timedelta(days=days)
        return days, d.strftime("%Y-%m-%d")

    # 년 전
    m = re.search(r'(\d+)\s*년\s*전', rel)
    if m:
        years = int(m.group(1))
        days = years * 365
        d = now - timedelta(days=days)
        return days, d.strftime("%Y-%m-%d")

    # 영문 표기 대비
    if "hour" in rel or "minute" in rel or "second" in rel:
        return 0, now.strftime("%Y-%m-%d")
    m = re.search(r'(\d+)\s*day', rel)
    if m:
        days = int(m.group(1))
        return days, (now - timedelta(days=days)).strftime("%Y-%m-%d")
    m = re.search(r'(\d+)\s*week', rel)
    if m:
        days = int(m.group(1)) * 7
        return days, (now - timedelta(days=days)).strftime("%Y-%m-%d")
    m = re.search(r'(\d+)\s*month', rel)
    if m:
        days = int(m.group(1)) * 30
        return days, (now - timedelta(days=days)).strftime("%Y-%m-%d")
    m = re.search(r'(\d+)\s*year', rel)
    if m:
        days = int(m.group(1)) * 365
        return days, (now - timedelta(days=days)).strftime("%Y-%m-%d")

    return 0, now.strftime("%Y-%m-%d")

def parse_subscriber_count(html):
    """
    유튜브 채널 메타데이터에서 구독자 수를 파싱하여 정수로 반환.
    예: '구독자 245만명' -> 2450000, '52.3만명' -> 523000, '1.2M' -> 1200000, '50K' -> 50000
    """
    # 1. '구독자 X만명' 패턴 (한국어)
    m = re.search(r'구독자\s*([\d\.]+)\s*만명', html)
    if m:
        try:
            return int(float(m.group(1)) * 10000)
        except ValueError:
            pass

    # 2. '구독자 X천명'
    m = re.search(r'구독자\s*([\d\.]+)\s*천명', html)
    if m:
        try:
            return int(float(m.group(1)) * 1000)
        except ValueError:
            pass

    # 3. '구독자 X명' (단순 숫자)
    m = re.search(r'구독자\s*([\d,]+)\s*명', html)
    if m:
        try:
            return int(m.group(1).replace(',', ''))
        except ValueError:
            pass

    # 4. 영문 표기: 'subscriberCountText': '2.45M subscribers' 또는 '50K subscribers'
    m = re.search(r'([\d\.]+)\s*M\s*subscribers', html, re.IGNORECASE)
    if m:
        try:
            return int(float(m.group(1)) * 1000000)
        except ValueError:
            pass

    m = re.search(r'([\d\.]+)\s*K\s*subscribers', html, re.IGNORECASE)
    if m:
        try:
            return int(float(m.group(1)) * 1000)
        except ValueError:
            pass

    return None

def fetch_channel_videos(channel_info):
    """
    유튜브 채널의 최신 영상 목록을 가져옴:
    1차: 채널 동영상 탭 (https://www.youtube.com/@{handle}/videos) 직접 파싱 (100% 안정적, HTTP 200)
    2차: 채널 공식 RSS 피드 (폴백용)
    """
    handle = channel_info.get("handle")
    channel_id = channel_info.get("channel_id")
    videos = []

    # 1차 방식: 채널 동영상 탭 직접 HTML/JSON 파싱
    if handle:
        url = f"https://www.youtube.com/@{handle}/videos"
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=12, context=SAFE_SSL_CONTEXT) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                
                # 구독자 수 실시간 검증 (5만 명 이상 기준)
                subs = parse_subscriber_count(html)
                if subs is not None:
                    if subs < MIN_SUBSCRIBER_COUNT:
                        print(f"      [!] ❌ 구독자 수 미달 ({subs:,}명 < {MIN_SUBSCRIBER_COUNT:,}명 기준) -> 채널 자동 제외")
                        return []
                    else:
                        print(f"      [i] 👥 구독자 수: {subs:,}명 (기준 5만+ 통과)")

                # ytInitialData 추출
                idx = html.find("var ytInitialData = ")
                if idx != -1:
                    end_idx = html.find(";</script>", idx)
                    if end_idx != -1:
                        raw_json = html[idx + len("var ytInitialData = "):end_idx]
                        try:
                            data = json.loads(raw_json)
                            tabs = data.get("contents", {}).get("twoColumnBrowseResultsRenderer", {}).get("tabs", [])
                            for tab in tabs:
                                tab_renderer = tab.get("tabRenderer", {})
                                if tab_renderer.get("selected") or tab_renderer.get("title") in ["동영상", "Videos"]:
                                    contents = tab_renderer.get("content", {}).get("richGridRenderer", {}).get("contents", [])
                                    for item in contents:
                                        rich_item = item.get("richItemRenderer", {}).get("content", {})
                                        # 최신 YouTube UI: lockupViewModel
                                        lvm = rich_item.get("lockupViewModel")
                                        if lvm:
                                            vid = lvm.get("contentId")
                                            meta = lvm.get("metadata", {}).get("lockupMetadataViewModel", {})
                                            title = meta.get("title", {}).get("content", "")
                                            rows = meta.get("metadata", {}).get("contentMetadataViewModel", {}).get("metadataRows", [])
                                            rel_time = ""
                                            for row in rows:
                                                for part in row.get("metadataParts", []):
                                                    txt = part.get("text", {}).get("content", "")
                                                    if "전" in txt or "ago" in txt:
                                                        rel_time = txt
                                            
                                            days_ago, pub_date = parse_relative_time(rel_time)
                                            if vid and title:
                                                videos.append({
                                                    "youtube_id": vid,
                                                    "title": title,
                                                    "published": pub_date,
                                                    "days_ago": days_ago,
                                                    "rel_time": rel_time,
                                                    "description": title
                                                })
                                        # 구형 UI 호환: videoRenderer
                                        elif "videoRenderer" in rich_item:
                                            vr = rich_item["videoRenderer"]
                                            vid = vr.get("videoId")
                                            title = vr.get("title", {}).get("runs", [{}])[0].get("text", "")
                                            rel_time = vr.get("publishedTimeText", {}).get("simpleText", "")
                                            days_ago, pub_date = parse_relative_time(rel_time)
                                            if vid and title:
                                                videos.append({
                                                    "youtube_id": vid,
                                                    "title": title,
                                                    "published": pub_date,
                                                    "days_ago": days_ago,
                                                    "rel_time": rel_time,
                                                    "description": title
                                                })
                                    break
                        except Exception as parse_err:
                            pass

                # JSON 파싱 미성공 시 안전한 정규식 추출 폴백
                if not videos:
                    id_matches = re.findall(r'"contentId":"([a-zA-Z0-9_-]{11})"', html)
                    title_matches = re.findall(r'"title":\{"content":"(.*?)"\}', html)
                    for i in range(min(len(id_matches), len(title_matches))):
                        vid = id_matches[i]
                        tit = title_matches[i].encode('utf-8').decode('unicode-escape', errors='ignore')
                        videos.append({
                            "youtube_id": vid,
                            "title": tit,
                            "published": datetime.now().strftime("%Y-%m-%d"),
                            "days_ago": 0,
                            "rel_time": "최근",
                            "description": tit
                        })
        except Exception as e:
            print(f"⚠️ 채널 페이지 조회 실패 (@{handle}): {e}")

    # 2차 방식: RSS 피드 폴백 (1차 결과가 비어있고 channel_id가 있을 경우)
    if not videos and channel_id:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=8, context=SAFE_SSL_CONTEXT) as resp:
                xml_data = resp.read()
                root = ET.fromstring(xml_data)
                ns = {
                    "atom": "http://www.w3.org/2005/Atom",
                    "yt": "http://www.youtube.com/xml/schemas/2015",
                    "media": "http://search.yahoo.com/mrss/"
                }
                for entry in root.findall("atom:entry", ns):
                    video_id = entry.find("yt:videoId", ns)
                    title = entry.find("atom:title", ns)
                    published = entry.find("atom:published", ns)
                    desc = ""
                    media_group = entry.find("media:group", ns)
                    if media_group is not None:
                        desc_el = media_group.find("media:description", ns)
                        if desc_el is not None and desc_el.text:
                            desc = desc_el.text

                    if video_id is not None and title is not None:
                        pub_str = published.text[:10] if published is not None and published.text else datetime.now().strftime("%Y-%m-%d")
                        try:
                            pub_dt = datetime.strptime(pub_str, "%Y-%m-%d")
                            days_ago = (datetime.now() - pub_dt).days
                        except Exception:
                            days_ago = 0

                        videos.append({
                            "youtube_id": video_id.text,
                            "title": title.text,
                            "published": pub_str,
                            "days_ago": days_ago,
                            "rel_time": f"{days_ago}일 전",
                            "description": desc
                        })
        except Exception:
            pass

    return videos

def load_existing_video_ids():
    """기존 데이터 파일들에서 이미 등록된 youtubeId 목록을 로드"""
    existing_ids = set()
    for path in [DATA_RECENT_PATH, DATA_ARCHIVE_PATH, DATA_JS_PATH]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            ids = set(re.findall(r'youtubeId:\s*["\']([a-zA-Z0-9_-]{11})["\']', content))
            existing_ids.update(ids)
    return existing_ids

def geocode_location(place_query):
    """지오코딩 API 폴백 (Nominatim & Photon 지원)"""
    try:
        encoded_query = urllib.parse.quote(place_query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TubeMapTravelBot/1.0 (https://github.com/bywalk/tubemap)"}
        )
        with urllib.request.urlopen(req, timeout=5, context=SAFE_SSL_CONTEXT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                return round(lat, 4), round(lng, 4)
    except Exception:
        pass
    return None, None

def load_local_env():
    """로컬 .env 파일에서 환경변수 로드"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

def extract_with_gemini_api(title, description, creator_name):
    """
    사전 매칭에 실패한 영상에 대해 Gemini API로 장소 및 위경도 자동 추출
    """
    load_local_env()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None

    prompt = f"""
당신은 여행 영상 정보 분석 전문가입니다.
주어진 YouTube 영상 제목과 설명란을 분석하여, 실제로 여행하고 있는 장소 정보를 다음 JSON 형식으로만 추출하세요.
국내/해외 무관하며, 모호하거나 특정 여행지가 아니라면 "is_travel": false로 반환하세요.

반환 형식 (반드시 유효한 JSON만 반환):
{{
  "is_travel": true,
  "country": "국가명 (예: 인도, 아랍에미리트, 미국)",
  "city": "도시/지역명 (예: 바라나시, 두바이, 샌프란시스코)",
  "spot": "구체적인 명소명 (예: 갠지스강, 버즈 알아랍, 소살리토)",
  "lat": 위도(실수, 예: 25.3176),
  "lng": 경도(실수, 예: 83.0062),
  "tip": "영상에서 알 수 있는 핵심 꿀팁/특징 (한 줄 요약)"
}}

영상 제목: {title}
영상 설명: {description}
"""

    models_to_try = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-pro-latest"]
    for model_name in models_to_try:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "response_mime_type": "application/json",
                    "temperature": 0.1
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12, context=SAFE_SSL_CONTEXT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text_out)
                if parsed.get("is_travel") and parsed.get("lat") and parsed.get("lng"):
                    city = parsed.get("city") or "여행지"
                    country = parsed.get("country") or "해외"
                    spot = parsed.get("spot") or city
                    tip = parsed.get("tip") or f"{creator_name}의 {city} 여행 추천 스팟입니다."
                    return {
                        "country": country,
                        "city": city,
                        "locationName": f"{city} {spot}" if spot != city else city,
                        "lat": float(parsed["lat"]),
                        "lng": float(parsed["lng"]),
                        "tags": [city, country, "유튜브추천", "Gemini추출"],
                        "tip": tip
                    }
        except Exception:
            continue

    return None

def analyze_video_location(title, description, creator_name):
    """
    영상 제목 및 설명에서 여행 국가, 도시, 스팟명, 좌표, 꿀팁, 태그 추출
    - 정밀 키워드 사전 (DESTINATION_DICTIONARY)
    - 국가 깃발 이모지 (COUNTRY_FLAGS)
    - 제목 대괄호/말머리 패턴 ([...], 【...】) 자동 파싱
    """
    full_text = f"{title} {description}"

    # 1. 길이 역순 정렬된 정밀 사전 키워드 매칭
    sorted_keywords = sorted(DESTINATION_DICTIONARY.keys(), key=lambda k: len(k), reverse=True)
    for kw in sorted_keywords:
        if kw in full_text:
            spot_data = DESTINATION_DICTIONARY[kw]
            country = spot_data["country"]
            city = spot_data["city"]
            location_name = f"{city} {kw}" if kw != city and kw != country else f"{city} 주요 명소"

            tip_templates = {
                "빠니보틀": f"빠니보틀이 방문한 {city} 현지 로컬 추천 코스입니다.",
                "곽튜브": f"곽튜브가 강력 추천한 {city} 가성비 맛집 & 명소입니다.",
                "원지의 하루": f"원지가 경험한 {city} 소소하고 아늑한 힐링 스팟입니다.",
                "채코제": f"채코제가 소개한 {city} 현지 분위기 가득한 로컬 스팟입니다.",
                "여행가 제이": f"여행가 제이의 실전 노하우가 담긴 {city} 여행지입니다.",
                "잰잰바리": f"잰잰바리가 만난 {city}의 따뜻하고 정겨운 여행지입니다.",
                "노마드션": f"노마드션의 로드트립 추천 {city} 여행 코스입니다.",
                "캡틴따거": f"캡틴따거가 전하는 {city}의 역사와 숨은 이야기 명소입니다.",
                "캐럿맨 여행기": f"캐럿맨의 생생한 모험이 담긴 {city} 추천 스팟입니다.",
                "희철리즘": f"희철리즘이 인터뷰한 {city} 현지인들의 진짜 삶의 현장입니다.",
                "또떠남": f"또떠남의 프리미엄 호텔 & 최적 동선 가이드 추천 스팟입니다.",
                "쏘이 The World": f"쏘이가 경험한 {city} 안전하고 매력적인 추천 여행지입니다.",
                "초마드": f"초마드가 소개한 {city} 럭셔리 호캉스 & 핫플레이스입니다."
            }
            tip = tip_templates.get(creator_name, f"{creator_name}의 {city} 여행 영상 추천 스팟입니다.")

            return {
                "country": country,
                "city": city,
                "locationName": location_name,
                "lat": spot_data["lat"],
                "lng": spot_data["lng"],
                "tags": [city, country, "유튜브추천", "여행"],
                "tip": tip
            }

    # 2. 제목 내 국가 국기 이모지 파싱
    for flag, country in COUNTRY_FLAGS.items():
        if flag in title:
            # 해당 국가의 대표 도시 확인
            for kw, spot_data in DESTINATION_DICTIONARY.items():
                if spot_data["country"] == country:
                    return {
                        "country": country,
                        "city": spot_data["city"],
                        "locationName": f"{country} {spot_data['city']}",
                        "lat": spot_data["lat"],
                        "lng": spot_data["lng"],
                        "tags": [spot_data["city"], country, "여행"],
                        "tip": f"{creator_name}의 {country} 여행기 추천 명소."
                    }

    # 3. 괄호 안의 후보명 추출 및 지오코딩 시도 (예: 【방글라데시2】 -> 방글라데시)
    bracket_match = re.search(r'\[(.*?)\]|【(.*?)】|\((.*?)\)', title)
    if bracket_match:
        raw_candidate = next(c for c in bracket_match.groups() if c)
        clean_candidate = re.sub(r'[\d_#\s下上]+$', '', raw_candidate).strip()
        if clean_candidate in DESTINATION_DICTIONARY:
            spot_data = DESTINATION_DICTIONARY[clean_candidate]
            return {
                "country": spot_data["country"],
                "city": spot_data["city"],
                "locationName": f"{spot_data['city']} ({clean_candidate})",
                "lat": spot_data["lat"],
                "lng": spot_data["lng"],
                "tags": [spot_data["city"], spot_data["country"], "여행"],
                "tip": f"{creator_name}의 추천 여행 스팟."
            }
        
        # 외부 지오코딩 시도
        lat, lng = geocode_location(clean_candidate)
        if lat and lng:
            return {
                "country": "해외",
                "city": clean_candidate,
                "locationName": clean_candidate,
                "lat": lat,
                "lng": lng,
                "tags": [clean_candidate, "여행"],
                "tip": f"{creator_name}의 추천 여행 스팟."
            }

    # 4. 사전 매칭 실패 시: Gemini LLM Fallback (AI 기반 위치 및 위경도 추출)
    gemini_result = extract_with_gemini_api(title, description, creator_name)
    if gemini_result:
        return gemini_result

    return None

def append_to_data_js(new_entries):
    """새로 발견된 여행 영상 목록을 videos_recent.js 파일 상단에 깔끔하게 추가"""
    target_path = DATA_RECENT_PATH if os.path.exists(DATA_RECENT_PATH) else DATA_JS_PATH
    if not new_entries or not os.path.exists(target_path):
        return

    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # RECENT_VIDEOS 또는 INITIAL_TRAVEL_VIDEOS 배열 위치 찾기
    insert_pos = content.find("const RECENT_VIDEOS = [")
    if insert_pos == -1:
        insert_pos = content.find("const INITIAL_TRAVEL_VIDEOS = [")
    if insert_pos == -1:
        print(f"❌ {target_path} 파일에서 대상 배열을 찾을 수 없습니다.")
        return

    bracket_pos = content.find("[", insert_pos) + 1
    
    formatted_entries = []
    for item in new_entries:
        escaped_title = item['title'].replace('"', '\\"')
        escaped_loc = item['locationName'].replace('"', '\\"')
        escaped_tip = item['tip'].replace('"', '\\"')
        tags_json = json.dumps(item['tags'], ensure_ascii=False)
        pub_date = item.get('publishedAt', datetime.now().strftime("%Y-%m-%d"))
        
        entry_str = f"""
  // [신규 자동 수집] {item['creator']} - {escaped_loc} ({pub_date})
  {{
    id: "auto-{item['youtubeId']}",
    creator: "{item['creator']}",
    youtubeId: "{item['youtubeId']}",
    title: "{escaped_title}",
    channel: "{item['creator']}",
    country: "{item['country']}",
    city: "{item['city']}",
    locationName: "{escaped_loc}",
    lat: {item['lat']},
    lng: {item['lng']},
    tags: {tags_json},
    tip: "{escaped_tip}",
    publishedAt: "{pub_date}",
    description: "{escaped_title}",
    highlights: []
  }},"""
        formatted_entries.append(entry_str)

    new_content = content[:bracket_pos] + "".join(formatted_entries) + content[bracket_pos:]

    with open(target_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    file_basename = os.path.basename(target_path)
    print(f"\n🎉 {file_basename} 파일에 총 {len(new_entries)}개의 최신 여행지가 성공적으로 추가되었습니다!")

# =============================================================================
# 4. 메인 실행 흐름
# =============================================================================
def main():
    print("=" * 70)
    print("📍 TubeMap Travel - 한국 대표 여행 유튜버 (13팀) 최신 영상 자동 수집기")
    print(f"⏰ 실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 필터 기준: 최근 {MAX_VIDEO_AGE_DAYS}일(1년) 이내 최신 영상만 수집")
    print("=" * 70)

    existing_ids = load_existing_video_ids()
    print(f"📦 현재 data.js에 등록된 여행 영상 수: {len(existing_ids)}편\n")

    new_discovered_spots = []

    for idx, ch in enumerate(CHANNELS, 1):
        name = ch["name"]
        handle = ch["handle"]

        print(f"📡 [{idx:2d}/{len(CHANNELS)}] {name} (@{handle}) 최신 영상 수집 중...")
        videos = fetch_channel_videos(ch)
        time.sleep(0.3)  # 정중한 요청 간격 준수

        if not videos:
            print(f"   ⚠️ 영상을 가져오지 못했습니다. 건너뜁니다.")
            continue

        unregistered = [v for v in videos if v["youtube_id"] not in existing_ids]

        if not unregistered:
            print(f"   ✓ 새로운 신규 영상 없음 (최근 영상 모두 이미 등록됨)")
            continue

        print(f"   ✨ 미등록 영상 {len(unregistered)}편 확인 중...")

        creator_matched_count = 0
        for v in unregistered:
            days_ago = v.get("days_ago", 0)
            pub_date = v.get("published", "")

            # 1년(365일) 이내 최신 영상인지 엄격히 검사
            if days_ago > MAX_VIDEO_AGE_DAYS:
                continue

            spot_info = analyze_video_location(v["title"], v["description"], name)
            
            if spot_info:
                entry = {
                    "creator": name,
                    "youtubeId": v["youtube_id"],
                    "title": v["title"],
                    "country": spot_info["country"],
                    "city": spot_info["city"],
                    "locationName": spot_info["locationName"],
                    "lat": spot_info["lat"],
                    "lng": spot_info["lng"],
                    "tags": spot_info["tags"],
                    "tip": spot_info["tip"],
                    "publishedAt": pub_date
                }
                new_discovered_spots.append(entry)
                # 동일 실행 내 중복 추가 방지
                existing_ids.add(v["youtube_id"])
                creator_matched_count += 1
                print(f"      [+] 📍 {spot_info['country']} {spot_info['city']} ({pub_date}): {v['title'][:38]}...")

        if creator_matched_count == 0:
            print(f"      [-] 최근 영상 중 명확한 여행지 키워드 미감지 (토크/일상 콘텐츠 등)")

    print("\n" + "=" * 70)
    print(f"📊 수집 결과: 총 {len(new_discovered_spots)}개의 새로운 여행지 추출 완료")
    print("=" * 70)

    if not new_discovered_spots:
        print("💡 새로 추가할 여행 영상이 없습니다. 지도가 이미 최신 상태입니다.")
        return

    # CLI 인자 검사: --auto 여부
    is_auto = "--auto" in sys.argv
    if not is_auto:
        print("\n아래 항목들을 data.js에 추가하시겠습니까?")
        for idx, s in enumerate(new_discovered_spots[:10], 1):
            print(f"  {idx:2d}. [{s['creator']}] {s['country']} {s['city']} - {s['title'][:40]}...")
        if len(new_discovered_spots) > 10:
            print(f"  ... 외 {len(new_discovered_spots) - 10}개 추가")
        
        try:
            answer = input("\n👉 data.js에 반영할까요? (Y/n): ").strip().lower()
            if answer not in ["y", "yes", ""]:
                print("작업이 취소되었습니다.")
                return
        except EOFError:
            print("비대화형 환경이 감지되어 자동 반영합니다.")

    append_to_data_js(new_discovered_spots)

if __name__ == "__main__":
    main()
