// --- MOBILE MENU TOGGLE ---
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
      // Reset opacity and transform after transition
      setTimeout(() => {
        if (!navMenu.classList.contains('menu-open')) {
          navMenu.style.opacity = '';
          navMenu.style.transform = '';
        }
      }, 400); // Match transition duration
    }
  });

  // Helper function to close menu
  function closeMenu() {
    menuToggle.setAttribute('aria-expanded', 'false');
    navMenu.style.maxHeight = '0';
    navMenu.classList.remove('menu-open');
    // Ensure opacity and transform reset after transition completes
    // The CSS transition will handle the animation, but we ensure state is correct
    setTimeout(() => {
      if (!navMenu.classList.contains('menu-open')) {
        navMenu.style.opacity = '';
        navMenu.style.transform = '';
      }
    }, 400); // Match transition duration
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
  // Use matchMedia to align with Tailwind's md breakpoint (768px)
  const mediaQuery = window.matchMedia('(min-width: 768px)');
  
  function handleResize() {
    cachedMenuHeight = null;
    if (mediaQuery.matches) {
      closeMenu();
    }
  }
  
  window.addEventListener('resize', handleResize);
  // Also check on initial load
  if (mediaQuery.matches) {
    closeMenu();
  }

    // Close menu when navigating (clicking on links)
    document.querySelectorAll('.navbar-right a').forEach(function (link) {
        link.addEventListener('click', function () {
            if (!mediaQuery.matches) {
                closeMenu();
            }
        });
    });
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

// --- ERROR SUMMARY NAVIGATION ---
(function () {
    const errorLinks = document.querySelectorAll('.error-summary-list a');

    // Helper function to scroll to and highlight an error field
    function scrollToErrorField(targetField) {
        if (!targetField) return;

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

    // Handle clicks on error summary links
    errorLinks.forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').substring(1);
            const targetField = document.getElementById(targetId);
            scrollToErrorField(targetField);
        });
    });

    // Auto-scroll to first error field on page load (for server-side validation errors)
    if (errorLinks.length > 0) {
        // Wait for page to fully render before scrolling
        setTimeout(function() {
            const firstErrorLink = errorLinks[0];
            if (firstErrorLink) {
                const targetId = firstErrorLink.getAttribute('href').substring(1);
                const targetField = document.getElementById(targetId);
                scrollToErrorField(targetField);
            }
        }, 100);
    } else {
        // Check for form fields with error classes (fallback for forms without error summary)
        const firstErrorField = document.querySelector('.form-group.has-error input, .form-group.has-error textarea, .form-group.has-error select, .is-invalid, [aria-invalid="true"]');
        if (firstErrorField) {
            setTimeout(function() {
                scrollToErrorField(firstErrorField);
            }, 100);
        }
    }
})();

// --- FORM VALIDATION FEEDBACK ---
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

// --- BACK TO TOP BUTTON ---
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

// --- DELETE CONFIRMATION DIALOG ---
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

// --- SMOOTH SCROLL FOR ANCHOR LINKS ---
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



// --- MODAL FOCUS TRAP ---
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

// --- USER MENU DROPDOWN ---
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

// --- PASSWORD VISIBILITY TOGGLE ---
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

// --- DJANGO MESSAGES TO TOAST ---
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

// --- PAGE-SPECIFIC GSAP BOOTSTRAP ---
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
