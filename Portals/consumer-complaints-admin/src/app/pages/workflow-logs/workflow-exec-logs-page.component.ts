import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';
import { ButtonComponent } from '../../shared/components/ui/button/button.component';
import {
  ENGINE_TYPE_OPTIONS,
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

type SortKey =
  | 'workflow_name'
  | 'engine_label'
  | 'display_status'
  | 'engine_run_id'
  | 'requested_at'
  | 'started_at'
  | 'finished_at'
  | 'message';

type ColumnSearch = Record<SortKey, string>;

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
  protected readonly rawRows = signal<WorkflowLogEntry[]>([]);
  protected readonly error = signal('');
  protected readonly loading = signal(true);
  protected readonly pageSize = WORKFLOW_LOG_PAGE_SIZE;
  protected readonly pageOffset = signal(0);
  protected readonly hasNextPage = signal(false);
  protected readonly engineOptions = ENGINE_TYPE_OPTIONS;

  protected readonly sortKey = signal<SortKey>('requested_at');
  protected readonly sortDir = signal<'asc' | 'desc'>('desc');
  protected readonly detailRow = signal<WorkflowLogEntry | null>(null);

  protected startDate = '';
  protected endDate = '';
  protected startTime = '';
  protected endTime = '';
  protected engineRunId = '';
  protected engineTypeFilter = '';
  protected statusFilter = '';

  protected columnSearch: ColumnSearch = {
    workflow_name: '',
    engine_label: '',
    display_status: '',
    engine_run_id: '',
    requested_at: '',
    started_at: '',
    finished_at: '',
    message: '',
  };
  /** bump so computed re-reads columnSearch object mutations */
  protected readonly searchTick = signal(0);

  protected readonly displayRows = computed(() => {
    this.searchTick();
    let rows = [...this.rawRows()];
    const searches = this.columnSearch;
    for (const key of Object.keys(searches) as SortKey[]) {
      const q = (searches[key] || '').trim().toLowerCase();
      if (!q) continue;
      rows = rows.filter((r) => String(this.cellValue(r, key) ?? '').toLowerCase().includes(q));
    }
    const key = this.sortKey();
    const dir = this.sortDir() === 'asc' ? 1 : -1;
    rows.sort((a, b) => {
      const av = this.cellValue(a, key) ?? '';
      const bv = this.cellValue(b, key) ?? '';
      if (av < bv) return -1 * dir;
      if (av > bv) return 1 * dir;
      return 0;
    });
    return rows;
  });

  async ngOnInit(): Promise<void> {
    this.route.data.subscribe(async (data) => {
      const cat = (data['category'] || 'import') as WorkflowLogCategory;
      this.category.set(cat);
      this.categoryLabel.set(CATEGORY_LABELS[cat] ?? cat);
      this.pageOffset.set(0);
      await this.reload();
    });
  }

  protected async onApplyFilters(): Promise<void> {
    this.pageOffset.set(0);
    await this.reload();
  }

  protected async onRefresh(): Promise<void> {
    await this.reload();
  }

  protected async onPrevPage(): Promise<void> {
    const next = Math.max(0, this.pageOffset() - this.pageSize);
    this.pageOffset.set(next);
    await this.reload();
  }

  protected async onNextPage(): Promise<void> {
    if (!this.hasNextPage()) return;
    this.pageOffset.set(this.pageOffset() + this.pageSize);
    await this.reload();
  }

  protected onSort(key: SortKey): void {
    if (this.sortKey() === key) {
      this.sortDir.set(this.sortDir() === 'asc' ? 'desc' : 'asc');
    } else {
      this.sortKey.set(key);
      this.sortDir.set(key === 'requested_at' || key === 'started_at' || key === 'finished_at' ? 'desc' : 'asc');
    }
  }

  protected onColumnSearchChange(): void {
    this.searchTick.update((n) => n + 1);
  }

  protected openDetail(row: WorkflowLogEntry): void {
    this.detailRow.set(row);
  }

  protected closeDetail(): void {
    this.detailRow.set(null);
  }

  protected sortIndicator(key: SortKey): string {
    if (this.sortKey() !== key) return '';
    return this.sortDir() === 'asc' ? ' ↑' : ' ↓';
  }

  private cellValue(row: WorkflowLogEntry, key: SortKey): string {
    const v = row[key];
    return v == null ? '' : String(v);
  }

  private async reload(): Promise<void> {
    this.loading.set(true);
    const from = this.combineDateTime(this.startDate, this.startTime);
    const to = this.combineDateTime(this.endDate, this.endTime || '23:59:59');
    const ctx: WorkflowLogsCtx = {
      req: {
        category: this.category(),
        limit: WORKFLOW_LOG_PAGE_SIZE,
        offset: this.pageOffset(),
        status: this.statusFilter || undefined,
        engine_type: this.engineTypeFilter || undefined,
        engine_run_id: this.engineRunId || undefined,
        requested_after: from,
        requested_before: to,
      },
      resp: { entries: [], error: '' },
    };
    const code = await loadWorkflowLogs(this.http, ctx);
    this.loading.set(false);
    if (code === SUCCESS) {
      this.rawRows.set(ctx.resp.entries);
      this.hasNextPage.set(ctx.resp.entries.length >= WORKFLOW_LOG_PAGE_SIZE);
      this.error.set('');
    } else {
      this.rawRows.set([]);
      this.hasNextPage.set(false);
      this.error.set(ctx.resp.error || 'Failed to load workflow logs');
    }
  }

  private combineDateTime(date: string, time: string): string | undefined {
    if (!date) return undefined;
    return `${date}T${time || '00:00:00'}`;
  }
}
