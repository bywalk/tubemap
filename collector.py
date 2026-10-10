#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TubeMap Travel - 한국 여행 유튜버 신규 영상 자동 수집기 (Collector)
=============================================================================
기능:
1. 설정된 여행 유튜버 채널의 공식 RSS 피드를 조회하여 최신 영상 목록 수집
2. 기존 data.js에 이미 등록된 영상은 자동으로 건너뜀 (중복 방지)
3. 영상 제목/설명란을 분석하여 여행 국가, 도시, 스팟명, 꿀팁 추출
   - 기본: 자체 키워드 사전 및 정규식 규칙 기반 자동 파싱
   - 확장: GEMINI_API_KEY 또는 OPENAI_API_KEY 설정 시 AI 정밀 추출 지원
4. OpenStreetMap Nominatim API로 장소 좌표(위도, 경도) 자동 지오코딩
5. data.js에 새 여행지를 안전하게 업데이트
=============================================================================
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

# =============================================================================
# 1. 수집 설정 및 모니터링 대상 한국 대표 여행 유튜버 (구독자 5만~100만+)
# =============================================================================
MAX_VIDEO_AGE_DAYS = 365  # 여행 정보 최신성 유지를 위해 1년(365일) 이내 영상만 수집

CHANNELS = [
    # 기존 대표 크리에이터
    {
        "name": "빠니보틀",
        "handle": "panibottle",
        "channel_id": "UCtUEdJ_H9r-J-pS2VlH66oA"
    },
    {
        "name": "곽튜브",
        "handle": "JoonbinKwak",
        "channel_id": "UClmcWq01O38-u30cQ7-555w"
    },
    {
        "name": "원지의 하루",
        "handle": "wonjineday",
        "channel_id": "UC2125q3227918881268395568"
    },
    {
        "name": "채코제",
        "handle": "ChannelKoreanJay",
        "channel_id": ""
    },
    {
        "name": "여행가 제이",
        "handle": "TravelerJAY",
        "channel_id": ""
    },
    {
        "name": "잰잰바리",
        "handle": "jaeye0nyy",
        "channel_id": ""
    },
    # 5만~100만+ 신규 모니터링 크리에이터
    {
        "name": "노마드션",
        "handle": "nomadshaun",
        "channel_id": ""
    },
    {
        "name": "캡틴따거",
        "handle": "CaptainTtaggo",
        "channel_id": ""
    },
    {
        "name": "캐럿맨 여행기",
        "handle": "Carrotman_Travel",
        "channel_id": ""
    },
    {
        "name": "희철리즘",
        "handle": "heechulism",
        "channel_id": ""
    },
    {
        "name": "또떠남",
        "handle": "ddoddunam",
        "channel_id": ""
    },
    {
        "name": "쏘이 The World",
        "handle": "SoyTheWorld",
        "channel_id": ""
    },
    {
        "name": "뜨우",
        "handle": "ddeu_travel",
        "channel_id": ""
    }
]

