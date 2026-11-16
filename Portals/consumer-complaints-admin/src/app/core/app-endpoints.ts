import { HttpClient, HttpParams } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { httpErrorMessage } from './http-error-message';
import { FAILURE, SUCCESS } from './return-codes';

/** Catalog fields from GET /app-endpoints — never includes secret values. */
export interface AppEndpointEntry {
  id: string;
  name: string;
  category: string;
  from_dataset_location_id: string | null;
  from_env_var_name: string | null;
  to_dataset_location_id: string | null;
  to_env_var_name: string | null;
  credentials_ref: string | null;
  description: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface AppEndpointsReq {
  category?: string;
  enabled?: boolean;
}

export interface AppEndpointsResp {
  entries: AppEndpointEntry[];
  error: string;
}

export interface AppEndpointsCtx {
  req: AppEndpointsReq;
  resp: AppEndpointsResp;
}

/** GET /app-endpoints — catalog only; never expect or store secret values. */
export async function loadAppEndpoints(
  http: HttpClient,
  ctx: AppEndpointsCtx,
): Promise<number> {
  const url = `${environment.apiBaseUrl}/app-endpoints`;
  let params = new HttpParams();
  if (ctx.req.category !== undefined && ctx.req.category !== '') {
    params = params.set('category', ctx.req.category);
  }
  if (ctx.req.enabled !== undefined) {
    params = params.set('enabled', String(ctx.req.enabled));
  }
  try {
    const entries = await firstValueFrom(
      http.get<AppEndpointEntry[]>(url, { params }),
    );
    ctx.resp.entries = entries ?? [];
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err: unknown) {
    ctx.resp.entries = [];
    ctx.resp.error = httpErrorMessage(err, 'Failed to load AppEndpoints');
    return FAILURE;
  }
}

/** Display from/to side: location id XOR env-var name (never a secret value). */
export function endpointSideLabel(
  locationId: string | null | undefined,
  envVarName: string | null | undefined,
): string {
  if (locationId) {
    return `loc:${locationId}`;
  }
  if (envVarName) {
    return `env:${envVarName}`;
  }
  return '—';
}
