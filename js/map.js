/**
 * TubeMap Travel - Leaflet Map & Marker Management
 */

// Map Initialization
function initMap() {
  map = L.map('map', {
    zoomControl: false,
    worldCopyJump: true, // Fixes pins not showing when panning across the world
    minZoom: 2           // Prevents zooming out too far to see multiple empty worlds
  }).setView([32.0, 60.0], 4); // Eurasia centered view

  // Remove 'Leaflet' prefix while keeping required tile provider attribution
  map.attributionControl.setPrefix(false);

  // Zoom control at top-right
  L.control.zoom({ position: 'topright' }).addTo(map);

  // Free Tile Layers (No API key needed)
  const esriGray = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    maxNativeZoom: 16,
    attribution: 'Tiles &copy; Esri'
  });

  const esriTopo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
    maxZoom: 19,
    attribution: 'Tiles &copy; Esri'
  });

  const osmLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a>'
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
        <div class="popup-thumb-wrapper" onclick="openVideoModal('${video.id}')">
          <img class="popup-thumb" src="https://img.youtube.com/vi/${video.youtubeId}/hqdefault.jpg" alt="${video.title}" loading="lazy" />
          <div class="popup-play-btn"><span class="material-symbols-rounded filled">play_arrow</span></div>
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

function handleLocationPicked(lat, lng) {
  isPickingLocation = false;
  document.getElementById('pickerBanner').classList.add('hidden');
  document.getElementById('map').style.cursor = '';

  document.getElementById('inputLat').value = lat.toFixed(6);
  document.getElementById('inputLng').value = lng.toFixed(6);

  document.getElementById('addVideoModal').classList.add('active');
  showToast(`좌표가 선택되었습니다: (${lat.toFixed(4)}, ${lng.toFixed(4)})`, 'location_on');
}
