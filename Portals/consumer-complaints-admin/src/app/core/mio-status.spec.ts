import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { FAILURE, SUCCESS } from './return-codes';
import { loadMioStatus, MioStatusCtx } from './mio-status';

describe('loadMioStatus', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('maps 200 list to SUCCESS and entries', async () => {
    const ctx: MioStatusCtx = { req: {}, resp: { entries: [], error: '' } };
    const pending = loadMioStatus(http, ctx);
    const req = httpMock.expectOne('/api/mios/status');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: 'seed',
        latest_ingest: {
          id: 'i1',
          mio_id: 'm1',
          status: 'failed',
          message: 'disk full',
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-14T00:00:00Z',
          started_at: null,
          finished_at: null,
          executions: [],
        },
      },
    ]);
    await expect(pending).resolves.toBe(SUCCESS);
    expect(ctx.resp.entries.length).toBe(1);
    expect(ctx.resp.entries[0].latest_ingest?.status).toBe('failed');
    expect(ctx.resp.entries[0].latest_ingest?.message).toBe('disk full');
    expect(ctx.resp.error).toBe('');
  });

  it('maps HTTP error to FAILURE without inventing entries', async () => {
    const ctx: MioStatusCtx = { req: {}, resp: { entries: [], error: '' } };
    const pending = loadMioStatus(http, ctx);
    httpMock.expectOne('/api/mios/status').flush('boom', {
      status: 500,
      statusText: 'Server Error',
    });
    await expect(pending).resolves.toBe(FAILURE);
    expect(ctx.resp.entries).toEqual([]);
    expect(ctx.resp.error.length).toBeGreaterThan(0);
  });
});
