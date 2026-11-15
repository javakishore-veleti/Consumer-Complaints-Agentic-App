import { HttpErrorResponse } from '@angular/common/http';

/** Prefer FastAPI `detail` when present; otherwise use `fallback`. Never invent status enums. */
export function httpErrorMessage(err: unknown, fallback: string): string {
  if (!(err instanceof HttpErrorResponse)) {
    return fallback;
  }
  const detail = err.error?.detail;
  if (typeof detail === 'string' && detail.trim() !== '') {
    return detail;
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) =>
        item && typeof item === 'object' && 'msg' in item
          ? String((item as { msg: unknown }).msg)
          : '',
      )
      .filter((s) => s.trim() !== '');
    if (parts.length) {
      return parts.join('; ');
    }
  }
  return fallback;
}
