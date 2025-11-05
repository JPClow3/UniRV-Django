// ========================================
// AgroHub - Main JavaScript
// ========================================

// ========================================
// AJAX FILTERS FOR INDEX PAGE
// ========================================
(function () {
    const searchForm = document.querySelector('.search-form');
    const editaisGrid = document.querySelector('.editais-grid');
    const paginationContainer = document.querySelector('.pagination-container');

    if (!searchForm || !editaisGrid) return;

    // Intercept form submission
    searchForm.addEventListener('submit', function (event) {
        event.preventDefault();

        // Get form data
        const formData = new FormData(searchForm);
        const params = new URLSearchParams(formData);

        // Build URL with parameters
        const url = `${window.location.pathname}?${params.toString()}`;

        // Show loading state
        editaisGrid.style.opacity = '0.5';
        editaisGrid.style.pointerEvents = 'none';

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

                if (newGrid) {
                    editaisGrid.innerHTML = newGrid.innerHTML;
                    editaisGrid.style.opacity = '1';
                    editaisGrid.style.pointerEvents = 'auto';

                    // Re-initialize favorite buttons for new content
                    if (window.setupFavoriteButtons) {
                        window.setupFavoriteButtons();
                    }
                }

                if (newPagination && paginationContainer) {
                    paginationContainer.innerHTML = newPagination.innerHTML;
                    setupPaginationAjax();
                }

                // Update URL in browser (allow sharing filtered results)
                history.pushState({search: params.toString()}, '', url);

                // Scroll to top of results
                editaisGrid.scrollIntoView({behavior: 'smooth', block: 'start'});
            })
            .catch(error => {
                console.error('Error fetching results:', error);
                editaisGrid.style.opacity = '1';
                editaisGrid.style.pointerEvents = 'auto';
                showToast('Erro ao filtrar editais. Tente novamente.', 'error');
            });
    });

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

                editaisGrid.style.opacity = '0.5';

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
                            editaisGrid.innerHTML = newGrid.innerHTML;
                            editaisGrid.style.opacity = '1';

                            // Re-initialize favorite buttons
                            if (window.setupFavoriteButtons) {
                                window.setupFavoriteButtons();
                            }
                        }

                        if (newPagination && paginationContainer) {
                            paginationContainer.innerHTML = newPagination.innerHTML;
                            setupPaginationAjax();
                        }

                        history.pushState({}, '', url);
                        editaisGrid.scrollIntoView({behavior: 'smooth', block: 'start'});
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        editaisGrid.style.opacity = '1';
                    });
            });
        });
    }

    // Initial setup for pagination
    setupPaginationAjax();
})();

// ========================================
// FAVORITE TOGGLE FUNCTIONALITY (Detail + Cards)
// ========================================
(function () {
    // Setup favorite buttons (works for both detail page and cards)
    window.setupFavoriteButtons = function () {
        const favoriteButtons = document.querySelectorAll('.favorite-btn, .favorite-btn-card');

        favoriteButtons.forEach(function (btn) {
            // Remove old listener by cloning
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);

            newBtn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();

                const editalId = this.dataset.editalId;
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                if (!csrfToken) {
                    window.location.href = '/admin/login/?next=' + window.location.pathname;
                    return;
                }

                // Show loading state
                this.disabled = true;
                const icon = this.querySelector('i');
                const originalClass = icon.className;
                icon.className = 'fas fa-spinner fa-spin';

                fetch(`/edital/${editalId}/toggle-favorite/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    }
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            this.classList.toggle('favorited');
                            icon.className = originalClass;

                            const text = this.querySelector('.favorite-text');
                            if (text) {
                                text.textContent = data.is_favorited ? 'Favoritado' : 'Favoritar';
                            }

                            const currentLabel = data.is_favorited ? 'Remover dos favoritos' : 'Adicionar aos favoritos';
                            this.setAttribute('aria-label', currentLabel);
                            this.setAttribute('title', currentLabel);

                            // Show toast message
                            showToast(data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        icon.className = originalClass;
                        showToast('Erro ao favoritar. Tente novamente.', 'error');
                    })
                    .finally(() => {
                        this.disabled = false;
                    });
            });
        });
    };

    // Initial setup
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', window.setupFavoriteButtons);
    } else {
        window.setupFavoriteButtons();
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
            }
        });
    });
})();

// ========================================
// FAVORITE TOGGLE FUNCTIONALITY
// ========================================
(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const favoriteButtons = document.querySelectorAll('.favorite-btn');

        favoriteButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                const editalId = this.dataset.editalId;
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                // Show loading state
                this.disabled = true;
                const icon = this.querySelector('i');
                const originalClass = icon.className;
                icon.className = 'fas fa-spinner fa-spin';

                fetch(`/edital/${editalId}/toggle-favorite/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    }
                })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            this.classList.toggle('favorited');
                            icon.className = originalClass;

                            const text = this.querySelector('.favorite-text');
                            if (text) {
                                text.textContent = data.is_favorited ? 'Favoritado' : 'Favoritar';
                            }

                            this.setAttribute('aria-label',
                                data.is_favorited ? 'Remover dos favoritos' : 'Adicionar aos favoritos'
                            );

                            // Show toast message
                            showToast(data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        icon.className = originalClass;
                        showToast('Erro ao favoritar. Tente novamente.', 'error');
                    })
                    .finally(() => {
                        this.disabled = false;
                    });
            });
        });
    });
})();

// Toast notification helper
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');

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

console.log('✓ Back to top button initialized');
console.log('✓ Confirmation dialogs initialized');

