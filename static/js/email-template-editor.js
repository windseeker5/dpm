// Minimal Email Template Editor JavaScript - Max 50 lines

// Initialize TinyMCE (8 lines max)
function initTinyMCE() {
  if (typeof tinymce !== 'undefined') {
    tinymce.init({
      selector: 'textarea.tinymce', height: 200, menubar: false,
      plugins: 'lists link', toolbar: 'bold italic | bullist numlist | link'
    });
  }
}

// Preview logo before upload (7 lines max)
function previewLogo(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = e => {
      const preview = input.parentElement.querySelector('.logo-preview') || Object.assign(document.createElement('img'), {className: 'logo-preview', style: 'max-width:200px;margin-top:10px'});
      preview.src = e.target.result; if (!preview.parentElement) input.parentElement.appendChild(preview);
    }; reader.readAsDataURL(input.files[0]);
  }
}

// Event delegation and initialization
document.addEventListener('DOMContentLoaded', function() {
  // Don't initialize TinyMCE globally - handled manually in modal
  document.addEventListener('change', function(e) { // Delegate file events
    if (e.target.type === 'file' && e.target.accept === 'image/*') previewLogo(e.target);
  });
  window.addEventListener('beforeunload', function() { // Cleanup
    if (typeof tinymce !== 'undefined') tinymce.remove();
  });
});

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { initTinyMCE, previewLogo };
}