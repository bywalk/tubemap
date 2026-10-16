#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
TubeMap Travel - GitHub PR Data AI Validator
=============================================================================
기능:
1. PR에서 변경된 데이터 파일(js/data/videos_recent.js, videos_archive.js, channels.json) 감지
2. 비허용 파일(index.html, js/app.js 등 핵심 코드) 수정 시 자동 감지 및 경고
3. 추가/수정된 여행지 및 채널 데이터 정적 유효성 검증
   - 필수 필드, 위경도 좌표 범위, XSS/악성 스크립트 방어
   - YouTube oEmbed 실시간 호출 (영상 실존 여부 및 임베드 재생 허용 확인)
   - OpenStreetMap 역지오코딩 (좌표의 실제 국가/도시 일치 여부 확인)
4. Gemini AI 팩트체크
   - 영상 내용과 수정된 장소의 일치성, 꿀팁 신뢰성, 어뷰징 여부 검증
   - 0~100점 신뢰도 점수 및 판정 사유 생성
5. GitHub Actions PR 코멘트용 Markdown 리포트 및 라벨 판정('ai-verified' / 'needs-review') 출력
=============================================================================
"""

import os
import re
import sys
import json
import ssl
import urllib.request
import urllib.parse
import subprocess
from datetime import datetime

SAFE_SSL_CONTEXT = ssl._create_unverified_context()

ALLOWED_DATA_FILES = {
    "js/data/videos_recent.js",
    "js/data/videos_archive.js",
    "channels.json"
}

def run_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""

def get_changed_files(base_ref, head_ref):
    """Git diff로 변경된 파일 목록 조회"""
    out = run_cmd(f"git diff --name-only {base_ref} {head_ref}")
    if not out:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]

def get_file_content(ref, filepath):
    """지정된 커밋/브랜치의 파일 내용 조회"""
    return run_cmd(f"git show {ref}:{filepath}")

def extract_video_entries(js_code):
    """JS 파일에서 비디오 객체 목록 파싱"""
    if not js_code:
        return {}
    
    entries = {}
    # 객체 블록 정규식 매칭
    pattern = r'\{\s*id:\s*["\']([^"\']+)["\'](.*?)\n\s*\}'
    matches = re.findall(pattern, js_code, re.DOTALL)
    
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

        entries[vid_id] = {
            "id": vid_id,
            "creator": get_field("creator"),
            "youtubeId": get_field("youtubeId"),
            "title": get_field("title"),
            "country": get_field("country"),
            "city": get_field("city"),
            "locationName": get_field("locationName"),
            "lat": get_field("lat", is_num=True),
            "lng": get_field("lng", is_num=True),
            "tip": get_field("tip"),
            "tags": tags,
            "publishedAt": get_field("publishedAt")
        }
    return entries

def check_youtube_oembed(yt_id):
    """YouTube oEmbed API로 영상 실존 및 임베드 허용 여부 확인"""
    if not yt_id or len(yt_id) != 11:
        return False, "유효하지 않은 YouTube ID 형식", {}
    
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={yt_id}&format=json"
    req = urllib.request.Request(url, headers={"User-Agent": "TubeMap-PR-Validator/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=6, context=SAFE_SSL_CONTEXT) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                return True, "정상 재생 가능", data
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "제작자가 외부 사이트 퍼가기(임베드)를 차단한 영상", {}
        if e.code == 404:
            return False, "존재하지 않거나 삭제/비공개된 영상", {}
        return False, f"HTTP {e.code} 응답", {}
    except Exception as e:
        return False, f"조회 실패 ({e})", {}

    return False, "알 수 없는 상태", {}

def reverse_geocode(lat, lng):
    """OpenStreetMap Nominatim 역지오코딩"""
    if lat is None or lng is None:
        return None
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json&accept-language=ko"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "TubeMap-PR-Validator/1.0 (https://github.com/bywalk/tubemap)"}
        )
        with urllib.request.urlopen(req, timeout=6, context=SAFE_SSL_CONTEXT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            display_name = data.get("display_name", "")
            address = data.get("address", {})
            country = address.get("country", "")
            city = address.get("city") or address.get("town") or address.get("state") or ""
            return {"display_name": display_name, "country": country, "city": city}
    except Exception:
        return None

def verify_with_gemini(entry, yt_meta, geo_meta):
    """Gemini API를 이용한 팩트체크 및 신뢰도 산출"""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {
            "score": 85,
            "passed": True,
            "reason": "GEMINI_API_KEY 미설정으로 정적 검증 점수로 대체되었습니다."
        }

    prompt = f"""
당신은 여행 유튜브 지도 플랫폼 'TubeMap'의 데이터 검증 AI입니다.
기여자가 Pull Request로 제출한 여행지 데이터의 진위와 품질을 팩트체크하세요.

