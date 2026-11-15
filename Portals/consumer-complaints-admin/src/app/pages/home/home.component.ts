import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { RouterLink } from '@angular/router';
import { AlertComponent } from '../../shared/components/ui/alert/alert.component';
import { ButtonComponent } from '../../shared/components/ui/button/button.component';
import { loadMioStatus, MioStatusCtx, MioStatusEntry } from '../../core/mio-status';
import { SUCCESS } from '../../core/return-codes';

export interface HomeKpiCounts {
  total: number;
  idle: number;
  inProgress: number;
  completed: number;
  failed: number;
}

function countFromEntries(entries: MioStatusEntry[]): HomeKpiCounts {
  const counts: HomeKpiCounts = {
    total: entries.length,
    idle: 0,
    inProgress: 0,
    completed: 0,
    failed: 0,
  };
  for (const mio of entries) {
    const status = mio.latest_ingest?.status;
    if (!status) {
      counts.idle += 1;
    } else if (status === 'requested' || status === 'started') {
      counts.inProgress += 1;
    } else if (status === 'completed') {
      counts.completed += 1;
    } else if (status === 'failed') {
      counts.failed += 1;
    } else {
      counts.idle += 1;
    }
  }
  return counts;
}

@Component({
  selector: 'app-home',
  imports: [RouterLink, AlertComponent, ButtonComponent],
  templateUrl: './home.component.html',
})
export class HomeComponent implements OnInit {
  private readonly http = inject(HttpClient);

  protected readonly loading = signal(true);
  protected readonly error = signal('');
  protected readonly counts = signal<HomeKpiCounts>({
    total: 0,
    idle: 0,
    inProgress: 0,
    completed: 0,
    failed: 0,
  });

  async ngOnInit(): Promise<void> {
    const ctx: MioStatusCtx = { req: {}, resp: { entries: [], error: '' } };
    const code = await loadMioStatus(this.http, ctx);
    this.loading.set(false);
    if (code === SUCCESS) {
      this.counts.set(countFromEntries(ctx.resp.entries));
      this.error.set('');
      return;
    }
    this.counts.set({ total: 0, idle: 0, inProgress: 0, completed: 0, failed: 0 });
    this.error.set(ctx.resp.error || 'Failed to load MIO status');
  }
}
