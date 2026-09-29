// Optional enhancement for the project index: shows each project's image or typographic
// cover next to the pointer while hovering a row. The page works fully without it.
(() => {
  if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const list = document.querySelector('.project-index__list');
  if (!list) return;
  const box = document.createElement('div');
  box.className = 'index-preview';
  box.setAttribute('aria-hidden', 'true');
  document.body.append(box);
  list.querySelectorAll('.project-row').forEach(row => {
    const src = row.querySelector('.project-row__preview');
    row.addEventListener('mouseenter', () => {
      box.innerHTML = src ? src.innerHTML : '';
      if (row.dataset.color) box.style.setProperty('--project-color', row.dataset.color);
      else box.style.removeProperty('--project-color');
      box.classList.add('is-visible');
    });
    row.addEventListener('mousemove', e => {
      box.style.transform = `translate(${e.clientX + 24}px, ${e.clientY - 60}px)`;
    });
    row.addEventListener('mouseleave', () => box.classList.remove('is-visible'));
  });
})();
