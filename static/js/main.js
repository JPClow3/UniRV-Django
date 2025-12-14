// AJAX FILTERS FOR INDEX PAGE WITH DEBOUNCING
(function () {
    const searchForm = document.querySelector('.search-form');
    const editaisGrid = document.querySelector('.editais-grid');
    const paginationContainer = document.querySelector('.pagination-container');
    const searchInput = document.querySelector('.search-input, .search-input-enhanced');
    const skeletonTemplate = document.getElementById('edital-skeleton-template');
    const templateSkeletonMarkup = skeletonTemplate ? skeletonTemplate.innerHTML.trim() : null;

    if (!searchForm || !editaisGrid) return;

    let searchTimeout = null;
    const SEARCH_DELAY = 500;
    let isLoading = false;

    // Expose searchTimeout to window for keyboard shortcuts
    window.searchTimeout = searchTimeout;

    // Function to show skeleton loading
    function showSkeletonLoading() {
        if (isLoading) return;
        isLoading = true;

        editaisGrid.classList.add('loading');
        
        // Always use template from DOM - no fallback to prevent duplication
        if (!templateSkeletonMarkup) {
            // If template is missing, show simple loading message
            editaisGrid.innerHTML = '<div class="text-center py-12 text-gray-500">Carregando editais...</div>';
            return;
        }

        const skeletonCount = 6;
        const skeletonCards = [];

        for (let i = 0; i < skeletonCount; i++) {
            skeletonCards.push(templateSkeletonMarkup);
        }

        editaisGrid.innerHTML = skeletonCards.join('');
    }

    // Function to perform search (exposed globally for keyboard shortcuts)
    window.performSearch = function() {
        if (isLoading) return;

        // Get form data from both search form and filter form
        const formData = new FormData(searchForm);
        const filterForm = document.getElementById('filter-form');
        
        if (filterForm) {
            const filterFormData = new FormData(filterForm);
            // Merge filter form data to search form data (use set to avoid duplicates)
            // Also read directly from form elements to ensure we get all values
            const filterValues = {};
            const filterInputs = filterForm.querySelectorAll('input, select, textarea');
            
            // Read from FormData first
            for (const [key, value] of filterFormData.entries()) {
                filterValues[key] = value;
            }
            
            // Also read directly from form elements to catch any values FormData might miss
            filterInputs.forEach(input => {
                if (input.name) {
                    let value = '';
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        value = input.checked ? input.value : '';
                    } else {
                        value = input.value || '';
                    }
                    // Only update if we have a value (don't overwrite FormData with empty)
                    if (value && value.trim() !== '') {
                        filterValues[input.name] = value;
                    }
                }
            });
            
            // Add all filter values to formData (use set to avoid duplicates)
            for (const [key, value] of Object.entries(filterValues)) {
                if (value && String(value).trim() !== '') { // Only add non-empty values
                    formData.set(key, value);
                }
            }
        }
        const params = new URLSearchParams(formData);
        const url = `${window.location.pathname}?${params.toString()}`;

        // Show skeleton loading
        showSkeletonLoading();

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.text();
            })
            .then(html => {
                // Server now returns partial HTML (only grid and pagination) for AJAX requests
                // Parse it to extract the grid and pagination sections
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');

                // Check for parsing errors (DOMParser may create error elements for malformed HTML)
                const parserError = doc.querySelector('parsererror');
                if (parserError) {
                    throw new Error('Failed to parse HTML response');
                }

                const newGrid = doc.querySelector('.editais-grid');
                const newPagination = doc.querySelector('.pagination-container');
                        // Check for empty state - try multiple selectors
                        const noResults = doc.querySelector('#no-results') || 
                                        doc.querySelector('.empty-state') || 
                                        doc.querySelector('.empty-state-container') ||
                                        doc.querySelector('div.empty-state');

                // Note: search-results-count element may not exist in all templates
                // This is safe - it just won't update if the element doesn't exist

                if (newGrid) {
                    editaisGrid.classList.remove('loading');
                    // Restore grid classes if they were removed (for empty state)
                    if (!editaisGrid.classList.contains('grid')) {
                        editaisGrid.classList.remove('flex', 'justify-center');
                        editaisGrid.classList.add('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
                    }
                    editaisGrid.innerHTML = newGrid.innerHTML;
                    isLoading = false;

                    editaisGrid.classList.add('fade-in');
                    setTimeout(() => editaisGrid.classList.remove('fade-in'), 400);

                    // Announce to screen readers
                    const cardCount = newGrid.querySelectorAll('.edital-card').length;
                    announceToScreenReader(`Resultados atualizados. ${cardCount} editais encontrados.`);
                } else if (noResults) {
                    // Handle empty state
                    editaisGrid.classList.remove('loading');
                    // Remove grid classes to allow proper centering
                    editaisGrid.classList.remove('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
                    editaisGrid.classList.add('flex', 'justify-center');
                    editaisGrid.innerHTML = noResults.outerHTML;
                    isLoading = false;
                    announceToScreenReader('Nenhum resultado encontrado.');
                } else {
                    // Fallback: Clear loading state and show error message
                    editaisGrid.classList.remove('loading');
                    isLoading = false;
                    editaisGrid.innerHTML = '<div class="text-center py-12 text-red-500">Erro ao carregar resultados. Por favor, recarregue a página.</div>';
                    showToast('Erro ao processar resposta do servidor. Tente novamente.', 'error');
                }

                if (newPagination && paginationContainer) {
                    paginationContainer.innerHTML = newPagination.innerHTML;
                    setupPaginationAjax();
                } else if (paginationContainer) {
                    // Clear pagination if no results
                    paginationContainer.innerHTML = '';
                }

                // Remove loading states
                const wrapper = searchForm.querySelector('.search-input-wrapper');
                if (wrapper) {
                    wrapper.classList.remove('searching');
                }
                const clearBtn = document.querySelector('.clear-filters-btn');
                if (clearBtn) {
                    clearBtn.classList.remove('loading');
                }

                // Update URL in browser (allow sharing filtered results)
                history.pushState({search: params.toString()}, '', url);

                // Smooth scroll to top of results
                if (editaisGrid) {
                editaisGrid.scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            })
            .catch(error => {
                if (editaisGrid) {
                editaisGrid.classList.remove('loading');
                }
                isLoading = false;
                
                // Remove loading states on error
                const wrapper = searchForm.querySelector('.search-input-wrapper');
                if (wrapper) {
                    wrapper.classList.remove('searching');
                }
                const clearBtn = document.querySelector('.clear-filters-btn');
                if (clearBtn) {
                    clearBtn.classList.remove('loading');
                }
                
                showToast('Erro ao filtrar editais. Tente novamente.', 'error');
            });
    };

    // Function to toggle clear button and keyboard hint (exposed for use in event handlers)
    function toggleSearchUI(inputElement, value) {
        if (!inputElement) return;
        const wrapper = inputElement.closest('.search-input-wrapper');
        if (!wrapper) return;

        const clearButton = wrapper.querySelector('.search-clear');
        const keyboardHint = wrapper.querySelector('.keyboard-hint');

        if (value && value.length > 0) {
            if (!clearButton) {
                const clearBtn = document.createElement('button');
                clearBtn.type = 'button';
                clearBtn.className = 'search-clear';
                clearBtn.setAttribute('aria-label', 'Limpar busca');
                clearBtn.innerHTML = '<i class="fas fa-times" aria-hidden="true"></i>';
                inputElement.parentNode.insertBefore(clearBtn, inputElement.nextSibling);
            } else {
                clearButton.style.display = 'flex';
            }
            if (keyboardHint) {
                keyboardHint.style.display = 'none';
            }
        } else {
            if (clearButton) {
                clearButton.style.display = 'none';
            }
            if (keyboardHint) {
                keyboardHint.style.display = 'flex';
            }
        }
    }

    if (searchInput) {
        toggleSearchUI(searchInput, searchInput.value);

        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            window.searchTimeout = null;

            toggleSearchUI(this, this.value);

            const wrapper = this.closest('.search-input-wrapper');
            if (wrapper) {
                wrapper.classList.add('searching');
            }

            searchTimeout = setTimeout(() => {
                if (this.value.length >= 3 || this.value.length === 0) {
                    window.performSearch();
                }
                if (wrapper) {
                    wrapper.classList.remove('searching');
                }
                window.searchTimeout = null;
            }, SEARCH_DELAY);
            window.searchTimeout = searchTimeout;
        });
    }

    // Clear button functionality - use event delegation for dynamic content
    document.addEventListener('click', function(e) {
        if (e.target.closest('.search-clear')) {
            e.preventDefault();
            const clearBtn = e.target.closest('.search-clear');
            const input = clearBtn.previousElementSibling;
            if (input && input.tagName === 'INPUT') {
                input.value = '';
                input.focus();

                toggleSearchUI(input, '');

                if (window.searchTimeout) {
                    clearTimeout(window.searchTimeout);
                    window.searchTimeout = null;
                }

                if (window.performSearch) {
                    window.performSearch();
                } else {
                    const form = input.closest('form');
                    if (form) {
                        form.dispatchEvent(new Event('submit', { cancelable: true }));
                    }
                }
            }
        }
    });

    // Clear filters button
    const clearFiltersBtn = document.querySelector('.clear-filters-btn');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', function(e) {
            e.preventDefault();
            const form = this.closest('form');
            if (form) {
                // Clear all form inputs
                form.querySelectorAll('input[type="text"], select').forEach(input => {
                    if (input.type === 'text') {
                        input.value = '';
                    } else if (input.tagName === 'SELECT') {
                        input.selectedIndex = 0;
                    }
                });
                // Clear URL params and reload
                window.location.href = window.location.pathname;
            }
        });
    }

    // Filter change handlers with loading states
    // Handle all filter inputs: status, orgao, start_date, end_date
    // Use a function to setup filters that can be called when DOM is ready
    function setupFilterHandlers() {
        const filterForm = document.getElementById('filter-form');
        
        if (!filterForm) {
            return;
        }
        
        // Get all filter inputs - use more specific selectors
        // Use querySelectorAll to get all selects and date inputs in the filter form
        const filterInputs = Array.from(filterForm.querySelectorAll('select[name], input[type="date"][name]'));
        
        filterInputs.forEach(input => {
            // Check if listener already attached (avoid duplicates)
            if (input.hasAttribute('data-filter-listener-attached')) {
                return;
            }
            input.setAttribute('data-filter-listener-attached', 'true');
            
            input.addEventListener('change', function() {
                // Note: We no longer sync to search form hidden inputs to avoid duplicates
                // The performSearch function now reads directly from filterForm
                
                // Add loading state to the input itself
                this.classList.add('loading');
                this.disabled = true;

                const wrapper = this.closest('form');
                if (wrapper) {
                    wrapper.classList.add('searching');
                }
                
                // Add loading state to clear button if it exists
                const clearBtn = document.querySelector('.clear-filters-btn');
                if (clearBtn) {
                    clearBtn.classList.add('loading');
                }
                
                // Perform search after a short delay
                setTimeout(() => {
                    if (window.performSearch) {
                        window.performSearch();
                    } else {
                        const form = this.closest('form');
                        if (form) {
                            form.dispatchEvent(new Event('submit', { cancelable: true }));
                        }
                    }
                    
                    // Remove loading states
                    if (wrapper) {
                        wrapper.classList.remove('searching');
                    }
                    if (clearBtn) {
                        clearBtn.classList.remove('loading');
                    }
                    this.classList.remove('loading');
                    this.disabled = false;
                }, 300);
            });
        });
    }
    
    // Setup filters when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupFilterHandlers);
    } else {
        // DOM already loaded, but wait a bit for dynamic content
        setTimeout(setupFilterHandlers, 100);
    }

    // Legacy support for old filter selectors (if they exist)
    const legacyFilterSelects = document.querySelectorAll('select[name="tipo"], select[name="status"], select[name="edital"]');
    legacyFilterSelects.forEach(select => {
        select.addEventListener('change', function() {
            // Add loading state to the select itself
            this.classList.add('loading');
            this.disabled = true;

            // Sync filter values to search form's hidden inputs
            if (searchForm) {
                const fieldName = this.name;
                let hiddenInput = searchForm.querySelector(`input[name="${fieldName}"]`);
                if (!hiddenInput) {
                    hiddenInput = document.createElement('input');
                    hiddenInput.type = 'hidden';
                    hiddenInput.name = fieldName;
                    searchForm.appendChild(hiddenInput);
                }
                hiddenInput.value = this.value;
            }
            
            const wrapper = this.closest('.search-input-wrapper') || this.closest('form');
            if (wrapper) {
                wrapper.classList.add('searching');
            }
            
            // Add loading state to clear button if it exists
            const clearBtn = document.querySelector('.clear-filters-btn');
            if (clearBtn) {
                clearBtn.classList.add('loading');
            }
            
            // Perform search after a short delay
            setTimeout(() => {
                if (window.performSearch) {
                    window.performSearch();
                } else {
                    const form = this.closest('form');
                    if (form) {
                        form.dispatchEvent(new Event('submit', { cancelable: true }));
                    }
                }
                
                // Remove loading states
                if (wrapper) {
                    wrapper.classList.remove('searching');
                }
                if (clearBtn) {
                    clearBtn.classList.remove('loading');
                }
                this.classList.remove('loading');
                this.disabled = false;
            }, 300);
        });
    });

    // Intercept form submission (manual submit)
    if (searchForm) {
        searchForm.addEventListener('submit', function (event) {
            event.preventDefault();
            clearTimeout(searchTimeout);
            window.searchTimeout = null;
            
            // Add loading state
            const wrapper = searchForm.querySelector('.search-input-wrapper');
            if (wrapper) {
                wrapper.classList.add('searching');
            }
            
            window.performSearch();
        });
    }

    window.addEventListener('popstate', function (event) {
        if (event.state && event.state.search) {
            // Reload the page with the stored search params
            window.location.search = event.state.search;
        }
    });

    // Setup AJAX pagination
    function setupPaginationAjax() {
        const paginationLinks = document.querySelectorAll('.pagination .page-link');

        paginationLinks.forEach(link => {
            link.addEventListener('click', function (event) {
                event.preventDefault();
                const url = this.href;

                // Show skeleton loading
                showSkeletonLoading();

                fetch(url, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                                })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.text();
                    })
                    .then(html => {
                        // Server now returns partial HTML for AJAX requests
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');

                        // Check for parsing errors
                        const parserError = doc.querySelector('parsererror');
                        if (parserError) {
                            throw new Error('Failed to parse HTML response');
                        }

                        const newGrid = doc.querySelector('.editais-grid');
                        const newPagination = doc.querySelector('.pagination-container');
                        // Check for both #no-results and .empty-state (empty_state component)
                        const noResults = doc.querySelector('#no-results') || doc.querySelector('.empty-state');

                        if (newGrid) {
                            editaisGrid.classList.remove('loading');
                            // Restore grid classes if they were removed (for empty state)
                            if (!editaisGrid.classList.contains('grid')) {
                                editaisGrid.classList.remove('flex', 'justify-center');
                                editaisGrid.classList.add('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
                            }
                            editaisGrid.innerHTML = newGrid.innerHTML;
                            isLoading = false;

                            editaisGrid.classList.add('fade-in');
                            setTimeout(() => editaisGrid.classList.remove('fade-in'), 400);

                            // Announce to screen readers
                            const cardCount = newGrid.querySelectorAll('.edital-card').length;
                            announceToScreenReader(`Página atualizada. ${cardCount} editais exibidos.`);
                        } else if (noResults) {
                            editaisGrid.classList.remove('loading');
                            // Remove grid classes to allow proper centering
                            editaisGrid.classList.remove('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
                            editaisGrid.classList.add('flex', 'justify-center');
                            editaisGrid.innerHTML = noResults.outerHTML;
                            isLoading = false;
                            announceToScreenReader('Nenhum resultado encontrado.');
                        } else {
                            // Fallback: Clear loading state
                            editaisGrid.classList.remove('loading');
                            isLoading = false;
                            showToast('Erro ao processar resposta. Tente novamente.', 'error');
                        }

                        if (newPagination && paginationContainer) {
                            paginationContainer.innerHTML = newPagination.innerHTML;
                            setupPaginationAjax();
                        } else if (paginationContainer) {
                            paginationContainer.innerHTML = '';
                        }

                        history.pushState({}, '', url);

                        // Smooth scroll to top of results
                        if (editaisGrid) {
                        editaisGrid.scrollIntoView({behavior: 'smooth', block: 'start'});
                        }
                    })
                    .catch(error => {
                        if (editaisGrid) {
                        editaisGrid.classList.remove('loading');
                        }
                        isLoading = false;
                        showToast('Erro ao carregar página. Tente novamente.', 'error');
                    });
            });
        });
    }

    // Initial setup for pagination
    setupPaginationAjax();

    // Announce to screen readers helper
    function announceToScreenReader(message) {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        document.body.appendChild(announcement);

        setTimeout(() => announcement.remove(), 1000);
    }
})();

