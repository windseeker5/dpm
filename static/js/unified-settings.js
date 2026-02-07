/**
 * Unified Settings JavaScript
 * Clean, functional JavaScript without UI effects
 */

console.log('Unified Settings JS loaded');

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeLogoPreview();
    initializePaymentBotToggle();
    initializeFuzzyThreshold();

    console.log('Unified Settings JS initialized');
});

/**
 * Logo Preview Functionality
 */
function initializeLogoPreview() {
    var fileInput = document.getElementById('logo-file-input');
    var deleteFlag = document.getElementById('deleteLogoFlag');

    function setupDeleteButton() {
        var btn = document.getElementById('deleteLogoBtn');
        if (btn) {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                deleteFlag.value = '1';
                fileInput.value = '';
                var wrapper = document.getElementById('logoWrapper');
                wrapper.innerHTML = '<div id="logo-preview" class="rounded bg-secondary-lt d-flex flex-column align-items-center justify-content-center" style="width: 80px; height: 80px;"><i class="ti ti-photo text-muted fs-2"></i><small class="text-muted">No logo</small></div>';
            });
        }
    }

    setupDeleteButton();

    if (fileInput) {
        fileInput.addEventListener('change', function(event) {
            var file = event.target.files[0];
            if (file && file.type.startsWith('image/')) {
                deleteFlag.value = '';
                var reader = new FileReader();
                reader.onload = function(e) {
                    var wrapper = document.getElementById('logoWrapper');
                    wrapper.innerHTML = '<img id="logo-preview" src="' + e.target.result + '" class="rounded" style="width: 80px; height: 80px; object-fit: contain; background: #f8f9fa;"><span class="position-absolute top-0 end-0 badge bg-danger rounded-circle p-2" style="cursor: pointer;" id="deleteLogoBtn"><i class="ti ti-x text-white" style="font-size: 14px;"></i></span>';
                    setupDeleteButton();
                };
                reader.readAsDataURL(file);
            }
        });
    }
}

/**
 * Payment Bot Toggle
 */
function initializePaymentBotToggle() {
    const toggle = document.getElementById('enable_email_payment_bot');
    const config = document.getElementById('email-bot-config');
    
    if (toggle && config) {
        toggle.addEventListener('change', function() {
            config.style.display = this.checked ? 'block' : 'none';
        });
    }
}

/**
 * Fuzzy Threshold Slider
 */
function initializeFuzzyThreshold() {
    const slider = document.getElementById('threshold-slider');
    const value = document.getElementById('threshold-value');
    
    if (slider && value) {
        slider.addEventListener('input', function() {
            value.textContent = this.value;
        });
    }
}

/**
 * Form Submission Handler - REMOVED
 * Now using standard Flask form submission with flash messages for consistency
 */

/**
 * Payment Bot Test Functionality - REMOVED
 * Payment bot test now uses standard GET request with flash messages
 * See unified_settings.html line 153: <a href="/admin/unified-settings?test_payment_bot=1">
 */

/**
 * Show Toast Notification - REMOVED
 * Now using standard Flask flash() messages for consistency across the entire app
 */