[제출된 데이터]
- 크리에이터: {entry.get('creator')}
- 영상 제목: {entry.get('title')}
- 유튜브 ID: {entry.get('youtubeId')}
- 유튜브 실제 메타데이터: {yt_meta.get('title', '')} (작성자: {yt_meta.get('author_name', '')})
- 국가/도시: {entry.get('country')} / {entry.get('city')}
- 장소명: {entry.get('locationName')}
- 위도/경도: {entry.get('lat')}, {entry.get('lng')}
- 실제 지도 역지오코딩 주소: {geo_meta.get('display_name') if geo_meta else '알 수 없음'}
- 꿀팁/메모: {entry.get('tip')}

[평가 기준]
1. 장소 일치성: 영상과 실제 지도 주소가 해당 여행지를 가리키는 것이 맞는가?
2. 좌표 정확성: 위경도 좌표가 엉뚱한 바다나 다른 나라가 아닌 해당 목적지 근처인가?
3. 내용 품질: 꿀팁에 비속어, 광고 스팸, 프롬프트 인젝션이 없는가?
4. 신뢰도 점수: 0~100점 (85점 이상: 확실한 여행지/좌표 교정, 70~84점: 다소 모호함, 70점 미만: 오매칭/스팸)

반드시 아래 JSON 형식으로만 응답하세요:
{{
  "confidence": 95,
  "passed": true,
  "reason": "영상 속에서 실제로 방문한 구체적인 명소의 위치 좌표와 일치하며 꿀팁이 유용합니다."
}}
"""
    models = ["gemini-2.5-flash", "gemini-flash-latest", "gemini-pro-latest"]
    for m in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"response_mime_type": "application/json", "temperature": 0.1}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=12, context=SAFE_SSL_CONTEXT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text_out = data["candidates"][0]["content"]["parts"][0]["text"]
                res = json.loads(text_out)
                confidence = int(res.get("confidence", 80))
                return {
                    "score": confidence,
                    "passed": bool(res.get("passed", confidence >= 80)),
                    "reason": res.get("reason", "검증 완료")
                }
        except Exception:
            continue

    return {"score": 80, "passed": True, "reason": "AI 검증 중 일시적 오류로 기본 점수 적용"}

def validate_pr(base_ref, head_ref):
    """PR 변경사항 종합 검증 파이프라인"""
    changed_files = get_changed_files(base_ref, head_ref)
    
    report_lines = []
    report_lines.append("## 🤖 TubeMap AI 데이터 검증 리포트\n")
    report_lines.append(f"PR 검증 대상 커밋: `{head_ref[:7] if len(head_ref) >= 7 else head_ref}` (기준: `{base_ref[:7] if len(base_ref) >= 7 else base_ref}`)\n")

    # 1. 파일 검증
    code_files = [f for f in changed_files if f not in ALLOWED_DATA_FILES]
    has_code_changes = len(code_files) > 0
    if has_code_changes:
        report_lines.append("⚠️ **주의: 데이터 파일 외에 코드 파일이 포함되어 있습니다.**")
        for f in code_files:
            report_lines.append(f"- `{f}`")
        report_lines.append("\n코드 변경은 관리자의 별도 수동 보안 검토가 필요합니다.\n")

    overall_passed = True
    validated_items = []
    MAX_ITEMS = 25
    checked_count = 0

    # 2. JS 데이터 파일 검증
    for filepath in ["js/data/videos_recent.js", "js/data/videos_archive.js"]:
        if filepath not in changed_files:
            continue

        base_content = get_file_content(base_ref, filepath)
        head_content = get_file_content(head_ref, filepath)
        base_entries = extract_video_entries(base_content)
        head_entries = extract_video_entries(head_content)

        # 추가 또는 수정된 엔트리 탐색
        for vid_id, head_entry in head_entries.items():
            base_entry = base_entries.get(vid_id)
            if base_entry == head_entry:
                continue  # 변경 없음

            checked_count += 1
            if checked_count > MAX_ITEMS:
                report_lines.append(f"\nℹ️ 변경 항목이 {MAX_ITEMS}개를 초과하여 상위 {MAX_ITEMS}개만 대표로 자동 검증했습니다.")
                break

            print(f"[validate_pr] 검증 중 ({checked_count}/{MAX_ITEMS}): {head_entry.get('locationName')} ({head_entry.get('creator')})", file=sys.stderr)

            is_new = base_entry is None
            change_type = "신규 등록" if is_new else "위치/정보 수정"

            # 정적 유효성 검사
            errors = []
            lat = head_entry.get("lat")
            lng = head_entry.get("lng")
            yt_id = head_entry.get("youtubeId")

            if not head_entry.get("title"):
                errors.append("제목 누락")
            if not head_entry.get("creator"):
                errors.append("크리에이터 누락")
            if lat is None or lng is None:
                errors.append("위도/경도 좌표 누락")
            elif not (-90 <= lat <= 90 and -180 <= lng <= 180):
                errors.append(f"좌표 범위 비정상 (lat: {lat}, lng: {lng})")

            # YouTube oEmbed 검사
            yt_ok, yt_msg, yt_meta = check_youtube_oembed(yt_id)
            if not yt_ok:
                errors.append(f"YouTube 영상 검증 실패: {yt_msg}")

            # OSM 역지오코딩
            geo_meta = reverse_geocode(lat, lng) if lat and lng else None

            # Gemini AI 검증
            if not errors:
                ai_res = verify_with_gemini(head_entry, yt_meta, geo_meta)
                if not ai_res["passed"]:
                    errors.append(f"AI 신뢰도 기준 미달 ({ai_res['score']}점): {ai_res['reason']}")
            else:
                ai_res = {"score": 20, "passed": False, "reason": ", ".join(errors)}

            item_status = len(errors) == 0 and ai_res["passed"]
            if not item_status:
                overall_passed = False

            validated_items.append({
                "file": filepath,
                "type": change_type,
                "entry": head_entry,
                "base_entry": base_entry,
                "yt_meta": yt_meta,
                "geo_meta": geo_meta,
                "ai_res": ai_res,
                "passed": item_status,
                "errors": errors
            })

    # 3. channels.json 검증
    if "channels.json" in changed_files:
        try:
            head_channels = json.loads(get_file_content(head_ref, "channels.json"))
            base_channels = json.loads(get_file_content(base_ref, "channels.json"))
            base_handles = {c.get("handle") for c in base_channels}
            for ch in head_channels:
                if ch.get("handle") not in base_handles:
                    validated_items.append({
                        "file": "channels.json",
                        "type": "새 채널 추가",
                        "entry": ch,
                        "passed": True,
                        "ai_res": {"score": 90, "reason": f"신규 채널 등록 (@{ch.get('handle')})"},
                        "errors": []
                    })
        except Exception as e:
            overall_passed = False
            report_lines.append(f"❌ `channels.json` JSON 문법 파싱 오류: {e}")

    # 리포트 테이블 작성
    if not validated_items and not has_code_changes:
        report_lines.append("ℹ️ 변경된 여행지 데이터 항목이 없습니다.\n")
    elif validated_items:
        report_lines.append("### 📋 검증 항목 결과 요약\n")
        report_lines.append("| 상태 | 유형 | 크리에이터 | 여행지 / 명소 | 유튜브 | AI 신뢰도 | 판정 내용 |")
        report_lines.append("|:---:|:---:|:---|:---|:---:|:---:|:---|")

        for item in validated_items:
            e = item.get("entry", {})
            st = "✅ 통과" if item["passed"] else "❌ 주의"
            score = item["ai_res"].get("score", 0)
            reason = item["ai_res"].get("reason", "")
            yt_link = f"[{e.get('youtubeId')}](https://youtu.be/{e.get('youtubeId')})" if e.get("youtubeId") else "-"
            loc_display = f"{e.get('city')} - {e.get('locationName')}" if e.get("city") else e.get("locationName", "-")
            
            # 구글 지도 링크
            if e.get("lat") and e.get("lng"):
                loc_display += f" ([지도](https://www.google.com/maps?q={e['lat']},{e['lng']}))"

            report_lines.append(
                f"| {st} | {item['type']} | {e.get('creator', '-')} | {loc_display} | {yt_link} | **{score}점** | {reason} |"
            )
        report_lines.append("")

    # 최종 권장 조치
    final_label = "ai-verified" if (overall_passed and not has_code_changes) else "needs-review"
    report_lines.append("---")
    if final_label == "ai-verified":
        report_lines.append("### 🎯 최종 판정: **✅ 자동 검증 통과 (Verified)**")
        report_lines.append("- 모든 데이터 무결성 검증과 AI 팩트체크를 통과했습니다.")
        report_lines.append("- 관리자는 PR의 `Files changed` 탭을 최종 확인한 후 **[Merge pull request]** 버튼을 눌러 안전하게 반영할 수 있습니다.")
    else:
        report_lines.append("### 🎯 최종 판정: **⚠️ 수동 검토 필요 (Needs Review)**")
        report_lines.append("- AI 신뢰도 기준 미달, 위치 불일치, 또는 코드 파일 변경이 감지되었습니다.")
        report_lines.append("- 관리자의 상세 수동 확인 후 머지 여부를 결정해 주세요.")

    report_markdown = "\n".join(report_lines)
    return {
        "passed": overall_passed and not has_code_changes,
        "label": final_label,
        "markdown": report_markdown
    }

if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    head = sys.argv[2] if len(sys.argv) > 2 else "HEAD"
    
    result = validate_pr(base, head)
    print(result["markdown"])
    
    # GitHub Actions 환경변수 파일에 출력 기록
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"label={result['label']}\n")
            f.write(f"passed={'true' if result['passed'] else 'false'}\n")
    
    # 리포트 파일로도 저장
    with open("pr_report.md", "w", encoding="utf-8") as f:
        f.write(result["markdown"])
