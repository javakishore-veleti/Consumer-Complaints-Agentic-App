import { Routes } from '@angular/router';
import { Home } from './home/home';
import { DatasetsLayout } from './datasets/datasets-layout';
import { ImportsPage } from './datasets/imports/imports-page';

export const routes: Routes = [
  { path: '', component: Home },
  {
    path: 'datasets',
    component: DatasetsLayout,
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'imports' },
      { path: 'imports', component: ImportsPage },
    ],
  },
];