// ========================================
// MOBILE MENU TOGGLE
// ========================================
(function() {
  const menuToggle = document.querySelector('.mobile-menu-toggle');
  const navMenu = document.querySelector('.navbar-right');

  if (!menuToggle || !navMenu) return;

  // Cache menu height to avoid reflows when toggling
  let cachedMenuHeight = null;

  // Calculate actual menu height dynamically instead of hardcoded max-height
  function getMenuHeight() {
    if (cachedMenuHeight !== null) {
      return cachedMenuHeight;
    }

    // Temporarily show menu to measure its height
    navMenu.style.display = 'block';
    navMenu.style.maxHeight = 'none';
    navMenu.style.visibility = 'hidden';
    const height = navMenu.scrollHeight;
    navMenu.style.display = '';
    navMenu.style.maxHeight = '';
    navMenu.style.visibility = '';

    // Limit to 80% viewport height for safety
    cachedMenuHeight = Math.min(height, window.innerHeight * 0.8);
    return cachedMenuHeight;
  }

  menuToggle.addEventListener('click', function() {
    const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';

    menuToggle.setAttribute('aria-expanded', !isExpanded);

    if (!isExpanded) {
      // Opening menu - calculate actual height
      const menuHeight = getMenuHeight();
      navMenu.style.maxHeight = menuHeight + 'px';
      navMenu.classList.add('menu-open');
      
      // Accessibility: trap focus inside menu when open
      const firstLink = navMenu.querySelector('a');
      if (firstLink) {
        setTimeout(() => firstLink.focus(), 100);
      }
    } else {
      // Closing menu
      navMenu.style.maxHeight = '0';
      navMenu.classList.remove('menu-open');
    }
  });

  // Helper function to close menu
  function closeMenu() {
    menuToggle.setAttribute('aria-expanded', 'false');
    navMenu.style.maxHeight = '0';
    navMenu.classList.remove('menu-open');
  }

  // Swipe-to-close gesture on mobile (optimized to prevent conflicts with horizontal scrolling)
  let touchStartX = 0;
  let touchEndX = 0;
  let touchStartY = 0;
  let touchEndY = 0;
  let isScrolling = false;

  function isWithinScrollableContainer(element) {
    // Check if element is within a horizontally scrollable container (table, carousel, etc.)
    let parent = element.parentElement;
    while (parent && parent !== document.body) {
      const style = window.getComputedStyle(parent);
      const overflowX = style.overflowX;
      if (overflowX === 'auto' || overflowX === 'scroll' || overflowX === 'hidden') {
        // Check if container can scroll horizontally
        if (parent.scrollWidth > parent.clientWidth) {
          return true;
        }
      }
      parent = parent.parentElement;
    }
    return false;
  }

  function handleSwipe() {
    const swipeDistance = touchEndX - touchStartX;
    const verticalDistance = Math.abs(touchEndY - touchStartY);
    const horizontalDistance = Math.abs(swipeDistance);
    const swipeThreshold = 120; // Increased from 100px for better intentionality
    
    // Only trigger if:
    // 1. Swipe is primarily horizontal (horizontal > vertical)
    // 2. Swipe distance exceeds threshold
    // 3. Swipe is to the right (positive distance)
    // 4. User is not scrolling (vertical movement is minimal)
    if (horizontalDistance > swipeThreshold && 
        horizontalDistance > verticalDistance && 
        swipeDistance > 0 && 
        verticalDistance < 50 && 
        !isScrolling) {
      closeMenu();
    }
  }

  navMenu.addEventListener('touchstart', function(e) {
    // Only track touches on the menu element itself, not children
    if (e.target !== navMenu && !navMenu.contains(e.target)) {
      return;
    }
    
    // Check if touch is within a scrollable container
    if (isWithinScrollableContainer(e.target)) {
      isScrolling = true;
      return;
    }
    
    touchStartX = e.changedTouches[0].screenX;
    touchStartY = e.changedTouches[0].screenY;
    isScrolling = false;
  }, { passive: true });

  navMenu.addEventListener('touchmove', function(e) {
    // Detect if user is scrolling (vertical or horizontal)
    if (touchStartY !== 0) {
      const currentY = e.changedTouches[0].screenY;
      const currentX = e.changedTouches[0].screenX;
      const verticalDelta = Math.abs(currentY - touchStartY);
      const horizontalDelta = Math.abs(currentX - touchStartX);
      
      // If vertical movement is significant, user is scrolling
      if (verticalDelta > 10 || (horizontalDelta > 10 && isWithinScrollableContainer(e.target))) {
        isScrolling = true;
      }
    }
  }, { passive: true });

  navMenu.addEventListener('touchend', function(e) {
    // Only process if touch started on menu and wasn't scrolling
    if (touchStartX === 0 || isScrolling) {
      touchStartX = 0;
      touchStartY = 0;
      touchEndX = 0;
      touchEndY = 0;
      isScrolling = false;
      return;
    }
    
    touchEndX = e.changedTouches[0].screenX;
    touchEndY = e.changedTouches[0].screenY;
    handleSwipe();
    
    // Reset
    touchStartX = 0;
    touchStartY = 0;
    touchEndX = 0;
    touchEndY = 0;
    isScrolling = false;
  }, { passive: true });

  document.addEventListener('click', function(event) {
    const isClickInsideMenu = navMenu.contains(event.target);
    const isClickOnToggle = menuToggle.contains(event.target);
    const isMenuOpen = menuToggle.getAttribute('aria-expanded') === 'true';

    if (isMenuOpen && !isClickInsideMenu && !isClickOnToggle) {
      closeMenu();
    }
  });

  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && menuToggle.getAttribute('aria-expanded') === 'true') {
      closeMenu();
      menuToggle.focus();
    }
  });

  // Close menu when window is resized to desktop size
  window.addEventListener('resize', function() {
    cachedMenuHeight = null;
    if (window.innerWidth > 767) {
      closeMenu();
    }
  });

    // Close menu when navigating (clicking on links)
    document.querySelectorAll('.navbar-right a').forEach(function (link) {
        link.addEventListener('click', function () {
            if (window.innerWidth <= 767) {
                closeMenu();
            }
        });
    });
})();

