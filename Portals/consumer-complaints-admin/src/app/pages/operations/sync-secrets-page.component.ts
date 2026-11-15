import { Component, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';
import { ButtonComponent } from '../../shared/components/ui/button/button.component';
import {
  upsertAirflowSecrets,
  UpsertSecretResult,
  UpsertSecretsCtx,
} from '../../core/airflow-upsert-secrets';
import { SUCCESS } from '../../core/return-codes';

@Component({
  selector: 'app-sync-secrets-page',
  imports: [AlertComponent, ButtonComponent],
  templateUrl: './sync-secrets-page.component.html',
})
export class SyncSecretsPageComponent {
  private readonly http = inject(HttpClient);

  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly info = signal('');
  protected readonly results = signal<UpsertSecretResult[]>([]);

  protected async onSync(): Promise<void> {
    if (this.busy()) {
      return;
    }
    this.busy.set(true);
    this.error.set('');
    this.info.set('');
    this.results.set([]);
    const ctx: UpsertSecretsCtx = { resp: { results: [], error: '' } };
    const code = await upsertAirflowSecrets(this.http, ctx);
    this.busy.set(false);
    this.results.set(ctx.resp.results);
    if (code === SUCCESS) {
      this.info.set('Synced named variables to Airflow. Values are never shown here.');
      return;
    }
    this.error.set(ctx.resp.error || 'Sync secrets failed');
  }
}
