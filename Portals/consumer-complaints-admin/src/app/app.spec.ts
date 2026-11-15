import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { By } from '@angular/platform-browser';
import { App } from './app';
import { routes } from './app.routes';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter(routes)],
    }).compileComponents();
  });

  it('should create the app', () => {
    const fixture = TestBed.createComponent(App);
    expect(fixture.componentInstance).toBeTruthy();
  });

  it('exposes a DataSets top link to the datasets area', () => {
    const fixture = TestBed.createComponent(App);
    fixture.detectChanges();
    const link = fixture.debugElement.query(By.css('a[data-testid="top-nav-datasets"]'));
    expect(link).toBeTruthy();
    expect(link.nativeElement.textContent.trim()).toBe('DataSets');
    const href = link.nativeElement.getAttribute('href') ?? '';
    expect(href).toContain('/datasets');
  });
});
