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
  MioStatusExecution,
} from '../../../core/mio-status';
import { startWorkflow, StartWorkflowCtx } from '../../../core/start-workflow';
import { SUCCESS } from '../../../core/return-codes';

const RUNNING_STATUSES = new Set(['requested', 'started']);

/** Pipeline order for Lakehouse hydrate (Iceberg stages, then optional Chroma catalog). */
const HYDRATE_PIPELINE_ORDER: ReadonlyArray<{ match: RegExp; step: number }> = [
  { match: /^hydrate_raw_iceberg/, step: 1 },
  { match: /^hydrate_refined_iceberg/, step: 2 },
  { match: /^hydrate_taxonomy/, step: 3 },
  { match: /^hydrate_curated_iceberg/, step: 4 },
  { match: /^hydrate_chroma_signatures/, step: 5 },
];

function isLakehouseWorkflow(w: MioAllowedWorkflow): boolean {
  return w.workflow_name.startsWith('hydrate_');
}

function hydratePipelineStep(workflowName: string): number {
  for (const row of HYDRATE_PIPELINE_ORDER) {
    if (row.match.test(workflowName)) {
      return row.step;
    }
  }
  return 99;
}

@Component({
  selector: 'app-lakehouse-page',
  imports: [BadgeDirective, AlertComponent, ButtonComponent],
  templateUrl: './lakehouse-page.component.html',
})
export class LakehousePageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  protected readonly entries = signal<MioStatusEntry[]>([]);
  protected readonly error = signal('');
  protected readonly loading = signal(true);
  protected readonly selectedByMio = signal<Record<string, string>>({});
  protected readonly startingMioIds = signal<ReadonlySet<string>>(new Set());
  protected readonly actionError = signal('');

  async ngOnInit(): Promise<void> {
    await this.loadStatus();
    this.loading.set(false);
  }

  protected allowedWorkflows(mio: MioStatusEntry): MioAllowedWorkflow[] {
    return (mio.allowed_workflows ?? [])
      .filter((w) => w.enabled && isLakehouseWorkflow(w))
      .slice()
      .sort(
        (a, b) =>
          hydratePipelineStep(a.workflow_name) - hydratePipelineStep(b.workflow_name) ||
          a.workflow_name.localeCompare(b.workflow_name),
      );
  }

  protected workflowOptionLabel(wf: MioAllowedWorkflow): string {
    const step = hydratePipelineStep(wf.workflow_name);
    return step < 99 ? `${step}. ${wf.workflow_name}` : wf.workflow_name;
  }

  protected selectedWorkflowId(mioId: string): string {
    return this.selectedByMio()[mioId] ?? '';
  }

  protected onWorkflowChange(mioId: string, event: Event): void {
    const value = (event.target as HTMLSelectElement).value;
    this.selectedByMio.update((m) => ({ ...m, [mioId]: value }));
  }

  protected latestLakehouseExec(mio: MioStatusEntry): MioStatusExecution | null {
    const execs = mio.latest_ingest?.executions ?? [];
    const lake = execs.filter((e) => (e.workflow_name || '').startsWith('hydrate_'));
    return lake[0] ?? null;
  }

  protected isStartDisabled(mio: MioStatusEntry): boolean {
    const workflowId = this.selectedWorkflowId(mio.id);
    if (!workflowId) {
      return true;
    }
    if (this.startingMioIds().has(mio.id)) {
      return true;
    }
    if (!this.allowedWorkflows(mio).length) {
      return true;
    }
    const latest = this.latestLakehouseExec(mio);
    if (latest && RUNNING_STATUSES.has(latest.status)) {
      return true;
    }
    return false;
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
