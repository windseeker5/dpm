/**
 * SearchComponent - Reusable enhanced search functionality
 * Provides Ctrl+K shortcuts, debounced search, visual feedback, and URL-based navigation
 */
window.SearchComponent = (function() {
    'use strict';

    let config = {};
    let isSearching = false;
    let searchTimeout;
    let enhancedSearchInput;
    let searchForm;
    let tableContainer;
    let loadingIndicator;
    let charCounter;
    let kbdHint;
    let clearBtn;
    let searchSound;

    // Default configuration
    const defaultConfig = {
        formId: 'dynamicSearchForm',
        inputId: 'enhancedSearchInput',
        charCounterId: 'searchCharCounter',
        kbdHintId: 'searchKbdHint',
        clearBtnId: 'searchClearBtn',
        tableContainerSelector: '.table-responsive',
        preserveParams: ['status', 'payment_status', 'activity', 'template'],
        minSearchLength: 3,
        debounceDelay: 250,
        soundEnabled: true,
        preserveScrollPosition: true
    };

    function init(userConfig = {}) {
        config = { ...defaultConfig, ...userConfig };
        
        // Get DOM elements
        enhancedSearchInput = document.getElementById(config.inputId);
        if (!enhancedSearchInput) {
            console.warn('SearchComponent: Search input not found');
            return;
        }

        searchForm = enhancedSearchInput.closest('form') || document.getElementById(config.formId);
        tableContainer = document.querySelector(config.tableContainerSelector);
        charCounter = document.getElementById(config.charCounterId);
        kbdHint = document.getElementById(config.kbdHintId);
        clearBtn = document.getElementById(config.clearBtnId);

        if (config.soundEnabled) {
            initializeSound();
        }

        if (tableContainer) {
            initializeLoadingIndicator();
        }

        setupEventListeners();
        updateSearchFeedback(enhancedSearchInput.value || '');
        
        // Initialize scroll restoration if enabled
        if (config.preserveScrollPosition) {
            initScrollRestoration();
        }
        
        console.log('SearchComponent initialized');
    }

    function initializeSound() {
        try {
            searchSound = new Audio('/static/beep.wav');
            searchSound.volume = 0.3;
        } catch (err) {
            console.warn('SearchComponent: Audio not available');
        }
    }

    function initializeLoadingIndicator() {
        loadingIndicator = createLoadingIndicator();
        tableContainer.style.position = 'relative';
        tableContainer.appendChild(loadingIndicator);
    }

    function createLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'searchLoadingIndicator';
        loadingDiv.innerHTML = `
            <div class="d-flex align-items-center justify-content-center p-3">
                <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <span class="text-muted">Searching...</span>
            </div>
        `;
        loadingDiv.style.cssText = `
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.9);
            z-index: 10;
            display: none;
            border-radius: inherit;
            backdrop-filter: blur(4px);
            -webkit-backdrop-filter: blur(4px);
        `;
        return loadingDiv;
    }

    function setupEventListeners() {
        // Ctrl+K keyboard shortcut to focus search with glow effect
        document.addEventListener('keydown', function(e) {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                e.stopPropagation();
                
                enhancedSearchInput.focus();
                enhancedSearchInput.select();
                
                // Add pink glow effect
                enhancedSearchInput.classList.add('search-glow-active');
                
                // Play sound effect
                if (searchSound) {
                    try {
                        searchSound.currentTime = 0;
                        searchSound.play().catch(() => {
                            // Silently fail if audio can't play
                        });
                    } catch (err) {
                        // Ignore audio errors
                    }
                }
                
                // Remove glow after animation
                setTimeout(() => {
                    enhancedSearchInput.classList.remove('search-glow-active');
                }, 800);
            }
        });

        // Handle input changes with debouncing
        enhancedSearchInput.addEventListener('input', function(e) {
            const query = e.target.value;
            updateSearchFeedback(query);
            debouncedSearch(query);
        });

        // Handle Enter key for immediate search
        enhancedSearchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(searchTimeout);
                const query = e.target.value;
                if (query.trim().length >= config.minSearchLength || query.trim().length === 0) {
                    performSearch(query);
                }
            }
        });

        // Clear button functionality
        if (clearBtn) {
            clearBtn.addEventListener('click', function(e) {
                e.preventDefault();
                enhancedSearchInput.value = '';
                enhancedSearchInput.focus();
                updateSearchFeedback('');
                
                // Show pink glow on clear
                enhancedSearchInput.classList.add('search-glow-active');
                setTimeout(() => {
                    enhancedSearchInput.classList.remove('search-glow-active');
                }, 800);
                
                // Trigger search to clear results
                performSearch('');
            });
        }

        // Focus/blur handling
        enhancedSearchInput.addEventListener('focus', function() {
            if (this.value.length > 0 && this.value.length < config.minSearchLength) {
                this.setAttribute('title', `Type at least ${config.minSearchLength} characters to search`);
            }
            updateSearchFeedback(this.value);
            
            // Add subtle glow on regular focus (not as intense as Ctrl+K)
            if (this.value.length === 0) {
                this.classList.add('search-focus-glow');
            }
        });

        enhancedSearchInput.addEventListener('blur', function() {
            this.removeAttribute('title');
            this.classList.remove('search-focus-glow');
            // Hide counter when not focused unless searching
            if (!isSearching && this.value.trim().length < config.minSearchLength) {
                if (charCounter) charCounter.style.display = 'none';
            }
        });

        // Prevent form submission (we handle it with JavaScript)
        if (searchForm) {
            searchForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const query = enhancedSearchInput.value;
                if (query.trim().length >= config.minSearchLength || query.trim().length === 0) {
                    performSearch(query);
                }
            });
        }

        // Handle browser back/forward navigation
        window.addEventListener('popstate', function(e) {
            // Page will reload automatically, just ensure we're not in a loading state
            setLoadingState(false);
        });
    }

    function updateSearchFeedback(query) {
        const length = query.trim().length;
        
        // Toggle between kbd hint and clear button
        if (length === 0) {
            if (charCounter) charCounter.style.display = 'none';
            enhancedSearchInput.classList.remove('is-valid', 'is-invalid');
            // Show kbd hint, hide clear button
            if (kbdHint) kbdHint.style.display = 'inline-block';
            if (clearBtn) clearBtn.style.display = 'none';
        } else {
            // Hide kbd hint, show clear button
            if (kbdHint) kbdHint.style.display = 'none';
            if (clearBtn) clearBtn.style.display = 'inline-flex';
            
            if (length < config.minSearchLength) {
                if (charCounter) {
                    charCounter.style.display = 'inline';
                    const remaining = config.minSearchLength - length;
                    charCounter.textContent = `${remaining} more char${remaining === 1 ? '' : 's'}`;
                    charCounter.className = 'text-muted';
                }
                enhancedSearchInput.classList.remove('is-valid', 'is-invalid');
            } else {
                // Ready to search - hide counter, no Bootstrap validation styling
                if (charCounter) charCounter.style.display = 'none';
                enhancedSearchInput.classList.remove('is-valid', 'is-invalid');
            }
        }
    }

    function debouncedSearch(query) {
        clearTimeout(searchTimeout);
        
        // If query is empty, clear search immediately
        if (!query || query.trim().length === 0) {
            searchTimeout = setTimeout(() => performSearch(''), 150);
            return;
        }
        
        // If query is less than min length, don't search yet
        if (query.trim().length < config.minSearchLength) {
            return;
        }
        
        // Debounce search for queries with min+ characters
        searchTimeout = setTimeout(() => {
            performSearch(query);
        }, config.debounceDelay);
    }

    function performSearch(query) {
        if (isSearching) return; // Prevent multiple simultaneous searches
        
        setLoadingState(true);
        
        // Store scroll position with additional context for better restoration
        if (config.preserveScrollPosition) {
            const scrollY = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop || 0;
            const timestamp = Date.now();
            const currentUrl = window.location.href;
            
            // Store scroll data with metadata
            const scrollData = {
                position: scrollY,
                timestamp: timestamp,
                url: currentUrl,
                query: query.trim(),
                userAgent: navigator.userAgent.substring(0, 50)
            };
            
            sessionStorage.setItem('searchScrollPosition', scrollY.toString());
            sessionStorage.setItem('searchScrollData', JSON.stringify(scrollData));
            
            console.log('SearchComponent: Stored scroll position', scrollY, 'for search:', query.trim());
        }
        
        // Build URL with search query while preserving filter parameters
        const url = new URL(window.location.href);
        if (query && query.trim().length >= config.minSearchLength) {
            url.searchParams.set('q', query.trim());
        } else {
            url.searchParams.delete('q');
        }
        
        // Preserve existing filter parameters
        const currentParams = new URLSearchParams(window.location.search);
        config.preserveParams.forEach(param => {
            const value = currentParams.get(param);
            if (value && !url.searchParams.has(param)) {
                url.searchParams.set(param, value);
            }
        });
        
        // Navigate to the search URL - this will reload the page with results
        window.location.href = url.toString();
    }

    function setLoadingState(loading) {
        isSearching = loading;
        if (loading) {
            if (loadingIndicator) loadingIndicator.style.display = 'flex';
            enhancedSearchInput.style.opacity = '0.8';
            enhancedSearchInput.classList.add('searching-pulse');
            if (charCounter) {
                charCounter.style.display = 'inline';
                charCounter.textContent = 'searching...';
                charCounter.className = 'text-primary fw-bold';
            }
        } else {
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            enhancedSearchInput.style.opacity = '1';
            enhancedSearchInput.classList.remove('searching-pulse');
            // Reset character counter based on current input
            updateSearchFeedback(enhancedSearchInput.value);
        }
    }

    // Robust scroll position restoration for search operations
    function initScrollRestoration() {
        const restoreScroll = () => {
            const savedPosition = sessionStorage.getItem('searchScrollPosition');
            if (savedPosition) {
                const targetY = parseInt(savedPosition);
                
                // Robust scroll restoration with multiple attempts
                const attemptRestore = (attempt = 1, maxAttempts = 10) => {
                    // Ensure page is fully loaded before scrolling
                    if (document.readyState === 'complete' && 
                        document.body && 
                        document.body.scrollHeight > targetY) {
                        
                        // Use multiple scroll methods for maximum compatibility
                        try {
                            window.scrollTo({
                                top: targetY,
                                left: 0,
                                behavior: 'instant'
                            });
                            
                            // Fallback for older browsers
                            if (window.scrollY !== targetY) {
                                document.documentElement.scrollTop = targetY;
                                document.body.scrollTop = targetY;
                            }
                            
                            // Verify scroll position was set correctly
                            setTimeout(() => {
                                if (Math.abs(window.scrollY - targetY) < 50) {
                                    // Success - remove saved position
                                    sessionStorage.removeItem('searchScrollPosition');
                                    console.log('SearchComponent: Scroll restored to', targetY);
                                } else if (attempt < maxAttempts) {
                                    // Try again if scroll didn't work
                                    attemptRestore(attempt + 1, maxAttempts);
                                }
                            }, 50);
                            
                        } catch (e) {
                            console.warn('SearchComponent: Scroll restoration failed:', e);
                            if (attempt < maxAttempts) {
                                attemptRestore(attempt + 1, maxAttempts);
                            }
                        }
                    } else if (attempt < maxAttempts) {
                        // Page not ready yet, try again
                        setTimeout(() => attemptRestore(attempt + 1, maxAttempts), 100);
                    } else {
                        // Max attempts reached, clean up
                        sessionStorage.removeItem('searchScrollPosition');
                        console.warn('SearchComponent: Could not restore scroll position after', maxAttempts, 'attempts');
                    }
                };
                
                attemptRestore();
            }
        };
        
        // Multiple restoration strategies
        if (document.readyState === 'loading') {
            // Page still loading
            document.addEventListener('DOMContentLoaded', () => {
                setTimeout(restoreScroll, 150);
            });
        } else if (document.readyState === 'interactive') {
            // DOM loaded but resources may still be loading
            setTimeout(restoreScroll, 200);
        } else {
            // Page fully loaded
            setTimeout(restoreScroll, 50);
        }
        
        // Additional safety net for late-loading content
        window.addEventListener('load', () => {
            setTimeout(restoreScroll, 100);
        });
    }

    // Public API
    return {
        init: init,
        performSearch: performSearch,
        setLoadingState: setLoadingState,
        updateSearchFeedback: updateSearchFeedback,
        initScrollRestoration: initScrollRestoration
    };
})();