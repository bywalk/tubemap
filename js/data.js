/**
 * 한국 대표 여행 유튜버 추천 여행지 데이터셋
 * (빠니보틀, 곽튜브, 원지의 하루, 채코제, 여행가 제이, 잰잰바리 등)
 */
const INITIAL_TRAVEL_VIDEOS = [
  // ================= 빠니보틀 (Pani Bottle) =================
  {
    id: "pani-1",
    creator: "빠니보틀",
    youtubeId: "yvo9Jyg35y4",
    title: "이집트 홍해 한달살기, 배낭여행자들의 무덤 다합 라이트하우스",
    channel: "빠니보틀 Pani Bottle",
    country: "이집트",
    city: "다합",
    locationName: "다합 라이트하우스 (Lighthouse Reef)",
    lat: 28.5034,
    lng: 34.5192,
    tags: ["다이빙", "한달살기", "배낭여행", "홍해"],
    tip: "프리다이빙과 스쿠버다이빙 자격증을 전 세계에서 가장 저렴하게 취득할 수 있는 성지. 라이트하우스 해변 카페에서 노을 감상 필수.",
    description: "배낭여행자들의 블랙홀이라 불리는 이집트 다합에서의 여유로운 일상과 에메랄드빛 홍해 바다 다이빙 라이프.",
    highlights: [
      { time: 60, label: "다합 시내 도착 및 숙소 탐색" },
      { time: 240, label: "라이트하우스 해변 풍경" },
      { time: 510, label: "홍해 바다 스노클링 & 다이빙" }
    ]
  },
  {
    id: "pani-2",
    creator: "빠니보틀",
    youtubeId: "oOEvHsbO02c",
    title: "인도 기차 1등칸 vs 중간칸 vs 꼴등칸 타보기 【유라시아35】",
    channel: "빠니보틀 Pani Bottle",
    country: "인도",
    city: "바라나시",
    locationName: "바라나시 정션 역 & 아시 가트 (Assi Ghat)",
    lat: 25.2891,
    lng: 83.0068,
    tags: ["인도기차", "갠지스강", "생존여행", "로컬"],
    tip: "갠지스강 보트 투어는 아침 일출 때 타야 가장 아름다우며, 가트 주변 릭샤 바가지는 흥정 필수.",
    description: "빠니보틀의 전설적인 인도 기차 탑승기! 갠지스강 가트에서 마주하는 인도의 강렬한 문화와 삶의 모습.",
    highlights: [
      { time: 45, label: "인도 기차 등급별 객차 비교" },
      { time: 320, label: "바라나시 갠지스강 도착" },
      { time: 600, label: "가트 화장터와 힌두 의식" }
    ]
  },
  {
    id: "pani-3",
    creator: "빠니보틀",
    youtubeId: "2e6i0GjS07s",
    title: "인도에서 10,000원으로 하루 보내기, 올드델리 길거리 탐방",
    channel: "빠니보틀 Pani Bottle",
    country: "인도",
    city: "뉴델리",
    locationName: "올드델리 찬드니 초크 (Chandni Chowk)",
    lat: 28.6506,
    lng: 77.2303,
    tags: ["올드델리", "가성비", "스트리트푸드", "시장"],
    tip: "찬드니 초크 시장은 소매치기 주의! 짜이(Chai) 차와 길거리 파라타(Paratha)는 현지 인기 메뉴.",
    description: "만원 한 장으로 뉴델리 구도심에서 삼시세끼 길거리 음식 먹방과 로컬 교통수단 탑승기.",
    highlights: [
      { time: 30, label: "찬드니 초크 골목 진입" },
      { time: 180, label: "100원짜리 짜이 맛보기" },
      { time: 420, label: "자마 마스지드 모스크 조망" }
    ]
  },

  // ================= 곽튜브 (Kwaktube) =================
  {
    id: "kwak-1",
    creator: "곽튜브",
    youtubeId: "8_hpcebDNFw",
    title: "제3의 고향 아제르바이잔 바쿠 올드시티와 대사관 방문기",
    channel: "곽튜브 KWAKTUBE",
    country: "아제르바이잔",
    city: "바쿠",
    locationName: "바쿠 올드시티 (Icherisheher) & 메이든 타워",
    lat: 40.3662,
    lng: 49.8351,
    tags: ["실크로드", "코카서스", "양꼬치", "샤슬릭"],
    tip: "올드시티 메이든 타워 인근 골목의 로컬 샤슬릭(양꼬치) 식당은 가성비 최고. 카스피해 바람이 강하니 겉옷 필수.",
    description: "전 직장이었던 대사관이 있는 바쿠로 3년 만에 금의환향! 고대 성벽 골목길과 최애 로컬 맛집 탐방.",
    highlights: [
      { time: 80, label: "바쿠 시내 전경 및 불꽃 타워" },
      { time: 270, label: "올드시티 성벽 골목길 산책" },
      { time: 540, label: "단골 현지 샤슬릭 먹방" }
    ]
  },
  {
    id: "kwak-2",
    creator: "곽튜브",
    youtubeId: "rSyxycgYqvg",
    title: "내가 우즈베키스탄에 돌아온 이유, 타슈켄트 & 사마르칸트",
    channel: "곽튜브 KWAKTUBE",
    country: "우즈베키스탄",
    city: "사마르칸트",
    locationName: "사마르칸트 레기스탄 광장 (Registan)",
    lat: 39.6548,
    lng: 66.9757,
    tags: ["중앙아시아", "레기스탄", "플로프", "야경"],
    tip: "레기스탄 광장은 낮에도 웅장하지만 밤에 조명이 켜질 때가 절정! 현지 볶음밥인 '오쉬(플로프)'는 점심 시간에 먹어야 가장 신선함.",
    description: "곽튜브의 정체성이 깃든 우즈베키스탄! 실크로드의 찬란한 푸른 모스크 레기스탄과 따뜻한 현지인들과의 재회.",
    highlights: [
      { time: 100, label: "사마르칸트 고속열차 아프라시욥 탑승" },
      { time: 340, label: "레기스탄 웅장한 3대 마드라사" },
      { time: 620, label: "현지인 친구들과 오쉬(플로프) 파티" }
    ]
  },

  // ================= 원지의 하루 (Wonji's Life) =================
  {
    id: "wonji-1",
    creator: "원지의 하루",
    youtubeId: "luQS67K8Sys",
    title: "모든 게 놀라운 몽골 테를지 게르 캠프 & 은하수 대자연",
    channel: "원지의하루 Wonji",
    country: "몽골",
    city: "울란바토르",
    locationName: "테를지 국립공원 게르 캠프 (Gorkhi-Terelj)",
    lat: 47.8864,
    lng: 107.4258,
    tags: ["대자연", "게르", "은하수", "승마체험"],
    tip: "게르는 밤에 기온이 급격히 떨어지므로 난로 장작 관리가 필수. 보조배터리와 침낭을 꼭 챙길 것.",
    description: "지평선 끝까지 펼쳐진 초원과 거북이 바위, 전통 가옥 게르에서 장작 피우며 쏟아지는 밤하늘 별 보기.",
    highlights: [
      { time: 70, label: "테를지 거북이 바위 포토존" },
      { time: 260, label: "게르 숙소 체크인 및 난로 불피우기" },
      { time: 490, label: "몽골 초원 승마 트레킹" }
    ]
  },
  {
    id: "wonji-2",
    creator: "원지의 하루",
    youtubeId: "F28hSaD3LHk",
    title: "치앙마이 님만해민 감성 카페거리 & 조용한 한달살기",
    channel: "원지의하루 Wonji",
    country: "태국",
    city: "치앙마이",
    locationName: "님만해민 원님만 & 카페거리 (One Nimman)",
    lat: 18.7997,
    lng: 98.9681,
    tags: ["한달살기", "카페투어", "원님만", "힐링"],
    tip: "원님만 광장에서 열리는 화이트 마켓은 아기자기한 수공예품 쇼핑에 제격. 그랩(Grab) 대신 볼트(Bolt)가 저렴함.",
    description: "느긋한 힐링 도시 치앙마이! 원지의 최애 베이커리 카페들과 평화로운 골목길 산책 브이로그.",
    highlights: [
      { time: 50, label: "님만해민 감성 카페거리" },
      { time: 220, label: "원님만 수공예 야시장" },
      { time: 410, label: "치앙마이 똠얌 국수 맛집" }
    ]
  },

  // ================= 채코제 (Channel Korean Jay) =================
  {
    id: "chae-1",
    creator: "채코제",
    youtubeId: "F28hSaD3LHk",
    title: "방콕 카오산 로드 밤거리 & 쩟페어 야시장 랭쌥 먹방",
    channel: "채코제 Channel Korean Jay",
    country: "태국",
    city: "방콕",
    locationName: "카오산 로드 (Khaosan Road) & 쩟페어 야시장",
    lat: 13.7589,
    lng: 100.4974,
    tags: ["카오산로드", "랭쌥", "야시장", "배낭여행"],
    tip: "쩟페어 야시장의 고추 듬뿍 등뼈찜 '랭쌥'은 비닐장갑 끼고 뜯어먹는 맛! 카오산 로드는 밤 10시 이후가 피크.",
    description: "세계 배낭여행자들의 심장 카오산 로드의 흥겨운 밤거리와 신상 핫플 쩟페어 야시장 먹방 투어.",
    highlights: [
      { time: 60, label: "카오산로드 맥도날드 싸와디캅 포토존" },
      { time: 280, label: "쩟페어 화산 랭쌥 먹방" },
      { time: 520, label: "람부뜨리 로드 라이브 펍" }
    ]
  },
  {
    id: "chae-2",
    creator: "채코제",
    youtubeId: "F28hSaD3LHk",
    title: "라오스 방비엥 청춘의 블루라군 & 버기카 오프로드 질주",
    channel: "채코제 Channel Korean Jay",
    country: "라오스",
    city: "방비엥",
    locationName: "블루라군 1 & 남송강 (Blue Lagoon Vang Vieng)",
    lat: 18.9189,
    lng: 102.3965,
    tags: ["청춘여행", "블루라군", "버기카", "액티비티"],
    tip: "버기카 대여 시 흙먼지가 심하니 마스크와 고글은 필수 착용! 블루라군 다이빙대는 높이가 있으니 안전 유의.",
    description: "에메랄드빛 천연 수영장 블루라군에서의 아찔한 나무 다이빙과 방비엥 비포장길 버기카 투어.",
    highlights: [
      { time: 40, label: "버기카 렌탈 후 진흙길 질주" },
      { time: 210, label: "블루라군 나무 다이빙" },
      { time: 390, label: "남송강 튜빙 & 야시장 샌드위치" }
    ]
  },

  // ================= 여행가 제이 (Traveler JAY) =================
  {
    id: "jay-1",
    creator: "여행가 제이",
    youtubeId: "X3XftN-Wo3o",
    title: "튀르키예 카파도키아 괴레메 열기구 투어 & 항아리 케밥",
    channel: "여행가 제이 [Traveler JAY]",
    country: "튀르키예",
    city: "카파도키아",
    locationName: "괴레메 선셋 뷰포인트 & 열기구 이륙장",
    lat: 38.6431,
    lng: 34.8289,
    tags: ["열기구", "선셋포인트", "항아리케밥", "인생샷"],
    tip: "열기구는 날씨(바람)의 영향으로 취소될 확률이 높으므로 최소 3일 이상 머무르는 일정을 추천.",
    description: "새벽하늘을 수놓는 수백 개의 열기구 파노라마 장관과 카파도키아 전통 도자기 항아리 케밥 격파기.",
    highlights: [
      { time: 80, label: "새벽 열기구 이륙 장소 이동" },
      { time: 310, label: "카파도키아 하늘 위에서 본 기암괴석" },
      { time: 540, label: "항아리를 깨서 먹는 케밥 시식" }
    ]
  },
  {
    id: "jay-2",
    creator: "여행가 제이",
    youtubeId: "X3XftN-Wo3o",
    title: "모로코 사하라 사막 메르주가 낙타 트레킹 & 베르베르 텐트",
    channel: "여행가 제이 [Traveler JAY]",
    country: "모로코",
    city: "사하라 사막",
    locationName: "메르주가 에르그 셰비 사구 (Erg Chebbi, Merzouga)",
    lat: 31.0802,
    lng: -4.0133,
    tags: ["사하라사막", "낙타투어", "오아시스", "은하수"],
    tip: "사막 모래가 매우 고와서 스마트폰 충전 단자에 모래가 끼기 쉬우니 지퍼백 필수. 밤에는 패딩이 필요할 만큼 춥습니다.",
    description: "황금빛 붉은 모래사구가 끝없이 펼쳐진 메르주가에서 낙타를 타고 사막 깊숙이 들어가 맞이하는 일몰.",
    highlights: [
      { time: 90, label: "낙타 캐러밴 타고 사구 행진" },
      { time: 340, label: "붉은 사하라 사막 일몰 감상" },
      { time: 610, label: "베르베르 텐트 전통 북 연주와 모닥불" }
    ]
  },

  // ================= 잰잰바리 (JanJanBari) =================
  {
    id: "jan-1",
    creator: "잰잰바리",
    youtubeId: "ZBNL99EiFjA",
    title: "우즈베키스탄 타슈켄트 초르수 바자르 현지 시장 털기",
    channel: "잰잰바리",
    country: "우즈베키스탄",
    city: "타슈켄트",
    locationName: "초르수 바자르 (Chorsu Bazaar)",
    lat: 41.3275,
    lng: 69.2356,
    tags: ["초르수시장", "전통빵리뾰시카", "로컬시장", "가성비"],
    tip: "초르수 시장 중앙 돔 1층의 견과류(피스타치오, 아몬드)와 갓 구운 화덕 빵 '리뾰시카'는 필수 구매 품목.",
    description: "우즈벡어 원어민급 구사력으로 현지 상인들과 티키타카를 나누며 로컬 시장의 정을 만끽하는 여행기.",
    highlights: [
      { time: 50, label: "푸른 돔 초르수 바자르 입구" },
      { time: 230, label: "우즈벡 화덕 빵(리뾰시카) 시식" },
      { time: 460, label: "현지인들과의 훈훈한 소통 먹방" }
    ]
  },
  {
    id: "jan-2",
    creator: "잰잰바리",
    youtubeId: "ZBNL99EiFjA",
    title: "코카서스의 심장, 조지아 카즈베기 게르게티 삼위일체 교회",
    channel: "잰잰바리",
    country: "조지아",
    city: "카즈베기",
    locationName: "게르게티 삼위일체 교회 (Gergeti Trinity Church)",
    lat: 42.6625,
    lng: 44.6204,
    tags: ["설산뷰", "코카서스", "트레킹", "인생풍경"],
    tip: "트빌리시에서 디두베 역 마슈롯카(미니버스)를 타고 스테판츠민다로 이동 가능. 카즈베기 만년설 배경 사진은 아침 시간대가 역광 없이 좋습니다.",
    description: "해발 5,000m 카즈벡 산 설산을 뒤로하고 솟아있는 14세기 절벽 교회, 전 세계 여행자들의 버킷리스트.",
    highlights: [
      { time: 70, label: "군용도로 지나 카즈베기 마을 도착" },
      { time: 290, label: "게르게티 교회 앞 압도적인 만년설 뷰" },
      { time: 480, label: "조지아 전통 만두 힌칼리 & 와인 먹방" }
    ]
  }
];
