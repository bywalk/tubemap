/**
 * TubeMap Travel - Application Entry & Event Listeners
 */

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  loadInitialData();
  initMap();
  renderCreatorChips();
  initEventListeners();
  initDragToScroll();
  renderFilteredList();
  renderMapMarkers();
});

// Event Listeners
function initEventListeners() {
  // Theme Toggle Button (Dark / Light Mode)
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', toggleTheme);
  }

  // Search Inputs (Desktop header & Sidebar sync)
  const searchInput = document.getElementById('searchInput');
  const sidebarSearchInput = document.getElementById('sidebarSearchInput');
  let searchTrackTimer = null;

  function handleSearch(val) {
    currentSearchQuery = val;
    if (searchInput && searchInput.value !== val) searchInput.value = val;
    if (sidebarSearchInput && sidebarSearchInput.value !== val) sidebarSearchInput.value = val;
    renderFilteredList();
    renderMapMarkers();

    if (window.umami && val && val.trim().length >= 2) {
      clearTimeout(searchTrackTimer);
      searchTrackTimer = setTimeout(() => {
        window.umami.track('search', { query: val.trim() });
      }, 1000);
    }
  }

  if (searchInput) {
    searchInput.addEventListener('input', (e) => handleSearch(e.target.value));
  }
  if (sidebarSearchInput) {
    sidebarSearchInput.addEventListener('input', (e) => handleSearch(e.target.value));
  }

  // Filter Tabs (유튜버별 vs 국가/지역별 vs 나만의 맵)
  const tabCreatorBtn = document.getElementById('tabCreatorBtn');
  const tabRegionBtn = document.getElementById('tabRegionBtn');
  const tabMyMapBtn = document.getElementById('tabMyMapBtn');
  const creatorChipsContainer = document.getElementById('creatorChipsContainer');
  const regionChipsContainer = document.getElementById('regionChipsContainer');
  const myMapChipsContainer = document.getElementById('myMapChipsContainer');

  function activateTab(tabName) {
    currentTab = tabName;
    tabCreatorBtn.classList.toggle('active', tabName === 'creator');
    tabRegionBtn.classList.toggle('active', tabName === 'region');
    if (tabMyMapBtn) tabMyMapBtn.classList.toggle('active', tabName === 'mymap');

    creatorChipsContainer.classList.toggle('hidden', tabName !== 'creator');
    regionChipsContainer.classList.toggle('hidden', tabName !== 'region');
    if (myMapChipsContainer) myMapChipsContainer.classList.toggle('hidden', tabName !== 'mymap');

    renderFilteredList();
    renderMapMarkers();

    if (window.umami) {
      window.umami.track('tab-switch', { tab: tabName });
    }
  }

  tabCreatorBtn.addEventListener('click', () => activateTab('creator'));
  tabRegionBtn.addEventListener('click', () => activateTab('region'));
  if (tabMyMapBtn) {
    tabMyMapBtn.addEventListener('click', () => {
      activateTab('mymap');
      const filtered = getFilteredVideos();
      if (filtered.length > 0) {
        const bounds = L.latLngBounds(filtered.map(v => [v.lat, v.lng]));
        map.fitBounds(bounds, { padding: [60, 60], maxZoom: 10, animate: true });
      }
    });
  }

  // Region Chips
  const regionChips = document.querySelectorAll('#regionChipsContainer .chip');
  regionChips.forEach(chip => {
    chip.addEventListener('click', () => {
      regionChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentRegionFilter = chip.getAttribute('data-region');
      renderFilteredList();
      renderMapMarkers();

      if (window.umami) {
        window.umami.track('filter-region', { region: currentRegionFilter });
      }

      if (REGION_COORDINATES[currentRegionFilter]) {
        const coord = REGION_COORDINATES[currentRegionFilter];
        map.flyTo(coord.center, coord.zoom, { duration: 1.5 });
      } else if (currentRegionFilter === 'all') {
        map.flyTo([32.0, 60.0], 4, { duration: 1.5 });
      }
    });
  });

  // My Map Chips
  const myMapChips = document.querySelectorAll('#myMapChipsContainer .chip');
  myMapChips.forEach(chip => {
    chip.addEventListener('click', () => {
      myMapChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentMyMapFilter = chip.getAttribute('data-mymap');
      renderFilteredList();
      renderMapMarkers();

      if (window.umami) {
        window.umami.track('filter-mymap', { filter: currentMyMapFilter });
      }

      const filtered = getFilteredVideos();
      if (filtered.length > 0) {
        const bounds = L.latLngBounds(filtered.map(v => [v.lat, v.lng]));
        map.fitBounds(bounds, { padding: [60, 60], maxZoom: 10, animate: true });
      }
    });
  });

  // Brand click -> reset
  document.getElementById('brandBtn').addEventListener('click', () => {
    if (searchInput) searchInput.value = '';
    if (sidebarSearchInput) sidebarSearchInput.value = '';
    currentSearchQuery = '';
    activateTab('creator');
    const allChip = document.querySelector('#creatorChipsContainer .chip[data-creator="all"]');
    if (allChip) allChip.click();
  });

  // Date Sort Toggle Button (최신순 / 오래된순)
  const sortBtn = document.getElementById('sortOrderBtn');
  const sortIcon = document.getElementById('sortOrderIcon');
  const sortLabel = document.getElementById('sortOrderLabel');

  if (sortBtn) {
    sortBtn.addEventListener('click', () => {
      const newOrder = toggleDateSortOrder();
      if (sortIcon) {
        sortIcon.textContent = newOrder === 'desc' ? 'arrow_downward' : 'arrow_upward';
      }
      if (sortLabel) {
        sortLabel.textContent = newOrder === 'desc' ? '최신순' : '오래된순';
      }
      renderFilteredList();
      renderMapMarkers();
    });
  }

  // Mobile Drawer & Controls
  const closeSidebarBtn = document.getElementById('closeSidebarBtn');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  const floatingListBtn = document.getElementById('floatingListBtn');
  const sidebar = document.getElementById('sidebar');

  if (floatingListBtn) {
    floatingListBtn.addEventListener('click', openSidebar);
  }

  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener('click', closeSidebar);
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', closeSidebar);
  }

  // Video Modal Controls
  document.getElementById('closeVideoModalBtn').addEventListener('click', closeVideoModal);
  document.getElementById('modalDoneBtn').addEventListener('click', closeVideoModal);
  document.getElementById('videoModal').addEventListener('click', (e) => {
    if (e.target.id === 'videoModal') closeVideoModal();
  });

  const modalBookmarkBtn = document.getElementById('modalBookmarkBtn');
  if (modalBookmarkBtn) {
    modalBookmarkBtn.addEventListener('click', () => {
      if (currentModalVideoId) toggleBookmark(currentModalVideoId);
    });
  }

  const modalEditBtn = document.getElementById('modalEditBtn');
  if (modalEditBtn) {
    modalEditBtn.addEventListener('click', () => {
      if (currentModalVideoId) openEditVideoModal(currentModalVideoId);
    });
  }

  const detailReportBtn = document.getElementById('detailReportBtn');
  if (detailReportBtn) {
    detailReportBtn.addEventListener('click', () => {
      if (!currentModalVideoId) return;
      const target = travelVideos.find(v => v.id === currentModalVideoId);
      if (target) openContribModal(target);
    });
  }

  // Add / Edit Video Modal
  const addModal = document.getElementById('addVideoModal');
  const openAddBtn = document.getElementById('openAddModalBtn');
  const closeAddBtn = document.getElementById('closeAddModalBtn');
  const cancelAddBtn = document.getElementById('cancelAddBtn');
  const deleteVideoBtn = document.getElementById('deleteVideoBtn');

  openAddBtn.addEventListener('click', openAddModeModal);

  const closeAddModal = () => {
    addModal.classList.remove('active');
  };

  closeAddBtn.addEventListener('click', closeAddModal);
  cancelAddBtn.addEventListener('click', closeAddModal);
  addModal.addEventListener('click', (e) => {
    if (e.target.id === 'addVideoModal') closeAddModal();
  });

  // Delete Video Spot
  if (deleteVideoBtn) {
    deleteVideoBtn.addEventListener('click', () => {
      if (!editingVideoId) return;
      const target = travelVideos.find(v => v.id === editingVideoId);
      if (!target) return;
      if (!confirm(`'${target.locationName}' (${target.creator}) 여행지를 내 지도에서 삭제하시겠습니까?`)) {
        return;
      }
      deletedVideoIds.add(target.id);
      if (!isCustomVideo(target) && target.youtubeId) {
        deletedVideoIds.add(target.youtubeId);
      }
      travelVideos = travelVideos.filter(v => v.id !== editingVideoId);
      saveToStorage();
      closeAddModal();
      renderCreatorChips();
      renderFilteredList();
      renderMapMarkers();
      showToast(`'${target.locationName}' 여행지가 삭제되었습니다.`, 'delete');
    });
  }

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

  // Add / Edit Video Form Submit
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

    if (editingVideoId) {
      const idx = travelVideos.findIndex(v => v.id === editingVideoId);
      if (idx !== -1) {
        const existing = travelVideos[idx];
        travelVideos[idx] = {
          ...existing,
          creator: creator || existing.creator || '추천 크리에이터',
          channel: creator || existing.channel,
          youtubeId: ytId,
          title,
          country,
          city,
          locationName,
          lat,
          lng,
          tip,
          tags,
          isEdited: true
        };
      }
      saveToStorage();
      closeAddModal();
      renderCreatorChips();
      renderFilteredList();
      renderMapMarkers();
      showToast(`'${locationName}' 위치 및 정보가 수정되었습니다!`, 'edit_location_alt');
      map.flyTo([lat, lng], Math.max(map.getZoom(), 13), { duration: 1.2 });
      editingVideoId = null;
      return;
    }

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
      bookmarked: true,
      description: tip || '사용자가 직접 등록한 추천 여행지입니다.',
      highlights: []
    };

    travelVideos.unshift(newVideo);
    saveToStorage();

    addForm.reset();
    thumbPreviewBox.innerHTML = `<span>URL을 입력하면 썸네일 미리보기가 표시됩니다</span>`;
    closeAddModal();

    renderCreatorChips();
    renderFilteredList();
    renderMapMarkers();
    showToast(`[${creator}] '${locationName}' 여행지가 나만의 맵에 등록되었습니다!`, 'add_location_alt');

    map.flyTo([lat, lng], 13, { duration: 1.5 });
  });

  // Official Map Contribution (GitHub Issue & PR Modal)
  const contribModal = document.getElementById('contribModal');
  const closeContribModalBtn = document.getElementById('closeContribModalBtn');
  const doneContribModalBtn = document.getElementById('doneContribModalBtn');
  const copyContribDataBtn = document.getElementById('copyContribDataBtn');
  const openGithubIssueBtn = document.getElementById('openGithubIssueBtn');
  const openGithubPrBtn = document.getElementById('openGithubPrBtn');
  const reportGithubBtn = document.getElementById('reportGithubBtn');

  let currentContribSnippet = '';

  const closeContribModal = () => {
    if (contribModal) contribModal.classList.remove('active');
  };

  if (closeContribModalBtn) closeContribModalBtn.addEventListener('click', closeContribModal);
  if (doneContribModalBtn) doneContribModalBtn.addEventListener('click', closeContribModal);
  if (contribModal) {
    contribModal.addEventListener('click', (e) => {
      if (e.target.id === 'contribModal') closeContribModal();
    });
  }

  const openContribModal = (data) => {
    if (!data) return;
    const { creator, youtubeId, title, country, city, locationName, lat, lng, tip, tags } = data;

    const previewCreatorEl = document.getElementById('contribPreviewCreator');
    const previewLocEl = document.getElementById('contribPreviewLocation');
    const previewCoordsEl = document.getElementById('contribPreviewCoords');
    const previewTipEl = document.getElementById('contribPreviewTip');

    if (previewCreatorEl) previewCreatorEl.textContent = `[${creator || '유튜버'}] ${title || '여행 영상'}`;
    if (previewLocEl) previewLocEl.textContent = `📍 ${country || ''} ${city || ''} - ${locationName || ''}`;
    if (previewCoordsEl) previewCoordsEl.textContent = `🌐 좌표: ${lat}, ${lng}`;
    if (previewTipEl) previewTipEl.textContent = tip ? `💡 ${tip}` : '💡 등록된 꿀팁/메모 없음';

    // Format JS snippet
    currentContribSnippet = `  {\n    id: "user-${youtubeId}",\n    creator: "${creator || ''}",\n    youtubeId: "${youtubeId}",\n    title: "${(title || '').replace(/"/g, '\\"')}",\n    country: "${country || ''}",\n    city: "${city || ''}",\n    locationName: "${(locationName || '').replace(/"/g, '\\"')}",\n    lat: ${lat},\n    lng: ${lng},\n    tags: ${JSON.stringify(tags || [city, country, "유튜브추천"])},\n    tip: "${(tip || '').replace(/"/g, '\\"')}",\n    publishedAt: "${new Date().toISOString().slice(0, 10)}"\n  }`;

    // GitHub Issue Pre-filled URL
    const issueTitle = `[제보] ${creator || '유튜버'} - ${locationName || '명소'} (${city || country || '여행지'})`;
    const issueBody = `### 1. 유튜브 영상 정보\n- **영상 링크**: https://www.youtube.com/watch?v=${youtubeId}\n- **크리에이터**: ${creator || ''}\n- **영상 제목**: ${title || ''}\n\n### 2. 제보 여행지 정보\n- **국가 / 도시**: ${country || ''} / ${city || ''}\n- **장소 / 명소명**: ${locationName || ''}\n- **위치 좌표**: \`${lat}, ${lng}\` ([구글맵으로 위치 확인](https://www.google.com/maps?q=${lat},${lng}))\n- **유튜버 꿀팁**: ${tip || '없음'}\n\n### 3. 제보 데이터 코드 (TubeMap 자동 생성)\n\`\`\`javascript\n${currentContribSnippet}\n\`\`\`\n\n*(GitHub Actions AI가 위 데이터를 자동으로 팩트체크한 후 공식 지도에 반영합니다.)*`;

    if (openGithubIssueBtn) {
      openGithubIssueBtn.href = `https://github.com/bywalk/tubemap/issues/new?title=${encodeURIComponent(issueTitle)}&body=${encodeURIComponent(issueBody)}&labels=spot-contribution`;
    }
    if (openGithubPrBtn) {
      openGithubPrBtn.href = `https://github.com/bywalk/tubemap/edit/main/js/data/videos_recent.js`;
    }

    contribModal.classList.add('active');
  };

  if (copyContribDataBtn) {
    copyContribDataBtn.addEventListener('click', () => {
      if (!currentContribSnippet) return;
      navigator.clipboard.writeText(currentContribSnippet).then(() => {
        showToast('제보용 데이터 코드가 클립보드에 복사되었습니다!', 'content_copy');
      }).catch(() => {
        prompt('아래 코드를 복사하세요:', currentContribSnippet);
      });
    });
  }

  if (reportGithubBtn) {
    reportGithubBtn.addEventListener('click', () => {
      const rawUrl = urlInput.value.trim();
      const ytId = extractYoutubeId(rawUrl);
      const title = document.getElementById('inputTitle').value.trim();
      const creator = document.getElementById('inputCreator').value.trim();
      const countryCity = document.getElementById('inputCountry').value.trim();
      const locationName = document.getElementById('inputLocationName').value.trim();
      const lat = parseFloat(document.getElementById('inputLat').value);
      const lng = parseFloat(document.getElementById('inputLng').value);
      const tip = document.getElementById('inputTip').value.trim();
      const rawTags = document.getElementById('inputTags').value.trim();

      if (!ytId) {
        alert('유튜브 영상 URL 또는 영상 ID를 먼저 입력해주세요.');
        return;
      }
      if (isNaN(lat) || isNaN(lng)) {
        alert('지도에서 위치를 선택하거나 올바른 위도/경도 좌표를 입력해주세요.');
        return;
      }

      const parts = countryCity.split(' ');
      const country = parts[0] || '기타';
      const city = parts.slice(1).join(' ') || country;
      const tags = rawTags ? rawTags.split(',').map(t => t.trim()).filter(Boolean) : [];

      openContribModal({
        creator: creator || '여행 유튜버',
        youtubeId: ytId,
        title: title || '유튜브 여행 영상',
        country,
        city,
        locationName: locationName || city,
        lat,
        lng,
        tip,
        tags
      });
    });
  }

  // Export / Backup JSON
  document.getElementById('exportBtn').addEventListener('click', () => {
    const backupPayload = {
      version: 1,
      exportedAt: new Date().toISOString(),
      deletedIds: Array.from(deletedVideoIds),
      videos: travelVideos
    };
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(backupPayload, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `my_tubemap_backup_${new Date().toISOString().slice(0,10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast('나만의 맵 데이터가 JSON 파일로 백업되었습니다.', 'download');
  });

  // Import / Restore JSON
  const importBtn = document.getElementById('importBtn');
  const importFileInput = document.getElementById('importFileInput');
  if (importBtn && importFileInput) {
    importBtn.addEventListener('click', () => {
      importFileInput.value = '';
      importFileInput.click();
    });

    importFileInput.addEventListener('change', (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const parsed = JSON.parse(event.target.result);
          const importedVideos = Array.isArray(parsed) ? parsed : (parsed && Array.isArray(parsed.videos) ? parsed.videos : null);

          if (!importedVideos) {
            alert('올바른 TubeMap 백업 JSON 파일이 아닙니다.');
            return;
          }

          if (parsed && Array.isArray(parsed.deletedIds)) {
            deletedVideoIds = new Set(parsed.deletedIds);
          }

          localStorage.setItem(STORAGE_KEY, JSON.stringify(importedVideos));
          localStorage.setItem(DELETED_IDS_KEY, JSON.stringify(Array.from(deletedVideoIds)));

          loadInitialData();
          renderCreatorChips();
          renderFilteredList();
          renderMapMarkers();
          showToast(`백업 파일에서 총 ${travelVideos.length}곳의 여행지를 불러왔습니다!`, 'upload');
        } catch (err) {
          console.error('JSON Import Error:', err);
          alert('백업 파일을 읽는 중 오류가 발생했습니다.');
        }
      };
      reader.readAsText(file);
    });
  }

  // Keydown Escape
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeVideoModal();
      closeAddModal();
      closeContribModal();
      if (isPickingLocation) {
        cancelPickBtn.click();
      }
    }
  });
}
