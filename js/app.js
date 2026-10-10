/**
 * TubeMap Travel - Application Core Logic (Korean Travel YouTubers Edition)
 */

// State Management
let map = null;
let markerClusterGroup = null;
let currentTab = 'creator'; // 'creator' | 'region'
let currentCreatorFilter = 'all';
let currentRegionFilter = 'all';
let currentSearchQuery = '';
let tableSearchQuery = '';
let isPickingLocation = false;
let markersMap = new Map(); // id -> L.marker
let activeMarkerId = null;

// Table Sort State
let currentSortColumn = 'creator';
let currentSortDirection = 'asc';

// Load Data from LocalStorage or Defaults
const STORAGE_KEY = 'tubemap_travel_videos_k_creators_v3';
let travelVideos = [];

function loadInitialData() {
  const saved = localStorage.getItem(STORAGE_KEY) || localStorage.getItem('tubemap_travel_videos_k_creators_v2');
  if (saved) {
    try {
      const localList = JSON.parse(saved);
      // 사용자 수동 등록 영상(custom-*) 보존
      const userCustomVideos = localList.filter(v => v.id && String(v.id).startsWith('custom-'));
      
      const seenIds = new Set();
      const merged = [];
      
      // 1. 사용자 등록 커스텀 영상 우선 유지
      for (const v of userCustomVideos) {
        const idKey = v.youtubeId || v.id;
        if (!seenIds.has(idKey)) {
          seenIds.add(idKey);
          merged.push(v);
        }
      }
      
      // 2. data.js의 최신 INITIAL_TRAVEL_VIDEOS 전체 병합 (신규 수집 영상 즉시 반영)
      for (const v of INITIAL_TRAVEL_VIDEOS) {
        const idKey = v.youtubeId || v.id;
        if (!seenIds.has(idKey)) {
          seenIds.add(idKey);
          merged.push(v);
        }
      }
      
      travelVideos = merged;
      saveToStorage();
    } catch (e) {
      console.error('Failed to parse localStorage data:', e);
      travelVideos = [...INITIAL_TRAVEL_VIDEOS];
      saveToStorage();
    }
  } else {
    travelVideos = [...INITIAL_TRAVEL_VIDEOS];
    saveToStorage();
  }
}

function saveToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(travelVideos));
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

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  loadInitialData();
  initMap();
  renderCreatorChips();
  initEventListeners();
  initDragToScroll();
  renderFilteredList();
  renderMapMarkers();
});

// Map Initialization
function initMap() {
  map = L.map('map', {
    zoomControl: false
  }).setView([32.0, 60.0], 4); // Eurasia centered view

  // Zoom control at top-right
  L.control.zoom({ position: 'topright' }).addTo(map);

  // Free Tile Layers (No API key needed)
  const esriGray = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    maxNativeZoom: 16,
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ'
  });

  const esriTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ, TomTom, Intermap, iPC, USGS, FAO, NPS, NRCAN, GeoBase, Kadaster NL, Ordnance Survey, Esri Japan, METI, Esri China (Hong Kong), and the GIS User Community'
  });

  const osmLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap contributors'
  });

  // Set default to the cleanest map
  esriGray.addTo(map);

  L.control.layers({
    "심플한 지도 (기본)": esriGray,
    "여행 지도 (지형)": esriTopo,
    "오픈스트리트맵": osmLayer
  }, null, { position: 'topright' }).addTo(map);

  // Marker Cluster Group
  markerClusterGroup = L.markerClusterGroup({
    showCoverageOnHover: false,
    maxClusterRadius: 45,
    spiderfyOnMaxZoom: true
  });
  map.addLayer(markerClusterGroup);

  // Map Click Listener (for Coordinate Picker)
  map.on('click', (e) => {
    if (isPickingLocation) {
      handleLocationPicked(e.latlng.lat, e.latlng.lng);
    }
  });
}

// Create Custom Pin Icon
function createMarkerIcon(isSelected = false) {
  return L.divIcon({
    className: 'custom-pin-container',
    html: `<div class="custom-pin ${isSelected ? 'selected' : ''}"></div>`,
    iconSize: [38, 38],
    iconAnchor: [19, 38],
    popupAnchor: [0, -38]
  });
}

