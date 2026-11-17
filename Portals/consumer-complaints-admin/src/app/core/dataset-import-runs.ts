import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { httpErrorMessage } from './http-error-message';
import { FAILURE, SUCCESS } from './return-codes';

export interface DatasetImportRun {
  id: string;
  run_folder_name: string;
  location_kind: string;
  location_ref: string;
  source_snapshot_start: string;
  source_snapshot_end: string;
  status: string;
  workflow_started_at: string;
  workflow_completed_at: string | null;
  ingested_at: string | null;
  part_count: number | null;
  message: string | null;
}

export interface DatasetImportRunsCtx {
  req: { eligibleOnly?: boolean };
  resp: { runs: DatasetImportRun[]; error: string };
}

export async function loadDatasetImportRuns(
  http: HttpClient,
  ctx: DatasetImportRunsCtx,
): Promise<number> {
  const params: Record<string, string> = {};
  if (ctx.req.eligibleOnly) {
    params['eligible_only'] = 'true';
  }
  const url = `${environment.apiBaseUrl}/dataset-import-runs`;
  try {
    const data = await firstValueFrom(http.get<DatasetImportRun[]>(url, { params }));
    ctx.resp.runs = Array.isArray(data) ? data : [];
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err) {
    ctx.resp.runs = [];
    ctx.resp.error = httpErrorMessage(err, 'Failed to load import runs');
    if (err instanceof HttpErrorResponse) {
      return FAILURE;
    }
    return FAILURE;
  }
}
