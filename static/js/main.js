// ========================================
// AgroHub - Main JavaScript
// ========================================

// ========================================
// AJAX FILTERS FOR INDEX PAGE WITH DEBOUNCING
// ========================================
(function () {
    const searchForm = document.querySelector('.search-form');
    const editaisGrid = document.querySelector('.editais-grid');
    const paginationContainer = document.querySelector('.pagination-container');
    const searchInput = document.querySelector('.search-input, .search-input-enhanced');

    if (!searchForm || !editaisGrid) return;

    let searchTimeout = null; // Initialize as null
    const SEARCH_DELAY = 500; // ms - debounce delay
    let isLoading = false;
    
    // Expose searchTimeout to window for keyboard shortcuts
    window.searchTimeout = searchTimeout;

    // Function to show skeleton loading
    function showSkeletonLoading() {
        if (isLoading) return;
        isLoading = true;

        editaisGrid.classList.add('loading');
        const skeletonCount = 6; // Show 6 skeleton cards
        const skeletonCards = [];

        for (let i = 0; i < skeletonCount; i++) {
            skeletonCards.push(`
                <article class="skeleton-card" role="listitem" aria-hidden="true">
                    <div class="skeleton skeleton-badge"></div>
                    <div class="skeleton skeleton-title"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text"></div>
                    <div class="skeleton skeleton-text" style="width: 60%;"></div>
                    <div class="skeleton skeleton-button"></div>
                </article>
            `);
        }

        editaisGrid.innerHTML = skeletonCards.join('');
    }

    // Function to perform search (exposed globally for keyboard shortcuts)
    window.performSearch = function() {
        if (isLoading) return;

        // Get form data
        const formData = new FormData(searchForm);
        const params = new URLSearchParams(formData);

        // Build URL with parameters
        const url = `${window.location.pathname}?${params.toString()}`;

        // Show skeleton loading
        showSkeletonLoading();

        // Fetch filtered results
        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.text())
            .then(html => {
                // Parse the response
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');

                // Extract the new grid content
                const newGrid = doc.querySelector('.editais-grid');
                const newPagination = doc.querySelector('.pagination-container');
                const newResultsCount = doc.querySelector('.search-results-count');

                // Update results count if exists
                const resultsCountElement = document.querySelector('.search-results-count');
                if (newResultsCount && resultsCountElement) {
                    resultsCountElement.innerHTML = newResultsCount.innerHTML;
                }

                if (newGrid) {
                    editaisGrid.classList.remove('loading');
                    editaisGrid.innerHTML = newGrid.innerHTML;
                    isLoading = false;

                    // Add fade-in animation
                    editaisGrid.classList.add('fade-in');
                    setTimeout(() => editaisGrid.classList.remove('fade-in'), 400);

                    // Announce to screen readers
                    announceToScreenReader(`Resultados atualizados. ${newGrid.children.length} editais encontrados.`);
                }

                if (newPagination && paginationContainer) {
                    paginationContainer.innerHTML = newPagination.innerHTML;
                    setupPaginationAjax();
                }

                // Update URL in browser (allow sharing filtered results)
                history.pushState({search: params.toString()}, '', url);

                // Smooth scroll to top of results
                editaisGrid.scrollIntoView({behavior: 'smooth', block: 'start'});
            })
            .catch(error => {
                console.error('Error fetching results:', error);
                editaisGrid.classList.remove('loading');
                isLoading = false;
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
            // Show clear button, hide hint
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
            // Hide clear button, show hint
            if (clearButton) {
                clearButton.style.display = 'none';
            }
            if (keyboardHint) {
                keyboardHint.style.display = 'flex';
            }
        }
    }

    // Debounced search on input
    if (searchInput) {
        // Initial state
        toggleSearchUI(searchInput, searchInput.value);

        searchInput.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            window.searchTimeout = null;
            
            // Toggle UI elements
            toggleSearchUI(this, this.value);
            
            // Visual feedback during typing
            const wrapper = this.closest('.search-input-wrapper');
            if (wrapper) {
                wrapper.classList.add('searching');
            }

            searchTimeout = setTimeout(() => {
                // Auto-submit after user stops typing (only if 3+ chars or empty)
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
                
                // Toggle UI to show hint again
                toggleSearchUI(input, '');
                
                // Clear any pending timeout
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

    // Intercept form submission (manual submit)
    if (searchForm) {
        searchForm.addEventListener('submit', function (event) {
            event.preventDefault();
            clearTimeout(searchTimeout);
            window.searchTimeout = null;
            window.performSearch();
        });
    }

    // Handle browser back/forward buttons
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
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');

                        const newGrid = doc.querySelector('.editais-grid');
                        const newPagination = doc.querySelector('.pagination-container');

                        if (newGrid) {
                            editaisGrid.classList.remove('loading');
                            editaisGrid.innerHTML = newGrid.innerHTML;
                            isLoading = false;

                            // Add fade-in animation
                            editaisGrid.classList.add('fade-in');
                            setTimeout(() => editaisGrid.classList.remove('fade-in'), 400);

                            // Announce to screen readers
                            announceToScreenReader(`Página atualizada. ${newGrid.children.length} editais exibidos.`);
                        }

                        if (newPagination && paginationContainer) {
                            paginationContainer.innerHTML = newPagination.innerHTML;
                            setupPaginationAjax();
                        }

                        history.pushState({}, '', url);
                        
                        // Smooth scroll to top of results
                        editaisGrid.scrollIntoView({behavior: 'smooth', block: 'start'});
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        editaisGrid.classList.remove('loading');
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

  menuToggle.addEventListener('click', function() {
    const isExpanded = menuToggle.getAttribute('aria-expanded') === 'true';

    // Toggle aria-expanded
    menuToggle.setAttribute('aria-expanded', !isExpanded);

    // Toggle menu open class
    navMenu.classList.toggle('menu-open');

    // Accessibility: trap focus inside menu when open
    if (!isExpanded) {
      // Menu is opening - focus first link
      const firstLink = navMenu.querySelector('a');
      if (firstLink) {
        setTimeout(() => firstLink.focus(), 100);
      }
    }
  });

  // Close menu when clicking outside
  document.addEventListener('click', function(event) {
    const isClickInsideMenu = navMenu.contains(event.target);
    const isClickOnToggle = menuToggle.contains(event.target);
    const isMenuOpen = menuToggle.getAttribute('aria-expanded') === 'true';

    if (isMenuOpen && !isClickInsideMenu && !isClickOnToggle) {
      menuToggle.setAttribute('aria-expanded', 'false');
      navMenu.classList.remove('menu-open');
    }
  });

  // Close menu on escape key
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape' && menuToggle.getAttribute('aria-expanded') === 'true') {
      menuToggle.setAttribute('aria-expanded', 'false');
      navMenu.classList.remove('menu-open');
      menuToggle.focus();
    }
  });

  // Close menu when window is resized to desktop size
  window.addEventListener('resize', function() {
    if (window.innerWidth > 767) {
      menuToggle.setAttribute('aria-expanded', 'false');
      navMenu.classList.remove('menu-open');
    }
  });

    // Close menu when navigating (clicking on links)
    document.querySelectorAll('.navbar-right a').forEach(function (link) {
        link.addEventListener('click', function () {
            if (window.innerWidth <= 767) {
                menuToggle.setAttribute('aria-expanded', 'false');
                navMenu.classList.remove('menu-open');
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
    const AUTOSAVE_INTERVAL = 10000; // 10 seconds
    let formChanged = false;
    let autosaveInterval;

    // Get all form fields
    const formFields = editalForm.querySelectorAll('input, textarea, select');

    // Check for saved data on page load
    window.addEventListener('DOMContentLoaded', function () {
        const savedData = localStorage.getItem(AUTOSAVE_KEY);

        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                const savedDate = new Date(data.timestamp);
                const now = new Date();
                const hoursSince = (now - savedDate) / (1000 * 60 * 60);

                // Only restore if saved within last 24 hours
                if (hoursSince < 24) {
                    if (confirm(`Encontramos um rascunho salvo em ${savedDate.toLocaleString()}. Deseja restaurá-lo?`)) {
                        restoreFormData(data.fields);
                        showToast('Rascunho restaurado com sucesso!');
                    } else {
                        localStorage.removeItem(AUTOSAVE_KEY);
                    }
                }
            } catch (e) {
                console.error('Error restoring autosave:', e);
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

    // Autosave function
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
            localStorage.setItem(AUTOSAVE_KEY, JSON.stringify(saveData));
            // Show subtle indicator
            showAutosaveIndicator();
        } catch (e) {
            console.error('Autosave failed:', e);
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

    // Show autosave indicator
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

    // Manual save button (optional - add to template if desired)
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


// Toast notification helper
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    // A11Y-002: Usar role="alert" para notificações importantes
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

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
                // Scroll to field
                targetField.scrollIntoView({behavior: 'smooth', block: 'center'});

                // Focus the field
                setTimeout(function () {
                    targetField.focus();

                    // Add visual highlight
                    const formGroup = targetField.closest('.form-group');
                    if (formGroup) {
                        formGroup.style.animation = 'highlight-flash 1s';
                        setTimeout(() => {
                            formGroup.style.animation = '';
                        }, 1000);
                    }
                }, 300);
            }
        });
    });
})();

// ========================================
// FORM VALIDATION FEEDBACK
// ========================================
(function() {
  // Add real-time validation feedback for required fields
  const requiredInputs = document.querySelectorAll('input[required], textarea[required], select[required]');

  requiredInputs.forEach(function(input) {
    input.addEventListener('blur', function() {
      const formGroup = input.closest('.form-group');
      if (!formGroup) return;

      if (input.value.trim() === '') {
        formGroup.classList.add('has-error');

        // Add error message if not already present
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
// GREEN CURVE PARALLAX EFFECT (Detail pages)
// ========================================
// Move a curva DEVAGAR conforme o scroll (parallax) para criar sensação de fluir pela curva
(function(){
  const curve = document.querySelector('.green-curve');
  if(!curve) return;

  function updateCurvePosition() {
    const scrolled = window.pageYOffset || document.documentElement.scrollTop;

    // A curva se move MAIS DEVAGAR que o scroll (fator 0.22 para movimento ultra suave)
    // Isso cria o efeito de você "passar" pela curva enquanto scrolla
    const parallaxFactor = 0.22;
    const translateY = -(scrolled * parallaxFactor);

    curve.style.transform = `translateY(${translateY}px)`;
  }

  // Atualiza na inicialização
  updateCurvePosition();

    // Atualiza conforme scrolla (com throttle via requestAnimationFrame + debouncing)
  let ticking = false;
    let scrollTimeout;

  window.addEventListener('scroll', function() {
      // Debounce: wait 10ms before processing
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(function () {
          if (!ticking) {
              window.requestAnimationFrame(function () {
                  updateCurvePosition();
                  ticking = false;
              });
              ticking = true;
          }
      }, 10);
  }, { passive: true });

  window.addEventListener('resize', updateCurvePosition);
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

function showConfirmDialog(options) {
    // Store the element that triggered the dialog
    const triggerElement = document.activeElement;

  // Create overlay
  const overlay = document.createElement('div');
  overlay.className = 'confirm-dialog-overlay';
    overlay.setAttribute('role', 'alertdialog');
    overlay.setAttribute('aria-modal', 'true');

  // Create dialog
  const dialog = document.createElement('div');
  dialog.className = 'confirm-dialog';
    dialog.setAttribute('role', 'document');
  dialog.setAttribute('aria-labelledby', 'dialog-title');
  dialog.setAttribute('aria-describedby', 'dialog-desc');

  dialog.innerHTML = `
    <h3 id="dialog-title">${options.title || 'Confirmar'}</h3>
    <p id="dialog-desc">${options.message || 'Tem certeza?'}</p>
    <div class="confirm-dialog-actions">
      <button class="btn btn-secondary" id="dialog-cancel">
        ${options.cancelText || 'Cancelar'}
      </button>
      <button class="btn ${options.confirmClass || 'btn-primary'}" id="dialog-confirm">
        ${options.confirmText || 'Confirmar'}
      </button>
    </div>
  `;

  overlay.appendChild(dialog);
  document.body.appendChild(overlay);

    // Get all focusable elements in dialog
    const focusableElements = dialog.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

  // Show dialog
  setTimeout(() => overlay.classList.add('active'), 10);

  // Focus first button for accessibility
    firstFocusable.focus();

    // Focus trap implementation
    function trapFocus(e) {
        if (e.key === 'Tab') {
            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstFocusable) {
                    lastFocusable.focus();
                    e.preventDefault();
                }
            } else {
                // Tab
                if (document.activeElement === lastFocusable) {
                    firstFocusable.focus();
                    e.preventDefault();
                }
            }
        }
    }

    dialog.addEventListener('keydown', trapFocus);

  // Handle cancel
  dialog.querySelector('#dialog-cancel').addEventListener('click', function() {
    closeDialog();
  });

  // Handle confirm
  dialog.querySelector('#dialog-confirm').addEventListener('click', function() {
    if (options.onConfirm) {
      options.onConfirm();
    }
    closeDialog();
  });

  // Close on overlay click
  overlay.addEventListener('click', function(e) {
    if (e.target === overlay) {
      closeDialog();
    }
  });

    // Handle escape key
  function handleEscape(e) {
    if (e.key === 'Escape') {
      closeDialog();
    }
  }

  document.addEventListener('keydown', handleEscape);

    // Close dialog function
  function closeDialog() {
    overlay.classList.remove('active');
    setTimeout(() => {
      overlay.remove();
      document.removeEventListener('keydown', handleEscape);
        dialog.removeEventListener('keydown', trapFocus);

        // Return focus to trigger element
        if (triggerElement && typeof triggerElement.focus === 'function') {
            triggerElement.focus();
        }
    }, 300);
  }
}

// ========================================
// KEYBOARD SHORTCUTS (Ctrl+K for search, Escape to clear)
// ========================================
(function() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus search input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.search-input, .search-input-enhanced');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
                
                // Show hint briefly
                const hint = document.querySelector('.keyboard-hint');
                if (hint) {
                    hint.style.opacity = '1';
                    setTimeout(() => {
                        hint.style.opacity = '0.5';
                    }, 2000);
                }
            }
        }

        // Escape to clear search when focused
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('.search-input:focus, .search-input-enhanced:focus');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.value = '';
                const searchForm = searchInput.closest('form');
                if (searchForm) {
                    // Clear any pending search timeout
                    if (window.searchTimeout) {
                        clearTimeout(window.searchTimeout);
                        window.searchTimeout = null;
                    }
                    
                    // Trigger search with empty value
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

// Development logging (remove in production or use proper logging)
if (typeof DEBUG !== 'undefined' && DEBUG) {
    console.log('✓ Back to top button initialized');
    console.log('✓ Confirmation dialogs initialized');
    console.log('✓ Keyboard shortcuts initialized (Ctrl+K for search)');
    console.log('✓ Smooth scroll initialized');
    console.log('✓ Loading skeletons initialized');
    console.log('✓ Debounced search initialized');
}

// ========================================
// LOADING STATE FOR CSV EXPORT (UI-004)
// ========================================
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        const exportLinks = document.querySelectorAll('a[href*="export_editais_csv"], .export-link');
        
        exportLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Adicionar estado de loading
                const originalHTML = this.innerHTML;
                this.innerHTML = '<i class="fas fa-spinner fa-spin" aria-hidden="true"></i> Exportando...';
                this.style.pointerEvents = 'none';
                this.style.opacity = '0.7';
                
                // Restaurar após 5 segundos (caso o download não inicie)
                setTimeout(() => {
                    this.innerHTML = originalHTML;
                    this.style.pointerEvents = '';
                    this.style.opacity = '';
                }, 5000);
            });
        });
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
        
        // Trap focus on Tab key
        function handleTabKey(e) {
            if (e.key !== 'Tab') return;
            
            if (e.shiftKey) {
                // Shift + Tab
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                // Tab
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        }
        
        // Close on Escape key
        function handleEscapeKey(e) {
            if (e.key === 'Escape') {
                closeModal(modal);
            }
        }
        
        modal.addEventListener('keydown', handleTabKey);
        modal.addEventListener('keydown', handleEscapeKey);
        
        // Store handlers for cleanup
        modal._focusHandlers = { handleTabKey, handleEscapeKey };
    }
    
    // Function to release focus trap
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
    
    // Initialize modals
    document.addEventListener('DOMContentLoaded', function() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.setAttribute('aria-hidden', 'true');
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            
            // Close on backdrop click
            modal.addEventListener('click', function(e) {
                if (e.target === modal) {
                    closeModal(modal);
                }
            });
            
            // Close buttons
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
})();

