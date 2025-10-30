// placeholder for future interactivity
console.log('AgroHub static JS loaded');

(function(){
  const page = document.querySelector('.edital-detail-page');
  const curve = document.querySelector('.edital-detail-page .side-curve');
  if(!page || !curve) return;

  let ticking = false;
  const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const speed = 0.15; // lower = subtler parallax

  function onScroll(){
    if(ticking || prefersReduced) return;
    window.requestAnimationFrame(() => {
      const y = window.scrollY || window.pageYOffset;
      curve.style.transform = `translateY(${y * speed}px)`;
      ticking = false;
    });
    ticking = true;
  }

  window.addEventListener('scroll', onScroll, { passive: true });
})();
