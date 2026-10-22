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
MIN_SUBSCRIBER_COUNT = 50000  # 최소 구독자 수 필터 (5만 명 이상 채널만 수집)
DISCOVER_MIN_SUBSCRIBER_COUNT = 100000  # 브이로그 자동 발굴 시 엄격한 기준 (10만 명 이상)

CHANNELS_JSON_PATH = os.path.join(os.path.dirname(__file__), "channels.json")

DEFAULT_CHANNELS = [
    {"name": "빠니보틀", "handle": "PaniBottle"},
    {"name": "곽튜브", "handle": "JBKWAK"},
    {"name": "원지의 하루", "handle": "im1G"},
    {"name": "채코제", "handle": "koreanjay"},
    {"name": "여행가 제이", "handle": "jayworldtraveler"},
    {"name": "잰잰바리", "handle": "jaeye0nyy"},
    {"name": "노마드션", "handle": "NomadShaun"},
    {"name": "캡틴따거", "handle": "captainbrother"},
    {"name": "캐럿맨 여행기", "handle": "carrotman1198"},
    {"name": "희철리즘", "handle": "HeechulismTV"},
    {"name": "또떠남", "handle": "ddoddunam"},
    {"name": "쏘이 The World", "handle": "soy_the_world"},
    {"name": "초마드", "handle": "CHOMAD"}
]

def load_channels():
    """channels.json 파일에서 모니터링 대상 채널 목록 로드"""
    if os.path.exists(CHANNELS_JSON_PATH):
        try:
            with open(CHANNELS_JSON_PATH, "r", encoding="utf-8") as f:
                ch_list = json.load(f)
                if isinstance(ch_list, list) and ch_list:
                    return ch_list
        except Exception as e:
            print(f"⚠️ channels.json 로드 중 오류: {e}")
    return DEFAULT_CHANNELS

