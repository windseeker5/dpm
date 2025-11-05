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
    const fileInput = document.getElementById('logo-file-input');
    const preview = document.getElementById('logo-preview');
    
    if (fileInput && preview) {
        fileInput.addEventListener('change', function(event) {
            const file = event.target.files[0];
            if (file && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            } else {
                preview.src = '';
                preview.style.display = 'none';
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