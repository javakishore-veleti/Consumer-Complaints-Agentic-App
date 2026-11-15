import { CONFLICT, FAILURE, INVALID_INPUT, NOT_FOUND, SUCCESS } from './return-codes';
import { HealthCtx, checkHealth } from './health-ctx';

describe('checkHealth', () => {
  it('returns SUCCESS and sets ok on resp', () => {
    const ctx: HealthCtx = { req: {}, resp: { ok: false, apiBaseUrl: '' } };
    expect(checkHealth(ctx)).toBe(SUCCESS);
    expect(ctx.resp.ok).toBe(true);
    expect(ctx.resp.apiBaseUrl).toBe('/api');
  });

  it('exposes the same integer codes as Python', () => {
    expect([SUCCESS, FAILURE, NOT_FOUND, INVALID_INPUT, CONFLICT]).toEqual([0, 1, 2, 3, 4]);
  });
});
