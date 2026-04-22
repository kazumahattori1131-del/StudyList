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

  // ── 印刷前: zoom+幅補正で全スライドを339mm幅・文字切れなしに ──
  // zoom=0.9にすることで最大800pxのコンテンツを191mm以内に収める
  // widthを1280/0.9≈1423pxにすることでzoom後の幅が339mmになる
  var PRINT_ZOOM = 0.9;
  window.addEventListener('beforeprint', function () {
    slides.forEach(function (s) {
      s.style.zoom = PRINT_ZOOM.toFixed(2);
      s.style.width = Math.round(1280 / PRINT_ZOOM) + 'px';
    });
  });
  window.addEventListener('afterprint', function () {
    slides.forEach(function (s) {
      s.style.zoom = '';
      s.style.width = '';
    });
    scaleToFit();
  });
})();

// ── Canva用画像エクスポート（16:9 PNG × 2560×1440 / ZIP一括保存） ──
(function () {
  const nav = document.getElementById('nav');
  if (!nav) return;

  const btnImg = document.createElement('button');
  btnImg.id = 'btn-img';
  btnImg.textContent = '🖼 画像保存';
  const hint = nav.querySelector('.hint');
  hint ? nav.insertBefore(btnImg, hint) : nav.appendChild(btnImg);

  function loadScript(src) {
    return new Promise(function (res, rej) {
      if (document.querySelector('script[src="' + src + '"]')) { res(); return; }
      var s = document.createElement('script');
      s.src = src; s.onload = res; s.onerror = rej;
      document.head.appendChild(s);
    });
  }

  btnImg.addEventListener('click', async function () {
    btnImg.disabled = true;
    var allSlides = Array.from(document.querySelectorAll('.slide'));
    try {
      if (!window.html2canvas)
        await loadScript('https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js');
      if (!window.JSZip)
        await loadScript('https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js');

      var zip = new JSZip();
      for (var i = 0; i < allSlides.length; i++) {
        btnImg.textContent = '⏳ ' + (i + 1) + ' / ' + allSlides.length;
        var slide = allSlides[i];
        var saved = {
          display: slide.style.display, opacity: slide.style.opacity,
          zoom: slide.style.zoom, width: slide.style.width,
          height: slide.style.height, minHeight: slide.style.minHeight,
        };
        slide.style.display = 'flex'; slide.style.opacity = '1';
        slide.style.zoom = '1'; slide.style.width = '1280px';
        slide.style.height = '720px'; slide.style.minHeight = '720px';

        await new Promise(function (r) { setTimeout(r, 80); });
        await new Promise(function (r) { requestAnimationFrame(function () { requestAnimationFrame(r); }); });

        var canvas = await html2canvas(slide, {
          scale: 2,
          width: 1280, height: 720,
          backgroundColor: '#ffffff',
          useCORS: true,
          allowTaint: false,
          logging: false,
          ignoreElements: function (el) { return el.id === 'nav' || el.id === 'progress-bar'; },
          onclone: function (_, el) { el.style.boxShadow = 'none'; },
        });
        Object.assign(slide.style, saved);

        var blob = await new Promise(function (r) { canvas.toBlob(r, 'image/png'); });
        zip.file('slide_' + String(i + 1).padStart(2, '0') + '.png', blob);
      }
      var zipBlob = await zip.generateAsync({ type: 'blob' });
      var fname = (document.title || 'slides') + '_canva.zip';
      var a = Object.assign(document.createElement('a'),
                            { href: URL.createObjectURL(zipBlob), download: fname });
      document.body.appendChild(a); a.click();
      document.body.removeChild(a); URL.revokeObjectURL(a.href);
    } catch (err) {
      console.error('Image export error:', err);
      alert('画像の生成に失敗しました。ブラウザのコンソールでエラーを確認してください。');
    } finally {
      btnImg.disabled = false;
      btnImg.textContent = '🖼 画像保存';
    }
  });
})();
