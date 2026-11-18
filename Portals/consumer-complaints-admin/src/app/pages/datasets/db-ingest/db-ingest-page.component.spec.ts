import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import {
  DbIngestPageComponent,
  IMPORT_RUNS_PAGE_SIZE,
} from './db-ingest-page.component';

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

  function landedRun(id: string, folder: string): Record<string, unknown> {
    return {
      id,
      run_folder_name: folder,
      location_kind: 'local_path',
      location_ref: `/data/cfpb/${folder}`,
      source_snapshot_start: '2026-11-14T15:18:00Z',
      source_snapshot_end: '2026-11-14T15:18:00Z',
      status: 'landed',
      workflow_started_at: '2026-11-14T15:18:00Z',
      workflow_completed_at: '2026-11-14T15:20:00Z',
      ingested_at: null,
      part_count: 2,
      message: null,
    };
  }

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
        landedRun('imp-1', '2026-11-14-15-18-00'),
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
    const reason = fixture.debugElement.query(By.css('[data-testid="mio-start-disabled-reason"]'));
    expect(reason.nativeElement.textContent).toContain('Select one or more landed import runs');
    boxes[0].nativeElement.checked = true;
    boxes[0].nativeElement.dispatchEvent(new Event('change'));
    fixture.detectChanges();
    expect(btn.nativeElement.disabled).toBe(false);
    expect(fixture.debugElement.query(By.css('[data-testid="mio-start-disabled-reason"]'))).toBeNull();
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

  it('paginates import runs and filters by search', async () => {
    const fixture = TestBed.createComponent(DbIngestPageComponent);
    fixture.detectChanges();
    const many = Array.from({ length: IMPORT_RUNS_PAGE_SIZE + 3 }, (_, i) =>
      landedRun(`imp-${i}`, `2026-11-14-15-${String(i).padStart(2, '0')}-00`),
    );
    flushBoot(
      [
        {
          id: 'm1',
          name: 'Customer complaints 3 months 2026',
          description: null,
          latest_ingest: null,
          allowed_workflows: [wrapper],
        },
      ],
      many,
    );
    await settle();
    fixture.detectChanges();

    let boxes = fixture.debugElement.queryAll(By.css('[data-testid="import-run-checkbox"]'));
    expect(boxes.length).toBe(IMPORT_RUNS_PAGE_SIZE);
    const meta = fixture.debugElement.query(By.css('[data-testid="import-runs-page-meta"]'));
    expect(meta.nativeElement.textContent).toContain(`${IMPORT_RUNS_PAGE_SIZE + 3} match`);
    expect(meta.nativeElement.textContent).toContain('page 1 / 2');

    const next = fixture.debugElement.query(By.css('[data-testid="import-runs-next-page"]'));
    next.nativeElement.click();
    fixture.detectChanges();
    boxes = fixture.debugElement.queryAll(By.css('[data-testid="import-run-checkbox"]'));
    expect(boxes.length).toBe(3);
    expect(meta.nativeElement.textContent).toContain('page 2 / 2');

    const search = fixture.debugElement.query(By.css('[data-testid="import-runs-search"]'));
    search.nativeElement.value = '15-27-00';
    search.nativeElement.dispatchEvent(new Event('input'));
    fixture.detectChanges();
    boxes = fixture.debugElement.queryAll(By.css('[data-testid="import-run-checkbox"]'));
    expect(boxes.length).toBe(1);
    expect(
      fixture.debugElement.query(By.css('[data-testid="import-runs-page-meta"]')).nativeElement
        .textContent,
    ).toContain('1 match');
  });

  it('select latest landed checks the first landed run', async () => {
    const fixture = TestBed.createComponent(DbIngestPageComponent);
    fixture.detectChanges();
    flushBoot(
      [
        {
          id: 'm1',
          name: 'Customer complaints 3 months 2026',
          description: null,
          latest_ingest: null,
          allowed_workflows: [wrapper],
        },
      ],
      [
        {
          id: 'imp-old',
          run_folder_name: '2026-11-14-10-00-00',
          location_kind: 'local_path',
          location_ref: '/data/cfpb/2026-11-14-10-00-00',
          source_snapshot_start: '2026-11-14T10:00:00Z',
          source_snapshot_end: '2026-11-14T10:00:00Z',
          status: 'ingested',
          workflow_started_at: '2026-11-14T10:00:00Z',
          workflow_completed_at: '2026-11-14T10:05:00Z',
          ingested_at: '2026-11-14T10:10:00Z',
          part_count: 1,
          message: null,
        },
        landedRun('imp-latest', '2026-11-14-15-18-00'),
      ],
    );
    await settle();
    fixture.detectChanges();

    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(true);

    fixture.debugElement.query(By.css('[data-testid="import-runs-select-latest"]')).nativeElement.click();
    fixture.detectChanges();

    expect(btn.nativeElement.disabled).toBe(false);
    expect(
      fixture.debugElement.query(By.css('[data-testid="import-runs-selected-count"]')).nativeElement
        .textContent,
    ).toContain('1 selected');
  });
});