// ========================================
// FORM AUTOSAVE & UNSAVED CHANGES WARNING
// ========================================
(function () {
    const editalForm = document.querySelector('form#edital-form');
    if (!editalForm) return;

    const AUTOSAVE_KEY = 'edital_form_autosave';
    const AUTOSAVE_INTERVAL = 10000;
    let formChanged = false;
    let autosaveInterval;

    // Get all form fields
    const formFields = editalForm.querySelectorAll('input, textarea, select');

    window.addEventListener('DOMContentLoaded', function () {
        const savedData = localStorage.getItem(AUTOSAVE_KEY);

        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                const savedDate = new Date(data.timestamp);
                const now = new Date();
                const hoursSince = (now - savedDate) / (1000 * 60 * 60);

                if (hoursSince < 24) {
                    if (confirm(`Encontramos um rascunho salvo em ${savedDate.toLocaleString()}. Deseja restaurá-lo?`)) {
                        restoreFormData(data.fields);
                        showToast('Rascunho restaurado com sucesso!');
                    } else {
                        localStorage.removeItem(AUTOSAVE_KEY);
                    }
                }
            } catch (e) {
                localStorage.removeItem(AUTOSAVE_KEY);
            }
        }
    });

    // Track form changes
    formFields.forEach(function (field) {
        field.addEventListener('input', function () {
            formChanged = true;
        });

        field.addEventListener('change', function () {
            formChanged = true;
        });
    });

    function autosaveForm() {
        if (!formChanged) return;

        const formData = {};
        formFields.forEach(function (field) {
            if (field.type !== 'password' && field.name) {
                formData[field.name] = field.value;
            }
        });

        const saveData = {
            fields: formData,
            timestamp: new Date().toISOString()
        };

        try {
            const jsonString = JSON.stringify(saveData);
            // Prevent localStorage overflow (approx. 5MB limit)
            if (jsonString.length > 4.5 * 1024 * 1024) {
                showToast('Rascunho muito grande para salvar automaticamente', 'warning');
                return;
            }
            localStorage.setItem(AUTOSAVE_KEY, jsonString);
            showAutosaveIndicator();
        } catch (e) {
            if (e.name === 'QuotaExceededError') {
                showToast('Armazenamento local cheio. Rascunho não salvo.', 'error');
                // Clear old autosaves
                Object.keys(localStorage).forEach(key => {
                    if (key.startsWith('edital_form_autosave')) {
                        localStorage.removeItem(key);
                    }
                });
            }
            // Silently ignore other storage errors
        }
    }

    // Restore form data
    function restoreFormData(data) {
        Object.keys(data).forEach(function (name) {
            const field = editalForm.querySelector(`[name="${name}"]`);
            if (field) {
                field.value = data[name];
            }
        });
    }

    function showAutosaveIndicator() {
        let indicator = document.querySelector('.autosave-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'autosave-indicator';
            indicator.innerHTML = '<i class="fas fa-check-circle"></i> Rascunho salvo';
            document.body.appendChild(indicator);
        }

        indicator.classList.add('visible');
        setTimeout(function () {
            indicator.classList.remove('visible');
        }, 2000);
    }

    // Start autosave interval
    autosaveInterval = setInterval(autosaveForm, AUTOSAVE_INTERVAL);

    // Warn before leaving if form has changes
    window.addEventListener('beforeunload', function (e) {
        if (formChanged) {
            e.preventDefault();
            e.returnValue = 'Você tem alterações não salvas. Tem certeza que deseja sair?';
            return e.returnValue;
        }
    });

    // Clear autosave on successful submit
    editalForm.addEventListener('submit', function () {
        formChanged = false;
        clearInterval(autosaveInterval);
        localStorage.removeItem(AUTOSAVE_KEY);
    });

    const manualSaveBtn = document.getElementById('manual-save-draft');
    if (manualSaveBtn) {
        manualSaveBtn.addEventListener('click', function (e) {
            e.preventDefault();
            autosaveForm();
            showToast('Rascunho salvo manualmente!');
        });
    }
})();

