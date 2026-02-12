// Editais index only: AJAX filters + pagination + shortcuts
(function () {
  const searchForm = document.querySelector('.search-form');
  const editaisGrid = document.querySelector('.editais-grid');
  const paginationContainer = document.querySelector('.pagination-container');
  const searchInput = document.querySelector('.search-input, .search-input-enhanced, #search-editais');
  const skeletonTemplate = document.getElementById('edital-skeleton-template');
  const templateSkeletonMarkup = skeletonTemplate ? skeletonTemplate.innerHTML.trim() : null;

  if (!searchForm || !editaisGrid) return;

  let searchTimeout = null;
  const SEARCH_DELAY = 500;
  let isLoading = false;
  let searchAbortController = null;

  // Expose searchTimeout to window for keyboard shortcuts
  window.searchTimeout = searchTimeout;

  function showSkeletonLoading() {
    if (isLoading) return;
    isLoading = true;

    editaisGrid.classList.add('loading');

    if (!templateSkeletonMarkup) {
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

  function announceToScreenReader(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('role', 'status');
    announcement.setAttribute('aria-live', 'polite');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    document.body.appendChild(announcement);

    setTimeout(() => announcement.remove(), 1000);
  }

  // Perform search (exposed globally for keyboard shortcuts)
  window.performSearch = function () {
    if (isLoading) return;

    const formData = new FormData(searchForm);
    const filterForm = document.getElementById('filter-form');

    if (filterForm) {
      const filterFormData = new FormData(filterForm);
      const filterValues = {};
      const filterInputs = filterForm.querySelectorAll('input, select, textarea');

      for (const [key, value] of filterFormData.entries()) {
        filterValues[key] = value;
      }

      filterInputs.forEach((input) => {
        if (!input.name) return;
        let value = '';
        if (input.type === 'checkbox' || input.type === 'radio') {
          value = input.checked ? input.value : '';
        } else {
          value = input.value || '';
        }
        if (value && value.trim() !== '') {
          filterValues[input.name] = value;
        }
      });

      for (const [key, value] of Object.entries(filterValues)) {
        if (value && String(value).trim() !== '') {
          formData.set(key, value);
        }
      }
    }

    const params = new URLSearchParams(formData);
    const url = `${window.location.pathname}?${params.toString()}`;

    showSkeletonLoading();

    // Cancel any in-flight search request
    if (searchAbortController) searchAbortController.abort();
    searchAbortController = new AbortController();

    fetch(url, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
      signal: searchAbortController.signal,
    })
      .then((response) => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.text();
      })
      .then((html) => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        const parserError = doc.querySelector('parsererror');
        if (parserError) throw new Error('Failed to parse HTML response');

        const newGrid = doc.querySelector('.editais-grid');
        const newPagination = doc.querySelector('.pagination-container');
        const noResults =
          doc.querySelector('#no-results') ||
          doc.querySelector('.empty-state') ||
          doc.querySelector('.empty-state-container') ||
          doc.querySelector('div.empty-state');

        if (newGrid) {
          editaisGrid.classList.remove('loading');
          if (!editaisGrid.classList.contains('grid')) {
            editaisGrid.classList.remove('flex', 'justify-center');
            editaisGrid.classList.add('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
          }
          editaisGrid.innerHTML = newGrid.innerHTML;
          isLoading = false;

          editaisGrid.classList.add('fade-in');
          setTimeout(() => editaisGrid.classList.remove('fade-in'), 400);

          const cardCount = newGrid.querySelectorAll('.edital-card').length;
          announceToScreenReader(`Resultados atualizados. ${cardCount} editais encontrados.`);
        } else if (noResults) {
          editaisGrid.classList.remove('loading');
          editaisGrid.classList.remove('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
          editaisGrid.classList.add('flex', 'justify-center');
          editaisGrid.innerHTML = noResults.outerHTML;
          isLoading = false;
          announceToScreenReader('Nenhum resultado encontrado.');
        } else {
          editaisGrid.classList.remove('loading');
          isLoading = false;
          editaisGrid.innerHTML =
            '<div class="text-center py-12 text-red-500">Erro ao carregar resultados. Por favor, recarregue a página.</div>';
          if (typeof window.showToast === 'function') {
            window.showToast('Erro ao processar resposta do servidor. Tente novamente.', 'error');
          }
        }

        if (newPagination && paginationContainer) {
          paginationContainer.innerHTML = newPagination.innerHTML;
          setupPaginationAjax();
        } else if (paginationContainer) {
          paginationContainer.innerHTML = '';
        }

        const wrapper = searchForm.querySelector('.search-input-wrapper');
        if (wrapper) wrapper.classList.remove('searching');
        const clearBtn = document.querySelector('.clear-filters-btn');
        if (clearBtn) clearBtn.classList.remove('loading');

        history.pushState({ search: params.toString() }, '', url);
        editaisGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
      })
      .catch((err) => {
        if (err && err.name === 'AbortError') return;
        editaisGrid.classList.remove('loading');
        isLoading = false;

        const wrapper = searchForm.querySelector('.search-input-wrapper');
        if (wrapper) wrapper.classList.remove('searching');
        const clearBtn = document.querySelector('.clear-filters-btn');
        if (clearBtn) clearBtn.classList.remove('loading');

        if (typeof window.showToast === 'function') {
          window.showToast('Erro ao filtrar editais. Tente novamente.', 'error');
        }
      });
  };

  function toggleSearchUI(inputElement, value) {
    if (!inputElement) return;
    const wrapper = inputElement.closest('.search-input-wrapper') || inputElement.closest('.relative');
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
      if (keyboardHint) keyboardHint.style.display = 'none';
    } else {
      if (clearButton) clearButton.style.display = 'none';
      if (keyboardHint) keyboardHint.style.display = 'flex';
    }
  }

  if (searchInput) {
    toggleSearchUI(searchInput, searchInput.value);

    searchInput.addEventListener('input', function () {
      clearTimeout(searchTimeout);
      window.searchTimeout = null;

      toggleSearchUI(this, this.value);

      const wrapper = this.closest('.search-input-wrapper');
      if (wrapper) wrapper.classList.add('searching');

      searchTimeout = setTimeout(() => {
        if (this.value.length >= 3 || this.value.length === 0) {
          window.performSearch();
        }
        if (wrapper) wrapper.classList.remove('searching');
        window.searchTimeout = null;
      }, SEARCH_DELAY);
      window.searchTimeout = searchTimeout;
    });
  }

  document.addEventListener('click', function (e) {
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
        }
      }
    }
  });

  const clearFiltersBtn = document.querySelector('.clear-filters-btn');
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', function (e) {
      e.preventDefault();
      const form = this.closest('form');
      if (form) {
        form.querySelectorAll('input[type="text"], select').forEach((input) => {
          if (input.type === 'text') input.value = '';
          else if (input.tagName === 'SELECT') input.selectedIndex = 0;
        });
        window.location.href = window.location.pathname;
      }
    });
  }

  function setupFilterHandlers() {
    const filterForm = document.getElementById('filter-form');
    if (!filterForm) return;

    const filterInputs = Array.from(filterForm.querySelectorAll('select[name], input[type="date"][name]'));

    filterInputs.forEach((input) => {
      if (input.hasAttribute('data-filter-listener-attached')) return;
      input.setAttribute('data-filter-listener-attached', 'true');

      input.addEventListener('change', function () {
        this.classList.add('loading');
        this.disabled = true;

        const wrapper = this.closest('form');
        if (wrapper) wrapper.classList.add('searching');

        const clearBtn = document.querySelector('.clear-filters-btn');
        if (clearBtn) clearBtn.classList.add('loading');

        setTimeout(() => {
          if (window.performSearch) window.performSearch();

          if (wrapper) wrapper.classList.remove('searching');
          if (clearBtn) clearBtn.classList.remove('loading');
          this.classList.remove('loading');
          this.disabled = false;
        }, 300);
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupFilterHandlers);
  } else {
    setTimeout(setupFilterHandlers, 100);
  }

  if (searchForm) {
    searchForm.addEventListener('submit', function (event) {
      event.preventDefault();
      clearTimeout(searchTimeout);
      window.searchTimeout = null;
      const wrapper = searchForm.querySelector('.search-input-wrapper');
      if (wrapper) wrapper.classList.add('searching');
      window.performSearch();
    });
  }

  window.addEventListener('popstate', function (event) {
    if (event.state && event.state.search) {
      window.location.search = event.state.search;
    }
  });

  function setupPaginationAjax() {
    const paginationLinks = document.querySelectorAll('.pagination .page-link, .pagination-container .page-link');
    paginationLinks.forEach((link) => {
      link.addEventListener('click', function (event) {
        event.preventDefault();
        const url = this.href;
        showSkeletonLoading();

        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
          .then((response) => {
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            return response.text();
          })
          .then((html) => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const parserError = doc.querySelector('parsererror');
            if (parserError) throw new Error('Failed to parse HTML response');

            const newGrid = doc.querySelector('.editais-grid');
            const newPagination = doc.querySelector('.pagination-container');
            const noResults = doc.querySelector('#no-results') || doc.querySelector('.empty-state');

            if (newGrid) {
              editaisGrid.classList.remove('loading');
              if (!editaisGrid.classList.contains('grid')) {
                editaisGrid.classList.remove('flex', 'justify-center');
                editaisGrid.classList.add('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
              }
              editaisGrid.innerHTML = newGrid.innerHTML;
              isLoading = false;

              editaisGrid.classList.add('fade-in');
              setTimeout(() => editaisGrid.classList.remove('fade-in'), 400);

              const cardCount = newGrid.querySelectorAll('.edital-card').length;
              announceToScreenReader(`Página atualizada. ${cardCount} editais exibidos.`);
            } else if (noResults) {
              editaisGrid.classList.remove('loading');
              editaisGrid.classList.remove('grid', 'grid-cols-1', 'md:grid-cols-2', 'lg:grid-cols-3');
              editaisGrid.classList.add('flex', 'justify-center');
              editaisGrid.innerHTML = noResults.outerHTML;
              isLoading = false;
              announceToScreenReader('Nenhum resultado encontrado.');
            } else {
              editaisGrid.classList.remove('loading');
              isLoading = false;
              if (typeof window.showToast === 'function') {
                window.showToast('Erro ao processar resposta. Tente novamente.', 'error');
              }
            }

            if (newPagination && paginationContainer) {
              paginationContainer.innerHTML = newPagination.innerHTML;
              setupPaginationAjax();
            } else if (paginationContainer) {
              paginationContainer.innerHTML = '';
            }

            history.pushState({}, '', url);
            editaisGrid.scrollIntoView({ behavior: 'smooth', block: 'start' });
          })
          .catch(() => {
            editaisGrid.classList.remove('loading');
            isLoading = false;
            if (typeof window.showToast === 'function') {
              window.showToast('Erro ao carregar página. Tente novamente.', 'error');
            }
          });
      });
    });
  }

  setupPaginationAjax();

  // Ctrl+K focuses search; Escape clears it
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      const input = document.querySelector('#search-editais, .search-input, .search-input-enhanced');
      if (input) {
        input.focus();
        input.select();
      }
    }
    if (e.key === 'Escape') {
      const input = document.querySelector('#search-editais');
      if (input && document.activeElement === input) {
        input.value = '';
        if (window.searchTimeout) {
          clearTimeout(window.searchTimeout);
          window.searchTimeout = null;
        }
        if (window.performSearch) window.performSearch();
        input.blur();
      }
    }
  });
})();

