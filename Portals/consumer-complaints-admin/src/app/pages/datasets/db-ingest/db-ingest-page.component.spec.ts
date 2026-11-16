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

  function flushStatus(status: unknown[] = []): void {
    httpMock.expectOne((r) => r.url.includes('/mios/status')).flush(status);
  }

  it('renders the DB Ingest shell and only ingest_* workflows', async () => {
    const fixture = TestBed.createComponent(DbIngestPageComponent);
    fixture.detectChanges();
    flushStatus([
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
        allowed_workflows: [downloadAll, ingestAll],
      },
    ]);
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('[data-testid="db-ingest-page"]'))).toBeTruthy();
    const select = fixture.debugElement.query(By.css('[data-testid="mio-workflow-select"]'));
    expect(select.nativeElement.textContent).toContain('ingest_cfpb_all');
    expect(select.nativeElement.textContent).not.toContain('download_cfpb_all');
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(false);
  });

  it('disables Start when there is no prior status (download not done)', async () => {
    const fixture = TestBed.createComponent(DbIngestPageComponent);
    fixture.detectChanges();
    flushStatus([
      {
        id: 'm1',
        name: 'Customer complaints all 2026',
        description: null,
        latest_ingest: null,
        allowed_workflows: [ingestAll],
      },
    ]);
    await settle();
    fixture.detectChanges();
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(true);
  });
});
