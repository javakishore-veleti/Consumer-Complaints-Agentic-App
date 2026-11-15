import { HttpErrorResponse } from '@angular/common/http';
import { httpErrorMessage } from './http-error-message';

describe('httpErrorMessage', () => {
  it('returns string detail from FastAPI body', () => {
    const err = new HttpErrorResponse({
      error: { detail: 'engine start failed' },
      status: 502,
      statusText: 'Bad Gateway',
    });
    expect(httpErrorMessage(err, 'fallback')).toBe('engine start failed');
  });

  it('joins validation-array detail msgs', () => {
    const err = new HttpErrorResponse({
      error: { detail: [{ msg: 'field a' }, { msg: 'field b' }] },
      status: 422,
      statusText: 'Unprocessable Entity',
    });
    expect(httpErrorMessage(err, 'fallback')).toBe('field a; field b');
  });

  it('uses fallback when body has no detail', () => {
    const err = new HttpErrorResponse({
      error: 'boom',
      status: 500,
      statusText: 'Server Error',
    });
    expect(httpErrorMessage(err, 'Failed to load')).toBe('Failed to load');
  });

  it('uses fallback for non-HTTP errors', () => {
    expect(httpErrorMessage(new Error('x'), 'Failed to load')).toBe('Failed to load');
  });
});
