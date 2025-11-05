console.log('AgroHub static JS loaded');

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
})();

// ========================================
// FORM LOADING STATES
// ========================================
(function() {
  const forms = document.querySelectorAll('form#edital-form');

  forms.forEach(function(form) {
    form.addEventListener('submit', function(event) {
      const submitBtn = form.querySelector('#submit-btn');

      if (submitBtn && !submitBtn.classList.contains('loading')) {
        // Add loading state
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;

        // If form validation fails, remove loading state after a moment
        setTimeout(function() {
          // Check if form is still on page (not redirected)
          if (document.contains(form)) {
            const hasErrors = form.querySelector('.has-error, .field-error, .alert-error');
            if (hasErrors) {
              submitBtn.classList.remove('loading');
              submitBtn.disabled = false;
            }
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

  // Atualiza conforme scrolla (com throttle leve via requestAnimationFrame)
  let ticking = false;
  window.addEventListener('scroll', function() {
    if (!ticking) {
      window.requestAnimationFrame(function() {
        updateCurvePosition();
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });

  window.addEventListener('resize', updateCurvePosition);
})();

console.log('✓ Mobile menu initialized');
console.log('✓ Form loading states initialized');
console.log('✓ Form validation initialized');
console.log('✓ Accessibility features initialized');

