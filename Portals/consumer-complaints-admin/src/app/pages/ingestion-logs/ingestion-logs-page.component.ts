import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { ActivatedRoute } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';
import { ButtonComponent } from '../../shared/components/ui/button/button.component';
import {
  INGESTION_LOG_PAGE_SIZE,
  INGESTION_LOG_ZONES,
  IngestionLogEntry,
  IngestionLogZone,
  IngestionLogsCtx,
  loadIngestionLogs,
} from '../../core/ingestion-logs';
import { SUCCESS } from '../../core/return-codes';

@Component({
  selector: 'app-ingestion-logs-page',
  imports: [AlertComponent, ButtonComponent, FormsModule],
  templateUrl: './ingestion-logs-page.component.html',
})
export class IngestionLogsPageComponent implements OnInit {
  private readonly http = inject(HttpClient);
  private readonly route = inject(ActivatedRoute);

  protected readonly zone = signal<IngestionLogZone>('raw');
  protected readonly zoneLabel = signal('Raw');
  protected readonly rows = signal<IngestionLogEntry[]>([]);
  protected readonly error = signal('');
  protected readonly loading = signal(true);
  protected readonly pageSize = INGESTION_LOG_PAGE_SIZE;

  protected startDate = '';
  protected endDate = '';
  protected startTime = '';
  protected endTime = '';
  protected workflowExecutionId = '';
  protected statusFilter = '';

  async ngOnInit(): Promise<void> {
    this.route.paramMap.subscribe(async (params) => {
      const z = (params.get('zone') || 'raw') as IngestionLogZone;
      this.zone.set(z);
      this.zoneLabel.set(INGESTION_LOG_ZONES.find((x) => x.zone === z)?.label ?? z);
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
    const ctx: IngestionLogsCtx = {
      req: {
        zone: this.zone(),
        limit: INGESTION_LOG_PAGE_SIZE,
        status: this.statusFilter || undefined,
        workflow_execution_id: this.workflowExecutionId || undefined,
        status_updated_from: from,
        status_updated_to: to,
      },
      resp: { entries: [], error: '' },
    };
    const code = await loadIngestionLogs(this.http, ctx);
    this.loading.set(false);
    if (code === SUCCESS) {
      this.rows.set(ctx.resp.entries);
      this.error.set('');
    } else {
      this.rows.set([]);
      this.error.set(ctx.resp.error || 'Failed to load ingestion logs');
    }
  }

  private combineDateTime(date: string, time: string): string | undefined {
    if (!date) return undefined;
    const t = time || '00:00:00';
    return `${date}T${t.length === 5 ? `${t}:00` : t}Z`;
  }
}
