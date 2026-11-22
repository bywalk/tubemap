#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean up false positives and normalize day-chapters in videos_recent.js
"""

import subprocess
import json

JS_SCRIPT = """
let fs = $.NSString.stringWithContentsOfFileEncodingError('js/data/videos_recent.js', $.NSUTF8StringEncoding, null).js;
fs = fs.replace('const RECENT_VIDEOS', 'var RECENT_VIDEOS');
eval(fs);

// Process and clean up
const cleaned = [];
const seenVideoIds = new Set();

// Special replacements map by youtubeId
const specialFixes = {
  "c_NjIzSb244": { // 전지영 부산 촌뜨기 -> LA
    country: "미국",
    city: "로스앤젤레스",
    locationName: "로스앤젤레스 주요 명소",
    lat: 34.0522,
    lng: -118.2437,
    tags: ["로스앤젤레스", "미국", "유튜브추천", "여행"],
    tip: "전지영의 로스앤젤레스 여행 영상 추천 스팟입니다."
  },
  "txGdg7Cyujw": { // 유네린 튀르키예 파묵칼레 (고대로마 -> 파묵칼레)
    country: "튀르키예",
    city: "파묵칼레",
    locationName: "파묵칼레",
    lat: 37.9255,
    lng: 29.1213,
    tags: ["파묵칼레", "튀르키예", "유튜브추천", "여행"],
    tip: "유네린LIN의 파묵칼레 여행 영상 추천 스팟입니다."
  },
  "0z6SZ_dAiEc": { // 유정 이집트 카이로 피라미드
    country: "이집트",
    city: "카이로",
    locationName: "카이로 피라미드 & 스핑크스",
    lat: 29.9792,
    lng: 31.1342,
    tags: ["카이로", "이집트", "유튜브추천", "여행"],
    tip: "유정 YUJEONG의 카이로 피라미드 & 스핑크스 추천 스팟입니다."
  },
  "2t3bLdG_WVo": { // 유정 다합
    country: "이집트",
    city: "다합",
    locationName: "다합 블루홀",
    lat: 28.5724,
    lng: 34.5369,
    tags: ["다합", "이집트", "유튜브추천", "여행"],
    tip: "유정 YUJEONG의 다합 블루홀 추천 스팟입니다."
  },
  "YobD6OBYToE": { // 유정 포지타노
    country: "이탈리아",
    city: "포지타노",
    locationName: "포지타노 & 폼페이 남부 투어",
    lat: 40.6281,
    lng: 14.4850,
    tags: ["포지타노", "이탈리아", "유튜브추천", "여행"],
    tip: "유정 YUJEONG의 포지타노 & 폼페이 남부 투어 추천 스팟입니다."
  },
  "bybYtAtURCM": { // 유정 런던
    country: "영국",
    city: "런던",
    locationName: "런던 쇼디치 & 노팅힐",
    lat: 51.5074,
    lng: -0.1278,
    tags: ["런던", "영국", "유튜브추천", "여행"],
    tip: "유정 YUJEONG의 런던 쇼디치 & 노팅힐 추천 스팟입니다."
  },
  "J543v1EnWGI": { // 빠니보틀 네바다 버닝맨
    country: "미국",
    city: "네바다",
    locationName: "네바다 블랙록 사막 (버닝맨)",
    lat: 40.7864,
    lng: -119.2065,
    tags: ["네바다", "미국", "버닝맨", "블랙록사막", "유튜브추천"],
    tip: "빠니보틀이 참가한 네바다 블랙록 사막의 버닝맨 축제 생생한 현장입니다."
  },
  "C5fSM-oBRLU": { // 곽튜브 라스베이거스
    country: "미국",
    city: "라스베이거스",
    locationName: "라스베이거스 스트립",
    lat: 36.1699,
    lng: -115.1398,
    tags: ["라스베이거스", "미국", "유튜브추천", "여행"],
    tip: "곽튜브가 방문한 라스베이거스 추천 스팟입니다."
  },
  "HdgVr1uWSr0": { // 곽튜브 라스베이거스 (上)
    country: "미국",
    city: "라스베이거스",
    locationName: "라스베이거스 스트립",
    lat: 36.1699,
    lng: -115.1398,
    tags: ["라스베이거스", "미국", "유튜브추천", "여행"],
    tip: "곽튜브가 방문한 라스베이거스 추천 스팟입니다."
  },
  "aoulvT4e2HY": { // 트립콤파니 그랜드 캐니언
    country: "미국",
    city: "그랜드캐니언",
    locationName: "그랜드캐니언 국립공원",
    lat: 36.0544,
    lng: -112.1401,
    tags: ["그랜드캐니언", "애리조나", "미국", "유튜브추천"],
    tip: "트립콤파니가 추천하는 미국 그랜드캐니언 완벽 가이드 코스입니다."
  },
  "TlFUN5vz33U": { // 콩빈 LA
    country: "미국",
    city: "로스앤젤레스",
    locationName: "로스앤젤레스 주요 명소",
    lat: 34.0522,
    lng: -118.2437,
    tags: ["로스앤젤레스", "미국", "LA", "유튜브추천"],
    tip: "콩빈Cong Been의 로스앤젤레스(LA) 맛집 & 빈티지샵 투어 스팟입니다."
  },
  "-Sm2CX-rNH0": { // 캡틴따거 송탄 미군기지
    country: "대한민국",
    city: "평택",
    locationName: "평택 송탄 신장쇼핑몰 (오산공군기지)",
    lat: 37.0818,
    lng: 127.0543,
    tags: ["평택", "송탄", "대한민국", "유튜브추천"],
    tip: "캡틴따거가 복무했던 오산공군기지 앞 추억의 거리입니다."
  },
  "mpR_HcJ3Szc": { // 곽튜브 샌프란시스코
    country: "미국",
    city: "샌프란시스코",
    locationName: "샌프란시스코 시내",
    lat: 37.7749,
    lng: -122.4194,
    tags: ["샌프란시스코", "미국", "유튜브추천"],
    tip: "곽튜브가 방문한 샌프란시스코 시내 추천 명소입니다."
  }
};