// ========================================
// FORM LOADING STATES
// ========================================
(function() {
    const forms = document.querySelectorAll('form#edital-form');

    forms.forEach(function (form) {
        form.addEventListener('submit', function (event) {
            const submitBtn = form.querySelector('#submit-btn');

            // Check form validity first
            if (!form.checkValidity()) {
                return; // Let browser handle validation
            }

            if (submitBtn && !submitBtn.classList.contains('loading')) {
                // Add loading state
                submitBtn.classList.add('loading');
                submitBtn.disabled = true;

                // Show loading text, hide normal text
                const btnText = submitBtn.querySelector('.btn-text');
                const btnLoading = submitBtn.querySelector('.btn-loading');
                if (btnText) btnText.style.display = 'none';
                if (btnLoading) btnLoading.style.display = 'inline-block';
            }
        });
    });
})();

// ========================================
// DATE VALIDATION (Frontend)
// ========================================
(function() {
    const startDateInput = document.getElementById('id_start_date');
    const endDateInput = document.getElementById('id_end_date');

    if (!startDateInput || !endDateInput) return;

    function validateDates() {
        if (startDateInput.value && endDateInput.value) {
            const start = new Date(startDateInput.value);
            const end = new Date(endDateInput.value);

            if (end < start) {
                endDateInput.setCustomValidity('A data de encerramento deve ser posterior à data de abertura.');
                endDateInput.classList.add('has-date-error');
                return false;
            } else {
                endDateInput.setCustomValidity('');
                endDateInput.classList.remove('has-date-error');
            }
        } else {
            endDateInput.setCustomValidity('');
            endDateInput.classList.remove('has-date-error');
        }
        return true;
    }

    // Validate on change
    startDateInput.addEventListener('change', validateDates);
    endDateInput.addEventListener('change', validateDates);

    // Validate on input (for real-time feedback)
    startDateInput.addEventListener('input', validateDates);
    endDateInput.addEventListener('input', validateDates);

    // Validate on form submit
    const form = startDateInput.closest('form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (!validateDates()) {
                e.preventDefault();
                endDateInput.focus();
                showToast('A data de encerramento deve ser posterior à data de abertura.', 'error');
            }
        });
    }
})();

