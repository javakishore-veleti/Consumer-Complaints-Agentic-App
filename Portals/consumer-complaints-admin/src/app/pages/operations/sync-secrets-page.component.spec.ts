import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { SyncSecretsPageComponent } from './sync-secrets-page.component';

describe('SyncSecretsPageComponent', () => {
  let fixture: ComponentFixture<SyncSecretsPageComponent>;
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [SyncSecretsPageComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    fixture = TestBed.createComponent(SyncSecretsPageComponent);
    httpMock = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  });

  afterEach(() => httpMock.verify());

  it('Sync button POSTs upsert-secrets and lists outcomes', async () => {
    const btn: HTMLButtonElement = fixture.nativeElement.querySelector(
      '[data-testid="sync-secrets-button"]',
    );
    btn.click();
    fixture.detectChanges();
    const req = httpMock.expectOne('/api/management/airflow/upsert-secrets');
    expect(req.request.method).toBe('POST');
    req.flush({
      results: [{ name: 'CCA_CALLBACK_SECRET', outcome: 'updated' }],
    });
    await fixture.whenStable();
    fixture.detectChanges();
    const rows = fixture.nativeElement.querySelectorAll(
      '[data-testid="sync-secrets-result-row"]',
    );
    expect(rows.length).toBe(1);
    expect(rows[0].textContent).toContain('CCA_CALLBACK_SECRET');
    expect(rows[0].textContent).toContain('updated');
    expect(fixture.nativeElement.textContent).not.toContain('never-leak');
  });
});
