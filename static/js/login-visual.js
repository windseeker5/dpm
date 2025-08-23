/**
 * Login Visual Enhancements
 * Provides ONLY visual improvements for the login page without modifying form behavior
 */

document.addEventListener('DOMContentLoaded', function() {
    // Page load animation
    document.body.classList.add('fade-in');
    
    // Password show/hide toggle functionality
    initPasswordToggle();
    
    // Visual loading spinner on form submit (cosmetic only)
    initVisualLoadingSpinner();
    
    // Visual feedback for input validation
    initInputValidationFeedback();
});

/**
 * Initialize password show/hide toggle
 */
function initPasswordToggle() {
    const passwordInput = document.querySelector('input[type="password"]');
    if (!passwordInput) return;
    
    // Create toggle button
    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.className = 'btn btn-link position-absolute end-0 top-50 translate-middle-y me-2';
    toggleButton.style.cssText = 'border: none; background: none; z-index: 5; padding: 0.25rem;';
    toggleButton.innerHTML = '<i class="ti ti-eye text-muted"></i>';
    toggleButton.setAttribute('aria-label', 'Show password');
    
    // Position the input container relatively
    const inputGroup = passwordInput.closest('.form-group') || passwordInput.parentElement;
    inputGroup.style.position = 'relative';
    
    // Add padding to prevent text overlap with button
    passwordInput.style.paddingRight = '2.5rem';
    
    // Insert toggle button
    inputGroup.appendChild(toggleButton);
    
    // Toggle functionality
    toggleButton.addEventListener('click', function() {
        const isPassword = passwordInput.type === 'password';
        passwordInput.type = isPassword ? 'text' : 'password';
        
        const icon = toggleButton.querySelector('i');
        icon.className = isPassword ? 'ti ti-eye-off text-muted' : 'ti ti-eye text-muted';
        toggleButton.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
        
        // Add visual feedback
        toggleButton.style.transform = 'scale(0.95)';
        setTimeout(() => {
            toggleButton.style.transform = 'scale(1)';
        }, 150);
    });
}

/**
 * Initialize visual loading spinner on form submit (cosmetic only)
 */
function initVisualLoadingSpinner() {
    const loginForm = document.querySelector('form[method="POST"]');
    if (!loginForm) return;
    
    const submitButton = loginForm.querySelector('button[type="submit"]');
    if (!submitButton) return;
    
    // Store original button content
    const originalContent = submitButton.innerHTML;
    
    loginForm.addEventListener('submit', function() {
        // Visual loading state (doesn't prevent submission)
        submitButton.disabled = true;
        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Signing in...';
        
        // Add loading class for additional visual effects
        submitButton.classList.add('btn-loading');
        
        // Reset button state after a delay (in case submission fails)
        setTimeout(() => {
            submitButton.disabled = false;
            submitButton.innerHTML = originalContent;
            submitButton.classList.remove('btn-loading');
        }, 5000);
    });
}

/**
 * Initialize visual feedback for input validation
 */
function initInputValidationFeedback() {
    const inputs = document.querySelectorAll('input[type="email"], input[type="password"]');
    
    inputs.forEach(input => {
        // Visual feedback on focus
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('input-focused');
            
            // Basic visual validation (doesn't affect form submission)
            if (this.type === 'email' && this.value) {
                const isValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this.value);
                this.classList.toggle('is-valid-visual', isValid);
                this.classList.toggle('is-invalid-visual', !isValid);
            }
            
            if (this.type === 'password' && this.value) {
                const hasMinLength = this.value.length >= 6;
                this.classList.toggle('is-valid-visual', hasMinLength);
                this.classList.toggle('is-invalid-visual', !hasMinLength);
            }
        });
        
        // Remove visual validation classes on input
        input.addEventListener('input', function() {
            this.classList.remove('is-valid-visual', 'is-invalid-visual');
        });
    });
}

// CSS styles injected for visual enhancements
const styles = `
<style>
/* Page load animation */
body.fade-in {
    animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Input focus enhancement */
.input-focused {
    transform: scale(1.01);
    transition: transform 0.2s ease;
}

/* Visual validation styles (non-intrusive) */
.is-valid-visual {
    border-color: #20c997 !important;
    box-shadow: 0 0 0 0.125rem rgba(32, 201, 151, 0.25) !important;
}

.is-invalid-visual {
    border-color: #fd7e14 !important;
    box-shadow: 0 0 0 0.125rem rgba(253, 126, 20, 0.25) !important;
}

/* Button loading state */
.btn-loading {
    position: relative;
    pointer-events: none;
}

/* Password toggle button hover effect */
.btn-link:hover i {
    color: var(--tblr-primary) !important;
    transition: color 0.2s ease;
}

/* Smooth transitions for all interactive elements */
input, button {
    transition: all 0.2s ease;
}
</style>
`;

// Inject styles
document.head.insertAdjacentHTML('beforeend', styles);