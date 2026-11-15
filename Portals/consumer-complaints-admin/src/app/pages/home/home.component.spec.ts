import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { HomeComponent } from './home.component';

describe('HomeComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [HomeComponent],
      providers: [provideRouter([]), provideHttpClient(), provideHttpClientTesting()],
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

  it('does not show API base URL copy', async () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    httpMock.expectOne((r) => r.url.includes('/mios/status')).flush([]);
    await settle();
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).not.toContain('API base URL');
    expect(fixture.nativeElement.textContent).not.toContain('/api');
  });

  it('shows KPI counts from live MIO status', async () => {
    const fixture = TestBed.createComponent(HomeComponent);
    fixture.detectChanges();
    httpMock.expectOne((r) => r.url.includes('/mios/status')).flush([
      { id: '1', name: 'a', description: null, latest_ingest: null },
      {
        id: '2',
        name: 'b',
        description: null,
        latest_ingest: {
          id: 'i',
          mio_id: '2',
          status: 'failed',
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
      {
        id: '3',
        name: 'c',
        description: null,
        latest_ingest: {
          id: 'i2',
          mio_id: '3',
          status: 'completed',
          message: null,
          rows_loaded: 1,
          batch_count: null,
          increment_marker: null,
          requested_at: '2026-11-15T00:00:00Z',
          started_at: null,
          finished_at: null,
          executions: [],
        },
      },
      {
        id: '4',
        name: 'd',
        description: null,
        latest_ingest: {
          id: 'i3',
          mio_id: '4',
          status: 'started',
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
    expect(fixture.debugElement.query(By.css('[data-testid="home-kpi-idle"]')).nativeElement.textContent).toContain(
      '1',
    );
    expect(
      fixture.debugElement.query(By.css('[data-testid="home-kpi-failed"]')).nativeElement.textContent,
    ).toContain('1');
    expect(
      fixture.debugElement.query(By.css('[data-testid="home-kpi-completed"]')).nativeElement
        .textContent,
    ).toContain('1');
    expect(
      fixture.debugElement.query(By.css('[data-testid="home-kpi-in-progress"]')).nativeElement
        .textContent,
    ).toContain('1');
    expect(fixture.debugElement.query(By.css('[data-testid="home-cta-imports"]'))).toBeTruthy();
  });
});
