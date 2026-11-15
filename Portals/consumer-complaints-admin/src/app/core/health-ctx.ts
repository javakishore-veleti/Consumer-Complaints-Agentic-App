import { SUCCESS } from './return-codes';
import { environment } from '../../environments/environment';

export interface HealthReq {}
export interface HealthResp {
  ok: boolean;
  apiBaseUrl: string;
}
export interface HealthCtx {
  req: HealthReq;
  resp: HealthResp;
}

/** Example portal method: one ctx in, integer out (D5 / D65). */
export function checkHealth(ctx: HealthCtx): number {
  ctx.resp.ok = true;
  ctx.resp.apiBaseUrl = environment.apiBaseUrl;
  return SUCCESS;
}
