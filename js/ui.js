/**
 * TubeMap Travel - Sidebar List, Modals, and UI Components
 */

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
    const emptyMsg = currentTab === 'mymap'
      ? '아직 나만의 맵에 저장된 여행지가 없습니다.<br>마음에 드는 여행지의 <b>[찜]</b>을 누르거나 <b>[+ 등록]</b>해보세요!'
      : '검색어를 바꾸거나 새 영상을 등록해보세요!';
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon"><span class="material-symbols-rounded" style="font-size: 42px; color: #94a3b8;">${currentTab === 'mymap' ? 'star' : 'explore'}</span></div>
        <h4>조건에 맞는 여행 영상이 없습니다</h4>
        <p style="font-size: 0.85rem; margin-top: 6px; line-height: 1.5;">${emptyMsg}</p>
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
        <div class="play-badge"><span class="material-symbols-rounded filled" style="font-size: 18px;">play_arrow</span></div>
      </div>
      <div class="video-card-content">
        <div class="card-top-row">
          <span class="video-creator-pill"><span class="material-symbols-rounded icon-xs" style="vertical-align: -2px;">person</span> ${video.creator || '크리에이터'}</span>
          <div class="card-action-btns">
            <button class="card-icon-btn ${video.bookmarked ? 'bookmarked' : ''}" onclick="toggleBookmark('${video.id}', event)" title="나만의 맵에 찜하기">
              <span class="material-symbols-rounded icon-xs ${video.bookmarked ? 'filled' : ''}">star</span>
            </button>
            <button class="card-icon-btn" onclick="openEditVideoModal('${video.id}', event)" title="위치 및 정보 편집">
              <span class="material-symbols-rounded icon-xs">edit</span>
            </button>
          </div>
        </div>
        <div class="video-card-title">${video.title}</div>
        ${video.tip ? `<div class="card-tip-snippet"><span class="material-symbols-rounded icon-xs" style="vertical-align: -2px;">lightbulb</span> ${video.tip}</div>` : ''}
        <div class="video-card-meta">
          <span class="channel-name"><span class="material-symbols-rounded icon-xs filled" style="vertical-align: -2px; color: var(--accent);">location_on</span> ${video.country || ''} · ${video.locationName}</span>
          <span style="font-size: 0.72rem; color: #64748b; display: inline-flex; align-items: center; gap: 2px;"><span class="material-symbols-rounded" style="font-size: 13px;">calendar_today</span> ${video.publishedAt || '1년 이내'}</span>
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

function updateModalBookmarkBtn(video) {
  const btn = document.getElementById('modalBookmarkBtn');
  if (!btn || !video) return;
  if (video.bookmarked) {
    btn.innerHTML = '<span class="material-symbols-rounded icon-sm filled">star</span> 찜됨';
    btn.style.background = '#fffbeb';
    btn.style.borderColor = '#fcd34d';
    btn.style.color = '#b45309';
  } else {
    btn.innerHTML = '<span class="material-symbols-rounded icon-sm">star</span> 찜하기';
    btn.style.background = '';
    btn.style.borderColor = '';
    btn.style.color = '';
  }
}

// Open Video Player Modal
function openVideoModal(videoId, startTime = 0) {
  const video = travelVideos.find(v => v.id === videoId);
  if (!video) return;

  currentModalVideoId = videoId;

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
  locationTag.innerHTML = `<span class="material-symbols-rounded icon-sm filled">location_on</span> ${video.country || ''} ${video.city || ''} · ${video.locationName}`;
  creatorBadge.innerHTML = `<span class="material-symbols-rounded icon-sm" style="vertical-align: -3px;">person</span> ${video.creator || video.channel}`;
  updateModalBookmarkBtn(video);

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
  currentModalVideoId = null;
  modal.classList.remove('active');
}

// Open Edit Modal for an existing or custom spot
function openEditVideoModal(videoId, event) {
  if (event) {
    event.stopPropagation();
  }
  const video = travelVideos.find(v => v.id === videoId);
  if (!video) return;

  closeVideoModal();

  editingVideoId = videoId;

  const modalTitle = document.getElementById('addModalTitle');
  const submitBtn = document.getElementById('submitVideoFormBtn');
  const deleteBtn = document.getElementById('deleteVideoBtn');
  const thumbPreviewBox = document.getElementById('thumbnailPreviewBox');

  if (modalTitle) modalTitle.innerHTML = '<span class="material-symbols-rounded icon-sm" style="vertical-align: -3px;">edit_location_alt</span> 여행지 정보 및 위치 편집';
  if (submitBtn) submitBtn.textContent = '수정 내용 저장';
  if (deleteBtn) deleteBtn.classList.remove('hidden');

  document.getElementById('inputYoutubeUrl').value = `https://www.youtube.com/watch?v=${video.youtubeId}`;
  document.getElementById('inputTitle').value = video.title || '';
  document.getElementById('inputCreator').value = video.creator || video.channel || '';
  document.getElementById('inputCountry').value = [video.country, video.city && video.city !== video.country ? video.city : ''].filter(Boolean).join(' ');
  document.getElementById('inputLocationName').value = video.locationName || '';
  document.getElementById('inputLat').value = video.lat;
  document.getElementById('inputLng').value = video.lng;
  document.getElementById('inputTip').value = video.tip || '';
  document.getElementById('inputTags').value = (video.tags || []).join(', ');

  if (video.youtubeId && thumbPreviewBox) {
    thumbPreviewBox.innerHTML = `<img src="https://img.youtube.com/vi/${video.youtubeId}/hqdefault.jpg" alt="미리보기" />`;
  }

  document.getElementById('addVideoModal').classList.add('active');
}

function openAddModeModal() {
  editingVideoId = null;
  const addForm = document.getElementById('addVideoForm');
  const modalTitle = document.getElementById('addModalTitle');
  const submitBtn = document.getElementById('submitVideoFormBtn');
  const deleteBtn = document.getElementById('deleteVideoBtn');
  const thumbPreviewBox = document.getElementById('thumbnailPreviewBox');

  if (addForm) addForm.reset();
  if (modalTitle) modalTitle.innerHTML = '<span class="material-symbols-rounded icon-sm" style="vertical-align: -3px;">add_location_alt</span> 새 여행 유튜브 영상 등록';
  if (submitBtn) submitBtn.textContent = '지도에 등록하기';
  if (deleteBtn) deleteBtn.classList.add('hidden');
  if (thumbPreviewBox) thumbPreviewBox.innerHTML = `<span>URL을 입력하면 썸네일 미리보기가 표시됩니다</span>`;

  document.getElementById('addVideoModal').classList.add('active');
}

// Toast Notification
function showToast(message, icon = 'check_circle') {
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
