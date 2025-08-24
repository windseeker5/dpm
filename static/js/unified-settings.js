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
    initializeFormSubmission();
    
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
 * Form Submission Handler
 */
function initializeFormSubmission() {
    const form = document.getElementById('unified-settings-form');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Get the submit button and show loading state
            const submitBtn = document.querySelector('button[type="submit"][form="unified-settings-form"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
            
            // Create form data and add hardcoded values for removed fields
            const formData = new FormData(form);
            formData.append('gmail_label_folder_processed', 'InteractProcessed');
            formData.append('default_pass_amount', '50');
            formData.append('default_session_qt', '4');
            formData.append('email_info_text', '');
            formData.append('email_footer_text', '');
            formData.append('activities', '');
            
            // Submit the form
            fetch(form.action || '/admin/unified-settings', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                // Restore button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                
                // Show toast notification
                if (data.success) {
                    showToast('success', data.message || 'Settings saved successfully');
                    
                    // Update logo preview if new logo was uploaded
                    if (data.logo_url) {
                        const preview = document.getElementById('logo-preview');
                        if (preview) {
                            preview.src = data.logo_url;
                            preview.style.display = 'block';
                        }
                    }
                } else {
                    showToast('error', data.error || 'Failed to save settings');
                }
            })
            .catch(error => {
                // Restore button state
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                
                console.error('Error saving settings:', error);
                showToast('error', 'An error occurred while saving settings');
            });
        });
    }
}

/**
 * Show Toast Notification
 */
function showToast(type, message) {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : 'danger'} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Create container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    // Add toast to container
    container.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}