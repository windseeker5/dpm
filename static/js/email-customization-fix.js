// Simple image upload handler for email customization
document.addEventListener('DOMContentLoaded', function() {
    // Handle hero image file selection
    document.querySelectorAll('.hero-upload').forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            // Show preview
            const reader = new FileReader();
            const templateKey = this.dataset.templateKey;
            reader.onload = function(e) {
                const preview = document.getElementById(`hero-preview-${templateKey}`);
                if (preview) {
                    preview.querySelector('img').src = e.target.result;
                }
            };
            reader.readAsDataURL(file);
        });
    });
    
    // Handle owner logo file selection
    document.querySelectorAll('.owner-logo-upload').forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;
            
            // Show preview
            const reader = new FileReader();
            const templateKey = this.dataset.templateKey;
            reader.onload = function(e) {
                const preview = document.getElementById(`owner-logo-preview-${templateKey}`);
                if (preview) {
                    preview.querySelector('img').src = e.target.result;
                }
            };
            reader.readAsDataURL(file);
        });
    });
});