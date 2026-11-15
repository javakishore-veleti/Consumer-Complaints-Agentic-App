import { Component, input } from '@angular/core';

export type UiBadgeTone = 'success' | 'danger' | 'info' | 'warning' | 'muted';

@Component({
  selector: 'app-ui-badge',
  templateUrl: './ui-badge.html',
  styleUrl: './ui-badge.css',
})
export class UiBadge {
  readonly tone = input<UiBadgeTone>('muted');
  /** Keep `.mio-status` for existing Imports tests when set. */
  readonly extraClass = input('');
}
