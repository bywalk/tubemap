/**
 * TubeMap Travel - State & Storage Management
 */

// State Management
let map = null;
let markerClusterGroup = null;
let currentTab = 'creator'; // 'creator' | 'region' | 'mymap'
let currentCreatorFilter = 'all';
let currentRegionFilter = 'all';
let currentMyMapFilter = 'all'; // 'all' | 'bookmarked' | 'custom' | 'edited'
let currentSearchQuery = '';
let isPickingLocation = false;
let editingVideoId = null;
let currentModalVideoId = null;
let markersMap = new Map(); // id -> L.marker
let activeMarkerId = null;
let currentPage = 1;
const ITEMS_PER_PAGE = 20; // 사이드바 페이지당 비디오 카드 수

// Utility: Format seconds to MM:SS
function formatTime(seconds) {
  if (!seconds || seconds <= 0) return '';
  const m = Math.floor(seconds / 60);
  const s = String(seconds % 60).padStart(2, '0');
  return `${m}:${s}`;
}

// Combined travel videos dataset (Modular data: recent + archive)
const INITIAL_TRAVEL_VIDEOS = [
  ...(typeof RECENT_VIDEOS !== 'undefined' ? RECENT_VIDEOS : []),
  ...(typeof ARCHIVE_VIDEOS !== 'undefined' ? ARCHIVE_VIDEOS : [])
];

const STORAGE_KEY = 'tubemap_travel_videos_k_creators_v5';
const DELETED_IDS_KEY = 'tubemap_deleted_video_ids_v1';
const THEME_KEY = 'tubemap_theme';
let travelVideos = [];
let deletedVideoIds = new Set();
let currentTheme = 'light';

function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === 'dark' || saved === 'light') {
    currentTheme = saved;
  } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    currentTheme = 'dark';
  } else {
    currentTheme = 'light';
  }
  applyTheme(currentTheme, false);
}

function applyTheme(theme, save = true) {
  currentTheme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('themeToggleIcon');
  if (icon) {
    icon.textContent = theme === 'dark' ? 'light_mode' : 'dark_mode';
  }
  if (save) {
    localStorage.setItem(THEME_KEY, theme);
  }
  if (typeof setMapTheme === 'function') {
    setMapTheme(theme === 'dark');
  }
}

function toggleTheme() {
  const nextTheme = currentTheme === 'dark' ? 'light' : 'dark';
  applyTheme(nextTheme, true);
  if (typeof showToast === 'function') {
    showToast(nextTheme === 'dark' ? '다크 모드가 적용되었습니다.' : '라이트 모드가 적용되었습니다.', nextTheme === 'dark' ? 'dark_mode' : 'light_mode');
  }
}

function isCustomVideo(v) {
  return Boolean(v && v.id && String(v.id).startsWith('custom-'));
}

function isMyMapVideo(v) {
  return Boolean(v && (v.bookmarked || v.isEdited || isCustomVideo(v)));
}

function updateMyMapCountBadge() {
  const badge = document.getElementById('myMapTabCount');
  if (badge) {
    badge.textContent = travelVideos.filter(isMyMapVideo).length;
  }
}

