/**
 * Email Settings JavaScript Module
 * Handles client-side validation, form submission, and user feedback for email configuration
 * Compatible with organization-specific email setups and Sender Name field
 */

class EmailSettingsManager {
    constructor() {
        this.isTestingConnection = false;
        this.validationErrors = new Map();
        this.init();
    }

    init() {
        this.bindEventListeners();
        this.initializeValidation();
        this.setupDependentFieldsVisibility();
    }

    bindEventListeners() {
        // Email form submission
        const emailForm = document.querySelector('form[method="POST"]');
        if (emailForm) {
            emailForm.addEventListener('submit', this.handleFormSubmit.bind(this));
        }

        // Real-time validation on input change
        this.bindFieldValidation('input[name="mail_server"]', this.validateMailServer.bind(this));
        this.bindFieldValidation('input[name="mail_port"]', this.validateMailPort.bind(this));
        this.bindFieldValidation('input[name="mail_username"]', this.validateEmailUsername.bind(this));
        this.bindFieldValidation('input[name="mail_default_sender"]', this.validateDefaultSender.bind(this));
        this.bindFieldValidation('input[name="mail_sender_name"]', this.validateSenderName.bind(this));

        // Test connection button
        const testButton = this.createTestConnectionButton();
        if (testButton) {
            this.insertTestButton(testButton);
        }

        // Organization domain validation
        this.bindOrganizationDomainValidation();
    }

    bindFieldValidation(selector, validator) {
        const field = document.querySelector(selector);
        if (field) {
            field.addEventListener('blur', validator);
            field.addEventListener('input', () => {
                // Clear error state on typing
                this.clearFieldError(field);
            });
        }
    }

    validateMailServer(event) {
        const field = event.target;
        const value = field.value.trim();
        
        // Clear previous errors
        this.clearFieldError(field);

        if (!value) {
            this.setFieldError(field, 'Mail server is required');
            return false;
        }

        // Validate SMTP server format
        const smtpPattern = /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;
        if (!smtpPattern.test(value)) {
            this.setFieldError(field, 'Please enter a valid SMTP server address');
            return false;
        }

        // Suggest common SMTP configurations
        this.suggestSMTPConfiguration(field, value);
        return true;
    }

    validateMailPort(event) {
        const field = event.target;
        const value = parseInt(field.value);
        
        this.clearFieldError(field);

        if (!value || value < 1 || value > 65535) {
            this.setFieldError(field, 'Please enter a valid port number (1-65535)');
            return false;
        }

        // Warn about non-standard ports
        const standardPorts = [25, 587, 465, 2525];
        if (!standardPorts.includes(value)) {
            this.setFieldWarning(field, `Port ${value} is not a standard SMTP port. Common ports: 587 (TLS), 465 (SSL), 25 (unsecured)`);
        }

        return true;
    }

    validateEmailUsername(event) {
        const field = event.target;
        const value = field.value.trim();
        
        this.clearFieldError(field);

        if (!value) {
            this.setFieldError(field, 'Email username is required');
            return false;
        }

        // Basic email format validation
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(value)) {
            this.setFieldError(field, 'Please enter a valid email address');
            return false;
        }

