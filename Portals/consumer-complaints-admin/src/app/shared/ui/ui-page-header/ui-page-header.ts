import { Component, input } from '@angular/core';

@Component({
  selector: 'app-ui-page-header',
  templateUrl: './ui-page-header.html',
  styleUrl: './ui-page-header.css',
})
export class UiPageHeader {
  readonly title = input.required<string>();
  readonly subtitle = input('');
  readonly headingId = input('page-heading');
}