function loadInitialData() {
  try {
    const savedDeleted = localStorage.getItem(DELETED_IDS_KEY);
    deletedVideoIds = savedDeleted ? new Set(JSON.parse(savedDeleted)) : new Set();
  } catch (e) {
    deletedVideoIds = new Set();
  }

  const saved = localStorage.getItem(STORAGE_KEY) || localStorage.getItem('tubemap_travel_videos_k_creators_v4') || localStorage.getItem('tubemap_travel_videos_k_creators_v3');
  if (saved) {
    try {
      const localList = JSON.parse(saved);
      const userCustomVideos = localList.filter(v => isCustomVideo(v) && !deletedVideoIds.has(v.id));
      const localById = new Map();
      for (const v of localList) {
        if (v.id) localById.set(v.id, v);
        if (v.youtubeId) localById.set(v.youtubeId, v);
      }

      const seenIds = new Set();
      const merged = [];

      // 1. 사용자 등록 커스텀 영상 우선 유지
      for (const v of userCustomVideos) {
        const idKey = v.id;
        if (!seenIds.has(idKey)) {
          seenIds.add(idKey);
          merged.push(v);
        }
      }

      // 2. 기본 데이터 병합 (사용자가 찜했거나 위치/정보를 수정한 내역 보존, 삭제한 항목 제외)
      for (const baseVideo of INITIAL_TRAVEL_VIDEOS) {
        const idKey = baseVideo.youtubeId || baseVideo.id;
        if (deletedVideoIds.has(baseVideo.id) || deletedVideoIds.has(baseVideo.youtubeId)) {
          continue;
        }
        if (!seenIds.has(idKey)) {
          seenIds.add(idKey);
          const savedItem = localById.get(baseVideo.id) || localById.get(baseVideo.youtubeId);
          if (savedItem && (savedItem.isEdited || savedItem.bookmarked)) {
            merged.push({
              ...baseVideo,
              ...(savedItem.isEdited ? savedItem : {}),
              bookmarked: Boolean(savedItem.bookmarked),
              isEdited: Boolean(savedItem.isEdited)
            });
          } else {
            merged.push({ ...baseVideo });
          }
        }
      }

      travelVideos = merged;
      saveToStorage();
    } catch (e) {
      console.error('Failed to parse localStorage data:', e);
      travelVideos = INITIAL_TRAVEL_VIDEOS.map(v => ({ ...v }));
      saveToStorage();
    }
  } else {
    travelVideos = INITIAL_TRAVEL_VIDEOS.map(v => ({ ...v }));
    saveToStorage();
  }
  updateMyMapCountBadge();
}

function saveToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(travelVideos));
  localStorage.setItem(DELETED_IDS_KEY, JSON.stringify(Array.from(deletedVideoIds)));
  updateMyMapCountBadge();
}

function toggleBookmark(videoId, event) {
  if (event) {
    event.stopPropagation();
  }
  const video = travelVideos.find(v => v.id === videoId);
  if (!video) return;

  video.bookmarked = !video.bookmarked;
  saveToStorage();
  renderFilteredList();
  renderMapMarkers();

  // Update Video Modal Bookmark button if open
  if (currentModalVideoId === videoId) {
    updateModalBookmarkBtn(video);
  }

  if (video.bookmarked) {
    showToast(`'${video.locationName}' 스팟을 나만의 맵에 찜했습니다!`, 'star');
  } else {
    showToast(`'${video.locationName}' 찜을 해제했습니다.`, 'bookmark_remove');
  }

  if (window.umami) {
    window.umami.track(video.bookmarked ? 'bookmark-add' : 'bookmark-remove', {
      creator: video.creator,
      spot: video.locationName,
      country: video.country || ''
    });
  }
}

// YouTube URL parser
function extractYoutubeId(urlOrId) {
  if (!urlOrId) return null;
  const str = urlOrId.trim();
  if (/^[a-zA-Z0-9_-]{11}$/.test(str)) {
    return str;
  }
  const regExp = /(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=|shorts\/))([a-zA-Z0-9_-]{11})/;
  const match = str.match(regExp);
  return match ? match[1] : null;
}

// Region categorization helper
const REGION_MAP = {
  '동아시아': ['일본', '대만', '홍콩', '대한민국', '한국', '몽골', '중국', '마카오'],
  '동남아': ['태국', '인도네시아', '베트남', '필리핀', '라오스', '말레이시아', '싱가포르', '캄보디아'],
  '유럽': ['프랑스', '스페인', '스위스', '튀르키예', '이탈리아', '영국', '체코', '헝가리', '오스트리아', '포르투갈', '아일랜드', '핀란드', '네덜란드', '독일', '덴마크', '폴란드', '크로아티아', '노르웨이', '스웨덴', '아이슬란드', '그리스', '벨기에', '리히텐슈타인', '룩셈부르크'],
  '아메리카': ['미국', '캐나다', '칠레', '아르헨티나', '멕시코', '페루', '콜롬비아', '볼리비아', '브라질'],
  '오세아니아': ['호주', '뉴질랜드', '괌'],
  '중동/아프리카': ['이집트', '아랍에미리트', '모로코', '에티오피아', '카보베르데', '남아프리카공화국', '요르단', '사우디아라비아'],
  '중앙/남아시아': ['인도', '방글라데시', '키르기스스탄', '네팔', '우즈베키스탄', '카자흐스탄', '조지아', '아제르바이잔', '아르메니아']
};

