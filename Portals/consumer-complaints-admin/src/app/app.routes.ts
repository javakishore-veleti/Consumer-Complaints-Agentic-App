import { Routes } from '@angular/router';
import { AppLayoutComponent } from './layout/shell/app-layout/app-layout.component';
import { NotFoundComponent } from './pages/other-page/not-found/not-found.component';
import { HomeComponent } from './pages/home/home.component';
import { ImportsPageComponent } from './pages/datasets/imports/imports-page.component';

export const routes: Routes = [
  {
    path: '',
    component: AppLayoutComponent,
    children: [
      {
        path: '',
        component: HomeComponent,
        pathMatch: 'full',
        title: 'Consumer Complaints Admin',
      },
      {
        path: 'datasets',
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'imports' },
          {
            path: 'imports',
            component: ImportsPageComponent,
            title: 'Imports | Consumer Complaints Admin',
          },
        ],
      },
    ],
  },
  {
    path: '**',
    component: NotFoundComponent,
    title: 'Not found | Consumer Complaints Admin',
  },
];
