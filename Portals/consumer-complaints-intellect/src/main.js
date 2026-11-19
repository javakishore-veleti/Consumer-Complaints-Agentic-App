const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

/** Golden Money Topics AST (M50 / M52) — Capital One + Credit Cards on curated 3m. */
export const GOLDEN_QUERY_AST = {
  table: 'demo.curated.cfpb_complaints_3m',
  filter_tree: {
    op: 'AND',
    args: [
      {
        op: 'EQ',
        field: 'parent_org_id',
        value: '6d55f403495e51ed7212000a597144abed8a3c310895cb601bea4403339300c6',
      },
      {
        op: 'EQ',
        field: 'primary_money_topic',
        value: 'Credit Cards',
      },
    ],
  },
};

export async function runQuery(query, { fetchImpl = fetch, apiBase = API_BASE, config = 'baseline' } = {}) {
  const response = await fetchImpl(`${apiBase}/intellect/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit: 5, config }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export async function runQueryAst(ast, { fetchImpl = fetch, apiBase = API_BASE, execute = false } = {}) {
  const response = await fetchImpl(`${apiBase}/intellect/query-ast`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ast, execute }),
  });
  if (!response.ok) {
    let detail = await response.text();
    try {
      const parsed = JSON.parse(detail);
      detail = parsed.detail || detail;
    } catch {
      /* keep text */
    }
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function renderHits(hits) {
  const list = document.getElementById('results');
  if (!list) return;
  list.innerHTML = '';
  for (const hit of hits) {
    const li = document.createElement('li');
    li.innerHTML = `<div class="score">score ${hit.score.toFixed(3)} · ${hit.id}</div><div>${hit.text}</div>`;
    list.appendChild(li);
  }
}

function setStatus(message, show = true) {
  const el = document.getElementById('status');
  if (!el) return;
  el.hidden = !show;
  el.textContent = message;
}

function setAstStatus(message, show = true) {
  const el = document.getElementById('ast-status');
  if (!el) return;
  el.hidden = !show;
  el.textContent = message;
}

function renderAstResult(data) {
  const sqlEl = document.getElementById('ast-sql');
  const metaEl = document.getElementById('ast-meta');
  if (sqlEl) {
    sqlEl.hidden = !data?.sql;
    sqlEl.textContent = data?.sql || '';
  }
  if (metaEl) {
    if (!data) {
      metaEl.hidden = true;
      metaEl.textContent = '';
      return;
    }
    const parts = [];
    if (data.executed) parts.push(`count ${data.count}`);
    if (data.k_anon_ok != null) parts.push(`k-anon ${data.k_anon_ok ? 'ok' : 'fail'}`);
    if (!data.executed) parts.push('translate only (not executed)');
    metaEl.hidden = parts.length === 0;
    metaEl.textContent = parts.join(' · ');
  }
}

const form = document.getElementById('query-form');
if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = document.getElementById('query-input').value.trim();
    const config = document.getElementById('config-input')?.value || 'baseline';
    setStatus('Searching…');
    try {
      const data = await runQuery(query, { config });
      renderHits(data.hits || []);
      const cfg = data.config || config;
      setStatus((data.hits || []).length ? `${data.hits.length} hit(s) · ${cfg}` : `No hits · ${cfg}`);
    } catch (err) {
      renderHits([]);
      setStatus(err instanceof Error ? err.message : 'Query failed');
    }
  });
}

const astInput = document.getElementById('ast-input');
if (astInput && !astInput.value.trim()) {
  astInput.value = JSON.stringify(GOLDEN_QUERY_AST, null, 2);
}

const astForm = document.getElementById('ast-form');
if (astForm) {
  astForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const raw = document.getElementById('ast-input')?.value?.trim() || '';
    const execute = Boolean(document.getElementById('ast-execute')?.checked);
    setAstStatus('Running Query AST…');
    renderAstResult(null);
    let ast;
    try {
      ast = JSON.parse(raw);
    } catch (err) {
      setAstStatus(err instanceof Error ? `Invalid JSON: ${err.message}` : 'Invalid JSON');
      return;
    }
    try {
      const data = await runQueryAst(ast, { execute });
      renderAstResult(data);
      setAstStatus(data.executed ? `Executed · n=${data.count}` : 'Translated');
    } catch (err) {
      renderAstResult(null);
      setAstStatus(err instanceof Error ? err.message : 'Query AST failed');
    }
  });
}
