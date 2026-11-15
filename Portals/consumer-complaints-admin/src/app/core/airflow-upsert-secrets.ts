import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { httpErrorMessage } from './http-error-message';
import { FAILURE, SUCCESS } from './return-codes';

export interface UpsertSecretResult {
  name: string;
  outcome: string;
}

export interface UpsertSecretsResp {
  results: UpsertSecretResult[];
  error: string;
}

export interface UpsertSecretsCtx {
  resp: UpsertSecretsResp;
}

/** POST /management/airflow/upsert-secrets — never expect or store secret values. */
export async function upsertAirflowSecrets(
  http: HttpClient,
  ctx: UpsertSecretsCtx,
): Promise<number> {
  const url = `${environment.apiBaseUrl}/management/airflow/upsert-secrets`;
  try {
    const body = await firstValueFrom(http.post<{ results: UpsertSecretResult[] }>(url, {}));
    ctx.resp.results = body.results ?? [];
    ctx.resp.error = '';
    return SUCCESS;
  } catch (err: unknown) {
    ctx.resp.results = [];
    ctx.resp.error = httpErrorMessage(err, 'Sync secrets failed');
    return FAILURE;
  }
}
