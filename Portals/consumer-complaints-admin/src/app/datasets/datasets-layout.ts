import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-datasets-layout',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './datasets-layout.html',
  styleUrl: './datasets-layout.css',
})
export class DatasetsLayout {}
