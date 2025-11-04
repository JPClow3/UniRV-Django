console.log('AgroHub static JS loaded');

// Move a curva gigante conforme o scroll para criar sensação de fluir pela curva
(function(){
  const curve = document.querySelector('.green-curve');
  if(!curve) return;

  function updateCurvePosition() {
    const scrolled = window.pageYOffset || document.documentElement.scrollTop;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = scrolled / docHeight;

    // Move a curva de -100vh (topo) até 0vh (final)
    // Conforme você scrolla, você vê partes diferentes da curva
    const translateY = -100 + (scrollPercent * 100);

    curve.style.transform = `translateY(${translateY}vh)`;
  }

  // Atualiza na inicialização
  updateCurvePosition();

  // Atualiza conforme scrolla
  window.addEventListener('scroll', updateCurvePosition, { passive: true });
  window.addEventListener('resize', updateCurvePosition);
})();
