import { TestBed } from '@angular/core/testing';
import { HttpClient, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { FAILURE, INVALID_INPUT, SUCCESS } from './return-codes';
import { startWorkflow, StartWorkflowCtx } from './start-workflow';

describe('startWorkflow', () => {
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

  it('maps 202 to SUCCESS and executionId with mio_id body', async () => {
    const ctx: StartWorkflowCtx = {
      req: { workflowId: 'w1', mioId: 'm1' },
      resp: { executionId: '', error: '' },
    };
    const pending = startWorkflow(http, ctx);
    const req = httpMock.expectOne('/api/workflows/w1/start');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ mio_id: 'm1' });
    req.flush({ execution_id: 'e1' }, { status: 202, statusText: 'Accepted' });
    await expect(pending).resolves.toBe(SUCCESS);
    expect(ctx.resp.executionId).toBe('e1');
    expect(ctx.resp.error).toBe('');
  });

  it('maps 422 to INVALID_INPUT with API detail', async () => {
    const ctx: StartWorkflowCtx = {
      req: { workflowId: 'w1', mioId: 'm1' },
      resp: { executionId: '', error: '' },
    };
    const pending = startWorkflow(http, ctx);
    httpMock.expectOne('/api/workflows/w1/start').flush(
      { detail: 'invalid request' },
      { status: 422, statusText: 'Unprocessable Entity' },
    );
    await expect(pending).resolves.toBe(INVALID_INPUT);
    expect(ctx.resp.executionId).toBe('');
    expect(ctx.resp.error).toBe('invalid request');
  });

  it('maps 502 to FAILURE with engine detail', async () => {
    const ctx: StartWorkflowCtx = {
      req: { workflowId: 'w1', mioId: 'm1' },
      resp: { executionId: '', error: '' },
    };
    const pending = startWorkflow(http, ctx);
    httpMock.expectOne('/api/workflows/w1/start').flush(
      { detail: 'engine start failed' },
      { status: 502, statusText: 'Bad Gateway' },
    );
    await expect(pending).resolves.toBe(FAILURE);
    expect(ctx.resp.error).toBe('engine start failed');
  });

  it('maps other HTTP errors to FAILURE with fallback when no detail', async () => {
    const ctx: StartWorkflowCtx = {
      req: { workflowId: 'w1', mioId: 'm1' },
      resp: { executionId: '', error: '' },
    };
    const pending = startWorkflow(http, ctx);
    httpMock.expectOne('/api/workflows/w1/start').flush('boom', {
      status: 500,
      statusText: 'Server Error',
    });
    await expect(pending).resolves.toBe(FAILURE);
    expect(ctx.resp.error).toBe('Failed to start workflow');
  });
});
