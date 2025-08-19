/**
 * FilterComponent - Reusable GitHub-style filter functionality
 * Handles both server-side (URL) and client-side (AJAX) filtering
 */
window.FilterComponent = (function() {
    'use strict';

    let config = {};
    let searchComponent;

    // Default configuration
    const defaultConfig = {
        filterClass: 'github-filter-btn',
        mode: 'server', // 'server' or 'ajax'
        preserveScrollPosition: true,
        enableSearchPreservation: true
    };

    function init(userConfig = {}) {
        config = { ...defaultConfig, ...userConfig };
        
        // Get reference to search component if available
        searchComponent = window.SearchComponent;
        
        setupEventListeners();
        
        console.log('FilterComponent initialized in', config.mode, 'mode');
    }

    function setupEventListeners() {
        // Handle filter button clicks
        document.querySelectorAll(`.${config.filterClass}`).forEach(filterBtn => {
            filterBtn.addEventListener('click', function(e) {
                handleFilterClick(e, this);
            });
        });
    }

    function handleFilterClick(event, filterBtn) {
        if (config.mode === 'server') {
            handleServerFilter(event, filterBtn);
        } else if (config.mode === 'ajax') {
            handleAjaxFilter(event, filterBtn);
        }
    }

    function handleServerFilter(event, filterBtn) {
        // For server-side filtering, preserve search query when switching filters
        if (config.enableSearchPreservation && searchComponent) {
            const searchInput = document.getElementById('enhancedSearchInput');
            if (searchInput) {
                const currentQuery = searchInput.value.trim();
                if (currentQuery && currentQuery.length >= 3) {
                    const url = new URL(filterBtn.href);
                    url.searchParams.set('q', currentQuery);
                    filterBtn.href = url.toString();
                }
            }
        }

        // For scroll position preservation, we need to handle differently
        if (config.preserveScrollPosition) {
            // Store current scroll position
            sessionStorage.setItem('scrollPosition', window.scrollY.toString());
            
            // Let the browser navigate normally
            // On page load, the scroll position will be restored
            window.addEventListener('load', function() {
                const savedPosition = sessionStorage.getItem('scrollPosition');
                if (savedPosition) {
                    window.scrollTo(0, parseInt(savedPosition));
                    sessionStorage.removeItem('scrollPosition');
                }
            });
        }
        
        // Allow default navigation to proceed
    }

    function handleAjaxFilter(event, filterBtn) {
        // Prevent default navigation for AJAX filtering
        event.preventDefault();
        event.stopPropagation();

        // Extract filter information from the button
        const filterInfo = extractFilterInfo(filterBtn);
        if (!filterInfo) {
            console.warn('FilterComponent: Could not extract filter info');
            return;
        }

        // Update button states immediately for visual feedback
        updateButtonStates(filterBtn, filterInfo.type);

        // Determine which filter function to call based on the button ID or data attributes
        if (filterInfo.category === 'passport') {
            if (typeof window.filterPassports === 'function') {
                window.filterPassports(filterInfo.value);
            } else {
                console.error('FilterComponent: filterPassports function not found');
            }
        } else if (filterInfo.category === 'signup') {
            if (typeof window.filterSignups === 'function') {
                window.filterSignups(filterInfo.value);
            } else {
                console.error('FilterComponent: filterSignups function not found');
            }
        } else {
            // Generic AJAX filter handler
            performAjaxFilter(filterInfo);
        }

        return false;
    }

    function extractFilterInfo(filterBtn) {
        // Extract filter information from button ID, data attributes, or href
        const buttonId = filterBtn.id;
        const href = filterBtn.href;
        
        // Parse from button ID (e.g., "filter-unpaid", "signup-filter-paid")
        if (buttonId.includes('filter-')) {
            const parts = buttonId.split('-');
            if (parts.length >= 2) {
                if (buttonId.startsWith('signup-filter-')) {
                    return {
                        category: 'signup',
                        value: parts[2] || 'all',
                        type: parts[2] || 'all'
                    };
                } else if (buttonId.startsWith('filter-')) {
                    return {
                        category: 'passport',
                        value: parts[1] || 'all',
                        type: parts[1] || 'all'
                    };
                }
            }
        }

        // Parse from href if available
        if (href) {
            try {
                const url = new URL(href);
                const passportFilter = url.searchParams.get('passport_filter');
                const signupFilter = url.searchParams.get('signup_filter');
                const status = url.searchParams.get('status');
                const paymentStatus = url.searchParams.get('payment_status');

                if (passportFilter) {
                    return {
                        category: 'passport',
                        value: passportFilter,
                        type: passportFilter
                    };
                } else if (signupFilter) {
                    return {
                        category: 'signup',
                        value: signupFilter,
                        type: signupFilter
                    };
                } else if (status) {
                    return {
                        category: 'status',
                        value: status,
                        type: status
                    };
                } else if (paymentStatus) {
                    return {
                        category: 'payment',
                        value: paymentStatus,
                        type: paymentStatus
                    };
                }
            } catch (err) {
                console.warn('FilterComponent: Could not parse href', err);
            }
        }

        return null;
    }

    function updateButtonStates(activeBtn, filterType) {
        // Get all filter buttons in the same group
        const filterGroup = activeBtn.closest('.github-filter-group');
        if (filterGroup) {
            const buttons = filterGroup.querySelectorAll(`.${config.filterClass}`);
            buttons.forEach(btn => {
                btn.classList.remove('active');
            });
            activeBtn.classList.add('active');
        } else {
            // Fallback: find related buttons by similar IDs
            const category = extractFilterInfo(activeBtn)?.category;
            if (category === 'passport') {
                document.querySelectorAll('#filter-all, #filter-unpaid, #filter-paid, #filter-active').forEach(btn => {
                    btn.classList.remove('active');
                });
            } else if (category === 'signup') {
                document.querySelectorAll('#signup-filter-all, #signup-filter-unpaid, #signup-filter-paid, #signup-filter-pending, #signup-filter-approved').forEach(btn => {
                    btn.classList.remove('active');
                });
            }
            activeBtn.classList.add('active');
        }
    }

    function performAjaxFilter(filterInfo) {
        // Generic AJAX filter implementation
        console.log('FilterComponent: Performing AJAX filter', filterInfo);
        
        // This would be implemented based on specific needs
        // For now, log the action
        showFilterLoading(true);
        
        // Simulate filter delay
        setTimeout(() => {
            showFilterLoading(false);
            console.log('FilterComponent: Filter completed');
        }, 500);
    }

    function showFilterLoading(loading) {
        // Show/hide loading state for filters
        const tableContainers = document.querySelectorAll('.table-responsive');
        tableContainers.forEach(container => {
            if (loading) {
                container.style.opacity = '0.5';
                container.style.pointerEvents = 'none';
            } else {
                container.style.opacity = '1';
                container.style.pointerEvents = 'auto';
            }
        });
    }

    // Scroll position restoration for server-side filtering
    function initScrollRestoration() {
        // Restore scroll position if we came from a filter action
        document.addEventListener('DOMContentLoaded', function() {
            const savedPosition = sessionStorage.getItem('scrollPosition');
            if (savedPosition) {
                setTimeout(() => {
                    window.scrollTo(0, parseInt(savedPosition));
                    sessionStorage.removeItem('scrollPosition');
                }, 100); // Small delay to ensure page is fully loaded
            }
        });
    }

    // Initialize scroll restoration immediately
    if (config.preserveScrollPosition) {
        initScrollRestoration();
    }

    // Public API
    return {
        init: init,
        handleFilterClick: handleFilterClick,
        updateButtonStates: updateButtonStates,
        showFilterLoading: showFilterLoading
    };
})();