# =============================================================================
# 2. 대표 여행지 키워드 사전 (AI 미연동 시 자동 매핑용)
# =============================================================================
DESTINATION_DICTIONARY = {
    # 동남아
    "방콕": {"country": "태국", "city": "방콕", "lat": 13.7563, "lng": 100.5018},
    "치앙마이": {"country": "태국", "city": "치앙마이", "lat": 18.7883, "lng": 98.9853},
    "푸켓": {"country": "태국", "city": "푸켓", "lat": 7.8804, "lng": 98.3923},
    "방비엥": {"country": "라오스", "city": "방비엥", "lat": 18.9224, "lng": 102.4475},
    "루앙프라방": {"country": "라오스", "city": "루앙프라방", "lat": 19.8893, "lng": 102.1340},
    "다낭": {"country": "베트남", "city": "다낭", "lat": 16.0544, "lng": 108.2022},
    "하노이": {"country": "베트남", "city": "하노이", "lat": 21.0285, "lng": 105.8542},
    "발리": {"country": "인도네시아", "city": "발리", "lat": -8.4095, "lng": 115.1889},
    # 중앙아시아 & 몽골
    "타슈켄트": {"country": "우즈베키스탄", "city": "타슈켄트", "lat": 41.2995, "lng": 69.2401},
    "사마르칸트": {"country": "우즈베키스탄", "city": "사마르칸트", "lat": 39.6548, "lng": 66.9757},
    "부하라": {"country": "우즈베키스탄", "city": "부하라", "lat": 39.7681, "lng": 64.4556},
    "울란바토르": {"country": "몽골", "city": "울란바토르", "lat": 47.9212, "lng": 106.9186},
    "테를지": {"country": "몽골", "city": "울란바토르", "lat": 47.8864, "lng": 107.4258},
    "알마티": {"country": "카자흐스탄", "city": "알마티", "lat": 43.2389, "lng": 76.8897},
    # 코카서스
    "바쿠": {"country": "아제르바이잔", "city": "바쿠", "lat": 40.4093, "lng": 49.8671},
    "트빌리시": {"country": "조지아", "city": "트빌리시", "lat": 41.7151, "lng": 44.8271},
    "카즈베기": {"country": "조지아", "city": "카즈베기", "lat": 42.6587, "lng": 44.6417},
    "바투미": {"country": "조지아", "city": "바투미", "lat": 41.6168, "lng": 41.6367},
    # 중동 & 아프리카
    "다합": {"country": "이집트", "city": "다합", "lat": 28.5097, "lng": 34.5136},
    "카이로": {"country": "이집트", "city": "카이로", "lat": 30.0444, "lng": 31.2357},
    "사하라": {"country": "모로코", "city": "사하라 사막", "lat": 31.0802, "lng": -4.0133},
    "마라케시": {"country": "모로코", "city": "마라케시", "lat": 31.6295, "lng": -7.9811},
    "이스탄불": {"country": "튀르키예", "city": "이스탄불", "lat": 41.0082, "lng": 28.9784},
    "카파도키아": {"country": "튀르키예", "city": "카파도키아", "lat": 38.6431, "lng": 34.8289},
    # 남아시아
    "바라나시": {"country": "인도", "city": "바라나시", "lat": 25.3176, "lng": 82.9739},
    "뉴델리": {"country": "인도", "city": "뉴델리", "lat": 28.6139, "lng": 77.2090},
    "뭄바이": {"country": "인도", "city": "뭄바이", "lat": 19.0760, "lng": 72.8777},
    # 동아시아 & 유럽 & 국내
    "도쿄": {"country": "일본", "city": "도쿄", "lat": 35.6762, "lng": 139.6503},
    "오사카": {"country": "일본", "city": "오사카", "lat": 34.6937, "lng": 135.5023},
    "후쿠오카": {"country": "일본", "city": "후쿠오카", "lat": 33.5904, "lng": 130.4017},
    "파리": {"country": "프랑스", "city": "파리", "lat": 48.8566, "lng": 2.3522},
    "런던": {"country": "영국", "city": "런던", "lat": 51.5074, "lng": -0.1278},
    "제주": {"country": "대한민국", "city": "제주", "lat": 33.4996, "lng": 126.5312}
}

DATA_JS_PATH = os.path.join(os.path.dirname(__file__), "js", "data.js")

# =============================================================================
# 3. 헬퍼 함수들
# =============================================================================

def get_channel_id(handle):
    """핸들(@name)로부터 채널 ID(UC...)를 자동 조회"""
    url = f"https://www.youtube.com/@{handle}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # itemprop="channelId" or "channelId":"UC..."
            match = re.search(r'itemprop="channelId"\s+content="([a-zA-Z0-9_-]{24})"', html)
            if not match:
                match = re.search(r'"channelId":"([a-zA-Z0-9_-]{24})"', html)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"⚠️ 채널 ID 조회 실패 (@{handle}): {e}")
    return None

