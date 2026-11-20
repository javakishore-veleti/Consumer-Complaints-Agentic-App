import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { AppSidebarComponent } from './app-sidebar.component';
import { SidebarService } from '../../../core/services/sidebar.service';

/** M59-0001 / #402: top-level Admin left-nav order. */
describe('AppSidebarComponent nav order', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AppSidebarComponent],
      providers: [SidebarService, provideRouter([])],
    }).compileComponents();
  });

  it('orders top-level items Dashboard → App Endpoints → Schemas → DataSets → …', () => {
    const fixture = TestBed.createComponent(AppSidebarComponent);
    const order = fixture.componentInstance.navItems.map((i) => i.name);
    expect(order).toEqual([
      'Dashboard',
      'App Endpoints',
      'Schemas',
      'DataSets',
      'DB Ingest',
      'Lakehouse',
      'Vector Stores',
      'Workflow Logs',
      'Operations',
    ]);
  });
});