        return true;
    }

    validateDefaultSender(event) {
        const field = event.target;
        const value = field.value.trim();
        
        this.clearFieldError(field);

        if (!value) {
            this.setFieldError(field, 'Default sender email is required');
            return false;
        }

        // Validate email format
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(value)) {
            this.setFieldError(field, 'Please enter a valid email address');
            return false;
        }

        return true;
    }

    validateSenderName(event) {
        const field = event.target;
        const value = field.value.trim();
        
        this.clearFieldError(field);

        if (value && value.length > 100) {
            this.setFieldError(field, 'Sender name must be 100 characters or less');
            return false;
        }

        return true;
    }

    bindOrganizationDomainValidation() {
        const senderField = document.querySelector('input[name="mail_default_sender"]');
        const usernameField = document.querySelector('input[name="mail_username"]');
        
        if (senderField && usernameField) {
            const validateOrgDomain = () => {
                const senderEmail = senderField.value.trim();
                const usernameEmail = usernameField.value.trim();
                
                if (senderEmail && usernameEmail) {
                    // Check if using organization domain (@minipass.me)
                    if (senderEmail.endsWith('@minipass.me')) {
                        this.setFieldInfo(senderField, 'Using organization domain - ensure your email server is configured for @minipass.me');
                    }
                    
                    // Warn if sender and username domains don't match
                    const senderDomain = senderEmail.split('@')[1];
                    const usernameDomain = usernameEmail.split('@')[1];
                    
                    if (senderDomain && usernameDomain && senderDomain !== usernameDomain) {
                        this.setFieldWarning(senderField, 'Sender domain differs from username domain. Ensure your SMTP server allows this configuration.');
                    }
                }
            };

            senderField.addEventListener('blur', validateOrgDomain);
            usernameField.addEventListener('blur', validateOrgDomain);
        }
    }

    suggestSMTPConfiguration(field, server) {
        const commonConfigs = {
            'smtp.gmail.com': { port: 587, tls: true, note: 'Gmail SMTP' },
            'smtp.outlook.com': { port: 587, tls: true, note: 'Outlook/Hotmail SMTP' },
            'smtp.yahoo.com': { port: 587, tls: true, note: 'Yahoo SMTP' },
            'mail.privateemail.com': { port: 587, tls: true, note: 'Namecheap Private Email' }
        };

        const config = commonConfigs[server.toLowerCase()];
        if (config) {
            this.setFieldInfo(field, `${config.note} - Suggested port: ${config.port}, TLS: ${config.tls ? 'Yes' : 'No'}`);
        }
    }

    createTestConnectionButton() {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-outline-primary btn-sm ms-2';
        button.innerHTML = '<i class="ti ti-plug me-1"></i>Test Connection';
        button.addEventListener('click', this.testEmailConnection.bind(this));
        return button;
    }

    insertTestButton(testButton) {
        const mailServerField = document.querySelector('input[name="mail_server"]');
        if (mailServerField && mailServerField.parentNode) {
            const serverContainer = mailServerField.parentNode;
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'mt-2';
            buttonContainer.appendChild(testButton);
            serverContainer.appendChild(buttonContainer);
        }
    }

    async testEmailConnection() {
        if (this.isTestingConnection) return;

        const testButton = document.querySelector('button:has(.ti-plug)');
        if (!testButton) return;

        this.isTestingConnection = true;
        
        // Update button state
        const originalHTML = testButton.innerHTML;
        testButton.innerHTML = '<i class="ti ti-loader-2 spin me-1"></i>Testing...';
        testButton.disabled = true;

        try {
            const formData = this.gatherEmailSettings();
            
            const response = await fetch('/api/test-email-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(formData)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showAlert('success', 'Email connection test successful!', 'Your email server configuration is working correctly.');
            } else {
                this.showAlert('danger', 'Email connection test failed', result.error || 'Unable to connect to email server. Please check your settings.');
            }
        } catch (error) {
            console.error('Email connection test error:', error);
            this.showAlert('danger', 'Connection test error', 'Unable to test email connection. Please try again later.');
        } finally {
            // Restore button state
            testButton.innerHTML = originalHTML;
            testButton.disabled = false;
            this.isTestingConnection = false;
        }
    }

    gatherEmailSettings() {
        return {
            mail_server: document.querySelector('input[name="mail_server"]')?.value || '',
            mail_port: parseInt(document.querySelector('input[name="mail_port"]')?.value) || 587,
            mail_use_tls: document.querySelector('input[name="mail_use_tls"]')?.checked || false,
            mail_username: document.querySelector('input[name="mail_username"]')?.value || '',
            mail_password: document.querySelector('input[name="mail_password_raw"]')?.value || '',
            mail_default_sender: document.querySelector('input[name="mail_default_sender"]')?.value || '',
            mail_sender_name: document.querySelector('input[name="mail_sender_name"]')?.value || ''
        };
    }

    handleFormSubmit(event) {
        // Validate all fields before submission
        const isValid = this.validateAllFields();
        
        if (!isValid) {
            event.preventDefault();
            this.showAlert('warning', 'Validation Failed', 'Please correct the errors before saving.');
            return false;
        }

        // Show loading state
        this.showSubmissionLoading(event.target);
        
        // Allow form to submit normally
        return true;
    }

    validateAllFields() {
        const fields = [
            { selector: 'input[name="mail_server"]', validator: this.validateMailServer.bind(this) },
            { selector: 'input[name="mail_port"]', validator: this.validateMailPort.bind(this) },
            { selector: 'input[name="mail_username"]', validator: this.validateEmailUsername.bind(this) },
            { selector: 'input[name="mail_default_sender"]', validator: this.validateDefaultSender.bind(this) },
            { selector: 'input[name="mail_sender_name"]', validator: this.validateSenderName.bind(this) }
        ];

        let allValid = true;

        fields.forEach(fieldConfig => {
            const field = document.querySelector(fieldConfig.selector);
            if (field) {
                const isValid = fieldConfig.validator({ target: field });
                if (!isValid) allValid = false;
            }
        });

        return allValid;
    }

    showSubmissionLoading(form) {
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            const originalHTML = submitButton.innerHTML;
            submitButton.innerHTML = '<i class="ti ti-loader-2 spin me-2"></i>Saving Settings...';
            submitButton.disabled = true;

            // Store original HTML for potential restoration
            submitButton.dataset.originalHtml = originalHTML;
        }
    }

    setupDependentFieldsVisibility() {
        // Toggle Email Payment Bot configuration
        const toggle = document.getElementById("enable_email_payment_bot");
        const configSection = document.getElementById("email-bot-config");

        if (toggle && configSection) {
            const updateVisibility = () => {
                configSection.style.display = toggle.checked ? "block" : "none";
            };

            toggle.addEventListener("change", updateVisibility);
            updateVisibility(); // Initial state
        }
    }

    initializeValidation() {
        // Add visual indicators for required fields
        const requiredFields = document.querySelectorAll('input[required]');
        requiredFields.forEach(field => {
            const label = field.parentNode.querySelector('.form-label');
            if (label && !label.querySelector('.text-danger')) {
                label.innerHTML += ' <span class="text-danger">*</span>';
            }
        });
    }

    // Utility methods for field feedback
    setFieldError(field, message) {
        this.setFieldFeedback(field, message, 'error');
        field.classList.add('is-invalid');
        field.classList.remove('is-valid');
        this.validationErrors.set(field.name, message);
    }

    setFieldWarning(field, message) {
        this.setFieldFeedback(field, message, 'warning');
        field.classList.remove('is-invalid', 'is-valid');
    }

    setFieldInfo(field, message) {
        this.setFieldFeedback(field, message, 'info');
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid', 'is-valid');
        this.clearFieldFeedback(field);
        this.validationErrors.delete(field.name);
    }

    setFieldFeedback(field, message, type) {
        this.clearFieldFeedback(field);
        
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = `form-text text-${this.getFeedbackClass(type)}`;
        feedbackDiv.textContent = message;
        feedbackDiv.setAttribute('data-feedback-type', type);
        
        field.parentNode.appendChild(feedbackDiv);
    }

    clearFieldFeedback(field) {
        const existingFeedback = field.parentNode.querySelector('[data-feedback-type]');
        if (existingFeedback) {
            existingFeedback.remove();
        }
    }

    getFeedbackClass(type) {
        const classes = {
            'error': 'danger',
            'warning': 'warning',
            'info': 'muted',
            'success': 'success'
        };
        return classes[type] || 'muted';
    }

    showAlert(type, title, message) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.email-settings-alert');
        existingAlerts.forEach(alert => alert.remove());

        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible email-settings-alert`;
        alertDiv.innerHTML = `
            <div class="d-flex">
                <div>
                    <i class="ti ti-${this.getAlertIcon(type)} me-2"></i>
                </div>
                <div>
                    <h4 class="alert-title">${title}</h4>
                    <div class="text-muted">${message}</div>
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert alert at the top of the email settings section
        const emailSettingsSection = document.querySelector('h3') || document.querySelector('.card-body');
        if (emailSettingsSection) {
            emailSettingsSection.parentNode.insertBefore(alertDiv, emailSettingsSection);
        }

        // Auto-remove success alerts after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    getAlertIcon(type) {
        const icons = {
            'success': 'check-circle',
            'danger': 'alert-circle',
            'warning': 'alert-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getCSRFToken() {
        const csrfInput = document.querySelector('input[name="csrf_token"]');
        return csrfInput ? csrfInput.value : '';
    }
}

// Initialize email settings manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new EmailSettingsManager();
});