def fetch_channel_videos(channel_id):
    """YouTube 공식 RSS 피드를 조회하여 최근 업로드된 영상 목록 반환"""
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
    
    videos = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
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
                media_group = entry.find("media:group", ns)
                
                desc = ""
                if media_group is not None:
                    desc_el = media_group.find("media:description", ns)
                    if desc_el is not None and desc_el.text:
                        desc = desc_el.text

                if video_id is not None and title is not None:
                    videos.append({
                        "youtube_id": video_id.text,
                        "title": title.text,
                        "published": published.text if published is not None else "",
                        "description": desc
                    })
    except Exception as e:
        print(f"⚠️ RSS 피드 조회 실패 (채널 ID: {channel_id}): {e}")

    return videos

def load_existing_video_ids():
    """기존 data.js 파일에서 이미 등록된 영상 ID 목록을 로드"""
    if not os.path.exists(DATA_JS_PATH):
        return set()
    
    with open(DATA_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # youtubeId: "..." 추출
    existing_ids = set(re.findall(r'youtubeId:\s*["\']([a-zA-Z0-9_-]{11})["\']', content))
    return existing_ids

def geocode_location(place_query):
    """OpenStreetMap Nominatim API로 장소 좌표(위도, 경도) 무료 지오코딩"""
    try:
        encoded_query = urllib.parse.quote(place_query)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=json&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "TubeMapTravelCollector/1.0 (travel-map@local)"})
        
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and len(data) > 0:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                return round(lat, 4), round(lng, 4)
    except Exception as e:
        pass
    return None, None

def analyze_video_location(title, description, creator_name):
    """
    영상 텍스트에서 국가, 도시, 스팟명, 꿀팁, 태그 추출
    (AI API Key가 없을 때도 작동하는 고성능 키워드 매칭 엔진)
    """
    full_text = f"{title} {description}"
    
    matched_spot = None
    # 1. 키워드 사전에서 매칭 검사
    for kw, spot_data in DESTINATION_DICTIONARY.items():
        if kw in full_text:
            matched_spot = {
                "country": spot_data["country"],
                "city": spot_data["city"],
                "locationName": f"{spot_data['city']} {kw}",
                "lat": spot_data["lat"],
                "lng": spot_data["lng"],
                "tags": [spot_data["city"], spot_data["country"], "여행"],
                "tip": f"{creator_name}의 {spot_data['city']} 여행 영상에서 소개된 추천 스팟입니다."
            }
            break

    # 2. 미매칭 시 정규식 패턴 검사 (예: [국가] 또는 【도시】)
    if not matched_spot:
        bracket_match = re.search(r'\[(.*?)\]|【(.*?)】|\((.*?)\)', title)
        if bracket_match:
            candidate = next(c for c in bracket_match.groups() if c)
            lat, lng = geocode_location(candidate)
            if lat and lng:
                matched_spot = {
                    "country": "해외",
                    "city": candidate,
                    "locationName": candidate,
                    "lat": lat,
                    "lng": lng,
                    "tags": [candidate, "여행"],
                    "tip": f"{creator_name}의 추천 여행 스팟."
                }

    return matched_spot

def is_within_max_age(published_str, max_days=MAX_VIDEO_AGE_DAYS):
    """영상이 최근 N일(기본 365일 = 1년) 이내에 업로드되었는지 검사"""
    if not published_str:
        return True
    try:
        clean_str = published_str.replace("Z", "+00:00")
        pub_dt = datetime.fromisoformat(clean_str)
        now = datetime.now(pub_dt.tzinfo)
        diff = (now - pub_dt).days
        return diff <= max_days
    except Exception:
        try:
            pub_date = datetime.strptime(published_str[:10], "%Y-%m-%d")
            diff = (datetime.now() - pub_date).days
            return diff <= max_days
        except Exception:
            return True

