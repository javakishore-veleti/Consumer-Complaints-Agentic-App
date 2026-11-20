import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { SchemasPageComponent } from './schemas-page.component';

describe('SchemasPageComponent', () => {
  let httpMock: HttpTestingController;

  const applyIceberg = {
    id: 'w-apply-iceberg',
    workflow_name: 'apply_iceberg_foundational_schema',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'apply_iceberg_foundational_schema',
    enabled: true,
  };

  const hydrateRaw = {
    id: 'w-hydrate-raw',
    workflow_name: 'hydrate_raw_iceberg_3m',
    engine_type: 'apache_airflow',
    engine_workflow_id: 'hydrate_raw_iceberg_3m',
    enabled: true,
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SchemasPageComponent],
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

  it('renders Schemas shell and only apply_* workflows', async () => {
    const fixture = TestBed.createComponent(SchemasPageComponent);
    fixture.detectChanges();
    flushStatus([
      {
        id: 'm1',
        name: 'Customer complaints 3 months 2026',
        description: null,
        latest_ingest: null,
        allowed_workflows: [hydrateRaw, applyIceberg],
      },
    ]);
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('[data-testid="schemas-page"]'))).toBeTruthy();
    const select = fixture.debugElement.query(By.css('[data-testid="mio-workflow-select"]'));
    expect(select.nativeElement.textContent).toContain('apply_iceberg_foundational_schema');
    expect(select.nativeElement.textContent).not.toContain('hydrate_raw_iceberg_3m');
    const btn = fixture.debugElement.query(By.css('[data-testid="mio-start-workflow"]'));
    expect(btn.nativeElement.disabled).toBe(false);
  });
});
