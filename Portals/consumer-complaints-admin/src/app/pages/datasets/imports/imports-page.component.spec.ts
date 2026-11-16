import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ImportsPageComponent } from './imports-page.component';

describe('ImportsPageComponent', () => {
  let httpMock: HttpTestingController;

  const downloadAll = {
    id: 'w1',
    workflow_name: 'download_cfpb_all',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'download_cfpb_all',
    enabled: true,
  };

  const filter3m = {
    id: 'w2',
    workflow_name: 'filter_cfpb_3_months',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'filter_cfpb_3_months',
    enabled: true,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImportsPageComponent],
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

  function flushEndpoints(endpoints: unknown[] = []): void {
    httpMock
      .expectOne((r) => r.url.includes('/app-endpoints'))
      .flush(endpoints);
  }

  function flushStatus(status: unknown[] = []): void {
    httpMock.expectOne((r) => r.url.includes('/mios/status')).flush(status);
  }

  /** Init loads status + AppEndpoints in parallel. */
  function flushInit(status: unknown[] = [], endpoints: unknown[] = []): void {
    flushStatus(status);
    flushEndpoints(endpoints);
  }

  const sampleEndpoint = {
    id: 'ccbce57d-bd9f-56fe-a258-fa2deb9dd393',
    name: 'cfpb_source_http_to_local',
    category: 'source',
    from_dataset_location_id: 'loc-http',
    from_env_var_name: null,
    to_dataset_location_id: 'loc-local',
    to_env_var_name: null,
    credentials_ref: null,
    description: 'CFPB HTTP → local',
    enabled: true,
    created_at: '2026-11-15T00:00:00Z',
    updated_at: '2026-11-15T00:00:00Z',
  };

  it('renders the accordion shell host', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
    fixture.detectChanges();
    flushInit();
    await settle();
    fixture.detectChanges();
    const host = fixture.debugElement.query(By.css('[data-testid="imports-accordion-shell"]'));
    expect(host).toBeTruthy();
  });

  it('lists AppEndpoints from GET /app-endpoints without secret values', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
    fixture.detectChanges();
    flushInit([], [sampleEndpoint]);
    await settle();
    fixture.detectChanges();
    const panel = fixture.debugElement.query(By.css('[data-testid="app-endpoints-panel"]'));
    expect(panel).toBeTruthy();
    const rows = fixture.debugElement.queryAll(By.css('[data-testid="app-endpoints-row"]'));
    expect(rows.length).toBe(1);
    expect(rows[0].nativeElement.textContent).toContain('cfpb_source_http_to_local');
    expect(rows[0].nativeElement.textContent).toContain('source');
    expect(rows[0].nativeElement.textContent).toContain('loc:loc-http');
    expect(rows[0].nativeElement.textContent).toContain('loc:loc-local');
    expect(panel.nativeElement.textContent).toContain('values are never shown');
    expect(panel.nativeElement.textContent).not.toMatch(/password|api[_-]?key/i);
  });

  it('renders one accordion per MIO with API status verbatim', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
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
        allowed_workflows: [filter3m],
      },
      {
        id: 'm2',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
        allowed_workflows: [downloadAll],
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

  it('shows only per-MIO allowed workflows in the picker', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: null,
        latest_ingest: null,
        allowed_workflows: [filter3m],
      },
      {
        id: 'm2',
        name: 'Customer complaints all 2026',
        description: null,
        latest_ingest: null,
        allowed_workflows: [downloadAll],
      },
    ]);
    await settle();
    fixture.detectChanges();
    const selects = fixture.debugElement.queryAll(By.css('[data-testid="mio-workflow-select"]'));
    expect(selects[0].nativeElement.textContent).toContain('filter_cfpb_3_months');
    expect(selects[0].nativeElement.textContent).not.toContain('download_cfpb_all');
    expect(selects[1].nativeElement.textContent).toContain('download_cfpb_all');
    expect(selects[1].nativeElement.textContent).not.toContain('filter_cfpb_3_months');
  });

  it('disables Start when allowed_workflows is empty', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints 6 months 2026',
        description: null,
        latest_ingest: null,
        allowed_workflows: [],
      },
    ]);
    await settle();
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(true);
  });

  it('shows load error without fabricating status rows', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
    fixture.detectChanges();
    httpMock
      .expectOne((r) => r.url.includes('/mios/status'))
      .flush('boom', { status: 500, statusText: 'Server Error' });
    flushEndpoints();
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.queryAll(By.css('[data-testid="mio-accordion"]')).length).toBe(0);
    const err = fixture.debugElement.query(By.css('[data-testid="mio-status-error"]'));
    expect(err).toBeTruthy();
    expect(err.nativeElement.textContent.length).toBeGreaterThan(0);
  });

  it('disables Start when latest_ingest status is started', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
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
        allowed_workflows: [downloadAll],
      },
    ]);
    await settle();
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(true);
  });

  it('starts workflow with mio_id then refreshes status', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
        allowed_workflows: [downloadAll],
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
        allowed_workflows: [downloadAll],
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

  it('Refresh status reloads GET /mios/status and AppEndpoints', async () => {
    const fixture = TestBed.createComponent(ImportsPageComponent);
    fixture.detectChanges();
    flushInit([
      {
        id: 'm1',
        name: 'Customer complaints all',
        description: null,
        latest_ingest: null,
        allowed_workflows: [downloadAll],
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
        allowed_workflows: [downloadAll],
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
    flushEndpoints([sampleEndpoint]);
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('.mio-status')).nativeElement.textContent).toContain(
      'completed',
    );
    expect(
      fixture.debugElement.queryAll(By.css('[data-testid="app-endpoints-row"]')).length,
    ).toBe(1);
  });
});
