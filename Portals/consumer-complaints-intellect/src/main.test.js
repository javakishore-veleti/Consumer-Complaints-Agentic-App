import { describe, expect, it, vi } from 'vitest';
import { GOLDEN_QUERY_AST, runQuery, runQueryAst } from './main.js';

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
