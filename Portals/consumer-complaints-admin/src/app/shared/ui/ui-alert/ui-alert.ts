import { Component, input } from '@angular/core';

export type UiAlertTone = 'error' | 'info' | 'warning' | 'success';

@Component({
  selector: 'app-ui-alert',
  templateUrl: './ui-alert.html',
  styleUrl: './ui-alert.css',
})
export class UiAlert {
  readonly tone = input<UiAlertTone>('info');
  readonly testId = input<string>('');
  readonly role = input<'alert' | 'status' | null>(null);
}