// Render Markers on Map
function renderMapMarkers() {
  markerClusterGroup.clearLayers();
  markersMap.clear();

  const filtered = getFilteredVideos();

  filtered.forEach(video => {
    const marker = L.marker([video.lat, video.lng], {
      icon: createMarkerIcon(video.id === activeMarkerId)
    });

    const popupContent = `
      <div class="popup-card">
        <div class="popup-thumb-wrapper" onclick="openVideoModal('${video.id}')">
          <img class="popup-thumb" src="https://img.youtube.com/vi/${video.youtubeId}/hqdefault.jpg" alt="${video.title}" loading="lazy" />
          <div class="popup-play-btn">▶</div>
        </div>
        <div class="popup-body">
          <div class="popup-creator-tag">👤 ${video.creator || video.channel}</div>
          <div class="popup-location">📍 ${video.country || ''} · ${video.locationName}</div>
          <div class="popup-title">${video.title}</div>
          ${video.tip ? `<div class="popup-tip-text">💡 ${video.tip}</div>` : ''}
          <div class="popup-footer">
            <span class="popup-channel">${video.city || ''}</span>
            <button class="popup-btn-play" onclick="openVideoModal('${video.id}')">영상 보기</button>
          </div>
        </div>
      </div>
    `;

    marker.bindPopup(popupContent, { maxWidth: 280, closeButton: false });

    marker.on('click', () => {
      highlightActiveVideo(video.id, false);
    });

    markerClusterGroup.addLayer(marker);
    markersMap.set(video.id, marker);
  });
}

