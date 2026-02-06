// Centralized GSAP animations for AgroHub pages
// Each init function is safe to call once per page and guards against missing GSAP.

(function (window) {
  'use strict';

  function hasGSAP() {
    return typeof window.gsap !== 'undefined' && typeof window.ScrollTrigger !== 'undefined';
  }

  /**
   * Home page animations (hero, stats, pillars, helix, timeline, nav glass)
   */
  function initHomeAnimations() {
    if (!hasGSAP()) return;

    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;
    gsap.registerPlugin(ScrollTrigger);

    // Navigation Glass Effect
    const nav = document.querySelector('.site-header');
    if (nav) {
      ScrollTrigger.create({
        trigger: 'body',
        start: 'top -50',
        end: 'max',
        onEnter: () => {
          nav.classList.add('glass-nav', 'text-gray-800', 'shadow-sm');
          nav.classList.remove('bg-transparent', 'text-white');
        },
        onLeaveBack: () => {
          nav.classList.remove('glass-nav', 'text-gray-800', 'shadow-sm');
          nav.classList.add('bg-transparent', 'text-white');
        }
      });
    }

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Reveal Animations
    gsap.utils.toArray('.reveal-up').forEach((elem) => {
      // Skip animation if user prefers reduced motion
      if (prefersReducedMotion) {
        gsap.set(elem, { opacity: 1, y: 0 });
        return;
      }

      // Add will-change hint for better performance
      elem.style.willChange = 'transform, opacity';
      gsap.to(elem, {
        scrollTrigger: { trigger: elem, start: 'top 92%' },
        y: 0,
        opacity: 1,
        duration: 0.5,
        ease: 'power1.out',
        onComplete: function() {
          // Mark as animated to prevent fallback
          elem.classList.add('animated');
          // Remove will-change after animation completes
          elem.style.willChange = 'auto';
        }
      });
    });

    // Pillars stagger
    if (document.querySelector('#pillars-section')) {
      gsap.to('.pillar-card', {
        scrollTrigger: {
          trigger: '#pillars-section',
          start: 'top 80%'
        },
        opacity: 1,
        y: 0,
        duration: 0.7,
        stagger: 0.15,
        ease: 'power1.out'
      });
    }

    // Hero parallax
    if (document.querySelector('.hero-bg')) {
      gsap.to('.hero-bg', {
        scrollTrigger: { trigger: 'header', start: 'top top', end: 'bottom top', scrub: true },
        y: 150,
        scale: 1.2,
        ease: 'none'
      });
    }

    // Counters
    gsap.utils.toArray('.counter').forEach((counter) => {
      const target = parseInt(counter.getAttribute('data-target') || '0', 10);
      const obj = { value: 0 };
      gsap.to(obj, {
        value: target,
        duration: 1.8,
        snap: { value: 1 },
        scrollTrigger: { trigger: counter, start: 'top 88%' },
        ease: 'power1.inOut',
        onUpdate: () => {
          counter.innerText = String(Math.round(obj.value));
        }
      });
    });

    // Timeline progress line
    const progressLine = document.querySelector('#progress-line');
    const timelineSection = document.querySelector('.timeline-wrapper');
    if (progressLine && timelineSection) {
      // Ensure progress line is visible
      gsap.set(progressLine, { width: '0%', opacity: 1 });
      // Stop at 50% (phase 2 is current, so progress should stop at 1/2, not 2/3)
      gsap.to(progressLine, {
        width: '50%',
        duration: 0.8,
        ease: 'power2.out',
        scrollTrigger: { 
          trigger: timelineSection, 
          start: 'top 75%',
          once: true
        }
      });
      
      // Animate timeline items
      const timelineItems = document.querySelectorAll('.timeline-item');
      timelineItems.forEach((item, index) => {
        // Check if item should remain at reduced opacity (future phases)
        const shouldKeepOpacity = item.classList.contains('opacity-60');
        const targetOpacity = shouldKeepOpacity ? 0.6 : 1;
        
        gsap.fromTo(item,
          { opacity: 0, y: 30 },
          {
            opacity: targetOpacity,
            y: 0,
            duration: 0.7,
            delay: index * 0.12,
            ease: 'power1.out',
            scrollTrigger: {
              trigger: item,
              start: 'top 85%',
              once: true
            }
          }
        );
      });
    }
  }

  /**
   * Startups showcase animations (hero reveal, counters, cards)
   */
  function initStartupShowcaseAnimations() {
    if (!hasGSAP()) return;

    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;
    gsap.registerPlugin(ScrollTrigger);

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Hero animations
    const heroElems = document.querySelectorAll('.reveal-hero');
    if (heroElems.length) {
      // Skip animation if user prefers reduced motion
      if (prefersReducedMotion) {
        heroElems.forEach(elem => {
          gsap.set(elem, { opacity: 1, y: 0 });
          elem.classList.add('animated');
        });
        return;
      }

      // Add will-change hint for better performance
      heroElems.forEach(elem => {
        elem.style.willChange = 'transform, opacity';
      });
      gsap.from(heroElems, {
        y: 30,
        opacity: 0,
        duration: 0.7,
        stagger: 0.08,
        ease: 'power1.out',
        onComplete: function() {
          // Mark as animated to prevent fallback
          heroElems.forEach(elem => {
            elem.classList.add('animated');
            elem.style.willChange = 'auto';
          });
        }
      });
    }

    // Counters
    gsap.utils.toArray('.counter').forEach((counter) => {
      const target = parseInt(counter.getAttribute('data-target') || '0', 10);
      const obj = { value: 0 };
      gsap.to(obj, {
        value: target,
        duration: 1.8,
        snap: { value: 1 },
        scrollTrigger: { trigger: counter, start: 'top 92%' },
        ease: 'power2.out',
        onUpdate: () => {
          counter.innerText = String(Math.round(obj.value));
        }
      });
    });

    // Cards entrance animation
    const allCards = document.querySelectorAll('.startup-card');
    function animateCards(elements) {
      if (!elements || !elements.length) return;
      // Add will-change hint for better performance
      elements.forEach(card => {
        card.style.willChange = 'transform, opacity';
      });
      gsap.fromTo(
        elements,
        { y: 50, opacity: 0, scale: 0.95 },
        {
          y: 0,
          opacity: 1,
          scale: 1,
          duration: 0.8,
          stagger: 0.12,
          ease: 'power1.out',
          clearProps: 'transform',
          onComplete: function() {
            // Remove will-change after animation completes
            elements.forEach(card => {
              card.style.willChange = 'auto';
            });
          }
        }
      );
    }
    if (allCards.length) {
      animateCards(allCards);

      // Reveal on scroll for each card
      gsap.utils.toArray('.startup-card').forEach((card, index) => {
        // Add will-change hint for better performance
        card.style.willChange = 'transform, opacity';
        gsap.fromTo(
          card,
          { opacity: 0, y: 30 },
          {
            opacity: 1,
            y: 0,
            duration: 0.7,
            delay: index * 0.12,
            ease: 'power1.out',
            scrollTrigger: {
              trigger: card,
              start: 'top 88%',
              toggleActions: 'play none none none'
            },
            onComplete: function() {
              // Remove will-change after animation completes
              card.style.willChange = 'auto';
            }
          }
        );
      });
    }

    // Search form debounced submit (fallback – page reload, not AJAX)
    const searchInput = document.querySelector('form[action$="startups_showcase"] input[name="search"]');
    const searchForm = searchInput && searchInput.closest('form');
    let searchTimeout = null;
    const SEARCH_DELAY = 500;

    if (searchInput && searchForm) {
      searchInput.addEventListener('input', function () {
        window.clearTimeout(searchTimeout);
        searchTimeout = window.setTimeout(() => {
          if (this.value.length >= 3 || this.value.length === 0) {
            searchForm.submit();
          }
        }, SEARCH_DELAY);
      });

      searchInput.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          window.clearTimeout(searchTimeout);
          searchForm.submit();
        }
      });
    }
  }

  /**
   * Editais index animations (header, filters, cards, empty state)
   */
  function initEditaisIndexAnimations() {
    if (!hasGSAP()) return;

    const gsap = window.gsap;
    const ScrollTrigger = window.ScrollTrigger;
    gsap.registerPlugin(ScrollTrigger);

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Header immediate reveal
    const headerSection = document.querySelector('section.bg-gradient-to-r');
    if (headerSection) {
      const headerRevealElements = headerSection.querySelectorAll('.reveal-up');
      if (headerRevealElements.length) {
        if (prefersReducedMotion) {
          headerRevealElements.forEach(elem => {
            gsap.set(elem, { opacity: 1, y: 0 });
            elem.classList.add('animated');
          });
        } else {
          gsap.to(headerRevealElements, {
            y: 0,
            opacity: 1,
            duration: 0.6,
            stagger: 0.06,
            ease: 'power1.out',
            delay: 0.05,
            onComplete: function() {
              headerRevealElements.forEach(elem => {
                elem.classList.add('animated');
              });
            }
          });
        }
      }
    }

    // Below-fold reveal (filters/search/badges)
    const mainContentSection = document.querySelector('section.container');
    if (mainContentSection) {
      const belowFoldReveal = mainContentSection.querySelectorAll('.reveal-up');
      belowFoldReveal.forEach((elem) => {
        if (prefersReducedMotion) {
          gsap.set(elem, { opacity: 1, y: 0 });
          elem.classList.add('animated');
        } else {
          gsap.to(elem, {
            scrollTrigger: { trigger: elem, start: 'top 88%' },
            y: 0,
            opacity: 1,
            duration: 0.6,
            ease: 'power1.out',
            onComplete: function() {
              elem.classList.add('animated');
            }
          });
        }
      });
    }

    // Edital cards staggered fade-in
    const editalCards = document.querySelectorAll('.edital-card');
    if (editalCards.length) {
      // Check for reduced motion
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      if (prefersReducedMotion) {
        editalCards.forEach(card => {
          gsap.set(card, { opacity: 1, y: 0 });
        });
        return;
      }

      // Add will-change hint for better performance
      editalCards.forEach(card => {
        card.style.willChange = 'transform, opacity';
      });
      gsap.set(editalCards, { opacity: 0, y: 20 });

      const editaisGrid = document.querySelector('.editais-grid');
      const runAnimation = () => {
        if (!editaisGrid) return;
        const rect = editaisGrid.getBoundingClientRect();
        const isInViewport = rect.top < window.innerHeight * 0.95;

        const animCfg = {
          opacity: 1,
          y: 0,
          duration: 0.6,
          stagger: 0.08,
          ease: 'power1.out',
          onComplete: function() {
            // Remove will-change after animation completes
            editalCards.forEach(card => {
              card.style.willChange = 'auto';
            });
          }
        };

        if (isInViewport) {
          gsap.to(editalCards, animCfg);
        } else {
          gsap.to(editalCards, {
            ...animCfg,
            scrollTrigger: {
              trigger: '.editais-grid',
              start: 'top 92%',
              once: true
            }
          });
        }
      };

      runAnimation();
    }

    // Empty state animation
    const emptyState = document.querySelector('.empty-state-container, .empty-state');
    if (emptyState) {
      gsap.from(emptyState, {
        scrollTrigger: { trigger: emptyState, start: 'top 88%' },
        opacity: 0,
        scale: 0.95,
        y: 20,
        duration: 0.9,
        ease: 'power1.out'
      });
    }

    // Observe AJAX-updated cards (integrates with main.js filters)
    const editaisGrid = document.querySelector('.editais-grid');
    if (editaisGrid) {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (!mutation.addedNodes.length) return;
          const newCards = document.querySelectorAll('.edital-card:not(.animated)');
          if (!newCards.length) return;

          // Safety check: ensure GSAP is available before using it
          if (!hasGSAP()) {
            // Fallback: use CSS classes for animation
            newCards.forEach((card) => {
              card.style.opacity = '0';
              card.style.transform = 'translateY(30px)';
              setTimeout(() => {
                card.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
                card.classList.add('animated');
              }, 10);
            });
            return;
          }

          newCards.forEach((card) => {
            card.style.willChange = 'transform, opacity';
            gsap.set(card, { opacity: 0, y: 30 });
          });

          gsap.to(newCards, {
            opacity: 1,
            y: 0,
            duration: 0.6,
            stagger: 0.08,
            ease: 'power1.out',
            onComplete: () => {
              newCards.forEach((card) => {
                card.classList.add('animated');
                card.style.willChange = 'auto';
              });
            }
          });
        });
      });

      observer.observe(editaisGrid, { childList: true, subtree: true });

      // Safety: ensure cards visible even if animations are skipped
      window.setTimeout(() => {
        const allCards = document.querySelectorAll('.edital-card');
        allCards.forEach((card) => {
          const opacity = parseFloat(window.getComputedStyle(card).opacity || '1');
          if (opacity < 0.5) {
            if (hasGSAP()) {
              gsap.set(card, { opacity: 1, y: 0, clearProps: 'all' });
            } else {
              // Fallback: use CSS
              card.style.opacity = '1';
              card.style.transform = 'translateY(0)';
              card.style.transition = 'none';
            }
          }
        });
      }, 2000);
    }

    // Ctrl+K shortcut focusing search (page-specific fallback)
    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        const searchInput = document.getElementById('search-editais');
        if (searchInput) {
          e.preventDefault();
          searchInput.focus();
          searchInput.select();
        }
      }
    });
  }

  window.AgroHubAnimations = {
    initHomeAnimations,
    initStartupShowcaseAnimations,
    initEditaisIndexAnimations
  };

  // Initialize animations when GSAP is ready
  function initAnimationsWhenReady() {
    if (hasGSAP()) {
      // GSAP is available, initialize animations
      const currentURL = window.location.pathname;
      if (currentURL === '/' || currentURL === '/home/') {
        initHomeAnimations();
      } else if (currentURL.includes('startups')) {
        initStartupShowcaseAnimations();
      } else if (currentURL.includes('editais')) {
        initEditaisIndexAnimations();
      }
    } else {
      // GSAP not available yet, wait and retry
      window._gsapRetryCount = (window._gsapRetryCount || 0) + 1;
      if (window._gsapRetryCount < 10) { // Max 10 retries (5 seconds)
        setTimeout(initAnimationsWhenReady, 500);
      }
    }
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAnimationsWhenReady);
  } else {
    initAnimationsWhenReady();
  }
})(window);


