import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';
import { ButtonComponent } from '../../shared/components/ui/button/button.component';
import {
  WORKFLOW_LOG_PAGE_SIZE,
  WorkflowLogCategory,
  WorkflowLogEntry,
  WorkflowLogsCtx,
  loadWorkflowLogs,
} from '../../core/workflow-logs';
import { SUCCESS } from '../../core/return-codes';

const CATEGORY_LABELS: Record<string, string> = {
  import: 'DataSets Import',
  db_ingest: 'DB Ingest',
};

@Component({
  selector: 'app-workflow-exec-logs-page',
  imports: [AlertComponent, ButtonComponent, FormsModule],
  templateUrl: './workflow-exec-logs-page.component.html',
})
export class WorkflowExecLogsPageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);

  protected readonly category = signal<WorkflowLogCategory>('import');
  protected readonly categoryLabel = signal('DataSets Import');
  protected readonly rows = signal<WorkflowLogEntry[]>([]);
  protected readonly error = signal('');
  protected readonly loading = signal(true);
  protected readonly pageSize = WORKFLOW_LOG_PAGE_SIZE;

  protected startDate = '';
  protected endDate = '';
  protected startTime = '';
  protected endTime = '';
  protected engineRunId = '';
  protected statusFilter = '';

  async ngOnInit(): Promise<void> {
    this.route.data.subscribe(async (data) => {
      const cat = (data['category'] || 'import') as WorkflowLogCategory;
      this.category.set(cat);
      this.categoryLabel.set(CATEGORY_LABELS[cat] ?? cat);
      await this.reload();
    });
  }

  protected async onApplyFilters(): Promise<void> {
    await this.reload();
  }

  protected async onRefresh(): Promise<void> {
    await this.reload();
  }

  private async reload(): Promise<void> {
    this.loading.set(true);
    const from = this.combineDateTime(this.startDate, this.startTime);
    const to = this.combineDateTime(this.endDate, this.endTime || '23:59:59');
    const ctx: WorkflowLogsCtx = {
      req: {
        category: this.category(),
        limit: WORKFLOW_LOG_PAGE_SIZE,
        status: this.statusFilter || undefined,
        engine_run_id: this.engineRunId || undefined,
        requested_after: from,
        requested_before: to,
      },
      resp: { entries: [], error: '' },
    };
    const code = await loadWorkflowLogs(this.http, ctx);
    this.loading.set(false);
    if (code === SUCCESS) {
      this.rows.set(ctx.resp.entries);
      this.error.set('');
    } else {
      this.rows.set([]);
      this.error.set(ctx.resp.error || 'Failed to load workflow logs');
    }
  }

  private combineDateTime(date: string, time: string): string | undefined {
    if (!date) return undefined;
    return `${date}T${time || '00:00:00'}`;
  }
}