// HTML escape function to prevent XSS attacks
function escapeHtml(text) {
    if (text == null) {
        return '';
    }
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// Escape JavaScript string for template literals (prevents injection via ${}, backticks, etc.)
function escapeJsString(text) {
    if (text == null) {
        return '';
    }
    return String(text)
        .replace(/\\/g, '\\\\')
        .replace(/`/g, '\\`')
        .replace(/\${/g, '\\${');
}

// Toast notification helper - Enhanced version
function showToast(message, type = 'success', duration = 5000) {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
    toast.setAttribute('aria-atomic', 'true');
    
    // Add icon based on type
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    // Escape user-supplied message to prevent XSS
    const escapedMessage = escapeHtml(message);
    const iconClass = icons[type] || icons.success;
    
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas ${iconClass} toast-icon"></i>
            <span class="toast-message">${escapedMessage}</span>
        </div>
        <button class="toast-close" aria-label="Fechar notificação">
            <i class="fas fa-times"></i>
        </button>
    `;

    toastContainer.appendChild(toast);
    
    // Force reflow for screen readers
    void toast.offsetHeight;

    // Show toast with animation
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto-dismiss
    const dismissTimer = setTimeout(() => {
        dismissToast(toast);
    }, duration);
    
    // Clear timer on manual close and dismiss toast
    toast.querySelector('.toast-close').addEventListener('click', () => {
        clearTimeout(dismissTimer);
        dismissToast(toast);
    });
}

function dismissToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
        const container = document.getElementById('toast-container');
        if (container && container.children.length === 0) {
            container.remove();
        }
    }, 300);
}

// Confirmation dialog helper
function showConfirmDialog(options) {
    return new Promise((resolve) => {
        const {
            title = 'Confirmar ação',
            message = 'Tem certeza que deseja continuar?',
            confirmText = 'Confirmar',
            cancelText = 'Cancelar',
            type = 'warning',
            confirmButtonClass = options.confirmClass || 'btn-danger'  // Support both confirmClass and confirmButtonClass
        } = options;

        // Create dialog overlay
        const overlay = document.createElement('div');
        overlay.className = 'confirm-dialog-overlay';
        overlay.setAttribute('role', 'dialog');
        overlay.setAttribute('aria-modal', 'true');
        overlay.setAttribute('aria-labelledby', 'confirm-dialog-title');
        
        const icons = {
            warning: 'fa-exclamation-triangle',
            danger: 'fa-trash',
            info: 'fa-info-circle'
        };
        
        // Escape user-supplied text to prevent XSS attacks
        const escapedTitle = escapeHtml(title);
        const escapedMessage = escapeHtml(message);
        const escapedConfirmText = escapeHtml(confirmText);
        const escapedCancelText = escapeHtml(cancelText);
        const iconClass = icons[type] || icons.warning;
        
        overlay.innerHTML = `
            <div class="confirm-dialog">
                <div class="confirm-dialog-header">
                    <div class="confirm-dialog-icon confirm-dialog-icon-${type}">
                        <i class="fas ${iconClass}"></i>
                    </div>
                    <h3 id="confirm-dialog-title" class="confirm-dialog-title">${escapedTitle}</h3>
                </div>
                <div class="confirm-dialog-body">
                    <p>${escapedMessage}</p>
                </div>
                <div class="confirm-dialog-footer">
                    <button class="confirm-dialog-btn confirm-dialog-cancel" data-action="cancel">
                        ${escapedCancelText}
                    </button>
                    <button class="confirm-dialog-btn ${confirmButtonClass}" data-action="confirm">
                        ${escapedConfirmText}
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Focus trap
        const focusableElements = overlay.querySelectorAll('button');
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        
        // Show dialog
        setTimeout(() => overlay.classList.add('show'), 10);
        firstFocusable.focus();
        
        // Handle button clicks
        const handleAction = (action) => {
            overlay.classList.remove('show');
            setTimeout(() => {
                overlay.remove();
                if (action === 'confirm' && options.onConfirm) {
                    // Support callback pattern for backward compatibility
                    options.onConfirm();
                }
                resolve(action === 'confirm');
            }, 300);
        };
        
        overlay.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', () => {
                handleAction(btn.getAttribute('data-action'));
            });
        });
        
        // Handle Escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                handleAction('cancel');
                document.removeEventListener('keydown', handleEscape);
            }
        };
        document.addEventListener('keydown', handleEscape);
        
        // Handle Enter key (confirm)
        const handleEnter = (e) => {
            if (e.key === 'Enter' && e.target === lastFocusable) {
                e.preventDefault();
                handleAction('confirm');
            }
        };
        overlay.addEventListener('keydown', handleEnter);
        
        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                handleAction('cancel');
            }
        });
    });
}

