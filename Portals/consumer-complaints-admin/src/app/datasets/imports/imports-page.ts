import { Component, OnInit, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { loadMioStatus, MioStatusCtx, MioStatusEntry } from '../../core/mio-status';
import { SUCCESS } from '../../core/return-codes';

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

  async ngOnInit(): Promise<void> {
    const ctx: MioStatusCtx = { req: {}, resp: { entries: [], error: '' } };
    const code = await loadMioStatus(this.http, ctx);
    this.loading.set(false);
    if (code === SUCCESS) {
      this.entries.set(ctx.resp.entries);
      this.error.set('');
    } else {
      this.entries.set([]);
      this.error.set(ctx.resp.error || 'Failed to load MIO status');
    }
  }
}
