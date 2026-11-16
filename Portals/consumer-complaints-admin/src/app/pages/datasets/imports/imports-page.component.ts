import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BadgeDirective, BadgeColor } from '../../../shared/components/ui/badge/badge.directive';
import { AlertComponent } from '../../../shared/components/ui/alert/alert.component';
import { ButtonComponent } from '../../../shared/components/ui/button/button.component';
import {
  loadMioStatus,
  MioAllowedWorkflow,
  MioStatusCtx,
  MioStatusEntry,
} from '../../../core/mio-status';
import {
  AppEndpointEntry,
  AppEndpointsCtx,
  endpointSideLabel,
  loadAppEndpoints,
} from '../../../core/app-endpoints';
import { startWorkflow, StartWorkflowCtx } from '../../../core/start-workflow';
import { SUCCESS } from '../../../core/return-codes';

const RUNNING_STATUSES = new Set(['requested', 'started']);

@Component({
  selector: 'app-imports-page',
  imports: [BadgeDirective, AlertComponent, ButtonComponent],
  templateUrl: './imports-page.component.html',
})
export class ImportsPageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly entries = signal<MioStatusEntry[]>([]);
  protected readonly error = signal('');
  protected readonly loading = signal(true);
  protected readonly selectedByMio = signal<Record<string, string>>({});
  protected readonly startingMioIds = signal<ReadonlySet<string>>(new Set());
  protected readonly actionError = signal('');
  protected readonly appEndpoints = signal<AppEndpointEntry[]>([]);
  protected readonly appEndpointsError = signal('');
  protected readonly endpointSideLabel = endpointSideLabel;

  async ngOnInit(): Promise<void> {
    await Promise.all([this.loadStatus(), this.loadEndpoints()]);
    this.loading.set(false);
  }

  protected allowedWorkflows(mio: MioStatusEntry): MioAllowedWorkflow[] {
    return (mio.allowed_workflows ?? []).filter(
      (w) =>
        w.enabled &&
        !w.workflow_name.startsWith('ingest_') &&
        !w.workflow_name.startsWith('index_'),
    );
  }

  protected selectedWorkflowId(mioId: string): string {
    return this.selectedByMio()[mioId] ?? '';
  }

  protected onWorkflowChange(mioId: string, event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.selectedByMio.update((m) => ({ ...m, [mioId]: value }));
  }

  protected isStartDisabled(mio: MioStatusEntry): boolean {
    const workflowId = this.selectedWorkflowId(mio.id);
    if (!workflowId) {
      return true;
    }
    if (this.startingMioIds().has(mio.id)) {
      return true;
    }
    const status = mio.latest_ingest?.status;
    return status !== undefined && status !== null && RUNNING_STATUSES.has(status);
  }

  protected async onStart(mio: MioStatusEntry): Promise<void> {
    const workflowId = this.selectedWorkflowId(mio.id);
    if (!workflowId || this.isStartDisabled(mio)) {
      return;
    }
    this.actionError.set('');
    this.startingMioIds.update((ids) => new Set([...ids, mio.id]));
    const ctx: StartWorkflowCtx = {
      req: { workflowId, mioId: mio.id },
      resp: { executionId: '', error: '' },
    };
    const code = await startWorkflow(this.http, ctx);
    this.startingMioIds.update((ids) => {
      const next = new Set(ids);
      next.delete(mio.id);
      return next;
    });
    if (code !== SUCCESS) {
      this.actionError.set(ctx.resp.error || 'Failed to start workflow');
      return;
    }
    await this.loadStatus();
  }

  protected async onRefresh(): Promise<void> {
    this.actionError.set('');
    await Promise.all([this.loadStatus(), this.loadEndpoints()]);
  }

  /** Visual color only — label text stays the API status string. */
  protected statusColor(status: string | null | undefined): BadgeColor {
    if (!status) {
      return 'gray';
    }
    switch (status) {
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'started':
      case 'requested':
        return 'info';
      default:
        return 'warning';
    }
  }

  private async loadStatus(): Promise<void> {
    const ctx: MioStatusCtx = { req: {}, resp: { entries: [], error: '' } };
    const code = await loadMioStatus(this.http, ctx);
    if (code === SUCCESS) {
      this.entries.set(ctx.resp.entries);
      this.error.set('');
      this.ensureSelections(ctx.resp.entries);
    } else {
      this.entries.set([]);
      this.error.set(ctx.resp.error || 'Failed to load MIO status');
    }
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

  private ensureSelections(entries: MioStatusEntry[]): void {
    this.selectedByMio.update((current) => {
      const next = { ...current };
      for (const mio of entries) {
        const allowed = this.allowedWorkflows(mio);
        if (!allowed.length) {
          delete next[mio.id];
          continue;
        }
        if (!next[mio.id] || !allowed.some((w) => w.id === next[mio.id])) {
          next[mio.id] = allowed[0].id;
        }
      }
      return next;
    });
  }
}
