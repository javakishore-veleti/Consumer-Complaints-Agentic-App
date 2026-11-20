import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { httpErrorMessage } from './http-error-message';
import { FAILURE, SUCCESS } from './return-codes';

export type WorkflowLogCategory =
  | 'import'
  | 'db_ingest'
  | 'raw'
  | 'refined'
  | 'curated'
  | 'taxonomy'
  | 'chroma';

export const WORKFLOW_LOG_PAGE_SIZE = 60;

export const ENGINE_TYPE_OPTIONS: { value: string; label: string }[] = [
  { value: 'apache_airflow', label: 'Apache Airflow' },
  { value: 'aws_step_functions', label: 'AWS Step Functions' },
  { value: 'spring_batch', label: 'Spring Batch' },
  { value: 'bpmn', label: 'BPMN' },
  { value: 'spark_job', label: 'Spark job' },
  { value: 'aws_emr', label: 'AWS EMR' },
];

export interface WorkflowLogEntry {
  id: string;
  workflow_id: string;
  workflow_name: string;
  engine_type: string;
  engine_label: string;
  engine_workflow_id: string;
  engine_run_id: string | null;
  status: string;
  display_status: string;
  message: string | null;
  mios_ingest_log_id: string | null;
  requested_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface WorkflowLogsListReq {
  category?: WorkflowLogCategory;
  status?: string;
  engine_type?: string;
  engine_run_id?: string;
  requested_after?: string;
  requested_before?: string;
  limit?: number;
  offset?: number;
}

export interface WorkflowLogsCtx {
  req: WorkflowLogsListReq;
  resp: { entries: WorkflowLogEntry[]; error: string };
}

export async function loadWorkflowLogs(http: HttpClient, ctx: WorkflowLogsCtx): Promise<number> {
  try {
    let params = new HttpParams().set(
      'limit',
      String(Math.min(ctx.req.limit ?? WORKFLOW_LOG_PAGE_SIZE, WORKFLOW_LOG_PAGE_SIZE)),
    );
    if (ctx.req.offset != null) params = params.set('offset', String(ctx.req.offset));
    if (ctx.req.category) params = params.set('category', ctx.req.category);
    if (ctx.req.status) params = params.set('status', ctx.req.status);
    if (ctx.req.engine_type) params = params.set('engine_type', ctx.req.engine_type);
    if (ctx.req.engine_run_id) params = params.set('engine_run_id', ctx.req.engine_run_id);
    if (ctx.req.requested_after) params = params.set('requested_after', ctx.req.requested_after);
    if (ctx.req.requested_before) params = params.set('requested_before', ctx.req.requested_before);
    const url = `${environment.apiBaseUrl}/workflow-logs`;
    const entries = await firstValueFrom(http.get<WorkflowLogEntry[]>(url, { params }));
    ctx.resp.entries = entries;
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err: unknown) {
    ctx.resp.entries = [];
    ctx.resp.error = httpErrorMessage(err, 'Failed to load workflow logs');
    return FAILURE;
  }
}
