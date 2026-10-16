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

// Combined travel videos dataset (Modular data: recent + archive)
const INITIAL_TRAVEL_VIDEOS = [
  ...(typeof RECENT_VIDEOS !== 'undefined' ? RECENT_VIDEOS : []),
  ...(typeof ARCHIVE_VIDEOS !== 'undefined' ? ARCHIVE_VIDEOS : [])
];

const STORAGE_KEY = 'tubemap_travel_videos_k_creators_v3';
const DELETED_IDS_KEY = 'tubemap_deleted_video_ids_v1';
let travelVideos = [];
let deletedVideoIds = new Set();

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

  const saved = localStorage.getItem(STORAGE_KEY) || localStorage.getItem('tubemap_travel_videos_k_creators_v2');
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
function getRegionForCountry(country) {
  if (!country) return '기타';
  if (['태국', '라오스', '베트남', '인도네시아'].includes(country)) return '동남아';
  if (['우즈베키스탄', '몽골', '카자흐스탄'].includes(country)) return '중앙아시아';
  if (['아제르바이잔', '조지아', '아르메니아'].includes(country)) return '코카서스';
  if (['이집트', '모로코', '튀르키예', '요르단'].includes(country)) return '중동/아프리카';
  if (['인도', '네팔'].includes(country)) return '남아시아';
  return '기타';
}

// Region Zoom Coordinates
const REGION_COORDINATES = {
  '동남아': { center: [15.8700, 100.9925], zoom: 6 },
  '중앙아시아': { center: [43.0000, 75.0000], zoom: 5 },
  '코카서스': { center: [41.5000, 47.0000], zoom: 6 },
  '중동/아프리카': { center: [30.0000, 20.0000], zoom: 4 },
  '남아시아': { center: [24.0000, 78.0000], zoom: 5 }
};

// Filter Logic
function getFilteredVideos() {
  return travelVideos.filter(item => {
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
}
