/**
 * TubeMap Travel - Leaflet Map & Marker Management
 */

// Map Initialization
function initMap() {
  map = L.map('map', {
    zoomControl: false,
    worldCopyJump: true, // Fixes pins not showing when panning across the world
    minZoom: 2,          // Prevents zooming out too far to see multiple empty worlds
    maxZoom: 15          // Prevents over-zooming and missing tile placeholders
  }).setView([32.0, 60.0], 4); // Eurasia centered view

  // Remove 'Leaflet' prefix while keeping required tile provider attribution
  map.attributionControl.setPrefix(false);

  // Zoom control at top-right
  L.control.zoom({ position: 'topright' }).addTo(map);

  // Free Tile Layers (No API key needed, no watermarks)
  // Note: Esri canvas/topo tiles only provide native data up to zoom 13 in Korea and many global regions.
  // Setting maxNativeZoom: 13 scales zoom 13 tiles for zoom 14-15, eliminating 'Map data not yet available' placeholders.
  const esriDark = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 15,
    maxNativeZoom: 13,
    attribution: 'Tiles &copy; Esri'
  });

  const esriGray = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 15,
    maxNativeZoom: 13,
    attribution: 'Tiles &copy; Esri'
  });

  const esriTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 15,
    maxNativeZoom: 13,
    attribution: 'Tiles &copy; Esri'
  });

  const osmLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 15,
    maxNativeZoom: 15,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'
  });

  window.baseLayers = { esriGray, esriDark, esriTopo, osmLayer };

  // Set default tile according to currentTheme
  if (typeof currentTheme !== 'undefined' && currentTheme === 'dark') {
    esriDark.addTo(map);
  } else {
    esriGray.addTo(map);
  }

  L.control.layers({
    "심플한 지도 (기본)": esriGray,
    "다크 지도 (Dark)": esriDark,
    "여행 지도 (지형)": esriTopo,
    "오픈스트리트맵": osmLayer
  }, null, { position: 'topright' }).addTo(map);

  // Marker Cluster Group with Controlled Zooming
  markerClusterGroup = L.markerClusterGroup({
    showCoverageOnHover: false,
    maxClusterRadius: 45,
    zoomToBoundsOnClick: false, // 과도한 줌인 방지를 위해 커스텀 핸들러 사용
    spiderfyOnMaxZoom: true,
    spiderfyDistanceMultiplier: 1.6
  });

  // 숫자(클러스터) 클릭 시: 현재 보고 있는 지도의 크기(viewport)와 클러스터의 실제 범위를 계산하여 동작
  // 1) 같은 도시/지역에 모여 있는 마커들은 여러 번 클릭할 필요 없이 '단 1번의 클릭'으로 즉시 원형 펼침(spiderfy)되어 영상 선택 가능
  // 2) 건물 옥상 수준으로 과도하게 줌인되는 현상 방지 (최대 줌 11로 도시 전체 조망 유지)
  // 3) 대륙/전 세계 단위의 광역 뷰에서는 +2씩 찔끔찔끔 확대하지 않고 한 번에 해당 지역 뷰로 이동
  markerClusterGroup.on('clusterclick', function (a) {
    const mapBounds = map.getBounds();
    const mapDiagonalKm = mapBounds.getNorthEast().distanceTo(mapBounds.getSouthWest()) / 1000;

    const clusterBounds = a.layer.getBounds();
    const clusterSpreadKm = clusterBounds.getNorthEast().distanceTo(clusterBounds.getSouthWest()) / 1000;
    const currentZoom = map.getZoom();
    const MAX_CLUSTER_ZOOM = 11;

    // 영상들이 동일 위치이거나 같은 도시/생활권 범위(< 100km)에 있거나,
    // 이미 지도가 특정 국가/지역 규모(< 800km 또는 zoom >= 8)를 보고 있는 경우:
    // -> 1번의 클릭으로 즉시 핀들을 원형으로 펼쳐(spiderfy) 영상을 바로 선택할 수 있게 함
    if (clusterSpreadKm < 100 || mapDiagonalKm < 800 || currentZoom >= 8) {
      a.layer.spiderfy();
      return;
    }

    // 전 세계/대륙 레벨에서 수백 km 이상 떨어진 여러 지역이 묶여 있는 경우:
    // -> 여러 번 누를 필요 없이 클러스터의 실제 크기에 맞춰 최대 zoom 11 한도로 '한 번에' 쾌적하게 이동
    const targetZoom = Math.min(map.getBoundsZoom(clusterBounds), MAX_CLUSTER_ZOOM);
    if (targetZoom > currentZoom + 1) {
      map.flyToBounds(clusterBounds, {
        maxZoom: MAX_CLUSTER_ZOOM,
        padding: [50, 50],
        duration: 0.5
      });
    } else {
      a.layer.spiderfy();
    }
  });

  map.addLayer(markerClusterGroup);

  // Map Click Listener (for Coordinate Picker)
  map.on('click', (e) => {
    if (isPickingLocation) {
      handleLocationPicked(e.latlng.lat, e.latlng.lng);
    }
  });
}

