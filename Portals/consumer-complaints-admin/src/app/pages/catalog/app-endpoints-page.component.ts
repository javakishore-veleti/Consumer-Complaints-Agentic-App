import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';
import { ButtonComponent } from '../../shared/components/ui/button/button.component';
import {
  AppEndpointEntry,
  AppEndpointsCtx,
  endpointSideLabel,
  loadAppEndpoints,
} from '../../core/app-endpoints';
import { SUCCESS } from '../../core/return-codes';

@Component({
  selector: 'app-app-endpoints-page',
  imports: [AlertComponent, ButtonComponent],
  templateUrl: './app-endpoints-page.component.html',
})
export class AppEndpointsPageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly appEndpoints = signal<AppEndpointEntry[]>([]);
  protected readonly appEndpointsError = signal('');
  protected readonly loading = signal(true);
  protected readonly endpointSideLabel = endpointSideLabel;

  async ngOnInit(): Promise<void> {
    await this.loadEndpoints();
    this.loading.set(false);
  }

  protected async onRefresh(): Promise<void> {
    this.loading.set(true);
    await this.loadEndpoints();
    this.loading.set(false);
  }

  private async loadEndpoints(): Promise<void> {
    const ctx: AppEndpointsCtx = {
      req: { enabled: true },
      resp: { entries: [], error: '' },
    };
    const code = await loadAppEndpoints(this.http, ctx);
    if (code === SUCCESS) {
      this.appEndpoints.set(ctx.resp.entries);
      this.appEndpointsError.set('');
    } else {
      this.appEndpoints.set([]);
      this.appEndpointsError.set(ctx.resp.error || 'Failed to load AppEndpoints');
    }
  }
}
