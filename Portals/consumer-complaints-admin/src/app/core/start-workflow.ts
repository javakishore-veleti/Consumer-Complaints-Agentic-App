import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { httpErrorMessage } from './http-error-message';
import { FAILURE, INVALID_INPUT, SUCCESS } from './return-codes';

export interface StartWorkflowReq {
  workflowId: string;
  mioId?: string;
  importIds?: string[];
  mode?: 'sequential' | 'parallel';
  sourceSnapshotStart?: string;
  sourceSnapshotEnd?: string;
}
export interface StartWorkflowResp {
  executionId: string;
  error: string;
}
export interface StartWorkflowCtx {
  req: StartWorkflowReq;
  resp: StartWorkflowResp;
}

interface StartWorkflowApiBody {
  execution_id: string;
}

export async function startWorkflow(http: HttpClient, ctx: StartWorkflowCtx): Promise<number> {
  const url = `${environment.apiBaseUrl}/workflows/${encodeURIComponent(ctx.req.workflowId)}/start`;
  const body: Record<string, unknown> = {};
  if (ctx.req.mioId !== undefined && ctx.req.mioId !== null && ctx.req.mioId !== '') {
    body['mio_id'] = ctx.req.mioId;
  }
  if (ctx.req.importIds && ctx.req.importIds.length) {
    body['import_ids'] = ctx.req.importIds;
  }
  if (ctx.req.mode) {
    body['mode'] = ctx.req.mode;
  }
  if (ctx.req.sourceSnapshotStart) {
    body['source_snapshot_start'] = ctx.req.sourceSnapshotStart;
  }
  if (ctx.req.sourceSnapshotEnd) {
    body['source_snapshot_end'] = ctx.req.sourceSnapshotEnd;
  }
  try {
    const data = await firstValueFrom(
      http.post<StartWorkflowApiBody>(url, body, {
        headers: { 'X-CCA-Audience': 'internal' },
      }),
    );
    ctx.resp.executionId = data?.execution_id ?? '';
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err) {
    ctx.resp.executionId = '';
    if (err instanceof HttpErrorResponse && err.status === 422) {
      ctx.resp.error = httpErrorMessage(err, 'Invalid start request');
      return INVALID_INPUT;
    }
    ctx.resp.error = httpErrorMessage(err, 'Failed to start workflow');
    return FAILURE;
  }
}
