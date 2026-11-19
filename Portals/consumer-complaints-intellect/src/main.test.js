import { describe, expect, it, vi } from 'vitest';
import {
  GOLDEN_QUERY_AST,
  applyAlertDrilldown,
  fetchRiskRadar,
  runQuery,
  runQueryAst,
} from './main.js';

describe('runQuery', () => {
  it('posts to /intellect/query and returns hits', async () => {
    const fetchImpl = vi.fn(async () => ({
      ok: true,
      json: async () => ({ hits: [{ id: '1', text: 'billing', score: 0.9 }] }),
    }));
    const data = await runQuery('billing dispute', { fetchImpl, apiBase: '/api', config: 'hybrid' });
    expect(fetchImpl).toHaveBeenCalledWith(
      '/api/intellect/query',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ query: 'billing dispute', limit: 5, config: 'hybrid' }),
      }),
    );
    expect(data.hits[0].id).toBe('1');
  });
});

describe('runQueryAst', () => {
  it('posts AST to /intellect/query-ast', async () => {
    const fetchImpl = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        sql: 'SELECT COUNT(*) AS n FROM demo.curated.cfpb_complaints_3m WHERE (1=1)',
        executed: false,
        count: null,
        k_anon_ok: null,
      }),
    }));
    const data = await runQueryAst(GOLDEN_QUERY_AST, { fetchImpl, apiBase: '/api', execute: false });
    expect(fetchImpl).toHaveBeenCalledWith(
      '/api/intellect/query-ast',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ ast: GOLDEN_QUERY_AST, execute: false }),
      }),
    );
    expect(data.sql).toContain('SELECT COUNT(*)');
    expect(data.executed).toBe(false);
  });

  it('surfaces HTTP error detail', async () => {
    const fetchImpl = vi.fn(async () => ({
      ok: false,
      status: 503,
      text: async () => JSON.stringify({ detail: 'warehouse unavailable' }),
    }));
    await expect(runQueryAst(GOLDEN_QUERY_AST, { fetchImpl, execute: true })).rejects.toThrow(
      'warehouse unavailable',
    );
  });
});

describe('fetchRiskRadar', () => {
  it('GETs /intellect/risk-radar fixture alerts', async () => {
    const fetchImpl = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        source: 'fixture',
        alerts: [{ id: 'rr1', title: 'spike', drilldown_ast: GOLDEN_QUERY_AST }],
      }),
    }));
    const data = await fetchRiskRadar({ fetchImpl, apiBase: '/api', source: 'fixture' });
    expect(fetchImpl).toHaveBeenCalledWith(
      '/api/intellect/risk-radar?source=fixture',
      expect.objectContaining({ method: 'GET' }),
    );
    expect(data.alerts[0].id).toBe('rr1');
  });
});

describe('applyAlertDrilldown', () => {
  it('writes drilldown_ast into the AST textarea', () => {
    const astInput = { value: '', focus: vi.fn() };
    const panel = { scrollIntoView: vi.fn() };
    const alert = { id: 'rr1', drilldown_ast: GOLDEN_QUERY_AST };
    const ast = applyAlertDrilldown(alert, { astInput, panel });
    expect(ast).toEqual(GOLDEN_QUERY_AST);
    expect(JSON.parse(astInput.value)).toEqual(GOLDEN_QUERY_AST);
    expect(astInput.focus).toHaveBeenCalled();
    expect(panel.scrollIntoView).toHaveBeenCalled();
  });
});
