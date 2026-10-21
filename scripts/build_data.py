#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TubeMap Travel - Contributions JSON Compiler & Data Synchronizer
=============================================================================
기능:
1. contributions/ 폴더(creators/, regions/, custom/ 등) 내의 모든 기여 JSON 파일 수집
2. 다양한 JSON 포맷(배열, { videos: [...] }, 단일 객체 등) 자동 파싱 및 정규화
3. 기존 js/data/videos_recent.js 데이터와 지능적 비교 (중복 제거 및 좌표/꿀팁 개선 업데이트)
4. 신규 유튜버 발견 시 channels.json 자동 등록
5. 최종 병합 결과를 js/data/videos_recent.js에 컴파일하여 자동 갱신
6. --dry-run 옵션 지원 (미리보기 및 CI 리포트용)
=============================================================================
"""

import os
import re
import sys
import json
import glob
import argparse
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTRIBUTIONS_DIR = os.path.join(ROOT_DIR, "contributions")
DATA_RECENT_PATH = os.path.join(ROOT_DIR, "js", "data", "videos_recent.js")
DATA_ARCHIVE_PATH = os.path.join(ROOT_DIR, "js", "data", "videos_archive.js")
CHANNELS_PATH = os.path.join(ROOT_DIR, "channels.json")

def load_channels():
    if not os.path.exists(CHANNELS_PATH):
        return []
    try:
        with open(CHANNELS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_channels(channels):
    with open(CHANNELS_PATH, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)

def extract_video_entries_from_js(js_content):
    """JS 코드에서 비디오 객체 목록 파싱"""
    if not js_content:
        return []
    
    pattern = r'\{\s*id:\s*["\']([^"\']+)["\'](.*?)\n\s*\}'
    matches = re.findall(pattern, js_content, re.DOTALL)
    
    entries = []
    for vid_id, body in matches:
        def get_field(name, is_num=False):
            if is_num:
                m = re.search(rf'{name}:\s*([-\d\.]+)', body)
                return float(m.group(1)) if m else None
            m = re.search(rf'{name}:\s*["\'](.*?)["\']', body)
            return m.group(1) if m else ""

        tags_m = re.search(r'tags:\s*(\[[^\]]*\])', body)
        tags = []
        if tags_m:
            try:
                tags = json.loads(tags_m.group(1))
            except Exception:
                pass

        highlights_m = re.search(r'highlights:\s*(\[[^\]]*\])', body)
        highlights = []
        if highlights_m:
            try:
                highlights = json.loads(highlights_m.group(1))
            except Exception:
                pass

        start_time_m = re.search(r'startTime:\s*(\d+)', body)
        start_time = int(start_time_m.group(1)) if start_time_m else None

        entry = {
            "id": vid_id,
            "creator": get_field("creator"),
            "youtubeId": get_field("youtubeId"),
            "title": get_field("title"),
            "channel": get_field("channel") or get_field("creator"),
            "country": get_field("country") or "기타",
            "city": get_field("city") or "기타",
            "locationName": get_field("locationName") or "주요 명소",
            "lat": get_field("lat", is_num=True),
            "lng": get_field("lng", is_num=True),
            "tip": get_field("tip"),
            "tags": tags,
            "publishedAt": get_field("publishedAt") or datetime.now().strftime("%Y-%m-%d"),
            "description": get_field("description") or get_field("title"),
            "highlights": highlights
        }
        if start_time is not None:
            entry["startTime"] = start_time
        entries.append(entry)
    return entries

def parse_contribution_file(filepath):
    """다양한 형식의 기여 JSON 파일 파싱 및 스팟 목록 추출"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    raw_spots = []
    if isinstance(data, list):
        raw_spots = data
    elif isinstance(data, dict):
        if "videos" in data and isinstance(data["videos"], list):
            raw_spots = data["videos"]
        elif "spots" in data and isinstance(data["spots"], list):
            raw_spots = data["spots"]
        elif "data" in data and isinstance(data["data"], list):
            raw_spots = data["data"]
        elif "youtubeId" in data:
            raw_spots = [data]
            
    normalized = []
    for idx, item in enumerate(raw_spots):
        if not isinstance(item, dict):
            continue
        yt_id = item.get("youtubeId") or item.get("youtube_id") or item.get("ytId")
        if not yt_id or len(str(yt_id).strip()) != 11:
            continue
            
        lat = item.get("lat")
        lng = item.get("lng")
        try:
            lat = float(lat)
            lng = float(lng)
        except (TypeError, ValueError):
            continue
            
        creator = (item.get("creator") or item.get("channel") or "").strip()
        location_name = (item.get("locationName") or item.get("location_name") or item.get("spot") or "").strip()
        country = (item.get("country") or "").strip() or "기타"
        city = (item.get("city") or "").strip() or country
        title = (item.get("title") or location_name or f"{creator} 여행 영상").strip()
        tip = (item.get("tip") or "").strip()
        tags = item.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        elif not isinstance(tags, list):
            tags = []
            
        pub_date = item.get("publishedAt") or item.get("published") or datetime.now().strftime("%Y-%m-%d")

        start_time = item.get("startTime") or item.get("start_time")
        if start_time is not None:
            try:
                start_time = int(start_time)
            except (ValueError, TypeError):
                start_time = None
        
        # 고유 ID 생성 (없을 경우)
        spot_id = item.get("id")
        if not spot_id:
            safe_loc = re.sub(r'[^a-zA-Z0-9]', '', location_name)[:8]
            spot_id = f"contrib-{yt_id}-{safe_loc or idx}"

        entry = {
            "id": spot_id,
            "creator": creator or "여행 유튜버",
            "youtubeId": yt_id,
            "title": title,
            "channel": item.get("channel") or creator or "여행 유튜버",
            "country": country,
            "city": city,
            "locationName": location_name or "추천 여행지",
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "tags": tags,
            "tip": tip or f"{creator}의 {location_name} 추천 스팟입니다.",
            "publishedAt": pub_date,
            "description": item.get("description") or title,
            "highlights": item.get("highlights") or []
        }
        if start_time is not None:
            entry["startTime"] = start_time

        normalized.append(entry)
        
    return normalized

