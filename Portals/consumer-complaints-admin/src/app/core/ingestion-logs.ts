import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { httpErrorMessage } from './http-error-message';
import { FAILURE, SUCCESS } from './return-codes';

export type IngestionLogZone = 'raw' | 'refined' | 'curated' | 'taxonomy' | 'chroma';

export const INGESTION_LOG_ZONES: { zone: IngestionLogZone; label: string }[] = [
  { zone: 'raw', label: 'Raw' },
  { zone: 'refined', label: 'Refined' },
  { zone: 'curated', label: 'Curated' },
  { zone: 'taxonomy', label: 'Taxonomy' },
  { zone: 'chroma', label: 'Chroma' },
];

export const INGESTION_LOG_PAGE_SIZE = 30;

export interface IngestionLogEntry {
  id: string;
  zone: string;
  partition_key: string;
  data_tech: string;
  source_end_point_id: string;
  dest_end_point_id: string;
  workflow_execution_id: string | null;
  status: string;
  status_on: string;
  status_updated_on: string;
  configs_json: string | null;
}

export interface IngestionLogListReq {
  zone: IngestionLogZone;
  limit?: number;
  offset?: number;
  status?: string;
  partition_key?: string;
  workflow_execution_id?: string;
  status_updated_from?: string;
  status_updated_to?: string;
}

export interface IngestionLogsCtx {
  req: IngestionLogListReq;
  resp: { entries: IngestionLogEntry[]; error: string };
}

export async function loadIngestionLogs(http: HttpClient, ctx: IngestionLogsCtx): Promise<number> {
  try {
    let params = new HttpParams().set('limit', String(Math.min(ctx.req.limit ?? INGESTION_LOG_PAGE_SIZE, INGESTION_LOG_PAGE_SIZE)));
    if (ctx.req.offset != null) params = params.set('offset', String(ctx.req.offset));
    if (ctx.req.status) params = params.set('status', ctx.req.status);
    if (ctx.req.partition_key) params = params.set('partition_key', ctx.req.partition_key);
    if (ctx.req.workflow_execution_id) {
      params = params.set('workflow_execution_id', ctx.req.workflow_execution_id);
    }
    if (ctx.req.status_updated_from) params = params.set('status_updated_from', ctx.req.status_updated_from);
    if (ctx.req.status_updated_to) params = params.set('status_updated_to', ctx.req.status_updated_to);
    const url = `${environment.apiBaseUrl}/ingestion-logs/${ctx.req.zone}`;
    const entries = await firstValueFrom(http.get<IngestionLogEntry[]>(url, { params }));
    ctx.resp.entries = entries;
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err: unknown) {
    ctx.resp.entries = [];
    ctx.resp.error = httpErrorMessage(err, 'Failed to load ingestion logs');
    return FAILURE;
  }
}
