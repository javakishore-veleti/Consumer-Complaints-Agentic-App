import { describe, expect, it, vi } from 'vitest';
import { runQuery } from './main.js';

describe('runQuery', () => {
  it('posts to /intellect/query and returns hits', async () => {
    const fetchImpl = vi.fn(async () => ({
      ok: true,
      json: async () => ({ hits: [{ id: '1', text: 'billing', score: 0.9 }] }),
    }));
    const data = await runQuery('billing dispute', { fetchImpl, apiBase: '/api' });
    expect(fetchImpl).toHaveBeenCalledWith(
      '/api/intellect/query',
      expect.objectContaining({ method: 'POST' }),
    );
    expect(data.hits[0].id).toBe('1');
  });
});
