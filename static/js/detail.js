// Detail page functionality
// Uses native Intersection Observer animations (loaded via animations-native.js)
// No GSAP dependency for simple fade-in animations
(function() {
    'use strict';

    // Print button functionality
    const printBtn = document.getElementById('print-btn');
    if (printBtn) {
        printBtn.addEventListener('click', function() {
            window.print();
        });
    }

    // Animations are handled by animations-native.js which uses Intersection Observer
    // This provides the same visual effect as GSAP but with zero external dependencies
})();
