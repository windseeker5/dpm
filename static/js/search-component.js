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
        debounceDelay: 500,
        soundEnabled: true,
        preserveScrollPosition: false
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
            // Reload page on back/forward to ensure correct state
            window.location.reload();
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
        if (isSearching) {
            console.warn('SearchComponent: Search already in progress, ignoring request');
            return; // Prevent multiple simultaneous searches
        }

        setLoadingState(true);

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

        // Fetch search results via AJAX (no page reload)
        fetch(url.toString())
            .then(response => {
                if (!response.ok) {
                    throw new Error('Search request failed');
                }
                return response.text();
            })
            .then(html => {
                // Update the table content without page reload
                updateTableContent(html);

                // Update URL without page reload (for back button support)
                history.pushState({ query: query.trim() }, '', url.toString());

                // Keep search input focused (mobile-friendly)
                enhancedSearchInput.focus();

                setLoadingState(false);
                console.log('SearchComponent: Search completed for query:', query.trim());
            })
            .catch(error => {
                console.error('SearchComponent: Search failed:', error);
                setLoadingState(false);

                // Fallback: Full page reload on error
                window.location.href = url.toString();
            });
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

    function updateTableContent(html) {
        // Parse the HTML response
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        // Extract the main table card (includes filters, table, and pagination)
        const newCard = doc.querySelector('.main-table-card');
        const currentCard = document.querySelector('.main-table-card');

        if (newCard && currentCard) {
            // Replace the entire card (includes filters with updated counts, table, pagination)
            currentCard.innerHTML = newCard.innerHTML;

            // Re-initialize table container reference
            tableContainer = document.querySelector(config.tableContainerSelector);

            // Re-initialize loading indicator for the new table
            if (tableContainer) {
                if (loadingIndicator) {
                    loadingIndicator.remove();
                }
                initializeLoadingIndicator();
            }

            console.log('SearchComponent: Table and filters updated');
        } else {
            console.warn('SearchComponent: Could not find table card in response');
        }
    }

    // Public API
    return {
        init: init,
        performSearch: performSearch,
        setLoadingState: setLoadingState,
        updateSearchFeedback: updateSearchFeedback
    };
})();