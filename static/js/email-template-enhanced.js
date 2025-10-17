/**
 * Enhanced Email Template Editor
 * Fixes common input issues and improves user experience
 */

// Enhanced email template functionality
(function() {
    'use strict';
    
    console.log('🔧 Enhanced email template system loading...');
    
    // Enhanced TinyMCE initialization with error handling
    function initEnhancedTinyMCE(selector = '#customizeModal textarea.tinymce') {
        if (typeof tinymce === 'undefined') {
            console.warn('TinyMCE not loaded - falling back to plain textareas');
            return false;
        }
        
        try {
            // Remove any existing instances
            tinymce.remove(selector);
            
            // Initialize with enhanced config
            tinymce.init({
                selector: selector,
                height: 250,
                menubar: false,
                plugins: 'lists link autoresize paste',
                toolbar: 'bold italic | bullist numlist | link | removeformat',
                autoresize_bottom_margin: 20,
                paste_as_text: true,
                setup: function(editor) {
                    editor.on('init', function() {
                        console.log('✅ TinyMCE initialized for:', editor.id);
                    });
                    
                    editor.on('change', function() {
                        // Auto-save indicator could go here
                    });
                }
            });
            
            return true;
        } catch (error) {
            console.error('TinyMCE initialization failed:', error);
            return false;
        }
    }
    
    // Enhanced form validation
    function validateEmailTemplateForm(formData, templateType) {
        const errors = [];
        
        // Check required fields
        const subject = formData.get(`${templateType}_subject`);
        const title = formData.get(`${templateType}_title`);
        
        if (!subject || subject.trim().length === 0) {
            errors.push('Email subject is required');
        }
        
        if (!title || title.trim().length === 0) {
            errors.push('Email title is required');
        }
        
        // Check for reasonable length limits
        if (subject && subject.length > 200) {
            errors.push('Email subject is too long (max 200 characters)');
        }
        
        return errors;
    }
    
    // Enhanced save functionality with better error handling
    async function saveTemplateEnhanced(templateType) {
        console.log('💾 Saving template:', templateType);
        
        try {
            const formData = new FormData();
            formData.append('csrf_token', document.querySelector('input[name="csrf_token"]')?.value || '');
            formData.append('single_template', templateType);
            
            // Get field values with fallbacks
            const subjectInput = document.querySelector(`#modal_${templateType}_subject`);
            const titleInput = document.querySelector(`#modal_${templateType}_title`);
            
            if (subjectInput) formData.append(`${templateType}_subject`, subjectInput.value);
            if (titleInput) formData.append(`${templateType}_title`, titleInput.value);
            
            // Get TinyMCE content with error handling
            if (typeof tinymce !== 'undefined') {
                const introEditor = tinymce.get(`modal_${templateType}_intro_text`);
                const conclusionEditor = tinymce.get(`modal_${templateType}_conclusion_text`);
                
                if (introEditor) {
                    formData.append(`${templateType}_intro_text`, introEditor.getContent());
                } else {
                    // Fallback to textarea value
                    const introTextarea = document.querySelector(`#modal_${templateType}_intro_text`);
                    if (introTextarea) formData.append(`${templateType}_intro_text`, introTextarea.value);
                }
                
                if (conclusionEditor) {
                    formData.append(`${templateType}_conclusion_text`, conclusionEditor.getContent());
                } else {
                    // Fallback to textarea value
                    const conclusionTextarea = document.querySelector(`#modal_${templateType}_conclusion_text`);
                    if (conclusionTextarea) formData.append(`${templateType}_conclusion_text`, conclusionTextarea.value);
                }
            }
            
            // Get file inputs
            const heroImageInput = document.querySelector(`#modal_${templateType}_hero_image`);
            const ownerLogoInput = document.querySelector(`#modal_${templateType}_owner_logo`);
            
            if (heroImageInput?.files[0]) {
                formData.append(`${templateType}_hero_image`, heroImageInput.files[0]);
            }
            if (ownerLogoInput?.files[0]) {
                formData.append(`${templateType}_owner_logo`, ownerLogoInput.files[0]);
            }
            
            // Validate before sending
            const errors = validateEmailTemplateForm(formData, templateType);
            if (errors.length > 0) {
                alert('Please fix the following errors:\n' + errors.join('\n'));
                return false;
            }
            
            // Show loading state
            const saveBtn = document.querySelector('#saveTemplateChanges');
            const originalText = saveBtn.innerHTML;
            saveBtn.innerHTML = '<i class="ti ti-loader-2 me-2"></i>Saving...';
            saveBtn.disabled = true;
            
            // Send request
            const response = await fetch(`/activity/${window.currentActivityId}/email-templates/save`, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            // Restore button state
            saveBtn.innerHTML = originalText;
            saveBtn.disabled = false;
            
            if (result.success) {
                console.log('✅ Template saved successfully');
                
                // Show success message
                const successMsg = document.createElement('div');
                successMsg.className = 'alert alert-success';
                successMsg.innerHTML = '<i class="ti ti-check me-2"></i>Template saved successfully!';
                
                const modalBody = document.querySelector('#customizeModal .modal-body');
                modalBody.insertBefore(successMsg, modalBody.firstChild);
                
                // Remove success message after 3 seconds
                setTimeout(() => successMsg.remove(), 3000);
                
                return true;
            } else {
                throw new Error(result.message || 'Save failed');
            }
            
        } catch (error) {
            console.error('❌ Save failed:', error);
            alert('Error saving template: ' + error.message);
            return false;
        }
    }
    
    // Enhanced preview functionality
    async function previewTemplateEnhanced(templateType) {
        console.log('👁️ Previewing template:', templateType);
        
        try {
            const formData = new FormData();
            formData.append('template_type', templateType);
            formData.append('csrf_token', document.querySelector('input[name="csrf_token"]')?.value || '');
            
            // Get current form values (same logic as save)
            const subjectInput = document.querySelector(`#modal_${templateType}_subject`);
            const titleInput = document.querySelector(`#modal_${templateType}_title`);
            
            if (subjectInput) formData.append(`${templateType}_subject`, subjectInput.value);
            if (titleInput) formData.append(`${templateType}_title`, titleInput.value);
            
            // Get TinyMCE content
            if (typeof tinymce !== 'undefined') {
                const introEditor = tinymce.get(`modal_${templateType}_intro_text`);
                const conclusionEditor = tinymce.get(`modal_${templateType}_conclusion_text`);
                
                if (introEditor) formData.append(`${templateType}_intro_text`, introEditor.getContent());
                if (conclusionEditor) formData.append(`${templateType}_conclusion_text`, conclusionEditor.getContent());
            }
            
            // Send preview request
            const response = await fetch(`/activity/${window.currentActivityId}/email-preview-live`, {
                method: 'POST',
                body: formData
            });
            
            const html = await response.text();

            // Create enhanced HTML with wrapper styling
            const enhancedHtml = `
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Email Preview - ${templateType}</title>
                    <style>
                        body { margin: 20px; background: #f5f5f5; font-family: Arial, sans-serif; }
                        .preview-wrapper { max-width: 800px; margin: 0 auto; background: white;
                                           padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                        .preview-header { text-align: center; padding: 10px 0; border-bottom: 1px solid #eee; margin-bottom: 20px; }
                    </style>
                </head>
                <body>
                    <div class="preview-wrapper">
                        <div class="preview-header">
                            <h3>📧 Email Preview: ${templateType}</h3>
                            <small>Generated at ${new Date().toLocaleString()}</small>
                        </div>
                        ${html}
                    </div>
                </body>
                </html>
            `;

            // Use blob URL with UTF-8 charset to handle French characters correctly
            const blob = new Blob([enhancedHtml], { type: 'text/html; charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const newTab = window.open(url, '_blank');

            // Clean up blob URL after browser loads it
            if (newTab) {
                setTimeout(() => URL.revokeObjectURL(url), 1000);
            }
            
            console.log('✅ Preview opened successfully');
            
        } catch (error) {
            console.error('❌ Preview failed:', error);
            alert('Error generating preview: ' + error.message);
        }
    }
    
    // DOM Ready initialization
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 Enhanced email template system ready');
        
        // Store activity ID for use in functions
        const activityMatch = window.location.pathname.match(/\/activity\/(\d+)/);
        if (activityMatch) {
            window.currentActivityId = activityMatch[1];
        }
        
        // Enhanced modal event handling
        document.addEventListener('click', function(e) {
            // Enhanced customize button
            if (e.target.closest('.customize-btn')) {
                const btn = e.target.closest('.customize-btn');
                const template = btn.dataset.template;
                const templateName = btn.dataset.templateName;
                
                console.log('🔧 Loading template customization:', template);
                
                // Load form content
                const formContent = document.getElementById(`form-template-${template}`);
                if (formContent) {
                    document.getElementById('customizeFormContent').innerHTML = formContent.innerHTML;
                    
                    // Update modal title
                    const modalTitle = document.getElementById('modalTemplateName');
                    if (modalTitle) {
                        modalTitle.textContent = templateName;
                    }
                    
                    // Initialize TinyMCE after a short delay
                    setTimeout(() => {
                        initEnhancedTinyMCE();
                    }, 200);
                }
            }
            
            // Enhanced save button
            if (e.target.id === 'saveTemplateChanges') {
                e.preventDefault();
                const activeSection = document.querySelector('.template-form-section[data-template]');
                if (activeSection) {
                    const templateType = activeSection.dataset.template;
                    saveTemplateEnhanced(templateType);
                }
            }
            
            // Enhanced preview button
            if (e.target.id === 'previewInModal') {
                e.preventDefault();
                const activeSection = document.querySelector('.template-form-section[data-template]');
                if (activeSection) {
                    const templateType = activeSection.dataset.template;
                    previewTemplateEnhanced(templateType);
                }
            }
        });
        
        // Enhanced image preview
        window.previewImageEnhanced = function(input, previewId) {
            if (input.files && input.files[0]) {
                const file = input.files[0];
                
                // Validate file type
                if (!file.type.startsWith('image/')) {
                    alert('Please select a valid image file');
                    input.value = '';
                    return;
                }
                
                // Validate file size (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    alert('Image file is too large. Please choose a file smaller than 5MB');
                    input.value = '';
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = function(e) {
                    const img = document.getElementById(previewId);
                    if (img) {
                        img.src = e.target.result;
                        img.style.border = '2px solid #28a745';
                        
                        // Add upload success indicator
                        const indicator = document.createElement('span');
                        indicator.className = 'badge bg-success ms-2';
                        indicator.innerHTML = '<i class="ti ti-check"></i> New';
                        indicator.style.position = 'absolute';
                        indicator.style.top = '5px';
                        indicator.style.right = '5px';
                        
                        const container = img.parentElement;
                        container.style.position = 'relative';
                        
                        // Remove any existing indicators
                        const existing = container.querySelector('.badge.bg-success');
                        if (existing) existing.remove();
                        
                        container.appendChild(indicator);
                    }
                };
                reader.readAsDataURL(file);
            }
        };
        
        // Override existing image preview function
        if (window.previewImage) {
            window.previewImage = window.previewImageEnhanced;
        }
    });
    
    console.log('✅ Enhanced email template system loaded successfully');
    
})();