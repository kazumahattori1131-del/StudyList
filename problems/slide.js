// スライドナビゲーション共通スクリプト
(function () {
  const slides = document.querySelectorAll('.slide');
  const info   = document.getElementById('pinfo');
  let cur = 0;

  function go(d) {
    slides[cur].classList.remove('active');
    cur = Math.max(0, Math.min(slides.length - 1, cur + d));
    slides[cur].classList.add('active');
    info.textContent = `${cur + 1} / ${slides.length}`;
  }

  document.getElementById('btn-prev').addEventListener('click', () => go(-1));
  document.getElementById('btn-next').addEventListener('click', () => go(1));
  document.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') go(1);
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   go(-1);
  });
})();
