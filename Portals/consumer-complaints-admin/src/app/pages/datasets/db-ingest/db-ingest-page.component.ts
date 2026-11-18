import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { BadgeDirective, BadgeColor } from '../../../shared/components/ui/badge/badge.directive';
import { AlertComponent } from '../../../shared/components/ui/alert/alert.component';
import { ButtonComponent } from '../../../shared/components/ui/button/button.component';
import {
  DatasetImportRun,
  loadDatasetImportRuns,
  DatasetImportRunsCtx,
} from '../../../core/dataset-import-runs';
import {
  loadMioStatus,
  MioAllowedWorkflow,
  MioStatusCtx,
  MioStatusEntry,
} from '../../../core/mio-status';
import { startWorkflow, StartWorkflowCtx } from '../../../core/start-workflow';
import { SUCCESS } from '../../../core/return-codes';

const RUNNING_STATUSES = new Set(['requested', 'started']);
const ELIGIBLE = new Set(['landed', 'failed']);
const WRAPPER_NAME = 'ingest_cfpb_imports_wrapper';

function isIngestWorkflow(w: MioAllowedWorkflow): boolean {
  return w.workflow_name.startsWith('ingest_');
}

@Component({
  selector: 'app-db-ingest-page',
  imports: [BadgeDirective, AlertComponent, ButtonComponent, FormsModule],
  templateUrl: './db-ingest-page.component.html',
})
export class DbIngestPageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly entries = signal<MioStatusEntry[]>([]);
  protected readonly importRuns = signal<DatasetImportRun[]>([]);
  protected readonly selectedImportIds = signal<ReadonlySet<string>>(new Set());
  protected readonly ingestMode = signal<'sequential' | 'parallel'>('sequential');
  protected readonly error = signal('');
  protected readonly loading = signal(true);
  protected readonly selectedByMio = signal<Record<string, string>>({});
  protected readonly startingMioIds = signal<ReadonlySet<string>>(new Set());
  protected readonly actionError = signal('');

  async ngOnInit(): Promise<void> {
    await this.loadAll();
    this.loading.set(false);
  }

  protected allowedWorkflows(mio: MioStatusEntry): MioAllowedWorkflow[] {
    return (mio.allowed_workflows ?? []).filter((w) => w.enabled && isIngestWorkflow(w));
  }

  protected selectedWorkflowId(mioId: string): string {
    return this.selectedByMio()[mioId] ?? '';
  }

  protected onWorkflowChange(mioId: string, event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.selectedByMio.update((m) => ({ ...m, [mioId]: value }));
  }

  protected isEligible(run: DatasetImportRun): boolean {
    return ELIGIBLE.has(run.status);
  }

  protected isImportChecked(id: string): boolean {
    return this.selectedImportIds().has(id);
  }

  protected onToggleImport(id: string, event: Event): void {
    const checked = (event.target as HTMLInputElement).checked;
    this.selectedImportIds.update((current) => {
      const next = new Set(current);
      if (checked) {
        next.add(id);
      } else {
        next.delete(id);
      }
      return next;
    });
  }

  protected onModeChange(event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.ingestMode.set(value === 'parallel' ? 'parallel' : 'sequential');
  }

  protected isStartDisabled(mio: MioStatusEntry): boolean {
    const workflowId = this.selectedWorkflowId(mio.id);
    if (!workflowId) {
      return true;
    }
    if (this.startingMioIds().has(mio.id)) {
      return true;
    }
    const wf = this.allowedWorkflows(mio).find((w) => w.id === workflowId);
    if (wf?.workflow_name === WRAPPER_NAME) {
      return this.selectedImportIds().size === 0;
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
    const wf = this.allowedWorkflows(mio).find((w) => w.id === workflowId);
    const ctx: StartWorkflowCtx = {
      req: {
        workflowId,
        mioId: mio.id,
        ...(wf?.workflow_name === WRAPPER_NAME
          ? {
              importIds: [...this.selectedImportIds()],
              mode: this.ingestMode(),
            }
          : {}),
      },
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
    this.selectedImportIds.set(new Set());
    await this.loadAll();
  }

  protected async onRefresh(): Promise<void> {
    this.actionError.set('');
    await this.loadAll();
  }

  protected statusColor(status: string | null | undefined): BadgeColor {
    if (!status) {
      return 'gray';
    }
    switch (status) {
      case 'completed':
      case 'ingested':
      case 'landed':
        return 'success';
      case 'failed':
        return 'error';
      case 'started':
      case 'requested':
      case 'ingesting':
      case 'staging':
        return 'info';
      default:
        return 'warning';
    }
  }

  private async loadAll(): Promise<void> {
    await Promise.all([this.loadStatus(), this.loadImports()]);
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

  private async loadImports(): Promise<void> {
    const ctx: DatasetImportRunsCtx = { req: {}, resp: { runs: [], error: '' } };
    const code = await loadDatasetImportRuns(this.http, ctx);
    if (code === SUCCESS) {
      this.importRuns.set(ctx.resp.runs);
    } else if (!this.error()) {
      this.error.set(ctx.resp.error || 'Failed to load import runs');
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
        const preferred = allowed.find((w) => w.workflow_name === WRAPPER_NAME) ?? allowed[0];
        if (!next[mio.id] || !allowed.some((w) => w.id === next[mio.id])) {
          next[mio.id] = preferred.id;
        }
      }
      return next;
    });
  }
}
