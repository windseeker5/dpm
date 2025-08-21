/**
 * Robust scroll position preservation for filter buttons
 * This provides a simple, reliable solution that works across all browsers
 */
window.ScrollPreservation = (function() {
    'use strict';

    function init() {
        // Handle scroll preservation on page load
        handleScrollRestoration();
        
        // Set up filter button click handlers
        setupFilterHandlers();
        
        console.log('ScrollPreservation: Initialized');
    }

    function setupFilterHandlers() {
        // Find all filter buttons
        const filterButtons = document.querySelectorAll('.github-filter-btn');
        
        filterButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                // Store current scroll position and which button was clicked
                const scrollY = window.pageYOffset || document.documentElement.scrollTop || 0;
                const buttonId = this.id;
                const timestamp = Date.now();
                
                // Store in sessionStorage for retrieval after page reload
                sessionStorage.setItem('scrollPreservation', JSON.stringify({
                    position: scrollY,
                    buttonId: buttonId,
                    timestamp: timestamp,
                    url: window.location.href
                }));
                
                console.log('ScrollPreservation: Stored scroll position', scrollY, 'for button', buttonId);
            });
        });
    }

    function handleScrollRestoration() {
        // Check if we have stored scroll data
        const storedData = sessionStorage.getItem('scrollPreservation');
        if (!storedData) {
            return;
        }

        try {
            const data = JSON.parse(storedData);
            
            // Check if data is recent (within last 5 seconds) to avoid stale data
            if (Date.now() - data.timestamp > 5000) {
                sessionStorage.removeItem('scrollPreservation');
                return;
            }

            // Clear the stored data to prevent repeated scrolling
            sessionStorage.removeItem('scrollPreservation');

            // Use multiple restoration strategies for maximum reliability
            restoreScrollPosition(data.position);
            
        } catch (e) {
            console.warn('ScrollPreservation: Error parsing stored data:', e);
            sessionStorage.removeItem('scrollPreservation');
        }
    }

    function restoreScrollPosition(targetY) {
        // Strategy 1: Use setTimeout to allow page to fully render
        setTimeout(() => attemptScroll(targetY, 1), 100);
        
        // Strategy 2: Use requestAnimationFrame for smooth rendering
        requestAnimationFrame(() => {
            setTimeout(() => attemptScroll(targetY, 2), 50);
        });
        
        // Strategy 3: Listen for load event as backup
        if (document.readyState !== 'complete') {
            window.addEventListener('load', () => {
                setTimeout(() => attemptScroll(targetY, 3), 100);
            }, { once: true });
        }
    }

    function attemptScroll(targetY, attempt) {
        // Ensure page content is available
        if (document.body.scrollHeight < targetY + 100) {
            if (attempt < 5) {
                // Page might still be loading, try again
                setTimeout(() => attemptScroll(targetY, attempt + 1), 200);
                return;
            }
        }

        // Perform the scroll
        try {
            // Modern browsers
            window.scrollTo({
                top: targetY,
                left: 0,
                behavior: 'instant'
            });

            // Fallback for older browsers
            if (Math.abs(window.pageYOffset - targetY) > 10) {
                document.documentElement.scrollTop = targetY;
                document.body.scrollTop = targetY;
            }

            console.log('ScrollPreservation: Restored scroll to', targetY, 'on attempt', attempt);
            
            // Verify scroll was successful
            setTimeout(() => {
                const currentScroll = window.pageYOffset || document.documentElement.scrollTop || 0;
                if (Math.abs(currentScroll - targetY) > 50) {
                    console.warn('ScrollPreservation: Scroll verification failed. Target:', targetY, 'Actual:', currentScroll);
                }
            }, 100);

        } catch (e) {
            console.warn('ScrollPreservation: Scroll attempt failed:', e);
        }
    }

    // Enhanced anchor handling for filter buttons
    function enhanceAnchorScrolling() {
        // If page loaded with a hash, ensure smooth scrolling to that element
        if (window.location.hash) {
            const targetId = window.location.hash.substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                // Small delay to ensure page is rendered
                setTimeout(() => {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }, 300);
            }
        }
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Enhance anchor scrolling on load
    window.addEventListener('load', enhanceAnchorScrolling);

    // Public API
    return {
        init: init,
        restoreScrollPosition: restoreScrollPosition
    };
})();