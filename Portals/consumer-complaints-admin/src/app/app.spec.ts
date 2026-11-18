import { TestBed } from '@angular/core/testing';
import { provideRouter, Router } from '@angular/router';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { By } from '@angular/platform-browser';
import { AppComponent } from './app.component';
import { routes } from './app.routes';

describe('AppComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [provideRouter(routes), provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  async function renderShell() {
    const fixture = TestBed.createComponent(AppComponent);
    const router = TestBed.inject(Router);
    await router.navigateByUrl('/');
    fixture.detectChanges();
    await fixture.whenStable();
    const pending = httpMock.match((r) => r.url.includes('/mios/status'));
    for (const req of pending) {
      req.flush([]);
    }
    await fixture.whenStable();
    fixture.detectChanges();
    return fixture;
  }

  it('should create the app', () => {
    const fixture = TestBed.createComponent(AppComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('exposes DataSets nav control', async () => {
    const fixture = await renderShell();
    const link = fixture.debugElement.query(By.css('[data-testid="top-nav-datasets"]'));
    expect(link).toBeTruthy();
    expect(link.nativeElement.textContent).toContain('DataSets');
  });

  it('exposes Imports and disabled DB Ingest in the sidebar', async () => {
    const fixture = await renderShell();

    const datasets = fixture.debugElement.query(By.css('[data-testid="top-nav-datasets"]'));
    expect(datasets).toBeTruthy();
    datasets.nativeElement.click();
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();

    const imports = fixture.debugElement.query(By.css('a[data-testid="left-nav-imports"]'));
    expect(imports).toBeTruthy();
    expect(imports.nativeElement.textContent.trim()).toBe('Imports');

    const dbIngest = fixture.debugElement.query(By.css('[data-testid="left-nav-db-ingest"]'));
    expect(dbIngest).toBeTruthy();
    expect(dbIngest.nativeElement.textContent.trim()).toBe('DB Ingest');

    const indexNav = fixture.debugElement.query(By.css('[data-testid="left-nav-index"]'));
    expect(indexNav).toBeTruthy();
    expect(indexNav.nativeElement.textContent.trim()).toBe('Vector Stores');
  });
});
