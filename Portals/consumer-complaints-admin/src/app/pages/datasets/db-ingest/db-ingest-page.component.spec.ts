import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { DbIngestPageComponent } from './db-ingest-page.component';

describe('DbIngestPageComponent', () => {
  let httpMock: HttpTestingController;

  const ingestAll = {
    id: 'w-ingest',
    workflow_name: 'ingest_cfpb_all',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'ingest_cfpb_all',
    enabled: true,
  };

  const wrapper = {
    id: 'w-wrapper',
    workflow_name: 'ingest_cfpb_imports_wrapper',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'ingest_cfpb_imports_wrapper',
    enabled: true,
  };

  const downloadAll = {
    id: 'w-download',
    workflow_name: 'download_cfpb_all',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'download_cfpb_all',
    enabled: true,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DbIngestPageComponent],
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

  function flushBoot(status: unknown[] = [], imports: unknown[] = []): void {
    const statusReq = httpMock.expectOne((r) => r.url.includes('/mios/status'));
    const importsReq = httpMock.expectOne((r) => r.url.includes('/dataset-import-runs'));
    statusReq.flush(status);
    importsReq.flush(imports);
  }

  it('renders import runs and prefers wrapper workflow', async () => {
    const fixture = TestBed.createComponent(DbIngestPageComponent);
    fixture.detectChanges();
    flushBoot(
      [
        {
          id: 'm1',
          name: 'Customer complaints all 2026',
          description: null,
          latest_ingest: {
            id: 'i1',
            mio_id: 'm1',
            status: 'completed',
            message: null,
            rows_loaded: 10,
            batch_count: null,
            increment_marker: null,
            requested_at: '2026-11-15T00:00:00Z',
            started_at: '2026-11-15T00:01:00Z',
            finished_at: '2026-11-15T00:02:00Z',
            executions: [],
          },
          allowed_workflows: [downloadAll, ingestAll, wrapper],
        },
      ],
      [
        {
          id: 'imp-1',
          run_folder_name: '2026-11-14-15-18-00',
          location_kind: 'local_path',
          location_ref: '/data/cfpb/2026-11-14-15-18-00',
          source_snapshot_start: '2026-11-14T15:18:00Z',
          source_snapshot_end: '2026-11-14T15:18:00Z',
          status: 'landed',
          workflow_started_at: '2026-11-14T15:18:00Z',
          workflow_completed_at: '2026-11-14T15:20:00Z',
          ingested_at: null,
          part_count: 2,
          message: null,
        },
        {
          id: 'imp-2',
          run_folder_name: '2026-11-14-16-00-00',
          location_kind: 'local_path',
          location_ref: '/data/cfpb/2026-11-14-16-00-00',
          source_snapshot_start: '2026-11-14T16:00:00Z',
          source_snapshot_end: '2026-11-14T16:00:00Z',
          status: 'ingested',
          workflow_started_at: '2026-11-14T16:00:00Z',
          workflow_completed_at: '2026-11-14T16:05:00Z',
          ingested_at: '2026-11-14T16:10:00Z',
          part_count: 1,
          message: null,
        },
      ],
    );
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('[data-testid="db-ingest-page"]'))).toBeTruthy();
    expect(fixture.debugElement.query(By.css('[data-testid="import-runs-list"]'))).toBeTruthy();
    const boxes = fixture.debugElement.queryAll(By.css('[data-testid="import-run-checkbox"]'));
    expect(boxes.length).toBe(2);
    expect(boxes[0].nativeElement.disabled).toBe(false);
    expect(boxes[1].nativeElement.disabled).toBe(true);
    const select = fixture.debugElement.query(By.css('[data-testid="mio-workflow-select"]'));
    expect(select.nativeElement.textContent).toContain('ingest_cfpb_imports_wrapper');
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(true);
    boxes[0].nativeElement.click();
    boxes[0].nativeElement.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(btn.nativeElement.disabled).toBe(false);
  });

  it('allows Start for legacy ingest when there is no prior status', async () => {
    const fixture = TestBed.createComponent(DbIngestPageComponent);
    fixture.detectChanges();
    flushBoot(
      [
        {
          id: 'm1',
          name: 'Customer complaints all 2026',
          description: null,
          latest_ingest: null,
          allowed_workflows: [ingestAll],
        },
      ],
      [],
    );
    await settle();
    fixture.detectChanges();
    const select = fixture.debugElement.query(By.css('[data-testid="mio-workflow-select"]'));
    select.nativeElement.value = ingestAll.id;
    select.nativeElement.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(false);
  });
});