def format_js_file(entries):
    """엔트리 리스트를 깨끗한 videos_recent.js 파일 문자열로 직렬화"""
    lines = [
        "/**",
        " * 최신 여행 영상 데이터 (2026년~)",
        " * Auto-compiled by scripts/build_data.py",
        " */",
        "const RECENT_VIDEOS = ["
    ]
    
    for item in entries:
        escaped_title = json.dumps(item.get('title', ''), ensure_ascii=False)
        escaped_creator = json.dumps(item.get('creator', ''), ensure_ascii=False)
        escaped_channel = json.dumps(item.get('channel', item.get('creator', '')), ensure_ascii=False)
        escaped_country = json.dumps(item.get('country', ''), ensure_ascii=False)
        escaped_city = json.dumps(item.get('city', ''), ensure_ascii=False)
        escaped_loc = json.dumps(item.get('locationName', ''), ensure_ascii=False)
        escaped_tip = json.dumps(item.get('tip', ''), ensure_ascii=False)
        escaped_desc = json.dumps(item.get('description', item.get('title', '')), ensure_ascii=False)
        tags_json = json.dumps(item.get('tags', []), ensure_ascii=False)
        highlights_json = json.dumps(item.get('highlights', []), ensure_ascii=False)
        pub_date = item.get('publishedAt', datetime.now().strftime("%Y-%m-%d"))

        start_time_line = f"\n    startTime: {int(item['startTime'])}," if item.get('startTime') is not None else ""

        entry_code = f"""  // [{item.get('creator', '')}] {item.get('country', '')} {item.get('city', '')} - {item.get('locationName', '')} ({pub_date})
  {{
    id: "{item['id']}",
    creator: {escaped_creator},
    youtubeId: "{item['youtubeId']}",
    title: {escaped_title},
    channel: {escaped_channel},
    country: {escaped_country},
    city: {escaped_city},
    locationName: {escaped_loc},
    lat: {float(item['lat'])},
    lng: {float(item['lng'])},{start_time_line}
    tags: {tags_json},
    tip: {escaped_tip},
    publishedAt: "{pub_date}",
    description: {escaped_desc},
    highlights: {highlights_json}
  }},"""
        lines.append(entry_code)

    lines.append("];\n")
    return "\n".join(lines)

