# 🌏 TubeMap 여행지 데이터 기여 가이드 (Contributions)

TubeMap Travel은 전 세계 여행 유튜버들의 실제 여행 코스와 맛집·명소 좌표를 지도 위에 기록하는 오픈소스 프로젝트입니다.  
복잡한 자바스크립트 코드 수정 없이, **유튜버별** 또는 **지역/도시별**로 모은 여행지 목록을 **JSON 파일**로 작성하여 간편하게 PR(Pull Request)을 올릴 수 있습니다.

---

## 📁 디렉터리 구성

기여하고자 하는 성격에 맞는 폴더에 `.json` 파일을 생성해 주세요:

```text
contributions/
  ├── creators/      # 특정 유튜버별 여행지 모음 (예: panibottle.json, wonji.json)
  ├── regions/       # 특정 국가/도시/지역별 여행지 모음 (예: japan_kyoto.json, egypt_dahab.json)
  ├── custom/        # 테마별 또는 개인 큐레이션 여행지 모음
  └── samples/       # 작성 참고용 샘플 템플릿
```

---

## 📋 JSON 데이터 형식 (Schema)

JSON 파일은 **배열(`[...]`)** 형태 또는 **래핑 객체(`{ "videos": [...] }`)** 형태 모두 지원합니다.

### 추천 포맷 (배열 형태)
```json
[
  {
    "youtubeId": "uaBHe5P4JF8",
    "creator": "빠니보틀",
    "title": "사막 한가운데서 먹는 양꼬치",
    "country": "이집트",
    "city": "다합",
    "locationName": "다합 라이트하우스 해변",
    "lat": 28.5097,
    "lng": 34.5136,
    "tip": "스노클링 장비 대여 가능, 석양이 아름다운 포인트",
    "tags": ["해변", "스노클링", "일몰"],
    "publishedAt": "2023-05-10"
  }
]
```

### 필드 상세 설명
| 필드명 | 타입 | 필수 여부 | 설명 |
| :--- | :--- | :---: | :--- |
| `youtubeId` | string | **필수** | 유튜브 영상 고유 ID 11자리 (URL의 `v=` 파라미터 값) |
| `creator` | string | **필수** | 여행 유튜버 이름 (예: `빠니보틀`, `곽튜브`, `원지의 하루`) |
| `title` | string | **필수** | 유튜브 영상 제목 |
| `country` | string | **필수** | 방문 국가명 (예: `이집트`, `일본`, `대한민국`) |
| `city` | string | **필수** | 방문 도시/지역명 (예: `다합`, `교토`, `제주`) |
| `locationName`| string | **필수** | 정확한 장소 / 명소 / 맛집 이름 |
| `lat` | number | **필수** | 위도 좌표 (예: `28.5097`, 구글맵 또는 TubeMap 지도에서 확인) |
| `lng` | number | **필수** | 경도 좌표 (예: `34.5136`) |
| `tip` | string | 선택 | 유튜버의 꿀팁, 추천 메뉴, 방문 시 주의점 등 |
| `tags` | array | 선택 | 관련 키워드 태그 목록 (예: `["맛집", "오션뷰"]`) |
| `publishedAt` | string | 선택 | 영상 업로드 일자 (`YYYY-MM-DD` 형식) |

---

## 🤖 자동 검증 및 병합 시스템

1. **PR 등록**: `contributions/**/*.json` 파일이 포함된 PR을 등록하면 GitHub Actions의 AI 팩트체커가 작동합니다.
   - 필수 필드 및 위경도 좌표 정상 여부 확인
   - YouTube 영상 실제 존재 및 임베드 재생 허용 확인
   - OpenStreetMap 역지오코딩을 통한 실제 국가/도시 일치 여부 확인
   - Gemini AI를 통한 영상 내용과 장소의 사실 검증
2. **자동 리포트**: PR에 검증 결과 리포트 및 `ai-verified` 라벨이 부여됩니다.
3. **자동 병합**: PR이 머지되면 GitHub Actions가 `scripts/build_data.py`를 실행하여 서비스 메인 데이터([videos_recent.js](file:///Users/bongsok/dev/tubemap/js/data/videos_recent.js))에 즉시 컴파일·반영합니다.

---

## 🛠️ 로컬에서 테스트하기

로컬 환경에서 변경된 JSON 파일이 메인 데이터에 어떻게 반영되는지 미리 확인할 수 있습니다:

```bash
# 변경 사항 미리보기 (dry-run, 파일 수정 없음)
python3 scripts/build_data.py --dry-run

# 실제 videos_recent.js로 빌드 및 병합 실행
python3 scripts/build_data.py
```