// Filter Logic
function getFilteredVideos() {
  return travelVideos.filter(item => {
    // Tab filter
    let matchesCategory = true;
    if (currentTab === 'creator') {
      matchesCategory = currentCreatorFilter === 'all' || item.creator === currentCreatorFilter;
    } else {
      if (currentRegionFilter !== 'all') {
        const itemRegion = getRegionForCountry(item.country);
        matchesCategory = itemRegion === currentRegionFilter;
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

// Render Video List in Sidebar
function renderFilteredList() {
  const container = document.getElementById('videoListContainer');
  const countBadge = document.getElementById('videoCountBadge');
  const floatingCount = document.getElementById('floatingCountBadge');
  const filtered = getFilteredVideos();

  countBadge.textContent = `${filtered.length}곳`;
  if (floatingCount) {
    floatingCount.textContent = filtered.length;
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">🧭</div>
        <h4>조건에 맞는 여행 영상이 없습니다</h4>
        <p style="font-size: 0.85rem; margin-top: 6px;">검색어를 바꾸거나 새 영상을 등록해보세요!</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(video => `
    <div class="video-card ${video.id === activeMarkerId ? 'active' : ''}" 
         id="card-${video.id}" 
         onclick="handleCardClick('${video.id}')">
      <div class="video-thumb-wrapper" onclick="event.stopPropagation(); openVideoModal('${video.id}')">
        <img class="video-thumb" src="https://img.youtube.com/vi/${video.youtubeId}/hqdefault.jpg" alt="${video.title}" loading="lazy" />
        <div class="play-badge">▶</div>
      </div>
      <div class="video-card-content">
        <div class="card-top-row">
          <span class="video-creator-pill">👤 ${video.creator || '크리에이터'}</span>
          <span class="video-location-badge">📍 ${video.country || ''} · ${video.city || ''}</span>
        </div>
        <div class="video-card-title">${video.title}</div>
        ${video.tip ? `<div class="card-tip-snippet">💡 ${video.tip}</div>` : ''}
        <div class="video-card-meta">
          <span class="channel-name">${video.locationName}</span>
          <span style="font-size: 0.72rem; color: #64748b;">📅 ${video.publishedAt || '1년 이내'}</span>
        </div>
        ${video.tags && video.tags.length > 0 ? `
          <div class="video-tags">
            ${video.tags.slice(0, 3).map(tag => `<span class="tag-badge">#${tag}</span>`).join('')}
          </div>
        ` : ''}
      </div>
    </div>
  `).join('');
}

// Sidebar Drawer Controls
function openSidebar() {
  const sidebar = document.getElementById('sidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const floatingListBtn = document.getElementById('floatingListBtn');
  if (sidebar) sidebar.classList.add('open');
  if (sidebarBackdrop) sidebarBackdrop.classList.add('active');
  if (floatingListBtn) floatingListBtn.classList.add('hidden');
}

function closeSidebar() {
  const sidebar = document.getElementById('sidebar');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const floatingListBtn = document.getElementById('floatingListBtn');
  if (sidebar) sidebar.classList.remove('open');
  if (sidebarBackdrop) sidebarBackdrop.classList.remove('active');
  if (floatingListBtn) floatingListBtn.classList.remove('hidden');
}

// Video Card Click (Center map & open popup)
function handleCardClick(videoId) {
  highlightActiveVideo(videoId, true);
  if (window.innerWidth <= 768) {
    closeSidebar();
  }
}

function highlightActiveVideo(videoId, panMap = true) {
  activeMarkerId = videoId;
  const video = travelVideos.find(v => v.id === videoId);
  if (!video) return;

  // Highlight card
  document.querySelectorAll('.video-card').forEach(card => card.classList.remove('active'));
  const targetCard = document.getElementById(`card-${videoId}`);
  if (targetCard) {
    targetCard.classList.add('active');
    targetCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // Pan Map
  const marker = markersMap.get(videoId);
  if (marker && panMap) {
    map.flyTo([video.lat, video.lng], Math.max(map.getZoom(), 13), {
      duration: 1.2
    });
    setTimeout(() => {
      marker.openPopup();
    }, 1200);
  }
}

// Open Video Player Modal
function openVideoModal(videoId, startTime = 0) {
  const video = travelVideos.find(v => v.id === videoId);
  if (!video) return;

  const modal = document.getElementById('videoModal');
  const iframe = document.getElementById('videoPlayerFrame');
  const title = document.getElementById('modalVideoTitle');
  const locationTag = document.getElementById('modalLocationTag');
  const creatorBadge = document.getElementById('modalCreatorBadge');
  const tipBox = document.getElementById('modalTipBox');
  const tipContent = document.getElementById('modalTipContent');
  const desc = document.getElementById('modalDescription');
  const googleLink = document.getElementById('googleMapsLink');
  const highlightsContainer = document.getElementById('modalHighlightsContainer');
  const highlightsList = document.getElementById('modalHighlightsList');

  title.textContent = video.title;
  locationTag.textContent = `📍 ${video.country || ''} ${video.city || ''} · ${video.locationName}`;
  creatorBadge.textContent = `👤 ${video.creator || video.channel}`;

  if (video.tip) {
    tipBox.style.display = 'block';
    tipContent.textContent = video.tip;
  } else {
    tipBox.style.display = 'none';
  }

  desc.textContent = video.description || '등록된 상세 설명이 없습니다.';
  googleLink.href = `https://www.google.com/maps/search/?api=1&query=${video.lat},${video.lng}`;

  const embedUrl = `https://www.youtube.com/embed/${video.youtubeId}?autoplay=1&start=${startTime}`;
  iframe.src = embedUrl;

  // Highlights
  if (video.highlights && video.highlights.length > 0) {
    highlightsContainer.style.display = 'block';
    highlightsList.innerHTML = video.highlights.map(h => {
      const minutes = Math.floor(h.time / 60);
      const seconds = String(h.time % 60).padStart(2, '0');
      return `
        <button class="highlight-btn" onclick="jumpToVideoTime('${video.youtubeId}', ${h.time})">
          <span class="highlight-time">${minutes}:${seconds}</span>
          <span>${h.label}</span>
        </button>
      `;
    }).join('');
  } else {
    highlightsContainer.style.display = 'none';
  }

  modal.classList.add('active');
}

function jumpToVideoTime(youtubeId, seconds) {
  const iframe = document.getElementById('videoPlayerFrame');
  iframe.src = `https://www.youtube.com/embed/${youtubeId}?autoplay=1&start=${seconds}`;
}

function closeVideoModal() {
  const modal = document.getElementById('videoModal');
  const iframe = document.getElementById('videoPlayerFrame');
  iframe.src = '';
  modal.classList.remove('active');
}

// ================= Table View Logic =================
function renderTableView() {
  const tableBody = document.getElementById('tableBody');
  const tableCountTag = document.getElementById('tableCountTag');

  let list = [...travelVideos];

  // Search filter inside table
  if (tableSearchQuery.trim()) {
    const q = tableSearchQuery.trim().toLowerCase();
    list = list.filter(item => 
      (item.creator && item.creator.toLowerCase().includes(q)) ||
      (item.country && item.country.toLowerCase().includes(q)) ||
      (item.city && item.city.toLowerCase().includes(q)) ||
      (item.locationName && item.locationName.toLowerCase().includes(q)) ||
      (item.title && item.title.toLowerCase().includes(q)) ||
      (item.tip && item.tip.toLowerCase().includes(q)) ||
      (item.tags && item.tags.some(t => t.toLowerCase().includes(q)))
    );
  }

  // Sorting
  list.sort((a, b) => {
    let valA = a[currentSortColumn] || '';
    let valB = b[currentSortColumn] || '';
    if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
    if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  tableCountTag.textContent = `${list.length}개 스팟`;

  tableBody.innerHTML = list.map(item => `
    <tr>
      <td><span class="creator-tag">${item.creator || '크리에이터'}</span></td>
      <td><strong>${item.country || ''}</strong> / ${item.city || ''}</td>
      <td style="font-weight: 600; color: var(--accent);">${item.locationName}</td>
      <td style="max-width: 240px;">${item.title}</td>
      <td style="font-size: 0.8rem; color: #475569; max-width: 250px;">${item.tip || '-'}</td>
      <td>
        ${(item.tags || []).slice(0, 2).map(t => `<span class="tag-badge">#${t}</span>`).join(' ')}
      </td>
      <td style="font-size: 0.8rem; color: #64748b; white-space: nowrap;">${item.publishedAt || '1년 이내'}</td>
      <td>
        <div class="table-actions">
          <button class="table-btn table-btn-play" onclick="openVideoModal('${item.id}')">▶ 영상</button>
          <button class="table-btn table-btn-map" onclick="jumpToSpotOnMap('${item.id}')">📍 지도</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function jumpToSpotOnMap(videoId) {
  document.getElementById('tableModal').classList.remove('active');
  highlightActiveVideo(videoId, true);
}

// Export CSV Function (Excel UTF-8 BOM support)
function exportToCsv() {
  const headers = ["유튜버", "국가", "도시", "장소명", "영상제목", "유튜브ID", "위도", "경도", "업로드일", "추천팁", "태그"];
  const rows = travelVideos.map(v => [
    `"${(v.creator || '').replace(/"/g, '""')}"`,
    `"${(v.country || '').replace(/"/g, '""')}"`,
    `"${(v.city || '').replace(/"/g, '""')}"`,
    `"${(v.locationName || '').replace(/"/g, '""')}"`,
    `"${(v.title || '').replace(/"/g, '""')}"`,
    `"${v.youtubeId || ''}"`,
    v.lat,
    v.lng,
    `"${v.publishedAt || '1년 이내'}"`,
    `"${(v.tip || '').replace(/"/g, '""')}"`,
    `"${(v.tags || []).join(', ')}"`
  ]);

  const csvContent = "\uFEFF" + [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement("a");
  const url = URL.createObjectURL(blob);
  link.setAttribute("href", url);
  link.setAttribute("download", `k_travel_youtuber_spots_${new Date().toISOString().slice(0,10)}.csv`);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast('여행지 테이블이 CSV 파일로 다운로드되었습니다!', '📥');
}

// Toast Notification
function showToast(message, icon = '✅') {
  const toast = document.getElementById('toast');
  const msgEl = document.getElementById('toastMessage');
  const iconEl = document.getElementById('toastIcon');

  msgEl.textContent = message;
  iconEl.textContent = icon;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}

// Dynamic Creator Chips Renderer
function renderCreatorChips() {
  const container = document.getElementById('creatorChipsContainer');
  if (!container) return;

  const creators = Array.from(new Set(travelVideos.map(v => v.creator).filter(Boolean)));
  
  container.innerHTML = `
    <button class="chip ${currentCreatorFilter === 'all' ? 'active' : ''}" data-creator="all">전체 유튜버</button>
    ${creators.map(c => `
      <button class="chip ${currentCreatorFilter === c ? 'active' : ''}" data-creator="${c}">${c}</button>
    `).join('')}
  `;

  // Attach click listener to newly rendered chips
  container.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      container.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentCreatorFilter = chip.getAttribute('data-creator');
      renderFilteredList();
      renderMapMarkers();

      const creatorVideos = travelVideos.filter(v => currentCreatorFilter === 'all' || v.creator === currentCreatorFilter);
      if (creatorVideos.length > 0) {
        const bounds = L.latLngBounds(creatorVideos.map(v => [v.lat, v.lng]));
        map.fitBounds(bounds, { padding: [60, 60], maxZoom: 10, animate: true });
      }
    });
  });
}

// Event Listeners
function initEventListeners() {
  // Search Inputs (Desktop header & Sidebar sync)
  const searchInput = document.getElementById('searchInput');
  const sidebarSearchInput = document.getElementById('sidebarSearchInput');

  function handleSearch(val) {
    currentSearchQuery = val;
    if (searchInput && searchInput.value !== val) searchInput.value = val;
    if (sidebarSearchInput && sidebarSearchInput.value !== val) sidebarSearchInput.value = val;
    renderFilteredList();
    renderMapMarkers();
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => handleSearch(e.target.value));
  }
  if (sidebarSearchInput) {
    sidebarSearchInput.addEventListener('input', (e) => handleSearch(e.target.value));
  }

  // Filter Tabs (유튜버별 vs 국가/지역별)
  const tabCreatorBtn = document.getElementById('tabCreatorBtn');
  const tabRegionBtn = document.getElementById('tabRegionBtn');
  const creatorChipsContainer = document.getElementById('creatorChipsContainer');
  const regionChipsContainer = document.getElementById('regionChipsContainer');

  tabCreatorBtn.addEventListener('click', () => {
    tabCreatorBtn.classList.add('active');
    tabRegionBtn.classList.remove('active');
    creatorChipsContainer.classList.remove('hidden');
    regionChipsContainer.classList.add('hidden');
    currentTab = 'creator';
    renderFilteredList();
    renderMapMarkers();
  });

  tabRegionBtn.addEventListener('click', () => {
    tabRegionBtn.classList.add('active');
    tabCreatorBtn.classList.remove('active');
    regionChipsContainer.classList.remove('hidden');
    creatorChipsContainer.classList.add('hidden');
    currentTab = 'region';
    renderFilteredList();
    renderMapMarkers();
  });

  // Region Chips
  const regionChips = document.querySelectorAll('#regionChipsContainer .chip');
  regionChips.forEach(chip => {
    chip.addEventListener('click', () => {
      regionChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentRegionFilter = chip.getAttribute('data-region');
      renderFilteredList();
      renderMapMarkers();

      if (REGION_COORDINATES[currentRegionFilter]) {
        const coord = REGION_COORDINATES[currentRegionFilter];
        map.flyTo(coord.center, coord.zoom, { duration: 1.5 });
      } else if (currentRegionFilter === 'all') {
        map.flyTo([32.0, 60.0], 4, { duration: 1.5 });
      }
    });
  });

  // Brand click -> reset
  document.getElementById('brandBtn').addEventListener('click', () => {
    if (searchInput) searchInput.value = '';
    if (sidebarSearchInput) sidebarSearchInput.value = '';
    currentSearchQuery = '';
    tabCreatorBtn.click();
    const allChip = document.querySelector('#creatorChipsContainer .chip[data-creator="all"]');
    if (allChip) allChip.click();
  });

  // Mobile Menu & Drawer Controls
  const mobileToggle = document.getElementById('mobileMenuToggle');
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const floatingListBtn = document.getElementById('floatingListBtn');
  const sidebar = document.getElementById('sidebar');

  if (mobileToggle) {
    mobileToggle.addEventListener('click', () => {
      if (sidebar && sidebar.classList.contains('open')) {
        closeSidebar();
      } else {
        openSidebar();
      }
    });
  }

  if (floatingListBtn) {
    floatingListBtn.addEventListener('click', openSidebar);
  }

  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener('click', closeSidebar);
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', closeSidebar);
  }

  // Video Modal Close
  document.getElementById('closeVideoModalBtn').addEventListener('click', closeVideoModal);
  document.getElementById('modalDoneBtn').addEventListener('click', closeVideoModal);
  document.getElementById('videoModal').addEventListener('click', (e) => {
    if (e.target.id === 'videoModal') closeVideoModal();
  });

  // Table Modal
  const tableModal = document.getElementById('tableModal');
  const openTableModalBtn = document.getElementById('openTableModalBtn');
  const closeTableModalBtn = document.getElementById('closeTableModalBtn');
  const closeTableModalBottomBtn = document.getElementById('closeTableModalBottomBtn');
  const tableSearchInput = document.getElementById('tableSearchInput');

  openTableModalBtn.addEventListener('click', () => {
    renderTableView();
    tableModal.classList.add('active');
  });

  const closeTableModal = () => {
    tableModal.classList.remove('active');
  };

  closeTableModalBtn.addEventListener('click', closeTableModal);
  closeTableModalBottomBtn.addEventListener('click', closeTableModal);
  tableModal.addEventListener('click', (e) => {
    if (e.target.id === 'tableModal') closeTableModal();
  });

  tableSearchInput.addEventListener('input', (e) => {
    tableSearchQuery = e.target.value;
    renderTableView();
  });

  // Table Header Sort Click
  document.querySelectorAll('#travelDataTable th[data-sort]').forEach(th => {
    th.addEventListener('click', () => {
      const col = th.getAttribute('data-sort');
      if (currentSortColumn === col) {
        currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
      } else {
        currentSortColumn = col;
        currentSortDirection = 'asc';
      }
      renderTableView();
    });
  });

  // CSV Download
  document.getElementById('downloadCsvBtn').addEventListener('click', exportToCsv);

  // Add Video Modal
  const addModal = document.getElementById('addVideoModal');
  const openAddBtn = document.getElementById('openAddModalBtn');
  const closeAddBtn = document.getElementById('closeAddModalBtn');
  const cancelAddBtn = document.getElementById('cancelAddBtn');

  openAddBtn.addEventListener('click', () => {
    addModal.classList.add('active');
  });

  const closeAddModal = () => {
    addModal.classList.remove('active');
  };

  closeAddBtn.addEventListener('click', closeAddModal);
  cancelAddBtn.addEventListener('click', closeAddModal);
  addModal.addEventListener('click', (e) => {
    if (e.target.id === 'addVideoModal') closeAddModal();
  });

  // URL input preview
  const urlInput = document.getElementById('inputYoutubeUrl');
  const thumbPreviewBox = document.getElementById('thumbnailPreviewBox');

  urlInput.addEventListener('input', () => {
    const id = extractYoutubeId(urlInput.value);
    if (id) {
      thumbPreviewBox.innerHTML = `
        <img src="https://img.youtube.com/vi/${id}/hqdefault.jpg" alt="미리보기" />
      `;
    } else {
      thumbPreviewBox.innerHTML = `<span>URL을 입력하면 썸네일 미리보기가 표시됩니다</span>`;
    }
  });

  // Coordinate Picker on Map
  const pickBtn = document.getElementById('pickOnMapBtn');
  const pickerBanner = document.getElementById('pickerBanner');
  const cancelPickBtn = document.getElementById('cancelPickBtn');

  pickBtn.addEventListener('click', () => {
    addModal.classList.remove('active');
    isPickingLocation = true;
    pickerBanner.classList.remove('hidden');
    document.getElementById('map').style.cursor = 'crosshair';
  });

  cancelPickBtn.addEventListener('click', () => {
    isPickingLocation = false;
    pickerBanner.classList.add('hidden');
    document.getElementById('map').style.cursor = '';
    addModal.classList.add('active');
  });

  // Add Video Form Submit
  const addForm = document.getElementById('addVideoForm');
  addForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const rawUrl = urlInput.value.trim();
    const ytId = extractYoutubeId(rawUrl);

    if (!ytId) {
      alert('올바른 유튜브 URL 또는 영상 ID를 입력해주세요.');
      return;
    }

    const title = document.getElementById('inputTitle').value.trim();
    const creator = document.getElementById('inputCreator').value.trim();
    const countryCity = document.getElementById('inputCountry').value.trim();
    const locationName = document.getElementById('inputLocationName').value.trim();
    const lat = parseFloat(document.getElementById('inputLat').value);
    const lng = parseFloat(document.getElementById('inputLng').value);
    const tip = document.getElementById('inputTip').value.trim();
    const rawTags = document.getElementById('inputTags').value.trim();

    if (isNaN(lat) || isNaN(lng)) {
      alert('올바른 위도와 경도 좌표를 입력해주세요.');
      return;
    }

    const tags = rawTags ? rawTags.split(',').map(t => t.trim()).filter(Boolean) : [];
    const parts = countryCity.split(' ');
    const country = parts[0] || '기타';
    const city = parts.slice(1).join(' ') || country;

    const newVideo = {
      id: `custom-${Date.now()}`,
      creator: creator || '추천 크리에이터',
      youtubeId: ytId,
      title,
      channel: creator,
      country,
      city,
      locationName,
      lat,
      lng,
      tip,
      tags,
      description: tip || '사용자가 직접 등록한 추천 여행지입니다.',
      highlights: []
    };

    travelVideos.unshift(newVideo);
    saveToStorage();

    addForm.reset();
    thumbPreviewBox.innerHTML = `<span>URL을 입력하면 썸네일 미리보기가 표시됩니다</span>`;
    closeAddModal();

    renderFilteredList();
    renderMapMarkers();
    showToast(`[${creator}] '${locationName}' 여행지가 등록되었습니다!`, '🎉');

    map.flyTo([lat, lng], 13, { duration: 1.5 });
  });

  // Export / Backup JSON
  document.getElementById('exportBtn').addEventListener('click', () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(travelVideos, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `k_creator_travel_backup_${new Date().toISOString().slice(0,10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast('데이터가 JSON으로 백업되었습니다.', '💾');
  });

  // Re-sync / Refresh Data to Latest
  const refreshBtn = document.getElementById('refreshDataBtn');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem('tubemap_travel_videos_k_creators_v2');
      loadInitialData();
      renderFilteredList();
      renderMapMarkers();
      renderCreatorChips();
      if (typeof renderTableRows === 'function') {
        renderTableRows();
      }
      showToast(`총 ${travelVideos.length}곳의 최신 여행지로 동기화되었습니다!`, '🔄');
    });
  }

  // Keydown Escape
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeVideoModal();
      closeAddModal();
      closeTableModal();
      if (isPickingLocation) {
        cancelPickBtn.click();
      }
    }
  });
}

function handleLocationPicked(lat, lng) {
  isPickingLocation = false;
  document.getElementById('pickerBanner').classList.add('hidden');
  document.getElementById('map').style.cursor = '';

  document.getElementById('inputLat').value = lat.toFixed(6);
  document.getElementById('inputLng').value = lng.toFixed(6);

  document.getElementById('addVideoModal').classList.add('active');
  showToast(`좌표가 선택되었습니다: (${lat.toFixed(4)}, ${lng.toFixed(4)})`, '📍');
}

// Drag to scroll for filter chips
function initDragToScroll() {
  const containers = document.querySelectorAll('.filter-chips');
  containers.forEach(container => {
    let isDown = false;
    let startX;
    let scrollLeft;
    let dragged = false;

    const onMouseMove = (e) => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX;
      const walk = (x - startX) * 1.5;
      if (Math.abs(walk) > 5) dragged = true;
      container.scrollLeft = scrollLeft - walk;
    };

    const onMouseUp = () => {
      isDown = false;
      container.classList.remove('active');
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    container.addEventListener('mousedown', (e) => {
      isDown = true;
      dragged = false;
      container.classList.add('active');
      startX = e.pageX;
      scrollLeft = container.scrollLeft;
      
      window.addEventListener('mousemove', onMouseMove, { passive: false });
      window.addEventListener('mouseup', onMouseUp);
    });

    container.addEventListener('dragstart', (e) => {
      e.preventDefault(); // Stop ghost drag
    });

    // Handle touch/click edge cases for dragging
    container.addEventListener('click', (e) => {
      if (dragged) {
        e.preventDefault();
        e.stopPropagation();
      }
      // reset for next click
      setTimeout(() => { dragged = false; }, 50);
    }, true);
  });
}
