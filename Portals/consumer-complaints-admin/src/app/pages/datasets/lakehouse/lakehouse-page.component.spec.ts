import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { LakehousePageComponent } from './lakehouse-page.component';

describe('LakehousePageComponent', () => {
  let httpMock: HttpTestingController;

  const hydrateRaw = {
    id: 'w-hydrate-raw',
    workflow_name: 'hydrate_raw_iceberg_3m',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'hydrate_raw_iceberg_3m',
    enabled: true,
  };

  const hydrateChroma = {
    id: 'w-hydrate-chroma',
    workflow_name: 'hydrate_chroma_signatures_3m',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'hydrate_chroma_signatures_3m',
    enabled: true,
  };

  const hydrateCurated = {
    id: 'w-hydrate-curated',
    workflow_name: 'hydrate_curated_iceberg_3m',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'hydrate_curated_iceberg_3m',
    enabled: true,
  };

  const filter3m = {
    id: 'w-filter',
    workflow_name: 'filter_cfpb_3_months',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'filter_cfpb_3_months',
    enabled: true,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LakehousePageComponent],
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

  function flushStatus(status: unknown[] = []): void {
    httpMock.expectOne((r) => r.url.includes('/mios/status')).flush(status);
  }

  it('renders Lakehouse shell and only hydrate_* workflows', async () => {
    const fixture = TestBed.createComponent(LakehousePageComponent);
    fixture.detectChanges();
    flushStatus([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: null,
        latest_ingest: null,
        allowed_workflows: [filter3m, hydrateRaw],
      },
    ]);
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('[data-testid="lakehouse-page"]'))).toBeTruthy();
    const select = fixture.debugElement.query(By.css('[data-testid="mio-workflow-select"]'));
    expect(select.nativeElement.textContent).toContain('1. hydrate_raw_iceberg_3m');
    expect(select.nativeElement.textContent).not.toContain('filter_cfpb_3_months');
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(false);
  });

  it('orders hydrate workflows by pipeline sequence and defaults to raw', async () => {
    const fixture = TestBed.createComponent(LakehousePageComponent);
    fixture.detectChanges();
    flushStatus([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: null,
        latest_ingest: null,
        // Alphabetical would put chroma first — pipeline order must win.
        allowed_workflows: [hydrateChroma, hydrateCurated, hydrateRaw],
      },
    ]);
    await settle();
    fixture.detectChanges();
    const select: HTMLSelectElement = fixture.debugElement.query(
      By.css('[data-testid="mio-workflow-select"]'),
    ).nativeElement;
    const labels = Array.from(select.options).map((o) => o.textContent?.trim());
    expect(labels).toEqual([
      '1. hydrate_raw_iceberg_3m',
      '4. hydrate_curated_iceberg_3m',
      '5. hydrate_chroma_signatures_3m',
    ]);
    expect(select.value).toBe('w-hydrate-raw');
  });

  it('disables Start when a hydrate run is already started', async () => {
    const fixture = TestBed.createComponent(LakehousePageComponent);
    fixture.detectChanges();
    flushStatus([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: null,
        latest_ingest: {
          id: 'i1',
          mio_id: 'm1',
          status: 'started',
          message: null,
          rows_loaded: null,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-19T00:00:00Z',
          started_at: '2026-11-19T00:01:00Z',
          finished_at: null,
          executions: [
            {
              id: 'e1',
              workflow_id: 'w-hydrate-raw',
              workflow_name: 'hydrate_raw_iceberg_3m',
              engine_type: 'apache_airflow',
              engine_workflow_id: 'hydrate_raw_iceberg_3m',
              engine_run_id: 'run-1',
              status: 'started',
              message: null,
              mios_ingest_log_id: 'i1',
              requested_at: '2026-11-19T00:00:00Z',
              started_at: '2026-11-19T00:01:00Z',
              finished_at: null,
            },
          ],
        },
        allowed_workflows: [hydrateRaw],
      },
    ]);
    await settle();
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(true);
  });
});
