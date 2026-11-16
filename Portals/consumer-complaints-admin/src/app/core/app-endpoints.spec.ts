import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { AppEndpointsCtx, loadAppEndpoints } from './app-endpoints';
import { FAILURE, SUCCESS } from './return-codes';

describe('loadAppEndpoints', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => httpMock.verify());

  it('GETs /app-endpoints and stores catalog fields only', async () => {
    const ctx: AppEndpointsCtx = {
      req: {},
      resp: { entries: [], error: '' },
    };
    const pending = loadAppEndpoints(http, ctx);
    const req = httpMock.expectOne('/api/app-endpoints');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        id: 'ccbce57d-bd9f-56fe-a258-fa2deb9dd393',
        name: 'cfpb_source_http_to_local',
        category: 'source',
        from_dataset_location_id: 'loc-http',
        from_env_var_name: null,
        to_dataset_location_id: 'loc-local',
        to_env_var_name: null,
        credentials_ref: null,
        description: 'CFPB HTTP → local',
        enabled: true,
        created_at: '2026-11-15T00:00:00Z',
        updated_at: '2026-11-15T00:00:00Z',
      },
    ]);
    expect(await pending).toBe(SUCCESS);
    expect(ctx.resp.error).toBe('');
    expect(ctx.resp.entries.length).toBe(1);
    expect(ctx.resp.entries[0].name).toBe('cfpb_source_http_to_local');
    expect(ctx.resp.entries[0].category).toBe('source');
    expect(JSON.stringify(ctx.resp)).not.toMatch(/"value"\s*:/);
  });

  it('forwards category and enabled query params', async () => {
    const ctx: AppEndpointsCtx = {
      req: { category: 'source', enabled: true },
      resp: { entries: [], error: '' },
    };
    const pending = loadAppEndpoints(http, ctx);
    const req = httpMock.expectOne(
      (r) =>
        r.url.startsWith('/api/app-endpoints') &&
        r.params.get('category') === 'source' &&
        r.params.get('enabled') === 'true',
    );
    expect(req.request.method).toBe('GET');
    req.flush([]);
    expect(await pending).toBe(SUCCESS);
  });

  it('maps HTTP failure to FAILURE without inventing rows', async () => {
    const ctx: AppEndpointsCtx = {
      req: {},
      resp: { entries: [], error: '' },
    };
    const pending = loadAppEndpoints(http, ctx);
    httpMock
      .expectOne('/api/app-endpoints')
      .flush({ detail: 'boom' }, { status: 500, statusText: 'Server Error' });
    expect(await pending).toBe(FAILURE);
    expect(ctx.resp.entries).toEqual([]);
    expect(ctx.resp.error.length).toBeGreaterThan(0);
  });
});