// Switch map base tile layer according to dark/light theme
function setMapTheme(isDark) {
  if (!map || !window.baseLayers || !window.baseLayers.esriGray || !window.baseLayers.esriDark) return;
  const { esriGray, esriDark } = window.baseLayers;
  if (isDark) {
    if (map.hasLayer(esriGray)) {
      map.removeLayer(esriGray);
      esriDark.addTo(map);
    }
  } else {
    if (map.hasLayer(esriDark)) {
      map.removeLayer(esriDark);
      esriGray.addTo(map);
    }
  }
}

// Create Custom Pin Icon
function createMarkerIcon(isSelected = false, isBookmarkedOrCustom = false) {
  const classes = ['custom-pin'];
  if (isSelected) classes.push('selected');
  else if (isBookmarkedOrCustom) classes.push('bookmarked');
  return L.divIcon({
    className: 'custom-pin-container',
    html: `<div class="${classes.join(' ')}"></div>`,
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
      icon: createMarkerIcon(video.id === activeMarkerId, video.bookmarked || isCustomVideo(video))
    });

    const popupContent = `
      <div class="popup-card">
        <div class="popup-thumb-wrapper" onclick="openVideoModal('${video.id}', ${video.startTime || 0})">
          <img class="popup-thumb" src="https://img.youtube.com/vi/${video.youtubeId}/hqdefault.jpg" alt="${video.title}" loading="lazy" />
          <div class="popup-play-btn"><span class="material-symbols-rounded filled">play_arrow</span></div>
          ${video.startTime ? `<span class="thumb-time-badge">${formatTime(video.startTime)}</span>` : ''}
        </div>
        <div class="popup-body">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 2px;">
            <div class="popup-creator-tag" style="margin-bottom: 0; display: inline-flex; align-items: center; gap: 3px;"><span class="material-symbols-rounded icon-xs">person</span> ${video.creator || video.channel}</div>
            <div class="card-action-btns">
              <button class="card-icon-btn ${video.bookmarked ? 'bookmarked' : ''}" onclick="toggleBookmark('${video.id}', event)" title="나만의 맵에 찜하기">
                <span class="material-symbols-rounded icon-xs ${video.bookmarked ? 'filled' : ''}">star</span> ${video.bookmarked ? '찜됨' : '찜'}
              </button>
              <button class="card-icon-btn" onclick="openEditVideoModal('${video.id}', event)" title="위치 및 정보 편집">
                <span class="material-symbols-rounded icon-xs">edit</span> 편집
              </button>
            </div>
          </div>
          <div class="popup-location" style="display: flex; align-items: center; gap: 2px;"><span class="material-symbols-rounded icon-xs filled">location_on</span> ${video.country || ''} · ${video.locationName}</div>
          <div class="popup-title">${video.title}</div>
          ${video.tip ? `<div class="popup-tip-text"><span class="material-symbols-rounded icon-xs" style="vertical-align: -2px;">lightbulb</span> ${video.tip}</div>` : ''}
          <div class="popup-footer">
            <span class="popup-channel">${video.city || ''}</span>
            <button class="popup-btn-play" onclick="openVideoModal('${video.id}', ${video.startTime || 0})">영상 보기</button>
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

function highlightActiveVideo(videoId, panMap = true) {
  activeMarkerId = videoId;
  const video = travelVideos.find(v => v.id === videoId);
  if (!video) return;

  // Auto-switch to the page containing this video card
  if (typeof getFilteredVideos === 'function' && typeof ITEMS_PER_PAGE !== 'undefined') {
    const filtered = getFilteredVideos();
    const videoIndex = filtered.findIndex(v => v.id === videoId);
    if (videoIndex !== -1) {
      const targetPage = Math.floor(videoIndex / ITEMS_PER_PAGE) + 1;
      if (targetPage !== currentPage) {
        currentPage = targetPage;
        if (typeof renderFilteredList === 'function') {
          renderFilteredList();
        }
      }
    }
  }

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
    // 과도한 골목/건물 단위 줌인(13+) 방지하고 도시 광역 뷰(zoom 11)로 부드럽게 이동
    const currentZoom = map.getZoom();
    const targetZoom = Math.min(Math.max(currentZoom, 10), 11);
    map.flyTo([video.lat, video.lng], targetZoom, {
      duration: 1.0
    });
    setTimeout(() => {
      marker.openPopup();
    }, 1000);
  }
}

function handleLocationPicked(lat, lng) {
  isPickingLocation = false;
  document.getElementById('pickerBanner').classList.add('hidden');
  document.getElementById('map').style.cursor = '';

  document.getElementById('inputLat').value = lat.toFixed(6);
  document.getElementById('inputLng').value = lng.toFixed(6);

  document.getElementById('addVideoModal').classList.add('active');
  showToast(`좌표가 선택되었습니다: (${lat.toFixed(4)}, ${lng.toFixed(4)})`, 'location_on');
}
