document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('.puntuacion-contenedor').forEach(container => {
    const slider = container.querySelector('.sliderPuntuacion');
    const display = container.querySelector('.valor-puntuacion');

    if (!slider || !display) return;

    const fmt = v => (parseFloat(v) || 0).toFixed(1);

    const min = parseFloat(slider.min) || 1.0;
    const max = parseFloat(slider.max) || 9.9;
    let lastValue = slider.value = fmt(slider.value || min);
    display.textContent = lastValue;
    updateSliderBg(slider, min, max, lastValue);

    slider.addEventListener('input', (e) => {
      const v = fmt(e.target.value);
      display.textContent = v;
      updateSliderBg(slider, min, max, v);
    });

    
    slider.addEventListener('change', async (e) => {
      const newVal = fmt(e.target.value);
      const tipo = slider.dataset.tipo;      
      const itemId = slider.dataset.itemId;

      if (!tipo || !itemId) {
        console.warn('Faltan datos para actualizar puntuación (data-tipo o data-item-id).');
        lastValue = newVal;
        return;
      }

      const payload = { score: newVal };

      slider.classList.remove('error');

      try {
        const resp = await fetch(`/${tipo}/actualizar_puntuacion/${itemId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });

        if (!resp.ok) {
          throw new Error('Respuesta no OK');
        }

        const data = await resp.json();
        if (!data.success) throw new Error(data.error || 'Error en servidor');

        // success: fija lastValue
        lastValue = newVal;
        // opcional: mostrar breve confirmación visual (pequeño glow)
        slider.style.boxShadow = '0 0 12px rgba(124,100,255,0.18)';
        setTimeout(() => slider.style.boxShadow = '', 350);

      } catch (err) {
        console.error('No se pudo actualizar puntuación:', err);
        // marca error visualmente y revierte valor en UI
        slider.classList.add('error');
        slider.value = lastValue;
        display.textContent = lastValue;
        updateSliderBg(slider, min, max, lastValue);
        alert('No se pudo guardar la puntuación. Intenta de nuevo.');
      }
    });
  });

  function updateSliderBg(slider, min, max, value) {
    const v = parseFloat(value);
    const pct = Math.max(0, Math.min(100, ((v - min) / (max - min)) * 100));
  
    let color;
    if (v < 4) color = '#e74c3c';
    else if (v < 6) color = '#f39c12';
    else if (v < 7.5) color = '#f1c40f';
    else if (v < 9) color = '#2ecc71';  
    else color = '#6c63ff';             
  
    slider.style.background = `linear-gradient(90deg, ${color} ${pct}%, #d3d3d3 ${pct}%)`;
  
    slider.offsetHeight;
  }  
});



  