function getRegionForCountry(country) {
  if (!country) return '기타';
  for (const [region, countries] of Object.entries(REGION_MAP)) {
    if (countries.includes(country)) return region;
  }
  return '기타';
}

// Region Zoom Coordinates (6 Continents & Key Hubs)
const REGION_COORDINATES = {
  '동아시아': { center: [34.0, 131.0], zoom: 5 },
  '동남아': { center: [13.5, 105.0], zoom: 5 },
  '유럽': { center: [48.0, 12.0], zoom: 4 },
  '아메리카': { center: [20.0, -85.0], zoom: 3 },
  '오세아니아': { center: [-25.0, 135.0], zoom: 4 },
  '중동/아프리카': { center: [20.0, 30.0], zoom: 4 },
  '중앙/남아시아': { center: [28.0, 77.0], zoom: 4 }
};

// Date Sort State ('desc': 최신순, 'asc': 오래된순)
let currentDateSortOrder = 'desc';

function toggleDateSortOrder() {
  currentDateSortOrder = currentDateSortOrder === 'desc' ? 'asc' : 'desc';
  return currentDateSortOrder;
}

// Filter Logic
function getFilteredVideos() {
  const filtered = travelVideos.filter(item => {
    // Tab filter
    let matchesCategory = true;
    if (currentTab === 'creator') {
      matchesCategory = currentCreatorFilter === 'all' || item.creator === currentCreatorFilter;
    } else if (currentTab === 'region') {
      if (currentRegionFilter !== 'all') {
        const itemRegion = getRegionForCountry(item.country);
        matchesCategory = itemRegion === currentRegionFilter;
      }
    } else if (currentTab === 'mymap') {
      if (currentMyMapFilter === 'bookmarked') {
        matchesCategory = Boolean(item.bookmarked);
      } else if (currentMyMapFilter === 'custom') {
        matchesCategory = isCustomVideo(item);
      } else if (currentMyMapFilter === 'edited') {
        matchesCategory = Boolean(item.isEdited);
      } else {
        matchesCategory = isMyMapVideo(item);
      }
    }

    // Search query filter
    const q = currentSearchQuery.trim().toLowerCase();
    if (!q) return matchesCategory;

    const matchesQuery = 
      (item.title && item.title.toLowerCase().includes(q)) ||
      (item.creator && item.creator.toLowerCase().includes(q)) ||
      (item.country && item.country.toLowerCase().includes(q)) ||
      (item.city && item.city.toLowerCase().includes(q)) ||
      (item.locationName && item.locationName.toLowerCase().includes(q)) ||
      (item.tip && item.tip.toLowerCase().includes(q)) ||
      (item.tags && item.tags.some(t => t.toLowerCase().includes(q)));

    return matchesCategory && matchesQuery;
  });

  // 날짜 기준 정렬 (기본: 최신 발행일순 내림차순, 토글 시 오래된순 오름차순)
  return filtered.sort((a, b) => {
    const dateA = a.publishedAt || '';
    const dateB = b.publishedAt || '';
    if (dateA !== dateB) {
      if (!dateA) return 1;
      if (!dateB) return -1;
      return currentDateSortOrder === 'asc'
        ? dateA.localeCompare(dateB)
        : dateB.localeCompare(dateA);
    }
    // 동일 날짜 & 동일 영상 내 스팟일 경우 타임라인(startTime) 순서대로 정렬
    if (a.youtubeId === b.youtubeId && (a.startTime !== undefined || b.startTime !== undefined)) {
      return (a.startTime || 0) - (b.startTime || 0);
    }
    return (a.title || '').localeCompare(b.title || '');
  });
}
