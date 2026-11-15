import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ImportsPage } from './imports-page';

describe('ImportsPage', () => {
  let httpMock: HttpTestingController;

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
  }

  it('renders the accordion shell host', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    httpMock.expectOne('/api/mios/status').flush([]);
    await settle();
    fixture.detectChanges();
    const host = fixture.debugElement.query(By.css('[data-testid="imports-accordion-shell"]'));
    expect(host).toBeTruthy();
  });

  it('renders one accordion per MIO with API status verbatim', async () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    httpMock.expectOne('/api/mios/status').flush([
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
    httpMock.expectOne('/api/mios/status').flush('boom', {
      status: 500,
      statusText: 'Server Error',
    });
    await settle();
    fixture.detectChanges();
    expect(fixture.debugElement.queryAll(By.css('[data-testid="mio-accordion"]')).length).toBe(0);
    const err = fixture.debugElement.query(By.css('[data-testid="mio-status-error"]'));
    expect(err).toBeTruthy();
    expect(err.nativeElement.textContent.length).toBeGreaterThan(0);
  });
});
