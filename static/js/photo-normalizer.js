/**
 * Photo Normalization Tool — Shared utility
 * See docs/DESIGN_SYSTEM.md §15 for usage and HTML structure.
 *
 * Usage:
 *   var picker = initPhotoNormalizer({ wrapperId, uploadInputId, cropModalId,
 *                                      cropImageId, confirmBtnId, ...options });
 *   picker.setThumbnail(src);   // programmatically set image
 *   picker.reset(src);          // reset to a given src (or placeholder if null)
 */
function initPhotoNormalizer(config) {
  var opts = {
    wrapperId:        config.wrapperId,
    uploadInputId:    config.uploadInputId,
    cropModalId:      config.cropModalId,
    cropImageId:      config.cropImageId,
    confirmBtnId:     config.confirmBtnId,
    optionsPanelId:   config.optionsPanelId   || null,
    hiddenInputId:    config.hiddenInputId     || null,
    sourceToggleId:   config.sourceToggleId    || null,
    searchPanelId:    config.searchPanelId     || null,
    uploadPanelId:    config.uploadPanelId     || null,
    searchInputId:    config.searchInputId     || null,
    searchBtnId:      config.searchBtnId       || null,
    unsplashModalId:  config.unsplashModalId   || null,
    unsplashImagesId: config.unsplashImagesId  || null,
    prevPageBtnId:    config.prevPageBtnId     || null,
    nextPageBtnId:    config.nextPageBtnId     || null,
    aspectRatio:      config.aspectRatio       !== undefined ? config.aspectRatio : NaN,
    maxWidth:         config.maxWidth          || 1200,
    maxHeight:        config.maxHeight         || 800,
    quality:          config.quality           || 0.92,
    objectFit:        config.objectFit         || 'cover',
    placeholderLabel: config.placeholderLabel  || 'Add photo',
    onConfirm:        config.onConfirm         || null,
    onDelete:         config.onDelete          || null,
    src:              config.src               || null,
  };

  var cropperInstance = null;
  var uploadInput     = document.getElementById(opts.uploadInputId);
  var cropModalEl     = document.getElementById(opts.cropModalId);
  var cropModal       = cropModalEl ? new bootstrap.Modal(cropModalEl) : null;
  var cropImageEl     = document.getElementById(opts.cropImageId);
  var confirmBtn      = document.getElementById(opts.confirmBtnId);
  var hiddenInput     = opts.hiddenInputId ? document.getElementById(opts.hiddenInputId) : null;
  var optionsPanel    = opts.optionsPanelId ? document.getElementById(opts.optionsPanelId) : null;

  function getWrapper() {
    return document.getElementById(opts.wrapperId);
  }

  function placeholderHtml() {
    return '<div class="d-flex flex-column align-items-center justify-content-center"' +
           ' style="width:100%;height:100%;">' +
           '<i class="ti ti-photo text-muted fs-2"></i>' +
           '<small class="text-muted">' + opts.placeholderLabel + '</small>' +
           '</div>';
  }

  function thumbnailHtml(src) {
    return '<img src="' + src + '" class="rounded"' +
           ' style="width:100%;height:100%;object-fit:' + opts.objectFit + ';">' +
           '<span class="position-absolute top-0 end-0 badge bg-danger rounded-circle p-1"' +
           ' style="cursor:pointer;" data-pnt-delete>' +
           '<i class="ti ti-x text-white" style="font-size:12px;"></i></span>';
  }

  function setThumbnail(src) {
    var w = getWrapper();
    if (!w) return;
    w.innerHTML = thumbnailHtml(src);
    if (optionsPanel) optionsPanel.style.display = 'none';
  }

  function setPlaceholder() {
    var w = getWrapper();
    if (!w) return;
    w.innerHTML = placeholderHtml();
    if (optionsPanel) optionsPanel.style.display = 'none';
    if (hiddenInput) hiddenInput.value = '';
    if (uploadInput) uploadInput.value = '';
    if (opts.onDelete) opts.onDelete();
  }

  // ── Event delegation — one listener covers dynamic innerHTML ────────────
  document.addEventListener('click', function(e) {
    var wrapper = e.target.closest('#' + opts.wrapperId);
    if (!wrapper) return;

    // Delete badge clicked
    if (e.target.closest('[data-pnt-delete]')) {
      e.stopPropagation();
      setPlaceholder();
      return;
    }

    // Wrapper body clicked — toggle options panel
    if (optionsPanel) {
      optionsPanel.style.display = (optionsPanel.style.display === 'none') ? 'block' : 'none';
    }
  });

  // ── Source toggle (Search ↔ Upload) — optional ───────────────────────────
  if (opts.sourceToggleId) {
    var sourceToggle  = document.getElementById(opts.sourceToggleId);
    var searchPanel   = opts.searchPanelId ? document.getElementById(opts.searchPanelId) : null;
    var uploadPanel   = opts.uploadPanelId ? document.getElementById(opts.uploadPanelId) : null;
    if (sourceToggle) {
      sourceToggle.addEventListener('change', function() {
        if (searchPanel) searchPanel.style.display = this.checked ? 'none' : 'block';
        if (uploadPanel) uploadPanel.style.display  = this.checked ? 'block' : 'none';
      });
    }
  }

  // ── Unsplash search — optional ───────────────────────────────────────────
  if (opts.unsplashModalId) {
    var searchInput     = opts.searchInputId  ? document.getElementById(opts.searchInputId)  : null;
    var searchBtnEl     = opts.searchBtnId    ? document.getElementById(opts.searchBtnId)    : null;
    var unsplashModalEl = document.getElementById(opts.unsplashModalId);
    var unsplashModal   = unsplashModalEl ? new bootstrap.Modal(unsplashModalEl) : null;
    var imagesDiv       = opts.unsplashImagesId ? document.getElementById(opts.unsplashImagesId) : null;
    var prevBtn         = opts.prevPageBtnId ? document.getElementById(opts.prevPageBtnId) : null;
    var nextBtn         = opts.nextPageBtnId ? document.getElementById(opts.nextPageBtnId) : null;
    var paginationEl    = prevBtn ? prevBtn.parentElement : null;
    var uPage = 1, uQuery = '';

    function loadUnsplashImages(page) {
      if (!uQuery || !imagesDiv) return;
      imagesDiv.innerHTML = '<div class="text-center p-4"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div></div>';
      fetch('/unsplash-search?q=' + encodeURIComponent(uQuery) + '&page=' + page)
        .then(function(r) {
          return r.ok ? r.json() : r.json().then(function(d) { throw new Error(d.error || 'Search failed'); });
        })
        .then(function(data) {
          imagesDiv.innerHTML = '';
          if (!data.length) {
            imagesDiv.innerHTML = '<div class="text-center p-4"><p class="text-muted">No images found for this search.</p></div>';
            if (paginationEl) paginationEl.style.display = 'none';
            return;
          }
          data.forEach(function(image) {
            var col = document.createElement('div');
            col.className = 'col-md-4 mb-3';
            col.innerHTML = '<div class="card card-link card-border h-100"><img src="' + image.thumb + '" class="card-img-top" style="cursor:pointer;height:200px;object-fit:cover;" alt="Unsplash Image"></div>';
            col.querySelector('img').addEventListener('click', function() {
              var self = this;
              self.style.opacity = '0.5'; self.style.cursor = 'wait';
              fetch('/download-unsplash-image?url=' + encodeURIComponent(image.full))
                .then(function(r) { return r.json(); })
                .then(function(result) {
                  if (result.success) {
                    var imgUrl = '/static/uploads/activity_images/' + result.filename;
                    if (hiddenInput) hiddenInput.value = result.filename;
                    if (uploadInput) uploadInput.value = '';
                    setThumbnail(imgUrl);
                    if (opts.onConfirm) opts.onConfirm(null, imgUrl);
                    if (unsplashModal) unsplashModal.hide();
                  } else {
                    self.style.opacity = '1'; self.style.cursor = 'pointer';
                  }
                })
                .catch(function() { self.style.opacity = '1'; self.style.cursor = 'pointer'; });
            });
            imagesDiv.appendChild(col);
          });
          if (paginationEl) paginationEl.style.display = 'flex';
          if (prevBtn) prevBtn.disabled = page === 1;
        })
        .catch(function(err) {
          var msg = err.message || 'Error loading images. Please try again.';
          if (msg.indexOf('API key') !== -1) msg = 'Image search is not available. The API key needs to be configured by an administrator.';
          else if (msg.indexOf('temporarily unavailable') !== -1) msg = 'Image search service is temporarily unavailable. Please try again later.';
          imagesDiv.innerHTML = '<div class="text-center p-4"><div class="alert alert-warning border-warning mb-3">' +
            '<div class="d-flex align-items-center"><i class="ti ti-alert-triangle me-2"></i>' +
            '<strong>Image Search Unavailable</strong></div>' +
            '<p class="mb-0 mt-2">' + msg + '</p></div>' +
            '<div class="text-muted small"><p class="mb-2"><strong>Alternative options:</strong></p>' +
            '<ul class="list-unstyled"><li>Use the "Upload your own image" option instead</li>' +
            '<li>Contact your administrator to configure image search</li>' +
            '<li>Proceed without an image for now</li></ul></div></div>';
          if (paginationEl) paginationEl.style.display = 'none';
        });
    }

    if (searchInput) {
      searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') { e.preventDefault(); if (searchBtnEl) searchBtnEl.click(); }
      });
    }
    if (searchBtnEl) {
      searchBtnEl.addEventListener('click', function() {
        uQuery = searchInput ? searchInput.value.trim() : '';
        if (!uQuery) return;
        uPage = 1;
        loadUnsplashImages(1);
        if (unsplashModal) unsplashModal.show();
      });
    }
    if (prevBtn) prevBtn.addEventListener('click', function() {
      if (uPage > 1) { uPage--; loadUnsplashImages(uPage); }
    });
    if (nextBtn) nextBtn.addEventListener('click', function() {
      uPage++; loadUnsplashImages(uPage);
    });
  }

  // ── File selected → open crop modal ────────────────────────────────────
  if (uploadInput) {
    uploadInput.addEventListener('change', function(e) {
      var file = e.target.files[0];
      if (!file || !cropImageEl) return;
      var reader = new FileReader();
      reader.onload = function(ev) {
        cropImageEl.src = ev.target.result;
        if (cropModal) cropModal.show();
      };
      reader.readAsDataURL(file);
      this.value = ''; // allow re-selecting same file
    });
  }

  // ── Crop modal: init Cropper on show, destroy on hide ──────────────────
  if (cropModalEl) {
    cropModalEl.addEventListener('shown.bs.modal', function() {
      if (cropperInstance) cropperInstance.destroy();
      cropperInstance = new Cropper(cropImageEl, {
        aspectRatio:  opts.aspectRatio,
        viewMode:     1,
        autoCropArea: 0.9,
        movable:      true,
        zoomable:     true,
        rotatable:    false,
        scalable:     false,
        responsive:   true,
      });
    });
    cropModalEl.addEventListener('hidden.bs.modal', function() {
      if (cropperInstance) { cropperInstance.destroy(); cropperInstance = null; }
    });
  }

  // ── Confirm crop: compress → inject into file input → update thumbnail ──
  if (confirmBtn) {
    confirmBtn.addEventListener('click', function() {
      if (!cropperInstance) return;
      cropperInstance.getCroppedCanvas({
        maxWidth: opts.maxWidth, maxHeight: opts.maxHeight,
        imageSmoothingQuality: 'high',
      }).toBlob(function(blob) {
        var objectUrl = URL.createObjectURL(blob);
        var dt = new DataTransfer();
        dt.items.add(new File([blob], 'photo.jpg', { type: 'image/jpeg' }));
        if (uploadInput) uploadInput.files = dt.files;
        if (hiddenInput) hiddenInput.value = '';
        setThumbnail(objectUrl);
        if (cropModal) cropModal.hide();
        if (opts.onConfirm) opts.onConfirm(blob, objectUrl);
      }, 'image/jpeg', opts.quality);
    });
  }

  // ── Initialize wrapper state on startup ─────────────────────────────────
  if (opts.src) { setThumbnail(opts.src); } else { setPlaceholder(); }

  // ── Public API ──────────────────────────────────────────────────────────
  return {
    setThumbnail: setThumbnail,
    reset: function(src) {
      if (src) { setThumbnail(src); } else { setPlaceholder(); }
    },
  };
}
