import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { loadMioStatus, MioStatusCtx, MioStatusEntry } from '../../core/mio-status';
import { startWorkflow, StartWorkflowCtx } from '../../core/start-workflow';
import { listWorkflows, WorkflowListCtx, WorkflowListEntry } from '../../core/workflow-list';
import { SUCCESS } from '../../core/return-codes';

const RUNNING_STATUSES = new Set(['requested', 'started']);
const DEFAULT_WORKFLOW_NAME = 'download_cfpb_all';

@Component({
  selector: 'app-imports-page',
  templateUrl: './imports-page.html',
  styleUrl: './imports-page.css',
})
export class ImportsPage implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly entries = signal<MioStatusEntry[]>([]);
  protected readonly error = signal('');
  protected readonly loading = signal(true);
  protected readonly enabledWorkflows = signal<WorkflowListEntry[]>([]);
  protected readonly selectedByMio = signal<Record<string, string>>({});
  protected readonly startingMioIds = signal<ReadonlySet<string>>(new Set());
  protected readonly actionError = signal('');

  async ngOnInit(): Promise<void> {
    await Promise.all([this.loadStatus(), this.loadWorkflows()]);
    this.loading.set(false);
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
    await this.loadStatus();
  }

  /** Visual tone only — label text stays the API status string. Keeps `.mio-status` for tests. */
  protected statusBadgeClass(status: string | null | undefined): string {
    if (!status) {
      return 'mio-status badge badge-muted';
    }
    switch (status) {
      case 'completed':
        return 'mio-status badge badge-success';
      case 'failed':
        return 'mio-status badge badge-danger';
      case 'started':
      case 'requested':
        return 'mio-status badge badge-info';
      default:
        return 'mio-status badge badge-warning';
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

  private async loadWorkflows(): Promise<void> {
    const ctx: WorkflowListCtx = { req: {}, resp: { workflows: [], error: '' } };
    const code = await listWorkflows(this.http, ctx);
    if (code === SUCCESS) {
      const enabled = ctx.resp.workflows.filter((w) => w.enabled);
      this.enabledWorkflows.set(enabled);
      this.ensureSelections(this.entries());
    } else {
      this.enabledWorkflows.set([]);
      if (!this.error()) {
        this.actionError.set(ctx.resp.error || 'Failed to load workflows');
      }
    }
  }

  private ensureSelections(entries: MioStatusEntry[]): void {
    const enabled = this.enabledWorkflows();
    if (!enabled.length) {
      return;
    }
    const preferred =
      enabled.find((w) => w.workflow_name === DEFAULT_WORKFLOW_NAME) ?? enabled[0];
    this.selectedByMio.update((current) => {
      const next = { ...current };
      for (const mio of entries) {
        if (!next[mio.id] || !enabled.some((w) => w.id === next[mio.id])) {
          next[mio.id] = preferred.id;
        }
      }
      return next;
    });
  }
}