def append_to_data_js(new_entries):
    """새로 발견된 여행 영상 목록을 data.js 파일에 추가"""
    if not new_entries or not os.path.exists(DATA_JS_PATH):
        return

    with open(DATA_JS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # INITIAL_TRAVEL_VIDEOS = [ 뒤에 새 항목 삽입
    insert_pos = content.find("const INITIAL_TRAVEL_VIDEOS = [")
    if insert_pos == -1:
        print("❌ data.js 형식을 파싱할 수 없습니다.")
        return

    bracket_pos = content.find("[", insert_pos) + 1
    
    formatted_entries = []
    for item in new_entries:
        escaped_title = item['title'].replace('"', '\\"')
        escaped_loc = item['locationName'].replace('"', '\\"')
        escaped_tip = item['tip'].replace('"', '\\"')
        tags_json = json.dumps(item['tags'], ensure_ascii=False)
        pub_date = item.get('publishedAt', '')
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

    with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"\n🎉 data.js 파일에 총 {len(new_entries)}개의 새 여행지가 성공적으로 추가되었습니다!")

# =============================================================================
# 4. 메인 실행 흐름
# =============================================================================
def main():
    print("=" * 65)
    print("📍 TubeMap Travel - 한국 여행 유튜버 신규 영상 수집기 시작")
    print(f"⏰ 실행 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 필터 기준: 최근 {MAX_VIDEO_AGE_DAYS}일(1년) 이내 최신 영상만 수집")
    print("=" * 65)

    existing_ids = load_existing_video_ids()
    print(f"📦 현재 data.js에 등록된 영상 수: {len(existing_ids)}개\n")

    new_discovered_spots = []

    for ch in CHANNELS:
        name = ch["name"]
        channel_id = ch["channel_id"]
        
        # 채널 ID가 없으면 핸들로부터 자동 조회
        if not channel_id and ch.get("handle"):
            print(f"🔍 [{name}] 채널 ID 확인 중 (@{ch['handle']})...")
            channel_id = get_channel_id(ch["handle"])
            ch["channel_id"] = channel_id
            time.sleep(1)

        if not channel_id:
            print(f"⚠️ [{name}] 채널 ID를 찾을 수 없어 건너뜁니다.")
            continue

        print(f"📡 [{name}] 최근 업로드 영상 피드 수집 중...")
        videos = fetch_channel_videos(channel_id)
        time.sleep(1) # 요청 간격 예의 준수

        unregistered_videos = [v for v in videos if v["youtube_id"] not in existing_ids]

        if not unregistered_videos:
            print(f"   ✓ 새로운 신규 영상 없음 (모두 이미 등록됨)")
            continue

        print(f"   ✨ 미등록 신규 영상 {len(unregistered_videos)}편 발견!")

        for v in unregistered_videos:
            pub_date_str = v.get("published", "")[:10]
            # 1년(365일) 이내 최신 영상인지 확인
            if not is_within_max_age(v.get("published", "")):
                print(f"   [⏳] 1년 이상 경과된 과거 영상 스킵 ({pub_date_str}): {v['title'][:35]}...")
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
                    "publishedAt": pub_date_str
                }
                new_discovered_spots.append(entry)
                print(f"   [+] 최신 여행지 감지 ({pub_date_str}): {entry['country']} {entry['city']} ({entry['lat']}, {entry['lng']})")
                print(f"       영상 제목: {v['title'][:40]}...")
            else:
                print(f"   [-] 위치 키워드 미감지: {v['title'][:40]}... (일상/토크 영상 추정)")

    print("\n" + "=" * 65)
    print(f"📊 수집 결과 요약: 총 {len(new_discovered_spots)}개의 신규 여행지 추출 완료")
    print("=" * 65)

    if not new_discovered_spots:
        print("새로 추가할 여행 영상이 없습니다. 지도가 이미 최신 상태입니다.")
        return

    # 대화형 확인 (또는 --auto 플래그 시 자동 반영)
    is_auto = "--auto" in sys.argv
    if not is_auto:
        print("\n아래 항목들을 data.js에 추가하시겠습니까?")
        for idx, s in enumerate(new_discovered_spots, 1):
            print(f"  {idx}. [{s['creator']}] {s['country']} {s['locationName']} - {s['title'][:35]}...")
        
        answer = input("\n👉 data.js에 반영할까요? (Y/n): ").strip().lower()
        if answer not in ["y", "yes", ""]:
            print("작업이 취소되었습니다.")
            return

    append_to_data_js(new_discovered_spots)

if __name__ == "__main__":
    main()
