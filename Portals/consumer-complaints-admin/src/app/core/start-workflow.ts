import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { FAILURE, INVALID_INPUT, SUCCESS } from './return-codes';

export interface StartWorkflowReq {
  workflowId: string;
  mioId?: string;
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
  const body =
    ctx.req.mioId !== undefined && ctx.req.mioId !== null && ctx.req.mioId !== ''
      ? { mio_id: ctx.req.mioId }
      : {};
  try {
    const data = await firstValueFrom(http.post<StartWorkflowApiBody>(url, body));
    ctx.resp.executionId = data?.execution_id ?? '';
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err) {
    ctx.resp.executionId = '';
    if (err instanceof HttpErrorResponse && err.status === 422) {
      ctx.resp.error = 'Invalid start request';
      return INVALID_INPUT;
    }
    ctx.resp.error = 'Failed to start workflow';
    return FAILURE;
  }
}
