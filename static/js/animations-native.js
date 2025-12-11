// Native animations using Intersection Observer (no GSAP dependency)
// Provides simple fade-in animations for elements with .reveal-up class
// This is a lightweight alternative to animations.js for pages that don't need complex GSAP animations

(function() {
    'use strict';

    // Module-level initialization lock to prevent duplicate script execution
    // This is checked immediately when the script loads, before any functions are defined
    const moduleInitKey = '_agrohubAnimationsNativeModuleInit';
    if (window[moduleInitKey]) {
        // Script already loaded and initialized, skip entirely
        return;
    }
    window[moduleInitKey] = true;

    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Shared Intersection Observer instance (created once, reused)
    // Use window property to persist across script reloads
    if (!window._agrohubAnimationsInitialized) {
        window._agrohubAnimationsInitialized = false;
    }
    if (!window._agrohubScrollHandlerAttached) {
        window._agrohubScrollHandlerAttached = false;
    }
    let revealObserver = null;

    // Create shared Intersection Observer for fade-in animations
    function createRevealObserver() {
        if (revealObserver) return revealObserver;

        revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const elem = entry.target;
                    
                    // Add animation classes
                    elem.style.opacity = '1';
                    elem.style.transform = 'translateY(0)';
                    elem.style.transition = 'opacity 0.4s ease-out, transform 0.4s ease-out';
                    elem.classList.add('animated');
                    
                    // Stop observing once animated
                    revealObserver.unobserve(elem);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        return revealObserver;
    }

    // Simple fade-in animation using Intersection Observer
    function initRevealAnimations() {
        // Only get elements that haven't been animated yet
        const revealElements = document.querySelectorAll('.reveal-up:not(.animated)');
        
        if (revealElements.length === 0) return;

        // If user prefers reduced motion, just show elements immediately
        if (prefersReducedMotion) {
            revealElements.forEach(elem => {
                elem.style.opacity = '1';
                elem.style.transform = 'translateY(0)';
                elem.classList.add('animated');
            });
            return;
        }

        // Get or create shared observer
        const observer = createRevealObserver();

        // Initialize elements and start observing
        revealElements.forEach(elem => {
            // Set initial state
            elem.style.opacity = '0';
            elem.style.transform = 'translateY(20px)';
            
            // Start observing
            observer.observe(elem);
        });
    }

    // Navigation glass effect on scroll (simple version without GSAP)
    function initNavGlassEffect() {
        // Prevent duplicate scroll listeners using global flag
        if (window._agrohubScrollHandlerAttached) return;
        
        const nav = document.querySelector('.site-header');
        if (!nav) return;

        let lastScrollY = window.scrollY;

        function handleScroll() {
            const currentScrollY = window.scrollY;
            
            if (currentScrollY > 50) {
                nav.classList.add('glass-nav', 'text-gray-800', 'shadow-sm');
                nav.classList.remove('bg-transparent', 'text-white');
            } else {
                nav.classList.remove('glass-nav', 'text-gray-800', 'shadow-sm');
                nav.classList.add('bg-transparent', 'text-white');
            }
            
            lastScrollY = currentScrollY;
        }

        // Throttle scroll events
        let ticking = false;
        const scrollHandler = () => {
            if (!ticking) {
                window.requestAnimationFrame(() => {
                    handleScroll();
                    ticking = false;
                });
                ticking = true;
            }
        };
        
        window.addEventListener('scroll', scrollHandler, { passive: true });
        window._agrohubScrollHandlerAttached = true;

        // Initial check
        handleScroll();
    }

    // Initialize when DOM is ready
    function initNativeAnimations() {
        // Check if animations are already initialized by checking DOM state
        // This is more reliable than window flags which may be lost on script reload
        const revealElements = document.querySelectorAll('.reveal-up');
        // Check if any reveal elements are already animated
        // Elements are considered animated if they have the 'animated' class OR
        // if their inline style opacity is set (even if it's 0, it means initialization happened)
        const alreadyAnimated = revealElements.length > 0 && Array.from(revealElements).some(el => {
            const hasAnimatedClass = el.classList.contains('animated');
            const hasInlineOpacity = el.style.opacity !== '';
            const computedOpacity = window.getComputedStyle(el).opacity;
            const isVisible = parseFloat(computedOpacity) > 0;
            return hasAnimatedClass || hasInlineOpacity || isVisible;
        });
        
        // Also check window flag as secondary check
        const pageKey = window.location.pathname.replace(/\//g, '_').replace(/^_|_$/g, '') || 'root';
        const initKey = `_agrohubAnimationsInit_${pageKey}`;
        const flagExists = window[initKey] === true;
        
        // Skip if already initialized (check DOM state OR flag - either is sufficient)
        // DOM state is more reliable as it persists across script reloads
        if (alreadyAnimated || flagExists) {
            return;
        }
        
        // Set flag immediately (atomic operation) before any other work
        window[initKey] = true;
        
        initRevealAnimations();
        initNavGlassEffect();
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNativeAnimations);
    } else {
        // DOM already loaded
        initNativeAnimations();
    }

    // Re-initialize animations for dynamically added content (e.g., AJAX-loaded cards)
    // This is useful when new .reveal-up elements are added after initial page load
    const mutationObserver = new MutationObserver((mutations) => {
        let shouldReinit = false;
        
        mutations.forEach(mutation => {
            mutation.addedNodes.forEach(node => {
                if (node.nodeType === 1) { // Element node
                    if (node.classList && node.classList.contains('reveal-up')) {
                        shouldReinit = true;
                    } else if (node.querySelector && node.querySelector('.reveal-up')) {
                        shouldReinit = true;
                    }
                }
            });
        });
        
        if (shouldReinit) {
            // Re-initialize only for new elements
            const newRevealElements = document.querySelectorAll('.reveal-up:not(.animated)');
            if (newRevealElements.length > 0) {
                initRevealAnimations();
            }
        }
    });

    // Start observing the document body for changes
    if (document.body) {
        mutationObserver.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
})();

