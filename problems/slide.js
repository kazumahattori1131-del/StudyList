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
})();
