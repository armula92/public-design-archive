/* Public Design Archive by armula / 화면 구성 스크립트
   데이터는 data/archive.js (tools/build.py가 생성) 의 window.ARCHIVE 를 사용합니다. */
(function () {
  const A = window.ARCHIVE;
  const $ = (s, el = document) => el.querySelector(s);
  const esc = s => String(s || '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const thumb = id => `img/t/${id}.jpg`;
  const full = id => `img/w/${id}.jpg`;
  const num = (n, u) => `${n}<span class="unit">${u}</span>`;
  const SEP = '<span class="sep">I</span>';
  const FIRST = 30, STEP = 40;

  /* 상단 내비게이션 */
  const hasRecent = (A.recent || []).length > 0;
  const navItems = (hasRecent ? [['recent', '최근 추가']] : [])
    .concat(A.types.map(t => [t.key, t.ko]), [['projects', '사업'], ['references', '참고 자료']]);
  $('#nav').innerHTML = navItems.map(([k, n]) => `<a href="#${k}" data-k="${k}"><span class="sq"></span>${esc(n)}</a>`).join('');

  /* 한 줄 통계: 같은 크기, 같은 굵기, 흐린 I 구분 */
  const total = A.types.reduce((s, t) => s + t.photos.length, 0);
  $('#stats').innerHTML = [
    `사진 ${num(total, '장')}`,
    `유형 ${num(A.types.length, '개')}`,
    `사업 ${num(A.projects.length, '건')}`,
    `기록 ${esc(A.span)}`
  ].map(x => `<span class="stat">${x}</span>`).join(SEP);

  /* 라이트박스 */
  const lb = $('#lb'); let list = [], idx = 0;
  function show(i) {
    idx = (i + list.length) % list.length;
    const p = list[idx];
    $('#lbImg').src = full(p.id);
    $('#lbImg').alt = p.c || '';
    $('#lbCap').textContent = p.c || '';
    $('#lbKind').textContent = `${p.k}  ${idx + 1} / ${list.length}`;
  }
  function open(l, i) { list = l; lb.classList.add('open'); lb.setAttribute('aria-hidden', 'false'); document.body.style.overflow = 'hidden'; show(i); }
  function close() { lb.classList.remove('open'); lb.setAttribute('aria-hidden', 'true'); document.body.style.overflow = ''; $('#lbImg').removeAttribute('src'); }
  $('#lbPrev').onclick = e => { e.stopPropagation(); show(idx - 1); };
  $('#lbNext').onclick = e => { e.stopPropagation(); show(idx + 1); };
  $('#lbX').onclick = close;
  lb.addEventListener('click', e => { if (e.target === lb || e.target.classList.contains('stage')) close(); });
  document.addEventListener('keydown', e => {
    if (!lb.classList.contains('open')) return;
    if (e.key === 'Escape') close();
    if (e.key === 'ArrowLeft') show(idx - 1);
    if (e.key === 'ArrowRight') show(idx + 1);
  });
  let tx = null;
  lb.addEventListener('touchstart', e => { tx = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', e => {
    if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; tx = null;
    if (Math.abs(dx) > 50) show(idx + (dx < 0 ? 1 : -1));
  });

  /* 표지 사진 띠 */
  const byId = {};
  A.types.forEach(t => t.photos.forEach(p => { byId[p[0]] = { id: p[0], w: p[1], h: p[2], c: p[3], k: `${t.ko} / ${t.en}` }; }));
  const stripList = A.strip.map(id => byId[id]).filter(Boolean);
  $('#strip').innerHTML = stripList.map((p, i) => `<img src="${thumb(p.id)}" alt="${esc(p.c)}" data-i="${i}" loading="lazy">`).join('');
  $('#strip').addEventListener('click', e => { const i = e.target.dataset.i; if (i !== undefined) open(stripList, +i); });

  /* 최근 추가: tools/inbox.py 로 새로 더한 사진 */
  const galleries = [];
  const recentList = (A.recent || []).map(id => byId[id]).filter(Boolean);
  if (recentList.length) {
    $('#recentWrap').innerHTML = `
    <section class="type" id="recent">
      <div class="type-head">
        <div><h2>최근 추가<span class="en">Recently Added</span></h2></div>
        <div>
          <p class="copy">새로 기록한 장면입니다.</p>
          <p class="desc">현장에서 찍어 온 사진을 유형별로 정리해 더했습니다. 각 사진은 아래 유형에도 함께 들어 있습니다.</p>
          <p class="count">마지막 업데이트 ${esc(A.updated.replace(/-/g, '.'))}${SEP}사진 ${num(recentList.length, '장')}</p>
        </div>
      </div>
      <div class="gallery" data-k="recent"></div>
    </section>`;
    addGallery('recent', recentList, recentList.length);
  }

  /* 유형 섹션 */
  $('#typesWrap').innerHTML = A.types.map(t => `
    <section class="type" id="${t.key}">
      <div class="type-head">
        <div><h2>${esc(t.ko)}<span class="en">${esc(t.en)}</span></h2></div>
        <div>
          <p class="copy">${esc(t.copy)}</p>
          <p class="desc">${esc(t.desc)}</p>
          <p class="count">사진 ${num(t.photos.length, '장')}</p>
        </div>
      </div>
      <div class="gallery" data-k="${t.key}"></div>
      ${t.photos.length > FIRST ? `<button class="more" data-k="${t.key}">사진 더 보기</button>` : ''}
    </section>`).join('');

  A.types.forEach(t => addGallery(t.key, t.photos.map(p => byId[p[0]]), FIRST));
  function addGallery(key, items, first) {
    const el = $(`.gallery[data-k="${key}"]`);
    const g = { el, items, shown: Math.min(first, items.length) };
    galleries.push(g);
    el.addEventListener('click', e => { const f = e.target.closest('figure'); if (f) open(items, +f.dataset.i); });
    render(g);
  }
  document.querySelectorAll('.more').forEach(b => b.addEventListener('click', () => {
    const g = galleries.find(x => x.el.dataset.k === b.dataset.k);
    g.shown = Math.min(g.items.length, g.shown + STEP);
    render(g);
    if (g.shown >= g.items.length) b.remove();
    else b.textContent = `사진 더 보기 (${g.items.length - g.shown}장 남음)`;
  }));
  document.querySelectorAll('.more').forEach(b => {
    const g = galleries.find(x => x.el.dataset.k === b.dataset.k);
    b.textContent = `사진 더 보기 (${g.items.length - g.shown}장 남음)`;
  });

  function render(g) {
    const have = g.el.children.length;
    let html = '';
    for (let i = have; i < g.shown; i++) {
      const p = g.items[i];
      html += `<figure data-i="${i}"><img src="${thumb(p.id)}" alt="${esc(p.c)}" loading="lazy" decoding="async">${p.c ? `<figcaption>${esc(p.c)}</figcaption>` : ''}</figure>`;
    }
    g.el.insertAdjacentHTML('beforeend', html);
    justify(g);
  }

  /* 사진 비율을 살린 정렬형 배치 */
  function justify(g) {
    const W = g.el.clientWidth; if (!W) return;
    const H = W < 600 ? 150 : W < 1100 ? 210 : 260, GAP = 4;
    const figs = g.el.children; let row = [], sum = 0;
    const place = (r, h) => r.forEach(([f, a]) => { f.style.width = (a * h) + 'px'; f.style.height = h + 'px'; });
    for (let i = 0; i < figs.length; i++) {
      const p = g.items[i]; const a = Math.min(Math.max(p.w / p.h, .5), 2.6);
      row.push([figs[i], a]); sum += a;
      if (sum * H + GAP * (row.length - 1) >= W) {
        place(row, (W - GAP * (row.length - 1)) / sum - .01);
        row = []; sum = 0;
      }
    }
    if (row.length) place(row, H);
  }
  const ro = new ResizeObserver(es => es.forEach(e => {
    const g = galleries.find(x => x.el === e.target);
    if (g && g.w !== g.el.clientWidth) { g.w = g.el.clientWidth; justify(g); }
  }));
  galleries.forEach(g => ro.observe(g.el));

  /* 사업 */
  const pj = A.projects;
  $('#projectsWrap').innerHTML = `<section id="projects">
    <div class="projects-intro">
      <div class="type-head">
        <div><h2>사업<span class="en">Projects</span></h2></div>
        <div>
          <p class="copy">현장에서 만들어진 공공디자인 사업을 기록합니다.</p>
          <p class="desc">직접 참여하거나 우수 사례로 살펴본 사업입니다. 발주처, 장소, 연도와 함께 핵심 내용을 짧게 정리했습니다.</p>
          <p class="count">사업 ${num(pj.length, '건')}</p>
        </div>
      </div>
    </div>` + pj.map((p, n) => {
      const meta = [p.client, p.place, p.year].filter(Boolean).map(esc).join(' / ');
      const imgs = p.images;
      return `
    <article class="project" data-n="${n}">
      ${imgs.length ? `<img class="cover" src="${full(imgs[0][0])}" width="${imgs[0][1]}" height="${imgs[0][2]}" alt="${esc(p.title)}" data-i="0" loading="lazy">` : ''}
      <div class="project-body">
        <div>
          <h3>${esc(p.title)}<span class="en">${esc(p.title_en)}</span></h3>
          ${meta ? `<p class="meta">${meta}</p>` : ''}
          ${p.award ? `<p class="meta"><span class="sq"></span>${esc(p.award)}</p>` : ''}
        </div>
        <div>
          <p class="copy">${esc(p.copy)}</p>
          <p class="desc">${esc(p.desc)}</p>
        </div>
      </div>
      ${imgs.length > 1 ? `<div class="thumbs">${imgs.slice(1).map((m, i) => `<img src="${thumb(m[0])}" alt="${esc(p.title)}" data-i="${i + 1}" loading="lazy">`).join('')}</div>` : ''}
    </article>`;
    }).join('') + '</section>';
  document.querySelectorAll('.project').forEach(el => {
    const p = pj[+el.dataset.n];
    const l = p.images.map(m => ({ id: m[0], c: p.title, k: [p.place, p.year].filter(Boolean).join(' / ') || '사업' }));
    el.addEventListener('click', e => { const i = e.target.dataset.i; if (i !== undefined) open(l, +i); });
  });

  /* 참고 자료 */
  $('#refsWrap').innerHTML = `
    <section class="type" id="references">
      <div class="type-head">
        <div><h2>참고 자료<span class="en">References</span></h2></div>
        <div>
          <p class="copy">아카이브를 만들며 함께 본 자료입니다.</p>
          <p class="desc">수상집, 사례집, 사업 보고서 등 공공디자인 사례를 정리한 문헌입니다.</p>
        </div>
      </div>
      <ul class="refs">${A.refs.map(r => `<li><span class="sq"></span><span><span class="t">${esc(r.t)}</span>${r.s ? ` <span class="s">/ ${esc(r.s)}</span>` : ''}</span></li>`).join('')}</ul>
    </section>`;

  /* 현재 위치 표시 */
  const links = [...document.querySelectorAll('#nav a')];
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    links.forEach(a => a.classList.toggle('on', a.dataset.k === e.target.id));
    const on = links.find(a => a.classList.contains('on'));
    if (on) on.scrollIntoView({ block: 'nearest', inline: 'nearest' });
  }), { rootMargin: '-45% 0px -50% 0px' });
  navItems.forEach(([k]) => { const s = document.getElementById(k); if (s) io.observe(s); });
})();
