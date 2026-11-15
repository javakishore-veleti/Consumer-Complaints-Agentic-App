import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { upsertAirflowSecrets, UpsertSecretsCtx } from './airflow-upsert-secrets';
import { FAILURE, SUCCESS } from './return-codes';

describe('upsertAirflowSecrets', () => {
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

  it('POSTs upsert-secrets and stores name/outcome only', async () => {
    const ctx: UpsertSecretsCtx = { resp: { results: [], error: '' } };
    const pending = upsertAirflowSecrets(http, ctx);
    const req = httpMock.expectOne('/api/management/airflow/upsert-secrets');
    expect(req.request.method).toBe('POST');
    req.flush({
      results: [
        { name: 'CCA_CALLBACK_SECRET', outcome: 'updated' },
        { name: 'CCA_API_URL', outcome: 'created' },
      ],
    });
    expect(await pending).toBe(SUCCESS);
    expect(ctx.resp.error).toBe('');
    expect(ctx.resp.results).toEqual([
      { name: 'CCA_CALLBACK_SECRET', outcome: 'updated' },
      { name: 'CCA_API_URL', outcome: 'created' },
    ]);
    expect(JSON.stringify(ctx.resp)).not.toContain('value');
  });

  it('maps HTTP failure to FAILURE without inventing results', async () => {
    const ctx: UpsertSecretsCtx = { resp: { results: [], error: '' } };
    const pending = upsertAirflowSecrets(http, ctx);
    httpMock
      .expectOne('/api/management/airflow/upsert-secrets')
      .flush(
        { detail: 'airflow variables upsert failed' },
        { status: 502, statusText: 'Bad Gateway' },
      );
    expect(await pending).toBe(FAILURE);
    expect(ctx.resp.results).toEqual([]);
    expect(ctx.resp.error.length).toBeGreaterThan(0);
  });
});
