(function () {
  const dataEl = document.getElementById('pipeline-data');
  if (!dataEl) return;

  const statusLabelsEl = document.getElementById('pipeline-status-labels');
  const pipelines = JSON.parse(dataEl.textContent || '[]');
  const statusLabels = statusLabelsEl ? JSON.parse(statusLabelsEl.textContent || '{}') : {};

  const defaultLabels = {
    done: 'Done',
    in_progress: 'In progress',
    blocked: 'Blocked',
    not_started: 'Not started',
  };

  const labelMap = { ...defaultLabels, ...statusLabels };
  const stateById = new Map(pipelines.map(item => [String(item.id), item.state || {}]));

  const wrappers = Array.from(document.querySelectorAll('.pipeline-wrap'));
  if (!wrappers.length) return;

  const renderers = [];

  wrappers.forEach((wrap) => {
    const grid = wrap.querySelector('.pipeline-grid');
    const svg = wrap.querySelector('.pipeline-lines');
    const state = stateById.get(String(wrap.dataset.pipelineId)) || {};

    if (!grid || !svg) return;

    const connectorColor = (getComputedStyle(wrap).getPropertyValue('--pipeline-connector') || '').trim() || '#d6c08c';

    const DAG = {
      version: { dependsOn: [] },
      self: { dependsOn: ['version'] },
      routing: { dependsOn: ['self'] },
      business: { dependsOn: ['routing'] },
      lang: { dependsOn: ['version'] },
      translation: { dependsOn: ['lang'] },
      approval: { dependsOn: ['business', 'translation'] },
      qbank: { dependsOn: ['translation'] },
    };

    const VALID = new Set(['done', 'in_progress', 'not_started', 'blocked']);

    function norm(s) {
      return VALID.has(s) ? s : 'not_started';
    }

    function depsDone(id) {
      const deps = DAG[id]?.dependsOn || [];
      return deps.every(d => norm(state[d]) === 'done');
    }

    function resolve(id) {
      const raw = norm(state[id]);
      if (raw === 'done' || raw === 'in_progress') return raw;
      return depsDone(id) ? 'not_started' : 'blocked';
    }

    function statusText(stepState) {
      return labelMap[stepState] || labelMap.not_started;
    }

    function renderNode(nodeEl) {
      const id = nodeEl.dataset.id;
      const nodeState = resolve(id);

      nodeEl.classList.remove('is-done', 'is-in_progress', 'is-not_started', 'is-blocked');
      nodeEl.classList.add(`is-${nodeState}`);

      const circle = nodeEl.querySelector('.pnode__circle');
      const statusEl = nodeEl.querySelector('.pnode__status');
      const step = nodeEl.dataset.step || '';

      if (statusEl) statusEl.textContent = statusText(nodeState);
      if (!circle) return;

      circle.innerHTML = '';

      if (nodeState === 'done') {
        circle.innerHTML = `
          <span class="pnode__icon pnode__icon--check" aria-hidden="true">
            <svg viewBox="0 0 16 16" focusable="false" aria-hidden="true">
              <path d="M6.5 11.3 3.2 8l1.1-1.1 2.2 2.2L11.7 4l1.1 1.1z"></path>
            </svg>
          </span>
        `;
        return;
      }

      if (nodeState === 'in_progress') {
        circle.innerHTML = `<span class="pnode__icon pnode__icon--spinner" aria-hidden="true"></span>`;
        return;
      }

      circle.innerHTML = `<span class="pnode__count">${step}</span>`;
    }

    function setSvgSize() {
      const r = wrap.getBoundingClientRect();
      svg.setAttribute('width', String(r.width));
      svg.setAttribute('height', String(r.height));
      svg.setAttribute('viewBox', `0 0 ${r.width} ${r.height}`);
    }

    function clearSvg() {
      while (svg.firstChild) svg.removeChild(svg.firstChild);
    }

    function circleCenter(id) {
      const el = grid.querySelector(`.pnode[data-id="${id}"]`);
      if (!el) return null;

      const wr = wrap.getBoundingClientRect();
      const c = el.querySelector('.pnode__circle');
      const cr = c ? c.getBoundingClientRect() : el.getBoundingClientRect();

      return {
        x: (cr.left + cr.right) / 2 - wr.left,
        y: (cr.top + cr.bottom) / 2 - wr.top
      };
    }

    function drawOrth(from, to) {
      const midX = (from.x + to.x) / 2;
      const d = `M ${from.x} ${from.y} L ${midX} ${from.y} L ${midX} ${to.y} L ${to.x} ${to.y}`;

      const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      p.setAttribute('d', d);
      p.setAttribute('fill', 'none');
      p.setAttribute('stroke', connectorColor);
      p.setAttribute('stroke-width', '4');
      p.setAttribute('stroke-linecap', 'round');
      p.setAttribute('stroke-linejoin', 'round');
      svg.appendChild(p);
    }

    function drawAllLines() {
      if (wrap.getBoundingClientRect().width < 980) return;

      setSvgSize();
      clearSvg();

      const v = circleCenter('version');
      const self = circleCenter('self');
      const routing = circleCenter('routing');
      const business = circleCenter('business');

      const lang = circleCenter('lang');
      const tr = circleCenter('translation');

      const approval = circleCenter('approval');
      const qbank = circleCenter('qbank');

      if (v && self) drawOrth(v, self);
      if (v && lang) drawOrth(v, lang);

      if (self && routing) drawOrth(self, routing);
      if (routing && business) drawOrth(routing, business);
      if (business && approval) drawOrth(business, approval);

      if (lang && tr) drawOrth(lang, tr);
      if (tr && approval) drawOrth(tr, approval);

      if (tr && qbank) drawOrth(tr, qbank);
    }

    function renderAll() {
      grid.querySelectorAll('.pnode').forEach(renderNode);
      drawAllLines();
    }

    renderers.push(renderAll);
    renderAll();
    setTimeout(renderAll, 50);
    setTimeout(renderAll, 250);
  });

  if (renderers.length) {
    window.addEventListener('resize', () => window.requestAnimationFrame(() => renderers.forEach(fn => fn())));
  }
})();
