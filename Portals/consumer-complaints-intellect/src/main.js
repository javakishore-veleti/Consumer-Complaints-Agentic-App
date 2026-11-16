const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api';

export async function runQuery(query, { fetchImpl = fetch, apiBase = API_BASE } = {}) {
  const response = await fetchImpl(`${apiBase}/intellect/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit: 5 }),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function renderHits(hits) {
  const list = document.getElementById('results');
  list.innerHTML = '';
  for (const hit of hits) {
    const li = document.createElement('li');
    li.innerHTML = `<div class="score">score ${hit.score.toFixed(3)} · ${hit.id}</div><div>${hit.text}</div>`;
    list.appendChild(li);
  }
}

function setStatus(message, show = true) {
  const el = document.getElementById('status');
  el.hidden = !show;
  el.textContent = message;
}

const form = document.getElementById('query-form');
if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = document.getElementById('query-input').value.trim();
    setStatus('Searching…');
    try {
      const data = await runQuery(query);
      renderHits(data.hits || []);
      setStatus((data.hits || []).length ? `${data.hits.length} hit(s)` : 'No hits');
    } catch (err) {
      renderHits([]);
      setStatus(err instanceof Error ? err.message : 'Query failed');
    }
  });
}
