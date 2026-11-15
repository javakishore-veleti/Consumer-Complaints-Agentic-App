import { TestBed } from '@angular/core/testing';
import { By } from '@angular/platform-browser';
import { ImportsPage } from './imports-page';

describe('ImportsPage', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ImportsPage],
    }).compileComponents();
  });

  it('renders the accordion shell host for later MIO status', () => {
    const fixture = TestBed.createComponent(ImportsPage);
    fixture.detectChanges();
    const host = fixture.debugElement.query(By.css('[data-testid="imports-accordion-shell"]'));
    expect(host).toBeTruthy();
  });
});