// Make functions globally available
window.showToast = showToast;
window.showConfirmDialog = showConfirmDialog;

// ========================================
// ERROR SUMMARY NAVIGATION (Accessibility)
// ========================================
(function () {
    const errorLinks = document.querySelectorAll('.error-summary-list a');

    errorLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetField = document.getElementById(targetId);

            if (targetField) {
                const headerHeight = document.querySelector('.site-header')?.offsetHeight || 0;
                const fieldPosition = targetField.getBoundingClientRect().top + window.pageYOffset;
                const offsetPosition = fieldPosition - headerHeight - 20;

                // Scroll to field with offset for fixed header
                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });

                // Focus the field after scroll completes
                setTimeout(function () {
                    targetField.focus({ preventScroll: true });

                    if (targetField.tagName === 'SELECT') {
                        targetField.click();
                    }

                    const formGroup = targetField.closest('.form-group');
                    if (formGroup) {
                        formGroup.style.animation = 'highlight-flash 1s';
                        setTimeout(() => {
                            formGroup.style.animation = '';
                        }, 1000);
                    }
                }, 500);
            }
        });
    });
})();

// ========================================
// FORM VALIDATION FEEDBACK
// ========================================
(function() {
  const requiredInputs = document.querySelectorAll('input[required], textarea[required], select[required]');

  requiredInputs.forEach(function(input) {
    input.addEventListener('blur', function() {
      const formGroup = input.closest('.form-group');
      if (!formGroup) return;

      if (input.value.trim() === '') {
        formGroup.classList.add('has-error');

        if (!formGroup.querySelector('.field-error')) {
          const errorDiv = document.createElement('div');
          errorDiv.className = 'field-error';
          errorDiv.textContent = 'Este campo é obrigatório.';
          errorDiv.setAttribute('role', 'alert');
          input.parentNode.insertBefore(errorDiv, input.nextSibling);
        }
      } else {
        formGroup.classList.remove('has-error');
        const errorDiv = formGroup.querySelector('.field-error');
        if (errorDiv && errorDiv.textContent === 'Este campo é obrigatório.') {
          errorDiv.remove();
        }
      }
    });

    // Remove error on input
    input.addEventListener('input', function() {
      const formGroup = input.closest('.form-group');
      if (formGroup && input.value.trim() !== '') {
        formGroup.classList.remove('has-error');
        const errorDiv = formGroup.querySelector('.field-error');
        if (errorDiv && errorDiv.textContent === 'Este campo é obrigatório.') {
          errorDiv.remove();
        }
      }
    });
  });
})();

