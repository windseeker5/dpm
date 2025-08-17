/**
 * SIMPLIFIED BULLETPROOF DROPDOWN FIX v3.0
 * 
 * This JavaScript ensures:
 * 1. Only one dropdown open at a time
 * 2. Click outside closes dropdowns
 * 3. Escape key closes dropdowns
 * 4. Proper cleanup and state management
 */

(function() {
    'use strict';
    
    let currentOpenDropdown = null;
    let initialized = false;
    
    console.log('🔧 Dropdown Fix v3.0 loading...');
    
    /**
     * Close all open dropdowns immediately
     */
    function closeAllDropdowns() {
        try {
            // Method 1: Close using Bootstrap API
            document.querySelectorAll('[data-bs-toggle="dropdown"][aria-expanded="true"]').forEach(toggle => {
                if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
                    const instance = bootstrap.Dropdown.getInstance(toggle);
                    if (instance) {
                        instance.hide();
                    }
                }
                // Fallback: manual close
                toggle.setAttribute('aria-expanded', 'false');
                toggle.classList.remove('show');
            });
            
            // Method 2: Manual cleanup for any remaining dropdowns
            document.querySelectorAll('.dropdown.show').forEach(dropdown => {
                dropdown.classList.remove('show');
                const menu = dropdown.querySelector('.dropdown-menu');
                if (menu) {
                    menu.classList.remove('show');
                    menu.style.display = 'none';
                }
            });
            
            // Method 3: Force close any orphaned menus
            document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                menu.classList.remove('show');
                menu.style.display = 'none';
            });
            
            // Reset state
            currentOpenDropdown = null;
            
            // console.log('🧹 All dropdowns closed');
            
        } catch (error) {
            console.warn('⚠️ Error closing dropdowns:', error);
            
            // Emergency cleanup
            document.querySelectorAll('.dropdown, .dropdown-menu').forEach(el => {
                el.classList.remove('show');
                if (el.classList.contains('dropdown-menu')) {
                    el.style.display = 'none';
                }
                if (el.hasAttribute('aria-expanded')) {
                    el.setAttribute('aria-expanded', 'false');
                }
            });
            currentOpenDropdown = null;
        }
    }
    
    /**
     * Handle click events to manage dropdown behavior
     */
    function handleDocumentClick(event) {
        const clickedToggle = event.target.closest('[data-bs-toggle="dropdown"]');
        const clickedDropdown = event.target.closest('.dropdown');
        const clickedMenuItem = event.target.closest('.dropdown-item');
        
        // If clicked on a dropdown toggle
        if (clickedToggle) {
            const parentDropdown = clickedToggle.closest('.dropdown');
            
            // If opening a different dropdown, close current one first
            if (currentOpenDropdown && parentDropdown !== currentOpenDropdown) {
                closeAllDropdowns();
            }
            
            // Let Bootstrap handle the toggle, but track state
            setTimeout(() => {
                const isOpen = parentDropdown.classList.contains('show');
                if (isOpen) {
                    currentOpenDropdown = parentDropdown;
                    // console.log('📂 Dropdown opened:', parentDropdown);
                    
                    // Ensure menu is visible (nuclear approach)
                    const menu = parentDropdown.querySelector('.dropdown-menu');
                    if (menu) {
                        menu.style.display = 'block';
                        menu.style.opacity = '1';
                        menu.style.visibility = 'visible';
                        menu.style.pointerEvents = 'auto';
                        
                        // Fix positioning for edge cases
                        const rect = menu.getBoundingClientRect();
                        if (rect.right > window.innerWidth - 20) {
                            menu.classList.add('dropdown-menu-end');
                        }
                    }
                } else {
                    currentOpenDropdown = null;
                }
            }, 50);
            
            return;
        }
        
        // If clicked on a dropdown item, close dropdown
        if (clickedMenuItem) {
            setTimeout(() => closeAllDropdowns(), 100);
            return;
        }
        
        // If clicked inside dropdown menu (but not on an item), do nothing
        if (clickedDropdown && event.target.closest('.dropdown-menu')) {
            return;
        }
        
        // If clicked outside any dropdown, close all
        if (!clickedDropdown) {
            closeAllDropdowns();
        }
    }
    
    /**
     * Handle escape key
     */
    function handleKeydown(event) {
        if (event.key === 'Escape' || event.keyCode === 27) {
            closeAllDropdowns();
            event.preventDefault();
        }
    }
    
    /**
     * Initialize Bootstrap dropdown instances and event listeners
     */
    function initialize() {
        if (initialized) {
            console.log('🔄 Dropdown fix already initialized');
            return;
        }
        
        // Wait for Bootstrap
        if (typeof bootstrap === 'undefined') {
            console.log('⏳ Waiting for Bootstrap...');
            setTimeout(initialize, 100);
            return;
        }
        
        // console.log('🚀 Initializing dropdown fix...');
        
        // Remove existing listeners to prevent duplicates
        document.removeEventListener('click', handleDocumentClick, true);
        document.removeEventListener('keydown', handleKeydown, true);
        
        // Add global event listeners
        document.addEventListener('click', handleDocumentClick, true);
        document.addEventListener('keydown', handleKeydown, true);
        
        // Initialize all existing dropdown toggles
        document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(toggle => {
            if (!bootstrap.Dropdown.getInstance(toggle)) {
                new bootstrap.Dropdown(toggle);
            }
        });
        
        // Listen for Bootstrap dropdown events
        document.addEventListener('show.bs.dropdown', function(event) {
            const dropdown = event.target.closest('.dropdown');
            
            // Close any other open dropdown first
            if (currentOpenDropdown && currentOpenDropdown !== dropdown) {
                closeAllDropdowns();
            }
        });
        
        document.addEventListener('shown.bs.dropdown', function(event) {
            const dropdown = event.target.closest('.dropdown');
            currentOpenDropdown = dropdown;
            
            // Force menu visibility
            const menu = dropdown.querySelector('.dropdown-menu');
            if (menu) {
                menu.style.display = 'block';
                menu.style.opacity = '1';
                menu.style.visibility = 'visible';
                
                // Auto-position for viewport edges
                setTimeout(() => {
                    const rect = menu.getBoundingClientRect();
                    if (rect.right > window.innerWidth - 20) {
                        menu.classList.add('dropdown-menu-end');
                    }
                    if (rect.bottom > window.innerHeight - 20) {
                        menu.style.top = 'auto';
                        menu.style.bottom = '100%';
                    }
                }, 10);
            }
            
            // console.log('✅ Dropdown shown:', dropdown);
        });
        
        document.addEventListener('hidden.bs.dropdown', function(event) {
            const dropdown = event.target.closest('.dropdown');
            if (currentOpenDropdown === dropdown) {
                currentOpenDropdown = null;
            }
            // console.log('✅ Dropdown hidden:', dropdown);
        });
        
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                closeAllDropdowns();
            }
        });
        
        // Set up DOM observer for dynamically added dropdowns
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver(mutations => {
                let needsInit = false;
                
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) {
                            if (node.matches && node.matches('[data-bs-toggle="dropdown"]')) {
                                needsInit = true;
                            } else if (node.querySelector && node.querySelector('[data-bs-toggle="dropdown"]')) {
                                needsInit = true;
                            }
                        }
                    });
                });
                
                if (needsInit) {
                    setTimeout(() => {
                        document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(toggle => {
                            if (!bootstrap.Dropdown.getInstance(toggle)) {
                                new bootstrap.Dropdown(toggle);
                            }
                        });
                    }, 50);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
        
        initialized = true;
        console.log('✅ Dropdown Fix v3.0 initialized');
        
        // Debug helper - run window.dropdownFix.debug() in console to see dropdown state
        // console.log('💡 To debug dropdowns, run: window.dropdownFix.debug()');
        
        // Continuous monitoring for broken dropdowns
        setInterval(() => {
            // Find dropdowns that should be visible but aren't
            document.querySelectorAll('.dropdown.show .dropdown-menu').forEach(menu => {
                const computed = window.getComputedStyle(menu);
                if (computed.display === 'none' || computed.opacity === '0' || computed.visibility === 'hidden') {
                    // console.log('🔧 Fixing broken dropdown menu visibility');
                    menu.style.display = 'block';
                    menu.style.opacity = '1';
                    menu.style.visibility = 'visible';
                    menu.style.pointerEvents = 'auto';
                }
            });
        }, 100);
    }
    
    // Global API for debugging and manual control
    window.dropdownFix = {
        closeAll: closeAllDropdowns,
        reinit: initialize,
        getCurrentOpen: () => currentOpenDropdown,
        getOpenCount: () => document.querySelectorAll('.dropdown.show').length,
        isInitialized: () => initialized,
        debug: () => {
            console.group('🔍 Dropdown Fix Debug');
            console.log('Initialized:', initialized);
            console.log('Current open:', currentOpenDropdown);
            console.log('Open count:', document.querySelectorAll('.dropdown.show').length);
            console.log('Bootstrap available:', typeof bootstrap !== 'undefined');
            
            const openDropdowns = document.querySelectorAll('.dropdown.show');
            openDropdowns.forEach((dropdown, i) => {
                console.log(`Open dropdown ${i + 1}:`, dropdown);
                const menu = dropdown.querySelector('.dropdown-menu');
                if (menu) {
                    const styles = window.getComputedStyle(menu);
                    console.log(`  Menu styles:`, {
                        display: styles.display,
                        opacity: styles.opacity,
                        visibility: styles.visibility,
                        zIndex: styles.zIndex
                    });
                }
            });
            console.groupEnd();
        }
    };
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        // DOM already loaded
        setTimeout(initialize, 100);
    }
    
    console.log('🎯 Dropdown Fix v3.0 loaded');
    
})();