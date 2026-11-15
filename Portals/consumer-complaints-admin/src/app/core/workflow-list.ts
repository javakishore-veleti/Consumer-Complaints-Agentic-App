import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { httpErrorMessage } from './http-error-message';
import { FAILURE, SUCCESS } from './return-codes';

export interface WorkflowListEntry {
  id: string;
  workflow_name: string;
  engine_type: string;
  engine_workflow_id: string;
  enabled: boolean;
}

export interface WorkflowListReq {}
export interface WorkflowListResp {
  workflows: WorkflowListEntry[];
  error: string;
}
export interface WorkflowListCtx {
  req: WorkflowListReq;
  resp: WorkflowListResp;
}

export async function listWorkflows(http: HttpClient, ctx: WorkflowListCtx): Promise<number> {
  const url = `${environment.apiBaseUrl}/workflows`;
  try {
    const workflows = await firstValueFrom(http.get<WorkflowListEntry[]>(url));
    ctx.resp.workflows = workflows ?? [];
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err) {
    ctx.resp.workflows = [];
    ctx.resp.error = httpErrorMessage(err, 'Failed to load workflows');
    return FAILURE;
  }
}