// ========================================
// SMOOTH SCROLL FOR SKIP LINK
// ========================================
(function() {
  const skipLink = document.querySelector('.skip-link');
  if (!skipLink) return;

  skipLink.addEventListener('click', function(event) {
    event.preventDefault();
    const target = document.querySelector('#main-content');
    if (target) {
      target.setAttribute('tabindex', '-1');
      target.focus();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
})();

// ========================================
// BACK TO TOP BUTTON
// ========================================
(function() {
  // Create back to top button
  const backToTop = document.createElement('button');
  backToTop.className = 'back-to-top';
  backToTop.setAttribute('aria-label', 'Voltar ao topo');
  backToTop.innerHTML = '<i class="fas fa-arrow-up" aria-hidden="true"></i>';
  document.body.appendChild(backToTop);

  // Show/hide based on scroll position
  window.addEventListener('scroll', function() {
    if (window.pageYOffset > 300) {
      backToTop.classList.add('visible');
    } else {
      backToTop.classList.remove('visible');
    }
  });

  // Scroll to top on click
  backToTop.addEventListener('click', function() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });
})();

// ========================================
// DELETE CONFIRMATION DIALOG
// ========================================
(function() {
  const deleteLinks = document.querySelectorAll('a[href*="/excluir/"]');

  deleteLinks.forEach(function(link) {
    link.addEventListener('click', function(event) {
      event.preventDefault();
      const url = this.href;
      const editalTitle = this.closest('.edital-card')?.querySelector('.edital-title a')?.textContent || 'este edital';

      showConfirmDialog({
        title: 'Confirmar Exclusão',
        message: `Tem certeza que deseja excluir "${editalTitle}"? Esta ação não pode ser desfeita.`,
        confirmText: 'Excluir',
        confirmClass: 'btn-danger',
        onConfirm: function() {
          window.location.href = url;
        }
      });
    });
  });
})();

// ========================================
// KEYBOARD SHORTCUTS (Ctrl+K for search, Escape to clear)
// ========================================
(function() {
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-input, .search-input-enhanced');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();

                const hint = document.querySelector('.keyboard-hint');
                if (hint) {
                    hint.style.opacity = '1';
                    setTimeout(() => {
                        hint.style.opacity = '0.5';
                    }, 2000);
                }
            }
        }

        if (e.key === 'Escape') {
            const searchInput = document.querySelector('.search-input:focus, .search-input-enhanced:focus');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.value = '';
                const searchForm = searchInput.closest('form');
                if (searchForm) {
                    if (window.searchTimeout) {
                        clearTimeout(window.searchTimeout);
                        window.searchTimeout = null;
                    }

                    if (window.performSearch) {
                        window.performSearch();
                    } else {
                        searchForm.dispatchEvent(new Event('submit', { cancelable: true }));
                    }
                }
                searchInput.blur();
            }
        }
    });
})();

// ========================================
// SMOOTH SCROLL FOR ALL ANCHOR LINKS
// ========================================
(function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#' || href === '#!') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Smooth scroll for pagination and internal links
    document.querySelectorAll('a[href*="#"]').forEach(link => {
        if (link.hash) {
            link.addEventListener('click', function(e) {
                const target = document.querySelector(this.hash);
                if (target) {
                    e.preventDefault();
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        }
    });
})();



// ========================================
// MODAL FOCUS TRAP (A11Y-005)
// ========================================
(function() {
    // Function to trap focus inside modal
    function trapFocus(modal) {
        const focusableElements = modal.querySelectorAll(
            'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
        );

        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        // Focus first element when modal opens
        setTimeout(() => firstElement.focus(), 100);

        function handleTabKey(e) {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }

        function handleEscapeKey(e) {
            if (e.key === 'Escape') {
                closeModal(modal);
            }
        }

        modal.addEventListener('keydown', handleTabKey);
        modal.addEventListener('keydown', handleEscapeKey);

        modal._focusHandlers = { handleTabKey, handleEscapeKey };
    }

    function releaseFocus(modal) {
        if (modal._focusHandlers) {
            modal.removeEventListener('keydown', modal._focusHandlers.handleTabKey);
            modal.removeEventListener('keydown', modal._focusHandlers.handleEscapeKey);
            delete modal._focusHandlers;
        }
    }

    // Function to open modal
    function openModal(modal) {
        modal.classList.add('active');
        modal.setAttribute('aria-hidden', 'false');
        trapFocus(modal);
        document.body.style.overflow = 'hidden'; // Prevent background scrolling
    }

    // Function to close modal
    function closeModal(modal) {
        modal.classList.remove('active');
        modal.setAttribute('aria-hidden', 'true');
        releaseFocus(modal);
        document.body.style.overflow = ''; // Restore scrolling
    }

    let manualModalCount = 0;

    function openManualModal(modal) {
        if (!modal) return;
        manualModalCount++;
        modal.classList.remove('hidden');
        modal.classList.add('manual-modal-open');
        modal.setAttribute('aria-hidden', 'false');
        trapFocus(modal);
        document.body.style.overflow = 'hidden';
    }

    function closeManualModal(modal) {
        if (!modal) return;
        modal.classList.add('hidden');
        modal.classList.remove('manual-modal-open');
        modal.setAttribute('aria-hidden', 'true');
        releaseFocus(modal);
        manualModalCount = Math.max(0, manualModalCount - 1);
        if (manualModalCount === 0) {
            document.body.style.overflow = '';
        }
    }

    // Initialize modals
    document.addEventListener('DOMContentLoaded', function() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.setAttribute('aria-hidden', 'true');
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');

            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    closeModal(modal);
                }
            });

            const closeButtons = modal.querySelectorAll('[data-modal-close]');
            closeButtons.forEach(btn => {
                btn.addEventListener('click', () => closeModal(modal));
            });
        });

        // Open modal triggers
        document.querySelectorAll('[data-modal-open]').forEach(trigger => {
            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                const modalId = this.getAttribute('data-modal-open');
                const modal = document.getElementById(modalId);
                if (modal) {
                    openModal(modal);
                }
            });
        });
    });

    // Expose functions globally
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.openManualModal = openManualModal;
    window.closeManualModal = closeManualModal;
})();

