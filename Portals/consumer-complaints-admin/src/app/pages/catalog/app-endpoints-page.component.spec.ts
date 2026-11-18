import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { AppEndpointsPageComponent } from './app-endpoints-page.component';

describe('AppEndpointsPageComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppEndpointsPageComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('lists App Endpoints from GET /app-endpoints', async () => {
    const fixture = TestBed.createComponent(AppEndpointsPageComponent);
    fixture.detectChanges();
    httpMock
      .expectOne((r) => r.url.includes('/app-endpoints'))
      .flush([
        {
          id: 'e1',
          name: 'cfpb_source_http_to_local',
          category: 'source',
          from_env_var_name: 'CCA_CFPB_URL',
          to_env_var_name: 'LOCAL_DATA_PATH_CFPB',
          credentials_ref: null,
          enabled: true,
        },
      ]);
    await fixture.whenStable();
    fixture.detectChanges();
    expect(fixture.debugElement.query(By.css('[data-testid="app-endpoints-page"]'))).toBeTruthy();
    const rows = fixture.debugElement.queryAll(By.css('[data-testid="app-endpoints-row"]'));
    expect(rows.length).toBe(1);
    expect(rows[0].nativeElement.textContent).toContain('cfpb_source_http_to_local');
  });
});