for (const v of RECENT_VIDEOS) {
  const yid = v.youtubeId;
  const name = v.locationName || '';

  // 1. Check special fixes
  if (specialFixes[yid]) {
    if (!seenVideoIds.has(yid)) {
      seenVideoIds.add(yid);
      const fix = specialFixes[yid];
      cleaned.push({
        ...v,
        id: `auto-${yid}`,
        locationName: fix.locationName,
        country: fix.country,
        city: fix.city,
        lat: fix.lat,
        lng: fix.lng,
        tags: fix.tags,
        tip: fix.tip,
        startTime: 0
      });
    }
    continue;
  }

  // 2. Filter out pure day chapters or intro
  if (/^\d+\s*일차?$/i.test(name) || /^[Dd]ay\s*\d+$/i.test(name) || /^intro$/i.test(name)) {
    // If we already added this video or it is a generic day, skip or normalize
    continue;
  }

  // 3. Normalize Japanese train name
  if (name.includes("출발일 기준 1개월")) {
    v.locationName = "오사카 긴테쓰 시마카제 관광특급";
  }

  cleaned.push(v);
}

JSON.stringify(cleaned);
"""

def main():
    res = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", JS_SCRIPT],
        capture_output=True,
        text=True,
        check=True
    )
    items = json.loads(res.stdout)
    print(f"Cleaned items count: {len(items)}")

    # Format into videos_recent.js
    header = '/**\n * 최신 여행 영상 데이터 (2026년~)\n */\nconst RECENT_VIDEOS = [\n'
    entries = []
    for item in items:
        entry_lines = ["  {"]
        for k in ["id", "creator", "youtubeId", "title", "channel", "country", "city", "locationName", "lat", "lng", "startTime", "tags", "tip", "publishedAt", "description", "highlights"]:
            if k not in item:
                if k == "highlights":
                    item[k] = []
                elif k == "startTime":
                    continue
                else:
                    item[k] = ""
            val = item[k]
            if isinstance(val, str):
                escaped = val.replace('\\', '\\\\').replace('"', '\\"').replace('\n', ' ')
                entry_lines.append(f'    {k}: "{escaped}",')
            elif isinstance(val, (int, float)):
                entry_lines.append(f'    {k}: {val},')
            elif isinstance(val, list):
                json_arr = json.dumps(val, ensure_ascii=False)
                entry_lines.append(f'    {k}: {json_arr},')
        # Remove trailing comma from last property
        entry_lines[-1] = entry_lines[-1].rstrip(',')
        entry_lines.append("  }")
        entries.append("\n".join(entry_lines))

    body = ",\n".join(entries) + "\n];\n"
    
    with open("js/data/videos_recent.js", "w", encoding="utf-8") as f:
        f.write(header + body)
    
    print("✅ js/data/videos_recent.js successfully cleaned and updated!")

if __name__ == "__main__":
    main()