def save_channels(channels):
    """channels.json 파일에 채널 목록 저장"""
    try:
        with open(CHANNELS_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(channels, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ channels.json 저장 실패: {e}")

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
    "거제도": {"country": "대한민국", "city": "거제", "lat": 34.8806, "lng": 128.6211},
    "경산": {"country": "대한민국", "city": "경산", "lat": 35.8251, "lng": 128.7414},
    "담양": {"country": "대한민국", "city": "담양", "lat": 35.3211, "lng": 126.9882},
    "나주": {"country": "대한민국", "city": "나주", "lat": 35.0158, "lng": 126.7108},
    "무안": {"country": "대한민국", "city": "무안", "lat": 34.9904, "lng": 126.4817},
    "광양": {"country": "대한민국", "city": "광양", "lat": 34.9407, "lng": 127.6959},
    "영주": {"country": "대한민국", "city": "영주", "lat": 36.8057, "lng": 128.6241},
    "용인": {"country": "대한민국", "city": "용인", "lat": 37.2411, "lng": 127.1776},
    "광주": {"country": "대한민국", "city": "광주", "lat": 35.1595, "lng": 126.8526},

    # --- 일본 ---
    "도쿄": {"country": "일본", "city": "도쿄", "lat": 35.6762, "lng": 139.6503},
    "오사카": {"country": "일본", "city": "오사카", "lat": 34.6937, "lng": 135.5023},
    "후쿠오카": {"country": "일본", "city": "후쿠오카", "lat": 33.5904, "lng": 130.4017},
    "삿포로": {"country": "일본", "city": "삿포로", "lat": 43.0618, "lng": 141.3545},
    "교토": {"country": "일본", "city": "교토", "lat": 35.0116, "lng": 135.7681},
    "나고야": {"country": "일본", "city": "나고야", "lat": 35.1815, "lng": 136.9066},
    "오키나와": {"country": "일본", "city": "오키나와", "lat": 26.2124, "lng": 127.6809},
    "유후인": {"country": "일본", "city": "유후인", "lat": 33.2647, "lng": 131.3558},
    "센다이": {"country": "일본", "city": "센다이", "lat": 38.2682, "lng": 140.8694},
    "미야자키": {"country": "일본", "city": "미야자키", "lat": 31.9077, "lng": 131.4202},
    "가고시마": {"country": "일본", "city": "가고시마", "lat": 31.5966, "lng": 130.5571},
    "오비히로": {"country": "일본", "city": "오비히로", "lat": 42.9239, "lng": 143.1966},
    "고토열도": {"country": "일본", "city": "나가사키 고토열도", "lat": 32.6953, "lng": 128.8419},
    "스즈카": {"country": "일본", "city": "미에현 스즈카", "lat": 34.8431, "lng": 136.5407},
    "기타큐슈": {"country": "일본", "city": "기타큐슈", "lat": 33.8835, "lng": 130.8752},
    "오이타": {"country": "일본", "city": "오이타", "lat": 33.2382, "lng": 131.6126},
    "왓카나이": {"country": "일본", "city": "왓카나이", "lat": 45.4156, "lng": 141.6731},
    "홋카이도": {"country": "일본", "city": "삿포로", "lat": 43.0618, "lng": 141.3545},
    "일본": {"country": "일본", "city": "도쿄", "lat": 35.6762, "lng": 139.6503},

    # --- 대만 / 홍콩 / 마카오 / 중국 ---
    "타이베이": {"country": "대만", "city": "타이베이", "lat": 25.0330, "lng": 121.5654},
    "가오슝": {"country": "대만", "city": "가오슝", "lat": 22.6273, "lng": 120.3014},
    "타이난": {"country": "대만", "city": "타이난", "lat": 22.9997, "lng": 120.2270},
    "지룽": {"country": "대만", "city": "지룽", "lat": 25.1276, "lng": 121.7392},
    "금문도": {"country": "대만", "city": "진먼(금문도)", "lat": 24.4493, "lng": 118.3767},
    "진먼": {"country": "대만", "city": "진먼(금문도)", "lat": 24.4493, "lng": 118.3767},
    "대만": {"country": "대만", "city": "타이베이", "lat": 25.0330, "lng": 121.5654},
    "홍콩": {"country": "홍콩", "city": "홍콩", "lat": 22.3193, "lng": 114.1694},
    "마카오": {"country": "마카오", "city": "마카오", "lat": 22.1987, "lng": 113.5439},
    "하이난": {"country": "중국", "city": "하이난", "lat": 18.2528, "lng": 109.5119},
    "싼야": {"country": "중국", "city": "싼야", "lat": 18.2528, "lng": 109.5119},
    "상하이": {"country": "중국", "city": "상하이", "lat": 31.2304, "lng": 121.4737},
    "베이징": {"country": "중국", "city": "베이징", "lat": 39.9042, "lng": 116.4074},
    "칭다오": {"country": "중국", "city": "칭다오", "lat": 36.0671, "lng": 120.3826},
    "웨이하이": {"country": "중국", "city": "웨이하이", "lat": 37.5131, "lng": 122.1204},
    "청두": {"country": "중국", "city": "청두", "lat": 30.5728, "lng": 104.0668},
    "사천": {"country": "중국", "city": "청두", "lat": 30.5728, "lng": 104.0668},
    "쑤저우": {"country": "중국", "city": "쑤저우", "lat": 31.2989, "lng": 120.5853},
    "소주": {"country": "중국", "city": "쑤저우", "lat": 31.2989, "lng": 120.5853},
    "이우": {"country": "중국", "city": "이우", "lat": 29.3069, "lng": 120.0750},
    "중국": {"country": "중국", "city": "상하이", "lat": 31.2304, "lng": 121.4737},

    # --- 동남아시아 ---
    "방콕": {"country": "태국", "city": "방콕", "lat": 13.7563, "lng": 100.5018},
    "치앙마이": {"country": "태국", "city": "치앙마이", "lat": 18.7883, "lng": 98.9853},
    "푸켓": {"country": "태국", "city": "푸켓", "lat": 7.8804, "lng": 98.3923},
    "파타야": {"country": "태국", "city": "파타야", "lat": 12.9276, "lng": 100.8771},
    "후아힌": {"country": "태국", "city": "후아힌", "lat": 12.5684, "lng": 99.9577},
    "차암": {"country": "태국", "city": "차암·후아힌", "lat": 12.7997, "lng": 99.9669},
    "태국": {"country": "태국", "city": "방콕", "lat": 13.7563, "lng": 100.5018},
    "다낭": {"country": "베트남", "city": "다낭", "lat": 16.0544, "lng": 108.2022},
    "하노이": {"country": "베트남", "city": "하노이", "lat": 21.0285, "lng": 105.8542},
    "호치민": {"country": "베트남", "city": "호치민", "lat": 10.8231, "lng": 106.6297},
    "나트랑": {"country": "베트남", "city": "나트랑", "lat": 12.2388, "lng": 109.1967},
    "푸꾸옥": {"country": "베트남", "city": "푸꾸옥", "lat": 10.2899, "lng": 103.9840},
    "달랏": {"country": "베트남", "city": "달랏", "lat": 11.9404, "lng": 108.4583},
    "하롱베이": {"country": "베트남", "city": "하롱베이", "lat": 20.9101, "lng": 107.1839},
    "하장": {"country": "베트남", "city": "하장", "lat": 22.8233, "lng": 104.9836},
    "푸꾸이": {"country": "베트남", "city": "푸꾸이섬", "lat": 10.5206, "lng": 108.9383},
    "판랑": {"country": "베트남", "city": "판랑탑짬", "lat": 11.5649, "lng": 108.9886},
    "베트남": {"country": "베트남", "city": "다낭", "lat": 16.0544, "lng": 108.2022},
    "방비엥": {"country": "라오스", "city": "방비엥", "lat": 18.9224, "lng": 102.4475},
    "루앙프라방": {"country": "라오스", "city": "루앙프라방", "lat": 19.8893, "lng": 102.1340},
    "비엔티안": {"country": "라오스", "city": "비엔티안", "lat": 17.9757, "lng": 102.6331},
    "라오스": {"country": "라오스", "city": "방비엥", "lat": 18.9224, "lng": 102.4475},
    "발리": {"country": "인도네시아", "city": "발리", "lat": -8.4095, "lng": 115.1889},
    "라부안바조": {"country": "인도네시아", "city": "라부안바조", "lat": -8.4964, "lng": 119.8877},
    "마나도": {"country": "인도네시아", "city": "마나도", "lat": 1.4748, "lng": 124.8421},
    "인도네시아": {"country": "인도네시아", "city": "발리", "lat": -8.4095, "lng": 115.1889},
    "세부": {"country": "필리핀", "city": "세부", "lat": 10.3157, "lng": 123.8854},
    "보라카이": {"country": "필리핀", "city": "보라카이", "lat": 11.9674, "lng": 121.9248},
    "마닐라": {"country": "필리핀", "city": "마닐라", "lat": 14.5995, "lng": 120.9842},
    "시아르가오": {"country": "필리핀", "city": "시아르가오", "lat": 9.8482, "lng": 126.0458},
    "보홀": {"country": "필리핀", "city": "보홀", "lat": 9.8500, "lng": 124.1435},
    "필리핀": {"country": "필리핀", "city": "세부", "lat": 10.3157, "lng": 123.8854},
    "싱가포르": {"country": "싱가포르", "city": "싱가포르", "lat": 1.3521, "lng": 103.8198},
    "쿠알라룸푸르": {"country": "말레이시아", "city": "쿠알라룸푸르", "lat": 3.1390, "lng": 101.6869},
    "코타키나발루": {"country": "말레이시아", "city": "코타키나발루", "lat": 5.9804, "lng": 116.0735},
    "말레이시아": {"country": "말레이시아", "city": "쿠알라룸푸르", "lat": 3.1390, "lng": 101.6869},
    "브루나이": {"country": "브루나이", "city": "반다르스리브가완", "lat": 4.9031, "lng": 114.9398},

    # --- 남아시아 ---
    "바라나시": {"country": "인도", "city": "바라나시", "lat": 25.3176, "lng": 82.9739},
    "뉴델리": {"country": "인도", "city": "뉴델리", "lat": 28.6139, "lng": 77.2090},
    "델리": {"country": "인도", "city": "뉴델리", "lat": 28.6139, "lng": 77.2090},
    "뭄바이": {"country": "인도", "city": "뭄바이", "lat": 19.0760, "lng": 72.8777},
    "자이푸르": {"country": "인도", "city": "자이푸르", "lat": 26.9124, "lng": 75.7873},
    "첸나이": {"country": "인도", "city": "첸나이", "lat": 13.0827, "lng": 80.2707},
    "마두라이": {"country": "인도", "city": "마두라이", "lat": 9.9252, "lng": 78.1198},
    "마이소르": {"country": "인도", "city": "마이소르", "lat": 12.2958, "lng": 76.6394},
    "인도": {"country": "인도", "city": "바라나시", "lat": 25.3176, "lng": 82.9739},
    "방글라데시": {"country": "방글라데시", "city": "다카", "lat": 23.8103, "lng": 90.4125},
    "다카": {"country": "방글라데시", "city": "다카", "lat": 23.8103, "lng": 90.4125},
    "카트만두": {"country": "네팔", "city": "카트만두", "lat": 27.7172, "lng": 85.3240},
    "네팔": {"country": "네팔", "city": "카트만두", "lat": 27.7172, "lng": 85.3240},
    "스리랑카": {"country": "스리랑카", "city": "콜롬보", "lat": 6.9271, "lng": 79.8612},
    "몰디브": {"country": "몰디브", "city": "말레", "lat": 4.1755, "lng": 73.5093},

    # --- 중앙아시아 & 몽골 ---
    "타슈켄트": {"country": "우즈베키스탄", "city": "타슈켄트", "lat": 41.2995, "lng": 69.2401},
    "사마르칸트": {"country": "우즈베키스탄", "city": "사마르칸트", "lat": 39.6548, "lng": 66.9757},
    "부하라": {"country": "우즈베키스탄", "city": "부하라", "lat": 39.7681, "lng": 64.4556},
    "우즈베키스탄": {"country": "우즈베키스탄", "city": "타슈켄트", "lat": 41.2995, "lng": 69.2401},
    "알마티": {"country": "카자흐스탄", "city": "알마티", "lat": 43.2389, "lng": 76.8897},
    "아스타나": {"country": "카자흐스탄", "city": "아스타나", "lat": 51.1694, "lng": 71.4491},
    "카자흐스탄": {"country": "카자흐스탄", "city": "알마티", "lat": 43.2389, "lng": 76.8897},
    "비슈케크": {"country": "키르기스스탄", "city": "비슈케크", "lat": 42.8746, "lng": 74.5698},
    "이식쿨": {"country": "키르기스스탄", "city": "이식쿨", "lat": 42.6500, "lng": 77.0833},
    "키르기스스탄": {"country": "키르기스스탄", "city": "비슈케크", "lat": 42.8746, "lng": 74.5698},
    "울란바토르": {"country": "몽골", "city": "울란바토르", "lat": 47.9212, "lng": 106.9186},
    "테를지": {"country": "몽골", "city": "울란바토르", "lat": 47.8864, "lng": 107.4258},
    "홉스골": {"country": "몽골", "city": "홉스골", "lat": 51.0167, "lng": 100.5167},
    "몽골": {"country": "몽골", "city": "울란바토르", "lat": 47.9212, "lng": 106.9186},

    # --- 코카서스 ---
    "바쿠": {"country": "아제르바이잔", "city": "바쿠", "lat": 40.4093, "lng": 49.8671},
    "아제르바이잔": {"country": "아제르바이잔", "city": "바쿠", "lat": 40.4093, "lng": 49.8671},
    "트빌리시": {"country": "조지아", "city": "트빌리시", "lat": 41.7151, "lng": 44.8271},
    "카즈베기": {"country": "조지아", "city": "카즈베기", "lat": 42.6587, "lng": 44.6417},
    "바투미": {"country": "조지아", "city": "바투미", "lat": 41.6168, "lng": 41.6367},
    "메스티아": {"country": "조지아", "city": "메스티아", "lat": 43.0444, "lng": 42.7278},
    "조지아": {"country": "조지아", "city": "트빌리시", "lat": 41.7151, "lng": 44.8271},
    "예레반": {"country": "아르메니아", "city": "예레반", "lat": 40.1792, "lng": 44.4991},
    "아르메니아": {"country": "아르메니아", "city": "예레반", "lat": 40.1792, "lng": 44.4991},

    # --- 중동 & 아프리카 & 튀르키예 ---
    "이스탄불": {"country": "튀르키예", "city": "이스탄불", "lat": 41.0082, "lng": 28.9784},
    "카파도키아": {"country": "튀르키예", "city": "카파도키아", "lat": 38.6431, "lng": 34.8289},
    "안탈리아": {"country": "튀르키예", "city": "안탈리아", "lat": 36.8969, "lng": 30.7133},
    "알라니아": {"country": "튀르키예", "city": "알라니아", "lat": 36.5444, "lng": 31.9954},
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
    "알울라": {"country": "사우디아라비아", "city": "알울라", "lat": 26.6084, "lng": 37.9232},
    "사우디아라비아": {"country": "사우디아라비아", "city": "리야드", "lat": 24.7136, "lng": 46.6753},
    "요하네스버그": {"country": "남아프리카공화국", "city": "요하네스버그", "lat": -26.2041, "lng": 28.0473},
    "케이프타운": {"country": "남아프리카공화국", "city": "케이프타운", "lat": -33.9249, "lng": 18.4241},
    "남아공": {"country": "남아프리카공화국", "city": "케이프타운", "lat": -33.9249, "lng": 18.4241},
    "에티오피아": {"country": "에티오피아", "city": "아디스아바바", "lat": 9.0320, "lng": 38.7469},
    "르완다": {"country": "르완다", "city": "키갈리", "lat": -1.9441, "lng": 30.0619},
    "우간다": {"country": "우간다", "city": "캄팔라", "lat": 0.3476, "lng": 32.5825},
    "카보베르데": {"country": "카보베르데", "city": "프라이아", "lat": 14.9330, "lng": -23.5133},

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
    "나폴리": {"country": "이탈리아", "city": "나폴리", "lat": 40.8518, "lng": 14.2681},
    "아말피": {"country": "이탈리아", "city": "아말피", "lat": 40.6340, "lng": 14.6027},
    "포지타노": {"country": "이탈리아", "city": "포지타노", "lat": 40.6281, "lng": 14.4850},
    "소렌토": {"country": "이탈리아", "city": "소렌토", "lat": 40.6263, "lng": 14.3758},
    "벨라지오": {"country": "이탈리아", "city": "벨라지오", "lat": 45.9866, "lng": 9.2619},
    "시칠리아": {"country": "이탈리아", "city": "시칠리아", "lat": 37.5990, "lng": 14.0154},
    "팔레르모": {"country": "이탈리아", "city": "팔레르모", "lat": 38.1157, "lng": 13.3615},
    "카타니아": {"country": "이탈리아", "city": "카타니아", "lat": 37.5079, "lng": 15.0873},
    "이탈리아": {"country": "이탈리아", "city": "로마", "lat": 41.9028, "lng": 12.4964},
    "바르셀로나": {"country": "스페인", "city": "바르셀로나", "lat": 41.3851, "lng": 2.1734},
    "마드리드": {"country": "스페인", "city": "마드리드", "lat": 40.4168, "lng": -3.7038},
    "세비야": {"country": "스페인", "city": "세비야", "lat": 37.3891, "lng": -5.9845},
    "산세바스티안": {"country": "스페인", "city": "산세바스티안", "lat": 43.3183, "lng": -1.9812},
    "스페인": {"country": "스페인", "city": "바르셀로나", "lat": 41.3851, "lng": 2.1734},
    "인터라켄": {"country": "스위스", "city": "인터라켄", "lat": 46.6863, "lng": 7.8632},
    "취리히": {"country": "스위스", "city": "취리히", "lat": 47.3769, "lng": 8.5417},
    "제네바": {"country": "스위스", "city": "제네바", "lat": 46.2044, "lng": 6.1432},
    "스위스": {"country": "스위스", "city": "인터라켄", "lat": 46.6863, "lng": 7.8632},
    "파두츠": {"country": "리히텐슈타인", "city": "파두츠", "lat": 47.1410, "lng": 9.5209},
    "리히텐슈타인": {"country": "리히텐슈타인", "city": "파두츠", "lat": 47.1410, "lng": 9.5209},
    "암스테르담": {"country": "네덜란드", "city": "암스테르담", "lat": 52.3676, "lng": 4.9041},
    "헤이그": {"country": "네덜란드", "city": "헤이그", "lat": 52.0705, "lng": 4.3007},
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

    # --- 아메리카 & 오세아니아 ---
    "뉴욕": {"country": "미국", "city": "뉴욕", "lat": 40.7128, "lng": -74.0060},
    "로스앤젤레스": {"country": "미국", "city": "로스앤젤레스", "lat": 34.0522, "lng": -118.2437},
    "LA": {"country": "미국", "city": "로스앤젤레스", "lat": 34.0522, "lng": -118.2437},
    "산타모니카": {"country": "미국", "city": "로스앤젤레스", "lat": 34.0195, "lng": -118.4912},
    "마이애미": {"country": "미국", "city": "마이애미", "lat": 25.7617, "lng": -80.1918},
    "하와이": {"country": "미국", "city": "하와이", "lat": 21.3069, "lng": -157.8583},
    "라스베이거스": {"country": "미국", "city": "라스베이거스", "lat": 36.1699, "lng": -115.1398},
    "샌프란시스코": {"country": "미국", "city": "샌프란시스코", "lat": 37.7749, "lng": -122.4194},
    "캘리포니아": {"country": "미국", "city": "캘리포니아", "lat": 36.7783, "lng": -119.4179},
    "요세미티": {"country": "미국", "city": "요세미티 국립공원", "lat": 37.8651, "lng": -119.5383},
    "미국": {"country": "미국", "city": "뉴욕", "lat": 40.7128, "lng": -74.0060},
    "몬테레이": {"country": "멕시코", "city": "몬테레이", "lat": 25.6866, "lng": -100.3161},
    "과달라하라": {"country": "멕시코", "city": "과달라하라", "lat": 20.6597, "lng": -103.3496},
    "멕시코시티": {"country": "멕시코", "city": "멕시코시티", "lat": 19.4326, "lng": -99.1332},
    "멕시코": {"country": "멕시코", "city": "멕시코시티", "lat": 19.4326, "lng": -99.1332},
    "시드니": {"country": "호주", "city": "시드니", "lat": -33.8688, "lng": 151.2093},
    "멜버른": {"country": "호주", "city": "멜버른", "lat": -37.8136, "lng": 144.9631},
    "호주": {"country": "호주", "city": "시드니", "lat": -33.8688, "lng": 151.2093},
    "부에노스아이레스": {"country": "아르헨티나", "city": "부에노스아이레스", "lat": -34.6037, "lng": -58.3816},
    "우수아이아": {"country": "아르헨티나", "city": "우수아이아", "lat": -54.8019, "lng": -68.3030},
    "파타고니아": {"country": "아르헨티나", "city": "파타고니아", "lat": -50.3379, "lng": -72.2648},
    "아르헨티나": {"country": "아르헨티나", "city": "부에노스아이레스", "lat": -34.6037, "lng": -58.3816},
    "리우데자네이루": {"country": "브라질", "city": "리우데자네이루", "lat": -22.9068, "lng": -43.1729},
    "브라질": {"country": "브라질", "city": "리우데자네이루", "lat": -22.9068, "lng": -43.1729},
    "리마": {"country": "페루", "city": "리마", "lat": -12.0464, "lng": -77.0428},
    "쿠스코": {"country": "페루", "city": "쿠스코", "lat": -13.5319, "lng": -71.9675},
    "와카치나": {"country": "페루", "city": "와카치나", "lat": -14.0875, "lng": -75.7626},
    "페루": {"country": "페루", "city": "리마", "lat": -12.0464, "lng": -77.0428},
    "우유니": {"country": "볼리비아", "city": "우유니", "lat": -20.4604, "lng": -66.8261},
    "볼리비아": {"country": "볼리비아", "city": "우유니", "lat": -20.4604, "lng": -66.8261},
    "칠레": {"country": "칠레", "city": "산티아고", "lat": -33.4489, "lng": -70.6693},
    "카르타헤나": {"country": "콜롬비아", "city": "카르타헤나", "lat": 10.3910, "lng": -75.4794},
    "콜롬비아": {"country": "콜롬비아", "city": "보고타", "lat": 4.7110, "lng": -74.0721}
}

COUNTRY_FLAGS = {
    "🇨🇳": "중국", "🇯🇵": "일본", "🇮🇹": "이탈리아", "🇻🇳": "베트남",
    "🇰🇬": "키르기스스탄", "🇹🇷": "튀르키예", "🇵🇱": "폴란드", "🇮🇪": "아일랜드",
    "🇧🇩": "방글라데시", "🇨🇭": "스위스", "🇹🇭": "태국", "🇳🇱": "네덜란드",
    "🇱🇺": "룩셈부르크", "🇦🇷": "아르헨티나", "🇫🇮": "핀란드", "🇺🇸": "미국",
    "🇬🇧": "영국", "🇫🇷": "프랑스", "🇪🇸": "스페인", "🇲🇳": "몽골",
    "🇪🇬": "이집트", "🇮🇳": "인도", "🇬🇪": "조지아", "🇺🇿": "우즈베키스탄",
    "🇵🇭": "필리핀", "🇲🇾": "말레이시아", "🇸🇬": "싱가포르", "🇩🇪": "독일",
    "🇧🇴": "볼리비아", "🇨🇱": "칠레", "🇨🇴": "콜롬비아", "🇲🇽": "멕시코", "🇵🇪": "페루"
}

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
        safe_handle = urllib.parse.quote(handle)
        url = f"https://www.youtube.com/@{safe_handle}/videos"
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
                    channel_info["subscribers"] = subs
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
    for path in [DATA_RECENT_PATH, DATA_ARCHIVE_PATH]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            ids = set(re.findall(r'youtubeId:\s*["\']([a-zA-Z0-9_-]{11})["\']', content))
            existing_ids.update(ids)
    return existing_ids

def load_existing_video_spots():
    """기존 데이터 파일들에서 이미 등록된 (youtubeId, locationName.lower()) 셋 반환"""
    existing_spots = set()
    for path in [DATA_RECENT_PATH, DATA_ARCHIVE_PATH]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            pattern = r'youtubeId:\s*["\']([a-zA-Z0-9_-]{11})["\'].*?locationName:\s*["\'](.*?)["\']'
            matches = re.findall(pattern, content, re.DOTALL)
            for y_id, loc in matches:
                existing_spots.add((y_id, loc.strip().lower()))
    return existing_spots

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
    - 비여행 영상(기내 좌석/기내식 리뷰, 홈메이드 요리, 단순 일상) 자동 제외
    - 부정어('교토 아님'), 오매칭 단어('비즈니스' -> 니스, '남아공전' -> 남아공) 사전 제거
    - 구체 도시 키워드 우선 매칭 후 광역 국가 키워드 폴백
    """
    # 0. 비여행 영상 필터링 (항공 좌석 리뷰, 홈쿠킹, 자취 일상 등)
    non_travel_patterns = [
        r'기내식\s*최대',
        r'비즈니스석.*탑승',
        r'비즈니스\s*탑승기',
        r'일등석.*탑승',
        r'홈메이드',
        r'출국.*노쇼',
        r'월세체험',
        r'자취생활',
        r'집\s*정리'
    ]
    for pat in non_travel_patterns:
        if re.search(pat, title):
            return None

    def sanitize_location_text(text):
        cleaned = text or ""
        # 오매칭 유발 부분 문자열 및 비유/부정 표현 제거
        cleaned = re.sub(r'비즈니스(?:석|클래스)?', ' ', cleaned)
        cleaned = re.sub(r'[가-힣A-Za-z]+\s*(?:아님|아닌|말고|다음으로|못지않은)', ' ', cleaned)
        cleaned = re.sub(r'[가-힣A-Za-z]+의\s*[가-힣A-Za-z]+', lambda m: m.group(0).split('의')[0], cleaned)
        cleaned = re.sub(r'(?:남아공|체코|일본|중국|브라질|멕시코)전', ' ', cleaned)
        cleaned = re.sub(r'(?:일본|브라질|러시아|미국|한국|대만)\s*(?:여사친|남사친|여자|남자|친구|관광객)', ' ', cleaned)
        cleaned = re.sub(r'(?:일본인|한국인|중국인|미국인|외국인)', ' ', cleaned)
        return cleaned

    clean_title = sanitize_location_text(title)
    clean_full = sanitize_location_text(f"{title} {description}")

    tip_templates = {
        "빠니보틀": lambda city: f"빠니보틀이 방문한 {city} 현지 로컬 추천 코스입니다.",
        "곽튜브": lambda city: f"곽튜브가 강력 추천한 {city} 가성비 맛집 & 명소입니다.",
        "원지의 하루": lambda city: f"원지가 경험한 {city} 소소하고 아늑한 힐링 스팟입니다.",
        "채코제": lambda city: f"채코제가 소개한 {city} 현지 분위기 가득한 로컬 스팟입니다.",
        "여행가 제이": lambda city: f"여행가 제이의 실전 노하우가 담긴 {city} 여행지입니다.",
        "잰잰바리": lambda city: f"잰잰바리가 만난 {city}의 따뜻하고 정겨운 여행지입니다.",
        "노마드션": lambda city: f"노마드션의 로드트립 추천 {city} 여행 코스입니다.",
        "캡틴따거": lambda city: f"캡틴따거가 전하는 {city}의 역사와 숨은 이야기 명소입니다.",
        "캐럿맨 여행기": lambda city: f"캐럿맨의 생생한 모험이 담긴 {city} 추천 스팟입니다.",
        "희철리즘": lambda city: f"희철리즘이 인터뷰한 {city} 현지인들의 진짜 삶의 현장입니다.",
        "또떠남": lambda city: f"또떠남의 프리미엄 호텔 & 최적 동선 가이드 추천 스팟입니다.",
        "쏘이 The World": lambda city: f"쏘이가 경험한 {city} 안전하고 매력적인 추천 여행지입니다.",
        "초마드": lambda city: f"초마드가 소개한 {city} 럭셔리 호캉스 & 핫플레이스입니다.",
        "시칠리안": lambda city: f"시칠리안 부부가 추천하는 {city} 실속 가성비 & 힐링 스팟입니다.",
        "걸어서 세계속으로": lambda city: f"KBS 걸어서 세계속으로가 소개한 {city} 역사·문화 핵심 명소입니다."
    }

    def match_keyword(kw, target_text):
        # 영문 약어(예: LA)는 단어 경계 확인
        if re.match(r'^[A-Za-z]+$', kw):
            return bool(re.search(rf'(?<![A-Za-z]){re.escape(kw)}(?![A-Za-z])', target_text))
        return kw in target_text

    def build_result(kw, spot_data):
        country = spot_data["country"]
        city = spot_data["city"]
        location_name = f"{city} {kw}" if kw != city and kw != country else f"{city} 주요 명소"
        tip_fn = tip_templates.get(creator_name)
        tip = tip_fn(city) if tip_fn else f"{creator_name}의 {city} 여행 영상 추천 스팟입니다."
        return {
            "country": country,
            "city": city,
            "locationName": location_name,
            "lat": spot_data["lat"],
            "lng": spot_data["lng"],
            "tags": [city, country, "유튜브추천", "여행"],
            "tip": tip
        }

    # 1. 구체 도시/명소 키워드 우선 매칭 (국가 대표 폴백 키워드보다 먼저 검사)
    city_keywords = sorted(
        [k for k, v in DESTINATION_DICTIONARY.items() if k != v["country"]],
        key=lambda k: len(k),
        reverse=True
    )
    country_keywords = sorted(
        [k for k, v in DESTINATION_DICTIONARY.items() if k == v["country"]],
        key=lambda k: len(k),
        reverse=True
    )

    # 1-A. 제목에서 구체 도시 우선 탐색 -> 본문 전체에서 구체 도시 탐색
    for target in (clean_title, clean_full):
        for kw in city_keywords:
            if match_keyword(kw, target):
                return build_result(kw, DESTINATION_DICTIONARY[kw])

    # 1-B. 제목/본문에서 국가명 키워드 탐색
    for target in (clean_title, clean_full):
        for kw in country_keywords:
            if match_keyword(kw, target):
                return build_result(kw, DESTINATION_DICTIONARY[kw])

    # 2. 제목 내 국가 국기 이모지 파싱
    for flag, country in COUNTRY_FLAGS.items():
        if flag in title:
            for kw, spot_data in DESTINATION_DICTIONARY.items():
                if spot_data["country"] == country:
                    return build_result(kw, spot_data)

    # 3. 대괄호/말머리 패턴 ([...], 【...】)에서 사전 등록 지명 매칭
    bracket_match = re.search(r'\[(.*?)\]|【(.*?)】', title)
    if bracket_match:
        raw_candidate = next(c for c in bracket_match.groups() if c)
        clean_candidate = re.sub(r'[\d_#\s下上편탄]+$', '', raw_candidate).strip()
        if clean_candidate in DESTINATION_DICTIONARY:
            return build_result(clean_candidate, DESTINATION_DICTIONARY[clean_candidate])

    # 4. 사전 매칭 실패 시: Gemini LLM Fallback (AI 기반 위치 및 위경도 추출)
    gemini_result = extract_with_gemini_api(title, description, creator_name)
    if gemini_result:
        return gemini_result

    return None

_VIDEO_DESC_CACHE = {}

def fetch_video_description(youtube_id):
    """유튜브 영상 상세 페이지에서 전체 설명란(더보기 내용)을 가져옴"""
    if youtube_id in _VIDEO_DESC_CACHE:
        return _VIDEO_DESC_CACHE[youtube_id]

    url = f"https://www.youtube.com/watch?v={youtube_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8, context=SAFE_SSL_CONTEXT) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            m = re.search(r'\"description\":\{\"simpleText\":\"(.*?)\"\}', html)
            if m:
                try:
                    desc = json.loads(f'"{m.group(1)}"')
                    _VIDEO_DESC_CACHE[youtube_id] = desc
                    return desc
                except Exception:
                    pass
    except Exception:
        pass
    _VIDEO_DESC_CACHE[youtube_id] = ""
    return ""

def parse_timestamp_seconds(ts_str):
    """03:25 또는 01:15:30 형식의 타임스탬프를 초 단위 정수로 변환"""
    parts = ts_str.strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        pass
    return 0

def extract_granular_locations(youtube_id, title, description, creator_name):
    """
    영상 설명란의 핀 마커(📍) 및 타임라인(03:20) 챕터를 분석하여,
    한 영상 내에 존재하는 여러 세부 스팟 목록(List[dict])을 자동 추출.
    세부 스팟이 없으면 1개 대표 스팟 반환.
    """
    full_desc = description
    if not full_desc or len(full_desc.strip()) <= len(title.strip()):
        fetched = fetch_video_description(youtube_id)
        if fetched:
            full_desc = fetched

    base_spot = analyze_video_location(title, full_desc, creator_name)
    base_city = base_spot["city"] if base_spot else ""
    base_country = base_spot["country"] if base_spot else ""
    base_lat = base_spot["lat"] if base_spot else None
    base_lng = base_spot["lng"] if base_spot else None

    granular_spots = []

    # 1. 📍 / 📌 핀 마커 섹션 파싱 (예: 잡식맨, 육식맨 등)
    if full_desc and re.search(r'[📍📌]', full_desc):
        sections = re.split(r'[📍📌]\s*', full_desc)[1:]
        for idx, sec in enumerate(sections, 1):
            lines = [l.strip() for l in sec.splitlines() if l.strip()]
            if not lines:
                continue
            raw_name = lines[0]
            spot_name = re.sub(r'\(.*?\)|\[.*?\]', '', raw_name).strip() or raw_name
            if len(spot_name) < 2 or len(spot_name) > 35 or any(b in spot_name for b in ["http", "구독", "인스타", "채널"]):
                continue

            tip = ""
            address = ""
            for l in lines[1:5]:
                if l.startswith("주소:") or l.startswith("위치:"):
                    address = re.sub(r'^(?:주소|위치):\s*', '', l).strip()
                elif not tip and not l.startswith("링크") and not l.startswith("http") and not l.startswith("구글"):
                    tip = l

            query = address if address else f"{spot_name}, {base_city}"
            lat, lng = geocode_location(query)
            if not lat and base_city:
                lat, lng = geocode_location(f"{spot_name} {base_city}")
            if not lat and base_lat and base_lng:
                offset_lat = ((idx % 3) - 1) * 0.003
                offset_lng = ((idx // 3) - 1) * 0.003
                lat = round(base_lat + offset_lat, 4)
                lng = round(base_lng + offset_lng, 4)

            if lat and lng:
                granular_spots.append({
                    "id": f"auto-{youtube_id}-{idx}",
                    "creator": creator_name,
                    "youtubeId": youtube_id,
                    "title": title,
                    "country": base_country or "기타",
                    "city": base_city or "기타",
                    "locationName": spot_name,
                    "lat": lat,
                    "lng": lng,
                    "startTime": 0,
                    "tags": [base_city, base_country, "로컬추천", "유튜브추천"] if base_city else ["유튜브추천"],
                    "tip": tip or f"{creator_name}의 {spot_name} 추천 스팟입니다."
                })

    # 2. 타임라인 / 챕터 파싱 (03:20 [장소])
    if not granular_spots and full_desc:
        ts_matches = re.findall(r'(?:^|\n)\s*(?:\[|\()?(\d{1,2}:\d{2}(?::\d{2})?)(?:\]|\))?\s+([^\n\r]+)', full_desc)
        ignore_kw = ["오프닝", "출발", "귀국", "비행기", "공항", "인트로", "에필로그", "엔딩", "아웃트로", "마무리", "도착", "환전", "준비", "쿠키"]
        for idx, (ts_str, label) in enumerate(ts_matches, 1):
            clean_lbl = re.sub(r'\[.*?\]|\(.*?\)', '', label).strip()
            if any(ig in clean_lbl for ig in ignore_kw) or len(clean_lbl) < 2 or len(clean_lbl) > 35:
                continue

            sec = parse_timestamp_seconds(ts_str)
            query = f"{clean_lbl}, {base_city}" if base_city else clean_lbl
            lat, lng = geocode_location(query)
            if not lat and base_city:
                lat, lng = geocode_location(f"{clean_lbl} {base_city}")
            if not lat and base_lat and base_lng:
                offset_lat = ((idx % 3) - 1) * 0.003
                offset_lng = ((idx // 3) - 1) * 0.003
                lat = round(base_lat + offset_lat, 4)
                lng = round(base_lng + offset_lng, 4)

            if lat and lng:
                granular_spots.append({
                    "id": f"auto-{youtube_id}-{idx}",
                    "creator": creator_name,
                    "youtubeId": youtube_id,
                    "title": title,
                    "country": base_country or "기타",
                    "city": base_city or "기타",
                    "locationName": clean_lbl,
                    "lat": lat,
                    "lng": lng,
                    "startTime": sec,
                    "tags": [base_city, base_country, "타임라인", "유튜브추천"] if base_city else ["타임라인"],
                    "tip": f"[{ts_str}] 영상 {clean_lbl} 방문 구간입니다."
                })

    # 세부 스팟이 2개 이상 추출된 경우 다중 핀 반환
    if len(granular_spots) >= 2:
        return granular_spots

    # 세부 스팟 추출 실패 시 기본 1개 대표 스팟 반환
    if base_spot:
        return [{
            "id": f"auto-{youtube_id}",
            "creator": creator_name,
            "youtubeId": youtube_id,
            "title": title,
            "country": base_spot["country"],
            "city": base_spot["city"],
            "locationName": base_spot["locationName"],
            "lat": base_spot["lat"],
            "lng": base_spot["lng"],
            "startTime": 0,
            "tags": base_spot["tags"],
            "tip": base_spot["tip"]
        }]

    return []

def append_to_data_js(new_entries):
    """새로 발견된 여행 영상 목록을 videos_recent.js 파일 상단에 깔끔하게 추가"""
    target_path = DATA_RECENT_PATH
    if not new_entries or not os.path.exists(target_path):
        return

    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()

    # RECENT_VIDEOS 배열 위치 찾기
    insert_pos = content.find("const RECENT_VIDEOS = [")
    if insert_pos == -1:
        print(f"❌ {target_path} 파일에서 RECENT_VIDEOS 배열을 찾을 수 없습니다.")
        return

    bracket_pos = content.find("[", insert_pos) + 1
    
    formatted_entries = []
    for item in new_entries:
        escaped_title = item['title'].replace('"', '\\"')
        escaped_loc = item['locationName'].replace('"', '\\"')
        escaped_tip = item['tip'].replace('"', '\\"')
        tags_json = json.dumps(item['tags'], ensure_ascii=False)
        pub_date = item.get('publishedAt', datetime.now().strftime("%Y-%m-%d"))
        start_time_line = f"\n    startTime: {int(item['startTime'])}," if item.get('startTime') else ""
        spot_id = item.get('id') or f"auto-{item['youtubeId']}"

        entry_str = f"""
  // [신규 자동 수집] {item['creator']} - {escaped_loc} ({pub_date})
  {{
    id: "{spot_id}",
    creator: "{item['creator']}",
    youtubeId: "{item['youtubeId']}",
    title: "{escaped_title}",
    channel: "{item['creator']}",
    country: "{item['country']}",
    city: "{item['city']}",
    locationName: "{escaped_loc}",
    lat: {item['lat']},
    lng: {item['lng']},{start_time_line}
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
# 4. 유튜버 실시간 검색 및 추가 워크플로우
# =============================================================================
def search_youtube_channel(query):
    """
    유튜브에서 유튜버 이름/핸들/URL을 검색하여 채널 정보 추출
    반환: {"name": str, "handle": str, "channel_id": str} 또는 None
    """
    query = query.strip()
    # 1. URL 형태인 경우
    if "youtube.com/" in query:
        m = re.search(r'youtube\.com/@([^/?&#\s]+)', query)
        if m:
            h = urllib.parse.unquote(m.group(1))
            return {"name": h, "handle": h, "channel_id": ""}
            
    # 2. @핸들 형태인 경우
    if query.startswith("@"):
        h = query[1:]
        return {"name": h, "handle": h, "channel_id": ""}

    # 3. 유튜버 이름으로 채널 검색
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}&sp=EgIQAg%3D%3D"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12, context=SAFE_SSL_CONTEXT) as r:
            html = r.read().decode("utf-8", errors="ignore")

        idx = html.find("var ytInitialData = ")
        if idx == -1:
            return None
        end = html.find(";</script>", idx)
        data = json.loads(html[idx + len("var ytInitialData = "):end])
        contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
        for sec in contents:
            for it in sec.get("itemSectionRenderer", {}).get("contents", []):
                cr = it.get("channelRenderer")
                if cr:
                    name = cr.get("title", {}).get("simpleText") or query
                    channel_id = cr.get("channelId", "")
                    nav = cr.get("navigationEndpoint", {}).get("commandMetadata", {}).get("webCommandMetadata", {}).get("url", "")
                    raw_handle = nav.replace("/@", "").replace("/", "")
                    handle = urllib.parse.unquote(raw_handle)
                    return {"name": name, "handle": handle, "channel_id": channel_id}
    except Exception as e:
        print(f"⚠️ 채널 검색 중 오류 발생: {e}")

    return None

def add_channel_workflow(query, is_auto=False):
    """
    유튜버 이름을 입력받아:
    1. 채널 자동 검색
    2. 구독자 5만+ 실시간 검증
    3. channels.json에 신규 등록
    4. 최근 1년 여행 영상 즉시 수집 & 위치 추출 후 데이터 파일에 추가
    """
    print("=" * 70)
    print(f"🔍 유튜버 추가 탐색: '{query}'")
    print("=" * 70)

    found = search_youtube_channel(query)
    if not found:
        print(f"❌ 유튜브에서 '{query}' 관련 채널을 찾을 수 없습니다.")
        return False

    print(f"   [+] 탐색된 채널: {found['name']} (@{found['handle']})")
    
    channels = load_channels()
    existing_match = None
    for ch in channels:
        if ch.get("handle", "").lower() == found["handle"].lower() or (found.get("channel_id") and ch.get("channel_id") == found.get("channel_id")):
            existing_match = ch
            break

    if existing_match:
        print(f"   💡 이미 등록된 채널입니다: {existing_match['name']} (@{existing_match['handle']})")
        target_channel = existing_match
    else:
        target_channel = found

    print(f"\n📡 채널 페이지 접속 및 구독자 수 실시간 검증 중...")
    videos = fetch_channel_videos(target_channel)

    if not videos:
        print(f"❌ 영상을 가져오지 못했거나 구독자 수 기준(5만+) 미달로 수집이 중단되었습니다.")
        return False

    # 신규 채널인 경우 channels.json에 영구 등록
    if not existing_match:
        channels.append({"name": target_channel["name"], "handle": target_channel["handle"]})
        save_channels(channels)
        print(f"🎉 '{target_channel['name']}' (@{target_channel['handle']}) 채널이 channels.json에 신규 등록되었습니다! (총 {len(channels)}개 채널)")

    # 기존 등록 영상 중복 체크
    existing_ids = load_existing_video_ids()
    unregistered = [v for v in videos if v["youtube_id"] not in existing_ids and v.get("days_ago", 0) <= MAX_VIDEO_AGE_DAYS]

    if not unregistered:
        print(f"💡 최근 {MAX_VIDEO_AGE_DAYS}일(1년) 이내에 등록할 새로운 신규 영상이 없습니다.")
        return True

    print(f"\n✨ 미등록 최신 영상 {len(unregistered)}편에서 여행지 분석 중...")
    new_spots = []
    existing_spots = load_existing_video_spots()
    for v in unregistered:
        extracted = extract_granular_locations(v["youtube_id"], v["title"], v.get("description", ""), target_channel["name"])
        for s in extracted:
            key = (v["youtube_id"], s["locationName"].strip().lower())
            if key not in existing_spots:
                s["publishedAt"] = v.get("published", "")
                new_spots.append(s)
                existing_spots.add(key)
                start_label = f" (⏱️ {s['startTime']//60}:{s['startTime']%60:02d})" if s.get("startTime") else ""
                print(f"      [+] 📍 [{s['country']} {s['city']}] {s['locationName']}{start_label} ({v.get('published')}): {v['title'][:38]}...")

    if not new_spots:
        print("[-] 영상들에서 구체적인 여행지 키워드가 감지되지 않았습니다.")
        return True

    print(f"\n📊 총 {len(new_spots)}개의 여행지가 추출되었습니다.")
    if not is_auto:
        try:
            ans = input("\n👉 지도 데이터(videos_recent.js)에 바로 반영할까요? (Y/n): ").strip().lower()
            if ans not in ["y", "yes", ""]:
                print("데이터 반영이 취소되었습니다. (channels.json에는 채널이 보존됩니다)")
                return True
        except EOFError:
            pass

    append_to_data_js(new_spots)
    return True

# =============================================================================
# 5. 10만+ 유튜버 여행 브이로그 자동 발굴 (Discover)
# =============================================================================
def search_youtube_videos(query, max_results=20):
    """
    유튜브에서 검색어로 최신 영상 목록 검색
    반환: [{"youtube_id": str, "title": str, "channel_name": str, "handle": str, "description": str}]
    """
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=12, context=SAFE_SSL_CONTEXT) as r:
            html = r.read().decode("utf-8", errors="ignore")

        idx = html.find("var ytInitialData = ")
        if idx == -1:
            return []
        end = html.find(";</script>", idx)
        data = json.loads(html[idx + len("var ytInitialData = "):end])
        contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
        
        videos = []
        for sec in contents:
            for it in sec.get("itemSectionRenderer", {}).get("contents", []):
                vr = it.get("videoRenderer")
                if vr:
                    vid = vr.get("videoId")
                    title = vr.get("title", {}).get("runs", [{}])[0].get("text", "")
                    owner_runs = vr.get("ownerText", {}).get("runs", [{}])
                    owner_name = owner_runs[0].get("text", "") if owner_runs else ""
                    nav = owner_runs[0].get("navigationEndpoint", {}).get("commandMetadata", {}).get("webCommandMetadata", {}).get("url", "") if owner_runs else ""
                    raw_handle = nav.replace("/@", "").replace("/", "")
                    handle = urllib.parse.unquote(raw_handle)
                    
                    snippet = ""
                    for run in vr.get("detailedMetadataSnippets", [{}])[0].get("snippetText", {}).get("runs", []):
                        snippet += run.get("text", "")

                    if vid and title and handle:
                        videos.append({
                            "youtube_id": vid,
                            "title": title,
                            "channel_name": owner_name or handle,
                            "handle": handle,
                            "description": snippet or title
                        })
                    if len(videos) >= max_results:
                        break
            if len(videos) >= max_results:
                break
        return videos
    except Exception as e:
        print(f"⚠️ 영상 검색 중 오류 발생: {e}")
        return []

def discover_travel_vlogs(query="해외여행 브이로그", is_auto=False, max_videos=20):
    """
    키워드로 여행 브이로그를 검색하고:
    1. 유튜버의 구독자가 10만 이상인지 실시간 검증
    2. 10만 이상이면 여행지 위치/좌표 추출
    3. channels.json에 신규 유튜버 자동 등록 및 지도 데이터(videos_recent.js)에 핀 추가
    """
    print("=" * 70)
    print(f"🌍 10만+ 유튜버 여행 브이로그 자동 발굴 모드")
    print(f"🔍 검색 키워드: '{query}'")
    print(f"🎯 자격 조건: 채널 구독자 {DISCOVER_MIN_SUBSCRIBER_COUNT:,}명(10만+) 이상")
    print("=" * 70)

    videos = search_youtube_videos(query, max_results=max_videos)
    if not videos:
        print(f"❌ '{query}' 관련 영상을 찾지 못했습니다.")
        return False

    print(f"📡 총 {len(videos)}편의 후보 브이로그 영상 탐색 완료. 검증 시작...\n")

    existing_ids = load_existing_video_ids()
    existing_spots = load_existing_video_spots()
    channels = load_channels()
    known_handles = {ch.get("handle", "").lower(): ch for ch in channels}
    
    channel_subs_cache = {}  # handle -> subs count
    new_spots = []
    new_channels_added = 0

    for idx, v in enumerate(videos, 1):
        vid = v["youtube_id"]
        title = v["title"]
        handle = v["handle"]
        cname = v["channel_name"]

        # 이미 등록된 영상인지 체크
        if vid in existing_ids:
            continue

        print(f"[{idx:2d}/{len(videos)}] {cname} (@{handle})")
        print(f"     영상: {title[:45]}...")

        # 채널 구독자 수 확인 (10만 이상인지)
        if handle in channel_subs_cache:
            subs = channel_subs_cache[handle]
        else:
            time.sleep(0.3)
            safe_handle = urllib.parse.quote(handle)
            ch_url = f"https://www.youtube.com/@{safe_handle}/videos"
            headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
            req = urllib.request.Request(ch_url, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=10, context=SAFE_SSL_CONTEXT) as r:
                    html = r.read().decode("utf-8", errors="ignore")
                subs = parse_subscriber_count(html)
            except Exception:
                subs = None
            channel_subs_cache[handle] = subs

        if subs is None or subs < DISCOVER_MIN_SUBSCRIBER_COUNT:
            subs_str = f"{subs:,}명" if subs else "미확인"
            print(f"     [-] ❌ 구독자 10만 미달 ({subs_str} < {DISCOVER_MIN_SUBSCRIBER_COUNT:,}명) -> 제외")
            continue

        print(f"     [i] 👥 구독자 수: {subs:,}명 (✅ 10만+ 기준 통과!)")

        # 여행지 위치 및 좌표 분석 (다중 세부 스팟/타임스탬프 추출 -> Gemini AI 폴백)
        extracted = extract_granular_locations(vid, title, v.get("description", ""), cname)
        if extracted:
            added_for_vid = 0
            for s in extracted:
                key = (vid, s["locationName"].strip().lower())
                if key not in existing_spots:
                    s["publishedAt"] = datetime.now().strftime("%Y-%m-%d")
                    new_spots.append(s)
                    existing_spots.add(key)
                    added_for_vid += 1
                    start_label = f" (⏱️ {s['startTime']//60}:{s['startTime']%60:02d})" if s.get("startTime") else ""
                    print(f"     [+] 📍 여행지 식별 성공: {s['country']} {s['city']} ({s['locationName']}){start_label}")

            if added_for_vid > 0:
                existing_ids.add(vid)
                # 신규 유튜버라면 channels.json에도 등록
                if handle.lower() not in known_handles:
                    channels.append({"name": cname, "handle": handle})
                    known_handles[handle.lower()] = True
                    new_channels_added += 1
                    print(f"     🎉 '{cname}' 채널이 channels.json에 신규 유튜버로 등록되었습니다!")
        else:
            print(f"     [-] 명확한 여행지 정보 미감지 (일상/토크 등)")

    print("\n" + "=" * 70)
    print(f"📊 탐색 결과: 총 {len(new_spots)}개의 새로운 10만+ 유튜버 여행 핀 추출 완료")
    if new_channels_added > 0:
        print(f"👥 신규 발굴된 10만+ 유튜버: {new_channels_added}팀")
    print("=" * 70)

    if not new_spots:
        print("💡 조건(10만+ 구독자 & 명확한 여행지)에 부합하는 새로운 영상이 없습니다.")
        return True

    if not is_auto:
        try:
            ans = input("\n👉 지도 데이터(videos_recent.js)에 바로 반영할까요? (Y/n): ").strip().lower()
            if ans not in ["y", "yes", ""]:
                print("데이터 반영이 취소되었습니다.")
                return True
        except EOFError:
            pass

    append_to_data_js(new_spots)
    save_channels(channels)
    return True

# =============================================================================
# 6. 메인 실행 흐름
# =============================================================================
def main():
    import argparse
    parser = argparse.ArgumentParser(description="TubeMap Travel - 한국 대표 여행 유튜버 영상 자동 수집기")
    parser.add_argument("--add", type=str, help="유튜버 이름 또는 @핸들을 입력하여 채널 등록 및 영상 수집")
    parser.add_argument("--discover", type=str, nargs="?", const="해외여행 브이로그", help="10만 이상 유튜버의 여행 브이로그 영상 자동 발굴 (기본값: '해외여행 브이로그')")
    parser.add_argument("--list", action="store_true", help="현재 등록된 모니터링 채널 목록 조회")
    parser.add_argument("--auto", action="store_true", help="프롬프트 없이 자동으로 데이터 파일에 반영")
    args = parser.parse_args()

    channels = load_channels()

    if args.list:
        print("=" * 70)
        print(f"📋 TubeMap 등록 모니터링 채널 목록 (총 {len(channels)}개)")
        print("=" * 70)
        for i, ch in enumerate(channels, 1):
            print(f"  {i:2d}. {ch['name']} (@{ch.get('handle', '-')})")
        return

    if args.add:
        add_channel_workflow(args.add, is_auto=args.auto)
        return

    if args.discover:
        discover_travel_vlogs(args.discover, is_auto=args.auto)
        return

    print("=" * 70)
    print(f"📍 TubeMap Travel - 한국 대표 여행 유튜버 ({len(channels)}팀) 최신 영상 자동 수집기")
    print(f"⏰ 실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 필터 기준: 최근 {MAX_VIDEO_AGE_DAYS}일(1년) 이내 최신 영상만 수집")
    print("=" * 70)

    existing_ids = load_existing_video_ids()
    existing_spots = load_existing_video_spots()
    print(f"📦 현재 등록된 여행 영상 수: {len(existing_ids)}편 (등록된 여행 스팟: {len(existing_spots)}곳)\n")

    new_discovered_spots = []

    for idx, ch in enumerate(channels, 1):
        name = ch["name"]
        handle = ch["handle"]

        print(f"📡 [{idx:2d}/{len(channels)}] {name} (@{handle}) 최신 영상 수집 중...")
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

            extracted = extract_granular_locations(v["youtube_id"], v["title"], v.get("description", ""), name)
            if extracted:
                for s in extracted:
                    key = (v["youtube_id"], s["locationName"].strip().lower())
                    if key not in existing_spots:
                        s["publishedAt"] = pub_date
                        new_discovered_spots.append(s)
                        existing_spots.add(key)
                        creator_matched_count += 1
                        start_label = f" (⏱️ {s['startTime']//60}:{s['startTime']%60:02d})" if s.get("startTime") else ""
                        print(f"      [+] 📍 {s['country']} {s['city']} ({s['locationName']}){start_label} ({pub_date}): {v['title'][:38]}...")
                existing_ids.add(v["youtube_id"])

        if creator_matched_count == 0:
            print(f"      [-] 최근 영상 중 명확한 여행지 키워드 미감지 (토크/일상 콘텐츠 등)")

    print("\n" + "=" * 70)
    print(f"📊 수집 결과: 총 {len(new_discovered_spots)}개의 새로운 여행지 추출 완료")
    print("=" * 70)

    if not new_discovered_spots:
        print("💡 새로 추가할 여행 영상이 없습니다. 지도가 이미 최신 상태입니다.")
        return

    if not args.auto:
        print("\n아래 항목들을 지도 데이터(videos_recent.js)에 추가하시겠습니까?")
        for idx, s in enumerate(new_discovered_spots[:10], 1):
            print(f"  {idx:2d}. [{s['creator']}] {s['country']} {s['city']} - {s['title'][:40]}...")
        if len(new_discovered_spots) > 10:
            print(f"  ... 외 {len(new_discovered_spots) - 10}개 추가")
        
        try:
            answer = input("\n👉 지도 데이터에 반영할까요? (Y/n): ").strip().lower()
            if answer not in ["y", "yes", ""]:
                print("작업이 취소되었습니다.")
                return
        except EOFError:
            print("비대화형 환경이 감지되어 자동 반영합니다.")

    append_to_data_js(new_discovered_spots)

if __name__ == "__main__":
    main()