def build_contributions(dry_run=False, verbose=False):
    """contributions/ 폴더 내 파일들을 videos_recent.js로 병합"""
    if not os.path.exists(CONTRIBUTIONS_DIR):
        print(f"📁 기여 폴더가 존재하지 않습니다: {CONTRIBUTIONS_DIR}")
        return {"added": 0, "updated": 0, "total": 0}

    # 1. 기존 데이터 로드
    with open(DATA_RECENT_PATH, "r", encoding="utf-8") as f:
        existing_recent = extract_video_entries_from_js(f.read())
    
    existing_archive = []
    if os.path.exists(DATA_ARCHIVE_PATH):
        with open(DATA_ARCHIVE_PATH, "r", encoding="utf-8") as f:
            existing_archive = extract_video_entries_from_js(f.read())

    # 빠른 조회를 위한 인덱스 생성
    # Key: (youtubeId, locationName.lower()) or id
    recent_map_by_key = {}
    recent_map_by_id = {}
    for entry in existing_recent:
        recent_map_by_id[entry["id"]] = entry
        key = (entry["youtubeId"], entry["locationName"].strip().lower())
        recent_map_by_key[key] = entry

    archive_keys = {
        (entry["youtubeId"], entry["locationName"].strip().lower())
        for entry in existing_archive
    }
    archive_ids = {entry["id"] for entry in existing_archive}

    # 2. contributions/ 폴더 스캔 (*.json)
    json_files = []
    for root, dirs, files in os.walk(CONTRIBUTIONS_DIR):
        # samples 디렉터리는 예시 템플릿이므로 자동 병합에서 제외
        if "samples" in root:
            continue
        for f in files:
            if f.endswith(".json"):
                json_files.append(os.path.join(root, f))

    print("=" * 70)
    print("🚀 TubeMap Contributions Compiler")
    print(f"📂 대상 기여 JSON 파일: {len(json_files)}개 발견")
    print(f"📦 현재 등록된 최신 여행지 수: {len(existing_recent)}개")
    print("=" * 70)

    added_entries = []
    updated_count = 0
    new_creators_found = set()
    channels = load_channels()
    known_channel_names = {c["name"].lower() for c in channels}

    for jpath in json_files:
        rel_path = os.path.relpath(jpath, ROOT_DIR)
        try:
            spots = parse_contribution_file(jpath)
        except Exception as e:
            print(f"⚠️ {rel_path} 파일 파싱 실패: {e}")
            continue

        if not spots:
            continue

        file_added = 0
        file_updated = 0

        for spot in spots:
            creator_name = spot["creator"]
            if creator_name and creator_name.lower() not in known_channel_names:
                new_creators_found.add(creator_name)

            key = (spot["youtubeId"], spot["locationName"].strip().lower())
            
            # 아카이브에 이미 있으면 건너뜀
            if key in archive_keys or spot["id"] in archive_ids:
                continue

            # 기존 최신 데이터에 존재하는지 확인
            target_entry = recent_map_by_id.get(spot["id"]) or recent_map_by_key.get(key)
            if target_entry:
                # 변경 사항이 있는지 확인 및 업데이트
                has_diff = False
                if abs(target_entry["lat"] - spot["lat"]) > 0.0001 or abs(target_entry["lng"] - spot["lng"]) > 0.0001:
                    target_entry["lat"] = spot["lat"]
                    target_entry["lng"] = spot["lng"]
                    has_diff = True
                if spot["tip"] and spot["tip"] != target_entry["tip"] and len(spot["tip"]) > len(target_entry.get("tip", "")):
                    target_entry["tip"] = spot["tip"]
                    has_diff = True
                if spot["tags"]:
                    merged_tags = list(dict.fromkeys(target_entry.get("tags", []) + spot["tags"]))
                    if merged_tags != target_entry.get("tags"):
                        target_entry["tags"] = merged_tags
                        has_diff = True
                if spot.get("startTime") is not None and spot["startTime"] != target_entry.get("startTime"):
                    target_entry["startTime"] = spot["startTime"]
                    has_diff = True

                if has_diff:
                    file_updated += 1
                    updated_count += 1
                    if verbose:
                        print(f"   [✏️ 수정] [{spot['creator']}] {spot['locationName']}")
            else:
                # 신규 스팟 추가
                added_entries.append(spot)
                recent_map_by_id[spot["id"]] = spot
                recent_map_by_key[key] = spot
                file_added += 1
                if verbose:
                    print(f"   [✨ 추가] [{spot['creator']}] {spot['country']} {spot['city']} - {spot['locationName']}")

        print(f"📄 {rel_path}: 신규 {file_added}개 추가, {file_updated}개 업데이트")

    # 신규 스팟을 최상단에 배치하여 최신성 유지
    final_entries = added_entries + existing_recent

    print("\n" + "=" * 70)
    print(f"📊 병합 결과 요약:")
    print(f"  - 신규 추가된 여행지: {len(added_entries)}곳")
    print(f"  - 정보 갱신된 여행지: {updated_count}곳")
    print(f"  - 최종 전체 여행지: {len(final_entries)}곳")
    if new_creators_found:
        print(f"  - 신규 감지된 유튜버 ({len(new_creators_found)}팀): {', '.join(list(new_creators_found)[:5])}")
    print("=" * 70)

    if dry_run:
        print("\n🔍 [dry-run] 실제 파일에 변경 사항을 기록하지 않았습니다.")
        return {
            "added": len(added_entries),
            "updated": updated_count,
            "total": len(final_entries),
            "new_creators": list(new_creators_found)
        }

    # 실제 파일 쓰기
    if added_entries or updated_count > 0:
        compiled_js = format_js_file(final_entries)
        with open(DATA_RECENT_PATH, "w", encoding="utf-8") as f:
            f.write(compiled_js)
        print(f"✅ {os.path.basename(DATA_RECENT_PATH)} 파일이 성공적으로 컴파일 및 갱신되었습니다!")

        # 신규 크리에이터 channels.json에 등록
        if new_creators_found:
            for cname in sorted(new_creators_found):
                channels.append({"name": cname, "handle": ""})
            save_channels(channels)
            print(f"🎉 channels.json에 신규 유튜버 {len(new_creators_found)}팀이 등록되었습니다.")
    else:
        print("💡 추가 또는 수정할 새로운 기여 데이터가 없습니다.")

    return {
        "added": len(added_entries),
        "updated": updated_count,
        "total": len(final_entries),
        "new_creators": list(new_creators_found)
    }

def main():
    parser = argparse.ArgumentParser(description="TubeMap Contributions JSON Compiler")
    parser.add_argument("--dry-run", action="store_true", help="파일을 수정하지 않고 병합 결과만 미리보기")
    parser.add_argument("--verbose", "-v", action="store_true", help="추가/수정되는 세부 여행지 로그 출력")
    args = parser.parse_args()

    build_contributions(dry_run=args.dry_run, verbose=args.verbose)

if __name__ == "__main__":
    main()
