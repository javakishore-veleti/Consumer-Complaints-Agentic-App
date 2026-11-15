import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ImportsPage } from './imports-page';

describe('ImportsPage', () => {
  let httpMock: HttpTestingController;

  const defaultWorkflows = [
    {
      id: 'w1',
      workflow_name: 'download_cfpb_all',
      engine_type: 'apache_airflow',
      engine_workflow_id: 'download_cfpb_all',
      enabled: true,
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImportsPage],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  async function settle(): Promise<void> {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  }

  function flushInit(
    status: unknown[] = [],
    workflows: unknown[] = defaultWorkflows,
  ): void {
    const pending = httpMock.match(
      (r) => r.url.includes('/mios/status') || r.url.includes('/workflows'),
    );
    for (const req of pending) {
      if (req.request.url.includes('/mios/status')) {
        req.flush(status);
      } else {
        req.flush(workflows);
      }
    }
  }

  it('renders the accordion shell host', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    flushInit();
    await settle();
    fixture.detectChanges();
    const host = fixture.debugElement.query(By.css('[data-testid="imports-accordion-shell"]'));
    expect(host).toBeTruthy();
  });

  it('renders one accordion per MIO with API status verbatim', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: null,
        latest_ingest: {
          id: 'i1',
          mio_id: 'm1',
          status: 'failed',
          message: 'disk full',
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-14T00:00:00Z',
          started_at: null,
          finished_at: null,
          executions: [],
        },
      },
      {
        id: 'm2',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
      },
    ]);
    await settle();
    fixture.detectChanges();
    const panels = fixture.debugElement.queryAll(By.css('[data-testid="mio-accordion"]'));
    expect(panels.length).toBe(2);
    expect(panels[0].nativeElement.textContent).toContain('Customer complaints 3 months 2026');
    expect(panels[0].nativeElement.textContent).toContain('failed');
    expect(panels[0].nativeElement.textContent).toContain('disk full');
    expect(panels[1].nativeElement.textContent).toContain('No ingest yet');
  });

  it('shows load error without fabricating status rows', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    const pending = httpMock.match(
      (r) => r.url.includes('/mios/status') || r.url.includes('/workflows'),
    );
    for (const req of pending) {
      if (req.request.url.includes('/mios/status')) {
        req.flush('boom', { status: 500, statusText: 'Server Error' });
      } else {
        req.flush(defaultWorkflows);
      }
    }
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.queryAll(By.css('[data-testid="mio-accordion"]')).length).toBe(0);
    const err = fixture.debugElement.query(By.css('[data-testid="mio-status-error"]'));
    expect(err).toBeTruthy();
    expect(err.nativeElement.textContent.length).toBeGreaterThan(0);
  });

  it('disables Start when latest_ingest status is started', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: {
          id: 'i1',
          mio_id: 'm1',
          status: 'started',
          message: null,
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-14T00:00:00Z',
          started_at: '2026-11-14T00:01:00Z',
          finished_at: null,
          executions: [],
        },
      },
    ]);
    await settle();
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(true);
  });

  it('starts workflow with mio_id then refreshes status', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
      },
    ]);
    await settle();
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(false);
    btn.nativeElement.click();
    await settle();
    const startReq = httpMock.expectOne('/api/workflows/w1/start');
    expect(startReq.request.method).toBe('POST');
    expect(startReq.request.body).toEqual({ mio_id: 'm1' });
    startReq.flush({ execution_id: 'e1' }, { status: 202, statusText: 'Accepted' });
    await settle();
    httpMock.expectOne('/api/mios/status').flush([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: {
          id: 'i2',
          mio_id: 'm1',
          status: 'requested',
          message: null,
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-15T00:00:00Z',
          started_at: null,
          finished_at: null,
          executions: [],
        },
      },
    ]);
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('.mio-status')).nativeElement.textContent).toContain(
      'requested',
    );
  });

  it('Refresh status reloads GET /mios/status', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
      },
    ]);
    await settle();
    fixture.detectChanges();
    fixture.debugElement.query(By.css('[data-testid="mio-refresh-status"]')).nativeElement.click();
    await settle();
    httpMock.expectOne('/api/mios/status').flush([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: {
          id: 'i3',
          mio_id: 'm1',
          status: 'completed',
          message: null,
          rows_loaded: 1,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-15T00:00:00Z',
          started_at: '2026-11-15T00:01:00Z',
          finished_at: '2026-11-15T00:02:00Z',
          executions: [],
        },
      },
    ]);
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('.mio-status')).nativeElement.textContent).toContain(
      'completed',
    );
  });
});
