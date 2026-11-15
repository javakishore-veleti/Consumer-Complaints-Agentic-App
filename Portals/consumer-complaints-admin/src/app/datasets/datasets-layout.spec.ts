import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { By } from '@angular/platform-browser';
import { DatasetsLayout } from './datasets-layout';

describe('DatasetsLayout', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DatasetsLayout],
      providers: [provideRouter([])],
    }).compileComponents();
  });

  it('shows Imports as a router link and DB Ingest as disabled', () => {
    const fixture = TestBed.createComponent(DatasetsLayout);
    fixture.detectChanges();
    const imports = fixture.debugElement.query(By.css('a[data-testid="left-nav-imports"]'));
    expect(imports).toBeTruthy();
    expect(imports.nativeElement.textContent.trim()).toBe('Imports');

    const dbIngest = fixture.debugElement.query(By.css('[data-testid="left-nav-db-ingest"]'));
    expect(dbIngest).toBeTruthy();
    expect(dbIngest.nativeElement.textContent.trim()).toBe('DB Ingest');
    expect(
      dbIngest.nativeElement.getAttribute('aria-disabled') === 'true' ||
        dbIngest.nativeElement.hasAttribute('disabled'),
    ).toBe(true);
  });
});
