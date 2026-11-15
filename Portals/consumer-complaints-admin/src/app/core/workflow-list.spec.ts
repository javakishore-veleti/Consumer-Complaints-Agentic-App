import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { FAILURE, SUCCESS } from './return-codes';
import { listWorkflows, WorkflowListCtx } from './workflow-list';

describe('listWorkflows', () => {
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

  it('maps 200 list to SUCCESS and workflows', async () => {
    const ctx: WorkflowListCtx = { req: {}, resp: { workflows: [], error: '' } };
    const pending = listWorkflows(http, ctx);
    const req = httpMock.expectOne('/api/workflows');
    expect(req.request.method).toBe('GET');
    req.flush([
      {
        id: 'w1',
        workflow_name: 'download_cfpb_all',
        engine_type: 'apache_airflow',
        engine_workflow_id: 'download_cfpb_all',
        enabled: true,
      },
    ]);
    await expect(pending).resolves.toBe(SUCCESS);
    expect(ctx.resp.workflows.length).toBe(1);
    expect(ctx.resp.workflows[0].workflow_name).toBe('download_cfpb_all');
    expect(ctx.resp.error).toBe('');
  });

  it('maps HTTP error to FAILURE without inventing workflows', async () => {
    const ctx: WorkflowListCtx = { req: {}, resp: { workflows: [], error: '' } };
    const pending = listWorkflows(http, ctx);
    httpMock.expectOne('/api/workflows').flush('boom', {
      status: 500,
      statusText: 'Server Error',
    });
    await expect(pending).resolves.toBe(FAILURE);
    expect(ctx.resp.workflows).toEqual([]);
    expect(ctx.resp.error.length).toBeGreaterThan(0);
  });
});
