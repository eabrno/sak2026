(() => {
  const dialog = document.getElementById('lightbox');
  if (!dialog) return;
  const image = document.getElementById('lightbox-image');
  const counter = dialog.querySelector('.lightbox-counter');
  const links = [...document.querySelectorAll('[data-lightbox]')];
  let current = 0;

  function show(index) {
    if (!links.length) return;
    current = (index + links.length) % links.length;
    image.src = links[current].href;
    image.alt = links[current].querySelector('img')?.alt || '';
    counter.textContent = `${current + 1} / ${links.length}`;
    if (!dialog.open) dialog.showModal();
  }

  links.forEach((link, index) => link.addEventListener('click', event => {
    event.preventDefault();
    show(index);
  }));
  dialog.querySelector('.prev').addEventListener('click', () => show(current - 1));
  dialog.querySelector('.next').addEventListener('click', () => show(current + 1));
  dialog.querySelector('.close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target === dialog) dialog.close();
  });
  document.addEventListener('keydown', event => {
    if (!dialog.open) return;
    if (event.key === 'Escape') dialog.close();
    if (event.key === 'ArrowLeft') show(current - 1);
    if (event.key === 'ArrowRight') show(current + 1);
  });
})();
