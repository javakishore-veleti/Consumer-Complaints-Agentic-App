import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { httpErrorMessage } from './http-error-message';
import { FAILURE, SUCCESS } from './return-codes';

export interface MioStatusExecution {
  id: string;
  workflow_id: string;
  workflow_name: string;
  engine_type: string;
  engine_workflow_id: string;
  engine_run_id: string | null;
  status: string;
  message: string | null;
  mios_ingest_log_id: string | null;
  requested_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface MioStatusIngest {
  id: string;
  mio_id: string;
  status: string;
  message: string | null;
  rows_loaded: number | null;
  batch_count: number | null;
  increment_marker: string | null;
  requested_at: string;
  started_at: string | null;
  finished_at: string | null;
  executions: MioStatusExecution[];
}

/** Enabled workflows allowed for this MIO (D84). Same shape as GET /workflows rows. */
export interface MioAllowedWorkflow {
  id: string;
  workflow_name: string;
  engine_type: string;
  engine_workflow_id: string;
  enabled: boolean;
}

export interface MioStatusEntry {
  id: string;
  name: string;
  description: string | null;
  latest_ingest: MioStatusIngest | null;
  allowed_workflows?: MioAllowedWorkflow[];
}

export interface MioStatusReq {}
export interface MioStatusResp {
  entries: MioStatusEntry[];
  error: string;
}
export interface MioStatusCtx {
  req: MioStatusReq;
  resp: MioStatusResp;
}

export async function loadMioStatus(http: HttpClient, ctx: MioStatusCtx): Promise<number> {
  const url = `${environment.apiBaseUrl}/mios/status`;
  try {
    const entries = await firstValueFrom(http.get<MioStatusEntry[]>(url));
    ctx.resp.entries = (entries ?? []).map((e) => ({
      ...e,
      allowed_workflows: e.allowed_workflows ?? [],
    }));
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err) {
    ctx.resp.entries = [];
    ctx.resp.error = httpErrorMessage(err, 'Failed to load MIO status');
    return FAILURE;
  }
}
