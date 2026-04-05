// スライドナビゲーション共通スクリプト
(function () {
  const slides   = document.querySelectorAll('.slide');
  const info     = document.getElementById('pinfo');
  const prev     = document.getElementById('btn-prev');
  const next     = document.getElementById('btn-next');
  const bar      = document.getElementById('progress-bar');
  const total    = slides.length;
  let cur = 0;

  // フッターのページ番号を自動生成
  const title = document.querySelector('.slide-header .slide-title')?.textContent ?? '';
  slides.forEach((s, i) => {
    const footer = s.querySelector('.slide-footer');
    if (footer) {
      footer.innerHTML =
        `<span>高校数学 重要問題解説</span><span>${i + 1} / ${total}</span>`;
    }
  });

  function go(d) {
    const next_idx = cur + d;
    if (next_idx < 0 || next_idx >= total) return;

    // フェードアウト → 切り替え → フェードイン
    slides[cur].style.opacity = '0';
    setTimeout(() => {
      slides[cur].classList.remove('active');
      cur = next_idx;
      slides[cur].classList.add('active');
      // 次フレームでフェードイン
      requestAnimationFrame(() => {
        requestAnimationFrame(() => { slides[cur].style.opacity = '1'; });
      });
      update();
    }, 150);
  }

  function update() {
    info.textContent = `${cur + 1} / ${total}`;
    prev.disabled = cur === 0;
    next.disabled = cur === total - 1;
    bar.style.width = `${((cur + 1) / total) * 100}%`;
  }

  prev.addEventListener('click', () => go(-1));
  next.addEventListener('click', () => go(1));
  document.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') go(1);
    if (e.key === 'ArrowLeft'  || e.key === 'ArrowUp')   go(-1);
  });

  update(); // 初期状態を設定

  // ── ビューポートに合わせてスライドをスケーリング ──
  function scaleToFit() {
    const vw = document.documentElement.clientWidth;
    const vh = document.documentElement.clientHeight;
    const scale = Math.min(vw / 1280, vh / 720, 1);
    const val = scale < 0.999 ? scale.toFixed(4) : '';
    slides.forEach(function (s) { s.style.zoom = val; });
  }
  window.addEventListener('resize', scaleToFit);
  scaleToFit();

  // ── 印刷前にズームを1にリセット、印刷後に復元 ──
  window.addEventListener('beforeprint', function () {
    slides.forEach(function (s) { s.style.zoom = '1'; });
  });
  window.addEventListener('afterprint', scaleToFit);
})();