// ========================================
// USER MENU DROPDOWN
// ========================================
(function() {
    const userMenuToggle = document.getElementById('user-menu-toggle');
    const userMenuDropdown = document.getElementById('user-menu') || document.getElementById('user-menu-dropdown');
    
    if (!userMenuToggle || !userMenuDropdown) return;
    
    function toggleMenu() {
        const isExpanded = userMenuToggle.getAttribute('aria-expanded') === 'true';
        userMenuToggle.setAttribute('aria-expanded', !isExpanded);
        // Support both 'hidden' (Tailwind) and 'show' (Bootstrap) class patterns
        if (userMenuDropdown.classList.contains('hidden')) {
            userMenuDropdown.classList.toggle('hidden');
        } else {
            userMenuDropdown.classList.toggle('show');
        }
    }
    
    userMenuToggle.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleMenu();
    });
    
    // Close on click outside
    document.addEventListener('click', function(e) {
        if (!userMenuToggle.contains(e.target) && !userMenuDropdown.contains(e.target)) {
            userMenuToggle.setAttribute('aria-expanded', 'false');
            // Support both class patterns
            if (userMenuDropdown.classList.contains('show')) {
                userMenuDropdown.classList.remove('show');
            } else {
                userMenuDropdown.classList.add('hidden');
            }
        }
    });
    
    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && userMenuToggle.getAttribute('aria-expanded') === 'true') {
            toggleMenu();
            userMenuToggle.focus();
        }
    });
    
    // Close on menu item click
    const menuItems = userMenuDropdown.querySelectorAll('.user-menu-item');
    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            userMenuToggle.setAttribute('aria-expanded', 'false');
            // Support both class patterns
            if (userMenuDropdown.classList.contains('show')) {
                userMenuDropdown.classList.remove('show');
            } else {
                userMenuDropdown.classList.add('hidden');
            }
        });
    });

    window.YPETECModal = {
        open(target) {
            const modal = typeof target === 'string' ? document.getElementById(target) : target;
            openManualModal(modal);
        },
        close(target) {
            const modal = typeof target === 'string' ? document.getElementById(target) : target;
            closeManualModal(modal);
        }
    };
})();

// ========================================
// PASSWORD VISIBILITY TOGGLE (A11Y-006)
// ========================================
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        const toggleButtons = document.querySelectorAll('[data-password-toggle]');

        toggleButtons.forEach(button => {
            const targetId = button.getAttribute('data-password-toggle');
            const icon = button.querySelector('i');

            button.addEventListener('click', function() {
                const input = document.getElementById(targetId);
                if (!input) return;

                const isVisible = input.type === 'text';
                input.type = isVisible ? 'password' : 'text';
                button.setAttribute('aria-pressed', (!isVisible).toString());

                if (icon) {
                    icon.classList.toggle('fa-eye', isVisible);
                    icon.classList.toggle('fa-eye-slash', !isVisible);
                }
            });
        });
    });
})();

// ========================================
// DJANGO MESSAGES TO TOAST NOTIFICATIONS
// ========================================
// Convert Django messages to toast notifications (T046 - Complete integration)
// Deferred execution to avoid blocking page render
(function () {
    // Wait for showToast function to be available
    function processMessages() {
        const messages = document.querySelectorAll(".messages .alert");
        
        if (messages.length === 0) return;

        // If showToast is not available yet, wait a bit
        if (typeof showToast !== "function") {
            setTimeout(processMessages, 100);
            return;
        }

        messages.forEach(function (messageEl) {
            // Skip if already processed
            if (messageEl.getAttribute("data-processed") === "true") return;

            const messageText = messageEl.textContent.trim();
            const messageTag =
                messageEl.getAttribute("data-message-tag") || "info";

            // Map Django message tags to toast types
            // Django default tags: debug, info, success, warning, error
            let toastType = "success";
            if (messageTag === "error" || messageTag === "danger") {
                toastType = "error";
            } else if (messageTag === "warning") {
                toastType = "warning";
            } else if (messageTag === "info" || messageTag === "debug") {
                toastType = "info";
            } else if (messageTag === "success") {
                toastType = "success";
            }

            // Show toast notification
            showToast(messageText, toastType);

            // Mark message as processed to avoid duplicates
            messageEl.setAttribute("data-processed", "true");
        });
    }

    // Process messages when DOM is ready (deferred)
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", function() {
            // Use requestIdleCallback if available, otherwise setTimeout
            if (window.requestIdleCallback) {
                requestIdleCallback(processMessages, { timeout: 2000 });
            } else {
                setTimeout(processMessages, 0);
            }
        });
    } else {
        // Use requestIdleCallback if available, otherwise setTimeout
        if (window.requestIdleCallback) {
            requestIdleCallback(processMessages, { timeout: 2000 });
        } else {
            setTimeout(processMessages, 0);
        }
    }
})();

// ========================================
// PAGE-SPECIFIC GSAP ANIMATION BOOTSTRAP
// ========================================
// Detect page via data-page on <body> and delegate to animations.js helpers
(function () {
  document.addEventListener('DOMContentLoaded', function () {
    const pageId = document.body && document.body.dataset
      ? document.body.dataset.page
      : '';
    const animations = window.AgroHubAnimations || {};

    if (!pageId) return;

    if (pageId === 'home' && typeof animations.initHomeAnimations === 'function') {
      animations.initHomeAnimations();
    } else if (pageId === 'startups' && typeof animations.initStartupShowcaseAnimations === 'function') {
      animations.initStartupShowcaseAnimations();
    } else if (pageId === 'editais-index' && typeof animations.initEditaisIndexAnimations === 'function') {
      animations.initEditaisIndexAnimations();
    }
  });
})();
