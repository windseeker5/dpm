/**
 * Global Dropdown Fix for Tabler.io/Bootstrap 5 Dropdowns
 * 
 * This module fixes dropdown display issues in tables where clicking dropdowns
 * in sequence (especially from bottom to top) causes display problems.
 * 
 * Features:
 * - Ensures only one dropdown is open at a time
 * - Fixes positioning issues in table cells
 * - Handles click-outside to close dropdowns
 * - Compatible with dynamic content (AJAX loaded)
 * 
 * Usage: Simply include this file in your base template
 * No additional initialization required - it auto-initializes on DOM ready
 */

(function() {
    'use strict';
    
    // Track currently open dropdown
    let currentOpenDropdown = null;
    
    /**
     * Close all open dropdowns on the page
     */
    function closeAllDropdowns() {
        document.querySelectorAll('.dropdown.show').forEach(dropdown => {
            const toggle = dropdown.querySelector('[data-bs-toggle="dropdown"]');
            if (toggle && typeof bootstrap !== 'undefined') {
                const instance = bootstrap.Dropdown.getInstance(toggle);
                if (instance) {
                    instance.hide();
                }
            }
            // Remove show class as fallback
            dropdown.classList.remove('show');
        });
        currentOpenDropdown = null;
    }
    
    /**
     * Initialize dropdown fix handlers
     */
    function initDropdownFix() {
        // Check if Bootstrap is available
        if (typeof bootstrap === 'undefined') {
            console.warn('Bootstrap not loaded. Dropdown fix waiting...');
            setTimeout(initDropdownFix, 100);
            return;
        }
        
        // Handle dropdown show event
        document.addEventListener('show.bs.dropdown', function(e) {
            // Close any previously open dropdown first
            if (currentOpenDropdown && currentOpenDropdown !== e.target) {
                closeAllDropdowns();
            }
            
            // Set current dropdown
            const dropdownElement = e.target.closest('.dropdown');
            if (dropdownElement) {
                currentOpenDropdown = dropdownElement;
                
                // Ensure parent containers allow overflow
                let parent = dropdownElement.parentElement;
                while (parent && parent !== document.body) {
                    if (parent.tagName === 'TD' || parent.tagName === 'TH') {
                        parent.style.overflow = 'visible';
                        parent.style.position = 'relative';
                    }
                    parent = parent.parentElement;
                }
            }
        });
        
        // Handle dropdown shown event (after animation)
        document.addEventListener('shown.bs.dropdown', function(e) {
            const dropdownElement = e.target.closest('.dropdown');
            if (dropdownElement) {
                dropdownElement.classList.add('show');
                
                // Force position recalculation for table dropdowns
                const menu = dropdownElement.querySelector('.dropdown-menu');
                if (menu) {
                    // Ensure menu is visible
                    menu.style.display = 'block';
                    menu.style.opacity = '1';
                    
                    // Check if dropdown is in a table
                    const inTable = dropdownElement.closest('table');
                    if (inTable) {
                        // Calculate optimal position
                        const rect = dropdownElement.getBoundingClientRect();
                        const menuRect = menu.getBoundingClientRect();
                        const viewportHeight = window.innerHeight;
                        
                        // If menu would extend below viewport, position it above
                        if (rect.bottom + menuRect.height > viewportHeight - 20) {
                            menu.classList.add('dropdown-menu-up');
                        } else {
                            menu.classList.remove('dropdown-menu-up');
                        }
                    }
                }
            }
        });
        
        // Handle dropdown hide event
        document.addEventListener('hide.bs.dropdown', function(e) {
            const dropdownElement = e.target.closest('.dropdown');
            if (dropdownElement) {
                dropdownElement.classList.remove('show');
                
                // Reset parent overflow
                let parent = dropdownElement.parentElement;
                while (parent && parent !== document.body) {
                    if (parent.tagName === 'TD' || parent.tagName === 'TH') {
                        parent.style.overflow = '';
                        parent.style.position = '';
                    }
                    parent = parent.parentElement;
                }
            }
            
            if (currentOpenDropdown === dropdownElement) {
                currentOpenDropdown = null;
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (currentOpenDropdown && !currentOpenDropdown.contains(e.target)) {
                closeAllDropdowns();
            }
        });
        
        // Handle escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && currentOpenDropdown) {
                closeAllDropdowns();
            }
        });
        
        // Re-initialize on dynamic content load (for AJAX)
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.addedNodes.length) {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1 && node.querySelector && node.querySelector('[data-bs-toggle="dropdown"]')) {
                                // New dropdown added, ensure it works correctly
                                const dropdowns = node.querySelectorAll('[data-bs-toggle="dropdown"]');
                                dropdowns.forEach(function(dropdown) {
                                    if (!bootstrap.Dropdown.getInstance(dropdown)) {
                                        new bootstrap.Dropdown(dropdown);
                                    }
                                });
                            }
                        });
                    }
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initDropdownFix);
    } else {
        // DOM already loaded
        initDropdownFix();
    }
    
    // Expose functions globally for debugging
    window.dropdownFix = {
        closeAllDropdowns: closeAllDropdowns,
        reinit: initDropdownFix
    };
    
})();