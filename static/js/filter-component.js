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
        
        // Initialize scroll restoration if enabled
        if (config.preserveScrollPosition) {
            initScrollRestoration();
        }
        
        console.log('FilterComponent initialized in', config.mode, 'mode');
    }

    function setupEventListeners() {
        // Handle filter button clicks
        const filterButtons = document.querySelectorAll(`.${config.filterClass}`);
        console.log(`FilterComponent: Found ${filterButtons.length} filter buttons with class '${config.filterClass}'`);
        
        filterButtons.forEach(filterBtn => {
            // Remove any existing listeners to prevent duplicates
            filterBtn.removeEventListener('click', handleFilterClickWrapper);
            filterBtn.addEventListener('click', handleFilterClickWrapper);
            console.log(`FilterComponent: Added listener to button ${filterBtn.id || filterBtn.textContent.trim()}`);
        });
    }

    function handleFilterClickWrapper(e) {
        console.log(`FilterComponent: Button clicked in ${config.mode} mode:`, this.id || this.textContent.trim());
        const result = handleFilterClick(e, this);
        if (config.mode === 'ajax') {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }
        return result;
    }

    function handleFilterClick(event, filterBtn) {
        if (config.mode === 'server') {
            return handleServerFilter(event, filterBtn);
        } else if (config.mode === 'ajax') {
            return handleAjaxFilter(event, filterBtn);
        }
        return true;
    }

    function handleServerFilter(event, filterBtn) {
        // CRITICAL: Prevent default navigation so we can build correct URL with search preserved
        event.preventDefault();

        // Get original href and parse it
        const originalHref = filterBtn.href;
        const url = new URL(originalHref);

        // Remove the hash to prevent automatic scrolling to anchor
        const cleanUrl = url.origin + url.pathname + url.search;
        let finalUrl = cleanUrl;

        // For server-side filtering, preserve search query when switching filters
        if (config.enableSearchPreservation) {
            const searchInput = document.getElementById('enhancedSearchInput');
            if (searchInput) {
                const currentQuery = searchInput.value.trim();
                if (currentQuery && currentQuery.length >= 1) {
                    const newUrl = new URL(cleanUrl);
                    newUrl.searchParams.set('q', currentQuery);
                    finalUrl = newUrl.toString();
                    console.log('FilterComponent: Preserving search query:', currentQuery, 'in filter URL');
                }
            }
        }

        // Store scroll position with additional context for better restoration
        if (config.preserveScrollPosition) {
            const scrollY = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0;
            const timestamp = Date.now();
            const buttonId = filterBtn.id || 'unknown';

            // Store scroll data with metadata
            const scrollData = {
                position: scrollY,
                timestamp: timestamp,
                url: window.location.href,
                buttonId: buttonId,
                targetUrl: finalUrl
            };

            sessionStorage.setItem('filterScrollPosition', scrollY.toString());
            sessionStorage.setItem('filterScrollData', JSON.stringify(scrollData));

            console.log('FilterComponent: Stored scroll position', scrollY, 'for button', buttonId, 'navigating to', finalUrl);
        }

        // Navigate to the final URL with search preserved
        console.log('FilterComponent: Navigating to:', finalUrl);
        window.location.href = finalUrl;

        // Return false to ensure no default navigation
        return false;
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

    // Robust scroll position restoration for server-side filtering
    function initScrollRestoration() {
        const restoreScroll = () => {
            const savedPosition = sessionStorage.getItem('filterScrollPosition');
            const savedData = sessionStorage.getItem('filterScrollData');
            
            if (savedPosition) {
                const targetY = parseInt(savedPosition);
                let buttonId = 'unknown';
                
                // Get additional context if available
                if (savedData) {
                    try {
                        const data = JSON.parse(savedData);
                        buttonId = data.buttonId || 'unknown';
                        
                        // Check if data is recent (within last 10 seconds)
                        if (Date.now() - data.timestamp > 10000) {
                            console.log('FilterComponent: Scroll data too old, ignoring');
                            sessionStorage.removeItem('filterScrollPosition');
                            sessionStorage.removeItem('filterScrollData');
                            return;
                        }
                    } catch (e) {
                        console.warn('FilterComponent: Could not parse scroll data');
                    }
                }
                
                // Robust scroll restoration with multiple attempts
                const attemptRestore = (attempt = 1, maxAttempts = 15) => {
                    // Ensure page is fully loaded before scrolling
                    const isPageReady = document.readyState === 'complete' && 
                                       document.body && 
                                       document.body.scrollHeight > 100;
                    
                    if (isPageReady) {
                        // Use multiple scroll methods for maximum compatibility
                        try {
                            // Force immediate scroll without smooth behavior
                            window.scrollTo({
                                top: targetY,
                                left: 0,
                                behavior: 'instant'
                            });
                            
                            // Fallback for older browsers
                            if (Math.abs(window.scrollY - targetY) > 20) {
                                document.documentElement.scrollTop = targetY;
                                document.body.scrollTop = targetY;
                                
                                // Force a second attempt if still not correct
                                setTimeout(() => {
                                    if (Math.abs(window.scrollY - targetY) > 20) {
                                        window.scrollTo(0, targetY);
                                    }
                                }, 50);
                            }
                            
                            // Verify scroll position was set correctly
                            setTimeout(() => {
                                const currentScroll = window.scrollY || document.documentElement.scrollTop || 0;
                                if (Math.abs(currentScroll - targetY) < 100) {
                                    // Success - remove saved position
                                    sessionStorage.removeItem('filterScrollPosition');
                                    sessionStorage.removeItem('filterScrollData');
                                    console.log('FilterComponent: Successfully restored scroll to', targetY, 'for button', buttonId, 'Current:', currentScroll);
                                } else if (attempt < maxAttempts) {
                                    // Try again if scroll didn't work
                                    console.log('FilterComponent: Scroll restoration attempt', attempt, 'failed. Target:', targetY, 'Current:', currentScroll);
                                    attemptRestore(attempt + 1, maxAttempts);
                                } else {
                                    console.warn('FilterComponent: Max attempts reached. Could not restore scroll to', targetY);
                                    sessionStorage.removeItem('filterScrollPosition');
                                    sessionStorage.removeItem('filterScrollData');
                                }
                            }, 100);
                            
                        } catch (e) {
                            console.warn('FilterComponent: Scroll restoration failed:', e);
                            if (attempt < maxAttempts) {
                                setTimeout(() => attemptRestore(attempt + 1, maxAttempts), 100);
                            } else {
                                sessionStorage.removeItem('filterScrollPosition');
                                sessionStorage.removeItem('filterScrollData');
                            }
                        }
                    } else if (attempt < maxAttempts) {
                        // Page not ready yet, try again
                        console.log('FilterComponent: Page not ready for scroll restoration, attempt', attempt);
                        setTimeout(() => attemptRestore(attempt + 1, maxAttempts), 150);
                    } else {
                        // Max attempts reached, clean up
                        console.warn('FilterComponent: Could not restore scroll position after', maxAttempts, 'attempts - page not ready');
                        sessionStorage.removeItem('filterScrollPosition');
                        sessionStorage.removeItem('filterScrollData');
                    }
                };
                
                attemptRestore();
            }
        };
        
        // Multiple restoration strategies with longer delays to ensure page is fully rendered
        if (document.readyState === 'loading') {
            // Page still loading
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(restoreScroll, 250);
            });
        } else if (document.readyState === 'interactive') {
            // DOM loaded but resources may still be loading
            setTimeout(restoreScroll, 300);
        } else {
            // Page fully loaded
            setTimeout(restoreScroll, 100);
        }
        
        // Additional safety net for late-loading content
        window.addEventListener('load', () => {
            setTimeout(restoreScroll, 200);
        });
        
        // Extra fallback for very slow loading pages
        setTimeout(() => {
            const savedPosition = sessionStorage.getItem('filterScrollPosition');
            if (savedPosition) {
                console.log('FilterComponent: Final fallback scroll restoration');
                restoreScroll();
            }
        }, 1000);
    }

    // Public API
    return {
        init: init,
        handleFilterClick: handleFilterClick,
        updateButtonStates: updateButtonStates,
        showFilterLoading: showFilterLoading
    };
})();