import { Component, OnInit, signal } from '@angular/core';
import { checkHealth, HealthCtx } from '../core/health-ctx';
import { UiPageHeader } from '../shared/ui/ui-page-header/ui-page-header';

@Component({
  selector: 'app-home',
  imports: [UiPageHeader],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit {
  protected readonly apiBaseUrl = signal('');

  ngOnInit(): void {
    const ctx: HealthCtx = { req: {}, resp: { ok: false, apiBaseUrl: '' } };
    checkHealth(ctx);
    this.apiBaseUrl.set(ctx.resp.apiBaseUrl);
  }
}
